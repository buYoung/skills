# Layout Helpers

## Layout helpers — `JBSplitter`, `JBTabs`

Tool windows and complex panels usually need resizable splits and tabbed regions. Use the
platform widgets — they handle drag persistence, theming, and IDE-style affordances; the
raw Swing `JSplitPane` / `JTabbedPane` look out of place inside the IDE.

```kotlin
// Two-pane resizable split (vertical = true means the divider is horizontal,
// stacking firstComponent on top). Initial proportion 0.6 → top gets 60%.
val splitter = JBSplitter(true, 0.6f).apply {
  firstComponent = topPanel
  secondComponent = bottomPanel
  proportionKey = "com.example.MySplitter"   // remembers user-resized split per session
  setHonorComponentsMinimumSize(true)
}
```

`OnePixelSplitter` is a thinner cousin used in the IDE's main editor splitter; pick it
when the divider should be visually unobtrusive.

```kotlin
// Tabs that match the IDE's tabbed views (e.g., the run tool window's output tabs)
val tabs = JBTabsFactory.createEditorTabs(project, parentDisposable)
val info = TabInfo(myComponent)
  .setText("Output")
  .setIcon(MyIcons.Output)
  .setActions(myActionGroup, /* place = */ "MyToolWindow")
tabs.addTab(info)
toolWindowContent.add(tabs.component, BorderLayout.CENTER)
```

`JBTabs` supports drag-reorder, tab-level actions, and the IDE's hover/selection styling.
For static, settings-style tabs, `JBTabbedPane` is a lighter alternative.
