---
name: jetbrains-plugin-development
description: >-
  IntelliJ Platform plugin development for JetBrains IDEs. Use when writing, debugging,
  or migrating a JetBrains plugin — `plugin.xml`, services, actions, PSI/VFS/Document,
  EDT/BGT threading and Read/Write actions, Kotlin coroutines on the IDE platform,
  custom languages (Grammar-Kit, JFlex, lexer/parser, syntax highlighting, completion,
  references), code insight (folding, inspections, intentions, inline completion,
  inlay hints), Kotlin UI DSL v2, tool windows, settings, run/debug configurations,
  External System (Gradle/Maven), IntelliJ Platform Gradle Plugin 2.x, dynamic reload,
  Plugin Verifier, signing, and Marketplace publishing; legacy migrations
  (`ApplicationComponent`, `getCoroutineScope`, raw `Thread`/`ExecutorService`). Not
  for end-user IDE configuration or vmoptions tuning.
---

# JetBrains IDE Plugin Development (IntelliJ Platform SDK)

This skill carries the IntelliJ Platform SDK domain knowledge needed to write, debug, and modify
JetBrains IDE plugins competently. It is opinionated toward 2024.1+ targets (Kotlin coroutines,
IntelliJ Platform Gradle Plugin 2.x, light services with `@Service`, dynamic plugin defaults) and
calls out where pre-2024.1 patterns are still required.

## How to use this skill

1. Read the **mental model** below — it is small but governs almost every decision.
2. Pick the reference file from the **Capability index** that matches the task and read it before editing.
3. For end-to-end shapes — how the registrations, classes, and `plugin.xml` of a feature line up — open the matching folder under `examples/`.
4. Before declaring any plugin-modifying task done, walk the **Pre-flight checklist**.

Do not invent extension point names, attribute names, or API signatures. The Platform is highly
specific about strings (`language="JAVA"` vs `"java"`, EP IDs, attribute spellings); a wrong
character is enough to silently disable a feature. When unsure, surface the question to the user
with the relevant reference cited — and verify the spelling in the IDE's `plugin.xml` editor,
which auto-completes valid EP names from the loaded plugin set and underlines unknown ones.

## Mental model — five invariants you must hold

These five invariants explain almost every "why doesn't this work?" question.

1. **`plugin.xml` is the contract.** A class is invisible to the IDE until it is registered.
   `@Service`, `@Service(cs)` annotations and a few `META-INF/` filename conventions are the
   only exceptions; everything else (extensions, listeners, actions, EPs you define, dependencies)
   must appear in `plugin.xml` (or a `config-file` of an `<depends optional>` block).
2. **Extensions are stateless; services hold state.** EP implementations are constructed once
   per scope and shared across all calls and threads. Storing mutable state on an extension
   leaks across projects, threads, and dynamic reloads. Put state in a service
   (`@Service` / `@Service(Service.Level.PROJECT)`), and have extensions look it up on demand.
3. **Threading is non-negotiable.** Reading platform model state (PSI, VFS, Document, project model)
   needs a Read Lock. Writing needs a Write Lock and **must** start on the EDT (or via the
   suspending `writeAction`/`backgroundWriteAction`). Long work belongs on a background thread
   with progress and cancellation. EDT freezes are user-visible; lock violations are immediate
   exceptions or data corruption. New code on 2024.1+ uses Kotlin coroutines
   (`Dispatchers.EDT`, `readAction { }`, `writeAction { }`, `cs.launch { }`).
4. **`Disposer` is how lifecycle works.** Resources tie into a `Disposable` parent and the
   platform calls `dispose()` post-order when the parent goes away. Services are usually the
   right parent. Never use `Application` or `Project` directly as a parent — that traps
   resources past plugin unload and leaks the classloader. `CoroutineScope` injection on a
   `@Service` is the modern alternative to `Disposable`.
5. **Dynamic plugin reload imposes hard constraints.** The default since 2020.1 is
   `require-restart="false"`. To stay reloadable: every EP your plugin contributes to and
   defines must be dynamic, no static caches of plugin classes, no `object` singletons holding
   state, no listeners parented to `Application`/`Project`, no `overrides="true"` services.

## Capability index

Use this section as a router. Do not bulk-read every reference. Start with the single most specific reference below, then add companion references only when the task crosses that boundary.

