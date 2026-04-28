// Pairs with references/02_runtime_actions.md (Action groups → Dynamic).
// Children are computed each time the group is shown.
package com.example.actionbasics

import com.intellij.openapi.actionSystem.ActionGroup
import com.intellij.openapi.actionSystem.ActionUpdateThread
import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.ui.Messages

class DynamicGreetingsGroup : ActionGroup() {
  override fun getActionUpdateThread(): ActionUpdateThread = ActionUpdateThread.BGT

  override fun getChildren(e: AnActionEvent?): Array<AnAction> =
    listOf("Hi", "Hello", "Bonjour", "안녕")
      .map { greeting -> GreetingAction(greeting) }
      .toTypedArray()

  private class GreetingAction(private val greeting: String)
    : AnAction(greeting) {

    override fun getActionUpdateThread(): ActionUpdateThread = ActionUpdateThread.BGT

    override fun actionPerformed(e: AnActionEvent) {
      val project = e.project ?: return
      Messages.showInfoMessage(project, greeting, "Greeting")
    }
  }
}
