# Background Work and Progress

## Background work — `Task.Backgroundable` (classic)

The pre-coroutine pattern for "user clicked something, do work in the background with
progress and cancellation":

```kotlin
object : Task.Backgroundable(project, "Analyzing files", /* canBeCancelled = */ true) {
  override fun run(indicator: ProgressIndicator) {
    indicator.text = "Collecting files…"
    val files = collectFiles()

    indicator.isIndeterminate = false
    files.forEachIndexed { i, f ->
      indicator.checkCanceled()
      indicator.fraction = i.toDouble() / files.size
      indicator.text2 = f.name
      process(f)
    }
  }
  override fun onSuccess() { Messages.showInfoMessage(project, "Done", "Analysis") }
  override fun onCancel()    { /* user pressed cancel */ }
  override fun onThrowable(error: Throwable) { /* logged automatically; override if needed */ }
}.queue()
```

- `Task.Backgroundable` — status-bar progress, IDE remains usable.
- `Task.Modal` — blocking modal progress dialog.
- `Task.WithResult<R, E>` — modal task with a return value (`@Obsolete` — prefer
  `withModalProgress` in coroutine code).

`task.queue()` is exactly equivalent to `ProgressManager.getInstance().run(task)`.

`run(indicator)` runs on a BGT. `onSuccess`/`onCancel`/`onThrowable`/`onFinished` run on
the EDT.

### `ProgressIndicator`

```kotlin
indicator.text  = "Top line"
indicator.text2 = "Secondary line"
indicator.isIndeterminate = false
indicator.fraction = 0.0..1.0
indicator.checkCanceled()
indicator.isCanceled       // poll without throwing
```

Call `checkCanceled()` at the top of every loop iteration and at every meaningful step.
The Plugin DevKit "Cancellation check in loops" inspection enforces this.

### Synchronous run-with-progress

When a piece of UI must wait for the result before continuing:

```kotlin
val ok = ProgressManager.getInstance().runProcessWithProgressSynchronously(
  Runnable {
    ProgressManager.checkCanceled()
    /* work */
  },
  "Analyzing", /* canBeCancelled = */ true, project
)
```

Must be called on the EDT. Returns `false` if cancelled.

### Fire-and-forget

For brief, non-progress work:

```kotlin
ApplicationManager.getApplication().executeOnPooledThread {
  /* short BGT task */
}
```

For scheduled / repeating work, use `AppExecutorUtil.getAppScheduledExecutorService()`.

**Never** create your own `Executors.newFixedThreadPool(...)` or raw `Thread`. They survive
plugin unload, leaking threads and the classloader. Use `AppExecutorUtil` or, on 2024.1+, a
service-injected `CoroutineScope`.
