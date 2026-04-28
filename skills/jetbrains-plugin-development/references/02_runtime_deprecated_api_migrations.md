# Deprecated API Migrations

## Common mistakes (cross-cutting)

- Putting state on an `AnAction` field (forbidden) or on an extension instance (forbidden).
  State always goes in a service.
- Subscribing to `PsiTreeChangeListener` declaratively. The traffic is huge; only subscribe
  manually within a scoped Disposable / `CoroutineScope` and only while needed.
- Constructor-injecting other services into a service. Look them up at call time.
- Forgetting `getActionUpdateThread()`. The default is EDT, which is wrong for nearly every
  new action.
- `bus.connect()` without a parent. Subscribe with `connect(disposable)` / `connect(cs)` and
  the platform takes care of cleanup.

### Listener anti-patterns — pointers to where each is covered

| Anti-pattern | Why it's wrong | Where covered |
|---|---|---|
| Manual `bus.connect()` with no parent | Subscription outlives the plugin → leak | `02_runtime_listeners_message_bus.md` |
| Listener implements `Disposable` | The platform manages listener lifetime; flagged by Plugin DevKit | `02_runtime_listeners_message_bus.md` |
| Listener stores mutable state on instance fields | Instance shared across events/threads → race conditions | `02_runtime_listeners_message_bus.md` |
| `PsiTreeChangeListener` registered declaratively | Event volume is huge — tanks IDE responsiveness | `02_runtime_listeners_message_bus.md` |
| Subscribing in a service constructor | Listener fires before the service finishes constructing → ordering hazards | `02_runtime_services.md` |

For listeners whose lifetime matches a service, prefer
`bus.connect(cs).subscribe(TOPIC, handler)` over `bus.connect(this).subscribe(...)` — the
injected `CoroutineScope` cancels for free on service disposal and makes the lifetime
explicit. See `02_runtime_services.md`.

### Coroutine scope APIs — replaced by injection

| Don't call | Use instead |
|---|---|
| `Application.getCoroutineScope()` | `@Service`-injected `CoroutineScope` (constructor parameter) |
| `Project.getCoroutineScope()` | Project `@Service`-injected `CoroutineScope` |
| `kotlinx.coroutines.GlobalScope` | Same — never `GlobalScope` from a plugin |
| `kotlinx.coroutines.runBlocking { }` (raw) | `runBlockingCancellable { }` from `com.intellij.openapi.progress` (BGT only — never EDT) |

The `Application` / `Project` scope getters are `@ApiStatus.Internal` / `@Obsolete`. They
survive plugin unload and leak the classloader. See `02_runtime_services.md` and
`04_threading_coroutines_2024.md` for the supported coroutine-scope pattern.

### Action API drift

| Old | Use instead |
|---|---|
| Omitting `getActionUpdateThread()` | Required since 2022.3; pick `BGT` or `EDT` explicitly — see `02_runtime_actions.md` |
| `update()` doing PSI walking / index queries | Move work into a service called from `actionPerformed`; keep `update` cheap — see `02_runtime_actions.md` |
| `ExtensionNotApplicableException.INSTANCE` | `ExtensionNotApplicableException.create()` — see `01_core_extensions.md` |
| Storing per-invocation state on `AnAction` fields | Forbidden — actions are IDE-lifetime singletons; put state in a service — see `02_runtime_actions.md` |

### Plugin DevKit inspections that catch most of the above

Run these (all enabled by default in `Settings | Editor | Inspections | Plugin DevKit | Code`):

- "Component can be replaced with service / startup activity"
- "Listener implementation implements 'Disposable'"
- "Non-default constructors for service and extension class"
- "Cancellation check in loops"
- "Plugin XML errors"
- "Statement effect" (catches missed cancellation re-throws)

If a changed file shows green for all of the above, the listener/service/action
correctness floor is met.
