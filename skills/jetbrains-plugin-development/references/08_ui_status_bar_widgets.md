# Status Bar Widgets

## API boundary for 2026.2.2

External plugins may implement the public
[`StatusBarWidget`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/ide-core/src/com/intellij/openapi/wm/StatusBarWidget.kt)
or `CustomStatusBarWidget` contracts, or extend the SDK-documented
[`EditorBasedWidget` / `EditorBasedStatusBarPopup`](https://plugins.jetbrains.com/docs/intellij/status-bar-widgets.html)
bases. The
[`EditorBasedStatusBarPopup` declaration](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/platform-impl/src/com/intellij/openapi/wm/impl/status/EditorBasedStatusBarPopup.kt)
is an unannotated public extension surface in `idea/2026.2.2`; do not
call their individual members when those members are marked `@ApiStatus.Internal`. This
boundary is checked at commit `1c7e601c0423e544917046c23763b15d0282e2a3`.

## Status bar widgets

```kotlin
class MyWidgetFactory : StatusBarWidgetFactory {
  override fun getId(): String = "com.example.MyWidget"
  override fun getDisplayName(): String = "My Plugin Status"
  override fun isAvailable(project: Project): Boolean =
    project.service<MyService>().isEnabled
  override fun createWidget(project: Project): StatusBarWidget = MyWidget(project)
  override fun disposeWidget(widget: StatusBarWidget) { Disposer.dispose(widget) }
  override fun canBeEnabledOn(statusBar: StatusBar): Boolean = true
}

class MyWidget(project: Project)
  : EditorBasedStatusBarPopup(project, /* writeable = */ false) {

  override fun ID(): String = "com.example.MyWidget"
  override fun createInstance(project: Project): StatusBarWidget = MyWidget(project)

  override fun getWidgetState(file: VirtualFile?): WidgetState =
    WidgetState(/* tooltip = */ "Click to choose", /* text = */ "Mode", /* enabled = */ true)

  override fun createPopup(context: DataContext): ListPopup =
    JBPopupFactory.getInstance().createActionGroupPopup(
      "Choose Mode",
      myActionGroup,
      context,
      JBPopupFactory.ActionSelectionAid.SPEEDSEARCH,
      /* showDisabledActions = */ false
    )
}
```

```xml
<statusBarWidgetFactory id="com.example.MyWidget"
                        implementation="com.example.MyWidgetFactory"
                        order="last"/>
```

Common `StatusBarWidget` bases and presentation choices:

- `EditorBasedStatusBarPopup` — current-editor-driven label and popup.
- `EditorBasedWidget` — current-editor-driven without a popup.
- Implement `StatusBarWidget.TextPresentation` or `IconPresentation` for simple widgets.
- Implement `CustomStatusBarWidget` when the public presentation interfaces are insufficient.

Users hide widgets via `View | Appearance | Status Bar Widgets`. `isAvailable(Project)`
controls whether your widget appears in that list at all.
