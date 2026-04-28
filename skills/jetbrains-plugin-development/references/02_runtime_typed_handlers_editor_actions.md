# Typed Handlers and Editor Actions

Read this when a plugin reacts to typed characters, Enter, Backspace, smart typing, editor
actions, or multi-caret editing behavior.

## Choose the right surface

Use `TypedHandlerDelegate` through `com.intellij.typedHandler` for normal typed-character
interception, especially when deciding whether to trigger autopopup completion. Use
`EditorActionHandler` when extending or wrapping an existing editor action such as caret
movement, delete, clone caret, or selection behavior.

Use specialized delegates where available: `EnterHandlerDelegate`, `BackspaceHandlerDelegate`,
`JoinLinesHandlerDelegate`, `SmartEnterProcessor`, `StatementUpDownMover`, `CodeBlockProvider`,
and related editor delegates. They preserve platform behavior better than replacing a raw
handler.

Avoid `com.intellij.editorTypedHandler` and `com.intellij.rawEditorTypedHandler` for new
plugin code; the extension point list marks them for removal or non-dynamic behavior.

## Threading and writes

Typed handlers run in an editor event path. Keep checks very small, avoid blocking work, and
perform document or PSI mutation only through the correct write-command path so undo,
document listeners, and PSI synchronization stay coherent.

When the goal is to show completion after a typed character, route through
`TypedHandlerDelegate.checkAutoPopup()` and `AutoPopupController.scheduleAutoPopup()` instead
of directly opening the lookup UI.

## Multi-caret rules

`TypedActionHandler` and `TypedHandlerDelegate` are invoked only once for each typed
character unless the specific delegate documents per-caret behavior. If the handler changes
text, handle all carets deliberately. For code insight actions, prefer
`MultiCaretCodeInsightAction` when the action must work independently at each caret.

## Diagnostics checklist

1. Confirm the task really needs a typing handler and is not better expressed as completion,
   intention, or postfix template behavior.
2. Confirm the registered EP is public and dynamic enough for the target IDE branch.
3. Confirm the handler preserves the original editor behavior when it declines the event.
4. Confirm document writes are undoable and do not bypass PSI/document synchronization.
5. Confirm behavior with zero, one, and multiple carets.

## Official docs

- https://plugins.jetbrains.com/docs/intellij/editor-events.html
- https://plugins.jetbrains.com/docs/intellij/multiple-carets.html
- https://plugins.jetbrains.com/docs/intellij/code-completion.html
