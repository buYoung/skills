# Folding

## Contents

  - Minimum implementation
  - `FoldingDescriptor` constructor — what each parameter does
  - Three callbacks govern visible behavior
  - Threading and dumb mode
  - `FoldingBuilder` vs `FoldingBuilderEx`
  - Custom folding settings — `JavaCodeFoldingSettings`-style
  - Folding for languages without a `Language` instance you control
  - Folding in non-file and editor-backed UI surfaces
  - Diagnosing missing folds — checklist



A folding builder produces `FoldingDescriptor`s that tell the platform which AST ranges can
be folded, what placeholder text to show when folded, and which to fold by default.

### Minimum implementation

```java
public class MyFoldingBuilder extends FoldingBuilderEx implements DumbAware {

  @Override
  public FoldingDescriptor @NotNull [] buildFoldRegions(@NotNull PsiElement root,
                                                        @NotNull Document document,
                                                        boolean quick) {
    var descriptors = new ArrayList<FoldingDescriptor>();
    PsiTreeUtil.findChildrenOfType(root, MyFoldableElement.class).forEach(el -> {
      TextRange range = computeFoldRange(el);
      if (range == null || range.isEmpty()) return;
      descriptors.add(new FoldingDescriptor(
        el.getNode(),
        range,
        /* group = */ null,
        /* dependencies = */ Collections.emptySet()
      ));
    });
    return descriptors.toArray(FoldingDescriptor.EMPTY_ARRAY);
  }

  @Override public String getPlaceholderText(@NotNull ASTNode node) { return "..."; }
  @Override public boolean isCollapsedByDefault(@NotNull ASTNode node) { return false; }
}
```

```xml
<lang.foldingBuilder language="JAVA"
                     implementationClass="com.example.MyFoldingBuilder"/>
```

### `FoldingDescriptor` constructor — what each parameter does

`new FoldingDescriptor(node, range, group, dependencies, neverExpands)`

- **`node` (`ASTNode`)**: the AST node the descriptor is associated with. Folding identifies
  regions by the node + range pair across edits.
- **`range` (`TextRange`)**: the **text range to be hidden** when folded. It is independent
  of the node's own range — for a string literal `"simple:foo"`, you might fold only the
  `:foo` portion. The range must be non-empty and inside the file.
- **`group` (`FoldingGroup?`)**: nullable. When non-null, all descriptors sharing the same
  `FoldingGroup` collapse and expand together. Use it for matching brace pairs or
  multi-region constructs.
- **`dependencies` (`Set<Any>`)**: objects whose modification invalidates the placeholder
  text. The platform recomputes the placeholder when any dependency reports a modification.
  Common entries: a `PsiElement` or a `ModificationTracker`.
- **`neverExpands` (boolean, optional)**: rare. Forces the region permanently folded.

### Three callbacks govern visible behavior

- `getPlaceholderText(ASTNode)` — text shown in place of the folded range. Avoid expensive
  computation here; if you need to derive it from the original PSI, that's fine, but no
  resolve.
- `isCollapsedByDefault(ASTNode)` — whether the fold is collapsed when the file first opens.
  Default: `false`.
- The descriptor's `canBeRemovedWhenCollapsed()`/`isNonExpandable()` knobs are seldom used.

### Threading and dumb mode

`buildFoldRegions` runs **inside a Read Action on a background thread**. It can read PSI
freely, but:

- Implement `DumbAware` (or extend `FoldingBuilderEx implements DumbAware`) so folds appear
  during Dumb Mode. Without it, no folds are produced until indexing finishes — which can
  look indistinguishable from "broken" on a large project.
- **Respect the `quick` parameter.** When `quick == true`, the platform is asking for an
  initial-open fast pass. Skip anything that needs resolution, index access, or
  cross-file analysis. Return only folds you can compute from the local AST. The platform
  will call you again with `quick == false` once the file is fully ready.

### `FoldingBuilder` vs `FoldingBuilderEx`

Use `FoldingBuilderEx`. It receives the `Document` so you can validate ranges against
current text and bail on stale invocations. The plain `FoldingBuilder` interface still
works but is the older API.

### Custom folding settings — `JavaCodeFoldingSettings`-style

