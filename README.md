# Skills

[![GitHub](https://img.shields.io/badge/GitHub-buYoung%2Fskills-blue?logo=github)](https://github.com/buYoung/skills)

**Skills** is a collection of skill packages for coding agents such as Claude Code and Codex. Each package has a `SKILL.md` entry point and, where needed, its own references, scripts, examples, and evals.

## Prerequisites

Some skills require external tools to be installed:

| Skill | Required Tools |
|-------|----------------|
| agents-md-generator | Python 3.10+, [tokei (required)](https://github.com/XAMPPRocky/tokei), [ripgrep (rg) (preferred)](https://github.com/BurntSushi/ripgrep), [tree](https://mama.indstate.edu/users/ice/tree/), git (update mode) |
| typst-creator | Typst CLI 0.13.0–0.15.1 for compilation (optional); Python 3.9+ for the version-support validator |
| task-brief-creator | Python 3.8+ for structural validators |
| task-brief-creator-caveman | Python 3.8+ for structural validators |
| document-writing | Python 3.9+ for package/FDD validation; Node.js 20+ for eval result validators; web access or user-supplied first-party sources for current storefront research |
| skill-creator | Independent agents for candidate refinement; Python 3.10+ and PyYAML for validation; Claude CLI on macOS or Linux for description optimization |
| react-guide | Node.js for eval validators |
| vite-guide | Node.js for eval validators |
| pi-package-creator | Pi v1.7.0 and Node.js 22.19+ for package checks; npm and `tar` for artifact checks |

## 🚀 Available Skills

Only skills that have been personally tested and approved by the user are listed here.

| Skill | Description |
|-------|-------------|
| [agents-md-generator](skills/agents-md-generator/) | Automatically sets up project structure and generates standardized `AGENTS.md` files. Supports both single-repo and monorepo structures. |
| [kysely-converter](./skills/kysely-converter/) | Converts SQL and writes, modifies, or refactors Kysely queries, with type-error diagnosis and version-aware references |
| [jetbrains-plugin-development](skills/jetbrains-plugin-development/) | IntelliJ Platform plugin development for JetBrains IDEs. Covers `plugin.xml`, services, actions, PSI/VFS/Document, EDT/BGT threading, Kotlin coroutines, custom languages (Grammar-Kit/JFlex), code insight, Kotlin UI DSL v2, IntelliJ Platform Gradle Plugin 2.x, Plugin Verifier, signing, and Marketplace publishing. |
| [jetbrains-vmoptions](skills/jetbrains-vmoptions/) | Diagnoses JetBrains IDE performance against the actual bundled or custom JBR 17/21/25 runtime, proposes minimal evidence-based VM option changes, verifies effective flags after restart, and provides rollback and controlled before/after measurement steps. |
| [system-prompt-creator](skills/system-prompt-creator/) | Analyzes user requirements to generate production-ready system prompts. It determines whether a single or multi-prompt architecture is needed and requests missing information if requirements are insufficient. |
| [typst-creator](skills/typst-creator/) | Create, update, review, or diagnose Typst source across stable Typst 0.13.0–0.15.1 with exact-version and cross-version compatibility routing. |
| [task-brief-creator](skills/task-brief-creator/) | Generates executable implementation work plans at `docs/briefs/` for one coding agent to author and another to execute. Each plan has nine required sections, including a staged `Execution Plan`. Briefset mode splits work that spans several execution contexts into a parent plan and child plans. Halts on vague input. Runs only when explicitly requested. |
| [code-security-audit](skills/code-security-audit/) | Performs OWASP-based code security audits on a codebase or a scoped path within it. Analyzes source code against ASVS 5.0.0 verification requirements, API Security Top 10 2023 risk patterns, OWASP CheatSheet secure coding practices, and WSTG v4.2 testing methodologies. |
| [release-it](skills/release-it/) | release-it configuration, setup, and plugin development. Analyzes project context (package.json, git remote, existing CI) to propose tailored release configs. Covers hooks, CLI workflows, pre-release, npm publishing, GitHub/GitLab releases, official plugins, and custom plugin development. |
| [document-writing](skills/document-writing/) | Creates, updates, rewrites, reviews, fact-checks, and normalizes human-readable structured documents through eleven routed types, including software READMEs, usage documentation, and Design System Documents for product UI or digital storefront visual assets. |
| [code-review](skills/code-review/) | Reviews Git changes for concrete defects and evidence-backed maintainability concerns. Defaults to all uncommitted changes, traces behavior in the selected version, checks counterevidence, and provides approval verdicts only on request. |
| [react-guide](skills/react-guide/) | React 18/19 guidance for React DOM web applications, covering explanation, design, implementation, and diagnosis across CSR, SSR/streaming/hydration, structure, Hooks/Effects, state/data, async UI, accessibility, performance, migrations, compatibility, and React Compiler behavior. |
| [vite-guide](skills/vite-guide/) | Vite 7/8 guidance for explanation, design, implementation, and diagnosis across client and SSR runtime integration, env/assets, separate client/server builds, manifests, Rollup/Rolldown, plugins, deployment recovery, performance, and Vite 6→7→8 migrations. |
| [task-brief-creator-caveman](skills/task-brief-creator-caveman/) | Caveman-output variant of `task-brief-creator`. Saved plans keep the same sections, stages, and checklists, but their prose is compressed. Chat, decision tables, reports, and `Open Questions` stay in normal prose, and Auto-Clarity restores normal prose wherever compression would obscure execution. |
| [clear-writing](skills/clear-writing/) | Writes, rewrites, and reviews practical reader-facing text such as notices, letters, emails, and text messages using ISO 24495-1 principles. Selects relevant content, improves structure and wording, and delivers finished text without drafting notes while preserving necessary meaning and exact references. |
| [skill-creator](skills/skill-creator/) | Creates, improves, and evaluates reusable skills. Refines a complete draft once through five independent candidates, integrates changes against shared requirements and consistency criteria, then continues the existing evaluation and feedback workflow. |

## 🧪 Skills Waiting for Review

These skills are currently under evaluation and will be promoted to **Available Skills** once verified.

| Skill | Description |
|-------|-------------|
| [biz-opportunity-scout](skills/biz-opportunity-scout/) | Identify and validate profitable business opportunities by analyzing TAM/SAM/SOM, unit economics, competitive landscape, and PMF indicators with HTML report generation |
| [iterative-self-review](skills/iterative-self-review/) | Iterative answer refinement loop. The main agent drafts a response and a sub-agent performs blind verification (only `user input + current answer`, no hints or history), reports back to the main agent only, and the loop terminates on a combination of positive (clean pass, severity floor), convergence (oscillation, stable findings, no-op, diminishing returns), defensive (regression), user-clarification, and hard-cap triggers. Evidence-mandatory findings, no numeric confidence scores. |
| [rust-guide](skills/rust-guide/) | Explains Rust characteristics and practical patterns through mechanisms, recommended usage, conditions, examples, and exceptions. Covers ownership, allocation, errors, async and parallel execution, code organization, Cargo workspaces, curated libraries, WebAssembly, embedded/no_std, SIMD, performance, unsafe/FFI, diagnostics, and compatibility. |
| [pi-package-creator](skills/pi-package-creator/) | Creates, extends, repairs, validates, tests, and packages Pi coding-agent packages: extensions and custom tools, skills, prompt templates, and themes. Includes a starter package, package checks, and executable tool tests. |
| [dba-guide](skills/dba-guide/) | Version-aware database administration guidance for MySQL, MariaDB, PostgreSQL, MongoDB, Amazon DocumentDB, Azure Cosmos DB, Couchbase, Redis, Valkey, Memcached, and Amazon DynamoDB. Covers data modeling, indexes and execution plans, transactions and locking, replication and failover, backup and PITR, configuration, security, monitoring, upgrades, and managed-service differences. |

## 🔒 Private Skills

Personal-use skills not included in the public marketplace.

| Skill | Description |
|-------|-------------|
| [linear-issue-creator](skills/linear-issue-creator/) | Creates structured Linear issues with a main issue + sub-issues, applying project linking, title prefix, and labeling rules. |
| [linear-issue-worker](skills/linear-issue-worker/) | Executes code tasks from Linear sub-issues. Resolves dependency graphs, transitions statuses, performs code work, addresses reviewer feedback, and posts completion comments. |
| [linear-issue-reviewer](skills/linear-issue-reviewer/) | Reviews completed Linear sub-issues by cross-validating Done Criteria, worker completion comments, and actual code changes. Produces Approved / Changes Requested / Clarification Needed verdicts. |

## 📖 How to Install Skills

### Claude Code (Marketplace)

1. Add the marketplace:
   ```
   /plugin marketplace add buYoung/skills
   ```

2. Install the skills plugin:
   - Select `Browse and install plugins`
   - Select `buyoung-agent-skills`
   - Select `document-skills`, `analysis-skills`, `backend-skills`, `devops-skills`, `frontend-skills`, or `jetbrains-skills`
   - Select `Install now`

   Or directly install via:
   ```
   /plugin install document-skills@buyoung-agent-skills
   /plugin install analysis-skills@buyoung-agent-skills
   /plugin install backend-skills@buyoung-agent-skills
   /plugin install devops-skills@buyoung-agent-skills
   /plugin install frontend-skills@buyoung-agent-skills
   /plugin install jetbrains-skills@buyoung-agent-skills
   ```

3. Use skills by mentioning them in your prompts (e.g., "Use agents-md-generator to create an AGENTS.md file")

### Codex

#### Method 1: Using skill-installer (Recommended)

1. Run Codex
2. Enter the following command:
   ```
   $skill-installer install https://github.com/buYoung/skills/tree/main/skills/{skill-name}
   # Example:
   $skill-installer install https://github.com/buYoung/skills/tree/main/skills/agents-md-generator
   ```
3. Restart Codex after installation completes
4. The skill will be available for use

#### Method 2: Manual Installation

1. Copy `agents-md-generator` folder to `~/.codex/skills/`
2. Run Codex
3. Navigate to the folder where you want to add `AGENTS.md`
4. Enter the following command and wait for completion:
   ```
   $agents-md-generator
   ```

## 💡 How to Use

Add the desired skill to your AI Agent (Claude Code, Codex, OpenCode, Gemini, etc.) and run it within your codebase. You can trigger skills by describing the task (e.g., "Create AGENTS.md for this project") or by calling the skill command directly.

### agents-md-generator

> ⚠️ Note: This skill defaults to `--all`, meaning it will generate `AGENTS.md` for all sub-packages in a monorepo.

#### Options
- `--root-only`: Generate for the root only.
- `--package <name>`: Generate for a specific package only.
- `--all`: Generate for the root and all packages (Default).

#### Example
- "Create AGENTS.md for this project"
- "Generate AGENTS.md --root-only"
- $agents-md-generator --package my-package

### document-writing

Describe the document you need; the skill picks one of eleven document types. Design System Documents apply one prebuilt per output set: product UI uses `default`, while digital storefront visual assets use `app-store-page`. Any in-scope storefront is identified dynamically from the request and current first-party material; examples do not form a supported-store list.

#### Examples

- "Write a README for this CLI package."
- "Explain idempotency keys to PM and customer support readers."
- "Write a runbook for diagnosing and recovering from DB connection failures."
- "Document this feature's behavior and policy decisions as the implementation decision source."
- "Create a platform-neutral product UI design system under docs/design-system."
- "Document an unfamiliar digital storefront's visual asset system from current first-party sources without creating the assets."
- "Research the current visual asset requirements for the storefronts in scope and document each one separately."
- "$document-writing review docs/operations/access-policy.md"

### skill-creator

After a complete draft, five independent candidates revise the same input once, and the main agent integrates their results before the usual evaluation and feedback workflow. You can ask for a different candidate count or skip this pass. Later evaluation-driven edits do not restart it unless you ask for another round.

#### Examples

- "Use skill-creator to create a skill for our release checklist."
- "Use skill-creator to improve this skill. Stop after integrating the candidate proposals."

## 📄 What is SKILL.md?

`SKILL.md` is the entry point of a skill package. Its frontmatter `name` and `description` tell the agent when to use the skill, and its body gives the workflow and links to the package's other files. The format is compatible with Claude Skills.

## 📚 References

- [system-prompt-creator](skills/system-prompt-creator/): The [Data Format Selection Guide](skills/system-prompt-creator/references/data_format_selection.md) was developed referencing the analysis table from [Improving Agents](https://www.improvingagents.com).
- [task-brief-creator](skills/task-brief-creator/): The Stage 4 user decision workflow is adapted from the [grill-me](https://github.com/mattpocock/skills/tree/main/skills/grill-me) skill from [mattpocock/skills](https://github.com/mattpocock/skills).
- [task-brief-creator-caveman](skills/task-brief-creator-caveman/): The caveman full-mode prose-compression rules (article/filler removal, fragment-friendly patterns, Auto-Clarity carve-outs) were adapted from the [caveman](https://github.com/juliusbrussee/caveman) skill by [juliusbrussee](https://github.com/juliusbrussee).
- [skill-creator](skills/skill-creator/): Adapted from Anthropic's [skill-creator](https://github.com/anthropics/skills/tree/main/skills/skill-creator), with an independent post-draft refinement and integration workflow. The upstream Apache-2.0 license is retained in the package.

## 🤝 Contributing

This project is open source. Bug reports, feature suggestions, and PRs are always welcome.

## 📝 License

MIT License — see [`LICENSE`](./LICENSE).

This repository incorporates material from third-party projects licensed under MIT, Apache-2.0, and CC BY-SA 4.0. See [`THIRD_PARTY_NOTICES.md`](./THIRD_PARTY_NOTICES.md) for upstream attributions and license texts.
