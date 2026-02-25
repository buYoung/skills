# Change Analysis

Methods for categorizing and interpreting file changes in commits.

## File Type Classification

### Default Classification Set

| Category | Extensions/Patterns |
|----------|---------------------|
| **Source** | `.ts`, `.tsx`, `.js`, `.jsx`, `.py`, `.java`, `.kt`, `.kts`, `.go`, `.rs`, `.cpp`, `.c`, `.h`, `.hpp`, `.cs`, `.swift`, `.php`, `.rb` |
| **Test** | `*.test.*`, `*.spec.*`, `__tests__/*`, `tests/*`, `test_*.py`, `*_test.*` |
| **Config** | `.json`, `.yaml`, `.yml`, `.toml`, `.ini`, `.env*`, `.*rc`, `config/*` |
| **Documentation** | `.md`, `.rst`, `.txt`, `docs/*` |
| **Build/CI** | `Dockerfile*`, `Makefile`, `*.gradle*`, `pom.xml`, `.github/workflows/*`, `build.*` |
| **Dependencies/Manifests** | `package.json`, `pyproject.toml`, `requirements*.txt`, `go.mod`, `Cargo.toml`, `Gemfile`, `composer.json` |

### Project Override Model

Classification supports a layered model:

1. Apply the default classification set
2. Apply repository-local overrides (naming conventions, folder layouts, generated markers)
3. Resolve conflicts by preferring explicit project conventions over defaults

## Change Type Classification

| Status | Description |
|--------|-------------|
| **Added** | New file introduced |
| **Modified** | Existing file changed |
| **Deleted** | File removed |
| **Renamed** | File path changed |
| **Copied** | File duplicated with or without modifications |
| **Mode Changed** | File permission or mode changed |

## Diff Interpretation

### Hunk Header Format
```
@@ -<old_start>,<old_count> +<new_start>,<new_count> @@ <context>
```
- **old_start/count**: Line position in original file
- **new_start/count**: Line position in modified file
- **context**: Function, class, or nearby structural context (when detectable)

### Line Prefixes

| Prefix | Meaning |
|--------|---------|
| `-` | Line removed |
| `+` | Line added |
| ` ` | Context line (unchanged) |

## Change Scope Metrics

### Size Indicators

| Metric | Calculation |
|--------|-------------|
| **Lines Added** | Count of `+` lines |
| **Lines Deleted** | Count of `-` lines |
| **Net Change** | Added - Deleted |
| **Churn** | Added + Deleted |

### Complexity Indicators

- **Files Changed**: Total number of changed files
- **Hunks per File**: Number of separate changed regions
- **Behavioral Units Touched**: Distinct behavior-bearing sections modified

## Noise Filtering

Large diffs often include non-reviewable or low-signal noise.

| Noise Type | Detection Pattern | Handling |
|------------|-------------------|----------|
| **Generated Files** | `generated/`, `gen/`, `*.g.dart`, `*.pb.*`, `*.generated.*` | Mark as non-reviewable; inspect generation source instead |
| **Dependency Lock Files** | `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `go.sum`, `Cargo.lock`, `Podfile.lock` | Verify manifest consistency; skip line-by-line logic review |
| **Minified/Bundled Artifacts** | `*.min.js`, `*.bundle.js`, transpiled distribution directories | Exclude from logic findings unless artifact integrity is in scope |
| **Third-Party/Vendor Code** | `vendor/`, `third_party/`, `external/` | Exclude from direct finding ownership; evaluate integration impact only |
| **Mechanical Renames/Moves** | Status mostly `R`/`C` with no behavioral delta | Validate path integrity, then deprioritize content review |
| **Format-Only Changes** | Whitespace/indent/order-only changes | Note as low-risk and skip deep logic analysis |

## Reviewable vs Non-Reviewable Classification

| Class | Definition | Review Depth |
|-------|------------|--------------|
| **Reviewable** | Files with author-owned behavioral/configuration impact | Full analysis |
| **Conditionally Reviewable** | Generated artifacts, lock files, mirrored configs | Consistency/integrity checks only |
| **Non-Reviewable** | External/vendor artifacts without local ownership | Exclude from findings unless runtime risk is introduced |

## Large Change Strategy

### Scale-Based Strategy

| Files Changed | Strategy |
|---------------|----------|
| **1-10** | Full line-by-line review |
| **11-30** | Prioritize reviewable source/config changes, then tests/docs |
| **30+** | Separate noise first, apply targeted sampling for low-risk files, full-review mandatory high-risk files |

### Sampling Guidance for Large Changes

- Sample low-risk repetitive files by pattern and representative hunks
- Record sampled scope explicitly in analysis limitations
- Avoid generalized conclusions from unsampled categories

### Mandatory Full-Review Risk Files

The following classes always receive full review regardless of change size:

- Security/authentication/authorization related files
- Data schema, migration, and persistence contract files
- Runtime entrypoints and dispatch/routing bindings
- Critical configuration files affecting production behavior
