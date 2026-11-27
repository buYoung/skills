# Examples

Curated skeletons that show how the patterns from `references/` fit together as a working
plugin. Each folder is a **subset of source files** for one focused feature — not a
buildable Gradle project. The generated lexer/parser code, Gradle setup, and IDE icons are
intentionally omitted. In `simple_language_plugin/`, the Grammar-Kit sub-plugin
(`org.jetbrains.intellij.platform.grammarkit`, see `references/01_core_gradle_project.md`)
generates `SimpleLexer`, `SimpleParser`, `SimpleTypes`, and the PSI classes from
`Simple.flex` and `Simple.bnf`; the hand-written element types and the `property` mixin it
references are included.

Apply the [public API baseline](../references/00_public_api_baseline.md) before copying any
snippet. Re-check every API, superclass, and extension point against the exact target IDE;
examples that use a public `@ApiStatus.Experimental` contract state their version requirement
in the paired reference.

| Folder | Pairs with reference |
|---|---|
| `simple_language_plugin/` | `references/07_language_pipeline.md` end-to-end |
| `action_basics/` | `references/02_runtime_actions.md` |
| `settings_persistence/` | `references/08_ui_settings_persistent_state.md` and `references/08_ui_settings_configurable.md` |
| `inline_completion_provider/` | `references/07_language_inline_completion.md` |
| `folding_builder/` | `references/06_code_insight_folding.md` |

Read each example top-to-bottom alongside the matching reference. The reference explains
*why*; the example shows *how the pieces wire together*.

Package names and plugin IDs are `com.example.<feature>` for clarity. Adjust both to your own
group when copying; Plugin Verifier rejects the `com.example` plugin ID prefix
(`ForbiddenPluginIdPrefix`).
