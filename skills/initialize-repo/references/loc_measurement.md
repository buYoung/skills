# LOC Measurement Specification

Defines the method for measuring repository size and determining dynamic character limits for AGENTS.md.

## Measurement Command

```bash
tokei -e "*.json" -e "*.yaml" -e "*.yml" -e "*.md" -e "*.sh" -e "*.lock" -e "*.map" -e "*.svg" .
```

**Priority**: This is the **first step** before generating AGENTS.md.

## Tool Installation

If `tokei` is not installed:

```
tokei가 설치되어 있지 않습니다.
https://github.com/XAMPPRocky/tokei 에서 설치 후 다시 시도하세요.
```

## Character Limit by Repository Scale

| Scale | LOC Range | Character Limit |
|-------|-----------|-----------------|
| 소규모 (Small) | ≤ 10,000 | 10,000자 |
| 중소규모 (Small-Medium) | 10,001 ~ 50,000 | 10,000자 |
| 중규모 (Medium) | 50,001 ~ 100,000 | 10,000자 |
| 중대규모 (Medium-Large) | 100,001 ~ 500,000 | 15,000자 |
| 대규모 (Large) | 500,001 ~ 1,000,000 | 20,000자 |
| 초대규모 (Extra-Large) | > 1,000,000 | 30,000자 |

## Workflow

1. Run `tokei` command to get total LOC
2. If tokei not installed → display installation guide and stop
3. Determine repository scale from LOC value
4. Apply corresponding character limit to AGENTS.md generation

## tokei Output Interpretation

Use the **Total** lines value from tokei output:

```
===============================================================================
 Language            Files        Lines         Code     Comments       Blanks
===============================================================================
 TypeScript            150        45000        38000         3000         4000
 JavaScript             30         5000         4200          400          400
-------------------------------------------------------------------------------
 Total                 180        50000        42200         3400         4400
===============================================================================
```

In this example: Total Lines = 50,000 → 중소규모 → 10,000자 limit
