# Leak Diagnostics

## Debugging leaks

### `-Didea.disposer.debug=on`

Add this JVM option in your run/sandbox configuration. Disposer records the stack trace of
every disposal, which you can later read via:

```kotlin
val trace: Throwable? = Disposer.getDisposalTrace(suspectDisposable)
```

Useful when an object is unexpectedly already disposed (or unexpectedly still alive after
its parent disposed).

### `LeakHunter` (test framework)

```kotlin
LeakHunter.checkProjectLeak()
LeakHunter.checkNonDefaultProjectLeak()
```

Walks the heap for the leaked object's reachable references. Used in IntelliJ's own tests;
worth adopting in plugin tests when you suspect long-lived references.

### `Disposer.assertIsEmpty()`

Test-only assertion that all `Disposer.newDisposable()` instances created during the test
have been disposed. `UsefulTestCase.tearDown` calls it automatically.

### Plugin Verifier

The `verifyPlugin` Gradle task (2.x) flags some classes of leaks (e.g., usage of internal APIs that prevent
unload) at build time. It does not catch all runtime leaks but catches a useful subset.

### Manual sandbox check

In `runIde`, install your plugin once, exercise the feature, then go to
`Settings | Plugins | Installed | <your plugin> | Disable`. If a class loaded by the plugin
classloader is still strongly referenced from elsewhere, the IDE warns:

> Plugin '…' was not unloaded successfully. Please restart …

That message is the canonical "I'm leaking something" signal in development.

## Common mistakes

- Picking `application` or `project` as parent. Forbidden — see `03_lifecycle_disposer.md`.
- Forgetting to pass a parent to `messageBus.connect()`. The connection lives forever and
  blocks plugin unload.
- Same `Disposable` registered under two parents. It will dispose twice; ensure your
  `dispose()` is idempotent.
- Heavy `dispose()` (e.g., flushing big buffers synchronously). Move it off-thread or split
  it.
- Service is `Disposable`, but `dispose()` re-creates resources (typo / confusion with
  reset). It is end-of-life only.

## Related references

- `02_runtime_services.md` — services as parents, declarative-listener lifetime.
- `04_threading_model.md` — `CoroutineScope` injection details, cancellation semantics.
- `11_distribution_deployment_checklist.md` — full dynamic-plugin checklist.
