---
name: agents-md-generator
description: Analyze repository structure and generate standardized AGENTS.md files that serve as contributor guides for AI agents. Supports both single-repo and monorepo structures. Measures LOC to determine character limits and produces structured documents covering overview, folder structure, patterns, conventions, and working agreements.
license: MIT
---

# AGENTS.md Generation Capability

This skill enables the agent to generate `AGENTS.md` files that serve as contributor guides for AI agents working on a codebase.

## Core Capability

- **Function**: Analyze repository structure and generate a standardized `AGENTS.md` document
- **Output Format**: Markdown file with structured sections
- **Character Limit**: Dynamic, based on repository LOC (Lines of Code)
- **Monorepo Support**: Automatically detects monorepo structures and generates hierarchical documentation (Root + Packages)

## Output Sections

### Standard / Package Document (5 Sections)
For single repositories or individual packages in a monorepo:

- **Overview**: 1-2 sentence project description (abstract, no tool/framework lists)
- **Folder Structure**: Key directories and their contents
- **Core Behaviors & Patterns**: Logging, error handling, control flow, module structure patterns observed in code
- **Conventions**: Naming, comments, code style derived from analysis
- **Working Agreements**: Rules for agent behavior and communication

### Monorepo Root Document (3 Sections)
For the root of a monorepo structure:

- **Overview**: 1-2 sentences describing the monorepo's purpose
- **Folder Structure**: High-level map of apps, packages, and shared configs
- **Working Agreements**: Common working agreements applicable to all packages

## Generation Modes (Monorepo)

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

See [./references/monorepo_strategy.md](./references/monorepo_strategy.md) for detailed strategy.

## Tools

This skill uses the following read-only tools for repository analysis. See [./references/read_only_commands.md](./references/read_only_commands.md) for detailed usage patterns.

- **`tokei`**: LOC measurement (required)
- **`rg` (ripgrep)**: Content search (preferred)
- **`grep` / `Select-String`**: Content search (fallback per OS)
- **`sed -n` / `Get-Content \| Select-Object`**: Paginated file reading per OS
- **`tree`**: Directory structure visualization
- **`find`**: File and directory discovery (Linux / macOS)
- **`ls`, `pwd`**: Basic directory navigation

## Domain Knowledge

- **LOC Measurement**: Capability to measure repository size and determine character limits. See [./references/loc_measurement.md](./references/loc_measurement.md)
- **Repository Analysis**: Capability to inspect and understand codebase structure. See [./references/read_only_commands.md](./references/read_only_commands.md)
- **Output Template**: Standardized AGENTS.md structure specification. See [./references/agents_md_template.md](./references/agents_md_template.md)
- **Working Agreements**: Agent behavior rules for generated documents. See [./references/working_agreements.md](./references/working_agreements.md)
- **Monorepo Detection**: Capability to identify monorepo structures. See [./references/monorepo_detection.md](./references/monorepo_detection.md)
- **Monorepo Strategy**: Strategy for generating documentation in monorepos. See [./references/monorepo_strategy.md](./references/monorepo_strategy.md)

## Constraints

- **Read-Only Analysis**: Repository inspection uses only non-destructive commands
- **No Run/Test/Build/Deploy**: Generated AGENTS.md excludes execution instructions
- **Files to Ignore**: Lock files (`pnpm-lock.yaml`, `package-lock.json`, `yarn.lock`, etc.)
