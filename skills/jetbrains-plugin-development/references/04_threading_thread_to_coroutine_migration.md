# Thread to Coroutine Migration

## Contents

- Migrating from `Thread` / `ExecutorService` / `Task.Backgroundable` to coroutines


## Migrating from `Thread` / `ExecutorService` / `Task.Backgroundable` to coroutines

The recipe most legacy plugins need. Apply this stepwise; each row is a self-contained
swap.

| Old | New |
|---|---|
| `class MyService { fun runAsync() { executor.submit { … } } }` | `class MyService(private val cs: CoroutineScope) { fun runAsync() = cs.launch { … } }` |
| `private val executor = Executors.newFixedThreadPool(N)` | Drop it. Use the injected `cs` and `Dispatchers.Default`/`Dispatchers.IO`/`Dispatchers.EDT`. For a strict pool, build one over `cs`: `val pool = cs.coroutineContext + limitedParallelism(N)`. |
| `Thread { … }.start()` | `cs.launch { … }` |
| `ApplicationManager.getApplication().executeOnPooledThread { … }` (returning `Future`) | `cs.async { … }` returning `Deferred<T>` |
| `CompletableFuture<T>` | `Deferred<T>` (via `cs.async { }`); `await()` to consume |
| `ApplicationManager.getApplication().invokeLater({ … }, ModalityState…)` | `withContext(Dispatchers.EDT) { … }` (modality-aware) |
| `ApplicationManager.getApplication().invokeAndWait({ … }, ModalityState…)` | `withContext(Dispatchers.EDT) { … }` (always blocks the suspending caller until done) |
| `ReadAction.compute { … }` | `readAction { … }` |
| `ReadAction.nonBlocking { … }.inSmartMode(p).submit(executor)` | `smartReadAction(project) { … }` |
| `WriteAction.run { … }` (already on EDT) | `edtWriteAction { … }` |
| `WriteCommandAction.runWriteCommandAction(project) { … }` | `writeCommandAction(project, "name") { … }` |
| `ProgressManager.run(Task.Backgroundable…)` | `cs.launch { withBackgroundProgress(project, title) { reportProgress(N) { r -> … } } }` |
| `ProgressManager.runProcessWithProgressSynchronously(…)` | `cs.launch { withModalProgress(project, title) { … } }`, or keep classic if you must stay on the EDT and block |
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
- `invokeLater + WriteCommandAction.runWriteCommandAction` collapses into a single suspending
  `writeCommandAction(project, name) { }`.
- The EDT hop is implicit in `writeCommandAction` (which acquires the EDT-bound write lock).
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
