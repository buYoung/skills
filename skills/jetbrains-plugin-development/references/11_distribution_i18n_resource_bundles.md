# Internationalization and Resource Bundles

Read this when a plugin has user-visible strings, localized resources, `@Nls` annotations,
or language-pack contributions.

## Resource bundles

### `<resource-bundle>`

```xml
<idea-plugin>
  …
  <resource-bundle>messages.MyPluginBundle</resource-bundle>
</idea-plugin>
```

Files:

```
src/main/resources/
  messages/
    MyPluginBundle.properties           # default (en)
    MyPluginBundle_ko.properties
    MyPluginBundle_ja.properties
    MyPluginBundle_zh_CN.properties
```

### Reading a key

```kotlin
@NlsContexts.DialogTitle val title: String = MyPluginBundle.message("dialog.title")
val msg: @Nls String = MyPluginBundle.message("error.connection.failed", host, port)
```

`MyPluginBundle` is typically a small singleton:

```kotlin
@NonNls private const val BUNDLE = "messages.MyPluginBundle"
object MyPluginBundle {
  private val bundle = DynamicBundle(MyPluginBundle::class.java, BUNDLE)
  fun message(@PropertyKey(resourceBundle = BUNDLE) key: String, vararg params: Any): String =
    bundle.getMessage(key, *params)
}
```

Using `DynamicBundle` correctly handles plugin-classloader-aware lookup and the IDE's
language pack support.

### Annotations for human-readable strings

| Annotation | Meaning |
|---|---|
| `@Nls` | Translatable user-facing text |
| `@NlsSafe` | Already-localized or always-fine string (e.g., a user-typed value) |
| `@NonNls` | Internal identifier, never translated (e.g., XML keys, action ids) |
| `@PropertyKey(resourceBundle = "...")` | Marks a string parameter as a resource-bundle key |

The platform's `NlsContexts` exposes more specific contracts: `@NlsContexts.DialogTitle`,
`@NlsContexts.Button`, `@NlsContexts.Tooltip`, etc. Use them where applicable; inspections
warn when a wrong category is supplied to a labeled API.

`NlsActions` is the same idea for action text.

`MessageFormat`/`ChoiceFormat` and `NlsMessages`/`DateFormatUtil` round out localization
needs. Avoid manual string concatenation; that defeats translation.

### Language-pack contributions

Do not register `com.intellij.languageBundle`: it is an internal EP, not an external
plugin customization surface. Localize your own plugin through its resource bundles.
Replacing platform-wide strings has no supported substitute established here; explain
that limitation instead of using internal registration or bundle-cache manipulation.

The external-public rule applies to individual `DynamicBundle` members as well: its
internal cache and language-pack helpers are unavailable to plugin code. On the pinned
2026.2.2 baseline, the inherited single-string constructor is `Obsolete`; the example
delegates to the public class-and-path constructor and public `getMessage` inherited from
`AbstractBundle`. For an existing older target, check those declarations before migrating
an inheritance-based bundle; do not copy its internal resource-resolution implementation.

Sources: [DynamicBundle at the pinned commit](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/core-api/src/com/intellij/DynamicBundle.java),
[AbstractBundle](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/util/src/com/intellij/AbstractBundle.kt),
[Core.analyzer.xml](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/core-api/resources/META-INF/Core.analyzer.xml),
and [EP status list](https://plugins.jetbrains.com/docs/intellij/intellij-platform-extension-point-list.html).
