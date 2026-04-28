# Tool Windows

## Tool windows

```kotlin
class MyToolWindowFactory : ToolWindowFactory, DumbAware {
  override fun createToolWindowContent(project: Project, tw: ToolWindow) {
    val content = ContentFactory.getInstance().createContent(MyPanel(project), "Main", false)
    tw.contentManager.addContent(content)
  }
}
```

```xml
<toolWindow id="MyToolWindow"
            anchor="right"
            icon="MyIcons.ToolWindow"
            factoryClass="com.example.MyToolWindowFactory"/>
```

Anchors: `left`, `right`, `bottom`. Add `secondary="true"` for the secondary stripe.
Implement `DumbAware` if the tool window can be open during indexing.

Multiple tabs:

```kotlin
val cf = ContentFactory.getInstance()
tw.contentManager.addContent(cf.createContent(panel1, "Tab 1", false))
tw.contentManager.addContent(cf.createContent(panel2, "Tab 2", false))
```

For dynamic tool windows that should appear conditionally, `RegisterToolWindowTask` plus
`ToolWindowManager.getInstance(project).registerToolWindow(...)`.
