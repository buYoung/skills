# Notifications

## Notifications

```kotlin
val group = NotificationGroupManager.getInstance().getNotificationGroup("MyPlugin")
group.createNotification("Title", "Body", NotificationType.WARNING)
  .addAction(NotificationAction.createSimple("Open Settings") {
    ShowSettingsUtil.getInstance().showSettingsDialog(project, MySettingsConfigurable::class.java)
  })
  .notify(project)
```

Register groups in `plugin.xml`:

```xml
<notificationGroup id="MyPlugin"
                   displayType="BALLOON"
                   isLogByDefault="true"
                   bundle="messages.MyPluginBundle"
                   key="notification.group.MyPlugin"/>
```

`displayType`: `BALLOON`, `STICKY_BALLOON`, `TOOL_WINDOW`, `NONE`. Sticky balloons stay until dismissed. The Notifications tool window keeps notifications until they are cleared; `displayType="NONE"` logs an entry there without a balloon, and `isLogByDefault="false"` shows a balloon without a tool-window entry.

`EditorNotificationProvider` (and the older `EditorNotifications.Provider`) display banners above an editor for a specific file:

```kotlin
class MyEditorNotification : EditorNotificationProvider {
  override fun collectNotificationData(project: Project, file: VirtualFile)
      : Function<in FileEditor, out JComponent?>? {
    if (!shouldShow(file)) return null
    return Function { editor ->
      EditorNotificationPanel(editor).apply { text = "…"; createActionLabel("…") { … } }
    }
  }
}
```

```xml
<editorNotificationProvider implementation="com.example.MyEditorNotification"/>
```
