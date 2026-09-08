# Dynamic Plugins and Classloaders

Read this when dynamic plugin reload is breaking, a plugin cannot unload without restart,
or plugin classloader boundaries affect optional dependencies and integration code.

## Dynamic plugin reload — what's actually required

Dynamic install/update/uninstall (no IDE restart) has been the default since 2020.1
(`require-restart="false"` is the implicit default). For your plugin to remain dynamic, the
following must hold simultaneously:

1. **Every EP your plugin uses must be dynamic.** The platform's standard EPs almost all
   are. Custom EPs you define must declare `dynamic="true"`. Non-dynamic EPs taint the
   dependency graph: they force every plugin that uses them to require a restart.
2. **No plugin state retained beyond unload.** Avoid static caches and singleton-held
   resources escaping the plugin lifecycle. Constants and resource-bundle singletons are
   not inherently forbidden; stateful resources belong in lifecycle-owned services.
3. **No constructor work in EP implementations.** They are stateless — see
   `01_core_extensions.md`.
4. **Every `Disposable` is parented to a plugin-owned `Disposable`** (a service, a dialog,
   a tool window content) — never `Application` or `Project` directly. See
   `03_lifecycle_disposer.md`.
5. **Every `MessageBusConnection` is `connect(parent)` or `connect(coroutineScope)`** with
   a parent owned by the plugin.
6. **No `<applicationService overrides="true">`.** Overriding platform implementations is
   incompatible with dynamic unload — replacement disappears mid-life.
7. **No use of `Application.getCoroutineScope()` / `Project.getCoroutineScope()`.** They
   are `@ApiStatus.Internal`. Inject `CoroutineScope` via service constructor instead.
8. **Custom EPs you define are `dynamic="true"`.** If another plugin extends them, that
   plugin's contributions disappear/reinstall correctly when your plugin reloads.

If any of these fail, the IDE shows "Plugin … was not unloaded successfully. Please
restart …" and refuses dynamic install/update. Diagnose with the techniques in
`03_lifecycle_leak_diagnostics.md`.

### `DynamicPluginListener`

Subscribe to receive plugin-load/unload events application-wide:

```kotlin
class MyPluginsListener : DynamicPluginListener {
  override fun beforePluginLoaded(descriptor: IdeaPluginDescriptor) { … }
  override fun pluginUnloaded(descriptor: IdeaPluginDescriptor, isUpdate: Boolean) { … }
}
```

Useful when your plugin integrates with another plugin you `optional`-depend on — react to
its presence/absence at runtime.

### Verifying dynamic-ness

- `runIde`, install your plugin, exercise it, then disable it via `Settings | Plugins`.
  The IDE should not warn about restart. Re-enable; behavior should resume.
- Recompile changed code/resources and update the sandbox before expecting `autoReload`
  to notice an artifact change. `autoReload` does not compile source or prove safe unloading.
- Run Plugin DevKit's dynamic plugin descriptor inspection and `verifyPlugin` for static
  checks; neither establishes that runtime objects release the plugin classloader.
- For unload failures, inspect `idea.log` and the heap snapshot using the SDK's
  [dynamic plugin troubleshooting](https://plugins.jetbrains.com/docs/intellij/dynamic-plugins.html#troubleshooting).
  Do not call platform-internal leak hunters or plugin loaders from plugin code.
- Report actual install/update/disable/re-enable/uninstall observations separately from
  static compatibility checks. Unrun checks remain unverified.

## Classloader rules

Each plugin runs under its own classloader. Important consequences:

- **Two classloaders mean two `Class<?>` objects.** A class loaded by another plugin's
  loader is *not* equal to the same FQN loaded by yours. Classes shared across plugins must
  come from the platform classloader.
- **No reflective access to internal plugin/platform APIs.** Declare dependencies and call
  their supported public interfaces; do not bypass access with reflection or internal casts.
- **`Thread.currentThread().contextClassLoader`** is normally the right loader to use for
  shared utility classes. The platform sets it appropriately for many entry points.
- **Don't keep static references to other plugins' classes** beyond the lifetime of those
  plugins.

If you need to call into another plugin from yours, declare a `<depends>` so dependency
classes can be resolved through its classloader, and use its supported external APIs.
Language-level visibility and dependency resolution do not establish public API status.

For interaction *with* a plugin without a hard `<depends>`, use `<depends optional
config-file=...>` and put the integration code inside the optional block — the optional
block's classes simply don't load when the dependency is absent.
