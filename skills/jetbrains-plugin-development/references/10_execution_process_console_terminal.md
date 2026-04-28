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

The Terminal plugin exposes `ShellTerminalWidget`/`TerminalView` for embedding shell
sessions. For a custom terminal, implement `TtyConnector` and register
`<terminal.shellSupport>` (when adding shell-specific helpers).
