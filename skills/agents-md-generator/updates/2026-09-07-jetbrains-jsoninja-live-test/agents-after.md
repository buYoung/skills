# AGENTS.md

<!-- agents-md-generator: v1; doc-type: single_repo -->
## 1. Overview
JSONinja is a JetBrains IDE plugin for editing, transforming, querying, comparing, generating, and converting JSON/JSON5 while preserving IntelliJ lifecycle, threading, and resource contracts.

## 2. Ownership Map

### Stable Ownership Boundaries
- **Editor transform boundary**: Start in `BaseEditorJsonAction` for selection-aware transforms. It owns input guards, per-document job replacement, stale checks, and `WriteCommandAction` updates shared by four actions; verify through their editor action path.
- **Settings persistence boundary**: Start in `JsoninjaSettingsState` for persisted settings. Its facade owns synced, local, sync-preference, and legacy stores; preserve copying and migration before reads, then verify through `JsoninjaSettingsConfigurable.apply()` and one consumer.
- **Shared JSON processing boundary**: Start in `JsonObjectMapperService` and `JsonFormatterService` for parsing, JSON5, formatting, sorting, escaping, or placeholders. They serve actions, query, schema, diff, conversion, paste, and tooltips; verify with formatter tests and one UI flow.
- **Query boundary**: Start in `JsonQueryService` and `JsonQueryPresenter` for query evaluation. They own engine selection, formatting, settings re-evaluation, and callback delivery to the active tab; verify all three engines through the tool-window query field.
- **Schema generation boundary**: Start in `services/schema` and `GenerateSchemaJsonTabPresenter` for schema output. They own parsing, reference resolution, compilation, validation, fallback generation, and pointer-bearing UI errors; verify `JsonSchemaDataGenerationServiceTest` and schema-tab output.
- **Type conversion boundary**: Start in `ui/dialog/convertType` and `services/typeConversion` for JSON/type conversion. They own seed detection, synchronized language selection, debounced previews, rendering, tree-sitter analysis, and bundled WASM contracts; verify conversion tests and dialog preview.
- **Diff boundary**: Start in `JsonDiffService`, `JsonDiffRequestChain`, and `JsonDiffExtension` for diff creation or auto-formatting. Preserve request markers, large-file consent, sort settings, self-update guards, and viewer disposal; verify service tests plus editor-tab and window paths.
- **Onboarding lifecycle boundary**: Start in `OnboardingService` for first-run or tutorial behavior. It owns the one-dialog guard, tool-window resolution, dialog lifecycle, and seen-state handoff; verify fresh-state welcome, settings, and tutorial paths.
- **Folding boundary**: Start in `FoldingAwareEditorTextField` for embedded-editor folding. It owns debounced PSI commits, read-action collection, stamp rejection, EDT application, and disposal; verify `FoldingAwareEditorTextFieldTest` and editor expand/collapse.
- **Platform registration boundary**: Start in `src/main/resources/META-INF/plugin.xml` for actions, listeners, tool windows, configurables, or extensions. Keep classes, IDs, icon paths, and localized keys aligned; verify by loading the plugin and exercising the surface.

### Active Change Routes
- **Settings Sync route**: Within **Settings persistence boundary**, start in `JsoninjaSettingsState.setSettingsSyncEnabled()` for the current storage split. Preserve the active store before switching, copy it to the destination, mark migration complete, and confirm `apply()` publishes to open projects.
- **Onboarding seen-state migration route**: Within **Onboarding lifecycle boundary**, start in `OnboardingService.isOnboardingSeen()` when changing compatibility with the old project `PropertiesComponent` flag. Preserve its one-way promotion into the application-level `OnboardingStateService`; verify a legacy-seen project does not reopen the welcome dialog.
- **Folding action-guard route**: Across **Folding boundary** and **Platform registration boundary**, start in `JsoninjaFoldingActionGuardService` for expand/collapse behavior. Limit it to `JSONINJA_EDITOR_KEY` documents, restore the IDE handler on disposal, and verify startup registration plus folding tests.

