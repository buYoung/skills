# Threading Diagnostics

## Diagnostics — common threading symptoms

| Symptom | Likely cause |
|---|---|
| "Read access is allowed from inside read-action only" | You're reading PSI/VFS without a Read Action. Wrap in `ReadAction.compute { }` / `readAction { }`. |
| "Write access is allowed from event dispatch thread only" | You're writing on a BGT. Hop to EDT (`invokeLater` + `WriteAction.run`) or use `writeAction`/`backgroundWriteAction`. |
| "Slow operations are prohibited on EDT" | You ran heavy work on the EDT. Move to `Task.Backgroundable` or `cs.launch`. |
| IDE "freezes" briefly | Long Read or Write on EDT, or long Read on BGT blocking incoming Writes. Use `nonBlocking` / suspending `readAction`. |
| Cancellation seems ignored | A `catch (Throwable)` or `catch (Exception)` block is swallowing PCE/`CancellationException`. Re-throw it. |
| Modal dialog reorders work strangely | `Dispatchers.Main` instead of `Dispatchers.EDT`, or wrong `ModalityState` on `invokeLater`. |
| Unrelated "Plugin … was not unloaded successfully" | A raw `Thread` / custom `ExecutorService` / `GlobalScope` / `Application.getCoroutineScope()` survived. Replace with injected `cs` or `AppExecutorUtil`. |
| Indexes missing in a coroutine's read | Use `smartReadAction` or `constrainedReadAction(ReadConstraint.inSmartMode(project)) { }`. |
| `runBlockingCancellable` deadlocks | You called it on the EDT. Move the call site to a BGT or rewrite as a coroutine. |

## Common mistakes

- `Dispatchers.Main` instead of `Dispatchers.EDT`.
- Catching `Exception`/`Throwable` and not re-throwing `CancellationException` /
  `ProcessCanceledException`.
- `WriteAction.run` from a BGT (legal only via `backgroundWriteAction { }`).
- Holding `readAction { … }` open for many seconds — every Write restarts it. Break work
  into smaller reads, or use `smartReadAction` and reportProgress.
- Mutating a field from inside a `readAction` (the block is supposed to be idempotent).
- Using `Application.getCoroutineScope()` / `Project.getCoroutineScope()`. Inject a scope
  via a service.
- `runBlocking { … }` (kotlinx) inside the IDE. Use `runBlockingCancellable` and only on BGT.
- A `Task.Backgroundable.run()` that touches Swing directly. Hop to EDT for any UI work.

## Best practice

- New code: coroutines, service-injected `CoroutineScope`, `readAction`/`writeAction`/
  `writeCommandAction`/`smartReadAction`, `withBackgroundProgress`.
- Annotate public methods with `@RequiresEdt` / `@RequiresBackgroundThread` /
  `@RequiresReadLock` / `@RequiresWriteLock`. Saves the next maintainer hours of debugging.
- Treat PCE / `CancellationException` as control flow. Always re-throw, never log it as
  error.
- Avoid creating your own threads or executors. The platform provides everything you need.
- For >100ms work triggered by a user action, use a progress-reporting background path.
  Anything less and you can keep it inline on the EDT, but err on the side of background.
- Keep `update()` cheap (`getActionUpdateThread() = BGT` and millisecond-level work).

## Import map for the suspending APIs

The platform's coroutine surface is spread across a few packages; pulling them all in by
hand is the most common newcomer pitfall. Use this as a copy-paste header for new files.

```kotlin
// Read / write actions
import com.intellij.openapi.application.readAction
import com.intellij.openapi.application.smartReadAction
import com.intellij.openapi.application.constrainedReadAction
import com.intellij.openapi.application.writeAction
import com.intellij.openapi.application.edtWriteAction
import com.intellij.openapi.application.backgroundWriteAction
import com.intellij.openapi.application.writeIntentReadAction
import com.intellij.openapi.application.readAndEdtWriteAction
import com.intellij.openapi.application.readAndBackgroundWriteAction

// Command (undo-able) writes
import com.intellij.openapi.command.writeCommandAction

// Progress + cancellation
import com.intellij.platform.ide.progress.withBackgroundProgress
import com.intellij.platform.ide.progress.withModalProgress
import com.intellij.platform.util.progress.reportProgress
import com.intellij.openapi.progress.runBlockingCancellable

// Threading assertions / annotations
import com.intellij.util.concurrency.annotations.RequiresEdt
import com.intellij.util.concurrency.annotations.RequiresBackgroundThread
import com.intellij.util.concurrency.annotations.RequiresReadLock
import com.intellij.util.concurrency.annotations.RequiresWriteLock
import com.intellij.util.concurrency.ThreadingAssertions

// Legacy executor pool (when you need a non-coroutine background thread)
import com.intellij.util.concurrency.AppExecutorUtil
```

## Related references

- `02_runtime_services.md` — `@Service` + `CoroutineScope` injection pattern.
- `03_lifecycle_disposer.md` — why `CoroutineScope` injection replaces `Disposable`.
- `05_file_model_psi_basics.md` — what *can* be read/written, and what `WriteCommandAction` covers.
- `06_code_insight_diagnostics.md` — provider-specific threading and dumb-mode checks.
