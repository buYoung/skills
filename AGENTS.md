# AGENTS.md

## 1. Overview

This repository maintains portable AI agent skill packages and the release/catalog metadata that makes those packages installable across agent runtimes. Each skill owns its own activation contract, domain references, examples, validators, and revision evidence.

## 2. Ownership Map

### Stable Ownership Boundaries

- **Skill package contract**: Start in `skills/<skill-name>/SKILL.md` when changing a skill's trigger, workflow, output contract, or guardrails. It owns the public activation surface consumed by README catalog entries and marketplace bundles, and must preserve package-local routing into `references/`, `scripts/`, `examples/`, `evals/`, or `updates/`; verify by checking the skill entry point plus any linked package-local artifacts.
- **Reference and artifact boundary**: Start in the owning package's `references/`, `examples/`, `evals/`, or `updates/` when changing detailed domain rules, sample outputs, regression material, or design notes. These files extend the owning `SKILL.md` without becoming shared repository policy; verify that relative links from the entry point still resolve and that examples/evals still match the documented output shape.
- **Structural validator boundary**: Start in the owning package's `scripts/` directory when changing machine-checkable document shape. Validators use standard-library Python with constants, regex contracts, explicit exit codes, and `Report` objects, and they must remain structural checks rather than semantic judges; verify through the script's own usage contract and representative fixture or target document.
- **Release and marketplace boundary**: Start in `scripts/release/`, `.release-it.json`, `.claude-plugin/marketplace.json`, README availability tables, and both changelogs when changing published bundle membership, package versioning, or release notes. These files form one metadata chain, so bundle paths, advertised availability, generated changelog sections, and tag workflow checks must stay aligned.
- **Repository guidance boundary**: Start in root `AGENTS.md`, `fable5.md`, and `docs/` when changing agent-facing repository policy or operating guidance. Repository-level guidance applies across skill packages, while package-specific rules stay beside the owning skill; verify that generated or managed sections preserve custom user sections and do not duplicate package-owned details.

### Active Change Routes

- **Brief skill evolution route**: Within **Skill package contract**, start in `skills/task-brief-creator/SKILL.md` and mirror only intentional variant differences into `skills/task-brief-creator-caveman/` when changing brief generation behavior. Recent churn clusters around Stage 4, briefset, examples, templates, and validators, so confirm normal and caveman package contracts separately instead of assuming one file proves both.
- **Catalog promotion route**: Within **Release and marketplace boundary**, start in README skill status tables before editing `.claude-plugin/marketplace.json` when promoting, demoting, renaming, or bundling a skill. Recent changes repeatedly co-touch README, marketplace metadata, changelogs, and `package.json`, so verify the public catalog and marketplace plugin lists describe the same availability state.
- **Operating-guidance route**: Within **Repository guidance boundary**, start in `fable5.md` and root `AGENTS.md` when changing agent behavior rules. Recent updates added operating instructions outside a skill package, so keep durable repository rules in `AGENTS.md` and keep the detailed reasoning source in `fable5.md`.

## 3. Core Behaviors & Patterns

- **Progressive disclosure**: `SKILL.md` files define activation, scope, workflow, output contract, and routing. Large domain rules move into package-local `references/`, and entry points tell agents which reference to read at each decision point instead of loading every file by default.
- **Frontmatter-driven discovery**: Skill activation is controlled by YAML `name` and especially `description`. Descriptions carry trigger phrases, exclusions, explicit-invocation boundaries, and routing to sibling variants such as `task-brief-creator-caveman`.
- **Capability-local evidence**: A skill's templates, validators, examples, evals, licenses, and update notes stay under the same `skills/<skill-name>/` package. Cross-skill repository material belongs only in root docs or release scripts; do not create shared evidence areas for a single package's behavior.
- **Workflow gates as contracts**: Complex skills encode numbered stages, halt conditions, role splits, decision tables, output schemas, and termination metadata. Preserve these transitions in `task-brief-creator`, `feature-design-doc`, `iterative-self-review`, `delegated-review-loop`, `orchestration`, and `linear-issue-*` because downstream agents rely on them for when to ask, stop, validate, or hand off.
- **Structural validation only**: Python validators check filenames, headings, section order, checklist shape, frontmatter, references, and duplicate/empty sections with explicit exit codes. They intentionally avoid judging content quality; semantic judgment remains in the skill workflow, reviewer, or user decision step.
- **Release metadata chain**: Release state flows through `package.json`, `.release-it.json`, `scripts/release/*`, changelog files, `.github/workflows/release.yml`, `.claude-plugin/marketplace.json`, and README tables. A version bump or bundle change is unsafe unless each public metadata surface agrees.
- **Agent isolation patterns**: Review and orchestration skills distinguish main-agent, sub-agent, reviewer, and worker responsibilities. Keep path-passing, clean-context, no-prior-findings, and user-judged halt contracts explicit when editing those skills.

