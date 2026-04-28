# File Editor Provider

Read this when a plugin adds a custom editor tab, preview editor, visual designer, split
editor, or non-text file editor for a `VirtualFile`.

## Registration and role

Register `FileEditorProvider` with `com.intellij.fileEditorProvider`. The provider decides
whether it accepts a file and creates a `FileEditor` for it. Mark it dumb aware only when
acceptance does not require indexes.

Prefer a custom file editor when the primary interaction is not plain text editing. If the
task only needs to open text at an offset, use `FileEditorManager` and the standard text
editor instead.

## Lifecycle

`FileEditor` instances are UI resources. They must release listeners, browser components,
models, background work, and message-bus subscriptions when disposed. Parent resources to a
plugin-controlled disposable, not directly to `Project` or `Application`.

Custom tab titles and colors are separate concerns. Use `EditorTabTitleProvider` and
`EditorTabColorProvider` instead of building a full file editor only to change tab
presentation.

## Light and fake files

For generated or temporary text content, create a `LightVirtualFile` and open it through
`FileEditorManager`. This is often simpler than inventing a file type and editor provider.

## Diagnostics checklist

1. Confirm the custom editor is needed; do not replace the text editor for simple previews.
2. Confirm `accept()` is cheap and dumb-aware only when it avoids indexes.
3. Confirm `FileEditor` releases all listeners and child UI resources.
4. Confirm file type, provider order, and competing providers do not hide the intended editor.
5. Confirm behavior for reload, project close, and dynamic plugin unload.

## Official docs

- https://plugins.jetbrains.com/docs/intellij/editors.html
- https://plugins.jetbrains.com/docs/intellij/intellij-platform-extension-point-list.html
