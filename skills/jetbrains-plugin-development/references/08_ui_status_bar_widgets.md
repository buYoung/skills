# Status Bar Widgets

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

Common `StatusBarWidget` superclasses:

- `EditorBasedStatusBarPopup` — current-editor-driven label + popup (encoding, line ending, etc.).
- `EditorBasedWidget` — current-editor-driven without a popup.
- For non-editor widgets, implement `StatusBarWidget` directly with a
  `StatusBarWidget.WidgetPresentation`.

Users hide widgets via `View | Appearance | Status Bar Widgets`. `isAvailable(Project)`
controls whether your widget appears in that list at all.
