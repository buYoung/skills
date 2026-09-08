# Thread to Coroutine Migration

## Contents

- Migrating from `Thread` / `ExecutorService` / `Task.Backgroundable` to coroutines


## Migrating from `Thread` / `ExecutorService` / `Task.Backgroundable` to coroutines

The recipe most legacy plugins need. Apply this stepwise; each row is a self-contained
swap.

| Old | New |
|---|---|
| `class MyService { fun runAsync() { executor.submit { … } } }` | `class MyService(private val cs: CoroutineScope) { fun runAsync() = cs.launch { … } }` |
| `private val executor = Executors.newFixedThreadPool(N)` | Drop it. Use the injected `cs` and `Dispatchers.Default`/`Dispatchers.IO`. To cap parallelism, launch with `Dispatchers.Default.limitedParallelism(N)`; do not create an orphan scope. |
| `Thread { … }.start()` | `cs.launch { … }` |
| `ApplicationManager.getApplication().executeOnPooledThread { … }` (returning `Future`) | `cs.async { … }` returning `Deferred<T>` |
| `CompletableFuture<T>` | `Deferred<T>` (via `cs.async { }`); `await()` to consume |
| `ApplicationManager.getApplication().invokeLater({ … }, ModalityState…)` | `withContext(modality.asContextElement() + Dispatchers.EDT) { … }`; keep the original modality explicitly |
| `ApplicationManager.getApplication().invokeAndWait({ … }, ModalityState…)` | Same suspending form; it waits without blocking the caller thread |
| `ReadAction.compute { … }` | `readAction { … }` |
| `ReadAction.nonBlocking { … }.inSmartMode(p).submit(executor)` | `smartReadAction(project) { … }` |
| `WriteAction.run { … }` (already on EDT) | `edtWriteAction { … }` on 2025.1+; on 2024.1–2024.3 keep `withContext(Dispatchers.EDT)` plus classic `WriteAction.run` |
| `WriteCommandAction.runWriteCommandAction(project) { … }` | Keep it for stable-only APIs, or use public `@Experimental` `writeCommandAction(project, "name") { … }` after recording the target-version risk |
| `ProgressManager.run(Task.Backgroundable…)` | `cs.launch { withBackgroundProgress(project, title) { reportProgress(N) { r -> … } } }` |
| `ProgressManager.runProcessWithProgressSynchronously(…)` | `cs.launch { withModalProgress(project, title) { … } }`, or keep classic when callers require its synchronous return contract |
| `Disposable` + manual cleanup of thread / future | Inject `CoroutineScope`. Drop the `Disposable`. |
| `try { … } catch (e: Exception) { log(e) }` | Add `if (e is CancellationException) throw e` (or split into two catches) |
| `blockingContext { foo() }` | `foo()` (2024.2+) |

A worked example. Before:

```kotlin
class MyService(private val project: Project) : Disposable {
  private val executor = Executors.newSingleThreadExecutor()
  private val futures = mutableListOf<Future<*>>()

  fun analyzeAsync(file: VirtualFile) {
    val f = executor.submit {
      val psi = ReadAction.compute<PsiFile?, Throwable> {
        PsiManager.getInstance(project).findFile(file)
      } ?: return@submit
      val results = ReadAction.compute<List<String>, Throwable> { walk(psi) }
      ApplicationManager.getApplication().invokeLater({
        WriteCommandAction.runWriteCommandAction(project) {
          applyResults(file, results)
        }
      }, ModalityState.defaultModalityState())
    }
    futures += f
  }

  override fun dispose() {
    futures.forEach { it.cancel(true) }
    executor.shutdownNow()
  }
}
```

After:

```kotlin
@Service(Service.Level.PROJECT)
class MyService(
  private val project: Project,
  private val cs: CoroutineScope,
) {
  fun analyzeAsync(file: VirtualFile) {
    cs.launch {
      val psi = readAction { PsiManager.getInstance(project).findFile(file) } ?: return@launch
      val results = readAction { walk(psi) }
      writeCommandAction(project, "Apply Analysis") {
        applyResults(file, results)
      }
    }
  }

  companion object {
    fun getInstance(project: Project): MyService =
      project.getService(MyService::class.java)
  }
}
```

Notes on the migration:

- `Disposable` and explicit cancellation disappear; the injected `cs` covers cancellation.
- `invokeLater + WriteCommandAction.runWriteCommandAction` can collapse into the public
  `@Experimental` suspending `writeCommandAction(project, name) { }` when the supported
  version range accepts that API. Otherwise keep the stable classic call.
- The suspending `writeCommandAction` keeps the EDT and undo contracts. In contrast,
  `writeAction` runs the write phase on a background thread in 2026.2.2; substituting it
  would change behavior.
- `serviceImplementation` XML registration disappears in favor of `@Service`.

When the legacy code is exposed publicly (other plugins or non-coroutine call sites), keep
the suspending core and add a thin blocking wrapper using `runBlockingCancellable` — but
*only* for BGT call sites:

```kotlin
@RequiresBackgroundThread
fun analyzeBlocking(file: VirtualFile): List<String> = runBlockingCancellable {
  analyzeSuspending(file)
}
```

For EDT call sites, do not block; either offer a coroutine API or schedule with
`cs.launch { … }`.

### Preserve behavior across platform versions

- On 2024.1-era targets, `writeAction` switched to EDT and was experimental.
- On 2025.1+, `edtWriteAction` is the stable, explicit choice for legacy EDT writes.
- At `idea/2026.2.2` (`1c7e601c0423e544917046c23763b15d0282e2a3`), `writeAction`
  delegates to `backgroundWriteAction`. Audit every called API before choosing it.
- For a coroutine launched by an action, use `AnActionEvent.coroutineScope` on 2026.1+,
  `currentThreadCoroutineScope()` on 2024.2–2025.3, or an injected service scope on 2024.1.

See the fixed-source links and public API status in `04_threading_coroutines_2024.md`.
