// Pairs with references/08_ui_settings_configurable.md.
// Built with Kotlin UI DSL v2 (panel { row { ... } }) — preferred over raw Swing for
// settings forms. The Configurable contract: createComponent() builds the UI; isModified,
// apply, reset compare/sync against the persisted state object.
package com.example.settings

import com.intellij.openapi.options.Configurable
import com.intellij.ui.dsl.builder.bindIntText
import com.intellij.ui.dsl.builder.bindSelected
import com.intellij.ui.dsl.builder.bindText
import com.intellij.ui.dsl.builder.panel
import javax.swing.JComponent

class MyConfigurable : Configurable {
  private val settings get() = MyAppSettings.getInstance().state

  private lateinit var panelComponent: JComponent

  override fun getDisplayName(): String = "My Plugin"

  override fun createComponent(): JComponent {
    panelComponent = panel {
      row("API base URL:") {
        textField().bindText(
          { settings.apiBaseUrl ?: "" },
          { settings.apiBaseUrl = it }
        )
      }
      row("Request timeout (s):") {
        intTextField(0..600).bindIntText(
          { settings.requestTimeoutSeconds },
          { settings.requestTimeoutSeconds = it }
        )
      }
      row {
        checkBox("Verbose logging").bindSelected(
          { settings.verboseLogging },
          { settings.verboseLogging = it }
        )
      }
    }
    return panelComponent
  }

  // The Kotlin UI DSL panel manages isModified / apply / reset for you when you
  // bind through the panel builder; if you need explicit control, override these
  // and compare against the state object yourself.
  override fun isModified(): Boolean = (panelComponent as? com.intellij.ui.dsl.builder.DialogPanel)?.isModified() == true
  override fun apply() { (panelComponent as? com.intellij.ui.dsl.builder.DialogPanel)?.apply() }
  override fun reset() { (panelComponent as? com.intellij.ui.dsl.builder.DialogPanel)?.reset() }
}