Reference filenames are prefixed by category for fast scanning: `01_core`, `02_runtime`,
`03_lifecycle`, `04_threading`, `05_file_model`, `06_code_insight`, `07_language`,
`08_ui`, `09_project`, `10_execution`, and `11_distribution`.

- [01_core_gradle_project.md](references/01_core_gradle_project.md): Project setup, IntelliJ Platform Gradle Plugin 2.x, sandbox IDE, generated helper tasks, multi-module project shape.
- [01_core_plugin_xml.md](references/01_core_plugin_xml.md): `plugin.xml`, required descriptor elements, file naming conventions, and descriptor blocks for listeners/actions.
- [01_core_dependencies.md](references/01_core_dependencies.md): `<depends>`, optional dependency config files, `sinceBuild`, `untilBuild`, and platform branch targeting.
- [01_core_extensions.md](references/01_core_extensions.md): Using, ordering, iterating, defining, or discovering extension points.
- [01_core_extension_diagnostics.md](references/01_core_extension_diagnostics.md): Plugin loading lifecycle and diagnosing extensions that are registered but ignored.
- [01_core_split_mode_remote_development.md](references/01_core_split_mode_remote_development.md): Split Mode, Remote Development, frontend/backend/shared modules, RPC boundaries, and split sandbox runs.
- [02_runtime_services.md](references/02_runtime_services.md): Light services, constructor rules, state holders, service-scoped `CoroutineScope`, and persistent-state handoff.
- [02_runtime_listeners_message_bus.md](references/02_runtime_listeners_message_bus.md): Declarative listeners, `MessageBus`, `Topic`, manual subscriptions, and listener lifetime.
- [02_runtime_actions.md](references/02_runtime_actions.md): `AnAction`, `update`, `ActionUpdateThread`, action groups, keymaps, and action skeletons.
- [02_runtime_typed_handlers_editor_actions.md](references/02_runtime_typed_handlers_editor_actions.md): `TypedHandlerDelegate`, `EditorActionHandler`, typing interception, autopopup routing, and multi-caret editor actions.
- [02_runtime_legacy_component_migration.md](references/02_runtime_legacy_component_migration.md): Migrating `ApplicationComponent`, `ProjectComponent`, or `ModuleComponent` to services, extensions, listeners, and startup activities.
- [02_runtime_deprecated_api_migrations.md](references/02_runtime_deprecated_api_migrations.md): Deprecated listener, coroutine-scope, action, and Plugin DevKit migration checks.
- [03_lifecycle_disposer.md](references/03_lifecycle_disposer.md): `Disposable` trees, safe parent selection, cleanup patterns, `Alarm`, and disposal triggers.
- [03_lifecycle_leak_diagnostics.md](references/03_lifecycle_leak_diagnostics.md): Disposer leak debugging, `LeakHunter`, sandbox checks, and leak-prone patterns.
- [04_threading_model.md](references/04_threading_model.md): EDT/BGT mental model, lock rules, dumb mode overview, and threading invariants.
- [04_threading_read_write_actions.md](references/04_threading_read_write_actions.md): Classic read/write actions, `ReadAction.nonBlocking`, `WriteCommandAction`, `invokeLater`, modality, and annotations.
- [04_threading_background_work_progress.md](references/04_threading_background_work_progress.md): `Task.Backgroundable`, progress indicators, cancellation, synchronous progress, and fire-and-forget work.
- [04_threading_coroutines_2024.md](references/04_threading_coroutines_2024.md): 2024.1+ coroutine APIs, `Dispatchers.EDT`, suspending read/write actions, progress, and `runBlockingCancellable`.
- [04_threading_thread_to_coroutine_migration.md](references/04_threading_thread_to_coroutine_migration.md): Replacing `Thread`, `ExecutorService`, and `Task.Backgroundable` with coroutine-based code.
- [04_threading_diagnostics.md](references/04_threading_diagnostics.md): Threading symptoms, common mistakes, best practices, and import map for suspending APIs.
- [05_file_model_vfs.md](references/05_file_model_vfs.md): `VirtualFile`, file lookup, refresh, listeners, VFS lifecycle, and identity.
- [05_file_model_documents.md](references/05_file_model_documents.md): `Document`, document lookup, reads, writes, synchronization with PSI, listeners, and guarded ranges.
- [05_file_model_psi_basics.md](references/05_file_model_psi_basics.md): `PsiElement`, PSI lookup, tree walking, modifications, whitespace, and formatting.
- [05_file_model_psi_references_caching.md](references/05_file_model_psi_references_caching.md): `SmartPsiElementPointer`, `PsiReference`, named elements, multi-language files, and `CachedValue`.
- [05_file_model_uast.md](references/05_file_model_uast.md): UAST for cross-JVM-language analysis (one inspection/line marker covering Java, Kotlin, Scala, Groovy), `UElement`/`UMethod`/`UCallExpression`, `sourcePsi` vs `javaPsi`, `AbstractBaseUastLocalInspectionTool`, and `UastHintedVisitorAdapter`.
- [05_file_model_indexing_stubs.md](references/05_file_model_indexing_stubs.md): Dumb Mode, smart mode, `FileBasedIndex`, stub indexes, and `AstLoadingFilter`.
- [05_file_model_psi_diagnostics.md](references/05_file_model_psi_diagnostics.md): Common VFS, Document, PSI, index, and cache failure modes.
- [06_code_insight_editor_model.md](references/06_code_insight_editor_model.md): `Editor`, caret, selection, multi-caret behavior, and editor coordinate systems.
- [06_code_insight_editor_markup_lifecycle.md](references/06_code_insight_editor_markup_lifecycle.md): `RangeMarker`, `MarkupModel`, `RangeHighlighter`, scrolling, editor lifecycle, console filters, and guarded blocks.
- [06_code_insight_file_editor_provider.md](references/06_code_insight_file_editor_provider.md): `FileEditorProvider`, custom editor tabs, preview editors, fake files, and editor disposal.
- [06_code_insight_line_markers.md](references/06_code_insight_line_markers.md): `LineMarkerProvider`, gutter icons, leaf-element rules, slow markers, and Dumb Mode behavior.
- [06_code_insight_folding.md](references/06_code_insight_folding.md): `FoldingBuilder`, descriptors, callbacks, custom folding settings, non-owned languages, and missing-fold diagnostics.
- [06_code_insight_formatter_commenter.md](references/06_code_insight_formatter_commenter.md): `FormattingModelBuilder` + `Block` (indent/wrap/`SpacingBuilder`/`getChildAttributes`) for `Ctrl+Alt+L`, and `Commenter` for `Ctrl+/` line/block comment toggles.
- [06_code_insight_inspections_intentions_quick_fixes.md](references/06_code_insight_inspections_intentions_quick_fixes.md): `LocalInspectionTool`, inspections, intentions, and quick fixes.
- [06_code_insight_inspection_options_suppression.md](references/06_code_insight_inspection_options_suppression.md): Declarative inspection options, legacy options panels, description files, and suppression guardrails.
- [06_code_insight_refactoring_documentation_structure.md](references/06_code_insight_refactoring_documentation_structure.md): `RefactoringSupportProvider` and Rename/Safe Delete/Inline preconditions tied to `PsiNamedElement.setName`, Find Usages, and `PsiReference.isReferenceTo`.
- [06_code_insight_documentation_target_api.md](references/06_code_insight_documentation_target_api.md): `DocumentationTarget`, PSI/symbol documentation providers, hover documentation, pointers, and legacy migration.
- [06_code_insight_parameter_info_and_navigation.md](references/06_code_insight_parameter_info_and_navigation.md): `ParameterInfoHandler`, structure view, breadcrumbs, choose-by-name, and spellchecking.
- [06_code_insight_surround_with.md](references/06_code_insight_surround_with.md): `SurroundDescriptor`, `Surrounder`, selection-based code wrapping, and caret/formatting rules.
- [06_code_insight_diagnostics.md](references/06_code_insight_diagnostics.md): Generic "why does my code-insight provider do nothing?" debug flow (EP/language match, construction, threading, Dumb Mode, ordering, prod-only missing dependencies) plus cross-cutting `LineMarkerProvider`/`FoldingBuilder`/`Annotator`/`IntentionAction` pitfalls.
- [07_language_pipeline.md](references/07_language_pipeline.md): End-to-end pipeline for adding a new language/DSL (FileType → Lexer → Parser → ParserDefinition → PSI → highlighter/annotator/completion/references/code insights), LSP-backed alternatives, and the order to implement them.
- [07_language_file_type.md](references/07_language_file_type.md): `Language` singleton, `LanguageFileType`, case-sensitive Language ID, and `<fileType>` registration with mandatory `fieldName="INSTANCE"`.
- [07_language_lexer_jflex.md](references/07_language_lexer_jflex.md): JFlex `.flex` files, `FlexLexer`/`FlexAdapter`, `%unicode` requirement, `--charat` Gradle flag, and `TokenType.WHITE_SPACE`/`BAD_CHARACTER` conventions.
- [07_language_grammar_kit_bnf.md](references/07_language_grammar_kit_bnf.md): Grammar-Kit BNF — generated parser/PSI/element-type holder, `psiClassPrefix`/`psiPackage`/`elementTypeHolderClass` settings, `mixin` classes for custom logic (never edit generated `*Impl`), and hand-rolled `PsiParser` skeleton.
- [07_language_parser_definition_psi_file.md](references/07_language_parser_definition_psi_file.md): `ParserDefinition` wiring (lexer/parser/`IFileElementType`/comment & whitespace token sets/element factory), `PsiFileBase` root file, and `<lang.parserDefinition>` registration.
- [07_language_syntax_highlighting.md](references/07_language_syntax_highlighting.md): Lexer-based syntax highlighting (`SyntaxHighlighterBase`, `TextAttributesKey` with `DefaultLanguageHighlighterColors` fallbacks), `<lang.syntaxHighlighterFactory>` registration, and `ColorSettingsPage` for user-themable colors.
- [07_language_annotator.md](references/07_language_annotator.md): `Annotator` for PSI-based semantic warnings/errors, `AnnotationHolder` builder API (`.create()` is mandatory), Annotator vs `LocalInspectionTool` decision, and stateless/cheap/cached-resolution rules.
- [07_language_highlighting_filters.md](references/07_language_highlighting_filters.md): `HighlightInfoFilter`, syntax/error highlighting suppression, external annotator filters, and false-positive control.
- [07_language_completion.md](references/07_language_completion.md): `CompletionContributor`, `CompletionType` (BASIC/SMART/CLASS_NAME), `CompletionParameters`/`CompletionResultSet`, `LookupElementBuilder`, prefix matchers, `runRemainingContributors`, and `<completion.contributor>` registration.
- [07_language_inline_completion.md](references/07_language_inline_completion.md): `InlineCompletionProvider`, gray inline suggestions, provider registration, debounce, direct calls, and update behavior.
- [07_language_next_edit_suggestions.md](references/07_language_next_edit_suggestions.md): Next Edit Suggestions, internal awaiter boundaries, direct-call routing, and public API guardrails.
- [07_language_postfix_templates.md](references/07_language_postfix_templates.md): `PostfixTemplateProvider`, postfix completion registration, description resources, and applicability diagnostics.
- [07_language_references_resolution.md](references/07_language_references_resolution.md): `PsiReference`, `PsiReferenceContributor`, multi-resolve, and search support.
- [07_language_find_usages_provider.md](references/07_language_find_usages_provider.md): `FindUsagesProvider`, `WordsScanner`, usage presentation, result grouping, Rename, and Safe Delete prerequisites.
- [07_language_element_patterns.md](references/07_language_element_patterns.md): `PlatformPatterns`/`StandardPatterns`/`PsiJavaPatterns` matcher DSL — gating completion and reference contributors via `.withParent`/`.withSuperParent`/`.afterLeaf`/`.afterSibling`/custom `PatternCondition`.
- [07_language_injection.md](references/07_language_injection.md): `MultiHostInjector` for injecting another language into string literals (regex inside Java strings, SQL inside Kotlin templates) so the inner language gets full PSI/completion/inspection.
- [07_language_code_vision_inlay_hints_polysymbols.md](references/07_language_code_vision_inlay_hints_polysymbols.md): Inline editor hints — `DeclarativeInlayHintsProvider` (2023.2+) and legacy `<inlayHintsProvider>` for parameter/type hints, `<codeVision.provider>` for usages/refs counts, and Polysymbols for polyglot web files.
- [07_language_custom_language_diagnostics.md](references/07_language_custom_language_diagnostics.md): Custom-language pitfalls — `language=` casing (`"JAVA"` vs `"java"`), reused stateful `Lexer`, BNF mixin work in generated `*Impl`, uncached annotator resolution, no-op `setName`, missing `BAD_CHARACTER` and `<colorSettingsPage>`.
- [08_ui_surface_selection.md](references/08_ui_surface_selection.md): Choosing between Kotlin UI DSL, JB Swing components, actions, or standard Swing fallback.
- [08_ui_settings_persistent_state.md](references/08_ui_settings_persistent_state.md): `PersistentStateComponent`, `BaseState`, immutable state, `@State`, `@Storage`, and `PasswordSafe`.
- [08_ui_settings_configurable.md](references/08_ui_settings_configurable.md): `Configurable` settings pages.
- [08_ui_kotlin_ui_dsl.md](references/08_ui_kotlin_ui_dsl.md): Kotlin UI DSL v2 panels and bindings.
- [08_ui_dialogs.md](references/08_ui_dialogs.md): `DialogWrapper` and modal dialogs.
- [08_ui_tool_windows.md](references/08_ui_tool_windows.md): `ToolWindowFactory` and tool-window content.
- [08_ui_jcef_embedded_browser.md](references/08_ui_jcef_embedded_browser.md): `JBCefBrowser`, support checks, browser/client disposal, handlers, and JavaScript bridge safety.
- [08_ui_layout_helpers.md](references/08_ui_layout_helpers.md): `JBSplitter`, `JBTabs`, and layout helpers.
- [08_ui_choosers.md](references/08_ui_choosers.md): File, class, and reference choosers.
- [08_ui_tables.md](references/08_ui_tables.md): `JBTable`, `TableView`, and `ListTableModel`.
- [08_ui_status_bar_widgets.md](references/08_ui_status_bar_widgets.md): Status bar widgets and editor-based popup widgets.
- [08_ui_drag_and_drop.md](references/08_ui_drag_and_drop.md): `DnDSupport`.
- [08_ui_notifications.md](references/08_ui_notifications.md): `Notification` and `EditorNotificationProvider`.
- [08_ui_icons.md](references/08_ui_icons.md): Standard platform icon constants (`IconLoader.getIcon(...)`), SVG resources under `resources/icons/`, dark-theme `_dark.svg` pairing, size conventions, and `AllIcons.*` catalog.
- [08_ui_theme_metadata_named_colors.md](references/08_ui_theme_metadata_named_colors.md): `JBColor`, named colors, `themeMetadataProvider`, custom theme keys, and theme-change-safe color lookup.
- [08_ui_data_context.md](references/08_ui_data_context.md): `UiDataProvider` and `DataContext`.
- [08_ui_diagnostics.md](references/08_ui_diagnostics.md): UI/settings/notification pitfalls — `BaseState` `var` fields, missing `@JvmField` on `SerializablePersistentStateComponent`, `roamingType` rules, `Configurable.apply` not flushing, leaked `Configurable` panels holding `Editor`/`Project`, non-`DumbAware` `ToolWindowFactory`, missing `<notificationGroup>`.
- [09_project_basics.md](references/09_project_basics.md): `Project` lookup and lifecycle (`e.project`, service injection, `ProjectManager.getInstance()`, `defaultProject` caveats), `messageBus`, and `isDisposed`/`isOpen`.
- [09_project_modules_roots_file_index.md](references/09_project_modules_roots_file_index.md): `Module`, roots, content entries, order entries, and `ProjectFileIndex`.
- [09_project_libraries_sdks_facets.md](references/09_project_libraries_sdks_facets.md): `LibraryTablesRegistrar` and modifying libraries via Write Action, `AdditionalLibraryRootsProvider`/`SyntheticLibrary`, `ProjectJdkTable` and custom `SdkType`/`ProjectSdkSetupValidator`, and `FacetManager`/`FacetType` for per-module tech config.
- [09_project_workspace_model.md](references/09_project_workspace_model.md): Modern entity-based project structure — `ImmutableEntityStorage`/`MutableEntityStorage`, `WorkspaceEntity` subclasses (`ModuleEntity`, `ContentRootEntity`, `LibraryEntity`), suspend `WorkspaceModel.update`, change `Flow<VersionedStorageChange>`, and `SymbolicEntityId`/`ExternalMappingKey` for external-system tracking.
- [09_project_view.md](references/09_project_view.md): Project View tree customization — `TreeStructureProvider` to re-bucket/hide/decorate children, `ProjectViewNodeDecorator` for suffix/icon overlays, `AbstractProjectViewPane` for custom panes, and public selection helpers without internal pane extractor APIs.
- [09_project_lifecycle.md](references/09_project_lifecycle.md): Project lifecycle hooks — `ProjectActivity` (suspend) and `StartupActivity.DumbAware` via `<postStartupActivity>`, `ProjectManagerListener`, `ModuleListener`, `ModuleRootListener`.
- [09_project_model_diagnostics.md](references/09_project_model_diagnostics.md): Project-model pitfalls — `defaultProject` misuse, holding `Project` references on application-level state, root-model edits outside Write Action, missing `model.commit()`/`dispose()`, EDT iteration of `ProjectFileIndex`, ignoring `isExcluded`, non-`DumbAware` `StartupActivity`.
- [10_execution_run_debug_configurations.md](references/10_execution_run_debug_configurations.md): Run/debug configurations, factories, `RunProfileState`, runners, run line markers, and before-run tasks.
- [10_execution_process_console_terminal.md](references/10_execution_process_console_terminal.md): `ProcessHandler`, `ConsoleView`, filters, and embedded terminal.
- [10_execution_external_system_integration.md](references/10_execution_external_system_integration.md): External System API for Gradle/Maven-style project importers.
- [10_execution_xml_dom_api.md](references/10_execution_xml_dom_api.md): DOM API for typed XML configs (Spring beans, custom XML DSLs) — `DomElement` interfaces with `@Attribute`/`@Required`/`GenericAttributeValue`, `DomFileDescription`, `Converter`/`ResolvingConverter` for reference resolution, and `<dom.fileDescription>`/`<dom.extender>`.
- [10_execution_ide_infrastructure_apis.md](references/10_execution_ide_infrastructure_apis.md): Error reporting, lifecycle listeners, paths, browser launcher, HTTP helpers, power-save mode, and web help.
- [10_execution_search_everywhere_api.md](references/10_execution_search_everywhere_api.md): Search Everywhere result providers, Remote Development-compatible APIs, serializable presentations, and migration from legacy contributors.
- [10_execution_diagnostics.md](references/10_execution_diagnostics.md): Run/debug & integration pitfalls — `RunProfileState.execute` running on EDT, missing `ProcessTerminatedListener.attach` (no exit-code line), global `OkHttpClient` on a service blocking unload, DOM `isMyFile` namespace bugs, EDT-bound `ErrorReportSubmitter`/`HttpRequests`.
- [11_distribution_dynamic_plugins_classloaders.md](references/11_distribution_dynamic_plugins_classloaders.md): Dynamic plugin requirements, reload verification, and classloader rules.
- [11_distribution_i18n_resource_bundles.md](references/11_distribution_i18n_resource_bundles.md): Resource bundles, localized strings, `@Nls`, and language-pack contributions.
- [11_distribution_file_live_templates.md](references/11_distribution_file_live_templates.md): `<internalFileTemplate>` for New-File templates (Velocity `.ft` files under `resources/fileTemplates/internal/`, name must match) and `<defaultLiveTemplates>` XML at `resources/liveTemplates/`.
- [11_distribution_vcs_extensions.md](references/11_distribution_vcs_extensions.md): VCS plugin EPs — `AbstractVcs`, `ChangeProvider`, `VcsDirtyScopeManager`, `ContentRevision`/`FilePath`/`VcsRevisionNumber`, `VcsRoot`/`VcsRootChecker`, diff/merge tools, and when to extend the existing Git plugin via `<depends optional config-file>` instead of a new `AbstractVcs`.
- [11_distribution_plugin_verifier.md](references/11_distribution_plugin_verifier.md): `verifyPlugin` Gradle task (2.x replacement for `runPluginVerifier`) — `pluginVerification.ides { recommended()/create()/local() }`, blocking issues (missing classes, `@Internal` usage from outside, plugin-class static reachability) vs informational `@Experimental` warnings.
- [11_distribution_plugin_signing_marketplace.md](references/11_distribution_plugin_signing_marketplace.md): Plugin signing and Marketplace publishing.
- [11_distribution_deployment_checklist.md](references/11_distribution_deployment_checklist.md): Pre-release checklist, deployment mistakes, and release-related references.

