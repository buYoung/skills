# Deployment Checklist

## Pre-release checklist

Before publishing or shipping an internal release:

- [ ] `<id>` is final (not a placeholder, not "test").
- [ ] `<idea-version>` `since-build` matches the lowest branch you've tested.
- [ ] `<change-notes>` describes the release.
- [ ] `pluginIcon.svg` (and ideally `pluginIcon_dark.svg`) exists in `META-INF/`.
- [ ] `verifyPlugin` report reviewed against the actual minimum and target IDE builds;
      configured failure levels do not hide prohibited API usage.
- [ ] Dynamic install/uninstall works in the sandbox without warnings.
- [ ] Plugin DevKit inspections clean: no "Listener implements Disposable", no
      "Non-default constructors for service and extension class", no "Cancellation check in
      loops", no "Plugin XML errors".
- [ ] Sandbox `idea.log` is clean of new exceptions during normal use.
- [ ] All user-facing text comes from a resource bundle with `@Nls`-typed APIs.
- [ ] Calls, base types, implementations, packages, and EP metadata checked: no private,
      `@ApiStatus.Internal`, `@IntellijInternalApi`, unsupported implementation APIs,
      internal EPs, or reflective/accessibility/cast bypasses.
- [ ] `Experimental` APIs confirmed external-public first; versions and instability
      tracked, with stable public alternatives preferred.
- [ ] Dispatcher choice matches the target version and required locks/modality. No
      unowned `GlobalScope`, raw thread migration shortcuts, or internal
      `Application.getCoroutineScope` / `Project.getCoroutineScope` access.
- [ ] Plugin signed (if shipping to Marketplace).

Record each check as passed, failed, or not run with its evidence. Static Plugin Verifier
results do not establish actual feature behavior or dynamic unload success. Partial
examples in this skill are not standalone build/run verification targets.

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
