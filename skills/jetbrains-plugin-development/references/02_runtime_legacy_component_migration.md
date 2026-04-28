# Legacy Component Migration

## Deprecated and discouraged patterns

A consolidated map of "don't do this any more" calls in this domain. Most of the *why* is
covered in `02_runtime_services.md`, `02_runtime_listeners_message_bus.md`, and `02_runtime_actions.md`; this section is a
quick checklist before declaring work done, plus the one big migration this skill doesn't
otherwise spell out — the legacy Components API.

### Components — replaced by services, extensions, and listeners

The legacy `ApplicationComponent` / `ProjectComponent` / `ModuleComponent` interfaces (and
their `<application-components>` / `<project-components>` / `<module-components>` XML
blocks) are obsolete. Reasons they're gone in new code:

- They eagerly initialise on container creation, so every plugin pays the cost up front.
- They cannot be unloaded; their presence forces plugins to require a restart.
- They share a single inheritance hierarchy, making composition and lazy lookup awkward.
- `projectOpened` / `projectClosed` ran on the EDT and routinely caused freezes.

Migration map:

| Old Component role | New equivalent | Reference |
|---|---|---|
| State holder with `initComponent` / `disposeComponent` | `@Service` light service (lazy + scoped + disposable) | `02_runtime_services.md` |
| Implementing a platform interface across all projects | Extension point implementation (no shared base class needed) | `01_core_extensions.md` |
| Reacting to platform events | Declarative listener (`<applicationListeners>` / `<projectListeners>`) | `02_runtime_listeners_message_bus.md` |
| Long-lived background work tied to project lifetime | `@Service` + injected `CoroutineScope` | `02_runtime_services.md`, `04_threading_coroutines_2024.md` |
| `projectOpened` / `projectClosed` callbacks | Suspending `ProjectActivity` registered via `<postStartupActivity>` / `<backgroundPostStartupActivity>`, or `ProjectManagerListener` | `09_project_lifecycle.md`, `02_runtime_listeners_message_bus.md` |

A `ProjectComponent` with `initComponent` setup and `projectOpened` per-project work
becomes:

```kotlin
@Service(Service.Level.PROJECT)
class MyProjectFeature(
  private val project: Project,
  private val cs: CoroutineScope,
) {
  // initComponent body → constructor work or lazy init on first getInstance()
  fun bootstrap() { /* … */ }
  // disposeComponent body → cs cancellation handles cleanup automatically
}

class MyProjectStartupActivity : ProjectActivity {
  override suspend fun execute(project: Project) {
    // projectOpened body, suspending — runs off the EDT after project open
    project.service<MyProjectFeature>().bootstrap()
  }
}
```

```xml
<extensions defaultExtensionNs="com.intellij">
  <postStartupActivity implementation="com.example.MyProjectStartupActivity"/>
</extensions>
```

Components remain *legible* in the API for backwards compatibility, but new plugins should
not register them. Plugin DevKit's "Component can be replaced with service / startup
activity" inspection flags every remaining one and offers a quick fix.
