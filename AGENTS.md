# AGENTS.md

## 1. Overview

This repository maintains reusable AI agent skills and supporting artifacts for developer-AI collaboration tasks. Each skill package defines a focused capability through `SKILL.md`, optional references, examples, scripts, and evaluation fixtures.

## 2. Folder Structure

- `skills/`: Primary skill packages; add or update capability work here.
    - `<skill-name>/SKILL.md`: Skill entry point with YAML frontmatter (`name`, `description`, optional metadata) followed by workflow, scope, and output guidance.
    - `<skill-name>/references/`: Detailed domain rules and specifications linked from `SKILL.md`; keep long or specialized material here instead of overloading the entry point.
    - `<skill-name>/examples/`: Sample artifacts and walkthroughs that demonstrate expected outputs or interaction patterns.
    - `<skill-name>/scripts/`: Small helper validators or generators that belong to one skill package.
    - `<skill-name>/evals/`: Evaluation fixtures for skills that need repeatable review or regression checks.
    - `agents-md-generator/updates/`: Dated review notes, benchmark records, and patch samples for generator revisions.
- `scripts/release/`: Release automation helpers for marketplace version bumps and changelog generation.
- `.claude-plugin/marketplace.json`: Claude plugin marketplace metadata grouping selected skills into installable plugin bundles.
- `.github/workflows/`: Repository automation for release and publication flows.
- `README.md`: Public skill catalog, installation options, usage examples, and attribution notes.
- `CHANGELOG.md` and `CHANGELOG.ko.md`: English and Korean release notes maintained by the release workflow.
- `package.json` and `.release-it.json`: Package metadata and release-it configuration for repository releases.

## 3. Core Behaviors & Patterns

- **Progressive disclosure**: `SKILL.md` introduces the skill, trigger conditions, workflow, and scope boundaries; detailed syntax, templates, policies, and process rules move into `references/` and are linked from the entry point.
- **Capability-first packaging**: Each directory under `skills/` is treated as an independent skill package. Keep package-specific references, examples, scripts, licenses, and notices inside that package unless the content is repository-wide.
- **Frontmatter-driven discovery**: Every skill starts with YAML frontmatter containing at least `name` and `description`. Descriptions are the primary activation surface, so they should state the supported capability and relevant trigger conditions directly.
- **Artifact-backed guidance**: Complex skills pair prose instructions with reusable artifacts such as templates, validators, examples, eval fixtures, or review notes. Prefer updating those supporting artifacts over duplicating long instructions in chat-oriented sections.
- **Release metadata flow**: Skill availability in Claude plugin bundles is controlled through `.claude-plugin/marketplace.json`; release scripts update marketplace metadata and changelogs as part of the release-it hook flow.
- **Revision trail for generators**: Generator-like skills keep dated review artifacts and patch samples under `updates/` so behavior changes can be compared against prior outputs.

## 4. Conventions

- **Skill directories**: Use `kebab-case` for package folders (for example, `code-security-audit`, `task-brief-creator-caveman`). Keep the folder name aligned with the `name` frontmatter value.
- **Reference filenames**: Use topic-oriented `snake_case` Markdown filenames in `references/` (for example, `working_agreements.md`, `stage-4-interview.md`). Existing domain-specific hyphenated names may remain when already established.
- **Entry point shape**: Keep `SKILL.md` as the required entry point. Start with YAML frontmatter, then use short Markdown sections for purpose, triggers, workflow, output contract, and scope boundaries.
- **Reference linking**: Link deeper material from `SKILL.md` with relative Markdown links. Do not copy the same long reference text into multiple skill files.
- **Examples and validators**: Place reusable examples under `examples/` and executable validators under `scripts/` inside the owning skill package. Name validator scripts by the artifact they validate, such as `validate_brief.py`.
- **Release scripts**: Node release helpers in `scripts/release/` use CommonJS, `node:` imports, explicit `fail(message)` exits, and uppercase constants for repository-level paths.
- **Documentation language**: Repository artifacts are written in English unless a file is intentionally localized, such as `CHANGELOG.ko.md`. Live user-facing responses follow the user's language preference.

## 5. Working Agreements

- Respond to the user in Korean unless they explicitly request another language; keep code blocks, file paths, identifiers, and exact logs unchanged.
- Ask the user before introducing tests, lint, formatter setup, or related automation; add them only when explicitly requested.
- Build context before editing by reviewing related skill packages, references, examples, scripts, and marketplace entries that may be affected.
- Prefer the narrowest complete documentation or script change that satisfies the request; avoid unrelated rewrites and large restructuring.
- Preserve existing public skill contracts, frontmatter names, output formats, and documented trigger behavior unless the user asks to change them.
- Ask for clarification when scope, behavior, or packaging decisions are ambiguous and cannot be resolved from repository context.
- New functions, scripts, or modules should be single-purpose and colocated with the owning skill package or release workflow.
- Avoid new external dependencies unless necessary; if one is added, explain why it is required.
- Preserve user-owned custom sections when updating generated `AGENTS.md` files; refresh only the standard managed sections.

## 6. user custom
- skill을 만들때 절대 serena를 활용하지마세요.