## Common task playbooks

These are decision sketches — they tell you which references to combine, not the full answer.

### "Add a new feature triggered by a menu item or shortcut"
1. Define an `AnAction` subclass — see `02_runtime_actions.md`.
2. Register it under `<actions>` in `plugin.xml` — see `01_core_plugin_xml.md`.
3. Make `update()` cheap; declare `getActionUpdateThread()` — see `02_runtime_actions.md`.
4. Long work goes through `04_threading_background_work_progress.md` or `04_threading_coroutines_2024.md`.

### "Add support for a new language"
1. Start with `07_language_pipeline.md`, then walk the step-specific language references in order: `07_language_file_type.md`, `07_language_lexer_jflex.md`, `07_language_grammar_kit_bnf.md`, `07_language_parser_definition_psi_file.md`, `07_language_syntax_highlighting.md`, `07_language_annotator.md`, `07_language_completion.md`, and `07_language_references_resolution.md`.
2. For search/refactoring/docs, add `07_language_find_usages_provider.md`, `06_code_insight_documentation_target_api.md`, or `06_code_insight_refactoring_documentation_structure.md`.
3. For navigation/insights, add the matching editor reference: `06_code_insight_line_markers.md`, `06_code_insight_folding.md`, `06_code_insight_formatter_commenter.md`, `06_code_insight_inspections_intentions_quick_fixes.md`, `07_language_postfix_templates.md`, or `06_code_insight_surround_with.md`.
4. Compare the implementation against `examples/simple_language_plugin/`.

