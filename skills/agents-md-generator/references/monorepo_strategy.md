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
