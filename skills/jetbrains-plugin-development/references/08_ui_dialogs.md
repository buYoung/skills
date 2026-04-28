# Dialogs

## `DialogWrapper` — modal dialogs

```kotlin
class MyDialog(project: Project?) : DialogWrapper(project, true /* modal */) {
  init { title = "Do the thing"; init() }

  override fun createCenterPanel(): JComponent = panel {
    row("Name:") { textField().columns(COLUMNS_MEDIUM) }
  }
  override fun doOKAction() {
    super.doOKAction()
    // act
  }
}

if (MyDialog(project).showAndGet()) { /* OK pressed */ }
```

`getDisposable()` is your dialog-scoped parent for resources (timers, subscriptions). See
`03_lifecycle_disposer.md`.

`Messages` for built-in dialogs: `Messages.showInfoMessage`, `showYesNoDialog`,
`showInputDialog`, `showErrorDialog`, etc.

`JBPopupFactory` for hover popups and inline lists:

```kotlin
JBPopupFactory.getInstance()
  .createListPopup(BaseListPopupStep("Pick", listOf("a", "b", "c")))
  .showInBestPositionFor(editor)
```
