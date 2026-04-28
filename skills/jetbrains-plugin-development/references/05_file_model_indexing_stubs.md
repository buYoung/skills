# Indexing and Stubs

## Indexing and stubs

Most non-trivial plugin features need fast lookups: "find files containing this name",
"resolve this symbol", "does this project have a class implementing X". Walking PSI for
every query is unaffordable. Indexes solve this.

### Dumb Mode and smart mode

Right after project open, after big VCS changes, and after some configuration changes, the
IDE enters **Dumb Mode** while it (re)builds indexes. Index reads are not allowed; many
features (Goto Class, full PSI resolution, code completion) are limited.

Detection and gating:

```kotlin
DumbService.getInstance(project).isDumb
DumbService.getInstance(project).runWhenSmart { /* runs on EDT after indexing finishes */ }
DumbService.getInstance(project).suspendIndexingAndRun("temp", { /* … */ })
```

For a provider (`Annotator`, `LineMarkerProvider`, `FoldingBuilder`, `CompletionContributor`,
`AnAction`) to remain available during dumb mode, the implementation must declare itself
`DumbAware` (the marker interface). Without it, the platform skips it during indexing.

For a coroutine-based read that needs indexes:

```kotlin
val r = smartReadAction(project) { /* indexes available here */ }
```

### `FileBasedIndex` — file-level indexes

Build a custom index keyed by string and producing values per file:

```kotlin
class MyKeyIndex : FileBasedIndexExtension<String, Void>() {
  override fun getName(): ID<String, Void> = ID.create("com.example.myKeys")
  override fun getIndexer(): DataIndexer<String, Void, FileContent> = DataIndexer { input ->
    extractKeys(input.contentAsText).associateWith { null }
  }
  override fun getKeyDescriptor() = EnumeratorStringDescriptor.INSTANCE
  override fun getValueExternalizer() = VoidDataExternalizer.INSTANCE
  override fun getVersion() = 1
  override fun getInputFilter() = DefaultFileTypeSpecificInputFilter(MyFileType.INSTANCE)
  override fun dependsOnFileContent() = true
}
```

```xml
<fileBasedIndex implementation="com.example.MyKeyIndex"/>
```

Querying:

```kotlin
val files = FileBasedIndex.getInstance().getContainingFiles(MyKeyIndex.NAME, "key", scope)
```

Increment `getVersion()` whenever the indexer changes — it triggers a rebuild.

### Stub indexes — symbol-level indexes

For language plugins that index symbols (classes, functions, methods, named declarations),
a **stub tree** is a lightweight serialized form of the file's declarations. Stub indexes
key declarations by name and avoid loading the full AST:

```kotlin
// Looking up by name
StubIndex.getInstance().getElements(MyNameIndex.KEY, "foo", project, scope, MyPsiElement::class.java)
StubIndex.getInstance().processAllKeys(MyNameIndex.KEY, processor, scope, idFilter)
```

When implementing a language with stub support: the parser produces stubs for declarations,
the platform stores them, and the stub serves resolution and goto-symbol without parsing
file bodies.

Typical custom-language stub plumbing:

1. Mark interesting PSI types as `StubBasedPsiElementBase` (Grammar-Kit can generate this).
2. Define an `IStubElementType<MyStub, MyDeclaration>` per declaration with custom
   serialize/deserialize logic.
3. Implement a `StubIndexExtension<String, MyDeclaration>` and register
   `<stubElementTypeHolder>` plus `<stubIndex>` in `plugin.xml`.
4. Query via `StubIndex.getInstance().getElements(...)` rather than walking all project PSI.

See `07_language_pipeline.md` for where stubs fit in the custom-language implementation order.

### `AstLoadingFilter`

When indexing or processing stubs, accidentally triggering AST loading is a major
performance regression. `AstLoadingFilter.disallowTreeLoading { … }` throws if any code in
the block needs the AST. The platform applies it during indexing automatically; you might
apply it in your own performance-critical paths.
