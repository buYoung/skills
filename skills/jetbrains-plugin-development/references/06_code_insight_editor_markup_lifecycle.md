# Editor Markup and Lifecycle

### `RangeMarker` — offsets that follow edits

```kotlin
val marker = document.createRangeMarker(start, end)
marker.setGreedyToLeft(true)
marker.setGreedyToRight(true)
// ...edits happen, possibly...
if (marker.isValid) use(marker.startOffset, marker.endOffset)
marker.dispose()
```

`RangeHighlighter` extends `RangeMarker`, so highlighters track edits automatically.

### `MarkupModel` and `RangeHighlighter`

Editor-local, non-persistent decorations: backgrounds, underlines, gutter icons, error stripe.

```kotlin
val model = editor.markupModel
val rh = model.addRangeHighlighter(
  textAttributesKey,                  // CodeInsightColors.WARNINGS_ATTRIBUTES, etc.
  startOffset, endOffset,
  HighlighterLayer.WARNING,           // ordering: SYNTAX < CARET_ROW < SELECTION < ERROR < ADDITIONAL_SYNTAX
  HighlighterTargetArea.EXACT_RANGE
)
rh.gutterIconRenderer = MyGutterIconRenderer()
rh.errorStripeMarkColor = JBColor.RED
rh.errorStripeTooltip = "…"
model.removeHighlighter(rh)
```

Use `MarkupModel` for plugin-introduced view markup that isn't tied to a language EP. For
language-driven highlighting, prefer `Annotator` (see `07_language_pipeline.md`).

### `ScrollingModel`

```kotlin
editor.scrollingModel.scrollToCaret(ScrollType.CENTER)            // CENTER, RELATIVE, MAKE_VISIBLE
editor.scrollingModel.scrollTo(LogicalPosition(line, col), ScrollType.CENTER)
editor.scrollingModel.runActionOnScrollingFinished { /* … */ }
```

### Editor lifecycle and listeners

`EditorFactory.editorCreated`/`editorReleased` track creation and disposal of editors.
Listeners need a parent disposable:

```kotlin
editor.caretModel.addCaretListener(myListener, parentDisposable)
editor.selectionModel.addSelectionListener(mySelListener, parentDisposable)
EditorFactory.getInstance().eventMulticaster.addCaretListener(global, parentDisposable)
```

Holding an `Editor` reference past `editorReleased` will throw on next access. Drop
references in `editorReleased`, or scope to a `CoroutineScope` you cancel there.

### Console filters (live in editor too)

```kotlin
class MyFilter(val project: Project) : Filter {
  override fun applyFilter(line: String, entireLength: Int): Filter.Result? {
    val m = pattern.matcher(line); if (!m.find()) return null
    val start = entireLength - line.length + m.start()
    val end   = entireLength - line.length + m.end()
    return Filter.Result(start, end, OpenFileHyperlinkInfo(project, file, lineNumber))
  }
}
```

Built-in filters: `RegexpFilter` (`$FILE_PATH$`, `$LINE$`, `$COLUMN$` macros), `UrlFilter`.
Register globally via `ConsoleFilterProvider` EP (`com.intellij.consoleFilterProvider`).

### Guarded blocks and read-only handling

```kotlin
val guard = document.createGuardedBlock(start, end)        // user can't edit
document.removeGuardedBlock(guard)
ReadonlyStatusHandler.getInstance(project).ensureFilesWritable(listOf(vf))
```

For programmatic edits inside a guarded range, remove the guard within a Write Action,
make the change, restore the guard.
