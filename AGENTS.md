# AGENTS.md

## 1. Overview

This repository maintains reusable AI agent skills and the package-local artifacts that make those skills portable across agent runtimes. Each skill is a self-contained capability with a `SKILL.md` entry point plus optional references, scripts, examples, evaluations, and revision notes.

## 2. Folder Structure

- `skills/`: Primary skill packages. Add capability content here unless the change is repository-level release or catalog work.
    - `<skill-name>/SKILL.md`: Required entry point with YAML frontmatter, activation description, workflow, output contract, references, and guardrails.
    - `<skill-name>/references/`: Detailed domain rules, templates, routing tables, prompt bodies, and policy material linked from `SKILL.md`.
    - `<skill-name>/scripts/`: Package-local deterministic helpers such as AGENTS parsers, brief validators, and Feature Design Doc validators.
    - `<skill-name>/examples/`: Worked sample artifacts or plugin examples that demonstrate expected output shape.
    - `<skill-name>/evals/`: Regression fixtures for skills that need repeatable behavior checks.
    - `<skill-name>/updates/`: Dated design notes, review records, and patch evidence for skills with explicit revision history.
    - `system-prompt-creator-workspace/`, `task-brief-creator-old/`, and similar workspace or legacy directories: preserve as supporting material unless the task explicitly targets them.
- `scripts/release/`: Repository-level release automation. `bump-marketplace.js` updates `.claude-plugin/marketplace.json`; `write-changelog.js` asks Codex for English and Korean changelog bodies.
- `.claude-plugin/marketplace.json`: Claude plugin marketplace bundles. Published bundles point at selected `skills/<skill-name>` directories and must stay aligned with README availability tables.
- `.github/workflows/`: Tag-triggered release publication. The workflow verifies both changelog files contain the tagged version before creating a draft GitHub release.
- `docs/`: Repository-level guidance, planning briefs, and snapshots. Keep this separate from per-skill `references/` unless a skill explicitly owns the material.
- `README.md`: Public catalog, install guidance, skill status tables, and attribution links.
- `CHANGELOG.md` and `CHANGELOG.ko.md`: Release notes maintained by release automation; keep both languages in sync.
- `package.json` and `.release-it.json`: Package metadata, Node engine constraints, and release-it hook wiring.
- `.agent/`, `.windsurf/`, and `.agents/`: Agent-runtime mirrors or orchestration run artifacts. Treat them as runtime/support surfaces, not the canonical source for published skill packages.

## 3. Core Behaviors & Patterns

- **Progressive disclosure**: `SKILL.md` files act as routers and contracts; long domain knowledge moves into package-local `references/`. Read the entry point first, then only the referenced files that match the current task.
- **Frontmatter-driven activation**: Skill discovery is controlled by `name` and especially `description`. Descriptions include capability, trigger language, and exclusions such as `Use when`, `Not for`, or explicit-invocation boundaries.
- **Capability-local ownership**: Templates, validators, examples, eval fixtures, licenses, and update notes live under the owning skill package. Repository-level scripts are reserved for release flows that span packages.
- **Structured workflow gates**: Complex skills encode numbered stages, halt conditions, routing tables, output contracts, and handoff rules. Preserve these transitions in `task-brief-creator`, `linear-issue-*`, `feature-design-doc`, `iterative-self-review`, `delegated-review-loop`, and `orchestration`.
- **Validation is structural by design**: Python validators use constants, regex contracts, explicit exit codes, and report objects to check shape, ordering, filenames, checklists, frontmatter, and references. They do not judge semantic quality; that stays in the skill workflow or human review.
- **Release chain is metadata-first**: Published grouping flows from `skills/` to README tables and `.claude-plugin/marketplace.json`, then through `release-it` hooks and the tag workflow. A promoted, demoted, renamed, or bundled skill needs all of those surfaces checked together.
- **Evidence stays near the skill**: Complex behavior changes should add or update evidence in `examples/`, `evals/`, `updates/`, or package-local scripts rather than creating a shared catch-all evidence area.
- **Runtime mirrors are secondary**: `.agent/`, `.windsurf/`, `.agents/`, and `docs/skills-main/` can provide context, but the canonical editable skill packages are under `skills/` unless the task names another surface.

## 4. Conventions

- **Skill package naming**: Skill directories use `kebab-case`, and the folder name should match the `name` frontmatter value. Variants keep the base name visible, as in `task-brief-creator-caveman`.
- **Frontmatter shape**: Every installable `SKILL.md` starts with YAML frontmatter. Keep `name` lowercase kebab-case, make `description` the activation surface, and add `license` when the package carries license material.
- **Entry point structure**: Keep `SKILL.md` concise and navigational. Use sections such as trigger, workflow, output contract, references, helper scripts, and scope boundaries instead of embedding all detailed rules inline.
- **Reference filenames**: Use topic-oriented names and follow local schemes: `snake_case` for AGENTS generator specs, hyphenated workflow topics for brief skills, and numbered prefixes for JetBrains reference ordering.
- **Relative package links**: Link package-local material with relative paths such as `references/template.md` or `scripts/validate_brief.py`. Do not point repository docs at installed absolute paths.
- **Template and validator placement**: Reusable Markdown templates belong in `references/`, structural checks in `scripts/`, sample outputs in `examples/`, and regression data in `evals/`.
- **Python script style**: Use standard-library modules, uppercase contract constants, compiled regexes, explicit exit codes, small parsing/validation functions, and report objects for user-facing output.
- **Node release script style**: Use CommonJS with `node:` imports, uppercase root/path constants, `fail(message)` helpers, explicit argument validation, and targeted file writes.
- **Catalog consistency**: When a skill is promoted, demoted, renamed, bundled, or made private, update README tables, marketplace bundles, changelog intent, and package paths together.
- **Documentation language**: Repository artifacts are English by default unless intentionally localized, such as `CHANGELOG.ko.md`; keep exact code, paths, command names, and frontmatter keys unchanged.

## 5. Working Agreements

- Respond to the user in Korean unless they explicitly request another language; keep code blocks, file paths, identifiers, and exact logs unchanged.
- Ask the user before introducing tests, lint, formatter setup, or related automation; add them only on explicit request.
- Build context by reviewing related skill packages, references, examples, scripts, marketplace entries, and release metadata before editing.
- Fix the underlying cause, not only the visible symptom; inspect related contracts and apply the narrowest complete documentation or script change.
- Check side effects across public skill contracts, frontmatter names, output formats, trigger behavior, bundle availability, and release metadata; report relevant compatibility risks.
- Ask actively when user decisions are needed for scope, behavior, packaging, or tradeoffs.
- New functions, scripts, or modules should be single-purpose and colocated with the owning skill package or release workflow.
- Avoid new external dependencies unless necessary; explain why any added dependency is required.
- Preserve user-owned custom sections when updating generated `AGENTS.md` files; refresh only the standard managed sections.

## 6. user custom
- skill을 만들때 절대 serena를 활용하지마세요.
- @fable5.md 를 참고해.