## 3. Core Behaviors & Patterns
- **Action-to-service delegation**: `AnAction` entry points resolve `Project`, editor, selection, or tool-window context and then delegate work. Selection-aware transforms converge on `BaseEditorJsonAction`; diff actions converge on `JsonDiffService`; conversion actions open presenter-backed dialogs.
- **Callback-wired UI composition**: Tool-window and dialog presenters connect child views with `setOn...Callback`, `setOn...Listener`, `setOn...Requested`, and `setOn...Changed` hooks. `JsoninjaPanelPresenter`, `JsonTabsPresenter`, and `JsonTabContextFactory` coordinate siblings without direct cross-component state mutation.
- **Shared JSON processing**: `JsonObjectMapperService` supplies the common Jackson JSON/JSON5 mapper. `JsonFormatterService` adds formatting, sorting, compact arrays, placeholders, escaping, cached writers, and original-text fallback; consumers reuse these owners.
- **Lifecycle-bound coroutines**: Long-lived presenters and editor components call `JsoninjaCoroutineScopeService.createChildScope()` and cancel that child during disposal; one-shot actions launch in the project service scope. CPU work uses `Dispatchers.Default`, I/O uses `Dispatchers.IO`, and Swing updates use `Dispatchers.EDT`, with a modality context inside dialogs.
- **Stale-result rejection**: Async paths capture current identity before leaving the UI thread. Editor actions and folding compare document stamps, previews use request sequences, presenters compare input/model state, and disposal checks repeat before applying output.
- **Query-to-tab feedback flow**: `JsonQueryPresenter` retains the original JSON, reacts to query edits and `JsoninjaSettingsListener`, delegates engine-specific evaluation to `JsonQueryService`, and sends the formatted result through tab callbacks. Invalid queries, invalid source JSON, and empty results keep the prior usable UI state.
- **Schema recovery flow**: Schema generation performs lightweight presenter validation, strict service parsing, normalization and reference resolution, compilation, sample generation, and instance validation. Primary generation failures fall back to a minimal valid node; `JsonSchemaGenerationException` carries a message and JSON pointer back to dialog validation.
- **Conversion preview and WASM flow**: Conversion presenters map settings into options and submit debounced work through `ConvertPreviewExecutor`; only the newest request reaches the EDT. Type analysis reuses `TreeSitterWasmRuntime`, exchanges UTF-8 buffers through `WasmMemoryBridge`, releases input, result, and error buffers in `finally`, then maps query results into conversion models.
- **Diff loop prevention**: JSON-marked two-editor requests install viewer-scoped listeners after large-file consent. `Alarm` debounces edits, a synchronized `WeakHashMap` caches document state, document user data and `AtomicBoolean` block self-updates, and final changes run in `WriteCommandAction` on the EDT.

