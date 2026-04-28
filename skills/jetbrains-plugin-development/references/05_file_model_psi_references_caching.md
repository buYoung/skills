# PSI References and Caching

### Long-lived references — `SmartPsiElementPointer`

Holding a `PsiElement` across Read Actions risks `IllegalStateException` (`element is not
valid`). Use a smart pointer:

```kotlin
val pointer = SmartPointerManager.getInstance(project).createSmartPsiElementPointer(element)
// ...later, in another Read Action:
val restored: PsiElement? = pointer.element
```

Smart pointers track document edits and survive incremental re-parses while the element's
identity remains meaningful.

### `PsiReference` and resolution

```kotlin
val refs: Array<PsiReference> = element.references
for (ref in refs) {
  val target: PsiElement? = ref.resolve()
}
```

Multi-target references implement `PsiPolyVariantReference`:

```kotlin
val results = (ref as? PsiPolyVariantReference)?.multiResolve(/* incompleteCode = */ false)
```

Contributing references for a custom language is covered in `07_language_pipeline.md`.

### `PsiNamedElement` / `PsiNameIdentifierOwner`

Symbol-like elements expose names:

```kotlin
interface PsiNamedElement : PsiElement {
  fun getName(): String?
  fun setName(name: String): PsiElement
}

interface PsiNameIdentifierOwner : PsiNamedElement {
  fun getNameIdentifier(): PsiElement?
}
```

Implementing these is the precondition for rename refactoring and correct find-usages.

### `FileViewProvider` — multi-language files

Files like JSP, Vue SFCs, Blade templates contain multiple languages. The `FileViewProvider`
keeps a separate PSI tree per language:

```kotlin
val viewProvider = psiFile.viewProvider
val languages: Set<Language> = viewProvider.languages
val htmlPsi = viewProvider.getPsi(HTMLLanguage.INSTANCE)
val jsPsi   = viewProvider.getPsi(Language.findInstance(JavaScriptSupportLoader::class.java).language)
val element = viewProvider.findElementAt(offset, HTMLLanguage.INSTANCE)
```

Custom multi-language files supply a `FileViewProviderFactory`.

### `CachedValue` — PSI-aware caching

Memoize an analysis with platform-tracked invalidation:

```kotlin
val result = CachedValuesManager.getCachedValue(psiElement) {
  CachedValueProvider.Result.create(
    analyze(psiElement),
    PsiModificationTracker.MODIFICATION_COUNT  // invalidate on any PSI change
  )
}
```

Common trackers:

- `PsiModificationTracker.MODIFICATION_COUNT` — any PSI change.
- `ModificationTracker.NEVER_CHANGED` — permanent cache.
- `ModificationTracker.EVER_CHANGED` — never cache (debug only).
- `VirtualFileManager.VFS_STRUCTURE_MODIFICATIONS` — VFS topology changes.
