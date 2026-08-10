# Skills

[![GitHub](https://img.shields.io/badge/GitHub-buYoung%2Fskills-blue?logo=github)](https://github.com/buYoung/skills)

**Skills** is a collection of AI agent skills designed for efficient collaboration between developers and AI coding assistants. Each skill provides structured capabilities that AI agents can leverage to perform specific tasks.

## Prerequisites

Some skills require external tools to be installed:

| Skill | Required Tools |
|-------|----------------|
| agents-md-generator | [tokei (required)](https://github.com/XAMPPRocky/tokei), [ripgrep (rg) (preferred)](https://github.com/BurntSushi/ripgrep), [tree](https://mama.indstate.edu/users/ice/tree/) |
| jetbrains-plugin-development | None |
| jetbrains-vmoptions | None |
| kysely-converter | None |
| code-review | None |
| doc-coauthoring | None |
| typst-creator | None |
| code-security-audit | None |
| system-prompt-creator | None |
| veo-prompt-director | None |
| release-it | None |
| task-brief-creator | None |
| task-brief-creator-caveman | None |

## 🚀 Available Skills

Only skills that have been personally tested and approved by the user are listed here.

| Skill | Description |
|-------|-------------|
| [agents-md-generator](skills/agents-md-generator/) | Automatically sets up project structure and generates standardized `AGENTS.md` files. Supports both single-repo and monorepo structures. |
| [kysely-converter](./skills/kysely-converter/) | Converts database queries and schemas using Kysely |
| [jetbrains-plugin-development](skills/jetbrains-plugin-development/) | IntelliJ Platform plugin development for JetBrains IDEs. Covers `plugin.xml`, services, actions, PSI/VFS/Document, EDT/BGT threading, Kotlin coroutines, custom languages (Grammar-Kit/JFlex), code insight, Kotlin UI DSL v2, IntelliJ Platform Gradle Plugin 2.x, Plugin Verifier, signing, and Marketplace publishing. |
| [jetbrains-vmoptions](skills/jetbrains-vmoptions/) | Generates JetBrains IDE VM options based on IDE version. Supports version-specific GC selection (Generational ZGC for 243+, G1GC for 222-242) and memory configuration. |
| [system-prompt-creator](skills/system-prompt-creator/) | Analyzes user requirements to generate production-ready system prompts. It determines whether a single or multi-prompt architecture is needed and requests missing information if requirements are insufficient. |
| [typst-creator](skills/typst-creator/) | Create, update, review, or diagnose Typst source across stable Typst 0.13.0–0.15.1 with exact-version and cross-version compatibility routing. |
| [task-brief-creator](skills/task-brief-creator/) | Generates executable implementation work plans at `docs/briefs/` for one coding agent to author and another to execute. Nine required sections include an `Execution Plan` with ordered stages, deliverables, handoffs, replan boundaries, and stage-level completion distinct from whole-work acceptance. Technical decisions stay with the plan author or worker; only non-blocking user-owned decisions with a safe default remain in `Open Questions`. Briefset mode coordinates multiple execution contexts. Halts on vague input. Manual trigger only. |
| [code-security-audit](skills/code-security-audit/) | Performs OWASP-based code security audits on any codebase. Analyzes source code against ASVS 5.0.0 verification requirements, API Security Top 10 2023 risk patterns, OWASP CheatSheet secure coding practices, and WSTG testing methodologies. |
| [release-it](skills/release-it/) | release-it configuration, setup, and plugin development. Analyzes project context (package.json, git remote, existing CI) to propose tailored release configs. Covers hooks, CLI workflows, pre-release, npm publishing, GitHub/GitLab releases, official plugins, and custom plugin development. |

## 🧪 Skills Waiting for Review

These skills are currently under evaluation and will be promoted to **Available Skills** once verified.

| Skill | Description |
|-------|-------------|
| [biz-opportunity-scout](skills/biz-opportunity-scout/) | Identify and validate profitable business opportunities by analyzing TAM/SAM/SOM, unit economics, competitive landscape, and PMF indicators with HTML report generation |
| [code-review](skills/code-review/) | Performs production-ready code reviews on git changes. Supports commit/range/file-scoped analysis, impact assessment, breaking-change detection, confidence-aware finding classification, and risk-weighted verdict generation. |
| [doc-coauthoring](skills/doc-coauthoring/) | Guide users through a structured 3-stage workflow for co-authoring documentation through Context Gathering, Refinement & Structure, and Reader Testing. |
| [react-guide](skills/react-guide/) | Build-tool-independent React 18/19 CSR execution router for structure, Hooks/Effects, state/data, performance, async UI, accessibility, migrations, version compatibility, and React Compiler behavior. |
| [vite-guide](skills/vite-guide/) | UI-framework-independent Vite 7/8 client execution router for runtime, env/assets, Rollup/Rolldown builds, plugins, deployment recovery, performance, and Vite 6→7→8 migrations. |
| [veo-prompt-director](skills/veo-prompt-director/) | Generates structured Google Veo 3.1 video prompts by collecting user input for subject, action, style, cinematography, and audio. Guides users through the Universal Prompt Formula to produce camera-ready prompts. |
| [task-brief-creator-caveman](skills/task-brief-creator-caveman/) | Caveman-output variant of `task-brief-creator`. It preserves the same nine-section execution contract, facts, bullets, stages, field order, handoffs, replan boundaries, and checklist depth while shortening only saved-plan prose values. Chat, decision tables, reports, and `Open Questions` stay in normal prose, and Auto-Clarity restores normal prose whenever compression would obscure execution. |
| [iterative-self-review](skills/iterative-self-review/) | Iterative answer refinement loop. The main agent drafts a response and a sub-agent performs blind verification (only `user input + current answer`, no hints or history), reports back to the main agent only, and the loop terminates on a combination of positive (clean pass, severity floor), convergence (oscillation, stable findings, no-op, diminishing returns), defensive (regression), user-clarification, and hard-cap triggers. Evidence-mandatory findings, no numeric confidence scores. |

## 🔒 Private Skills

Personal-use skills not included in the public marketplace.

| Skill | Description |
|-------|-------------|
| [linear-issue-creator](skills/linear-issue-creator/) | Creates structured Linear issues with a main issue + sub-issues, applying project linking, title prefix, and labeling rules. |
| [linear-issue-worker](skills/linear-issue-worker/) | Executes code tasks from Linear sub-issues. Resolves dependency graphs, transitions statuses, performs code work, and posts completion comments. |
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
   - Select `document-skills`, `analysis-skills`, `backend-skills`, or `devops-skills`
   - Select `Install now`

   Or directly install via:
   ```
   /plugin install document-skills@buyoung-agent-skills
   /plugin install analysis-skills@buyoung-agent-skills
   /plugin install backend-skills@buyoung-agent-skills
   /plugin install devops-skills@buyoung-agent-skills
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

### skill-creator (Claude Built-in)

Claude Code has a built-in `/skill-creator` slash command that guides you through creating new skills. No additional installation is required.

#### Usage
```
/skill-creator
```

Claude will interactively collect the necessary information (purpose, scope, domain, triggers, input/output) and generate a complete skill package with `SKILL.md`, optional bundled resources, and README integration.

## 📄 What is SKILL.md?

`SKILL.md` defines tools (capabilities) and skills usable by AI agents. It is compatible with Claude Skills and provides structured instructions for AI to perform specific tasks effectively.

## 📚 References

- [system-prompt-creator](skills/system-prompt-creator/): The [Data Format Selection Guide](skills/system-prompt-creator/references/data_format_selection.md) was developed referencing the analysis table from [Improving Agents](https://www.improvingagents.com).
- [task-brief-creator](skills/task-brief-creator/): The branch-walking decision-tree interview pattern incorporates the [grill-me](https://github.com/mattpocock/skills/tree/main/skills/grill-me) skill from [mattpocock/skills](https://github.com/mattpocock/skills).
- [task-brief-creator-caveman](skills/task-brief-creator-caveman/): The caveman full-mode prose-compression rules (article/filler removal, fragment-friendly patterns, Auto-Clarity carve-outs) were adapted from the [caveman](https://github.com/juliusbrussee/caveman) skill by [juliusbrussee](https://github.com/juliusbrussee).

## 🤝 Contributing

This project is open source. Bug reports, feature suggestions, and PRs are always welcome.

## 📝 License

MIT License — see [`LICENSE`](./LICENSE).

This repository incorporates material from third-party MIT-licensed projects.
See [`THIRD_PARTY_NOTICES.md`](./THIRD_PARTY_NOTICES.md) for upstream
attributions and license texts.
