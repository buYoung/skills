# Monorepo Generation Strategy

Defines the strategy for generating AGENTS.md files in a monorepo environment.

## Generation Modes

| Mode | Scope | When to Use |
|------|-------|-------------|
| All (Default) | Root + All Packages | Initial setup, full regeneration |
| Root Only | Root document only | Update shared working agreements |
| Single Package | One specific package | Package-specific changes |

## Document Hierarchy

| Document | Location | Sections | Character Limit |
|----------|----------|----------|-----------------|
| Root | `/AGENTS.md` | 3 | Dynamic based on LOC |
| Package | `/packages/*/AGENTS.md`, `/apps/*/AGENTS.md`, `/libs/*/AGENTS.md` | 5 (Standard) | Dynamic based on LOC |

## LOC Measurement

| Target | Method |
|--------|--------|
| Root Document | Run `tokei` in root directory |
| Package Document | Run `tokei` inside the package directory |

## Working Agreements Inheritance

| Document | Working Agreements Content |
|----------|---------------------------|
| Root | Full working agreements (master copy) |
| Package | "See root `/AGENTS.md`" (reference only, no additions) |

**Note**: Package-specific behaviors and conventions belong in **Section 3 (Core Behaviors & Patterns)** and **Section 4 (Conventions)**, not in Working Agreements.

## Section Boundary Rules

Defines what content belongs in which section of a package AGENTS.md.

| Content Type | Target Section | Examples                                                               |
|-------------|----------------|------------------------------------------------------------------------|
| Package-specific implementation patterns | Section 3 (Core Behaviors & Patterns) | Logging approach, error handling, control flow                         |
| Package-specific naming/style conventions | Section 4 (Conventions) | Naming rules, comment style, file organization                         |
| Common working principles across all packages | Section 5 (Working Agreements) | Response language, code block handling, commit rules, context building |

**Anti-pattern**: Do NOT place package-specific technical details (e.g., how a particular package handles errors or structures modules) into Section 5 (Working Agreements). Working Agreements are reserved for shared behavioral rules that apply uniformly across the entire repository.
