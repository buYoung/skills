# Services

## Contents

- Services — where mutable state lives
  - Light services (default for new code)
  - Constructor rules (strictly enforced)
  - `CoroutineScope` injection — the modern lifecycle pattern
  - `Disposable` services
  - Persistent state


Services hold mutable state and own long-lived work for a plugin. Read this when writing or
modifying an application, project, or module service.

## Services — where mutable state lives

A service is a **scoped singleton**. There are three scopes — `APP`, `PROJECT`, `MODULE`.
Each scope has at most one instance per container, lazily created on first `getService(...)`.

Module-scoped services exist but are usually a poor design choice for moderately large
projects: a project with hundreds of modules will materialize hundreds of instances. Prefer
a project-scoped service plus a `Map<Module, ...>` if you genuinely need per-module data.

### Light services (default for new code)

```kotlin
@Service(Service.Level.APP)
class MyApplicationService {
  fun doSomething(input: String) { /* ... */ }

  companion object {
    fun getInstance(): MyApplicationService =
      ApplicationManager.getApplication().getService(MyApplicationService::class.java)
  }
}

@Service(Service.Level.PROJECT)
class MyProjectService(private val project: Project) {
  fun findSomething(): List<String> = /* ... */ emptyList()

  companion object {
    fun getInstance(project: Project): MyProjectService =
      project.getService(MyProjectService::class.java)
  }
}
```

A light service:
- Is registered by the `@Service` annotation alone — **no `<applicationService>`/`<projectService>` in plugin.xml**.
- Must be a `final` `class` (not Kotlin `object`, not `open`).
- Cannot be overridden via the `overrides=true` mechanism.
- May declare both scopes simultaneously: `@Service(Service.Level.APP, Service.Level.PROJECT)`.

If you need to override a platform service, fall back to the legacy XML registration:

```xml
<extensions defaultExtensionNs="com.intellij">
  <applicationService serviceInterface="com.example.MyService"
                      serviceImplementation="com.example.MyServiceImpl"/>
  <projectService    serviceImplementation="com.example.MyProjectServiceImpl"
                     os="windows"/>
</extensions>
```

`<applicationService>`/`<projectService>` attributes worth knowing:

- `serviceInterface` / `serviceImplementation`
- `os` — `windows`, `mac`, `linux`, `freebsd`, `unix`
- `client` — separate instance per client kind for Code With Me / Remote Dev: `local`,
  `controller`, `guest`, `remote`, `all`
- `overrides="true"` — replaces a platform service implementation. Forbidden in dynamic plugins.

### Constructor rules (strictly enforced)

Allowed parameters:
- nothing
- `Project` (project-scoped service only)
- `Module` (module-scoped service only)
- `CoroutineScope` (light services on 2024.1+) — yields a scope tied to the service's lifetime

```kotlin
@Service(Service.Level.PROJECT)
class MyProjectService(
  private val project: Project,
  private val cs: CoroutineScope,
)
```

Forbidden:
- **Other services as constructor parameters.** Constructor injection of services is
  unsupported. Look up dependencies on demand via `OtherService.getInstance(...)`.
- **Heavy initialization** — file I/O, network, transitive service lookups. The first caller
  pays the entire cost; that caller might be the EDT.
- **Listener registration in the constructor** — same problem. Use declarative listeners or
  register lazily on first use.

The Plugin DevKit inspection "Non-default constructors for service and extension class"
catches violations.

### `CoroutineScope` injection — the modern lifecycle pattern

When the service receives a `CoroutineScope` parameter, the platform supplies a scope that
is automatically cancelled when the service is disposed (project close or plugin unload).
This replaces manual `Disposable` wiring for almost all "long-lived background work" cases.

```kotlin
@Service
class MyService(private val cs: CoroutineScope) {
  fun fetchInBackground(query: String) {
    cs.launch {
      val result = withContext(Dispatchers.IO) { httpClient.get(query) }
      val parsed  = readAction { parseAndResolve(result) }
      withContext(Dispatchers.EDT) { showResult(parsed) }
    }
  }
}
```

The injected scope is the only correct scope to use inside a service:

- `Application.getCoroutineScope()` and `Project.getCoroutineScope()` are
  `@ApiStatus.Internal`/`Obsolete` — do not call them from plugins.
- `GlobalScope` is forbidden — it survives plugin unload and leaks the classloader.
- Take care with `init { cs.launch { … } }` — the service instance is not yet returned to
  the caller, so referencing `this` from inside the launched coroutine creates ordering
  hazards. Prefer launching from explicit external triggers.

Do not route every action through a service merely to obtain a scope. For directly launched
action work, use the Action System-owned public API for the minimum target:
`e.coroutineScope` on 2026.1+, documented `currentThreadCoroutineScope()` on
2024.2–2025.3, and an injected service scope on 2024.1. The 2026.1 property remains valid for
the action lifetime chosen by Action System; do not cache it outside `actionPerformed`.

### `Disposable` services

A service can implement `Disposable`. The platform calls `dispose()` when the service goes
out of scope. Use `this` as the parent for `Disposer.register(this, child)` only when the
service implements `Disposable` (otherwise the relationship is implicit but unclear). For
`MessageBusConnection`, `connect(this)` works regardless.

For service-lifetime bus subscriptions, prefer `bus.connect(cs).subscribe(...)` when the
service already receives an injected `CoroutineScope`. Service disposal cancels the scope,
which cancels the message-bus connection and any child coroutines under the same lifetime.

If you have a `CoroutineScope` injected, you usually do **not** also need to implement
`Disposable` — the scope cancellation handles cleanup. Keep `Disposable` only for
non-coroutine resources (for example native handles or custom threads), or when you need a
child lifetime such as per-document state parented under the service. See
`03_lifecycle_disposer.md`.

### Persistent state

Services that need to persist across IDE restarts implement `PersistentStateComponent`.
See `08_ui_settings_persistent_state.md`.

## Fixed-source evidence

Service scope guidance follows the official coroutine-scope contract. The 2026.1 action
scope and 2026.2.2 public declaration are recorded in:

- [Coroutine Scopes](https://plugins.jetbrains.com/docs/intellij/coroutine-scopes.html)
- [Launching Coroutines](https://plugins.jetbrains.com/docs/intellij/launching-coroutines.html)
- [`AnActionEvent.java` at `idea/2026.2.2`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/editor-ui-api/src/com/intellij/openapi/actionSystem/AnActionEvent.java)
- [`MessageBus.kt` at `idea/2026.2.2`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/extensions/src/com/intellij/util/messages/MessageBus.kt)

`AnActionEvent.getCoroutineScope()` and service constructor injection are external public
contracts. `MessageBus.connect(CoroutineScope)` is also public and unannotated at the pinned
commit. `AnActionEvent.installCoroutineScope()` and platform scope-holder implementations are
internal and must not be called, reflected into, or cast to.
