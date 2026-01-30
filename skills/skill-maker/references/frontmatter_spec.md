# YAML Frontmatter Specification

Defines the required YAML frontmatter format for SKILL.md files.

## Required Fields

| Field | Type | Constraints |
|-------|------|-------------|
| `name` | string | ≤64 characters, lowercase letters/digits/hyphens only, no leading/trailing hyphens |
| `description` | string | ≤1024 characters, non-empty |

## Format

```yaml
---
name: {skill-name}
description: {description}
---
```

## Name Field

- **Character set**: `[a-z0-9-]`
- **Pattern**: `/^[a-z0-9]+(-[a-z0-9]+)*$/`
- **Examples**: `convert-schema`, `generate-docs`, `gh-address-comments`

## Description Field

Describes what the skill provides and its applicable context.

**Content**: Capability statement (what it does/knows)

**Examples**:
- `Generates AI agent skill packages with SKILL.md and optional bundled resources.`
- `Converts raw SQL queries into type-safe Kysely TypeScript code.`

## Naming Convention

| Pattern | Example | Use Case |
|---------|---------|----------|
| Verb-led | `convert-schema` | Action-oriented skills |
| Tool-namespaced | `gh-address-comments` | Platform-specific skills |
| Domain-prefixed | `react-component-gen` | Framework-specific skills |
