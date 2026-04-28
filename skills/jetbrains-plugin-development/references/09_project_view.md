# Project View

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

For a custom view pane (alternative tree mode in the Project tool window), implement
`AbstractProjectViewPane`.

`ProjectViewNodeDecorator` (`<projectViewNodeDecorator>`) decorates existing nodes —
suffix text, icon overlays — without changing structure.

`<projectViewPaneSelectionHelper>` is the public extension point for project-view pane
selection helpers. For general "Select In" routing, use the public `com.intellij.selectInTarget`
extension point with `SelectInTarget`.

Do not use `com.intellij.projectViewPaneExtractor` or `ProjectViewPaneModelExtractor` from
third-party plugins. The extension point is internal and can block Marketplace approval; keep
Project View presentation changes on `ProjectViewNodeDecorator` / `TreeStructureProvider` /
`AbstractProjectViewPane` public APIs.
