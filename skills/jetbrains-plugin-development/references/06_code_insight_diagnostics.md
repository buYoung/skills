# Code Insight Diagnostics

## Diagnosing missing code insights — generic flow

When *any* code-insight provider isn't doing what you expect, walk this:

1. Confirm the EP is correct, the `language` matches exactly, and the registration is in
   the right `plugin.xml` (main vs `<depends optional>` config-file).
2. Confirm the implementation is constructed at all (breakpoint at the entry method).
3. Confirm threading expectations — most providers run inside a Read Action on a BGT.
   Throwing PCE or `IndexNotReadyException` from a non-`DumbAware` provider drops the
   result.
4. Confirm the produced result is non-empty and ranges/elements are valid.
5. Confirm Dumb Mode behavior: provider is `DumbAware` if it doesn't need indexes; uses
   `smartReadAction` if it does.
6. Confirm there isn't a competing provider with `order="first"` that prempts you.
7. Confirm the production IDE has the dependencies your provider needs (Java plugin, your
   own `FileType`, etc.). The sandbox is preconfigured; production isn't.

Most "works in dev, broken in prod" cases reduce to step 7 (missing dependency) or step 1
(registration in the wrong file).

## Common mistakes

- `LineMarkerProvider` returning a marker on a composite element. Always leaf.
- `FoldingBuilder` not implementing `DumbAware`. Folds invisible during indexing.
- `FoldingBuilder` ignoring `quick = true` and doing resolution. Initial open is laggy.
- `Annotator` doing heavy work — switches to a stutter on every edit. Move to
  `LocalInspectionTool` if it can't be cheap.
- `IntentionAction.isAvailable` doing PSI resolution. Every Alt+Enter pays the cost.
- Mutating PSI/Document outside `WriteCommandAction`. No undo.
- Holding `Editor` references after `editorReleased`. Throws on next use.
- Using `Logical` coordinates where `Visual` is required (popups, gutter UI). Looks fine
  until folding kicks in.
- Not handling multi-caret (`runForEachCaret` or `MultiCaretCodeInsightAction`).
- Custom folding with `dependencies = emptySet()` when the placeholder text depends on
  another file or a tracker. Stale text after a change.

## Related references

- `05_file_model_psi_basics.md` — PSI walking and modification.
- `05_file_model_psi_references_caching.md` — `SmartPsiElementPointer`, `PsiReference`, and `CachedValue`.
- `07_language_pipeline.md` — custom-language implementation order.
- `04_threading_model.md` — read/write contracts; `DumbAware`, `smartReadAction`.
