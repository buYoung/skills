# Configurable Settings Pages

## `Configurable` — Settings page UI

```kotlin
class MySettingsConfigurable : Configurable {
  private var component: MySettingsComponent? = null

  override fun getDisplayName() = "My Plugin"
  override fun createComponent(): JComponent {
    component = MySettingsComponent()
    return component!!.panel
  }
  override fun isModified(): Boolean {
    val s = MyPluginSettings.getInstance().state
    val c = component!!
    return c.userName != s.userId || c.enabled != s.enabled
  }
  override fun apply() {
    val s = MyPluginSettings.getInstance().state
    val c = component!!
    s.userId = c.userName
    s.enabled = c.enabled
  }
  override fun reset() {
    val s = MyPluginSettings.getInstance().state
    val c = component!!
    c.userName = s.userId ?: ""
    c.enabled = s.enabled
  }
  override fun disposeUIResources() { component = null }
}
```

```xml
<applicationConfigurable instance="com.example.MySettingsConfigurable"
                         id="com.example.settings"
                         displayName="My Plugin"/>
<!-- or -->
<projectConfigurable    instance="com.example.MyProjectConfigurable"
                        id="com.example.project.settings"
                        displayName="My Plugin"
                        parentId="tools"/>
```

`parentId` nests under an existing settings node (`tools`, `editor`, `language`, `vcs`, …).

`SearchableConfigurable` gives the search bar in the Settings dialog hits in your page.

Implement `Configurable.NoScroll` if your page should not be wrapped in a scroll pane (when
your panel handles its own scrolling).
