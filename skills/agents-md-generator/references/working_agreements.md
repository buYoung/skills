# Working Agreements Specification

Defines the standard working agreements to be included in generated `AGENTS.md` files.

## Communication Rules

- **Response Language**: Use the language specified by the user. If no preference is given, infer the primary language from the codebase (comments, documentation, commit messages, README) and respond in that language.
- **Technical Terms**: Keep domain-specific terms (software/backend/infra) in English regardless of response language; do not transliterate
- **Code Blocks**: Never modify or translate fenced code blocks

## Task Execution Rules

- **Tests & Lint**: Do not introduce new tests, lint configurations, or formatter setups on your own, even when they seem beneficial. Ask the user before adding any of them; only proceed when the user has explicitly requested it
- **Context Building**: Before editing code, search for other usages of the same function/feature/module; review related flows, shared abstractions, recurring patterns, and likely impact
- **Root Cause Focus**: Solve the underlying cause, not only the visible symptom. Inspect neighboring flows, shared abstractions, and affected callers; choose the narrowest complete change that resolves the root issue in the broader context
- **Clarification**: When user decisions are needed for scope, behavior, or tradeoffs, ask actively instead of guessing

## Code Change Rules

- **Impact Reporting**: Check likely side effects across related flows, behavior boundaries, and public APIs. Report relevant impact, behavior changes, and API compatibility risks to the user
- **Type Check After Changes**: During codebase analysis, identify the project's type-check command from build configs, scripts, or tooling (e.g., `tsc --noEmit` from `tsconfig.json`, `mypy`/`pyright` from `pyproject.toml`, `cargo check` from `Cargo.toml`, `go vet`/`go build` from `go.mod`, `javac` from `pom.xml` or `build.gradle`, `gradle compileKotlin` from `build.gradle.kts`). Include the discovered command in this section. After code modifications, run that command to verify type safety before considering the task complete. If the project's stack has no type checker available, omit this bullet from the generated AGENTS.md rather than inventing a placeholder
- **Monorepo Root Package-Local Verification**: For confirmed monorepo root documents only, state that package-only tests, type-check, or other verification commands belong in the package-level `AGENTS.md`, not the root `AGENTS.md`. Do not include this rule in single-repository documents
- **New Code**: New functions/modules should be small, single-purpose, and colocated near related code
- **Dependencies**: Avoid new external dependencies unless necessary; if added, briefly explain why

## Monorepo Package Format

For AGENTS.md files generated within a package of a monorepo, reference the root document instead of duplicating rules.

```markdown
## 5. Working Agreements

See root `/AGENTS.md` for common working agreements.

Package-local verification: run `<discovered package command>` after changes in this package.
```

Include the package-local verification line only when analysis finds a command that applies to that package specifically. Do not duplicate root working agreements in package documents.

## Canonical Compressed Format for AGENTS.md

Due to the **dynamic character limit** (based on LOC), working agreements in generated AGENTS.md should be compressed. The output below is the canonical current generated rule set, not an optional example. Update mode must rebuild managed `Working Agreements` sections from this rule set, while still adding discovered repository-specific response language and type-check command details when applicable.

Use the correct heading number for the document type:

- Single repo / package document: `## 5. Working Agreements`
- Monorepo root document: `## 3. Working Agreements`

Use the base bullet set for single repositories and monorepo root documents. Add the monorepo-only package-local verification bullet **only** when generating a monorepo root document. Do not include monorepo-specific wording in single-repository `AGENTS.md` files.

### Base Bullet Set (Single Repo and Monorepo Root)

```markdown
- Respond in user's preferred language; if unspecified, infer from codebase (keep tech terms in English, never translate code blocks)
- Ask the user before introducing tests, lint, or formatter setups; add them only on explicit request
- Build context by reviewing related usages, flows, patterns, and likely impact before editing
- Fix the underlying cause, not only the visible symptom; inspect affected flows and apply the narrowest complete change that resolves the root issue
- Check side effects across callers, shared abstractions, and behavior/API boundaries; report relevant impact and compatibility risks
- Ask actively when user decisions are needed for scope, behavior, or tradeoffs
- Run type-check after code changes (include the discovered command, e.g., `tsc --noEmit`, `cargo check`, `go vet`, `javac`, `gradle compileKotlin`); omit this bullet if no type checker is configured
- New functions: single-purpose, colocated with related code
- External dependencies: only when necessary, explain why
```

### Monorepo Root Addition

Add this bullet to the root `AGENTS.md` only when the repository is confirmed as a monorepo with 2+ packages:

```markdown
- Put package-only tests/type-check/verification guidance in the package-level AGENTS.md, not the root document
```
