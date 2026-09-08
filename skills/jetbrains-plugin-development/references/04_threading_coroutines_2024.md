# Coroutines 2024

## Contents

- Coroutine API (2024.1+) — recommended
  - Service-injected `CoroutineScope`
  - Dispatchers
  - Suspending Read Actions
  - Suspending Write Actions
  - Read-then-write composites
  - Progress and cancellation
  - `runBlockingCancellable` — bridging blocking → suspending
  - `blockingContext { }` is deprecated (2024.2+)


## Coroutine API (2024.1+) — recommended

New code should use Kotlin coroutines. The platform provides dispatchers that integrate
with EDT modality and lock-aware suspending versions of read/write actions.

### Service-injected `CoroutineScope`

```kotlin
@Service
class MyApplicationService(private val cs: CoroutineScope) {
  fun fetchInBackground(query: String) {
    cs.launch {
      val result = withContext(Dispatchers.IO) { httpClient.get(query) }
      val parsed  = readAction { parseAndResolve(result) }
      withContext(Dispatchers.EDT) { showResult(parsed) }
    }
  }

  companion object {
    fun getInstance(): MyApplicationService =
      ApplicationManager.getApplication().getService(MyApplicationService::class.java)
  }
}
```

The injected `CoroutineScope`:

- Is cancelled when the service is disposed (project close, plugin unload, IDE shutdown).
- Replaces manual `Disposable` bookkeeping for almost everything launched inside it.
- Is the **only** correct scope for service-owned work. `Application.getCoroutineScope()`
  / `Project.getCoroutineScope()` are `@ApiStatus.Internal`/`Obsolete`. `GlobalScope` leaks.

For action work, use the public API that matches the minimum target:

- 2026.1+: launch from `e.coroutineScope` inside `actionPerformed`. The Action System owns
  cancellation; retrieve the property only from `actionPerformed`, then launch child work on it.
- 2024.2–2025.3: `currentThreadCoroutineScope()` is the documented action path.
- 2024.1: delegate to a service and launch from its injected scope.

### Dispatchers

| Dispatcher | Use for |
|---|---|
| `Dispatchers.Default` | CPU-bound work |
| `Dispatchers.IO` | Brief I/O. Do not stay here for PSI/VFS access |
| `Dispatchers.EDT` | EDT plus Write Intent for legacy model access; modality-aware |
| `Dispatchers.UI` | 2025.3+ pure UI on EDT, without Write Intent; preferred for Swing-only work |

The IntelliJ Platform installs its EDT dispatcher as `Dispatchers.Main`, so `Main` does run
on EDT. The lock semantics differ: since 2025.1 it is a pure-UI path without Write Intent,
and read/write actions must not start inside it. Use `Dispatchers.UI` for explicit pure UI on
2025.3+, and `Dispatchers.EDT` for legacy model access that must stay on EDT. Carry the
required `ModalityState` in the coroutine context rather than relying on an unspecified one.

### Suspending Read Actions

```kotlin
val file = readAction { PsiManager.getInstance(project).findFile(vf) }
```

Two flavors:

| API | Semantics |
|---|---|
| `readAction { }` | **WARA** — write-allows-read-action. If a Write arrives, the block is cancelled (PCE) and re-run. Block must be idempotent. Default for background analysis. |
| `readActionBlocking { }` | **WBRA** — write-blocking. The block runs to completion while Writes wait. Use only for short, atomic reads. |

Index-aware variants:

```kotlin
val r = smartReadAction(project) { /* indexes available */ }
val r = smartReadActionBlocking(project) { /* WBRA + smart mode */ }

val r = constrainedReadAction(
  ReadConstraint.inSmartMode(project),
  ReadConstraint.withDocumentsCommitted(project)
) { /* both constraints satisfied */ }
```

`ReadConstraint.inSmartMode(project)` waits until Dumb Mode finishes. `withDocumentsCommitted`
waits until pending document edits have been reflected into the PSI tree.

### Suspending Write Actions

These are top-level functions in `com.intellij.openapi.application`:

```kotlin
import com.intellij.openapi.application.writeAction
import com.intellij.openapi.application.edtWriteAction
import com.intellij.openapi.application.backgroundWriteAction
import com.intellij.openapi.application.writeIntentReadAction
```

| API | 2024.1-era behavior | 2026.2.2 behavior/status |
|---|---|---|
| `writeAction { }` | Experimental, EDT-switching | Public stable alias of `backgroundWriteAction`; runs from `Dispatchers.Default` |
| `edtWriteAction { }` | Added as the stable explicit path in 2025.1 | Public stable; EDT plus Write Lock |
| `backgroundWriteAction { }` | Not a compatibility substitute for EDT-only code | Public stable; background Write Lock |
| `writeIntentReadAction { }` | EDT Write Intent | Public `@Experimental`; prefer stable read/write actions |
| `writeCommandAction(project, name) { }` | EDT + CommandProcessor | Public `@Experimental`; use classic `WriteCommandAction` when stable-only support is required |

