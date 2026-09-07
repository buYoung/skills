# AGENTS.md

## 1. Overview
JSONinja is a JetBrains IDE plugin for formatting, querying, diffing, loading, generating, and converting JSON/JSON5. The code uses IntelliJ extension points, project services, Swing presenters, and tree-sitter/WASM resources.

## 2. Ownership Map

### Stable Ownership Boundaries
- **Editor transform boundary**: Start in `BaseEditorJsonAction` (`actions/editor`) when changing selection-aware JSON editor transforms. It owns blank/validation guards, background work, stale-write checks, and `WriteCommandAction` mutation shared by concrete editor actions; verify through an editor action on a JSON editor.
- **Shared JSON processing boundary**: Start in `JsonObjectMapperService` and `JsonFormatterService` (`services`) when changing parse/format/sort/escape behavior. They own the shared Jackson JSON/JSON5 mapper and formatting pipeline reused by formatting, query, schema, diff, conversion, and tooltips; verify through any feature that re-formats or re-parses JSON.
- **Query engine boundary**: Start in `JsonQueryService` and `JsonQueryPresenter` (`ui/component/jsonQuery`) when changing query evaluation. `JsoninjaSettingsState.jsonQueryType` selects Jayway JsonPath, JMESPath, or Jackson jq; the presenter keeps original JSON and returns results via tab callbacks, treating invalid/empty results as recoverable; verify through the tool-window query field.
- **Schema generation boundary**: Start in `services/schema` and the `generateJson` schema flow when changing schema parsing or sample generation. It owns `$ref`/`$dynamicRef` normalization, cached/SchemaStore-fallback resolution, and minimal-valid-node fallback; `JsonSchemaGenerationException` carries messages and JSON pointers to validation UI; verify through generate-from-schema dialog output.
- **Type conversion + tree-sitter boundary**: Start in `ConvertTypeDialogPresenter` and `ConvertPreviewExecutor` (`ui/dialog/convertType`) plus `services/typeConversion` when changing JSON↔type conversion. They own debounced, sequence-cancelled previews backed by `TreeSitterAssetRegistryService`, `TreeSitterWasmRuntime.getOrCreate()`, and `WasmMemoryBridge` (with `finally` buffer release); bundled assets live under `resources/tree-sitter/queries` and `resources/wasm/tree-sitter`; verify through the convert-type dialog preview.
- **Diff boundary**: Start in `JsonDiffExtension` and `JsonDiffKeys` (`diff`) when changing the JSON diff viewer. It attaches only to JSON-marked two-editor viewers, caches detection in a synchronized `WeakHashMap`, debounces with `Alarm`, and guards self-updates with document keys plus `AtomicBoolean`; verify by opening a JSON diff.
- **Platform registration boundary**: Start in `src/main/resources/META-INF/plugin.xml` when adding actions, listeners, tool windows, configurables, or diff extensions. It owns extension-point wiring grouped by feature, and user-facing strings belong in `messages/LocalizationBundle*.properties`; verify by loading the plugin and exercising the registration.

### Active Change Routes
- **Settings sync route**: Start in `JsoninjaSettingsState.activeSettings()` (`settings`) when changing how a setting is stored. It routes reads/writes between `JsoninjaSyncedSettingsState` (`jsoninja.xml`), `JsoninjaLocalSettingsState` (`jsoninja-local.xml`, roaming disabled), and the `JsoninjaSettingsSyncPreferenceState` toggle, and still migrates `JsoninjaLegacyProjectSettingsState`; verify by toggling sync in the settings panel.
- **Onboarding route**: Start in `OnboardingService` and `OnboardingStateService` (`services`) with `ui/onboarding` when changing first-run guidance. `OnboardingStateService` persists `isWelcomeDialogSeen` app-wide and the tutorial dialog presenter/view drive steps; verify through the welcome/tutorial dialog on fresh state.
- **Folding-aware editor route**: Start in `FoldingAwareEditorTextField` and `JsoninjaFoldingActionGuardService` (`ui/component/editor`) when changing JSON editor folding; verify through expand/collapse in a tab editor.

