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

- Identify **installed dependencies and technology stack** by reading detected package manifests before searching for code patterns — use this context to focus pattern discovery on relevant frameworks and libraries (see read_only_commands.md > Dependency Discovery)
- Search for **recurring idioms** that appear in 3+ files (e.g., shared error handling wrappers, common logging calls, repeated guard clause shapes)
- Identify **architectural boundaries** and how data flows across them (e.g., Controller → Service → Repository, Action → Service → UI)
- Look for **project-specific abstractions** the team has built on top of frameworks (e.g., custom base classes, shared decorators, wrapper utilities)
- Note **implicit rules** not captured in linter configs (e.g., "all async operations go through a central queue", "state mutations only via specific helpers")

**Pattern Categories** (include only those actually observed):

- **Logging**: Logger initialization pattern, log levels, structured logging conventions
- **Error Handling**: Error propagation strategy, recovery vs fail-fast, custom error types
- **Control Flow**: Guard clauses, early returns, null-safety idioms
- **Concurrency / Threading**: Thread model, async patterns, synchronization approaches
- **Module Communication**: How modules call each other, dependency direction, event/message patterns
- **State Management**: Where and how state is held, mutated, and shared

**Content Requirements**:

- Each pattern should explain **what** it is, **where** it appears, and **how** to follow it
- Include enough detail so a new contributor can replicate the pattern without reading the source
- When a pattern involves specific APIs or abstractions, name them explicitly
- Group related patterns under their category heading with sub-bullets for details

**Example Structure**:

```markdown
- **Error Handling**: All service-layer methods wrap external calls in `AppError.wrap()`, converting third-party exceptions into domain-specific `AppError` subtypes. Controllers catch `AppError` at the boundary and map to HTTP status codes via `ErrorMapper.toResponse()`.
- **Logging**: Each class initializes a logger via `LoggerFactory.getLogger(ClassName::class)`. Business events use `logger.info` with structured key-value pairs (`action=`, `entity=`, `id=`). Debug-level logs are reserved for intermediate state during multi-step operations.
- **Module Communication**: Services depend only on interfaces defined in the `ports/` package, never on concrete implementations. Wiring happens in `config/` modules via dependency injection. Cross-module calls always go through the interface boundary.
- **State Management**: Application state is held in `StateStore` as immutable data classes. Mutations go through `StateStore.update { }` lambdas, which trigger UI re-renders via the observer pattern. Direct field assignment on state objects is prohibited.
```

**Anti-patterns**:

- Listing individual functions or classes instead of cross-cutting patterns
- Describing what a single file does rather than what the codebase does consistently
- Including patterns that appear only once (not truly cross-cutting)
- One-line summaries that name a pattern without explaining how it works (e.g., "Uses repository pattern" without describing the actual convention)

### Section 4: Conventions

**Convention Discovery Approach**:

- Read package manifests to understand the project's technology stack before analyzing conventions
- Use stack context to focus on relevant convention patterns (e.g., framework-specific naming, project-specific abstractions built on top of dependencies)
- Sample **10+ files** across different directories to confirm a convention is consistent, not accidental
- Distinguish between **enforced conventions** (linter/formatter rules) and **team conventions** (implicit patterns) — both are worth documenting

**Convention Categories** (include only those actually observed):

- **Naming**: camelCase, snake_case, PascalCase usage per context (variables, classes, files, directories)
- **Prefixes/Suffixes**: Consistent type indicators like `SomethingService`, `useSomething`, `SomethingProps`, `ISomething`
- **File & Directory Naming**: kebab-case files, PascalCase component files, index barrel exports, co-location patterns
- **Comments**: Tone, language, brevity, when comments are used vs omitted
- **Legacy Handling**: TODO, FIXME, NOTE, deprecated markers and their conventions
- **Import Organization**: Grouping order (stdlib → external → internal), path alias usage, barrel imports
- **Type Patterns**: Type definition co-location, shared type files, generic usage conventions

**Content Requirements**:

- Each convention should state the **rule** and give a **concrete example** showing correct usage
- When a convention has **exceptions**, note them explicitly
- Cover both code-level conventions and project-structure-level conventions

**Example Structure**:

```markdown
- **Naming**: Variables and functions use `camelCase`. Classes and types use `PascalCase`. Constants use `UPPER_SNAKE_CASE`. Boolean variables are prefixed with `is`, `has`, or `should` (e.g., `isLoading`, `hasPermission`).
- **Prefixes/Suffixes**: Service classes are suffixed with `Service` (e.g., `UserService`). React hooks are prefixed with `use` (e.g., `useAuth`). Type/interface names for component props are suffixed with `Props` (e.g., `ButtonProps`).
- **File & Directory Naming**: Component files use PascalCase (`UserProfile.tsx`). Utility and helper files use camelCase (`formatDate.ts`). Each feature directory has an `index.ts` barrel export.
- **Import Organization**: Imports are grouped in three blocks separated by blank lines: (1) external packages, (2) internal aliases (`@/`), (3) relative imports. Side-effect imports (`import './styles.css'`) appear last.
```

**Anti-patterns**:

- Listing a convention name without showing the actual rule (e.g., "Uses camelCase" without specifying where)
- Mixing conventions with behavioral patterns that belong in Section 3
- Documenting IDE or tooling settings instead of code-level conventions

### Section 5: Working Agreements

See the working agreements specification referenced from SKILL.md.

## Format Requirements

- **Language**: English only (for the content of the `AGENTS.md` file)
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
