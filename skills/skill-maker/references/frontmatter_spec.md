# YAML Frontmatter Specification

Defines the required YAML frontmatter format for SKILL.md files.

## Required Fields

```yaml
- field: name
  type: string
  constraints: "≤64 characters, lowercase letters/digits/hyphens only, no leading/trailing hyphens"
- field: description
  type: string
  constraints: "≤1024 characters, non-empty"
```

## Optional Fields

```yaml
- field: license
  type: string
  constraints: License name or reference to a bundled license file
- field: compatibility
  type: string
  constraints: "≤500 characters. Environment requirements (intended product, system packages, network access, etc.)"
- field: metadata
  type: map
  constraints: Arbitrary string key-value mapping for additional properties
- field: allowed-tools
  type: string
  constraints: "Space-delimited list of pre-approved tools. Experimental \u2014 support varies by agent implementation"
```

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
- **Consecutive hyphens**: Not allowed (`--` is invalid)
- **Directory match**: Must match the parent directory name
- **Examples**: `convert-schema`, `generate-docs`, `gh-address-comments`

## Description Field

Describes both **what the skill does** and **when to use it**. Should include specific keywords that help agents identify relevant tasks.

**Good example**:
- `Extracts text and tables from PDF files, fills PDF forms, and merges multiple PDFs. Use when working with PDF documents or when the user mentions PDFs, forms, or document extraction.`

**Poor example**:
- `Helps with PDFs.`

**More examples**:
- `Generates AI agent skill packages with SKILL.md and optional bundled resources.`
- `Converts raw SQL queries into type-safe Kysely TypeScript code.`

## Optional Field Examples

```yaml
license: Apache-2.0
```

```yaml
compatibility: Requires git, docker, jq, and access to the internet
```

```yaml
metadata:
  author: example-org
  version: "1.0"
```

```yaml
allowed-tools: Bash(git:*) Bash(jq:*) Read
```

## Naming Convention

```yaml
- pattern: Verb-led
  example: convert-schema
  use_case: Action-oriented skills
- pattern: Tool-namespaced
  example: gh-address-comments
  use_case: Platform-specific skills
- pattern: Domain-prefixed
  example: react-component-gen
  use_case: Framework-specific skills
```
