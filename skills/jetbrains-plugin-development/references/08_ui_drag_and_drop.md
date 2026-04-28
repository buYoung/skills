# Drag and Drop

## Drag and drop

```kotlin
DnDSupport.createBuilder(myComponent)
  .setBeanProvider { info ->
    // Convert the start point into something carry-able
    val item = mySelectionAt(info.point) ?: return@setBeanProvider null
    DnDDragStartBean(item)
  }
  .setTargetChecker { event ->
    // Decide whether a drop is acceptable on this position
    event.isDropPossible = event.attachedObject is MyItem
    event.cursor = if (event.isDropPossible) DragSource.DefaultMoveDrop
                   else DragSource.DefaultMoveNoDrop
    true
  }
  .setDropHandler { event ->
    val item = event.attachedObject as? MyItem ?: return@setDropHandler
    handleDrop(item, event.point)
  }
  .install()
```

`DnDSupport` wraps Swing's `DropTarget`/`DragSource` with platform conventions (drop hints,
ghost preview, IDE-style cursor). Use it instead of raw Swing drag listeners — both ends of
the drag get a consistent IDE feel and integrate with existing IDE drag sources (Project
View, Recent Files popup, etc.).

For receiving files dropped from the OS file manager, `FileCopyPasteUtil.isFileListFlavorAvailable(transferable)`
detects file-list payloads, and `FileCopyPasteUtil.getFileListFromAttachedObject(...)`
extracts them.
