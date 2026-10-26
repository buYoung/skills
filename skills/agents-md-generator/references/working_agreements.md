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
- **Speculative Complexity**: Do not widen scope for theoretical robustness. Adding complexity for a speculative race or security case needs the user's agreement after the concrete failure mode, likelihood, and cost are explained. Do not add parameters, options, flags, or compatibility layers that no current caller or consumer needs

## Code Change Rules

- **Impact Reporting**: Check likely side effects across related flows, behavior boundaries, and public APIs. Report relevant impact, behavior changes, and API compatibility risks to the user
- **Type Check After Changes**: During codebase analysis, identify the project's type-check command from build configs, scripts, or tooling (e.g., `tsc --noEmit` from `tsconfig.json`, `mypy`/`pyright` from `pyproject.toml`, `cargo check` from `Cargo.toml`, `go vet`/`go build` from `go.mod`, `javac` from `pom.xml` or `build.gradle`, `gradle compileKotlin` from `build.gradle.kts`). Include the discovered command in this section. After code modifications, run that command to verify type safety before considering the task complete. If the project's stack has no type checker available, omit this bullet from the generated AGENTS.md rather than inventing a placeholder. Whether this bullet appears does not decide whether the type rules appear; see **Type Rules** below
- **Monorepo Root Package-Local Verification**: For confirmed monorepo root documents only, state that package-only tests, type-check, or other verification commands belong in the package-level `AGENTS.md`, not the root `AGENTS.md`. Do not include this rule in single-repository documents
- **New Code**: Create a new function only under the extraction conditions in the canonical set; give each new function or module one purpose and colocate it with related code
- **Dependencies**: Avoid new external dependencies unless necessary; if added, briefly explain why

## Code Shape Rules

The canonical bullet set below is the source of the generated wording. These labels summarize what each rule covers.

- **Scope of Code Rules**: Code-shape rules apply to code the agent adds and to existing code the task requires it to change, not to other code. A documented or tool-enforced repository convention wins unless it weakens type checking
- **Functions, Variables, and Conditionals**: Extract a function only for reuse, a complex boundary, or a named concept; inline single-use variables unless the name or evaluation timing matters; use at most one level of conditional expression
- **Abstractions and Values**: No single-implementation interfaces, base classes, or single-caller factories without a current need; access values through their owner unless unpacking is needed or idiomatic
- **Validation, Errors, and Cleanup**: Trust guaranteed values and check the shape of outside data where it enters the system; propagate errors instead of hiding them behind undefined defaults; remove what the change leaves unused, and leave unrelated dead code alone
- **Type Rules**: Do not weaken type checking, and write explicit types only where needed. Include these two bullets when a confirmed type checker applies to code the document governs. For a monorepo root, this includes a type checker confirmed in any package, because package documents inherit the root agreements. Omit both only when no governed code has a type checker
- **Comments**: Comment non-obvious constraints and their reasons; do not comment obvious code or describe change history

## Monorepo Package Format

For a package of a monorepo, first check whether the repository-root `AGENTS.md` exists. When it exists, reference it instead of duplicating rules. The example below uses root notation; in the actual output, replace that notation with the real path relative to the package (for example `../../AGENTS.md` for `packages/api/AGENTS.md`).

```markdown
## 5. Working Agreements

See root `/AGENTS.md` for common working agreements.

Package-local verification: run `<discovered package command>` after changes in this package.
```

Include the package-local verification line only when analysis finds a command that applies to that package specifically. Do not duplicate root working agreements when the root document exists.

When the root document is absent, omit the root reference and include the common base bullet set below directly in `## 5. Working Agreements`, applying the package's discovered response language and verification command. Do not include the Monorepo Root Addition and do not create a root file for a Single Package request. Recheck existence during later updates; once a root document exists, switch the managed section to inheritance through the ordinary replacement and dropped-wording report, preserving custom sections.

## Canonical Compressed Format for AGENTS.md

Due to the **dynamic character limit** (based on LOC), working agreements in generated AGENTS.md should be compressed. The output below is the canonical current generated rule set, not an optional example. Update mode must rebuild managed `Working Agreements` sections from this rule set, while still adding discovered repository-specific response language and type-check command details when applicable.

Use the correct heading number for the document type:

