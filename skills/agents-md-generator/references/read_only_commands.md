# Read-Only Commands Specification

Defines the allowed commands for repository analysis during AGENTS.md generation.

## Table of Contents

- [Allowed Command Categories](#allowed-command-categories)
- [ripgrep (`rg`) Usage Patterns](#ripgrep-rg-usage-patterns)
- [tree Command Usage](#tree-command-usage)
- [Files to Ignore](#files-to-ignore)
- [Files Allowed to Read](#files-allowed-to-read)
- [Source File Analysis Rules](#source-file-analysis-rules)

## Allowed Command Categories

### Basic Inspection

- **`pwd`**: Print working directory
- **`ls`**: List directory contents
- **`tree`**: Display directory structure
- **`find`**: File and directory discovery (Linux / macOS)
- **`Get-ChildItem`**: File and directory discovery (Windows PowerShell)

### LOC Measurement

- **`tokei`**: Count lines of code — **Required** for determining character limits (see LOC measurement specification referenced from SKILL.md)

### Content Search

```yaml
- command: rg (ripgrep)
  platform: All
  priority: Preferred
  notes: Check availability first with `rg --version`
- command: grep
  platform: Linux / macOS
  priority: Fallback
  notes: Use only if `rg` unavailable
- command: Select-String
  platform: Windows (PowerShell)
  priority: Fallback
  notes: Use only if `rg` unavailable
```

### Paginated File Reading

When additional context is needed beyond initial search results, read files in incremental ranges:

- **Linux / macOS**: `sed -n 'START,ENDp' FILE` — e.g. `sed -n '1,80p' src/app.js`
- **Windows (PowerShell)**: `Get-Content FILE | Select-Object -Skip (START-1) -First COUNT` — e.g. `Get-Content src\app.js | Select-Object -Skip 0 -First 80`

**Incremental reading pattern**:

1. Read an initial range (e.g., lines 1–80)
2. If the context is insufficient, continue from where the previous range ended (e.g., lines 81–160)
3. Repeat until enough context is collected

**Per-file reading limit**:

- Default upper bound: **800 lines** per file
- Line budget applies **from the first non-import line**; import/require/using blocks at the top of a file are excluded from the count
- Extend beyond 800 lines **only** when architecture boundaries (e.g., module exports, class definitions, route registrations) have not yet been identified
- When extending, read in additional 400-line increments and re-evaluate after each increment
- **Hard cap: 1600 lines** per file — never read beyond this limit regardless of context needs
- Collect only the context required for analysis; avoid excessive context collection that may degrade output quality

## ripgrep (`rg`) Usage Patterns

### Scope Filtering

```bash
rg "pattern" -g "*.js" -g "!*.min.js"  # Target by glob, exclude minified
rg "pattern" -g "src/**"               # Scope to a directory subtree
```

### Visibility & Configs

```bash
rg "pattern" --hidden       # Include hidden files, respect .gitignore
```

### Context Retrieval

```bash
rg "pattern" -C 5           # Include 5 surrounding lines
```

### Output Control

```bash
rg "pattern" -l             # List files only (discovery)
rg "pattern" --json         # JSON output for parsing
```

### Search Safety

```bash
rg -F "exact.string()"      # Literal search (no regex)
```

## tree Command Usage

```bash
tree -I 'node_modules|.git|dist|build|.turbo|.next|out' -L 3
```

**Purpose**: Ignore large, low-signal directories (node_modules, build artifacts, VCS metadata)

**Note**: `-L 3` is an example depth. Increase depth as needed for full structural analysis (e.g., `-L 5` or `-L 8` for deeper hierarchies).

## Files to Ignore

Lock files must NOT be read:

- `pnpm-lock.yaml`
- `package-lock.json`
- `yarn.lock`
- `poetry.lock`
- `Pipfile.lock`
- `Cargo.lock`
- `Gemfile.lock`
- `Podfile.lock`
- Any other dependency lockfile

## Files Allowed to Read

### Documentation

- `README.md`
- `CONTRIBUTING.md`
- `docs/` contents

### Style/Tooling Configuration

- `.editorconfig`
- `.eslintrc*`, `eslint.config.*`
- `.prettierrc*`
- `pyproject.toml`, `ruff.toml`, `mypy.ini`

### Package Manifests

- `package.json`
- `pyproject.toml`
- `go.mod`
- `Cargo.toml`

## Source File Analysis Rules

- **Skip**: Import/require/using sections when analyzing patterns
- **Infer Stack From**: Package manifests, not import statements
- **Additional Context**: Use paginated file reading to collect more context as needed