If you want a settings page where users toggle individual fold groups (like Java's "Imports",
"Generic constructor and method parameters", etc.), provide a `CodeFoldingOptionsProvider`
EP and a settings object backed by `PersistentStateComponent`. See
`08_ui_settings_persistent_state.md` and `08_ui_settings_configurable.md`.

### Folding for languages without a `Language` instance you control

A common situation: contributing folds to **someone else's language** (Java, Kotlin, XML,
HTML, plain text). The setup is identical, just with the right `language` attribute and a
`<depends>` on the providing plugin (`com.intellij.java`, `org.jetbrains.kotlin`, etc.).
Folding still uses the host file's language ID. Multi-language files (JSP, Vue) are handled
per-language: register one builder per language you care about.

### Folding in non-file and editor-backed UI surfaces

Any UI surface that owns, embeds, or exposes an `Editor` can participate in folding: primary
file editors, custom `FileEditor` implementations, preview editors, tool-window editors,
dialog or popup editors, console-like editors, `EditorTextField`, `LanguageTextField`, and
custom Swing panels wrapping `EditorFactory.createEditor(...)`. Treat folding in these
surfaces as a separate integration problem from registering the `FoldingBuilder`.

This section applies only when the component creates or exposes an IntelliJ `Editor` and you
expect code folding to work in that editor. It does not apply to ordinary Swing/JB UI
components that do not expose `CommonDataKeys.EDITOR`, or to editor-like fields where you
only need syntax highlighting, completion, or validation without fold regions.

- **Visual settings do not create folds.** Enabling `EditorSettings.isFoldingOutlineShown`,
  `isAutoCodeFoldingEnabled`, `isLineMarkerAreaShown`, or gutter icons only makes folding
  UI visible. Fold regions still come from `CodeFoldingManager`, the document's PSI, the
  file type/language association, and registered `lang.foldingBuilder` extensions. For
  editor components that start from text-field defaults, `isFoldingOutlineShown` alone is
  often not enough for visible gutter controls; also check `isLineMarkerAreaShown`,
  `setGutterIconsShown(true)`, and `isAutoCodeFoldingEnabled`.
- **Non-file editors need an explicit physical-file strategy.** Normal file editors usually
  get a `VirtualFile`, `PsiFile`, `Document`, and language association from the platform.
  Editors created directly for UI often do not. `CodeFoldingManager.updateFoldRegions(...)`
  and `updateFoldRegionsAsync(...)` first resolve the editor document through
  `PsiDocumentManager.getPsiFile(document)` and then reject invalid files and non-physical
  view providers outside unit tests:

  ```java
  if (psiFile == null || !psiFile.isValid() || !psiFile.getViewProvider().isPhysical() && !ApplicationManager.getApplication().isUnitTestMode()) {
    return null;
  }
  ```

  A document obtained from `PsiFileFactory.createFileFromText(...)` can still be backed by a
  non-physical `PsiFile`, so calling `CodeFoldingManager.updateFoldRegions(...)` alone may
  produce no fold regions even when the language has a registered `FoldingBuilder`.
- **For non-physical PSI, choose manual folding or a physical document.** If the editor must
  use a non-physical PSI file, directly query the registered builder with
  `LanguageFolding.INSTANCE.forLanguage(psiFile.language)`, build descriptors with
  `LanguageFolding.buildFoldingDescriptors(...)`, and apply them through
  `editor.foldingModel.runBatchFoldingOperation { addFoldRegion(...) }`. If the editor
  should behave like a normal file editor, use a real physical `VirtualFile`/`PsiFile`
  document instead and let `CodeFoldingManager` own folding updates.

  ```kotlin
  val descriptors = ReadAction.compute<Array<FoldingDescriptor>, RuntimeException> {
    val builder = LanguageFolding.INSTANCE.forLanguage(psiFile.language)
    LanguageFolding.buildFoldingDescriptors(builder, psiFile, document, false)
  }

  editor.foldingModel.runBatchFoldingOperation {
    for (descriptor in descriptors) {
      val range = descriptor.range
      if (!range.isEmpty && range.endOffset <= document.textLength) {
        val region = editor.foldingModel.addFoldRegion(
          range.startOffset,
          range.endOffset,
          descriptor.placeholderText ?: "..."
        )
        region?.isExpanded = descriptor.isCollapsedByDefault != true
      }
    }
  }
  ```

  This is the minimum shape: compute descriptors under a Read Action, then apply regions on
  the EDT inside a batch folding operation. Production code should remove or update only its
  own previous manual regions and preserve expansion state when that matters.
