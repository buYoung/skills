# Monorepo Generation Strategy

Defines the strategy for generating AGENTS.md files in a monorepo environment.

## Generation Modes

```yaml
- mode: All (Default)
  scope: Root + All Packages
  when_to_use: Initial setup, full regeneration
- mode: Root Only
  scope: Root document only
  when_to_use: Update shared working agreements
- mode: Single Package
  scope: One specific package
  when_to_use: Package-specific changes
```

## Document Hierarchy

```yaml
- document: Root
  location: /AGENTS.md
  sections: 3
  character_limit: Dynamic based on LOC
- document: Package
  location: Per-package directories discovered via workspace config (see monorepo_detection.md)
  sections: 5 (Standard)
  character_limit: Dynamic based on LOC
```

## LOC Measurement

- **Root Document**: Run `tokei` in root directory
- **Package Document**: Run `tokei` inside the package directory

## Working Agreements Inheritance

- **Root**: Full working agreements (master copy)
- **Package**: "See root `/AGENTS.md`" (reference first, no duplicated root rules)
- **Package-local verification**: If tests, type-check, or other verification guidance applies only to one package, place that guidance in that package's `AGENTS.md`, not the root document

**Note**: Package-specific behaviors and conventions belong in **Section 3 (Core Behaviors & Patterns)** and **Section 4 (Conventions)**, not in Working Agreements. The only package-specific Working Agreements addition is package-local verification guidance discovered from package-local configs or scripts.

## Section Boundary Rules

Defines what content belongs in which section of a package AGENTS.md.

```yaml
- content_type: Package-specific implementation patterns
  target_section: Section 3 (Core Behaviors & Patterns)
  examples: Logging approach, error handling, control flow
- content_type: Package-specific naming/style conventions
  target_section: Section 4 (Conventions)
  examples: Naming rules, comment style, file organization
- content_type: Common working principles across all packages
  target_section: Section 5 (Working Agreements)
  examples: Response language, code block handling, commit rules, context building
- content_type: Package-local tests/type-check/verification guidance
  target_section: Package Section 5 (Working Agreements)
  examples: Package-only type-check or test command discovered from local package config
```

**Anti-pattern**: Do NOT place package-specific technical details (e.g., how a particular package handles errors or structures modules) into Section 5 (Working Agreements). Working Agreements are reserved for shared behavioral rules that apply uniformly across the entire repository, plus package-local verification guidance when it cannot be stated correctly at the root.