### "Add a tool window with a settings page"
1. Tool window surface: `08_ui_tool_windows.md`.
2. State persistence: `02_runtime_services.md` and `08_ui_settings_persistent_state.md`.
3. Settings page: `08_ui_settings_configurable.md`.
4. Panel construction: `08_ui_kotlin_ui_dsl.md`.

### "Migrate threading from `Thread`/`ExecutorService`/`Task.Backgroundable` to coroutines"
Read `04_threading_thread_to_coroutine_migration.md` first. Add `04_threading_coroutines_2024.md` for API details, `02_runtime_services.md` for injected `CoroutineScope`, and `04_threading_background_work_progress.md` when replacing progress indicators.

### "Migrate a legacy `ApplicationComponent`/`ProjectComponent` to a modern shape"
Read `02_runtime_legacy_component_migration.md` first. Add `02_runtime_services.md`, `02_runtime_listeners_message_bus.md`, `09_project_lifecycle.md`, and `02_runtime_deprecated_api_migrations.md` as needed.

### "Picking a UI surface for a new feature"
Read `08_ui_surface_selection.md` first. Then route to `08_ui_kotlin_ui_dsl.md`, `08_ui_tool_windows.md`, `08_ui_dialogs.md`, `08_ui_tables.md`, `08_ui_choosers.md`, `08_ui_status_bar_widgets.md`, `08_ui_notifications.md`, or `08_ui_data_context.md` based on the chosen surface.

