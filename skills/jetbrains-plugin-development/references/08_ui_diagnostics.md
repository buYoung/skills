# UI Diagnostics

## Common mistakes

- Plain `var` fields in a `BaseState` subclass. No persistence.
- `@JvmField` missing on a `SerializablePersistentStateComponent` data class. Empty XML.
- Storing secrets in `PersistentStateComponent`. Use `PasswordSafe`.
- Application-level light service (`@Service`) that is a `PersistentStateComponent` with `roamingType = DEFAULT`, including an omitted `roamingType`. Disallowed; set `DISABLED`.
- `Configurable.apply` not actually flushing into the service. Settings page seems to "do nothing".
- Forgetting `disposeUIResources` on a `Configurable` and leaking a panel that holds an `Editor`/`Project` reference.
- Tool window factory not `DumbAware`. Tool window stays empty during Dumb Mode.
- Notification "displays nothing" — `notificationGroup` not declared in `plugin.xml`.

## Related references

- `02_runtime_services.md` — services as the canonical place for state.
- `03_lifecycle_disposer.md` — `DialogWrapper.getDisposable()`, dialog scopes.
- `08_ui_settings_persistent_state.md` — persistent settings and secret-storage boundaries.
- `08_ui_settings_configurable.md`, `08_ui_tool_windows.md`, and `08_ui_notifications.md` — `<applicationConfigurable>`, `<toolWindow>`, and `<notificationGroup>` registration.
