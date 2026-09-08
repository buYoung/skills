# Public API and Version Baseline

Read this before selecting APIs or applying a version migration. The public API boundary
in `../SKILL.md` governs every reference and example, including older-version guidance.

## Source identity

- Repository: [JetBrains/intellij-community](https://github.com/JetBrains/intellij-community).
- Fixed source tag: [`idea/2026.2.2`](https://github.com/JetBrains/intellij-community/tree/idea/2026.2.2).
- Resolved commit: [`1c7e601c0423e544917046c23763b15d0282e2a3`](https://github.com/JetBrains/intellij-community/commit/1c7e601c0423e544917046c23763b15d0282e2a3).
- Tag identity checked through the [GitHub ref API](https://api.github.com/repos/JetBrains/intellij-community/git/ref/tags/idea/2026.2.2) on 2026-09-08.
- SDK and Gradle documentation are live sources, not snapshots of this commit. Record their
  applicable versions separately; a current page can describe changes newer than 2026.2.2.

The repository name does not establish availability in a particular IDE product or edition.
Resolve the target product/build, dependencies, minimum IDE version, Gradle plugin version,
and Java/Kotlin toolchain before adapting an example. Keep 2024.1-era guidance only where
its documented contract still applies; do not project current dispatcher, LSP, or Kotlin
frontend behavior onto that branch.

## How to establish external availability

For each changed API, record the member/signature or EP, intended operation (call, override,
implementation, or registration), minimum and target version, source permalink, and status.
Inspect the member and enclosing declarations, supertypes, package-level restrictions,
module visibility/exports, documentation, and EP metadata. Visibility and an `-api` directory
are clues, not proof; a type in a module declared `visibility="internal"` is not a supported
external dependency simply because its Kotlin declaration is public or experimental.
An `impl` package name or internal calls inside a library implementation is not by itself
proof that a documented external base class is forbidden. Check the supported public member
contract and its actual restrictions; apply the same evidence standard to allowing and
rejecting a candidate.
`Internal` or `IntellijInternalApi` at an applicable boundary rejects the candidate; a
`NonExtendable` type may be consumed but not implemented, while an `OverrideOnly` callback
may be overridden but not called as a client operation.

For a supported declarative EP, its platform-owned descriptor bean may itself be an
implementation detail. Register the documented XML; do not instantiate or access that bean.
Conversely, a dynamic EP is not necessarily external-public. Inspect API-status metadata
as well as its dynamic flag.

Separate availability from stability. External `Experimental` APIs still require version
qualification and may change without compatibility guarantees. Never accept an internal
API merely because it also carries `Experimental`, because the user accepts risk, or
because Plugin Verifier exits successfully. Keep unresolved candidates out of recommended
examples and state the public alternative's functional limits.

Official policy: [Internal API Migration](https://plugins.jetbrains.com/docs/intellij/api-internal.html),
[API status and compatibility](https://plugins.jetbrains.com/docs/intellij/verifying-plugin-compatibility.html),
and [2026 API changes](https://plugins.jetbrains.com/docs/intellij/api-changes-list-2026.html).

## Evidence routing

The relevant capability references carry source links and version-specific contracts:

| Area | Read | Boundary to preserve |
|---|---|---|
| Dispatchers, locks, actions | `04_threading_model.md`, `04_threading_coroutines_2024.md`, `04_threading_read_write_actions.md`, `02_runtime_actions.md` | Thread affinity, lock acquisition, modality, cancellation, lifetime, and undo are separate requirements. |
| Gradle and generators | `01_core_gradle_project.md`, `07_language_grammar_kit_bnf.md` | IDE source baseline is independent of Gradle/generator versions; rebuilding is separate from reload. |
| Disk visibility | `05_file_model_documents.md`, `05_file_model_vfs.md` | Document commit, document save, VFS write completion, and external-process visibility are distinct. |
| LSP and Kotlin | `07_language_pipeline.md`, `01_core_dependencies.md`, `05_file_model_uast.md` | Check product/module availability and minimum-version route, plus K2 compatibility. |
| Inline and Next Edit | `07_language_inline_completion.md`, `07_language_next_edit_suggestions.md` | No internal-provider or direct-call bypass, even with risk acceptance. |
| API/EP review | Provider-specific `06_*`–`10_*` references | Check base types, called members, and registered EP metadata individually. |
| Terminal | `10_execution_process_console_terminal.md` | Prefer console APIs for process output; Reworked Terminal APIs are versioned, experimental, and contain internal members that remain forbidden. |
| Completion evidence | `11_distribution_plugin_verifier.md`, `11_distribution_dynamic_plugins_classloaders.md` | Static compatibility, runtime feature behavior, and unload observations are independent. |

## Additional pinned declaration checks

These findings apply to the pinned 2026.2.2 declarations, not automatically to every older branch.

| API or EP | Status and resulting guidance | Source at the fixed commit |
|---|---|---|
| `MergeRequestProcessor` | `Internal`; remove the implementation-class recommendation. Use public `DiffManager` display methods; an embedded diff panel is not an equivalent embedded merge processor. | [Processor](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/diff-impl/src/com/intellij/diff/merge/MergeRequestProcessor.java), [DiffManager](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/diff-api/src/com/intellij/diff/DiffManager.java) |
| `DynamicBundle(Class, String)` and inherited `getMessage` | Public entry points. Prefer delegation; the single-string inheritance constructor is `Obsolete`. Do not call internal cache/bundle helpers or extend `AbstractBundle` directly. | [DynamicBundle](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/core-api/src/com/intellij/DynamicBundle.java), [AbstractBundle](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/util/src/com/intellij/AbstractBundle.kt) |
| `com.intellij.languageBundle` | Internal language-pack surface, backed by `DynamicBundle.LanguageBundleEP` marked `Internal`; remove external registration advice. Localize the plugin's own bundles instead. | [Core.analyzer.xml](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/core-api/resources/META-INF/Core.analyzer.xml), [bean](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/core-api/src/com/intellij/DynamicBundle.java) |
| `internalFileTemplate`, `defaultLiveTemplates` | Supported declarative EPs; retain XML examples. Neither EP is marked internal; do not access the Kotlin-internal live-template bean. | [LangExtensionPoints.xml](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/platform-resources/src/META-INF/LangExtensionPoints.xml), [InternalTemplateBean](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/lang-impl/src/com/intellij/ide/fileTemplates/InternalTemplateBean.java), [DefaultLiveTemplateEP](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/lang-impl/src/com/intellij/codeInsight/template/impl/DefaultLiveTemplateEP.kt) |
| `DynamicPluginListener.beforePluginLoaded` / `pluginUnloaded` | Public callbacks; retain listener example. Consume the supplied `IdeaPluginDescriptor`; its `NonExtendable` contract forbids implementing it. This does not authorize other descriptor members. | [Listener](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/core-api/src/com/intellij/ide/plugins/DynamicPluginListener.kt), [descriptor](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/core-api/src/com/intellij/ide/plugins/IdeaPluginDescriptor.java) |

## Verification limits

Source review establishes the inspected contracts only. It does not compile a plugin,
run its feature, prove support across all IDE versions, or demonstrate dynamic unload.
The bundled examples are partial integration skeletons, not independent build projects.
Record which declaration checks, local consistency checks, builds, verifier runs, and
sandbox exercises actually occurred. Never promote an unrun check to a passing result.
