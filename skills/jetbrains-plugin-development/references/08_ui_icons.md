# Icons

Read this for standard IntelliJ Platform icon constants, plugin resource icons, and
`AllIcons.*` reuse. ExpUI-specific icon authoring has additional constraints and is outside
this short reference.

## Icon constants and resources

Convention: a Kotlin `object` (or Java `final class`) with `@JvmField` or `val` constants,
each backed by an SVG or PNG resource.

```kotlin
object MyIcons {
  @JvmField val ToolWindow = IconLoader.getIcon("/icons/toolwindow.svg", MyIcons::class.java)
  @JvmField val Action     = IconLoader.getIcon("/icons/action.svg",     MyIcons::class.java)
}
```

Resources go under `src/main/resources/icons/`. Use SVG. Provide a paired `_dark.svg` for
dark themes (e.g. `action_dark.svg`); the platform picks it automatically.

Icon size convention: tool window stripes 13x13, action icons 16x16, gutter icons 12x12,
plugin marketplace icon 40x40.

`AllIcons.*` is the catalog of platform icons — reuse them where it makes sense.
