# Skills

[![GitHub](https://img.shields.io/badge/GitHub-buYoung%2Fskills-blue?logo=github)](https://github.com/buYoung/skills)

**Skills** is a collection of AI agent skills designed for efficient collaboration between developers and AI coding assistants. Each skill provides structured capabilities that AI agents can leverage to perform specific tasks.

## Prerequisites

Some skills require external tools to be installed:

| Skill | Required Tools |
|-------|----------------|
| agents-md-generator | [tokei (required)](https://github.com/XAMPPRocky/tokei), [ripgrep (rg) (preferred)](https://github.com/BurntSushi/ripgrep), [tree](https://mama.indstate.edu/users/ice/tree/) |
| jetbrains-vmoptions | None |
| kysely-converter | None |
| code-review | None |
| doc-coauthoring | None |
| typst-creator | None |
| ui-guide | None |
| code-security-audit | None |
| ux-design-guide | None |
| system-prompt-creator | None |
| veo-prompt-director | None |
| release-it | None |
| task-brief-creator | None |

## 🚀 Available Skills

Only skills that have been personally tested and approved by the user are listed here.

| Skill | Description |
|-------|-------------|
| [agents-md-generator](skills/agents-md-generator/) | Automatically sets up project structure and generates standardized `AGENTS.md` files. Supports both single-repo and monorepo structures. |
| [kysely-converter](./skills/kysely-converter/) | Converts database queries and schemas using Kysely |
| [jetbrains-vmoptions](skills/jetbrains-vmoptions/) | Generates JetBrains IDE VM options based on IDE version. Supports version-specific GC selection (Generational ZGC for 243+, G1GC for 222-242) and memory configuration. |
| [system-prompt-creator](skills/system-prompt-creator/) | Analyzes user requirements to generate production-ready system prompts. It determines whether a single or multi-prompt architecture is needed and requests missing information if requirements are insufficient. |
| [typst-creator](skills/typst-creator/) | Generate Typst source code for documents, reports, papers, and presentations, covering markup, math, scripting, and layout syntax. |
| [task-brief-creator](skills/task-brief-creator/) | Generates structured work-brief Markdown at `docs/briefs/` from planning notes or rough task descriptions. Eight required sections plus optional task-specific constraints are keyed to Conventional Commits types, with briefset mode for coordinated multi-brief execution. Halts on vague input. Manual trigger only. |
| [code-security-audit](skills/code-security-audit/) | Performs OWASP-based code security audits on any codebase. Analyzes source code against ASVS 5.0.0 verification requirements, API Security Top 10 2023 risk patterns, OWASP CheatSheet secure coding practices, and WSTG testing methodologies. |
| [release-it](skills/release-it/) | release-it configuration, setup, and plugin development. Analyzes project context (package.json, git remote, existing CI) to propose tailored release configs. Covers hooks, CLI workflows, pre-release, npm publishing, GitHub/GitLab releases, official plugins, and custom plugin development. |

## 🧪 Skills Waiting for Review

These skills are currently under evaluation and will be promoted to **Available Skills** once verified.

| Skill | Description |
|-------|-------------|
| [biz-opportunity-scout](skills/biz-opportunity-scout/) | Identify and validate profitable business opportunities by analyzing TAM/SAM/SOM, unit economics, competitive landscape, and PMF indicators with HTML report generation |
| [code-review](skills/code-review/) | Performs production-ready code reviews on git changes. Supports commit/range/file-scoped analysis, impact assessment, breaking-change detection, confidence-aware finding classification, and risk-weighted verdict generation. |
| [doc-coauthoring](skills/doc-coauthoring/) | Guide users through a structured 3-stage workflow for co-authoring documentation through Context Gathering, Refinement & Structure, and Reader Testing. |
| [react-vite-guide](skills/react-vite-guide/) | React 19 + Vite SPA development guidelines. Composition patterns, performance optimization, and web interface best practices for client-side React applications. |
| [ui-guide](skills/ui-guide/) | Generate, update, and maintain UI style guide documents from actual codebase analysis. Scans project files to extract real color palettes, typography scales, spacing systems, component patterns, and layout approaches. |
| [veo-prompt-director](skills/veo-prompt-director/) | Generates structured Google Veo 3.1 video prompts by collecting user input for subject, action, style, cinematography, and audio. Guides users through the Universal Prompt Formula to produce camera-ready prompts. |
| [ux-design-guide](skills/ux-design-guide/) | Reviews existing UI for UX guideline violations and generates implementation guidance based on 99+ rules across Navigation, Layout, Accessibility, Forms, Performance, Typography, and more. Supports Web, Mobile, and Desktop GUI platforms. |

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
   - Select `document-skills` or `backend-skills`
   - Select `Install now`

   Or directly install via:
   ```
   /plugin install document-skills@buyoung-agent-skills
   /plugin install backend-skills@buyoung-agent-skills
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
- [ux-design-guide](skills/ux-design-guide/): UX guidelines were developed referencing the 99 UX rules from [ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill).

## 🤝 Contributing

This project is open source. Bug reports, feature suggestions, and PRs are always welcome.

## 📝 License

MIT License
