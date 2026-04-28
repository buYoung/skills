# Find Usages Provider

Read this when a plugin implements or fixes Find Usages, Rename participation, usage
grouping, or searchable names for a custom language.

## Required pieces

Find Usages needs cooperation between PSI and the usage provider:

- `PsiNamedElement` for declarations that can be searched.
- `PsiReference` for references that resolve to declarations.
- `FindUsagesProvider` registered with `com.intellij.lang.findUsagesProvider`.
- `WordsScanner` so the IDE can build a word index for candidate files.

`DefaultWordsScanner` is the usual starting point for custom languages: feed it the lexer and
token sets for identifiers, comments, and literals. The scanner determines which words are
indexed as code, comment, or literal occurrences.

## Presentation and scope

`FindUsagesProvider` controls whether an element supports Find Usages and how it is shown in
the dialog and results tree. Override `PsiNamedElement.getTextOffset()` when the declaration
text range includes syntax before the actual name.

For local symbols such as parameters and variables, consider narrowing `PsiElement.getUseScope()`
to the nearest meaningful scope. This avoids broad file parsing and makes Rename faster.

For better result grouping and labels, add `UsageTypeProvider` and `ElementDescriptionProvider`
when the default result text is ambiguous.

## Rename and Safe Delete dependency

Rename and Safe Delete depend on accurate Find Usages. If `PsiReference.isReferenceTo(...)`
is wrong, Rename misses usages or rewrites unrelated text. If `setName(...)` does not mutate
PSI correctly, the refactoring appears to run but leaves declarations unchanged.

## Diagnostics checklist

1. Confirm the declaration under the caret is a `PsiNamedElement` or resolves from a
   `PsiReference` to one.
2. Confirm `getName()` returns exactly the searchable identifier.
3. Confirm `getTextOffset()` points at the identifier, not at surrounding syntax.
4. Confirm the word scanner token sets classify identifiers correctly.
5. Confirm references resolve to the same declaration object or equivalent named element.
6. Confirm local declarations narrow `getUseScope()` where possible.

## Official docs

- https://plugins.jetbrains.com/docs/intellij/find-usages.html
- https://plugins.jetbrains.com/docs/intellij/find-usages-provider.html
