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
object MyPluginBundle : DynamicBundle(BUNDLE) {
  fun message(@PropertyKey(resourceBundle = BUNDLE) key: String, vararg params: Any): String =
    getMessage(key, *params)
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

Plugins can ship as IDE language packs by extending `com.intellij.languageBundle` EP. This
is the path to translating platform strings rather than just your own.
