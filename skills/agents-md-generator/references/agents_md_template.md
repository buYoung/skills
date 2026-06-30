# AGENTS.md Output Template Specification

Defines the exact structure and content requirements for generated `AGENTS.md` files.

## Table of Contents

- [Monorepo Root Document Structure](#monorepo-root-document-structure-agentsmd)
- [Standard Document Structure](#standard-document-structure-single-repo--packages)
- [Section Specifications](#section-specifications)
- [Format Requirements](#format-requirements)
- [Anti-Patterns (Excluded Content)](#anti-patterns-excluded-content)

## Monorepo Root Document Structure (`/AGENTS.md`)

Used only when generating the root document for a monorepo.

When package-level ownership boundaries, shared cross-package contracts, or active cross-package change routes are detected:

```markdown
# AGENTS.md

## 1. Overview
[1-2 sentences describing the monorepo's purpose]

## 2. Ownership Map
[Optional evidence-backed map split into Stable Ownership Boundaries and Active Change Routes. Omit this section when no stable boundaries or active routes are detected.]

## 3. Working Agreements
[Common working agreements applicable to all packages]
```

When no stable root-level ownership boundaries or active root-level change routes are detected:

```markdown
# AGENTS.md

## 1. Overview
[1-2 sentences describing the monorepo's purpose]

## 3. Working Agreements
[Common working agreements applicable to all packages]
```

## Standard Document Structure (Single Repo & Packages)

When ownership boundaries or active change routes are detected:

```markdown
# AGENTS.md

## 1. Overview
[1-2 sentences describing the project's purpose and role]

## 2. Ownership Map
[Optional evidence-backed map split into Stable Ownership Boundaries and Active Change Routes. Omit this section when no stable boundaries or active routes are detected.]

## 3. Core Behaviors & Patterns
[Observed patterns from code analysis]

## 4. Conventions
[Naming, comments, code style rules]

## 5. Working Agreements
[Agent behavior rules - see working_agreements.md]
```

When no stable ownership boundaries or active change routes are detected:

```markdown
# AGENTS.md

## 1. Overview
[1-2 sentences describing the project's purpose and role]

## 3. Core Behaviors & Patterns
[Observed patterns from code analysis]

## 4. Conventions
[Naming, comments, code style rules]

## 5. Working Agreements
[Agent behavior rules - see working_agreements.md]
```

## Section Specifications

**Numbering rule**: Section numbers are stable identifiers used by update mode. When optional `## 2. Ownership Map` is omitted, keep the remaining section numbers unchanged (for example `## 1`, `## 3`, `## 4`, `## 5`). Do not renumber sections to close the gap.

### Section 1: Overview

- **Length**: 1-2 very short sentences
- **Content**: Abstract description of project purpose and role
- **Excludes**: Long lists of tools, frameworks, commands, environment details

### Section 2: Ownership Map

Ownership Map is an **optional** standard section. It replaces directory inventory with a concise map of both long-lived system responsibility boundaries and currently active change routes that matter when updating an established project after meaningful changes. `Stable Ownership Boundaries` is the continuation of the previous single-list Ownership Map content; `Active Change Routes` is an additive subsection, not a replacement.

Do **not** force this section. If analysis finds no concrete, stable ownership boundaries or active change routes, omit `## 2. Ownership Map` entirely. Do not emit placeholder text such as "No ownership map detected", generic directory lists, or speculative ownership.

**Format**: Split the section into two evidence-backed subsections when both categories have content:

```markdown
### Stable Ownership Boundaries
[Long-lived responsibility boundaries that remain useful even when recent change focus shifts.]

### Active Change Routes
[Recently or repeatedly changed routes discovered from git history, then confirmed against current code or documented contracts.]
```

Omit an empty subsection rather than writing a placeholder. `Stable Ownership Boundaries` explains the durable safety map and should still include the same kind of high-value boundaries the old single-list Ownership Map would have produced. `Active Change Routes` explains recent or repeated change deltas that are not obvious from the stable boundary alone. Keep both within the `Ownership Map` section budget; do not impose an additional bullet-count limit.

Each bullet should answer "if I need to change this behavior, where do I start and what must I not break?" A useful bullet reads like a routing rule for future changes, not like an architecture inventory. Stable bullets and Active bullets have different contracts: Stable bullets describe durable ownership; Active bullets describe only the recent/change-specific delta.

For Stable bullets, use this sentence frame unless a repository-specific phrasing is clearer:

```markdown
- **[Boundary name]**: Start in `[primary owner]` when changing [specific behavior]. It owns [decision/state/output] and must preserve [contract or side effect]; verify through [concrete check surface].
```

For Active bullets that belong under a Stable boundary, use a parent-linked delta frame:

```markdown
- **[Active route name]**: Within **[Stable boundary name]**, start in `[focused owner]` when changing [recent/change-specific behavior]. Keep only the delta: [new start point, compatibility risk, migration detail, or specific verification surface not already covered by the parent].
```

Do not open a bullet with a long list of files; name the owner or entry point first, then mention only the supporting anchors needed to explain the contract.

**Analysis Scope**:

- Start from stable entry points, not from a directory tree.
- Trace where state/data is stored or read, where behavior is decided, how output is exposed, which contracts and side effects are touched, and what verifies the boundary.
- In Update mode, use git history as a discovery signal: recent changed-path clusters, repeated co-change, renames/moves, deleted paths, and high-churn boundary files can reveal where ownership may have shifted.
- Confirm every history-derived candidate against current code or documented contracts before writing it. Git history decides where to look next; it does not prove ownership by itself.
- Use file paths and identifiers only as evidence anchors; do not turn the section into a folder tour.
- For monorepo roots, map package-level responsibility boundaries, shared cross-package contracts, and active cross-package change routes only. A package qualifies when manifests, package names, README text, public exports, dependency direction, or recent confirmed change clusters show a clear role; package-internal ownership belongs in package `AGENTS.md` files.

**Content Requirements**:

- Put durable, always-relevant system boundaries under `### Stable Ownership Boundaries`. This subsection should preserve the useful output shape of the prior Ownership Map: request lifecycle, transaction ownership, public response contracts, report rendering, workers, package ownership, or other long-lived safety boundaries when current code supports them. Do not remove these stable boundaries just because `Active Change Routes` also exists.
- Keep Stable bullets focused on durable ownership: long-lived owner, protected contract, and representative verification surface. Do not include details that matter only because of recent churn, version-specific behavior, compatibility migrations, renames/moves, or high-churn file clusters unless they have become a permanent public contract.
- Put history-informed, currently relevant change routes under `### Active Change Routes`. These should come from recent high-churn paths, repeated co-change clusters, renames/moves, or active compatibility/migration work, then be confirmed against current code or documented contracts. Treat this subsection as additional update-mode signal, not as a filter that narrows or replaces stable boundaries.
- Active routes are child routes or cross-boundary routes, not standalone ownership summaries. If an Active route belongs under a Stable boundary, start with `Within **[Stable boundary name]**...` and keep only the recent/change-specific delta. Do not restate the parent boundary's broad owner, public contract, or general verification surface.
- Do not duplicate the same route in both subsections. If a stable boundary is also active, keep the durable contract in `Stable Ownership Boundaries` and put only the recent/change-specific route in `Active Change Routes`. If no meaningful delta remains after removing inherited Stable details, omit the Active route.
- Include only boundaries with concrete repository evidence: named entry points, state owners, behavior decision points, external surfaces, connection contracts, side effects, or verification anchors.
- Include a boundary only when at least two evidence anchors support it, such as entry point + behavior decision point, state owner + external surface, contract + side effect, or existing verification anchor + the code path it verifies.
- Each Stable bullet must cover all four parts in prose, preferably in this order:
  - `owns`: what responsibility boundary the code currently owns.
  - `starts`: which kind of future change should begin at this boundary.
  - `contracts`: which state, API, response, schema, side effect, lifecycle rule, or external surface must stay compatible.
  - `verify`: the concrete check surface, existing test area, type-check target, log point, generated output, API response, UI path, or manual confirmation point that proves the boundary still works.
- Each Active bullet should cover only delta-specific parts:
  - `parent`: the Stable boundary it belongs under, unless it truly crosses boundaries or has no Stable parent.
  - `trigger`: the recent, repeated, versioned, compatibility, migration, rename, or co-change signal that makes it worth calling out.
  - `delta start`: the focused file, service, module, package, or public entry point that differs from or narrows the Stable start point.
  - `delta risk/verify`: the contract risk or verification surface not already obvious from the Stable boundary.
- The first actionable clause should identify the start point. Avoid bullets whose first clause is mostly a catalog of participating files, modules, decorators, middleware, or dependencies.
- Explain `starts` and `verify` concretely enough that an agent can act on them. Avoid vague phrases such as "check related tests", "verify the flow", or "account for integrations" unless they name the actual path, output, or consumer.
- Prefer current code and documented contracts over inferred intent. Use recent history or comments only as supporting context when current ownership is otherwise ambiguous.
- Keep verification anchors concise: name the representative check path, existing test area, type-check target, log point, or manual confirmation surface. Do not create a testing strategy section or list common commands.
- Omit categories that are not detected. A well-evidenced critical boundary is better than several weak guesses.
- Split broad catch-all boundaries. If one bullet names unrelated integrations, unrelated persistence layers, multiple independent entry points, or several unrelated change-start locations, split it into separate bullets or omit the weaker candidates.
- Keep a boundary narrow enough that the owner responsible for deciding behavior is clear. A shared contract can mention multiple consumers. Split based on unrelated responsibility, entry point, or verification surface, not on a fixed bullet or file-count limit.
- Do not include timeline summaries such as "earlier focus", "recent focus", or "current focus" in `AGENTS.md`. Use those summaries only in the user-facing update report, unless the transition is currently represented in code as a live migration, compatibility layer, deprecated path, or adapter boundary.

**Candidate Filters**:

Before writing a Stable boundary, reject or split it unless all answers are concrete:

- Start: What is the first file, service, module, package, or public entry point an agent should inspect?
- Trigger: What kind of future change belongs here?
- Contract: What named consumer, persisted state, response shape, schema, generated output, lifecycle rule, or side effect would break if this owner changed incorrectly?
- Verification: What exact existing path, output, response, generated artifact, log point, or check target would show the boundary still works?
- Scope: Is this one coherent responsibility with a clear owner, contract, and verification surface? If not, split it.

Before writing an Active route, reject or rewrite it unless the delta is concrete:

- Parent: Which Stable boundary does this route belong under? If none, which Stable boundaries does it cross?
- Delta trigger: Which recent, repeated, versioned, compatibility, migration, rename, or co-change signal makes it worth calling out?
- Delta start: Which focused start point differs from or narrows the Stable start point?
- Delta risk/verify: Which contract risk or verification surface is not already obvious from the Stable boundary?
- If the route has a Stable parent and repeats the same owner, contract, and verification surface, rewrite it as `Within **[Stable boundary]**...` and keep only the delta.
- If the delta does not change the start point, add a compatibility/migration risk, add a focused verification surface, or cross multiple Stable boundaries, omit it.
- If the route crosses multiple Stable boundaries and no single parent owns it, state the crossed boundaries instead of inventing a new broad owner.
- If a Stable bullet contains active-only details, move those details into an Active route or drop them when they are not worth a separate route.

**Example Structure**:

```markdown
### Stable Ownership Boundaries

- **Editor command boundary**: Start in `EditorCommandService` when changing command execution or validation. It owns behavior delegated by `EditorAction` registrations and must preserve the action contract consumed by the editor shell; verify through the editor command integration path.
- **Settings state boundary**: Start in `SettingsStore` when changing persisted settings or defaults. It owns settings reads/writes and must preserve the config shape consumed by UI panels and startup loading; verify through the settings load/save path.
- **API response boundary**: Start at the HTTP handler and `ErrorMapper` when changing public response or error output. They own the external response surface and must preserve documented success/error shapes for consumers; verify through the representative API response path. Detailed error-flattening and schema-format rules belong in Section 4 (Conventions).

### Active Change Routes

- **Settings migration route**: Within **Settings state boundary**, start in the migration helper when changing compatibility handling for renamed or missing config keys. Preserve only the migration-specific fallback behavior; verify through the migration path rather than restating the general settings load/save contract.
- **Report export route**: Across the report rendering and external upload boundaries, start in the route-specific report request factory when recent changes require generated filenames and upload payloads to stay in sync. Verify through the affected download plus upload output because neither parent boundary proves the cross-boundary route alone.
```

**Anti-patterns**:

- Listing directories and their contents as a substitute for ownership
- Claiming ownership from naming alone (e.g., "`services/` owns business logic") without tracing entry points, state, contracts, or behavior
- Filling every category even when the repository does not expose evidence for it
- Writing speculative history or intent as fact
- Documenting a boundary from git history without current-code or documented-contract confirmation
- Combining unrelated owners into one broad bucket, such as all external integrations, all persistence technologies, or all background jobs, when they have different entry points, contracts, or verification surfaces
- Listing many files in a bullet without saying which file owns the decision, where a future change should start, and how the result is verified
- Writing bullets that begin with "`A`, `B`, `C`, and `D` own..." because this usually produces an inventory instead of a change route
- Dropping stable boundaries just because they were not recently changed, or dropping active routes because they do not look like top-level architecture
- Writing Active routes as standalone ownership summaries instead of parent-linked or cross-boundary deltas
- Repeating the Stable parent boundary's broad owner, contract, and verification in an Active route
- Keeping `v2`, migration, compatibility-shim, rename/move, or high-churn details in Stable bullets when they are not permanent public contracts
- Ending bullets with weak verification language such as "test accordingly", "verify related behavior", or "check downstream effects" instead of naming the concrete verification surface
- Turning `AGENTS.md` into a changelog with time-relative focus summaries
- Duplicating Section 3 by describing full recurring behavior flows instead of current responsibility boundaries
- Duplicating Section 4 by turning boundary ownership into naming/style rules, error-shape rules, schema-format rules, or other coding conventions

### Section 3: Core Behaviors & Patterns

Document **cross-cutting patterns** that repeat across the codebase. Focus on patterns that a contributor must follow to keep code consistent — not individual function descriptions.

**Pattern Discovery Approach**:

Surface-level scanning (e.g., "this codebase uses error handling") is not enough. The goal is to uncover **how the codebase actually works** — the specific mechanisms, flows, and constraints that a contributor must understand to write code that fits.

- **Phase 1 — Stack & Surface Discovery**:
  - Identify **installed dependencies and technology stack** by reading detected package manifests before searching for code patterns — use this context to focus pattern discovery on relevant frameworks and libraries (see read_only_commands.md > Dependency Discovery)
  - Search for **recurring idioms** that appear in 3+ files (e.g., shared error handling wrappers, common logging calls, repeated guard clause shapes)
  - Look for **project-specific abstractions** the team has built on top of frameworks (e.g., custom base classes, shared decorators, wrapper utilities)

- **Phase 2 — Deep Tracing** (this is where most missing patterns live):
  - **Trace patterns across layers**: When a surface pattern is found (e.g., "error handling"), follow it through the full flow — how does an error originate, propagate, transform at boundaries, and reach the user? A pattern like "wraps errors in AppError" becomes meaningful only when you also describe that the boundary layer flattens it, the UI layer maps it to a message, and recovery is attempted before surfacing.
  - **Follow the wiring**: Look at how components connect to each other. Direct calls, callback registration, event pairs, observer patterns, and delegation chains are all wiring mechanisms. When multiple components participate in a flow, document the connection pattern — not just the individual components.
  - **Identify state lifecycle flows**: Look for components that manage defined state transitions (e.g., initialization → ready → degraded → recovery). These often span multiple files and reveal operational behavior that surface scanning misses.
  - **Check what happens on failure**: Many codebases have resilience patterns that only appear when you look at error paths — graceful degradation, self-healing persistence, quarantine-and-recover, fallback snapshots. These are critical patterns but invisible to surface-level search.
  - **Spot centralized delegation**: When multiple callers share a common utility or lookup function instead of duplicating logic, that centralization is a pattern worth documenting — it tells contributors where to go instead of reinventing.

- **Phase 3 — Validation**:
  - Note **implicit rules** not captured in linter configs (e.g., "all async operations go through a central queue", "state mutations only via specific helpers")
  - Verify each discovered pattern appears in 3+ locations — but patterns that span multiple layers (e.g., a persistence flow touching store, service, and UI) count as cross-cutting even if the exact code shape differs at each layer
  - Prefer patterns observed in 3+ locations, but also document a single critical boundary when it defines safe agent work (e.g., the only public write path, the only generated-file boundary, or the only external side-effect entry point)

**Pattern Categories** (include only those actually observed):

- **Logging**: Logger initialization pattern, log levels, structured logging conventions
- **Error Handling**: Error propagation strategy, recovery vs fail-fast, custom error types, how errors transform at layer boundaries
- **Control Flow**: Guard clauses, early returns, null-safety idioms
- **Concurrency / Threading**: Thread model, async patterns, synchronization approaches
- **Module Communication**: How modules call each other — dependency direction, event/message patterns, callback/listener registration, paired event protocols
- **State Management**: Where and how state is held, mutated, and shared; state machine flows if components go through defined transitions
- **Resilience & Recovery**: Self-healing persistence, graceful degradation on failure, fallback strategies, data migration/schema evolution on corrupt or outdated state
- **Cross-boundary Wiring**: How layers or subsystems connect — callback registration patterns, event-driven handshakes, delegation chains where a shell/host delegates behavior to an inner component or service
- **Shared Resource Management**: Centralized services or utilities that multiple features reuse (e.g., a single configured parser shared across formatters, validators, and highlighters), and how consumers access them

**Content Requirements**:

- Each pattern should explain **what** it is, **where** it appears, and **how** to follow it
- Include enough detail so a new contributor can replicate the pattern without reading the source
- When a pattern involves specific APIs or abstractions, name them explicitly
- Group related patterns under their category heading with sub-bullets for details
- For multi-layer patterns, describe the full flow (origin → intermediate steps → final outcome), not just one layer

**Example Structure**:

```markdown
- **Error Handling**: All service-layer methods wrap external calls in `AppError.wrap()`, converting third-party exceptions into domain-specific `AppError` subtypes. Controllers catch `AppError` at the boundary and map to HTTP status codes via `ErrorMapper.toResponse()`. Internal errors from poisoned locks are recovered rather than propagated — the lock is re-acquired with a clean state.
- **Logging**: Each class initializes a logger via `LoggerFactory.getLogger(ClassName::class)`. Business events use `logger.info` with structured key-value pairs (`action=`, `entity=`, `id=`). Debug-level logs are reserved for intermediate state during multi-step operations.
- **Module Communication**: Services depend only on interfaces defined in the `ports/` package, never on concrete implementations. Wiring happens in `config/` modules via dependency injection. Cross-module calls always go through the interface boundary.
- **State Management**: Application state is held in `StateStore` as immutable data classes. Mutations go through `StateStore.update { }` lambdas, which trigger UI re-renders via the observer pattern. Direct field assignment on state objects is prohibited.
- **Resilience & Recovery**: The settings store is not a simple read/write — it detects corrupt files, quarantines them, attempts restore from backup, and falls back to defaults. Startup failures do not abort the application; instead, the system transitions to a degraded-capability snapshot, emits an event, and the UI layer reflects reduced functionality via banners or feature gating.
- **Cross-boundary Wiring**: Editor, query, and tab components do not directly reference each other. Instead, each registers callbacks (`setOnChangeCallback`, `setOnSearchCallback`) that the parent wires together. State flows through these callbacks rather than through shared mutable references.
- **Shared Resource Management**: A single configured `ObjectMapperService` is shared across formatter, query engine, and highlighter. Consumers access it via injection rather than creating their own instances, ensuring consistent parsing behavior.
```

**Anti-patterns**:

- Listing individual functions or classes instead of cross-cutting patterns
- Describing what a single file does rather than what the codebase does consistently
- Including patterns that appear only once (not truly cross-cutting)
- Omitting a single critical boundary that defines safe agent work just because it has only one entry point
- One-line summaries that name a pattern without explaining how it works (e.g., "Uses repository pattern" without describing the actual convention)
- Staying at the surface: saying "has error handling" without explaining the propagation flow, or "uses events" without describing the event protocol and wiring mechanism

### Section 4: Conventions

**Convention Discovery Approach**:

Conventions go beyond surface-level naming rules. They include **how the codebase structures its interfaces**, **how configuration files are organized**, and **what implicit contracts exist at boundaries**. A convention is any consistent rule that, if broken, would make the code look out of place.

- Read package manifests to understand the project's technology stack before analyzing conventions
- Use stack context to focus on relevant convention patterns (e.g., framework-specific naming, project-specific abstractions built on top of dependencies)
- Sample **10+ files** across different directories to confirm a convention is consistent, not accidental
- Distinguish between **enforced conventions** (linter/formatter rules) and **team conventions** (implicit patterns) — both are worth documenting
- **Look at interfaces, not just internals**: Examine function signatures, callback parameter names, return value shapes, and public API surfaces — these often follow stricter conventions than internal code
- **Check configuration and registration files**: Plugin manifests, DI configs, route registrations, and message/localization files often have their own structural conventions (grouping order, key naming hierarchy, feature bundling)

**Convention Categories** (include only those actually observed):

- **Naming**: camelCase, snake_case, PascalCase usage per context (variables, classes, files, directories)
- **Prefixes/Suffixes**: Consistent type indicators like `SomethingService`, `useSomething`, `SomethingProps`, `ISomething`
- **File & Directory Naming**: kebab-case files, PascalCase component files, index barrel exports, co-location patterns
- **Comments**: Tone, language, brevity, when comments are used vs omitted
- **Legacy Handling**: TODO, FIXME, NOTE, deprecated markers and their conventions
- **Import Organization**: Grouping order (stdlib → external → internal), path alias usage, barrel imports
- **Type Patterns**: Type definition co-location, shared type files, generic usage conventions
- **API & Interface Design**: Consistent shapes for function signatures, callback naming (e.g., `on*` for external callbacks vs `handle*` for internal handlers), return value structures from reusable abstractions (e.g., hooks always return `{ state, actions }` objects with consistent status fields like `isLoading`, `errorMessage`), method responsibility splitting (e.g., one method for presentation/validation, another for execution)
- **Configuration & Registration Structure**: How features are grouped in config/manifest files, key namespace hierarchies in message/localization bundles (e.g., `feature.component.role` taxonomy), registration ordering conventions
- **Boundary Conventions**: How data/errors are transformed at system boundaries (e.g., rich internal error types flattened to strings at the external boundary), schema versioning or drift absorption strategies (e.g., `default` annotations, version fields), containment rules for unsafe or platform-specific code (e.g., FFI code confined to specific modules with safe wrappers exposed)
- **Component Composition**: Shell/wrapper patterns (e.g., thin dialog shells that delegate to inner presenters), shared primitive wrappers (e.g., a base modal that feature-specific modals extend), provider-consumer patterns for state boundaries

**Content Requirements**:

- Each convention should state the **rule** and give a **concrete example** showing correct usage
- When a convention has **exceptions**, note them explicitly
- Cover both code-level conventions and project-structure-level conventions
- For interface design conventions, show the **consistent shape** that repeats across the codebase

**Example Structure**:

```markdown
- **Naming**: Variables and functions use `camelCase`. Classes and types use `PascalCase`. Constants use `UPPER_SNAKE_CASE`. Boolean variables are prefixed with `is`, `has`, or `should` (e.g., `isLoading`, `hasPermission`).
- **Prefixes/Suffixes**: Service classes are suffixed with `Service` (e.g., `UserService`). React hooks are prefixed with `use` (e.g., `useAuth`). Type/interface names for component props are suffixed with `Props` (e.g., `ButtonProps`).
- **File & Directory Naming**: Component files use PascalCase (`UserProfile.tsx`). Utility and helper files use camelCase (`formatDate.ts`). Each feature directory has an `index.ts` barrel export.
- **Import Organization**: Imports are grouped in three blocks separated by blank lines: (1) external packages, (2) internal aliases (`@/`), (3) relative imports. Side-effect imports (`import './styles.css'`) appear last.
- **API & Interface Design**: Callback props use `on*` prefix (`onChange`, `onSubmit`), local event handlers use `handle*` (`handleClick`, `handleSubmit`). Reusable hooks return `{ state, actions }` objects with consistent status fields (`isLoading`, `isSaving`, `errorMessage`). Async mutations use optimistic update with rollback on failure. Dialog classes are thin shells — `init` sets title/buttons, then delegates panel creation, validation, and disposal to an inner presenter or component.
- **Configuration Structure**: Plugin registrations group extensions, listeners, and actions into separate blocks. Within actions, entries are organized by feature group. Message/localization keys follow a `feature.component.role` hierarchy (e.g., `editor.tab.title`, `editor.tab.description`, `query.error.syntax`).
- **Boundary Conventions**: Internal errors use rich domain types (`AppError` subtypes). At the external boundary (commands, IPC, API), errors are flattened to plain strings. Schema fields use `default` annotations to absorb missing keys from older versions. Platform-specific or unsafe code is confined to dedicated modules; parent modules expose only safe wrapper interfaces.
```

**Anti-patterns**:

- Listing a convention name without showing the actual rule (e.g., "Uses camelCase" without specifying where)
- Mixing conventions with behavioral patterns that belong in Section 3
- Documenting IDE or tooling settings instead of code-level conventions
- Describing only naming conventions while ignoring interface design, configuration structure, and boundary conventions that are equally important for consistency

### Section 5: Working Agreements

See the working agreements specification referenced from SKILL.md.

## Format Requirements

- **Language**: English by default (for the content of the `AGENTS.md` file); if the user explicitly requests another language for the generated document, follow that request
- **Max Length**: Dynamic based on repository LOC (see LOC measurement specification referenced from SKILL.md)
- **Format**: Valid Markdown
- **Tone**: Concise, neutral
- **Headings**: Short and descriptive
- **Content Style**: Bullet points with enough detail to be actionable; each item should convey the rule and how to follow it

## Anti-Patterns (Excluded Content)

- "Common Commands" section
- "How to run" instructions
- "Testing Strategy" documentation
- Build/deploy instructions
- Detailed CI pipeline configuration

**Exception**: the discovered type-check command included in Working Agreements (see the working agreements specification, "Type Check After Changes") is required content — it is verification guidance, not a build/run instruction, even when the discovered command is literally a build tool invocation (e.g., `go build`, `gradle compileKotlin`). Do not remove it to satisfy this list.