- Single repo / package document: `## 5. Working Agreements`
- Monorepo root document: `## 3. Working Agreements`

Use the base bullet set for single repositories, monorepo root documents, and packages whose root document is absent. Add the monorepo-only package-local verification bullet **only** when generating a monorepo root document. Do not include monorepo-specific wording in single-repository `AGENTS.md` files.

Apply [plain_language.md](plain_language.md) to the generated wording. Keep every applicable rule, condition, and obligation; the writing review does not introduce new agreements. Replace the type-check placeholder with the confirmed command, or omit that bullet when no type checker is configured for the document's own verification. Include or omit the two type bullets (`Do not weaken type checking...` and `Rely on type inference...`) by the **Type Rules** condition above, separately from the type-check bullet. Keep every other bullet in every document. Do not emit the placeholder or discovery instructions in the generated document.

### Base Bullet Set (Single Repo and Monorepo Root)

```markdown
- Respond in the user's preferred language. If none is specified, infer it from the codebase. Keep technical terms in English and never translate code blocks.
- Ask the user before introducing tests, lint, or formatter setups. Add them only on explicit request.
- Before editing, review related usages, flows, patterns, and likely impact.
- Fix the underlying cause, not only the visible symptom. Inspect affected flows and apply the narrowest complete change that resolves the root issue.
- Check side effects across callers, shared abstractions, and behavior/API boundaries. Report relevant impact and compatibility risks.
- Ask the user when decisions are needed for scope, behavior, or tradeoffs.
- Do not silently expand scope for theoretical robustness. Before adding complexity for a speculative or vanishingly unlikely race or security edge case, explain the concrete failure mode, likelihood, and complexity cost, and get the user's agreement. Fixing a confirmed root cause across affected callers is not theoretical robustness.
- Do not add parameters, configuration options, feature flags, or compatibility layers that no current caller or consumer needs.
- Add external dependencies only when necessary. Explain why each added dependency is needed.
- After code changes, run `<discovered type-check command>` to verify type safety.
- Apply the rules on function extraction, inlining, conditional expressions, abstractions, options, unpacking, validation, errors, types, and comments to code you add and to existing code the task requires you to change. Do not rewrite other code to fit them unless the user asks. If a documented or tool-enforced repository convention differs from them, follow it unless it weakens type checking.
- Extract code into a new function only when more than one place calls it, it hides a genuinely complex boundary, or it is a real concept or composable step whose name makes the caller clearer. Otherwise, keep the logic inline. Reuse an existing function that does the same job. Give each new function one purpose and place it beside related code.
- Inline a local variable used only once, unless its name explains something the expression does not, or inlining would change when or how often the expression runs or how long its result lives.
- Use at most one level of conditional expression, such as `a ? b : c` or `b if a else c`. For more branches, use `if` statements, early returns, or a lookup table.
- Do not add an interface or base class with only one implementation, or a factory with only one caller, unless a framework, a public contract, a dependency rule the language or repository enforces, an existing or requested test, or another current need requires it.
- Access values through their owner, as in `order.total`, unless correct behavior needs unpacking, the language idiom expects it, or the owner adds no meaning.
- Do not revalidate values that a schema, constructor, or internal type already guarantees. When code reads outside data, such as requests, files, environment variables, or deserialized data, check its shape where it enters the system before other code relies on it.
- Let an error propagate unless the code at that point can handle it or an established boundary converts it. If you add context, keep the error type or cause that callers check. Do not hide a failure behind a default that the function's contract does not define, even if you log it.
- Remove imports and non-public code your change leaves unused, plus debug output you added. Leave unrelated dead code alone.
- Do not weaken type checking to make code pass. Avoid escape-hatch types, unchecked casts, and checker suppressions; fix the type instead. If one is unavoidable, keep it at the narrowest point and comment why.
- Rely on type inference. Write explicit types only where the language requires them, an exported API needs them, omitting them weakens type checking, or they clarify the code.
- Comment non-obvious constraints, surprising behavior, and their reasons. Do not comment obvious assignments or control flow, or describe change history in comments.
```

### Monorepo Root Addition

Add this bullet to the root `AGENTS.md` only when the repository is confirmed as a monorepo with 2+ packages:

```markdown
- Put package-only test, type-check, and verification guidance in the package-level `AGENTS.md`. Keep that guidance out of the root document.
```
