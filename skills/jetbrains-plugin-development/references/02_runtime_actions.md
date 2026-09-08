# Actions

## Contents

- Actions
  - Anatomy of an `AnAction`
  - `update(AnActionEvent)` — must be cheap
  - `getActionUpdateThread()` (2022.3+)
  - Field-on-AnAction is forbidden
  - Registering in `plugin.xml`
  - Action groups
  - `DumbAwareAction`
  - Reading context from `AnActionEvent`
  - Long work in `actionPerformed`
- Lifecycle of these three components
- End-to-end skeletons in this skill


## Actions

Actions are user-triggered commands: menu items, toolbar buttons, keyboard shortcuts,
context menus.

### Anatomy of an `AnAction`

```kotlin
class MyAction : AnAction() {
  override fun actionPerformed(e: AnActionEvent) {
    val project = e.project ?: return
    Messages.showInfoMessage(project, "Hello!", "My Action")
  }

  override fun update(e: AnActionEvent) {
    e.presentation.isEnabledAndVisible = e.project != null
  }

  override fun getActionUpdateThread(): ActionUpdateThread = ActionUpdateThread.BGT
}
```

### `update(AnActionEvent)` — must be cheap

`update` runs frequently: every menu open, every toolbar repaint, every key-routing pass.
Do **not** read the file system, hit the network, query indexes, or walk PSI here. Evaluate
trivial conditions on the supplied `AnActionEvent` data only.

`e.presentation` controls the user-visible side: `isEnabled`, `isVisible`,
`isEnabledAndVisible`, `text`, `description`, `icon`. Setting visibility off is preferable
to disabling for actions that are simply not applicable in the current context.

### `getActionUpdateThread()` (2022.3+)

Tells the platform whether to dispatch `update` on `BGT` (preferred for new code) or `EDT`.

| Value | Use when | Available |
|---|---|---|
| `BGT` | Most new actions | PSI, VFS, project model (read action implicit) |
| `EDT` | You must read live Swing component state (focus, tree selection, custom UI) | Swing UI state |

Implement it whenever `update` is overridden. Plugin DevKit reports a missing override.
Although 2026.2.2 returns BGT for an action whose `update` remains the default, an overridden
`update` still falls back to EDT. `actionPerformed` is invoked on EDT.

### Field-on-AnAction is forbidden

`AnAction` instances are singletons for the entire IDE lifetime. Storing per-invocation
state on a field is a race condition across projects/threads and a leak across plugin
unloads. Put state in a service and look it up from `actionPerformed`/`update`.

### Registering in `plugin.xml`

```xml
<actions>
  <action id="com.example.MyAction"
          class="com.example.MyAction"
          text="My Action"
          description="Does something useful"
          icon="MyIcons.ActionIcon">
    <add-to-group group-id="ToolsMenu" anchor="first"/>
    <add-to-group group-id="EditorPopupMenu" anchor="last"/>
    <keyboard-shortcut keymap="$default" first-keystroke="control alt A"/>
    <override-text place="MainMenu" text="Different Label"/>
  </action>
</actions>
```

Important details:

- `id` must be globally unique across **every plugin in the IDE**, not just yours. Convention:
  FQN. Duplicate ids break dynamic plugin loading.
- `<add-to-group>` can appear multiple times — same action shown in multiple places.
  Common group ids: `MainMenu`, `ToolsMenu`, `EditorPopupMenu`, `ProjectViewPopupMenu`,
  `MainToolbarLeft`, `EditorTabPopupMenu`, `ConsoleEditorPopupMenu`. The full list lives in
  `IdeActions` and platform/plugin XML files.
- Keyboard shortcuts: `keymap="$default"` applies to all keymaps. `keymap="$mac"` /
  `"Mac OS X 10.5+"` / `"Eclipse"` / etc. target specific keymaps. macOS modifiers: `meta` =
  Cmd, `control` = Ctrl. For chord shortcuts use `first-keystroke` + `second-keystroke`.
- `icon` references `AllIcons.*` directly or a field on a plugin icon class
  (`com.example.MyIcons.ActionIcon`). Typos silently fall back to the default icon —
  check `idea.log` if your icon is missing.
- `<override-text place="...">` lets the same action display different labels in different
  `ActionPlaces` (`MainMenu`, `EditorPopup`, `MainToolbar`, ...).

### Action groups

Static group:

```xml
<group id="com.example.MyGroup" text="My Submenu" popup="true">
  <action id="com.example.A1" class="com.example.A1" text="First"/>
  <action id="com.example.A2" class="com.example.A2" text="Second"/>
  <add-to-group group-id="ToolsMenu" anchor="last"/>
</group>
```

Dynamic group (children computed at runtime):