- **Refresh folds under a read lock.** `CodeFoldingManager.updateFoldRegions(editor)` reads
  PSI and is annotated as requiring a read lock. If UI code updates editor text and
  then refreshes folding, commit the document and run the refresh inside a Read Action, or
  use the coroutine read-action API on newer platform baselines.
- **Run UI scheduling with disposal and modality in mind.** If folding refresh is scheduled
  with `invokeLater`, check `project.isDisposed` and `editor.isDisposed` before touching the
  editor. Pick a modality state that matches the UI surface; dialogs, popups, tool windows,
  and file-editor tabs can have different scheduling constraints. `updateFoldRegions(...)`
  commits the document internally, so avoid calling it from arbitrary write-unsafe
  modality contexts; commit or schedule the refresh from a modality state that is safe for
  the owning component.

  ```kotlin
  val modalityState = ModalityState.stateForComponent(editor.component)
  ApplicationManager.getApplication().invokeLater({
    if (project.isDisposed || editor.isDisposed) return@invokeLater
    // Commit first from the owning component's modality, then compute folding under read access.
  }, modalityState)
  ```

  Avoid `ModalityState.any()` for folding refreshes that may commit documents. It can run
  while a dialog or editor component is in a write-unsafe modality.
- **Mark auxiliary editors with the supported API for that component.** Some editor-backed
  components have a first-class way to mark the editor as supplementary or non-primary. For
  example, `EditorTextField`-family components should use `setSupplementary(true)` before
  the backing editor is created when the editor is auxiliary UI rather than the user's main
  file editor. Setting a same-named Swing client property is not a general substitute for
  component state or editor user data initialized during editor creation.
- **Be deliberate about `DataContext`.** Any component that provides `CommonDataKeys.EDITOR`
  through `UiDataProvider`, `EditorTextField`, `LanguageTextField`, or another data-provider
  path can make global editor actions target that editor when it has focus. Only expose an
  editor from custom UI when standard editor actions are expected to work there.
- **Global editor actions may not validate fold availability.** Some editor actions are
  enabled from coarse editor/project availability and only inspect fold regions during
  execution. If your UI exposes an editor, assume users can invoke folding actions while no
  fold region exists at the caret.
- **Empty fold state is normal.** Empty documents, one-line snippets, invalid syntax, stale
  PSI, or a caret outside every fold range can all produce zero fold regions. Plugin code
  that invokes, wraps, or replaces folding actions must treat an empty fold-region array as
  a no-op, not as an exceptional state.

When adding folding to any non-standard editor surface, verify three states explicitly: an
empty document, a valid single-line document, and a valid multi-line document with the caret
both inside and outside foldable ranges. Many failures appear only when a global folding
action is invoked while that editor has focus and no fold region exists at the caret.

### Diagnosing missing folds — checklist

This is the failure mode that catches most plugins in production. Walk it in order; each
step rules out one cause.

1. **Are folds disabled in Settings?** `Settings | Editor | General | Code Folding`. The
   "Show code folding outline" master toggle must be on. Many users (and CI sandboxes)
   disable it. Reproduce the bug with the toggle confirmed on.
2. **Is the user's "Fold by Default" preference overriding `isCollapsedByDefault`?** The
   same settings page chooses default-collapse per category. A fold can be present yet
   visibly inactive on first open if "Fold by default" is on for its category and the user
   never expands it.
3. **Is the `language=` attribute exactly right?** Language IDs are case-sensitive. Java is
   `JAVA`, Kotlin is `kotlin`. A `language="java"` builder is silently registered against
   nothing.
4. **Is your plugin actually loaded into the production IDE?** A folder on disk with a
   different `<idea-version>` or a `<depends optional>` whose dependency isn't available
   in production may exclude your `<lang.foldingBuilder>` registration. Open `idea.log`
   and search for your plugin id.