## 4. Conventions
- **Naming**: Keep Kotlin under `com.livteam.jsoninja.*`; use `PascalCase` for types, `lowerCamelCase` for functions/properties, boolean prefixes such as `is`/`has`/`should`, and units in names such as `delayMs`.
- **Role suffixes**: Name classes by role: `*Action`, `*Service`, `*Presenter`, `*View`, `*Dialog`, `*Factory`, `*State`, `*Configurable`, `*Validator`, and `*Adapter`.
- **Interface shape**: Externally wired UI hooks use `setOn...Callback`, `setOn...Listener`, `setOn...Requested`, or `setOn...Changed`; internal operations stay verb-led, such as `performSearch`, `schedulePreview`, `loadSchemaFromUrl`, and `applyConfig`.
- **Service access and state**: Resolve IntelliJ services at the owning lifecycle. Persist primitives and enum names behind `JsoninjaSettingsState`; convert them with enum helpers or settings adapters.
- **Dialog composition**: Keep `DialogWrapper` classes thin: set titles/buttons, delegate component creation and validation, and dispose presenters. Presenters own validation, settings, service calls, previews, callbacks, and cancellation.
- **Document and disposal ownership**: Use IntelliJ write APIs for document mutations. Register editors, listeners, alarms, tabs, and child scopes under their owning `Disposable`; keep flags in nearby `Key` constants and clear guards in `finally`.
- **Localization and registration**: Put user text in `LocalizationBundle*.properties` with dotted keys. Group `plugin.xml` entries by extensions, listeners, actions, and feature groups; keep IDs and resources synchronized.
- **Resource layout**: Store tree-sitter queries at `tree-sitter/queries/<language>/type-declarations.scm`, the runtime module at `wasm/tree-sitter/tree-sitter.wasm`, language icons under `icons/languages`, and icon-pack variants under `icons/classic` and `icons/expui`.
- **Boundary failures**: Guard absent context, blank input, unsupported viewers, disposal, stale documents, invalid data, and large files before side effects. Flatten failures to `ValidationInfo`, localized text, preview state, `null`, or original input; rethrow coroutine cancellation.
- **Comments and logging**: Comment non-obvious lifecycle, threading, resource, or fallback constraints. Use `logger<T>()`, `thisLogger()`, or `Logger.getInstance(...)`; reserve `debug` for diagnostics, `warn` for recoverable failures, and `error` for hard failures.

## 5. Working Agreements
- Respond in Korean unless the user requests another language; keep technical terms in English and never translate fenced code blocks.
- Ask the user before introducing tests, lint, or formatter setups; add them only on explicit request.
- Build context by reviewing related usages, flows, patterns, and likely impact before editing.
- Fix the underlying cause, not only the visible symptom; inspect affected flows and apply the narrowest complete change that resolves the root issue.
- Check side effects across callers, shared abstractions, lifecycle/state boundaries, plugin registrations, and public behavior; report relevant impact and compatibility risks.
- Ask actively when user decisions are needed for scope, behavior, or tradeoffs.
- Run `./gradlew compileKotlin` after code changes to verify type safety.
- New functions and modules should be single-purpose and colocated with related code.
- Add external dependencies only when necessary, and explain why.

## 6. User Custom
- linear 이슈 작업할때 label[Front-end, Back-end] 상관없이 작업한다. (kotlin, java project는 FE,BE 구분하지않음)

## When Extending
- Register new actions/components in `plugin.xml` and align icons/messages.
- Co-locate new features with existing package patterns (service + action + UI wiring).
- Keep `JsonEditor`/tab lifecycle consistent: dispose resources via `Disposer`, preserve `JSONINJA_EDITOR_KEY`, respect large-file warning thresholds.
- For formatting changes, consider cache keys and `JsonFormatState` semantics (sorting, compact arrays, uglify override).
- For query-related features, handle both Jayway and JMESPath or gate by setting.

## Threading Rules

> Canonical source: [`docs/coroutine-threading-standard.md`](docs/coroutine-threading-standard.md). The table below is a summary; follow the canonical doc for the full pattern, scope-selection rules, staleness guards, and known issues. This codebase has migrated to Kotlin coroutines, so the legacy `executeOnPooledThread { ... invokeLater(...) }` pattern is **no longer the standard**.

| Intent | Pattern |
|--------|---------|
| Lifecycle-bound async work | `service<JsoninjaCoroutineScopeService>().createChildScope()` owned by the component; `cancel()` in `dispose` |
| One-shot project-lifetime async (e.g. actions) | `service<JsoninjaCoroutineScopeService>().launch { }` (add a sequence/stamp staleness guard if needed) |
| CPU compute (parse/format/sort/tree build) | `withContext(Dispatchers.Default) { }` |
| I/O (file, network) | `withContext(Dispatchers.IO) { }` |
| UI update | `withContext(Dispatchers.EDT) { }` (add `+ ModalityState.any().asContextElement()` inside modal dialogs) |
| Write + Undo | `WriteCommandAction.runWriteCommandAction(project) { }` (on EDT) |
| PSI / Document read (off-EDT) | `readAction { }` / `runReadAction { }` |
