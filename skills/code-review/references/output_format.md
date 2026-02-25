# Output Format

Structure and formatting specification for production-ready code review results.

## Review Report Structure

```
## Review Summary
- **Target**: <commit_hash | start_hash~end_hash>
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

## Risk Context
- **Critical Domains Affected**: <none | list>
- **Weighted Risk Score**: <numeric_score>

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
- **Confidence**: <0.0-1.0>
- **Verification Status**: <Verified | Partially Verified | Unverifiable>
- **Suggestion**: <at least one remediation direction>
```

### Example Entry
```
#### [Major] Incompatible output contract for downstream consumer
- **File**: `service/account/response_mapper.ext:118`
- **Issue**: Response field `accountStatus` was renamed to `status` without compatibility mapping
- **Evidence**: Consumer adapters still reference `accountStatus` in runtime parsing logic
- **Impact**: Downstream consumers may fail to parse responses, causing request failures
- **Confidence**: 0.86
- **Verification Status**: Verified
- **Suggestion**: Add compatibility mapping or versioned response contract before removing old field
```

## Verdict Criteria

Verdict selection combines count-based baseline rules and risk-weighted adjustments.

### Baseline Rules (Count-Based)

| Verdict | Condition |
|---------|-----------|
| **REQUEST_CHANGES** | Any Critical finding exists |
| **REQUEST_CHANGES** | 3+ Major findings exist |
| **COMMENT** | Major findings exist (1-2) |
| **COMMENT** | 5+ Minor findings exist |
| **APPROVE** | Only Minor/Nit findings or none |

### Weighted Risk Model

- **Severity Weights**: Critical=10, Major=5, Minor=2, Nit=1
- **Confidence Factor**: High=1.0, Medium=0.7, Low=0.4
- **Critical Domain Bonus**: +4 per finding impacting authentication/authorization, payment/billing, data integrity/migration, or availability/reliability

`Weighted Risk Score = Sum((Severity Weight * Confidence Factor) + Critical Domain Bonus)`

### Risk-Aware Verdict Adjustments

| Condition | Adjustment |
|-----------|------------|
| Any Verified Critical finding | REQUEST_CHANGES |
| Weighted Risk Score >= 12 with medium-or-higher confidence evidence | REQUEST_CHANGES |
| Weighted Risk Score 6-11 | COMMENT (unless baseline already requests changes) |
| Weighted Risk Score <= 5 and no Major+ findings | APPROVE candidate |

### Confidence-Aware Handling

| Evidence Shape | Handling |
|----------------|----------|
| High confidence + high impact | Keep or escalate severity as reported |
| Medium confidence + medium/high impact | Keep severity, include verification note |
| Low confidence finding | Avoid automatic escalation; request manual verification in rationale |

## Grouping Options

### By Severity (Default)
Findings are grouped under severity headers.

### By File
```
## path/to/file.ext
- [Major] Contract incompatibility (L118)
- [Minor] Error context is underspecified (L44)
```

## Positive Feedback

Include a `Highlights` section when clearly justified by the patch quality.

```
## Highlights
- <description of a notable positive practice>
```

## Summary Statistics

| Metric | Description |
|--------|-------------|
| **Total Findings** | Sum of all severity counts |
| **Critical Count** | Number of critical issues |
| **Major Count** | Number of major issues |
| **Minor Count** | Number of minor issues |
| **Nit Count** | Number of nit issues |
| **Weighted Risk Score** | Risk-weighted score using severity and confidence factors |
| **Unverifiable Count** | Number of findings marked as `Unverifiable` |