5. **Is the registration in the right `plugin.xml`?** When you have an `optional` config
   file (e.g., `myplugin-java.xml`), the `<lang.foldingBuilder>` belongs in **that** file
   so it loads only when the Java plugin is present. Putting it in the main descriptor
   succeeds in dev (Java plugin always around) and silently fails when run against an IDE
   without Java support.
6. **Does `buildFoldRegions` actually return descriptors?** Set a breakpoint at the
   beginning and end of the method, open a target file in `runIde`, and confirm both fire.
   If it isn't entered, the language association is wrong (step 3 or 5). If it returns
   empty, the analysis logic is the bug.
7. **Are the descriptor ranges valid?** A range that is empty, inverted, outside the
   document, or spans only whitespace will be silently skipped. Log
   `descriptor.range, descriptor.range.startOffset .. descriptor.range.endOffset` and
   compare with `document.textLength`.
8. **Is `quick == true` causing you to bail?** If your code path returns early when `quick`
   is true and the platform never calls you with `quick == false` (e.g., because of an
   index error elsewhere), you see no folds. Always handle the cheap path; only the
   *expensive* fold work should be quick-gated.
9. **Are you `DumbAware`?** Without it, the builder is skipped during Dumb Mode. Production
   projects spend significant time in Dumb Mode after pulls/branch switches.
10. **Did your descriptors include an `ASTNode` from a stale `PsiElement`?** Folds attached
    to nodes that were already replaced by an unrelated PSI rebuild silently disappear.
    Make `buildFoldRegions` re-walk the current PSI on each invocation.
11. **Is another `FoldingBuilder` registered against the same language overriding ranges?**
    Multiple builders are allowed and all run, but two builders producing overlapping
    ranges create unpredictable behavior. The IDE's running `plugin.xml` viewer
    (Help | Find Action → "Show Plugin XML" / `idea.log` extension dump) lists every
    `lang.foldingBuilder` registered for the target language; cross-check from there.
12. **Did you reformat / re-parse the file just before checking?** A pending re-parse may
    keep the platform showing old folds while it rebuilds. Trigger
    `PsiDocumentManager.commitAllDocuments(project)` or wait for the next idle pass.
13. **Production IDE branch is older than `sinceBuild` for an API you used?** Some folding
    APIs (e.g., `CustomFoldingProvider` extensions, `FoldingBuilder.getPlaceholderText`
    overloads) shifted across branches. Run Plugin Verifier against the production IDE
    build.
14. **Is the file actually associated with your language?** If your `FileType` registration
    is conditional or depends on a name pattern, files in production might not be parsed
    as your language and so your folds don't apply. Use `Help | Find Action | Show
    Filetype Reassociation` or check `psiFile.language` in a debugger.
15. **Custom folding settings vetoing your group?** If you contribute a
    `CodeFoldingOptionsProvider`, a checkbox in your settings page may default to "off"
    and disable the fold group entirely.
16. **Is this a non-file or editor-backed UI surface?** If the editor is created or exposed
    by a custom `FileEditor`, preview panel, tool window, dialog, popup, console-like
    component, `EditorTextField`, `LanguageTextField`, or another UI component, confirm
    whether the document is backed by a physical `PsiFile`. A non-physical `PsiFile` from
    `PsiFileFactory.createFileFromText(...)` is skipped by `CodeFoldingManager` outside
    unit tests, so you need either a physical document or a manual `LanguageFolding` +
    `FoldingModel` path.
17. **Does the language have a registered folding builder?** `CodeFoldingManager` and
    manual `LanguageFolding` paths both need a `lang.foldingBuilder` for the target
    language. Register a builder for the actual `psiFile.language`, not only for a related
    file extension or base language you expected to apply.
18. **Does folding refresh run in the right threading and modality context?** Commit the
    document from a safe modality state for the owning component, and compute descriptors
    or call `updateFoldRegions(...)` / `updateFoldRegionsAsync(...)` under a Read Action
    according to the API annotations.
19. **Are you assuming a fold exists at the caret?** `FoldingUtil.getFoldRegionsAtOffset`
    can legally return an empty array. Empty files, one-line files, and carets outside any
    foldable range must be handled as no-op states when you invoke or override folding
    behavior.

If you've walked the checklist and still see no folds, attach a remote debugger to the production
IDE and breakpoint inside `CodeFoldingManager`'s call sites — usually that pinpoints the
divergence between dev and prod.