```kotlin
class MyDynamicGroup : ActionGroup() {
  override fun getChildren(e: AnActionEvent?): Array<AnAction> = arrayOf(A1(), A2())
  override fun getActionUpdateThread(): ActionUpdateThread = ActionUpdateThread.BGT
}
```

```xml
<group id="com.example.Dynamic" class="com.example.MyDynamicGroup"
       text="Dynamic Menu" popup="true">
  <add-to-group group-id="MainMenu" anchor="last"/>
</group>
```

Implement `getActionUpdateThread()` on `ActionGroup` too — `getChildren` may be called from
the same threading regime as `update`.

### `DumbAwareAction`

The IDE goes through a "Dumb Mode" indexing phase shortly after project open and after
significant changes. Non-Dumb-aware actions are disabled during this period. If your action
does **not** depend on indexes (no `FileBasedIndex` queries, no resolution requiring
indexes), extend `DumbAwareAction` so it remains usable.

```kotlin
class MyAction : DumbAwareAction("My Action") {
  override fun actionPerformed(e: AnActionEvent) { /* ... */ }
}
```

Same applies to many providers (`DumbAware` interface) — folding builders, line marker
providers, completion contributors. See `05_file_model_psi_basics.md` for the indexing model.

### Reading context from `AnActionEvent`

```kotlin
val project = e.project                                  // null on Welcome Screen
val editor  = e.getData(CommonDataKeys.EDITOR)
val vfile   = e.getData(CommonDataKeys.VIRTUAL_FILE)
val psiFile = e.getData(CommonDataKeys.PSI_FILE)
val element = e.getData(CommonDataKeys.PSI_ELEMENT)
val files   = e.getData(CommonDataKeys.VIRTUAL_FILE_ARRAY)
val nav     = e.getData(CommonDataKeys.NAVIGATABLE)
```

`getData(...)` returns null if absent. Re-check the precondition in `actionPerformed` because
the platform does not guarantee that `update()` ran with the same context immediately before
the action. `getRequiredData(...)` is deprecated for removal in 2026.2.2, so do not use it in
new code.

### Long work in `actionPerformed`

`actionPerformed` runs on the EDT. Move blocking or expensive work off the EDT:

```kotlin
override fun actionPerformed(e: AnActionEvent) {
  val project = e.project ?: return
  e.coroutineScope.launch { // 2026.1+
    val result = readAction { collectResult(project) }
    withContext(Dispatchers.UI) { showResult(result) } // 2025.3+, pure Swing UI
  }
}
```

`AnActionEvent.coroutineScope` is public from 2026.1 and lets Action System control the
launched work. Retrieve it only during `actionPerformed`; do not cache it. For
2024.2–2025.3 use the documented `currentThreadCoroutineScope()`. For 2024.1, call a service
method that launches from its injected scope. `Task.Backgroundable` remains the classic
public alternative.

See `04_threading_model.md` for the full progress/cancellation story.

### Fixed-source evidence

The action threading and coroutine contracts were checked against tag `idea/2026.2.2`,
commit `1c7e601c0423e544917046c23763b15d0282e2a3`:

- [`AnAction.java`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/editor-ui-api/src/com/intellij/openapi/actionSystem/AnAction.java)
- [`AnActionEvent.java`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/editor-ui-api/src/com/intellij/openapi/actionSystem/AnActionEvent.java)
- [`ActionUpdateThread.java`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/editor-ui-api/src/com/intellij/openapi/actionSystem/ActionUpdateThread.java)

The 2026.1 introduction of `AnActionEvent.coroutineScope` is recorded in the official
[2026 API changes](https://plugins.jetbrains.com/docs/intellij/api-notable-list-2026.html).

The recommended methods are public (`getActionUpdateThread` is override-only); the examples
do not call Action System implementation classes or internal scope installers.

## Lifecycle of these three components

| Stage | Service | Listener (declarative) | Action |
|---|---|---|---|
| Registration | `@Service` annotation OR `<*Service>` | `<applicationListeners>`/`<projectListeners>` | `<action>` / `<group>` in `<actions>` |
| Instantiated | first `getService(...)` | first matching event | first display, edit, or invocation |
| Cached for | scope lifetime | container lifetime | IDE / plugin lifetime |
| Destroyed | scope close, plugin unload | container close, plugin unload | plugin unload |

## End-to-end skeletons in this skill

- `examples/action_basics/` — `HelloAction.kt` (`AnAction` with `getActionUpdateThread`,
  `update`, `actionPerformed`), `DynamicGreetingsGroup.kt` (`ActionGroup` with computed
  children), and a `plugin.xml` that registers them under `ToolsMenu` with a keymap entry.
- `examples/settings_persistence/` — `MyAppSettings.kt` (`@Service` + `SimplePersistentStateComponent`)
  paired with `MyConfigurable.kt` and a minimal `plugin.xml`.
