# Kotlin UI DSL

## Kotlin UI DSL v2 — building panels

The recommended UI builder for any new dialog, settings page, or tool window content. It
sits on top of Swing but is dramatically more concise.

```kotlin
class MySettingsComponent {
  var userName: String = ""
  var enabled: Boolean = true

  val panel: JComponent = panel {
    row("User name:") {
      textField()
        .bindText(::userName)
        .columns(COLUMNS_LARGE)
        .validationOnInput { if (it.text.isBlank()) error("Required") else null }
    }
    row {
      checkBox("Enable feature").bindSelected(::enabled)
    }
    group("Advanced") {
      row("Retries:") {
        spinner(0..10).bindIntValue(::retries)
      }
      row {
        label("Token stored in keychain").comment("Click <a>here</a> to update.")
      }
    }
  }
}
```

A non-exhaustive list of available cells: `label`, `link`, `text`, `comment`, `textField`,
`textArea`, `passwordField`, `expandableTextField`, `intTextField`, `spinner`, `checkBox`,
`radioButton`, `comboBox`, `dropDownLink`, `slider`, `colorButton`, `cell(component)` (any
Swing), `button`, `actionButton`, `actionsButton`, `browserLink`, `icon`, `separator`,
`segmentedButton`, plus container helpers `row`, `panel`, `group`, `groupRowsRange`,
`buttonsGroup`, `collapsibleGroup`.

Common idioms:

- `bindText` / `bindSelected` / `bindIntValue` / `bindItem` — two-way property binding via
  Kotlin reflection or a `MutableProperty`.
- `validationOnInput { … }` / `validationOnApply { … }` — return `null` for OK, or an
  `ValidationInfo` for errors.
- `enabledIf(predicate)` / `visibleIf(predicate)` — reactive enable/visible toggles.
- `align(Align.FILL)`, `resizableColumn()` — layout shaping.
- Settings-page convention: implement `apply` / `reset` / `isModified` on the surrounding
  `Configurable`; use `bind*` to keep the UI state synced with the settings model object.

For complex layouts, mix DSL with raw Swing via `cell(component).align(...)`.
