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
| `kotlinx.coroutines.runBlocking { }` (raw) | Keep the call chain suspending; only when a cancellable blocking bridge is unavoidable, use `runBlockingCancellable { }` under an existing Job/indicator on BGT |

The `Application` / `Project` scope getters are `@ApiStatus.Internal` / `@Obsolete`. They
survive plugin unload and leak the classloader. See `02_runtime_services.md` and
`04_threading_coroutines_2024.md` for the supported coroutine-scope pattern.

For action-owned work, use `AnActionEvent.coroutineScope` on 2026.1+,
`currentThreadCoroutineScope()` on 2024.2–2025.3, or a service-injected scope on 2024.1.
The event property is public in `idea/2026.2.2`; its installer is internal and forbidden.

### Action API drift

| Old | Use instead |
|---|---|
| Omitting `getActionUpdateThread()` | Required since 2022.3; pick `BGT` or `EDT` explicitly — see `02_runtime_actions.md` |
| `update()` doing PSI walking / index queries | Move work into a service called from `actionPerformed`; keep `update` cheap — see `02_runtime_actions.md` |
| `ExtensionNotApplicableException.INSTANCE` | `ExtensionNotApplicableException.create()` — see `01_core_extensions.md` |
| Storing per-invocation state on `AnAction` fields | Forbidden — actions are IDE-lifetime singletons; put state in a service — see `02_runtime_actions.md` |
| Calling deprecated `AnActionEvent.getRequiredData()` | Read with `getData(...)` and re-check null in `actionPerformed`; do not rely on a prior `update()` call |

### Threading migration drift

| Existing behavior | Behavior-preserving migration |
|---|---|
| EDT `WriteAction.run { ... }` or an older EDT-switching `writeAction` | `edtWriteAction { ... }` on 2025.1+ |
| Pure Swing work on `Dispatchers.Main` | `Dispatchers.UI` on 2025.3+; both are EDT paths without Write Intent in current versions |
| Model work on `Dispatchers.Main` | `Dispatchers.EDT` when EDT is required, or `Dispatchers.Default` plus explicit `readAction`/`writeAction` |
| Deprecated `readAndWriteAction` | `readAndEdtWriteAction` to preserve its EDT write phase; choose the background variant only after a BGT-safety audit |

At tag `idea/2026.2.2` (commit
`1c7e601c0423e544917046c23763b15d0282e2a3`), public `writeAction` delegates to public
`backgroundWriteAction`. This differs from its 2024.1-era EDT behavior. See the source and
status links in `04_threading_coroutines_2024.md` before applying a mechanical replacement.

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
