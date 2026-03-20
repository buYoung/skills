# Read-Only Commands Specification

Defines the allowed commands for repository analysis during AGENTS.md generation.

## Table of Contents

- [Allowed Command Categories](#allowed-command-categories)
- [ripgrep (`rg`) Usage Patterns](#ripgrep-rg-usage-patterns)
- [Dependency Discovery](#dependency-discovery)
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

## Dependency Discovery

Identify the technology stack by reading package manifest files before analyzing source code. This step provides essential context for Core Behaviors & Patterns and Conventions analysis.

### Workflow

1. **Check project root first**: Look for package manifests in the project root directory
2. **Read manifests directly**: Use paginated reading (`sed -n` / `Get-Content`) to read the manifest content — this is more reliable than pattern-based search which may produce false positives in source files (e.g., `require` in CJS)
3. **Fallback to subdirectories**: If no manifest is found at root, search subdirectories up to depth 2
4. **Build stack context**: Note key frameworks, libraries, and tooling to guide subsequent pattern and convention analysis

### Commands

```bash
# Step 1: Check project root for manifests
ls package.json pyproject.toml go.mod Cargo.toml *.csproj \
  build.gradle* pom.xml Gemfile 2>/dev/null

# Step 2: Read the detected manifest directly
sed -n '1,80p' <detected_manifest>

# Step 3 (fallback): If no manifest at root, search subdirectories
find . -maxdepth 2 -type f \( -name "package.json" -o -name "pyproject.toml" \
  -o -name "go.mod" -o -name "Cargo.toml" -o -name "*.csproj" \
  -o -name "build.gradle*" -o -name "pom.xml" -o -name "Gemfile" \) | head -20
```

### Rules

- **Read manifests directly** rather than searching with `rg` — avoids false positives from source code (e.g., `require()` calls in CJS modules)
- Do **not** hard-code language-specific extraction logic; adapt reading range to whatever manifest format is discovered
- Focus on identifying **frameworks and libraries** that influence architectural patterns and naming conventions
- Skip lock files — only read the manifest source files listed in [Files Allowed to Read](#files-allowed-to-read)

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
- **Infer Stack From**: Package manifests, not import statements — read dependency sections from detected manifests to build technology context before source analysis (see [Dependency Discovery](#dependency-discovery))
- **Additional Context**: Use paginated file reading to collect more context as needed

### Deep Analysis Strategy

Surface-level pattern scanning (searching for keywords like `try`, `catch`, `log`) is insufficient for Sections 3 and 4. Use these strategies to find deeper patterns:

- **Cross-reference callers**: When you find a utility, service, or shared abstraction, search for its callers to understand how it's actually used across the codebase. The usage pattern often reveals conventions not visible from the definition alone.
- **Trace flows end-to-end**: When documenting a pattern like error handling, don't stop at "uses AppError". Follow the error from where it's created → how it propagates → how it transforms at boundaries → how it reaches the user. Each layer may add a convention worth documenting.
- **Sample configuration/registration files**: Plugin manifests, DI configs, route files, and localization bundles often encode structural conventions (grouping order, key hierarchies, feature bundling) that source code analysis alone won't reveal.
- **Compare multiple implementations of the same role**: If the codebase has 5 dialogs, 5 commands, or 5 hooks, read at least 3 to identify the shared skeleton vs. per-instance variation. The skeleton is the convention.
- **Check error/failure paths**: Read not just the happy path but how the code handles failures — recovery strategies, fallback behavior, degraded states. These are often the most important patterns to document and the easiest to miss.
