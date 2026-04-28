# Editor Model

Read this when:
- You touch `Editor`, `CaretModel`, `SelectionModel`, or editor coordinate systems.
- For markup, lifecycle, console filters, or guarded blocks, read `06_code_insight_editor_markup_lifecycle.md`.
- For editor providers such as line markers, folding, formatter, inspections, intentions, refactoring support, documentation, parameter info, structure view, or navigation, read the provider-specific reference.

## The editor model

### Acquiring an `Editor`

```kotlin
val editor = e.getData(CommonDataKeys.EDITOR)                         // from action context
val editor = FileEditorManager.getInstance(project).selectedTextEditor // currently focused
val editor = FileEditorManager.getInstance(project)
  .openTextEditor(OpenFileDescriptor(project, vf, offset), /* requestFocus = */ true)
val editors = EditorFactory.getInstance().allEditors                  // every open editor
```

### Three coordinate systems — the most-misused concept

| Coordinate | Meaning | Affected by folding/soft-wrap? |
|---|---|---|
| **Offset** | Index from the document start (0-based, newline counted) | No |
| **Logical position** | `(line, column)` as written in the file | No |
| **Visual position** | `(line, column)` as drawn on screen | **Yes** |

Conversions live on `Editor`:

```kotlin
editor.offsetToLogicalPosition(offset)
editor.logicalPositionToOffset(logical)
editor.visualPositionToOffset(visual)
editor.offsetToVisualPosition(offset)
editor.logicalToVisualPosition(logical)
editor.visualToLogicalPosition(visual)

editor.logicalPositionToXY(logical)        // pixels for popup placement
editor.xyToLogicalPosition(Point(x, y))
```

Use **offset** or **logical** for analysis and storage. Use **visual** or **pixels** for
positioning popups, hints, gutter UI. Confusing them produces bugs that only manifest in
folded or soft-wrapped buffers.

### Caret and selection (incl. multi-caret)

```kotlin
val caret = editor.caretModel.primaryCaret
caret.offset; caret.logicalPosition; caret.visualPosition
caret.moveToOffset(100)

editor.caretModel.runForEachCaret { c ->
  if (c.hasSelection()) {
    val (s, e) = c.selectionStart to c.selectionEnd
    val text = c.selectedText
  }
}
```

Multi-caret is on by default since 2013 (`Alt+Click` / `Ctrl+G`). Any new editor action
must handle it. The simplest path is `MultiCaretCodeInsightAction`:

```java
public class MyAction extends MultiCaretCodeInsightAction {
  @Override protected @NotNull MultiCaretCodeInsightActionHandler getHandler() {
    return new MultiCaretCodeInsightActionHandler() {
      @Override public void invoke(@NotNull Project project,
                                   @NotNull Editor editor,
                                   @NotNull Caret caret,
                                   @NotNull PsiFile file) { /* per-caret */ }
      @Override public void postInvoke() { /* once after all carets */ }
    };
  }
}
```
