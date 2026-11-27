# Project View

## API boundary for 2026.3

For external plugins, use `TreeStructureProvider`, `ProjectViewNodeDecorator`, and—when a complete alternative pane is required—`AbstractProjectViewPane`. Their declarations and EP registrations are present without internal status in IntelliJ Community `idea/2026.3` at commit `c91871ae2864649d952825cff72569e3db0e7ac6`: see [`TreeStructureProvider`](https://github.com/JetBrains/intellij-community/blob/c91871ae2864649d952825cff72569e3db0e7ac6/platform/editor-ui-api/src/com/intellij/ide/projectView/TreeStructureProvider.java), [`ProjectViewNodeDecorator`](https://github.com/JetBrains/intellij-community/blob/c91871ae2864649d952825cff72569e3db0e7ac6/platform/lang-impl/src/com/intellij/ide/projectView/ProjectViewNodeDecorator.kt), [`AbstractProjectViewPane`](https://github.com/JetBrains/intellij-community/blob/c91871ae2864649d952825cff72569e3db0e7ac6/platform/lang-impl/src/com/intellij/ide/projectView/impl/AbstractProjectViewPane.java), and the EP declarations in [`intellij.platform.editor.ui.xml`](https://github.com/JetBrains/intellij-community/blob/c91871ae2864649d952825cff72569e3db0e7ac6/platform/editor-ui-api/resources/intellij.platform.editor.ui.xml) and [`intellij.platform.lang.impl.xml`](https://github.com/JetBrains/intellij-community/blob/c91871ae2864649d952825cff72569e3db0e7ac6/platform/lang-impl/resources/intellij.platform.lang.impl.xml).

## Project View customization

The Project View (left tree) is extended via `TreeStructureProvider` and friends.

```kotlin
class MyTreeStructureProvider : TreeStructureProvider {
  override fun modify(parent: AbstractTreeNode<*>,
                      children: Collection<AbstractTreeNode<*>>,
                      settings: ViewSettings): Collection<AbstractTreeNode<*>> {
    // Re-bucket / hide / decorate children
    return children
  }
}
```

```xml
<treeStructureProvider implementation="com.example.MyTreeStructureProvider"/>
```

`ProjectViewNodeDecorator` (`<projectViewNodeDecorator>`) decorates existing nodes — suffix text, icon overlays — without changing structure.

For a custom view pane (an alternative tree mode in the Project tool window), implement the public `AbstractProjectViewPane` contract registered by `com.intellij.projectViewPane`. Stay within its public/protected surface and re-check the superclass on every supported IDE branch.

For general "Select In" routing, use the public `com.intellij.selectInTarget` extension point with `SelectInTarget`.

Do not use `projectViewPaneSelectionHelper`, `com.intellij.projectViewPaneExtractor`, or `ProjectViewPaneModelExtractor` from third-party plugins. The selection helper requires overriding `@ApiStatus.Internal` members, and the extractor contract is internal. Keep selection and presentation changes on `ProjectViewNodeDecorator`, `TreeStructureProvider`, `AbstractProjectViewPane`, and `SelectInTarget` public surfaces.
