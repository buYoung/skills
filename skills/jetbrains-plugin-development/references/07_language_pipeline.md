# Custom Language Pipeline

Read this when you are adding a new language or DSL to a JetBrains IDE — i.e., you own the
file extension, the lexer, the parser, the PSI hierarchy, and most user-facing analysis on
top. The reference cross-cuts a lot of platform surface area; the order below is the
sequence in which you should normally implement things.

## Pipeline at a glance

```
VirtualFile
   ↓  (FileType match)
Language ─→ Lexer ─→ Parser ─→ ParserDefinition ─→ PsiFile / PsiElement tree
                                                       ↓
                                  SyntaxHighlighter (color)
                                  Annotator        (semantic)
                                  CompletionContributor
                                  PsiReference / ReferenceContributor
                                  Code insights (folding, line marker, ...)
                                  Refactoring, etc.
```

## LSP-backed languages

If a mature Language Server Protocol server already exists and the user is not trying to own
the lexer/parser/PSI stack, consider the platform LSP layer instead of a full custom-language
pipeline. For experimental implementations, extend `LspServerSupportProvider` and register
`<platform.lsp.serverSupportProvider>`.

LSP support is `@Experimental`; verify the API against the exact IDE version you target.

Reference implementation: `examples/simple_language_plugin/` in this skill.