### "A registered extension does nothing in the running IDE"
Read `01_core_extension_diagnostics.md`. Add `01_core_plugin_xml.md`, `01_core_dependencies.md`, or `01_core_extensions.md` if the diagnosis points to descriptor, dependency, or EP spelling issues.

### "A code-insight feature does nothing in production"
Read the provider-specific reference first — for example `06_code_insight_folding.md`, `06_code_insight_line_markers.md`, `07_language_annotator.md`, `07_language_completion.md`, `07_language_inline_completion.md`, or `06_code_insight_inspections_intentions_quick_fixes.md`. Then read `06_code_insight_diagnostics.md` for cross-cutting pipeline checks.

### "React to typing, Enter, Backspace, or editor actions"
Read `02_runtime_typed_handlers_editor_actions.md` first. Add `06_code_insight_editor_model.md`, `05_file_model_documents.md`, and `04_threading_read_write_actions.md` if the handler changes text or caret state.

### "Add gray inline suggestions or an inline completion provider"
Read `07_language_inline_completion.md` first. Add `06_code_insight_editor_model.md`, `05_file_model_documents.md`, and `04_threading_coroutines_2024.md` if the provider needs editor state, document reads, debouncing, or cancellable background work.

### "Work on Next Edit Suggestions"
Read `07_language_next_edit_suggestions.md` first. Do not invent a Next Edit provider EP; if the user wants a third-party implementable suggestion source, route the implementation through `07_language_inline_completion.md`.

