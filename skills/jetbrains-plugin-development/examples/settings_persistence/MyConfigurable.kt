// Pairs with references/08_ui_settings_configurable.md.
// Built with Kotlin UI DSL v2 (panel { row { ... } }) — preferred over raw Swing for
// settings forms. The Configurable contract: createComponent() builds the UI; isModified,
// apply, reset delegate to the panel's bindings, which read and write the persisted state.
package com.example.settings

import com.intellij.openapi.options.Configurable
import com.intellij.openapi.ui.DialogPanel
import com.intellij.ui.dsl.builder.bindIntText
import com.intellij.ui.dsl.builder.bindSelected
import com.intellij.ui.dsl.builder.bindText
import com.intellij.ui.dsl.builder.panel
import javax.swing.JComponent

class MyConfigurable : Configurable {
  private val settings get() = MyAppSettings.getInstance().state

  private lateinit var panelComponent: DialogPanel

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

  // panel { } returns com.intellij.openapi.ui.DialogPanel, which tracks the bind* bindings.
  // A plain Configurable must still delegate isModified / apply / reset to it;
  // BoundConfigurable with createPanel() does this delegation for you.
  override fun isModified(): Boolean = panelComponent.isModified()
  override fun apply() { panelComponent.apply() }
  override fun reset() { panelComponent.reset() }
}
