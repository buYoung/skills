# Output Format

Structure and formatting for code review reports.

## Review Report Structure

```
## Review Summary
- **Target**: <commit_hash | start_hash~end_hash | staged changes>
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

## Analysis Limitations
- <unverifiable area or analysis constraint>

## Highlights
- <notable positive practice, if any>

## Decision Rationale
- <why this verdict was selected>

## Verdict
<APPROVE | REQUEST_CHANGES | COMMENT>
```

## Finding Entry Format

```
#### [<severity>] <title>
- **File**: `<file_path>:<line_number>`
- **Issue**: <description>
- **Evidence**: <specific code/path/behavioral evidence>
- **Impact**: <user/service/data/operational impact>
- **Confidence**: <High | Medium | Low>
- **Suggestion**: <at least one remediation direction>
```

### Example Entry
```
#### [Major] Incompatible output contract for downstream consumer
- **File**: `service/account/response_mapper.ext:118`
- **Issue**: Response field `accountStatus` was renamed to `status` without compatibility mapping
- **Evidence**: Consumer adapters still reference `accountStatus` in runtime parsing logic
- **Impact**: Downstream consumers may fail to parse responses, causing request failures
- **Confidence**: High
- **Suggestion**: Add compatibility mapping or versioned response contract before removing old field
```

## Verdict Criteria

Verdict selection combines count-based baseline rules and risk-weighted adjustments.

### Baseline Rules

| Verdict | Condition |
|---------|-----------|
| **REQUEST_CHANGES** | Any Critical finding exists |
| **REQUEST_CHANGES** | 3+ Major findings exist |
| **COMMENT** | Major findings exist (1–2) |
| **COMMENT** | 5+ Minor findings exist |
| **APPROVE** | Only Minor/Nit findings or none |

### Risk-Aware Verdict Adjustments

Use the weighted risk score internally to validate the baseline verdict. Do not output the score.

| Condition | Adjustment |
|-----------|------------|
| Any verified Critical finding | REQUEST_CHANGES |
| High weighted risk with medium+ confidence evidence | REQUEST_CHANGES |
| Moderate weighted risk | COMMENT (unless baseline already requests changes) |
| Low weighted risk and no Major+ findings | APPROVE candidate |

## Grouping Options

### By Severity (Default)
Findings are grouped under severity headers.

### By File
```
## path/to/file.ext
- [Major] Contract incompatibility (L118)
- [Minor] Error context is underspecified (L44)
```