### "Make a plugin Remote Development-ready"
Read `01_core_split_mode_remote_development.md` first. Add `08_ui_tool_windows.md`, `08_ui_dialogs.md`, `02_runtime_typed_handlers_editor_actions.md`, or `06_code_insight_file_editor_provider.md` when the feature has frontend UI or latency-sensitive editing behavior.

### "Add a custom editor, preview, or embedded browser"
Read `06_code_insight_file_editor_provider.md` first for editor tabs. Add `08_ui_jcef_embedded_browser.md` only when the custom editor or tool window genuinely needs browser rendering.

## Pre-flight checklist before declaring work done

Run through this whenever you touch plugin code or `plugin.xml`. Most regressions show up here.

- [ ] `plugin.xml` parses (open in IDE, no red underlines; XML DTD validation enabled).
- [ ] `<depends>com.intellij.modules.platform</depends>` is present.
- [ ] Every new EP usage cites a real EP — verified against the IDE's `plugin.xml`
      completion (which only offers EPs from the plugins your `<depends>` resolved).
      Language IDs spelled correctly (case-sensitive).
- [ ] Every new extension implementation is `final`/`class` (not `object`), parameterless
      constructor (or only `Project`/`Module`/`CoroutineScope`), no static initializers, no work
      in the constructor.
