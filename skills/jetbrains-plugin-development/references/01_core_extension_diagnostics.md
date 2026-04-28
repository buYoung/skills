# Extension Loading Diagnostics

## Lifecycle of plugin loading

1. IDE starts (or dynamically loads). It scans installed plugins and parses every
   `META-INF/plugin.xml`.
2. `<idea-version>` is checked against the running build number. Mismatch → load fails.
3. `<depends>` is resolved. Missing required dependency → load fails. Missing optional
   dependency → that `config-file` is skipped.
4. EPs, services, listeners, and actions are **registered as metadata**. No instances yet.
5. The first time code reads `ExtensionPointName.extensionList` (or the platform iterates
   on its behalf), each extension is constructed. Same for services on first `getService(...)`,
   listeners when their topic fires, actions when shown or invoked.
6. On unload (dynamic plugin removal/update or IDE shutdown): plugin-controlled `Disposable`s
   dispose, services dispose, the plugin's classloader becomes unreachable. If anything
   outside the plugin still holds a reference to a plugin class, the classloader leaks and
   the next install of the plugin will silently coexist with the leaked one until the IDE
   restarts.

## Why an extension is silently ignored — diagnostic checklist

When you registered something in `plugin.xml` and it does nothing in the running IDE, walk
this list before reaching for a debugger.

1. **Is the plugin actually loaded?** In `Settings | Plugins | Installed`, look for your plugin
   and confirm the version/build matches the artifact you ran. The sandbox is a separate IDE;
   your dev machine's main IDE is irrelevant. Check `idea.log` for "Plugin '<id>' loaded".
2. **Does the EP id match exactly?** `defaultExtensionNs` plus the tag name must concatenate
   to a real EP. Open `plugin.xml` in the IDE and look for inspection warnings; they catch
   typos and missing `<depends>`.
3. **Is the language identifier correct?** Language IDs are case-sensitive. Java is `JAVA`,
   Kotlin is `kotlin`, Python is `Python`, Markdown is `Markdown`, Plain text is `TEXT`. The
   authoritative value is `Language.getID()` of the registered `Language` instance. Filter
   `<options>` are also case-sensitive.
4. **Is the plugin you depend on actually present?** A `language="kotlin"` annotator does
   nothing if the Kotlin plugin is not installed in the sandbox. Add it via
   `bundledPlugin("org.jetbrains.kotlin")` or `plugin(...)`.
5. **Is the constructor throwing `ExtensionNotApplicableException`?** That's by design — the
   extension opted out for the current environment.
6. **Is the constructor throwing some other exception?** Check `idea.log`. Constructor errors
   are logged but do not crash the IDE; the extension is just absent.
7. **Is the implementation actually being instantiated?** Set a breakpoint in the constructor
   and trigger the feature. If the breakpoint never hits, the EP is not iterating you — most
   often a registration mistake (wrong tag, wrong namespace, missing `<depends>`,
   `optional` block whose `config-file` did not load).
8. **Did `update()` short-circuit you?** Actions and many providers consult an `isApplicable`
   / `update()` first. The implementation may be reached but instantly disabled.
9. **Plugin Verifier complaining?** Run the `verifyPlugin` Gradle task. It can flag incompatible API
   usage that the IDE quietly excludes at runtime.
10. **Stale `idea.log`?** If you have changed `plugin.xml` and the change does not appear,
    you may be looking at the wrong sandbox config dir. The path is logged near the top of
    `idea.log` ("idea.log Path:").

## Common mistakes

- Editing the wrong `plugin.xml` (e.g., the one in a sub-module that isn't actually built
  into the artifact). The `prepareSandbox` task copies the canonical descriptor to
  `build/idea-sandbox/.../plugins/<plugin-name>/lib/META-INF/plugin.xml`; cross-check.
- Forgetting `<depends>com.intellij.modules.platform</depends>`. The plugin loads as a "legacy
  IDEA plugin" and behaves oddly.
- Setting `until-build` too narrow, then forgetting to bump it. EAP users see compatibility
  warnings.
- Using `Application` services for state that is per-project (then leaking across projects).
- Confusing `<depends>` (compile- and load-time required) with classpath dependencies in
  Gradle. Both must agree.
- Importing `com.intellij.openapi.application.Application` and calling `getCoroutineScope()`
  — that is `@ApiStatus.Internal` and deprecated. Inject `CoroutineScope` via service
  constructor instead.

## Related references

- `02_runtime_services.md` — services (`@Service`, `@Service(cs)`).
- `02_runtime_listeners_message_bus.md` — listeners and MessageBus subscriptions.
- `02_runtime_actions.md` — action registration and update behavior.
- `03_lifecycle_disposer.md` — Disposer parent rules, dynamic plugin requirements.
- `04_threading_model.md` — when EP code may run on which thread.
- `11_distribution_deployment_checklist.md` — dynamic plugin verification, signing, publishing.
