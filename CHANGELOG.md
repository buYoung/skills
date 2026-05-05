# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.0] - 2026-05-05

### Added

- Added the `grill-me` skill for `task-brief-creator`.
- Added the `task-brief-creator-caveman` skill.

### Removed

- Removed an unusable skill from the catalog.

### Internal

- Updated release automation to include the Claude plugin version.
- Cleaned up miscellaneous project maintenance.

## [1.1.0] - 2026-05-01

### Added

- Added `agents-md-generator` helper scripts `loc_to_limit.py`, `detect_monorepo.py`, and `parse_sections.py` for character budgets, monorepo detection, and update-mode section parsing.

### Improved

- Improved `task-brief-creator` with type-conditional sections (Reproduction, Baseline Measurement, Behavior Contract) for fix, perf, and refactor briefs.
- Improved `task-brief-creator` validation to check type-conditional section bodies and verify Entry Points paths point at real files.
- Improved `task-brief-creator` Stage 3 codebase review to allow Serena, ast-grep, and short-lived subagents instead of inline tools only.
- Improved `task-brief-creator` examples with a "Picked Up Cold — Coding Agent's First Actions" block and clarified that saved briefs are work instructions.
- Improved `agents-md-generator` with a 6-step Execution Workflow and a "Single-Context Execution (No Subagents)" scope boundary.
- Improved `agents-md-generator` monorepo detection by adding moonrepo and Buck2 markers.
- Improved `agents-md-generator` to prefer Serena MCP symbol tools for read-only exploration, with rg, grep, and find as fallback.
- Improved `agents-md-generator` working agreements so tests and lint guidance only appears when the user asks for it.

## [1.0.0] - 2026-04-30

### Initialize

- `agents-md-generator`: Use when creating or updating `AGENTS.md` from repository structure.
- `task-brief-creator`: Use when turning rough implementation notes into scoped work briefs.
- `code-review`: Use when reviewing commits, ranges, or files from a production code perspective.
- `code-security-audit`: Use when checking a codebase for OWASP-aligned security risks.
- `kysely-converter`: Use when converting raw SQL into type-safe Kysely code.
- `react-vite-guide`: Use when designing, implementing, or improving React 19 and Vite screens.
- `ui-guide`: Use when documenting UI style rules from the actual codebase.
- `ux-design-guide`: Use when reviewing usability, accessibility, and layout issues in an existing UI.
- `doc-coauthoring`: Use when drafting docs, proposals, technical specs, or decision records.
- `typst-creator`: Use when creating Typst documents, reports, papers, or slide content.
- `system-prompt-creator`: Use when designing production-ready system prompts from requirements.
- `release-it`: Use when configuring `release-it`, release workflows, or changelog generation.
- `jetbrains-vmoptions`: Use when tuning JetBrains IDE VM options and memory settings by version.
- `jetbrains-plugin-development`: Use when designing or implementing IntelliJ Platform plugins.
- `biz-opportunity-scout`: Use when evaluating markets, unit economics, and competitive positioning.
- `veo-prompt-director`: Use when structuring Google Veo video generation prompts.
- `linear-issue-creator`: Use when creating structured Linear main issues and sub-issues. - private only
- `linear-issue-worker`: Use when implementing work from Linear sub-issues. - private only
- `linear-issue-reviewer`: Use when reviewing completed Linear sub-issues against done criteria. - private only
