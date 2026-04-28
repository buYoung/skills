# Modules, Roots, and File Index

## `Module`

A project is divided into modules. Each module has its own content roots, libraries, SDK.

```kotlin
val modules = ModuleManager.getInstance(project).modules
val module = ProjectFileIndex.getInstance(project).getModuleForFile(vf)
val moduleForPsi = ModuleUtilCore.findModuleForPsiElement(psiElement)
```

Module-level services exist (`@Service(Service.Level.MODULE)`) but are usually overkill.
Prefer a project-level service keyed by `Module` if module-specific data is needed.

## `ProjectFileIndex` — most-used API

```kotlin
val pfi = ProjectFileIndex.getInstance(project)

pfi.isInContent(vf)                  // is the file under any module's content?
pfi.isInSource(vf)                   // ... and in a source root?
pfi.isInTestSourceContent(vf)
pfi.isInLibraryClasses(vf)
pfi.isInLibrarySource(vf)
pfi.isExcluded(vf)

pfi.getModuleForFile(vf)             // owning module
pfi.getContentRootForFile(vf)        // its module's content root
pfi.getSourceRootForFile(vf)         // its source root
pfi.getPackageNameByDirectory(dir)   // Java package

pfi.iterateContent(object : ContentIterator {
  override fun processFile(file: VirtualFile): Boolean = true   // false to stop
})
pfi.iterateContentUnderDirectory(dir, iterator)
```

Use `isInContent` to filter VFS events to "files this project actually owns" — otherwise
you'll receive global VFS noise.

## `ModuleRootManager`, `ContentEntry`, `OrderEntry`

Reading module structure:

```kotlin
val mrm = ModuleRootManager.getInstance(module)
val contentEntries: Array<ContentEntry> = mrm.contentEntries
for (e in contentEntries) {
  e.file                  // content root VirtualFile
  e.sourceFolders          // SourceFolder[]
  e.excludeFolders         // ExcludeFolder[]
}
val sourceRoots: Array<VirtualFile> = mrm.sourceRoots
val orderEntries: Array<OrderEntry> = mrm.orderEntries
```

`OrderEntry` subtypes:

| Subtype | Means |
|---|---|
| `ModuleSourceOrderEntry` | the module itself |
| `LibraryOrderEntry` | a library |
| `ModuleOrderEntry` | dependency on another module |
| `JdkOrderEntry` | a specific JDK |
| `InheritedJdkOrderEntry` | uses the project's SDK |

Modifying module structure (Write Action required):

```kotlin
WriteAction.runAndWait<Throwable> {
  val model = ModuleRootManager.getInstance(module).modifiableModel
  try {
    val entry = model.addContentEntry(newContentRoot)
    entry.addSourceFolder(srcDir, /* isTestSource = */ false)
    model.commit()
  } catch (t: Throwable) {
    model.dispose()
    throw t
  }
}
```

The `modifiableModel` is a snapshot; nothing is applied until `commit()`. On exception,
`dispose()` discards.

`ModuleRootListener` (declarative) fires before/after structure changes — useful for
caches that depend on roots.
