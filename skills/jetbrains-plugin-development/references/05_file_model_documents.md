# Documents

## Document — `Document`

The `Document` is the in-memory text buffer the editor displays. One `Document` per open
file, cached by `VirtualFile`.

### Acquiring a Document

```kotlin
val doc: Document? = FileDocumentManager.getInstance().getDocument(vf)
val doc2: Document? = PsiDocumentManager.getInstance(project).getDocument(psiFile)
```

`FileDocumentManager` is at the application level (no project context); `PsiDocumentManager`
is project-scoped because it bridges Documents and PSI for that project's PSI roots.

### Reading

```kotlin
ReadAction.compute<String, Throwable> {
  doc.text                     // entire text
  doc.getText(TextRange(s, e)) // a slice
  doc.lineCount
  doc.getLineNumber(offset)
  doc.getLineStartOffset(line)
}
```

### Writing — through `WriteCommandAction`

```kotlin
WriteCommandAction.runWriteCommandAction(project, "Insert", null, {
  doc.insertString(offset, "text")
  doc.replaceString(start, end, "new")
  doc.deleteString(start, end)
})
// Coroutine equivalent:
writeCommandAction(project, "Insert") { doc.insertString(offset, "text") }
```

Direct `Document` mutations bypass the user's undo stack unless inside a
`WriteCommandAction`. Always use the command form for any change a user might want to undo.

### Document ↔ PSI sync — `PsiDocumentManager`

When you modify a `Document`, the PSI is **not** instantly updated; the platform commits
edits asynchronously. Operations that depend on a fresh PSI tree need to wait:

```kotlin
val pdm = PsiDocumentManager.getInstance(project)
pdm.commitDocument(doc)             // synchronous commit
pdm.performWhenAllCommitted { /* run after pending commits */ }
pdm.doPostponedOperationsAndUnblockDocument(doc) // after PSI mutation, sync Document
```

Two common ordering bugs:

1. Modifying a `Document` and immediately reading PSI in the same Write Action — the PSI is
   stale. Either commit explicitly (only if you must) or refactor so the read happens after
   the next read action.
2. Modifying PSI and then asking the Document for offsets — PSI mutations *do* update the
   Document, but the Document may be marked uncommitted from the platform's POV. After
   structural PSI edits, call `doPostponedOperationsAndUnblockDocument(doc)` if you need to
   continue using offset math on the Document.

### Document listeners

```kotlin
doc.addDocumentListener(object : DocumentListener {
  override fun documentChanged(event: DocumentEvent) { /* ... */ }
}, parentDisposable)
```

Pass a parent disposable; otherwise the listener leaks. For application-level reactions to
saves/reloads, use the declarative `FileDocumentManagerListener`.

### Read-only ranges

```kotlin
val guard = doc.createGuardedBlock(start, end)        // raises an error on edit
ReadonlyStatusHandler.getInstance(project).ensureFilesWritable(listOf(vf))  // pre-check
```