- [ ] Every service is a light service (`@Service`) unless there is a real reason not to.
      Constructors only take 0–2 of: `Project`, `Module`, `CoroutineScope`. No other services
      injected via constructor.
- [ ] Every new `Disposable` registers under a plugin-controlled parent, not `Application`/`Project`.
- [ ] Long-running work runs off the EDT, calls `ProgressManager.checkCanceled()` or uses
      coroutine suspension points, and re-throws `ProcessCanceledException` /
      `CancellationException` rather than swallowing them.
- [ ] PSI/Document writes are inside a `WriteCommandAction` (or `writeCommandAction { }`),
      so they participate in undo.
- [ ] No new `Dispatchers.Main`, `GlobalScope`, `kotlinx.coroutines.runBlocking`,
      raw `new Thread(...)`, or `Executors.new*ThreadPool()` — replaced with `Dispatchers.EDT`,
      injected `cs`, `runBlockingCancellable`, and `AppExecutorUtil`.
- [ ] Run **Plugin DevKit** inspections: "Non-default constructors for service and extension class",
      "Cancellation check in loops", "Plugin XML errors". They catch most violations
      automatically.
- [ ] `runIde` boots, the changed feature works in the sandbox, and the IDE log
      (`idea.log` in the sandbox config dir) has no new exceptions related to the plugin.
