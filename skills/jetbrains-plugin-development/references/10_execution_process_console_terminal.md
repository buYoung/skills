# Process, Console, and Terminal

### Console: `ConsoleView`

```kotlin
val console = TextConsoleBuilderFactory.getInstance().createBuilder(project).console
console.print("text\n", ConsoleViewContentType.NORMAL_OUTPUT)
console.printHyperlink("Open file", OpenFileHyperlinkInfo(project, vf, line))
console.attachToProcess(processHandler)
console.addMessageFilter(MyFilter(project))   // see 06_code_insight_editor_markup_lifecycle.md "Console filters"
```

### Embedded terminal

First distinguish a process-output console from an interactive terminal. Prefer the public
`ConsoleView`/`ProcessHandler` route above when output, hyperlinks, and process attachment
are sufficient. It does not provide an interactive shell emulator.

For 2025.3+ Reworked Terminal integration, declare the Terminal plugin dependency
`org.jetbrains.plugins.terminal` and use the documented external API. On the pinned
2026.2.2 source:

- `com.intellij.terminal.frontend.view.TerminalView` and
  `com.intellij.terminal.frontend.toolwindow.TerminalToolWindowTabsManager` are public
  `Experimental`, `NonExtendable` interfaces. Obtain them through `TerminalView.DATA_KEY`
  or the manager's `getInstance(project)`; do not implement them or cast to their implementations.
- The manager's `tabs` accessor requires EDT; `createTabBuilder()` is the public creation
  entry point. Recheck individual builder methods on the minimum supported release.
- Public `TerminalAllowedActionsProvider.getActionIds()` and
  `org.jetbrains.plugins.terminal.allowedActionsProvider` support terminal shortcut actions.
  The EP is dynamic and its containing frontend module has `visibility="public"`.
  Its companion's internal `EP_NAME` is not a plugin-callable entry point.
- A public interface can contain internal members: do not use `TerminalView.sessionDeferred`,
  `addInputInterceptor`, or `setTopComponent`, which are marked `Internal` in this source.

These APIs remain experimental; record the chosen target version and instability. Do not
copy the older `org.jetbrains.plugins.terminal.TerminalView` or `ShellTerminalWidget` path
into a Reworked Terminal integration, cast a terminal widget to a concrete engine, or
invent `<terminal.shellSupport>` registration. A raw `TtyConnector` implementation does not
establish a supported IntelliJ extension contract. For 2024.1-era support, prefer the console
alternative or verify a documented classic-terminal API on that exact branch; do not
pretend the newer API exists there. Unsupported engine-specific embedding remains a limitation.

Sources: [Embedded Terminal SDK](https://plugins.jetbrains.com/docs/intellij/embedded-terminal.html),
[`TerminalView`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/plugins/terminal/frontend/src/com/intellij/terminal/frontend/view/TerminalView.kt),
[`TerminalToolWindowTabsManager`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/plugins/terminal/frontend/src/com/intellij/terminal/frontend/toolwindow/TerminalToolWindowTabsManager.kt),
[`TerminalAllowedActionsProvider`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/plugins/terminal/frontend/src/com/intellij/terminal/frontend/view/TerminalAllowedActionsProvider.kt),
and [frontend module/EP metadata](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/plugins/terminal/frontend/resources/intellij.terminal.frontend.xml).
