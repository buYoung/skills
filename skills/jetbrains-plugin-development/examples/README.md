# Examples

Curated skeletons that show how the patterns from `references/` fit together as a working
plugin. Each folder is a **subset of source files** for one focused feature — not a
buildable Gradle project. The generated lexer/parser code, Gradle setup, and IDE icons are
intentionally omitted; with the BNF/flex sources here plus the Gradle setup from
`references/01_core_gradle_project.md`, the IntelliJ Platform Gradle Plugin generates the rest.

| Folder | Pairs with reference |
|---|---|
| `simple_language_plugin/` | `references/07_language_pipeline.md` end-to-end |
| `action_basics/` | `references/02_runtime_actions.md` |
| `settings_persistence/` | `references/08_ui_settings_persistent_state.md` and `references/08_ui_settings_configurable.md` |
| `inline_completion_provider/` | `references/07_language_inline_completion.md` |
| `folding_builder/` | `references/06_code_insight_folding.md` |

Read each example top-to-bottom alongside the matching reference. The reference explains
*why*; the example shows *how the pieces wire together*.

Package names are `com.example.<feature>` for clarity. Adjust to your own group when
copying.
