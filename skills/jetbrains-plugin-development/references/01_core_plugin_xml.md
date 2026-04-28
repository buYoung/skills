# Plugin XML

## `plugin.xml` (Plugin Configuration File)

Located at `src/main/resources/META-INF/plugin.xml`. The IDE reads this file to learn what
your plugin contributes.

### Required and recommended elements

```xml
<idea-plugin>
  <id>com.example.myplugin</id>                <!-- never change after first release -->
  <name>My Plugin</name>
  <version>1.2.3</version>                     <!-- Gradle plugin can inject this -->
  <vendor url="https://example.com" email="dev@example.com">Example Inc.</vendor>

  <description><![CDATA[
    Marketplace description, HTML allowed.
  ]]></description>

  <change-notes><![CDATA[
    <ul><li>1.2.3 — fixed foo</li></ul>
  ]]></change-notes>

  <idea-version since-build="241" until-build="243.*"/>

  <depends>com.intellij.modules.platform</depends>

  <extensions defaultExtensionNs="com.intellij">
    <!-- registrations go here -->
  </extensions>

  <applicationListeners> <!-- ... --> </applicationListeners>
  <projectListeners>     <!-- ... --> </projectListeners>
  <actions>              <!-- ... --> </actions>
</idea-plugin>
```

`<idea-plugin>` attributes worth knowing:

- `url` — homepage link.
- `require-restart="true"` — opt out of dynamic install/update. Default is `false`.
  Set to `true` only when you cannot satisfy dynamic-plugin constraints.

The `<id>` is the **immutable identity** of the plugin in the JetBrains Marketplace. Renaming
it after publishing breaks every user's upgrade path; they will see a new, separate plugin.

### File-naming conventions that matter

```
src/main/resources/
  META-INF/
    plugin.xml
    pluginIcon.svg          # 40x40 light-theme icon (required for Marketplace)
    pluginIcon_dark.svg     # optional dark-theme variant
    <optional-config>.xml   # config-file targets of <depends optional>
  messages/
    MyPluginBundle.properties        # i18n bundle (referenced by <resource-bundle>)
    MyPluginBundle_ko.properties     # locale variants
```

Icons are picked up by filename, not by an XML element.

## Listeners, actions, and other top-level descriptor blocks

These have their own references: use `02_runtime_listeners_message_bus.md` for listeners,
`02_runtime_actions.md` for actions, and `01_core_extensions.md` for extension points.
Quick syntactic reminder so you can recognize them in `plugin.xml`:

```xml
<applicationListeners>
  <listener class="com.example.MyVfsListener"
            topic="com.intellij.openapi.vfs.newvfs.BulkFileListener"/>
</applicationListeners>

<projectListeners>
  <listener class="com.example.MyToolWindowListener"
            topic="com.intellij.openapi.wm.ex.ToolWindowManagerListener"/>
</projectListeners>

<actions>
  <action id="com.example.MyAction"
          class="com.example.MyAction"
          text="My Action"
          description="Does something">
    <add-to-group group-id="ToolsMenu" anchor="first"/>
    <keyboard-shortcut first-keystroke="control alt A" keymap="$default"/>
  </action>
</actions>
```
