# Virtual File System

The three-layer file/code model the IDE works in. Read this when you need to read or
modify a file's contents, observe file changes, walk or modify code structure, look up
symbols by name, or work with stubs and indexes.

## The three layers, briefly

| Layer | Type | Represents | Lives on |
|---|---|---|---|
| VFS | `VirtualFile` | Refreshable abstraction over the file system | Application (shared across projects) |
| Document | `Document` | In-memory text buffer for an *open* file | Application (cached per `VirtualFile`) |
| PSI | `PsiFile` / `PsiElement` | Parsed structure for a known language | Project |

Mental rule of thumb: **VFS is the file's identity, Document is its current text, PSI is
its structure.** The platform keeps these three in sync via document commits and bulk file
events; you mostly read PSI, write through Document (for raw text changes) or PSI (for
structural changes), and keep VFS in mind only for I/O and file-system events.

All access to any of these layers requires a Read Action; modifications require a Write
Action (and usually `WriteCommandAction` so they participate in undo). See
`04_threading_model.md`.

## VFS — `VirtualFile`

The VFS abstracts local files, files inside JAR/zip archives, and a few other
file-system-like things behind a uniform API. It caches metadata so the IDE can answer
"does this file exist", "when was it modified", "what's its content" without hitting the OS
on every call.

### Locating a file

```kotlin
// By absolute path
val vf = LocalFileSystem.getInstance().findFileByNioFile(Paths.get("/abs/path"))

// Inside a JAR
val jarRoot = JarFileSystem.getInstance().getJarRootForLocalFile(localJar)
val classFile = jarRoot?.findFileByRelativePath("com/example/Foo.class")

// Quick utilities
VfsUtil.findFile(Paths.get("/abs/path"), /* refreshIfNeeded = */ false)
VfsUtil.createDirectories("/abs/dir")
VfsUtil.copyFile(requestor, source, target)
```

### Reading and writing

```kotlin
val text = vf.contentsToByteArray().decodeToString()
val anyText = VfsUtil.loadText(vf)        // utility, picks correct charset
WriteCommandAction.runWriteCommandAction(project) {
  vf.setBinaryContent(bytes)              // VFS-level write; requires Write Action
}
```

Prefer `Document` (next section) for writes that should propagate through the editor and
PSI. Direct `setBinaryContent` is appropriate for files the user is not editing, but on
IntelliJ Platform `2026.2+` the physical disk write may be postponed after the enclosing
write action. The VFS snapshot is updated immediately from the caller's perspective, while
`java.nio` or an external process can still observe the old bytes briefly.
`VirtualFile.setBinaryContent` is a public API, but the 2026.2.2 declaration requires a
write lock for the overload that performs the write. Keep the write inside the platform's
write-action boundary and do not cast to a file-system implementation class.

When an external process must read bytes just written through VFS, flush the pending VFS I/O
after leaving the write action and before starting that process:

```kotlin
ManagingFS.getInstance().flushPendingUpdates() // outside a write action
project.service<ExternalProcessService>().startInBackground()
```

`flushPendingUpdates()` is the documented completion point for this 2026.2+ case and may
report an I/O failure, so propagate or handle its exception before launching the process. In the
`2026.2.2` declaration it is a public `@ApiStatus.Experimental` API, so record that
version-specific risk and prefer a stable non-VFS hand-off (for example, writing a
plugin-owned temporary input directly with `java.nio` and atomically handing it to the
process) when the feature cannot accept experimental API behavior. A VFS refresh observes
changes already made on disk; it does not replace this flush when the IDE itself has
postponed the write. When only one file is involved, the same declaration also exposes the
experimental `flushPendingUpdates(virtualFile)` overload to limit the flush scope.

### Refresh

```kotlin
vf.refresh(/* asynchronous = */ true, /* recursive = */ false) {
  // VFS refresh and event processing are complete at this point. If this plugin wrote the
  // file through VFS, flush that write outside the write action before scheduling this step.
  project.service<ExternalProcessService>().startInBackground()
}
LocalFileSystem.getInstance().refreshAndFindFileByPath(path)
```

The VFS does **not** auto-pick up out-of-IDE changes instantly. The IDE refreshes lazily on
focus and explicitly on certain user actions. After modifying files via `java.nio.file.*`,
call `refresh` so the IDE notices. `asynchronous = true` returns before the refresh is
complete; use the `postRunnable` overload when a later operation depends on VFS events having
been applied. The callback runs on the event-dispatch thread inside a write action, so hand
off long-running or blocking external-process work to a background scope instead of starting
it inline. The synchronous form (`asynchronous = false`) waits for refresh and event
processing, but must not be called from a read action. Neither form is a substitute for
`ManagingFS.flushPendingUpdates()` when the preceding write was initiated through VFS in
2026.2+.

`LocalFileSystem` and `VirtualFile.refresh` are public platform APIs. The implementation
classes behind them and convenience methods marked `@ApiStatus.Internal` are outside the
external-plugin contract. Confirm the declaration and extension-point metadata against the
target IDE before adding a newer VFS API.

### Listening to changes

Use a declarative `BulkFileListener` (see `02_runtime_services.md`):

```kotlin
class MyVfsListener : BulkFileListener {
  override fun after(events: List<VFileEvent>) {
    for (e in events) {
      when (e) {
        is VFileCreateEvent -> /* ... */
        is VFileDeleteEvent -> /* ... */
        is VFileContentChangeEvent -> /* ... */
        is VFileMoveEvent -> /* ... */
        is VFilePropertyChangeEvent -> /* ... */
      }
    }
  }
}
```

`AsyncFileListener` is a stricter alternative that lets you do work asynchronously without
holding the read lock for the duration. Use it for any handling that requires more than a
trivial amount of work.

`AsyncFileListener` is an external extension point for preparing a VFS change batch; its
`prepareChange` phase must remain cancellable and side-effect free, and its change applier
runs in the platform's write-action delivery phase. Do not use internal VFS event dispatch
classes as a shortcut.

### `VirtualFile` lifecycle and identity

A `VirtualFile` instance for a given path is a long-lived, canonical representation. It can
be **invalidated** (the file is deleted or moved). Always check `vf.isValid` before
non-trivial use, especially after Read Action boundaries.

The public/API-status checks above were made against the
[`idea/2026.2.2` source snapshot](https://github.com/JetBrains/intellij-community/tree/1c7e601c0423e544917046c23763b15d0282e2a3),
including the [`VirtualFile`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/core-api/src/com/intellij/openapi/vfs/VirtualFile.java),
[`ManagingFS`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/analysis-api/src/com/intellij/openapi/vfs/newvfs/ManagingFS.java),
and [`FileSystemInterface`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/core-api/src/com/intellij/openapi/vfs/newvfs/FileSystemInterface.java)
declarations, and the [official Virtual Files guide](https://plugins.jetbrains.com/docs/intellij/virtual-file.html).
