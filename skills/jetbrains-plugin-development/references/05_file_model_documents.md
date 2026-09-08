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
// Public but Experimental on 2026.2.2; see 04_threading_coroutines_2024.md:
writeCommandAction(project, "Insert") { doc.insertString(offset, "text") }
```

Direct `Document` mutations bypass the user's undo stack unless inside a
`WriteCommandAction`. Always use the command form for any change a user might want to undo.

### Document ↔ PSI sync — `PsiDocumentManager`

When you modify a `Document`, the PSI is **not** instantly updated; the platform commits
edits asynchronously. Operations that depend on a fresh PSI tree need to wait. In the
2026.2.2 public declaration, `commitDocument` is a synchronous commit operation, but
event-system-enabled documents should be committed on the EDT in a write-safe context:

```kotlin
val pdm = PsiDocumentManager.getInstance(project)
pdm.commitDocument(doc)             // synchronous PSI update; call in the documented context
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

### Saving before an external process

Committing PSI and saving bytes to disk are separate completion points. If a process outside
the IDE must consume the newest text, perform the sequence in the appropriate write-safe
context, then launch the process from a background scope:

```kotlin
// Enter from EDT in a write-safe context; this command participates in undo.
WriteCommandAction.runWriteCommandAction(project, "Update", null, {
  doc.replaceString(start, end, replacement)
  PsiDocumentManager.getInstance(project).commitDocument(doc)
  FileDocumentManager.getInstance().saveDocument(doc)
  check(!FileDocumentManager.getInstance().isDocumentUnsaved(doc)) { "Document was not saved" }
})
project.service<ExternalProcessService>().runInBackground {
  ManagingFS.getInstance().flushPendingUpdates() // outside the write action
  startProcess()
}
```

`ExternalProcessService` is a plugin-owned, lifecycle-scoped background helper, not a
platform API. Do not launch the process if saving or flushing fails.

For a group of documents, wait for `performWhenAllCommitted` (which must be registered from
the EDT) and then call `FileDocumentManager.saveAllDocuments()`. `saveDocument` and
`saveAllDocuments` are public save APIs, but on IntelliJ Platform `2026.2+` the underlying
`VirtualFile` I/O may still be postponed after the write action. Before starting an external
process, leave the write-safe context and call
`ManagingFS.getInstance().flushPendingUpdates()` off EDT and handle its possible I/O failure; this is
the documented disk-persistence completion point. If the process instead depends on an
out-of-IDE file change being visible to VFS, use the `VirtualFile.refresh` completion callback described in
`05_file_model_vfs.md` before starting it.

The flush only drains pending VFS writes. It does not prove that a save was accepted or freeze
the document against a concurrent edit. If the process requires a particular document
snapshot, record its modification stamp/text, verify `isDocumentUnsaved(document)` is false
after saving, and stop if the stamp changed before the process starts. For exact bytes without
the experimental VFS barrier, write the captured snapshot to a plugin-owned temporary file
through the JDK I/O API and pass that file to the process; this changes the process input path
and must be handled as an explicit design choice.

Do not call unsupported platform implementation classes, reflection, or internal document/VFS helpers to
force completion. Check the declaration's lock/thread annotations and API status against the
target IDE before adopting a newer save or commit method. `ManagingFS.flushPendingUpdates()`
is public but `@ApiStatus.Experimental` in the `2026.2.2` baseline; if that instability is
not acceptable, hand the external process a plugin-owned file written directly through a
stable JDK I/O path instead of depending on an undocumented barrier.

### Document listeners

```kotlin
doc.addDocumentListener(object : DocumentListener {
  override fun documentChanged(event: DocumentEvent) { /* ... */ }
}, parentDisposable)
```

Pass a parent disposable; otherwise the listener leaks. For application-level reactions to
saves/reloads, use the declarative `FileDocumentManagerListener`.

The save/commit and API-status checks above were made against the
[`idea/2026.2.2` source snapshot](https://github.com/JetBrains/intellij-community/tree/1c7e601c0423e544917046c23763b15d0282e2a3),
including the [`FileDocumentManager`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/core-api/src/com/intellij/openapi/fileEditor/FileDocumentManager.java),
[`PsiDocumentManager`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/core-api/src/com/intellij/psi/PsiDocumentManager.java),
and [`ManagingFS`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/analysis-api/src/com/intellij/openapi/vfs/newvfs/ManagingFS.java)
declarations, and the [official Documents guide](https://plugins.jetbrains.com/docs/intellij/documents.html).

### Read-only ranges

```kotlin
val guard = doc.createGuardedBlock(start, end)        // raises an error on edit
ReadonlyStatusHandler.getInstance(project).ensureFilesWritable(listOf(vf))  // pre-check
```
