// Pairs with references/02_runtime_actions.md.
// AnAction instances are singletons — never store per-invocation state on a field;
// put state in a service and look it up here.
package com.example.actionbasics

import com.intellij.openapi.actionSystem.ActionUpdateThread
import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.actionSystem.CommonDataKeys
import com.intellij.openapi.ui.Messages

class HelloAction : AnAction() {
  // BGT is the right default for most new actions. The implementation below only
  // touches AnActionEvent data, so background dispatch is safe.
  override fun getActionUpdateThread(): ActionUpdateThread = ActionUpdateThread.BGT

  override fun update(e: AnActionEvent) {
    // Keep this cheap — runs on every menu open / toolbar repaint.
    e.presentation.isEnabledAndVisible = e.project != null
  }

  override fun actionPerformed(e: AnActionEvent) {
    val project = e.project ?: return
    val file = e.getData(CommonDataKeys.VIRTUAL_FILE)?.name ?: "no file"
    Messages.showInfoMessage(project, "Hello from $file", "Action Basics")
  }
}
