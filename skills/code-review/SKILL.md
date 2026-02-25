---
name: code-review
description: Performs production-ready code reviews on git changes. Supports commit/range/file-scoped analysis, impact assessment, breaking-change detection, confidence-aware finding classification, and risk-weighted verdict generation.
---

# Code Review Capabilities

Structured capability set for reviewing git changes with evidence-backed findings and risk-aware verdicts.

## Tools

- **Git CLI**: Retrieves commit metadata, diffs, range context, and history graph information
- **Search tools (`rg`, `fd`)**: Traces references, consumer impact, and related tests across repositories

## Domains

- **Change analysis**: Diff interpretation, file classification, and change-scope characterization
- **Impact assessment**: Consumer tracing, publicly exposed contract impact, behavioral regression risk
- **Risk evaluation**: Severity classification, confidence modeling, and verdict generation

## Input Contract

Review targets support three input shapes:

| Target Type | Required Fields | Description |
|-------------|-----------------|-------------|
| **Single Commit** | `commit_hash` | Reviews one commit and its patch-level changes |
| **Commit Range** | `start_hash`, `end_hash` | Reviews a contiguous range where `start_hash` is earliest and `end_hash` is latest |
| **File-Scoped** | target (`commit_hash` or range) + `file_path[]` | Limits analysis to selected files within the target |

## Preconditions

- Repository context is available and readable by git
- Target commit or range can be resolved from repository history
- Diff and metadata can be retrieved for the target
- If analysis preconditions fail (unknown hash, missing parent, ambiguous range), limitations are recorded in the review output

## Core Capabilities

- **Commit and Range Analysis**: Collects metadata, patch details, and structural change information
- **Change Classification**: Categorizes files by role and change type for review prioritization
- **Impact Detection**: Traces direct and indirect consumers to estimate runtime and contract impact
- **Breaking Change Detection**: Identifies incompatible changes on externally consumable contracts
- **Confidence-Aware Findings**: Attaches evidence confidence and verification status to each finding
- **Risk-Weighted Verdicts**: Combines severity, confidence, and critical-domain context to determine outcome

## Output Contract

Review output consists of:

- **Findings**: Each finding includes severity, evidence, impact, confidence, verification status, and remediation suggestion
- **Verdict**: `APPROVE`, `COMMENT`, or `REQUEST_CHANGES` with explicit decision rationale
- **Analysis Limitations**: Unverifiable areas and constraints discovered during review
- **Risk Context**: Critical-domain exposure and weighted risk interpretation

## Supported Analysis Types

- **Commit Range**: Review changes across a start~end commit range (start = earliest, end = latest)
- **Single Commit**: Review changes in a specific commit hash
- **File-Scoped**: Review specific files within a commit or range

## Validation Scenarios

- **Root Commit Review**: Handles commits without parents via root-safe diff retrieval
- **Merge Commit Review**: Preserves first-parent and combined-merge perspectives for consistent interpretation
- **Breaking Change + Consumer Counting**: Uses normalized consumer counting to reduce false positives
- **Dynamic/Reflective Usage**: Reports unverifiable linkage with reduced confidence
- **Behavior Coverage Risk**: Escalates risk when changed behavior lacks relevant test coverage
- **Verdict Reproducibility**: Produces stable verdicts from deterministic weighted risk rules

## Severity Levels

| Level | Scope |
|-------|-------|
| **Critical** | Security exposure, data integrity risk, service availability risk, externally breaking contract changes |
| **Major** | Behavioral defects, reliability degradation, significant performance or observability regressions |
| **Minor** | Maintainability, readability, and medium-term quality concerns |
| **Nit** | Low-impact consistency and polish suggestions |

## Technical References

- **[git_operations.md](references/git_operations.md)**: Git retrieval patterns, range calculation, and fallback handling
- **[change_analysis.md](references/change_analysis.md)**: File classification, noise filtering, and large-change strategy
- **[impact_detection.md](references/impact_detection.md)**: Exposure analysis, consumer counting, and confidence modeling
- **[severity_criteria.md](references/severity_criteria.md)**: Severity boundaries, confidence axis, and escalation conditions
- **[output_format.md](references/output_format.md)**: Finding schema and risk-weighted verdict specification
