# Documentation Target API

Read this when a plugin provides Quick Documentation, hover documentation, documentation
links, or documentation actions for PSI or symbol targets.

## API boundary and version

The target-provider interfaces and their descriptor registrations are available to external
plugins in IntelliJ Community `idea/2026.2.2` at commit
`1c7e601c0423e544917046c23763b15d0282e2a3`. Register them through the qualified EP names in
[`LangExtensionPoints.xml`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/platform-resources/src/META-INF/LangExtensionPoints.xml);
their `EP_NAME` fields are `@ApiStatus.Internal` and must not be called by plugin code.
The declarations are
[`DocumentationTargetProvider`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/lang-impl/src/com/intellij/platform/backend/documentation/DocumentationTargetProvider.java),
[`PsiDocumentationTargetProvider`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/lang-impl/src/com/intellij/platform/backend/documentation/PsiDocumentationTargetProvider.java),
and [`SymbolDocumentationTargetProvider`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/lang-impl/src/com/intellij/platform/backend/documentation/SymbolDocumentationTargetProvider.java).
`SymbolDocumentationTargetProvider` is public but `@ApiStatus.Experimental` in this target;
prefer the stable `DocumentationTargetProvider` or `PsiDocumentationTargetProvider` when a
symbol-specific contract is unnecessary.

## API selection

For IntelliJ Platform 2023.1 and newer, prefer the Documentation Target API:

- `DocumentationTargetProvider` for targets derived from a file and offset.
- `PsiDocumentationTargetProvider` for targets derived from PSI elements.
- `SymbolDocumentationTargetProvider` for symbol-backed targets when the plugin's minimum IDE
  and experimental API risk are explicit.

Use `DocumentationProvider` only when supporting older IDE branches or maintaining legacy
code. It is obsolete for new 2023.1+ implementations.

## Target responsibilities

`DocumentationTarget` computes the rendered documentation, separate hover hints, and the
presentation shown in documentation UI. Documentation is returned as `DocumentationResult`,
usually containing HTML. Use `DocumentationMarkup` for consistent structure and
`HtmlSyntaxInfoUtil` when rendering lexer-highlighted code snippets.

`createPointer()` is mandatory for resilience across read actions. It must return a restorable
pointer or `null` when the underlying PSI or symbol is no longer valid.

## Asynchrony and remote resources

Documentation generation may be asynchronous when it would otherwise block the IDE. If the
content comes from external resources, keep cancellation, progress, and network failure in
mind. Do not fetch remote documentation from UI callbacks.

## Diagnostics checklist

1. Prefer the stable `platform.backend.documentation.*` target-provider EPs on 2023.1+; use
   the experimental symbol provider only when its symbol contract is required.
2. Confirm `createPointer()` handles invalid PSI and does not keep stale elements.
3. Confirm HTML is sanitized and structurally compatible with documentation UI.
4. Confirm lookup-item documentation returns the same target the user sees at the caret.
5. Confirm legacy `DocumentationProvider` code is retained only for older target branches.

## Official docs

- https://plugins.jetbrains.com/docs/intellij/documentation.html
