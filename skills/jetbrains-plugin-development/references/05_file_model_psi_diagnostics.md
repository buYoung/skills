# File and PSI Diagnostics

## Diagnostics — common file/PSI issues

| Symptom | Likely cause |
|---|---|
| "Element is no longer valid" | Holding a `PsiElement` across Read Actions. Use `SmartPsiElementPointer`. |
| Edits don't appear in PSI | Document not committed. Call `PsiDocumentManager.commitDocument` or wait via `performWhenAllCommitted`. |
| Edits don't appear on disk | `Document` change not saved. `FileDocumentManager.getInstance().saveDocument(doc)` (rare — usually unnecessary). |
| File appears outdated in IDE | VFS not refreshed. Call `vf.refresh(...)` or `LocalFileSystem.getInstance().refresh(true)`. |
| Goto-symbol misses entries from your language | Stub index version mismatch / missing input filter. Bump `getVersion()`. |
| Index queries throw "indexes are not ready" | You're in Dumb Mode. Use `smartReadAction` or `DumbService.runWhenSmart`. |
| `PsiTreeChangeListener` swamps the EDT | Subscribe manually with a tight `Disposable` / `CoroutineScope`, not declaratively. |

## Common mistakes

- Caching `PsiElement` references on a service field. Use `SmartPsiElementPointer`.
- Calling `getText()` for a comparison. Use `textMatches`.
- Modifying PSI without `WriteCommandAction` — the change skips undo and the user cannot
  reverse it.
- Mutating UAST (it's read-only). Drop down to `sourcePsi`.
- Reading indexes without checking Dumb Mode in a non-`DumbAware` provider.
- Inserting whitespace nodes manually. Reformat afterwards.
- Forgetting to bump a `FileBasedIndex` / stub `getVersion()` after changing serialization.

## Related references

- `04_threading_model.md` — Read/Write rules, suspending versions.
- `06_code_insight_editor_model.md` and `06_code_insight_editor_markup_lifecycle.md` — editor state and markup built on PSI.
- `07_language_pipeline.md` — implementing PSI for a new language; stub plumbing.
