# AGENTS.md

## 1. Overview

This repository maintains reusable AI agent skills and supporting artifacts for developer-AI collaboration. Each skill package defines one capability through a `SKILL.md` entry point plus optional references, examples, scripts, evaluations, and review artifacts.

## 2. Folder Structure

- `skills/`: Primary skill packages. Add or update capability content here.
    - `<skill-name>/SKILL.md`: Required entry point with YAML frontmatter, activation description, workflow, output contract, references, and scope boundaries.
    - `<skill-name>/references/`: Long-form domain rules, templates, routing tables, prompt bodies, and policy material linked from `SKILL.md`.
    - `<skill-name>/scripts/`: Package-local validators or generators, such as AGENTS parsers, brief validators, or feature-design-doc checks.
    - `<skill-name>/examples/`: Worked artifacts and sample plugin code that demonstrate expected output or implementation shape.
    - `<skill-name>/evals/`: Regression fixtures for skills whose behavior needs repeatable checks.
    - `<skill-name>/updates/`: Dated design notes, adversarial reviews, and patch samples for skills with an explicit revision trail.
- `scripts/release/`: Repository-level release helpers. These update marketplace metadata and generate bilingual changelog entries.
- `.claude-plugin/marketplace.json`: Claude plugin marketplace bundle definitions; each published bundle points at selected `skills/<skill-name>` directories.
- `.github/workflows/`: Release publication workflow that verifies changelog sections and creates draft GitHub releases from tags.
- `README.md`: Public catalog, install instructions, skill status tables, and attribution notes.
- `CHANGELOG.md` and `CHANGELOG.ko.md`: English and Korean release notes maintained by release automation.
- `package.json` and `.release-it.json`: Package metadata, Node engine constraints, and release-it hook configuration.
- `docs/`: Repository-level background material; keep it distinct from per-skill reference files.

## 3. Core Behaviors & Patterns

- **Progressive disclosure**: `SKILL.md` files carry the activation surface, workflow, output contract, and scope limits; detailed rules move to linked `references/` files. Follow the link path from the entry point instead of duplicating long reference text.
- **Frontmatter-driven activation**: Skill discovery depends on `name` and especially `description`. Descriptions usually include the supported capability, trigger phrases, and exclusions such as `Use when`, `Not for`, or explicit-invocation language.
- **Capability-local artifacts**: Reusable templates, validators, eval fixtures, examples, licenses, and review notes live inside the owning skill package. Repository-level scripts are reserved for release workflows that span packages.
- **Structured workflow gates**: Larger skills encode numbered stages, halt conditions, routing tables, and handoff contracts. Preserve those state transitions when editing `task-brief-creator`, `linear-issue-*`, `iterative-self-review`, or `delegated-review-loop`.
- **Structural validation boundary**: Validator scripts check document shape, filenames, section order, checklist format, references, and exit codes. They intentionally avoid judging semantic quality, which remains in the skill workflow or human review.
- **Marketplace release flow**: Published skill grouping flows from `skills/` to `.claude-plugin/marketplace.json`, then through `release-it` hooks. `bump-marketplace.js` updates the marketplace version; `write-changelog.js` asks Codex for English and Korean changelog bodies before tagging.
- **Revision and regression evidence**: Skills with complex behavior keep `evals/`, `examples/`, or `updates/` so changes can be checked against prior outputs. Add new evidence near the owning skill rather than in a shared catch-all folder.

## 4. Conventions

- **Package naming**: Skill directories use `kebab-case`, and the folder name should match the `name` frontmatter value. Keep variants explicit, as in `task-brief-creator-caveman`.
- **Entry point shape**: Every installable skill keeps `SKILL.md` at package root. Start with YAML frontmatter, then use concise Markdown sections for purpose, triggers, workflow, output guidance, reference files, and guardrails.
- **Reference organization**: Use topic-oriented reference filenames and keep established local schemes: `snake_case` for AGENTS specs, hyphenated workflow topics for brief skills, and numbered prefixes for JetBrains reference ordering.
- **Relative links**: Link package-local material with relative paths such as `references/template.md` or `scripts/validate_brief.py`. Do not point to installed absolute paths from repository docs.
- **Template and validator placement**: Put reusable Markdown templates under `references/`, executable structural checks under `scripts/`, and sample outputs under `examples/`. Name validators after the artifact contract they enforce.
- **Script style**: Python helper scripts use standard-library modules, uppercase contract constants, explicit exit codes, and small parsing functions. Node release helpers use CommonJS, `node:` imports, `fail(message)`, and uppercase root/path constants.
- **Catalog consistency**: When a skill is promoted, demoted, renamed, or bundled, keep `README.md`, `.claude-plugin/marketplace.json`, and the package path aligned.
- **Documentation language**: Repository artifacts are English by default unless intentionally localized, such as `CHANGELOG.ko.md`. Keep exact code, paths, command names, and frontmatter keys unchanged.

## 5. Working Agreements

- Respond to the user in Korean unless they explicitly request another language; keep code blocks, file paths, identifiers, and exact logs unchanged.
- Ask the user before introducing tests, lint, formatter setup, or related automation; add them only when explicitly requested.
- Build context by reviewing related skill packages, references, examples, scripts, marketplace entries, and release metadata before editing.
- Fix the underlying cause, not only the visible symptom; choose the narrowest complete documentation or script change that resolves the broader issue.
- Check side effects across public skill contracts, frontmatter names, output formats, documented trigger behavior, and package availability metadata; report compatibility risks.
- Ask for clarification when scope, behavior, or packaging decisions are ambiguous and cannot be resolved from repository context.
- New functions, scripts, or modules should be single-purpose and colocated with the owning skill package or release workflow.
- Avoid new external dependencies unless necessary; explain why any added dependency is required.
- Preserve user-owned custom sections when updating generated `AGENTS.md` files; refresh only the standard managed sections.

## 6. user custom
- skill을 만들때 절대 serena를 활용하지마세요.
