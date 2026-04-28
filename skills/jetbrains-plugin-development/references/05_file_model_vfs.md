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
PSI. Direct `setBinaryContent` is appropriate for files the user is not editing.

### Refresh

```kotlin
vf.refresh(/* asynchronous = */ true, /* recursive = */ false)
LocalFileSystem.getInstance().refreshAndFindFileByPath(path)
```

The VFS does **not** auto-pick up out-of-IDE changes instantly. The IDE refreshes lazily on
focus and explicitly on certain user actions. After modifying files via `java.nio.file.*`,
call `refresh` so the IDE notices.

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

### `VirtualFile` lifecycle and identity

A `VirtualFile` instance for a given path is a long-lived, canonical representation. It can
be **invalidated** (the file is deleted or moved). Always check `vf.isValid` before
non-trivial use, especially after Read Action boundaries.
