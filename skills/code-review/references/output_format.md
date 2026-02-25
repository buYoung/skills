# Output Format

Structure and formatting specification for code review results.

## Review Report Structure

```
## Review Summary
- **Commit**: <hash> (<short_message>)
- **Author**: <name>
- **Files Changed**: <count>
- **Lines**: +<added> / -<deleted>

## Findings

### Critical (<count>)
...

### Major (<count>)
...

### Minor (<count>)
...

### Nit (<count>)
...

## Verdict
<APPROVE | REQUEST_CHANGES | COMMENT>
```

## Finding Entry Format

```
#### [<severity>] <title>
- **File**: `<file_path>:<line_number>`
- **Issue**: <description>
- **Suggestion**: <recommendation>
```

### Example Entry
```
#### [Major] Missing null check
- **File**: `src/user/service.ts:45`
- **Issue**: `user.email` accessed without verifying user object exists
- **Suggestion**: Add null check before accessing properties
```

## Verdict Criteria

### Base Rules

| Verdict | Condition |
|---------|-----------|
| **REQUEST_CHANGES** | Any Critical finding exists |
| **REQUEST_CHANGES** | 3+ Major findings exist |
| **COMMENT** | Major findings exist (1-2) |
| **COMMENT** | 5+ Minor findings exist |
| **APPROVE** | Only Minor/Nit findings or none |

### Override Rules
Base rules may be overridden when context demands it:

| Context | Override |
|---------|-----------|
| Major finding involves **incorrect business logic** or **data corruption** | Escalate to REQUEST_CHANGES regardless of count |
| Major finding is in **dead/unreachable code path** | May downgrade to COMMENT |
| All findings are in **test files only** | COMMENT unless tests mask production bugs |

## Grouping Options

### By Severity (Default)
Findings grouped under severity headers

### By File
```
## src/user/service.ts
- [Major] Missing null check (L45)
- [Nit] Variable naming (L12)

## src/user/controller.ts
- [Minor] Long function (L30-85)
```

## Positive Feedback

Include a `Highlights` section when noteworthy good practices are observed:

```
## Highlights
- <description of good practice and where it appears>
```

### Examples of Highlight-Worthy Patterns
- Well-structured error handling with clear recovery paths
- Comprehensive test coverage accompanying the change
- Clean separation of concerns or thoughtful abstraction
- Proactive performance optimization
- Clear and helpful commit messages/code comments

> Include highlights only when genuinely earned. Omit the section entirely if nothing stands out.

## Summary Statistics

| Metric | Description |
|--------|-------------|
| **Total Findings** | Sum of all severity counts |
| **Critical Count** | Number of critical issues |
| **Major Count** | Number of major issues |
| **Minor Count** | Number of minor issues |
| **Nit Count** | Number of nit issues |
| **Risk Score** | Critical×10 + Major×5 + Minor×2 + Nit×1 |
