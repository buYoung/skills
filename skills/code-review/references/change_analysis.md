# Change Analysis

Methods for categorizing and interpreting file changes in commits.

## File Type Classification

### By Purpose
| Category | Extensions/Patterns |
|----------|---------------------|
| **Source** | `.ts`, `.js`, `.py`, `.java`, `.go`, `.rs`, `.cpp`, `.c` |
| **Test** | `*.test.*`, `*.spec.*`, `__tests__/*`, `test_*.py` |
| **Config** | `.json`, `.yaml`, `.yml`, `.toml`, `.env*`, `.*rc` |
| **Documentation** | `.md`, `.rst`, `.txt`, `docs/*` |
| **Build** | `Dockerfile`, `Makefile`, `*.gradle`, `pom.xml` |
| **Dependencies** | `package.json`, `requirements.txt`, `go.mod`, `Cargo.toml` |

### By Change Type
| Status | Description |
|--------|-------------|
| **Added** | New file introduced |
| **Modified** | Existing file changed |
| **Deleted** | File removed |
| **Renamed** | File path changed |

## Diff Interpretation

### Hunk Header Format
```
@@ -<old_start>,<old_count> +<new_start>,<new_count> @@ <context>
```
- **old_start/count**: Line position in original file
- **new_start/count**: Line position in new file
- **context**: Function or class name (if detectable)

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
| **Lines Added** | Count of `+` prefixed lines |
| **Lines Deleted** | Count of `-` prefixed lines |
| **Net Change** | Added - Deleted |
| **Churn** | Added + Deleted |

### Complexity Indicators
- **Files Changed**: Total number of modified files
- **Hunks per File**: Number of separate change regions
- **Functions Touched**: Distinct functions with changes
