# Working Agreements Specification

Defines the standard working agreements to be included in generated `AGENTS.md` files.

## Communication Rules

- **Response Language**: Use the language specified by the user. If no preference is given, infer the primary language from the codebase (comments, documentation, commit messages, README) and respond in that language.
- **Technical Terms**: Keep domain-specific terms (software/backend/infra) in English regardless of response language; do not transliterate
- **Code Blocks**: Never modify or translate fenced code blocks

## Task Execution Rules

- **Tests & Lint**: Do not introduce new tests, lint configurations, or formatter setups on your own, even when they seem beneficial. Ask the user before adding any of them; only proceed when the user has explicitly requested it
- **Context Building**: Before editing code, search for other usages of the same function/feature/module; review related flows, shared abstractions, recurring patterns, and likely impact
- **Simplicity**: Solve the user's underlying request with the smallest focused change that fits the broader context; use discovered side effects to guide scope and implementation, and report relevant impact to the user
- **Clarification**: When user decisions are needed for scope, behavior, or tradeoffs, ask actively instead of guessing

## Code Change Rules

- **Minimal Changes**: Prefer minimal, focused changes; avoid large refactors unless requested
- **Type Check After Changes**: During codebase analysis, identify the project's type-check command from build configs, scripts, or tooling (e.g., `tsc --noEmit` from `tsconfig.json`, `mypy`/`pyright` from `pyproject.toml`, `cargo check` from `Cargo.toml`, `go vet`/`go build` from `go.mod`, `javac` from `pom.xml` or `build.gradle`, `gradle compileKotlin` from `build.gradle.kts`). Include the discovered command in this section. After code modifications, run that command to verify type safety before considering the task complete. If the project's stack has no type checker available, omit this bullet from the generated AGENTS.md rather than inventing a placeholder
- **Public APIs**: Preserve public APIs and behavior unless user asks to change them; call out any behavior changes
- **New Code**: New functions/modules should be small, single-purpose, and colocated near related code
- **Dependencies**: Avoid new external dependencies unless necessary; if added, briefly explain why

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

- Respond in user's preferred language; if unspecified, infer from codebase (keep tech terms in English, never translate code blocks)
- Ask the user before introducing tests, lint, or formatter setups; add them only on explicit request
- Build context by reviewing related usages, flows, patterns, and likely impact before editing
- Solve the user's underlying request with the smallest focused change; use side-effect findings to guide scope/implementation and report relevant impact
- Ask actively when user decisions are needed for scope, behavior, or tradeoffs
- Minimal changes; preserve public APIs
- Run type-check after code changes (include the discovered command, e.g., `tsc --noEmit`, `cargo check`, `go vet`, `javac`, `gradle compileKotlin`); omit this bullet if no type checker is configured
- New functions: single-purpose, colocated with related code
- External dependencies: only when necessary, explain why
```
