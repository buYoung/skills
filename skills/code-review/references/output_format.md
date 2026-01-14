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

| Verdict | Condition |
|---------|-----------|
| **REQUEST_CHANGES** | Any Critical finding exists |
| **REQUEST_CHANGES** | 3+ Major findings exist |
| **COMMENT** | Major findings exist (1-2) |
| **COMMENT** | 5+ Minor findings exist |
| **APPROVE** | Only Minor/Nit findings or none |

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

## Summary Statistics

| Metric | Description |
|--------|-------------|
| **Total Findings** | Sum of all severity counts |
| **Critical Count** | Number of critical issues |
| **Major Count** | Number of major issues |
| **Minor Count** | Number of minor issues |
| **Nit Count** | Number of nit issues |
| **Risk Score** | Critical×10 + Major×5 + Minor×2 + Nit×1 |