Do not migrate `WriteAction.run` or an older `writeAction` mechanically to the 2026.2
`writeAction`: that can move the body from EDT to BGT. On 2025.1+, use `edtWriteAction` to
preserve EDT behavior; on earlier targets keep `withContext(Dispatchers.EDT)` plus the
classic `WriteAction`. For PSI/Document edits that must be undoable, use the experimental suspending
`writeCommandAction` only when the target accepts that stability risk; otherwise keep the
stable `WriteCommandAction` and its EDT contract. Use background writes only after confirming
every called API is BGT-safe.

### Read-then-write composites

```kotlin
readAndEdtWriteAction {
  val target = findTarget()
  writeAction { target.modify() } // receiver DSL method; the write phase runs on EDT
}

readAndBackgroundWriteAction {
  val file = findFile()
  writeAction { file.setBinaryContent(newBytes) } // receiver DSL method; BGT write phase
}

constrainedReadAndWriteAction(ReadConstraint.inSmartMode(project)) {
  val target = resolveTarget()
  writeAction { target.rename("newName") } // constrained public variant writes on EDT
}
```

`readAndWriteAction { }` is **deprecated** — replace it according to existing behavior:
`readAndEdtWriteAction` preserves the historical EDT write phase;
`readAndBackgroundWriteAction` is an intentional behavior change after a BGT-safety audit.
The `writeAction` called inside these blocks is the `ReadAndWriteScope` DSL method, not the
top-level suspending function. `ReadAndWriteScope` is public `@ApiStatus.NonExtendable`:
use the receiver supplied by these functions and never implement the interface yourself.

### Progress and cancellation

```kotlin
cs.launch {
  withBackgroundProgress(project, "Analyzing") {
    reportProgress(items.size) { reporter ->
      items.forEach { item ->
        reporter.itemStep("Processing ${item.name}") { process(item) }
      }
    }
  }
}
```

`withBackgroundProgress` is the coroutine equivalent of `Task.Backgroundable`. There is also
`withModalProgress(project, title) { }` for modal dialogs.

Cancellation propagates naturally: structured concurrency cancels children, suspension
points throw `CancellationException`, and the platform's PCE-based APIs translate into the
same. Critical rule:

```kotlin
try {
  doWork()
} catch (e: CancellationException) {
  throw e            // never swallow
} catch (e: Exception) {
  log.error(e)
}
```

A `try { … } catch (e: Exception) { log.error(e) }` without re-throwing
`CancellationException` (and `ProcessCanceledException` in non-coroutine code) silently
disables cancellation. This is one of the most common bugs in plugin code.

For tight Java loops with no suspension points, still call
`ProgressManager.checkCanceled()` periodically — coroutines only check at suspension points.

### `runBlockingCancellable` — bridging blocking → suspending

```kotlin
@RequiresBackgroundThread
@RequiresBlockingContext
fun <T> runBlockingCancellable(action: suspend CoroutineScope.() -> T): T
```

Use only when **legacy blocking code already running under a cancellable Job or progress
indicator** must call a suspending function:

```kotlin
fun run(indicator: ProgressIndicator) {
  val result = runBlockingCancellable {
    val data = readAction { collectData() }
    withContext(Dispatchers.IO) { sendToServer(data) }
  }
  use(result)
}
```

Rules:

- BGT only. Calling on the EDT deadlocks because it does not pump events.
- Cancellation of the calling thread's Job or indicator propagates into the suspend body.
- Without a current Job or indicator, the platform logs an error because the bridge cannot
  be cancelled from outside. Prefer keeping the call chain suspending.
- Do not use `kotlinx.coroutines.runBlocking` instead — it ignores platform context and
  cancellation.

### `blockingContext { }` is deprecated (2024.2+)

In 2024.1, `blockingContext { foo() }` was used to enter blocking-mode within a suspend
function. From 2024.2, the platform installs blocking context implicitly; just call
`foo()` directly. The old form emits a deprecation warning.

## Fixed-source evidence and public API status

The 2026.2.2 behavior and annotations above were checked at tag `idea/2026.2.2`, commit
`1c7e601c0423e544917046c23763b15d0282e2a3`:

- [`application/coroutines.kt`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/core-api/src/com/intellij/openapi/application/coroutines.kt)
- [`ReadConstraint.kt`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/core-api/src/com/intellij/openapi/application/ReadConstraint.kt)
- [`command/coroutines.kt`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/core-api/src/com/intellij/openapi/command/coroutines.kt)
- [`progress/coroutines.kt`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/core-api/src/com/intellij/openapi/progress/coroutines.kt)
- [`progress/shared/src/tasks.kt`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/progress/shared/src/tasks.kt)
- [`util/progress/src/steps.kt`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/util/progress/src/steps.kt)
- [`AnActionEvent.java`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/editor-ui-api/src/com/intellij/openapi/actionSystem/AnActionEvent.java)

Version boundaries come from the official [2025 API changes](https://plugins.jetbrains.com/docs/intellij/api-notable-list-2025.html)
and [2026 API changes](https://plugins.jetbrains.com/docs/intellij/api-notable-list-2026.html).

Only unannotated public APIs and explicitly identified public `@Experimental` APIs are
listed as callable plugin APIs. Do not call neighboring `@ApiStatus.Internal` helpers such
as `readActionUndispatched`, `Dispatchers.ui(...)`, or `Dispatchers.UiWithModelAccess`.
