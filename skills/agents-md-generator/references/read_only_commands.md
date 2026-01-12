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

```bash
rg -v "^import" [FILE_PATH] -m 800   # Skip imports, max 800 lines
```

## tree Command Usage

```bash
tree -I 'node_modules|.git|dist|build|.turbo|.next|out' -L 3
```

**Purpose**: Ignore large, low-signal directories (node_modules, build artifacts, VCS metadata)

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

- **Line Limit**: Maximum 800 lines per file (excluding imports)
- **Skip**: Import/require/using sections
- **Infer Stack From**: Package manifests, not import statements
