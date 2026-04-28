# Custom Language Diagnostics

## Common mistakes

- `language="java"` (lowercase) instead of `"JAVA"`. Silent miss.
- Reusing one `Lexer` instance across calls. Lexers are stateful — `new` per use.
- BNF mixin work edited in the *generated* `*Impl` files. Lost on regeneration.
- Annotator that does heavy resolution without caching. Visible stutter while typing.
- Returning `PsiReference[]` of length `> 0` from `getReferencesByElement` for elements
  outside your text range. Confuses Find Usages.
- Implementing `PsiNamedElement.setName(...)` as a no-op. Rename appears to "do nothing"
  silently.
- Forgetting `<colorSettingsPage>` — users can't theme your colors.
- Skipping `BAD_CHARACTER` from the lexer. Invalid characters slip past unhighlighted.

## Related references

- `05_file_model_psi_basics.md` — PSI fundamentals.
- `05_file_model_indexing_stubs.md` — indexes and stub-based lookup.
- `05_file_model_uast.md` — cross-JVM-language analysis.
- `06_code_insight_folding.md`, `06_code_insight_formatter_commenter.md`,
  `06_code_insight_inspections_intentions_quick_fixes.md`, and
  `06_code_insight_refactoring_documentation_structure.md` — folding, formatter,
  inspections, intentions, and refactoring.
- `01_core_plugin_xml.md` — XML registration mechanics.
- `04_threading_model.md` — read/write rules for analyzers.
