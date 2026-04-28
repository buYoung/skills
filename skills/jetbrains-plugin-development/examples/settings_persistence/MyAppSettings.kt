// Pairs with references/02_runtime_services.md (light services) and
// references/08_ui_settings_persistent_state.md.
// SimplePersistentStateComponent + a BaseState subclass is the modern pattern;
// avoid hand-rolling getState/loadState for plain data classes.
package com.example.settings

import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.components.BaseState
import com.intellij.openapi.components.Service
import com.intellij.openapi.components.SimplePersistentStateComponent
import com.intellij.openapi.components.State
import com.intellij.openapi.components.Storage

class MyAppState : BaseState() {
  var apiBaseUrl by string("https://api.example.com")
  var requestTimeoutSeconds by property(30)
  var verboseLogging by property(false)
}

@Service(Service.Level.APP)
@State(
  name = "com.example.settings.MyAppSettings",
  storages = [Storage("MyPlugin.xml")]
)
class MyAppSettings : SimplePersistentStateComponent<MyAppState>(MyAppState()) {
  companion object {
    fun getInstance(): MyAppSettings =
      ApplicationManager.getApplication().getService(MyAppSettings::class.java)
  }
}
