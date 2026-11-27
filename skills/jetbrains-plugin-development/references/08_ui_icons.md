# Icons

Read this for standard IntelliJ Platform icon constants, plugin resource icons, and `AllIcons.*` reuse. ExpUI-specific icon authoring has additional constraints and is outside this short reference.

## Icon constants and resources

Convention: a Kotlin `object` (or Java `final class`) with `@JvmField` or `val` constants, each backed by an SVG or PNG resource.

```kotlin
object MyIcons {
  @JvmField val ToolWindow = IconLoader.getIcon("/icons/toolwindow.svg", MyIcons::class.java)
  @JvmField val Action     = IconLoader.getIcon("/icons/action.svg",     MyIcons::class.java)
}
```

Resources go under `src/main/resources/icons/`. Use SVG. Provide a paired `_dark.svg` for dark themes (e.g. `action_dark.svg`); the platform picks it automatically.

Icon sizes from the official [Icons guide](https://plugins.jetbrains.com/docs/intellij/icons.html#icon-sizes):

| Usage | Classic UI | New UI |
|---|---|---|
| Node, action, file type | 16x16 | 16x16 (no separate New UI size) |
| Tool window | 13x13 | 20x20; 16x16 in Compact Mode |
| Editor gutter | 12x12 | 14x14 |

For New UI tool windows, ship `toolWindowIcon@20x20.svg` and `toolWindowIcon@20x20_dark.svg` (20x20) plus `toolWindowIcon.svg` and `toolWindowIcon_dark.svg` (16x16, Compact Mode). The plugin logo (`pluginIcon.svg`) is a separate asset, provided at 40x40.

`AllIcons.*` is the catalog of platform icons — reuse them where it makes sense.
