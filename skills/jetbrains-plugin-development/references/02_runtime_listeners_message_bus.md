# Listeners and Message Bus

## Contents

- Listeners and the message bus
  - Declarative listeners
  - Frequently used topics
  - Manual subscription via `MessageBusConnection`
  - Listener vs service vs extension


## Listeners and the message bus

Two layers:
- **Message bus** — the platform's pub/sub infrastructure, organized in an Application bus
  and per-Project buses.
- **Declarative listeners** — convenience syntax in `plugin.xml` that registers a class
  against a `Topic`. Lazily instantiated on first event.

Use declarative listeners by default. Use manual `MessageBusConnection` only when the
subscription must come and go dynamically (e.g., subscribed only while a tool window is
visible).

### Declarative listeners

```xml
<applicationListeners>
  <listener class="com.example.MyVfsListener"
            topic="com.intellij.openapi.vfs.newvfs.BulkFileListener"/>
</applicationListeners>

<projectListeners>
  <listener class="com.example.MyToolWindowListener"
            topic="com.intellij.openapi.wm.ex.ToolWindowManagerListener"
            activeInTestMode="false"/>
</projectListeners>
```

Attributes:

| Attribute | Meaning |
|---|---|
| `class` | implementation FQN |
| `topic` | topic interface FQN |
| `activeInTestMode` | also fire in test mode (default `false`) |
| `os` | OS gate |

Listener class rules:

1. **Stateless** — exactly the same reasoning as for extensions.
2. **Do NOT implement `Disposable`** — Plugin DevKit's "Listener implementation implements
   'Disposable'" inspection flags this. The platform manages listener lifetime.
3. **Lazy instantiation** — created on first matching event, not at plugin load.
4. **Project listeners may take a `Project` constructor parameter** when project context is
   needed:
   ```java
   final class MyToolWindowListener implements ToolWindowManagerListener {
     private final Project project;
     MyToolWindowListener(Project project) { this.project = project; }
     @Override public void stateChanged(@NotNull ToolWindowManager mgr) { /* ... */ }
   }
   ```

### Frequently used topics

| Topic | Fires on |
|---|---|
| `BulkFileListener` (`com.intellij.openapi.vfs.newvfs.BulkFileListener`) | Batched VFS changes |
| `FileDocumentManagerListener` | Document save / reload |
| `ToolWindowManagerListener` (in `wm.ex` — semi-public) | Tool window state changes |
| `ProjectManagerListener` | Project open/close |
| `DynamicPluginListener` | Other plugins load/unload |
| `EditorColorsListener` | Color scheme changes |
| `ModuleRootListener` | Module roots changed |
| `PsiTreeChangeListener` | PSI mutations — **very chatty**; use only with manual subscription on a tight scope |

### Manual subscription via `MessageBusConnection`

```kotlin
// Define a topic
interface MyChangeListener {
  fun onChanged(newValue: String)

  companion object {
    @Topic.AppLevel
    val TOPIC: Topic<MyChangeListener> =
      Topic.create("My Change Topic", MyChangeListener::class.java)
  }
}

// Subscribe
val bus = ApplicationManager.getApplication().messageBus
bus.connect(parentDisposable)
   .subscribe(MyChangeListener.TOPIC, object : MyChangeListener {
     override fun onChanged(newValue: String) { /* ... */ }
   })

// Or with a coroutine scope (auto-disconnects when scope cancels)
bus.connect(cs)
   .subscribe(MyChangeListener.TOPIC, handler)

// Publish (synchronous on the publishing thread)
bus.syncPublisher(MyChangeListener.TOPIC).onChanged("new value")
```

`@Topic.AppLevel` versus `@Topic.ProjectLevel` selects the bus. `broadcastDirection` on
`Topic` controls whether messages flow `TO_CHILDREN` (default — app-level publishes also
reach project-level subscribers), `TO_PARENT`, or `NONE`.

**Always pass a parent to `connect(...)`** — `parentDisposable`, the service's `this`
(if `Disposable`), or an injected `CoroutineScope`. A bare `connect()` with no parent
requires a manual `disconnect()` and is an easy leak source. Plugin DevKit warns about it.

### Listener vs service vs extension

Quick disambiguation when designing a new feature:

- **Need to react to platform events?** Listener.
- **Need to hold mutable state?** Service.
- **Need to implement an interface the platform calls based on context (a file type, a
  language, a PSI element)?** Extension.

A common composition: declarative listener delegates immediately to a service that owns the
state and the work.

```kotlin
class MyVfsListener : BulkFileListener {
  override fun after(events: List<VFileEvent>) {
    MyApplicationService.getInstance().handle(events)
  }
}
```
