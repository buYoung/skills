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

```markdown
# AGENTS.md

## 1. Overview
[1-2 sentences describing the monorepo's purpose]

## 2. Folder Structure
[High-level map of apps, packages, and shared configs]

## 3. Working Agreements
[Common working agreements applicable to all packages]
```

## Standard Document Structure (Single Repo & Packages)

```markdown
# AGENTS.md

## 1. Overview
[1-2 sentences describing the project's purpose and role]

## 2. Folder Structure
[Key directories with brief descriptions]

## 3. Core Behaviors & Patterns
[Observed patterns from code analysis]

## 4. Conventions
[Naming, comments, code style rules]

## 5. Working Agreements
[Agent behavior rules - see working_agreements.md]
```

## Section Specifications

### Section 1: Overview

- **Length**: 1-2 very short sentences
- **Content**: Abstract description of project purpose and role
- **Excludes**: Long lists of tools, frameworks, commands, environment details

### Section 2: Folder Structure

- **Format**: Hierarchical nested bullet list with indentation
- **Analysis Scope**: Traverse **all depths** of the directory tree during analysis
- **Output Scope**: Stop at **architecturally significant boundaries** where roles become clear
- **Content**: Each listed entry should explain the **role and responsibility** concisely
- **Goal**: Reader should understand where to find/place code for a given concern

**Analysis vs Output Principle**:

- **Analysis**: All depths — Understand full structure and identify architectural boundaries
- **Output**: Significant levels only — Present only directories where distinct roles and responsibilities exist

**When to Stop Drilling Down**:

- When a directory represents a **single cohesive concern** (e.g., `services`, `models`, `utils`)
- When further depth would only list individual files, not distinct modules
- When the role can be summarized in one brief sentence

**Content Requirements**:

- Describe **what** the directory contains and **why** it exists in a brief sentence
- For source directories, explain the architectural role (e.g., "actions", "services", "models")
- Mention any conventions (e.g., "mirror main packages if tests are added")
- Note cross-references to docs if relevant (e.g., "align changes with these when relevant")

**Example Structure**:

```markdown
- `src/main/kotlin/com/example/app`: core application code.
    - `actions`: UI actions wiring user interactions to business logic.
    - `services`: business logic, external integrations, data processing.
    - `ui`: view components, dialogs, panels, layout scaffolding.
    - `model`: domain entities, enums, DTOs.
    - `utils`: shared helpers and utility functions.
    - `settings`: configuration management and persistent state.
- `src/main/resources`: configuration files, message bundles, static assets.
- `src/test/kotlin`: test code; mirror main package structure when adding tests.
- `docs`: development guides and specifications; keep aligned with implementation.
- `gradle/` or `config/`: build configuration and tooling setup.
```

**Anti-patterns**:

- Flat list without hierarchy or context
- Generic descriptions like "Core plugin implementation" without explaining structure
- Omitting important subdirectories that define architecture
- Missing guidance on where to place new code

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
