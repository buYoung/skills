# Impact Detection

Techniques for identifying side effects and dependencies of code changes.

## Dependency Tracing

### Function/Method Usage Search
```bash
rg "<function_name>\(" --type <lang>
```
- **Purpose**: Find all call sites of a modified function

### Class/Type Reference Search
```bash
rg "(import|from).*<class_name>" --type <lang>
rg "<class_name>" --type <lang>
```
- **Purpose**: Locate imports and usages of modified classes

### Export Analysis
```bash
rg "export.*(function|class|const).*<name>"
```
- **Purpose**: Determine if changed entity is publicly exposed

### Interface/Type Reference Search
```bash
rg "(implements|extends)\s+<class_name>" --type <lang>
```
- **Purpose**: Find classes that implement or extend modified interfaces/base classes

### Constant/Enum Usage Search
```bash
rg "<EnumName>\.<member>" --type <lang>
```
- **Purpose**: Trace usage of modified constants or enum members

### Configuration Key Search
```bash
rg "['\"]<config_key>['\"]" --type <lang>
```
- **Purpose**: Find code referencing modified config keys or environment variables

### Cross-File Type Search (broad)
```bash
rg "<name>" -l
```
- **Purpose**: Quick file-level scan when unsure of usage patterns; refine with specific patterns after

### Search Limitations
- **Dynamic calls**: Reflection, dependency injection, decorators, and string-based lookups are invisible to `rg`. Note these as unverifiable in findings.
- **Aliases/Re-exports**: A symbol may be re-exported under a different name. Search for the original name may miss indirect consumers.
- **Generated code**: Auto-generated files may reference symbols but are not authored code. Exclude from impact analysis.

## Impact Categories

### Direct Impact
- **Callers**: Functions that directly invoke modified code
- **Implementors**: Classes implementing modified interfaces
- **Extenders**: Classes extending modified base classes

### Indirect Impact
- **Transitive Callers**: Functions calling the direct callers
- **Shared State**: Code accessing modified global/shared variables
- **Event Listeners**: Handlers for events emitted by modified code

## Test Coverage Check

### Related Test Files
| Source Pattern | Test Pattern |
|----------------|--------------|
| `src/foo.ts` | `src/foo.test.ts`, `src/foo.spec.ts` |
| `src/foo.ts` | `__tests__/foo.test.ts` |
| `foo.py` | `test_foo.py`, `foo_test.py` |

### Test Existence Verification
```bash
fd "<basename>.(test|spec).<ext>" <test_dir>
```

## API Breaking Change Detection

When a modified function/class is publicly exported, check for breaking changes:

| Change Type | Breaking? | Detection |
|-------------|-----------|----------|
| **Parameter added (required)** | Yes | Diff shows new non-optional parameter |
| **Parameter removed** | Yes | Diff shows parameter deletion |
| **Parameter type changed** | Yes | Diff shows type annotation change |
| **Return type changed** | Yes | Diff shows return type annotation change |
| **Method/field removed from class** | Yes | Diff shows public member deletion |
| **Enum member removed** | Yes | Diff shows member deletion |
| **HTTP endpoint path/method changed** | Yes | Diff shows route definition change |
| **Parameter added (optional with default)** | No | New parameter has default value |
| **New method/field added** | No | Additive changes are backward-compatible |

### Verification Steps
1. Confirm the changed entity is exported/public (`rg "export.*<name>"`)
2. Count consumers (`rg "<name>" -l | wc -l`)
3. If breaking + consumers exist → **Critical** finding

## Risk Indicators

| Indicator | Risk Level | Description |
|-----------|------------|-------------|
| **No Tests** | High | Modified code lacks test coverage |
| **Many Callers** | Medium | Change affects multiple consumers |
| **Public API** | High | Exported interface modified |
| **Breaking API Change** | Critical | Public signature modified with existing consumers |
| **Shared State** | High | Global or singleton state modified |
| **Database Schema** | Critical | Data structure changes |
| **Config Change** | Medium | Environment or runtime config modified |

## Analysis Commands

### Find Dependents (TypeScript/JavaScript)
```bash
rg "from ['\"].*/<module_name>['\"]"
```

### Find Implementations (Go)
```bash
rg "func \(.*\) <method_name>\("
```

### Find Overrides (Python)
```bash
rg "def <method_name>\(self"
```
