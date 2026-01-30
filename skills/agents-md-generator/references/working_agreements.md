# Working Agreements Specification

Defines the standard working agreements to be included in generated `AGENTS.md` files.

## Communication Rules

| Rule | Description |
|------|-------------|
| Response Language | Korean by default; English only if user explicitly requests |
| Technical Terms | Keep domain-specific terms (software/backend/infra) in English, no Korean transliteration |
| Code Blocks | Never modify or translate fenced code blocks |

## Task Execution Rules

| Rule | Description |
|------|-------------|
| Tests & Lint | Do not create tests or add lint/format tasks unless user explicitly mentions ("test code", "unit test", "jest", "vitest", "lint", "eslint", "prettier", "code format") |
| Context Building | Before editing code, search for other usages of the same function/feature/module; review related flows, shared abstractions, recurring patterns |
| Simplicity | Prefer simple solutions matching user's request; do not add extra features or abstraction unless requested |
| Clarification | If requirements are ambiguous, ask the user instead of guessing |

## Code Change Rules

| Rule | Description |
|------|-------------|
| Minimal Changes | Prefer minimal, focused changes; avoid large refactors unless requested |
| Public APIs | Preserve public APIs and behavior unless user asks to change them; call out any behavior changes |
| New Code | New functions/modules should be small, single-purpose, and colocated near related code |
| Dependencies | Avoid new external dependencies unless necessary; if added, briefly explain why |

## Monorepo Package Format

For AGENTS.md files generated within a package of a monorepo, reference the root document instead of duplicating rules.

```markdown
## 5. Working Agreements

See root `/AGENTS.md` for common working agreements.
```

## Compressed Format for AGENTS.md

Due to the **dynamic character limit** (based on LOC), working agreements in generated AGENTS.md should be compressed. Example format:

```markdown
## 5. Working Agreements

- Respond in Korean (keep tech terms in English, never translate code blocks)
- Create tests/lint only when explicitly requested
- Build context by reviewing related usages and patterns before editing
- Prefer simple solutions; avoid unnecessary abstraction
- Ask for clarification when requirements are ambiguous
- Minimal changes; preserve public APIs
- New functions: single-purpose, colocated with related code
- External dependencies: only when necessary, explain why
```

