# Severity Criteria

Classification criteria for code review findings by severity level.

## Critical

Issues that pose immediate risk to system integrity, security, or data.

| Category | Examples |
|----------|----------|
| **Security** | SQL injection, XSS vulnerabilities, hardcoded credentials, insecure deserialization |
| **Data Integrity** | Data loss potential, incorrect data migration, missing transaction boundaries |
| **Availability** | Infinite loops, resource leaks causing crashes, deadlock potential |
| **Authentication** | Broken auth flow, privilege escalation, session fixation |

### Indicators
- Unvalidated user input in sensitive operations
- Missing or incorrect access control checks
- Cryptographic misuse (weak algorithms, improper key handling)
- Direct database queries with string concatenation

## Major

Issues that cause incorrect behavior or significant degradation.

| Category | Examples |
|----------|----------|
| **Logic Errors** | Incorrect conditionals, off-by-one errors, wrong operator |
| **Performance** | N+1 queries, missing indexes, unbounded data fetching |
| **Error Handling** | Swallowed exceptions, missing error cases, incorrect error propagation |
| **Concurrency** | Race conditions, missing synchronization, incorrect async handling |

### Indicators
- Missing null/undefined checks on required values
- Incorrect loop boundaries or termination conditions
- Blocking calls in async contexts
- Missing retry logic for unreliable operations

## Minor

Issues affecting code quality and maintainability.

| Category | Examples |
|----------|----------|
| **Code Quality** | Long functions, deep nesting, high complexity |
| **Duplication** | Copy-pasted code, repeated patterns without abstraction |
| **Readability** | Unclear variable names, missing context, complex expressions |
| **Design** | Tight coupling, missing abstraction, god objects |

### Indicators
- Functions exceeding 50 lines
- Cyclomatic complexity > 10
- More than 3 levels of nesting
- Repeated code blocks (3+ occurrences)

## Nit

Minor suggestions for polish and consistency.

| Category | Examples |
|----------|----------|
| **Style** | Inconsistent formatting, irregular spacing |
| **Naming** | Non-descriptive names, inconsistent casing conventions |
| **Comments** | Outdated comments, missing documentation on public APIs |
| **Organization** | Import ordering, file structure |

### Indicators
- Variable names less than 3 characters (excluding common idioms: i, j, k)
- Commented-out code
- TODO comments without issue references
- Inconsistent quote style or semicolon usage