- [ ] If targeting multiple IDE versions: the `verifyPlugin` Gradle task (2.x; older guides
      may call it `runPluginVerifier`) passes against the declared `sinceBuild` and a
      recent build.
- [ ] If altering existing functionality: confirm dynamic reload still works
      (`autoReload = true`, install/uninstall in sandbox without IDE restart).

## Conventions used across this skill

- "EDT" = Event Dispatch Thread (Swing UI thread). "BGT" = any non-EDT thread.
- "PCE" = `com.intellij.openapi.progress.ProcessCanceledException`.
- "EP" = extension point. "Light service" = service declared via `@Service` (no `plugin.xml`).
- API stability tags follow `@ApiStatus`: `Internal` is forbidden for plugin code,
  `Experimental` may break across versions, `Obsolete` has a stable replacement, plain public
  is stable. Where a reference notes "Experimental", treat it as a deliberate trade-off.
- Code samples are Kotlin where the platform offers a Kotlin-friendly API (which is most
  of 2024.1+); Java appears when an API has no Kotlin form or when describing legacy code.

## Where to look inside this skill

The skill is self-contained — references explain the *why*, examples show the *how*:

- `references/` — capability-indexed deep dives. Read the one that matches your task before
  editing.
- `examples/simple_language_plugin/` — full custom-language skeleton.
- `examples/action_basics/` — `AnAction` + dynamic `ActionGroup` + keymap registration.
- `examples/settings_persistence/` — `@Service` + `SimplePersistentStateComponent` + Kotlin
  UI DSL v2 `Configurable`.
- `examples/inline_completion_provider/` — minimal `InlineCompletionProvider` plus
  `plugin.xml` registration.
- `examples/folding_builder/` — minimal `FoldingBuilderEx` plus `plugin.xml`
  registration for a known host language.

When the user reports a behaviour you can't explain from these alone, stop and ask rather
than fabricate API names or attribute spellings. The IDE's `plugin.xml` editor (with
auto-complete and validation against the resolved plugin set) is the authoritative live
verification surface.
