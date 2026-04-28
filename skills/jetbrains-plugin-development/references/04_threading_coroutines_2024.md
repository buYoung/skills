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

For a one-shot scope tied to a single action, use `currentThreadCoroutineScope()` (2024.2+)
inside `actionPerformed`.

### Dispatchers

| Dispatcher | Use for |
|---|---|
| `Dispatchers.Default` | CPU-bound work |
| `Dispatchers.IO` | Brief I/O. Do not stay here for PSI/VFS access |
| `Dispatchers.EDT` | Swing UI. Modality-aware. **Use this, not `Dispatchers.Main`** |
| `Dispatchers.UI` | Pure EDT, no Write Intent Lock — rarely the right choice |

`kotlinx.coroutines.Dispatchers.Main` is **not** the EDT for the IDE. It does not understand
`ModalityState`, so a coroutine on `Dispatchers.Main` can resume in the wrong order while
a modal dialog is open. Always use `Dispatchers.EDT`.

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

| API | Thread it acquires lock on | Stability |
|---|---|---|
| `writeAction { }` | EDT (auto-switch) | `@Experimental` |
| `edtWriteAction { }` | EDT (explicit) | **Stable** |
| `backgroundWriteAction { }` | `Dispatchers.Default` | **Stable** |
| `writeIntentReadAction { }` | EDT, Write Intent only | `@Experimental` |
| `writeCommandAction(project, name) { }` | EDT + CommandProcessor (undo) | `@Experimental` |

For PSI/Document edits that must be undoable, use `writeCommandAction(project, "Insert Hello") { ... }`.
For pure VFS or non-document state changes, `backgroundWriteAction` avoids EDT contention.

### Read-then-write composites

```kotlin
readAndEdtWriteAction {
  val target = findTarget()
  writeAction { target.modify() }
}

readAndBackgroundWriteAction {
  val file = findFile()
  writeAction { file.setBinaryContent(newBytes) }
}

constrainedReadAndWriteAction(ReadConstraint.inSmartMode(project)) {
  val target = resolveTarget()
  writeAction { target.rename("newName") }
}
```

`readAndWriteAction { }` is **deprecated** — replace with `readAndEdtWriteAction` or
`readAndBackgroundWriteAction` to make the EDT/BGT choice explicit.

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

Use when **legacy blocking code** must call a suspending function:

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
- Cancellation of the calling thread's Job propagates into the suspend body.
- Do not use `kotlinx.coroutines.runBlocking` instead — it ignores platform context and
  cancellation.

### `blockingContext { }` is deprecated (2024.2+)

In 2024.1, `blockingContext { foo() }` was used to enter blocking-mode within a suspend
function. From 2024.2, the platform installs blocking context implicitly; just call
`foo()` directly. The old form emits a deprecation warning.