## 4. Conventions

- **Skill package naming**: Use `kebab-case` for skill directories, and keep the directory name aligned with the `name` frontmatter value. Variants keep the base name visible, such as `task-brief-creator-caveman`.
- **Frontmatter shape**: Installable `SKILL.md` files start with YAML frontmatter. Keep `name` lowercase kebab-case, make `description` the complete activation surface, and add `license` when package-local license material requires it.
- **Entry point structure**: Keep `SKILL.md` navigational rather than encyclopedic. Use sections for triggers, workflow, output contract, reference routing, helper scripts, guardrails, and scope boundaries; push detailed domain rules into `references/`.
- **Reference naming**: Use topic-oriented filenames that match local package schemes: `snake_case` for AGENTS generator specs, hyphenated workflow topics for brief skills, and numbered prefixes for JetBrains plugin references.
- **Relative package links**: Link package-owned material with relative paths like `references/template.md` or `scripts/validate_brief.py`. Avoid installed absolute paths in repository-authored skill docs.
- **Artifact placement**: Put reusable Markdown templates in `references/`, structural checks in `scripts/`, sample outputs in `examples/`, regression fixtures in `evals/`, and design/revision notes in `updates/`.
- **Python validator style**: Use standard-library modules, uppercase contract constants, compiled regexes, explicit exit codes, small parsing/validation functions, and `Report` or dataclass report objects for user-facing output.
- **Node release script style**: Use CommonJS, `node:` imports, uppercase root/path constants, `fail(message)` helpers, explicit argument validation, and targeted writes to release-owned files.
- **Documentation language**: Repository artifacts are English by default unless intentionally localized, such as `CHANGELOG.ko.md`; keep code, paths, command names, frontmatter keys, and exact user-provided strings unchanged.

## 5. Working Agreements

- Respond in Korean unless the user explicitly requests another language; keep technical terms, code blocks, file paths, identifiers, and exact logs unchanged.
- Ask the user before introducing tests, lint, formatter setups, or related automation; add them only on explicit request.
- Build context by reviewing related usages, flows, patterns, and likely impact before editing.
- Fix the underlying cause, not only the visible symptom; inspect affected flows and apply the narrowest complete change that resolves the root issue.
- Check side effects across callers, shared abstractions, public skill contracts, output formats, trigger behavior, bundle availability, and release metadata; report relevant impact and compatibility risks.
- Ask actively when user decisions are needed for scope, behavior, packaging, or tradeoffs.
- New functions, scripts, or modules should be single-purpose and colocated with the owning skill package or release workflow.
- External dependencies are allowed only when necessary; explain why any added dependency is required.
- Preserve user-owned custom sections when updating generated `AGENTS.md` files; refresh only standard managed sections.

## 6. user custom
- skill을 만들때 절대 serena를 활용하지마세요.
- Absolute rule for `fable5.md`: before any work that reads, edits, summarizes, reviews, references, or derives decisions from `fable5.md`, read `fable5.md` first. Its current contents are the authoritative source of truth, and this rule must not be skipped, weakened, or overridden by convenience, assumptions, prior context, or conflicting secondary instructions.
