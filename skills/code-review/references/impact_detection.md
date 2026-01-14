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

## Risk Indicators

| Indicator | Risk Level | Description |
|-----------|------------|-------------|
| **No Tests** | High | Modified code lacks test coverage |
| **Many Callers** | Medium | Change affects multiple consumers |
| **Public API** | High | Exported interface modified |
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
