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

Patterns derived from code analysis:

- **Debugging & Logging**: Logger utilities, log levels, structured logs
- **Error Handling**: Error propagation, recovery strategies
- **Control Flow**: Early returns, guard clauses
- **Module Structure**: Responsibility separation between modules

### Section 4: Conventions

- **Naming**: camelCase, snake_case, PascalCase usage
- **Prefixes/Suffixes**: `SomethingService`, `useSomething`, `SomethingProps`
- **Comments**: Tone, language, brevity
- **Legacy Handling**: TODO, FIXME, NOTE, deprecated markers

### Section 5: Working Agreements

See the working agreements specification referenced from SKILL.md.

## Format Requirements

- **Language**: English only (for the content of the `AGENTS.md` file)
- **Max Length**: Dynamic based on repository LOC (see LOC measurement specification referenced from SKILL.md)
- **Format**: Valid Markdown
- **Tone**: Concise, neutral
- **Headings**: Short and descriptive
- **Content Style**: Compact bullet points or short sentences

## Anti-Patterns (Excluded Content)

- "Common Commands" section
- "How to run" instructions
- "Testing Strategy" documentation
- Build/deploy instructions
- Detailed CI pipeline configuration
