---
name: code-review
description: Performs comprehensive code reviews on git commits. Analyzes commit changes, investigates side effects in the codebase, and categorizes findings by severity levels (critical, major, minor, nit).
---

# Code Review Capabilities

Structured code review tooling for git commit analysis and feedback generation.

## Tools

- **Git CLI**: Retrieves commit metadata, diffs, and file change information
- **Search tools (rg, fd)**: Traces function/class usage across the codebase for impact detection

## Domains

- **Code analysis**: Primary domain - commit diff interpretation and code inspection
- **Git operations**: Commit metadata retrieval, diff operations, range analysis
- **Impact assessment**: Dependency tracing, test coverage verification

## Core Capabilities

- **Git Commit Analysis**: Retrieves commit metadata, messages, and diffs from git hash
- **Change Classification**: Categorizes modified files by type (source, test, config, new, modified, deleted)
- **Side Effect Detection**: Traces function/class usage across the codebase to identify potential impacts
- **Breaking Change Detection**: Identifies public API signature changes that affect existing consumers
- **Severity Classification**: Categorizes review findings into four severity levels (Critical, Major, Minor, Nit)
- **Verdict Generation**: Produces structured review verdicts (APPROVE, REQUEST_CHANGES, COMMENT)

## Supported Analysis Types

- **Commit Range**: Review changes across a start~end commit range (start = earliest, end = latest)
- **Single Commit**: Review changes in a specific commit hash
- **File-Scoped**: Review specific files within a commit

## Severity Levels

| Level | Scope |
|-------|-------|
| **Critical** | Security vulnerabilities, data loss risks, service outage potential, breaking API changes |
| **Major** | Bugs, performance issues, incorrect logic, logging/config issues |
| **Minor** | Code quality, readability, duplication |
| **Nit** | Style, naming conventions, comment improvements |

## Technical References

- **[git_operations.md](references/git_operations.md)**: Git commands for retrieving commit information and diffs
- **[change_analysis.md](references/change_analysis.md)**: File categorization and diff interpretation methods
- **[impact_detection.md](references/impact_detection.md)**: Side effect tracing and dependency analysis techniques
- **[severity_criteria.md](references/severity_criteria.md)**: Classification criteria for each severity level
- **[output_format.md](references/output_format.md)**: Review result structure and formatting specification
