# Read-Only Commands Specification

Defines the allowed commands for repository analysis during AGENTS.md generation.

## Allowed Command Categories

### Basic Inspection

| Command | Purpose |
|---------|---------|
| `pwd` | Print working directory |
| `ls` | List directory contents |
| `tree` | Display directory structure |
| `cat` | Display file contents |

### LOC Measurement

| Command | Purpose | Notes |
|---------|---------|-------|
| `tokei` | Count lines of code | **Required** for determining character limits. See [loc_measurement.md](./loc_measurement.md) |

### Content Search

| Command | Priority | Notes |
|---------|----------|-------|
| `rg` (ripgrep) | **Preferred** | Check availability first with `rg --version` |
| `grep` | Fallback | Use only if `rg` unavailable |
| `find` | Fallback | Use only if `rg` unavailable |

## ripgrep (`rg`) Usage Patterns

### Scope Filtering

```bash
rg "pattern" -t ts          # Target TypeScript files
rg "pattern" -g "*.js" -g "!*.min.js"  # Target JS, exclude minified
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

### Line Limit Enforcement

Use `rg` with match limit to enforce line limits without external piping:

```bash
rg [FILE_PATH] --max-count 1200   # limit to 1200 matching lines
```

**Note**: Use `--max-count` (or `-m`) to limit output lines directly within `rg`. Avoid piping to `head` as it may conflict with global workspace rules.

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

- **Line Limit**: Maximum 1600 lines per file (excluding imports)
- **Skip**: Import/require/using sections
- **Infer Stack From**: Package manifests, not import statements
