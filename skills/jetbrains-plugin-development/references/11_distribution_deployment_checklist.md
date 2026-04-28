# Deployment Checklist

## Pre-release checklist

Before publishing or shipping an internal release:

- [ ] `<id>` is final (not a placeholder, not "test").
- [ ] `<idea-version>` `since-build` matches the lowest branch you've tested.
- [ ] `<change-notes>` describes the release.
- [ ] `pluginIcon.svg` (and ideally `pluginIcon_dark.svg`) exists in `META-INF/`.
- [ ] `verifyPlugin` passes against the recommended set of IDEs.
- [ ] Dynamic install/uninstall works in the sandbox without warnings.
- [ ] Plugin DevKit inspections clean: no "Listener implements Disposable", no
      "Non-default constructors for service and extension class", no "Cancellation check in
      loops", no "Plugin XML errors".
- [ ] Sandbox `idea.log` is clean of new exceptions during normal use.
- [ ] All user-facing text comes from a resource bundle with `@Nls`-typed APIs.
- [ ] No `@ApiStatus.Internal` calls; `@ApiStatus.Experimental` calls intentional and
      tracked.
- [ ] Search the codebase for `Dispatchers.Main`, `GlobalScope`, raw `new Thread(`,
      `Executors.new`, `Application.getCoroutineScope`, `Project.getCoroutineScope` — none
      should be in production code.
- [ ] Plugin signed (if shipping to Marketplace).

## Common mistakes

- `<id>` changed after the first release. Marketplace treats it as a different plugin;
  users lose the upgrade path.
- `until-build` set to a narrow branch and forgotten. EAP users see "incompatible".
- Resource bundle declared in `plugin.xml` but missing from the artifact — `prepareSandbox`
  output should be inspected to confirm `messages/MyPluginBundle.properties` is in the JAR.
- Plugin signing cert expired — `signPlugin` fails right at release.
- `@JvmField` missing on Bundle constants in Kotlin, leading to bytecode mismatches with
  static analyzers.
- Translations stale because string concatenation hid the user-visible text from
  inspections. Fix by routing through `MessageFormat` / parameterized bundle keys.

## Related references

- `01_core_plugin_xml.md` — descriptor mechanics, `<depends>`, sinceBuild/untilBuild.
- `03_lifecycle_disposer.md` — leak diagnosis when dynamic unload fails.
- `04_threading_model.md` — `Application.coroutineScope` is forbidden, why injected
  scopes matter.
- `02_runtime_services.md` and `02_runtime_listeners_message_bus.md` — safe owners for plugin-owned state,
  listeners, and subscriptions.
