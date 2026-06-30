# Read-Only Commands Specification

Defines the allowed commands for repository analysis during AGENTS.md generation.

## Table of Contents

- [Allowed Command Categories](#allowed-command-categories)
- [Symbol-Level Analysis (Optional, requires Serena MCP)](#symbol-level-analysis-optional-requires-serena-mcp)
- [ripgrep (`rg`) Usage Patterns](#ripgrep-rg-usage-patterns)
- [Dependency Discovery](#dependency-discovery)
- [Git History Signals (Update Mode)](#git-history-signals-update-mode)
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

### Git History Signals

Use git only as an update-mode ownership discovery signal. Git history helps prioritize where to inspect next; current code and documented contracts decide what can be written into `AGENTS.md`.

Allowed commands:

- **`python scripts/git_ownership_signals.py`**: Preferred compact high-churn path aggregation helper; emits Markdown-KV
- **`git log`**: Commit metadata, changed paths, rename/delete status
- **`git show --stat`**: Compact stats for candidate commits only
- **`git show --name-only`**: Changed path list for candidate commits only

Do not read broad diffs by default. Use `git show` without `--stat` or `--name-only` only for a narrow candidate boundary after metadata/path signals are insufficient.

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

## Symbol-Level Analysis (Optional, requires Serena MCP)

When Serena MCP is available, prefer these tools over `rg` / `grep` / `find` for Section 3 (Core Behaviors & Patterns) and Section 4 (Conventions) deep analysis. Symbolic queries return precise definitions and references without re-parsing files line by line, which is more accurate for cross-layer tracing.

### Read-Only Tools

- **`find_symbol`**: Locate symbol definitions (functions, classes, methods) by `name_path` and optional `relative_path`
- **`find_referencing_symbols`**: Cross-reference callers — required for tracing flows end-to-end (e.g., error propagation, wiring chains)
- **`find_referencing_code_snippets`**: Inspect actual usage contexts surrounding a symbol
- **`get_symbols_overview`**: Top-level symbol map of a file — use to compare multiple implementations of the same role (e.g., 5 dialogs, 5 commands)
- **`search_for_pattern`**: Regex search across the codebase (alternative to `rg`)
- **`list_dir` / `find_file` / `read_file`**: File navigation and reading alternatives

### Constraints

- Use **only the read-only tools above**. Do **NOT** invoke write/edit tools (`replace_symbol_body`, `insert_after_symbol`, `insert_before_symbol`, `rename_symbol`, `safe_delete_symbol`, `create_text_file`, `edit_memory`, etc.) or `execute_shell_command` during AGENTS.md generation — generation is a read-only analysis task.
- Memory tools (`write_memory`, `read_memory`, `list_memories`, `delete_memory`, `rename_memory`) are out of scope for this skill.

### Fallback

If Serena MCP is not available, fall back to `rg` + `sed -n` (Linux/macOS) or `Select-String` + `Get-Content` (Windows) per the patterns in [ripgrep (`rg`) Usage Patterns](#ripgrep-rg-usage-patterns) and [Paginated File Reading](#paginated-file-reading).

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

## Git History Signals (Update Mode)

Git history is optional and non-authoritative. If git is unavailable, the repository is a shallow clone, or history commands fail, skip this step and continue with current-code analysis.

### Scope Selection

1. Prefer the change range since the target `AGENTS.md` was last updated by this skill.
2. If no reliable update anchor exists, use roughly the last 3 months.
3. Treat 3 months as an activity-adjusted default, not a hard truth. If the range is too sparse to reveal ownership movement, cautiously expand by commit count. If it is too noisy, cap the result set by top changed paths and report the truncation to the user.

Useful anchor commands:

```bash
# Find recent updates to the target AGENTS.md
git log --follow --date=short --pretty=format:"%h %ad %s" -- <path/to/AGENTS.md>

# Count commits in the fallback window before collecting path detail
git log --since="3 months ago" --oneline | wc -l
```

### Progressive Query Pattern

Start with the bundled compact helper. It prints Markdown-KV rather than JSON to minimize context use:

```bash
python ./scripts/git_ownership_signals.py <target_directory>
```

If an update anchor exists:

```bash
python ./scripts/git_ownership_signals.py <target_directory> --anchor <anchor_commit>
```

The output shape is stable:

```markdown
repo: /abs/path
scope: .
range: since
since: 3 months ago
commits: 142
limit: 20
min_commits: 2
truncated: true
deleted: excluded

top_changed_paths:
- 37 src/payment/retry.ts last=2026-06-12 exists=true
- 31 src/payment/PaymentService.ts last=2026-06-10 exists=true

notes:
- excludes: *.lock, pnpm-lock.yaml, package-lock.json, yarn.lock, node_modules/**, vendor/**, dist/**, build/**
- use: discovery signal only; confirm against current code or documented contracts
```

Only expand manually when the compact helper is too sparse, truncated, or points to an ambiguous boundary. Start manual expansion with metadata and changed paths only:

```bash
git log --since="3 months ago" --date=short --name-only --pretty=format:"%h %ad %s"
```

If an update anchor exists, replace the time filter with the anchored range:

```bash
git log <anchor_commit>..HEAD --date=short --name-only --pretty=format:"%h %ad %s"
```

Then inspect only candidate signals:

```bash
# Rename/delete movement only
git log --since="3 months ago" --name-status --diff-filter=RD --pretty=format:"%h %ad %s"

# Compact stat for a candidate commit
git show --stat <commit>

# Changed paths for a candidate commit
git show --name-only <commit>
```

### Signal Extraction

Look for:

- High-churn files surfaced by `git_ownership_signals.py`
- Changed-path clusters that repeatedly move together
- Repeated co-change between entry points, state owners, contract files, and external surfaces
- Renames/moves that show responsibility moved rather than disappeared
- Deleted paths that may indicate removed ownership, but confirm against current code before documenting absence
- High-churn boundary files such as route/command registrations, schema files, public exports, stores, adapters, or integration surfaces

### Exclusions

Ignore or down-rank:

- Lock files and generated/vendor/build output listed in [Files to Ignore](#files-to-ignore)
- Merge commits
- Bot-only automation churn
- Broad formatting-only commits
- Bulk rename commits unless rename/move tracking is the specific question
- Churn caused only by dependency upgrades or generated artifacts

### Output Rules

- Do not document a boundary from git history alone.
- Do not persist timeline summaries such as "earlier focus", "recent focus", or "current focus" in `AGENTS.md`.
- Use timeline summaries only in the final user-facing report, unless the transition is currently represented in code as a live migration, compatibility layer, deprecated path, or adapter boundary.
- Do not map ownership to authors, teams, or blame output. Ownership in this skill means system responsibility boundary, not person ownership.

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
- `tsconfig*.json`, `jsconfig*.json`
- `pyproject.toml`, `ruff.toml`, `mypy.ini`, `pytest.ini`, `tox.ini`
- Build configs such as `vite.config.*`, `webpack.config.*`, `rollup.config.*`, `build.gradle*`, `pom.xml`, `Makefile`, `Dockerfile`
- Test configs such as `vitest.config.*`, `jest.config.*`, `playwright.config.*`, `cypress.config.*`
- Workspace configs such as `pnpm-workspace.yaml`, `turbo.json`, `nx.json`, `lerna.json`, `rush.json`, `.moon/workspace.yml`
- CI workflow files such as `.github/workflows/*`, `.gitlab-ci.yml`, `azure-pipelines.yml`, `circle.yml`

### Package Manifests

- `package.json`
- `pyproject.toml`
- `go.mod`
- `Cargo.toml`

Readable command and configuration files are inputs for analysis only. Use them to infer stack, verification placement, conventions, and boundaries; do not copy their contents into generated `AGENTS.md` as command catalogs or add a "Common Commands" section.

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
