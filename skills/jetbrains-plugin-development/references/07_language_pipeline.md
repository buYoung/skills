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
pipeline. LSP integration is available only in products that ship the LSP module; declare
`<depends>com.intellij.modules.lsp</depends>` and verify that the target product includes it.

For `2026.1.4+` (including the `2026.2.2` baseline), use the public renamed API:

```kotlin
import com.intellij.openapi.project.Project
import com.intellij.openapi.vfs.VirtualFile
import com.intellij.execution.configurations.GeneralCommandLine
import com.intellij.platform.lsp.api.ProjectWideLspClientDescriptor
import com.intellij.platform.lsp.api.LspIntegrationProvider

class FooLspProvider : LspIntegrationProvider {
  override fun fileOpened(
    project: Project,
    file: VirtualFile,
    clientStarter: LspIntegrationProvider.LspClientStarter,
  ) {
    if (file.extension == "foo") {
      clientStarter.ensureClientStarted(FooLspDescriptor(project))
    }
  }
}

private class FooLspDescriptor(project: Project) : ProjectWideLspClientDescriptor(project, "Foo") {
  override fun isSupportedFile(file: VirtualFile) = file.extension == "foo"
  override fun createCommandLine() = GeneralCommandLine("foo", "--stdio")
}
```

Register the provider under the new extension point:

```xml
<extensions defaultExtensionNs="com.intellij">
  <platform.lsp.integrationProvider implementation="com.example.FooLspProvider"/>
</extensions>
```

For a plugin that still supports versions before `2026.1.4`, keep a version-specific source
adapter for the deprecated `LspServerSupportProvider`, `LspServerDescriptor`, and
`com.intellij.platform.lsp.serverSupportProvider` extension point. The old names remain
functional for compatibility, but the `2026.2.2` declarations mark them deprecated; do not
use them in a new implementation when the new public API is available. Do not call internal
helpers such as `LspIntegrationProvider.getAllExtensions()`.

`LspIntegrationProvider.fileOpened` is a background, read-locked callback in the fixed
source. Keep it quick and cancellable; do not block it on downloads or process startup.
Schedule slow work in a service scope and, after it completes, call the public
`LspClientManager.getInstance(project).startClientsIfNeeded(FooLspProvider::class.java)`
entry point. Do not retain the callback's `LspClientStarter` after `fileOpened` returns.

The new interface, starter, descriptor, and canonical extension point are public external
APIs in the `2026.2.2` source baseline. This is distinct from experimental or internal LSP
extension points. Verify the API and product module against the exact IDE version before
copying the example.

Kotlin-specific language services have an additional compatibility boundary. Analysis API is
available from `2024.2`, and K2 is the default Kotlin mode from `2025.1`; use the public
Analysis API for Kotlin semantic analysis and declare compatibility with K2. Do not depend on
Kotlin compiler implementation classes or use reflection to preserve a K1-only integration.

For a full lexer/parser/PSI pipeline rather than an LSP client, see
`examples/simple_language_plugin/` in this skill. The LSP snippet above assumes
`package com.example` and a server executable available to `GeneralCommandLine`.

The API names and deprecation boundary above were checked against the
[`idea/2026.2.2` source snapshot](https://github.com/JetBrains/intellij-community/tree/1c7e601c0423e544917046c23763b15d0282e2a3),
including [`LspIntegrationProvider`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/lsp/src/api/LspIntegrationProvider.kt),
[`LspClientDescriptor`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/lsp/src/api/LspClientDescriptor.kt),
[`ProjectWideLspClientDescriptor`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/lsp/src/api/ProjectWideLspClientDescriptor.kt),
[`LspClientManager`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/lsp/src/api/LspClientManager.kt),
[`LspServerSupportProvider`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/lsp/src/api/LspServerSupportProvider.kt),
and the [LSP extension-point descriptor](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/lsp-impl/resources/intellij.platform.lsp.impl.xml),
with its [public API module](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/lsp/resources/intellij.platform.lsp.xml),
as well as the [LSP SDK guide](https://plugins.jetbrains.com/docs/intellij/language-server-protocol.html)
and the [2026 API change list](https://plugins.jetbrains.com/docs/intellij/api-changes-list-2026.html).