## 3. Core Behaviors & Patterns
- **Action-to-Presenter Delegation**: `AnAction` classes resolve `Project`, editor, selection, or tool-window context, then delegate to presenters/services. Editor transforms share `BaseEditorJsonAction` for blank checks, validation, background transform, stale-write checks, and `WriteCommandAction` updates.
- **Callback-Wired UI Composition**: Tool-window and dialog shells stay thin. `JsoninjaPanelPresenter`, `JsonTabsPresenter`, and `JsonTabContextFactory` wire child views through `setOn...Callback`, `setOn...Listener`, and `setOn...Requested` hooks instead of direct sibling coupling.
- **Shared JSON Processing Boundary**: `JsonObjectMapperService` owns the JSON/JSON5 Jackson mapper reused by formatting, querying, schema parsing, tooltips, API loading, and conversion. `JsonFormatterService` adds placeholder restore, sorting, compact arrays, cached pretty-printers, escape/unescape, and original-text fallback.
- **Coroutine Threading and Staleness Guards**: Async work goes through `JsoninjaCoroutineScopeService`; lifecycle-bound presenters use `createChildScope()` and cancel jobs on disposal, while one-shot actions use the project scope. CPU uses `Default`, I/O uses `IO`, UI uses `EDT`, and stale results are rejected by disposed checks, document stamps, sequence counters, captured editor/text identity, or current input.
- **Runtime-Selectable Query Flow**: `JsoninjaSettingsState.jsonQueryType` selects Jayway JsonPath, JMESPath, or Jackson jq inside `JsonQueryService`. `JsonQueryPresenter` stores original JSON, listens for settings changes, validates expressions, and returns results through tab callbacks while treating invalid/empty results as recoverable.
- **Schema Generation and Recovery**: Schema generation validates at the presenter boundary, normalizes `$ref`/`$dynamicRef`, resolves references with caches and SchemaStore fallbacks, compiles schemas, generates primary candidates, and falls back to minimal valid nodes. `JsonSchemaGenerationException` carries messages and JSON pointers to UI validation/dialogs.
- **Type Conversion Preview Pipeline**: `ConvertTypeDialogPresenter` resolves JSON-vs-type seed text and syncs both tabs with `isSynchronizingLanguage`. `ConvertPreviewExecutor` debounces previews, cancels by sequence, computes off the EDT, and applies states only for the latest request.
- **Tree-sitter/WASM Resource Management**: Type-to-JSON analysis loads query resources through `TreeSitterAssetRegistryService`, reuses `TreeSitterWasmRuntime.getOrCreate()`, writes source through `WasmMemoryBridge`, releases buffers in `finally`, and decodes `TreeSitterQueryResult`.
- **Diff Loop Prevention**: Diff requests carry `JsonDiffKeys` markers and sort flags. `JsonDiffExtension` attaches only to JSON-marked two-editor viewers, caches detection in a synchronized `WeakHashMap`, debounces edits with `Alarm`, skips tiny whitespace edits, guards self-updates with document user data plus `AtomicBoolean`, and writes through `WriteCommandAction`.

## 4. Conventions
- **Naming and Packages**: Kotlin stays under `com.livteam.jsoninja.*`. Types use `PascalCase`, functions/properties use `lowerCamelCase`, booleans use `is`/`has`/`uses`/`should`, and numeric settings include units when useful (`delayMs`, `largeFileThresholdMB`).
- **Role Suffixes**: Type names identify layer and ownership: `*Action`, `*Service`, `*Presenter`, `*View`, `*Dialog`, `*Factory`, `*State`, `*Configurable`, `*Validator`, `*Adapter`, `*Executor`, and `*Utils`.
- **Interface Shapes**: UI hooks use `setOn...Callback`, `setOn...Listener`, `setOn...Requested`, or `setOn...Changed`; internal methods stay verb-led (`performSearch`, `schedulePreview`, `loadSchemaFromUrl`, `generateFromSchema`, `applyConfig`).
- **State Modeling**: Persisted settings live in `JsoninjaSettingsData` behind the `JsoninjaSettingsState` facade, which routes between synced and local stores; values stay strings, booleans, and primitives. Convert them through enum helpers, wrapper classes, or dialog settings adapters; avoid scattered raw enum-name parsing.
- **Dialog Composition**: `DialogWrapper` classes set title/buttons, delegate validation and component creation to presenters/views, and call presenter `dispose()`. Presenters own validation, settings persistence, preview scheduling, service calls, and coroutine cancellation.
- **Document and Disposal Ownership**: Editor/document mutations go through IntelliJ write APIs. Components that own editors, tabs, alarms, listeners, or child coroutine scopes dispose them via `Disposer.register`, explicit `dispose()`, or view cleanup; temporary document flags live in nearby `Key` constants.
- **Localization and Registration**: User-facing text comes from `LocalizationBundle*.properties` with existing dotted namespaces. Platform integrations belong in `src/main/resources/META-INF/plugin.xml`, grouped by extensions, listeners, actions, and feature action groups.
- **Resource Layout**: Tree-sitter queries live under `tree-sitter/queries/<language>/type-declarations.scm`, bundled WASM under `wasm/tree-sitter/tree-sitter.wasm`, language icons under `icons/languages`, and icon-pack variants under `icons/classic` and `icons/expui`.
- **Boundary and Error Flattening**: Platform-facing code checks missing `Project`, unsupported viewers, absent editors, blank input, disposed UI, invalid URL/JSON, and large-file settings before work. Internal failures flatten to localized `ValidationInfo`, dialogs, preview errors, hints, `null`, or original input.
- **Comments and Logging**: Comments are selective for IntelliJ lifecycle, threading, resource, or fallback nuance. Logging uses `logger<T>()`, `thisLogger()`, or `Logger.getInstance(...)`; `debug` is diagnostic, `warn` recoverable, and `error` hard failure.

## 5. Working Agreements
- Respond in Korean unless the user requests another language; keep identifiers, paths, exact logs/errors, and fenced code blocks verbatim.
- Ask before adding test files, lint rules, formatter setup, or formatting-only changes; require explicit request.
- Build context from related usages, actions, presenters, services, messages, plugin registration, and affected UI flows before editing.
- Fix the root cause; inspect affected callers and choose a focused complete change that fits existing wiring.
- Check side effects across callers, shared services, lifecycle/disposal boundaries, settings, localization, and plugin registrations; report risks.
- Ask actively when a user decision is needed for scope, behavior, or tradeoffs.
- After code changes, run `./gradlew compileKotlin` as the baseline type-safety check when verification is needed.
- New functions and modules should be single-purpose and colocated with the feature, service, or presenter that owns the behavior.
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
