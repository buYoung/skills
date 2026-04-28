# Disposer and lifecycle

## Contents

- The shape of the tree
- Choose the right parent — every other rule reduces to this
  - Forbidden: `Application` and `Project` as parents
- Common patterns
  - Service as parent for its own internal subscriptions
  - Dialog-scoped resource
  - Tool-window-tab-scoped resource
  - Manual scope you control
  - `Alarm` for debounce / delayed work
- `dispose()` contract
- Disposal triggers — when does each parent actually dispose?


The IntelliJ Platform has no destructors and no `finalize()`. Every resource that needs
cleanup is wired into a `Disposable` tree, and the platform calls `dispose()` post-order
when a parent goes away. Read this when adding listeners, alarms, custom executors, file
watchers, swing components that own model state, or anything else with a meaningful end of
life.

## The shape of the tree

```kotlin
interface Disposable {
  fun dispose()
}

Disposer.register(parent, child)         // parent's disposal triggers child's
Disposer.dispose(disposable)             // explicit disposal (children also disposed)
val handle = Disposer.newDisposable("name")  // manual scope you own
```

Disposal proceeds **post-order**: grandchildren first, then children, then the parent
itself. An exception in one branch is logged but does not abort sibling disposals — so a
buggy `dispose()` cannot poison the rest of the tree, but it can still leak its own subtree.

## Choose the right parent — every other rule reduces to this

Resource lifetime maps directly to the parent disposable. The single most consequential
decision is which parent you pick.

| Resource lives until… | Use as parent |
|---|---|
| The IDE shuts down or the plugin is unloaded | A light **application service** (`@Service`) you own |
| The user closes a project, or the plugin is unloaded | A light **project service** (`@Service(Service.Level.PROJECT)`) you own |
| The dialog closes | `DialogWrapper.getDisposable()` |
| The tool window tab closes | `Content` (the tab itself) — `Disposer.register(content, child)` |
| A specific operation completes | `Disposer.newDisposable("op")`, disposed by you when done |

### Forbidden: `Application` and `Project` as parents

```kotlin
// BAD — both lines.
Disposer.register(ApplicationManager.getApplication(), myDisposable)
Disposer.register(project, myDisposable)
```

Their lifetimes are the IDE / project lifetime, not your plugin's. When your plugin is
dynamically unloaded, neither parent disposes, so your `dispose()` is never called and the
plugin classloader cannot be GC'd. Always use a parent **your plugin controls**.

The platform offers helpers like `Application.getMessageBus().connect(...)`; pass the
disposable parent there too — `connect(applicationService)` or `connect(projectService)`.

## Common patterns

### Service as parent for its own internal subscriptions

```kotlin
@Service(Service.Level.PROJECT)
class MyProjectService(project: Project) : Disposable {
  init {
    project.messageBus.connect(this)
      .subscribe(ToolWindowManagerListener.TOPIC, MyTwListener())
  }

  override fun dispose() {
    // Optional explicit cleanup. The MessageBusConnection above is
    // already a child of `this`, so it is auto-disconnected.
  }
}
```

### Dialog-scoped resource

```kotlin
class MyDialog : DialogWrapper(true) {
  init {
    init()
    val alarm = Alarm(Alarm.ThreadToUse.SWING_THREAD, disposable)  // disposable = getDisposable()
    alarm.addRequest({ /* … */ }, 1000)
  }
}
```

### Tool-window-tab-scoped resource

```kotlin
val content = ContentFactory.getInstance().createContent(panel, "Tab", false)
Disposer.register(content, myDisposable)
toolWindow.contentManager.addContent(content)
```

### Manual scope you control

```kotlin
val scope = Disposer.newDisposable("my-op")
Disposer.register(scope, sub1)
Disposer.register(scope, sub2)
try {
  doWork(scope)
} finally {
  Disposer.dispose(scope)
}
```

### `Alarm` for debounce / delayed work

```kotlin
val alarm = Alarm(Alarm.ThreadToUse.POOLED_THREAD, parentDisposable)
alarm.addRequest({ /* … */ }, 500)
alarm.cancelAllRequests()
```

`Alarm` cancels all queued requests when its parent disposes.

## `dispose()` contract

Three rules:

1. **Idempotent.** Multiple disposal can happen due to platform retries; do not crash if
   already disposed.
2. **Fast.** `dispose()` runs on whichever thread triggered disposal. A slow `dispose()`
   delays everything queued behind it.
3. **No exceptions.** Throwing aborts your subtree's disposal and litters the log. Catch and
   log inside `dispose()`.

## Disposal triggers — when does each parent actually dispose?

| Parent | Disposal trigger |
|---|---|
| `@Service` (APP) | IDE shutdown OR plugin unload |
| `@Service` (PROJECT) | Project close OR plugin unload |
| `DialogWrapper.getDisposable()` | Dialog close (any reason) |
| `Content` (tool window tab) | Tab close, tool window unregister, content manager dispose |
| `Disposer.newDisposable()` | When you call `Disposer.dispose(...)` |
| Plugin descriptor disposable (do not use directly) | Plugin unload |

Note: **extensions do not auto-dispose**. Extensions are stateless by rule, so they should
not own resources. Any resource you might be tempted to put on an extension belongs in a
service, with the extension reading from it.
