# Skills

[![GitHub](https://img.shields.io/badge/GitHub-buYoung%2Fskills-blue?logo=github)](https://github.com/buYoung/skills)

**Skills** is a collection of AI agent skills designed for efficient collaboration between developers and AI coding assistants. Each skill provides structured capabilities that AI agents can leverage to perform specific tasks.

## Prerequisites

Some skills require external tools to be installed:

| Skill | Required Tools |
|-------|----------------|
| agents-md-generator | [ripgrep (rg)](https://github.com/BurntSushi/ripgrep), [tokei](https://github.com/XAMPPRocky/tokei) |
| jetbrains-vmoptions | None |
| skill-maker | None |

## 🚀 Available Skills

Only skills that have been personally tested and approved by the user are listed here.

| Skill | Description |
|-------|-------------|
| [agents-md-generator](skills/agents-md-generator/) | Automatically sets up project structure and generates metadata files like `AGENTS.md` for AI collaboration |
| [kysely-converter](./skills/kysely-converter/) | Converts database queries and schemas using Kysely |
| [jetbrains-vmoptions](skills/jetbrains-vmoptions/) | Generates JetBrains IDE VM options based on IDE version. Supports version-specific GC selection (Generational ZGC for 243+, G1GC for 222-242) and memory configuration. |
| [skill-maker](skills/skill-maker/) | Create new AI agent skills following the SKILL.md guidelines with complete structure and README updates |

## 🧪 Skills Waiting for Review

These skills are currently under evaluation and will be promoted to **Available Skills** once verified.

| Skill | Description |
|-------|-------------|
| [biz-opportunity-scout](skills/biz-opportunity-scout/) | Identify and validate profitable business opportunities by analyzing TAM/SAM/SOM, unit economics, competitive landscape, and PMF indicators with HTML report generation |
| [typst-creator](skills/typst-creator/) | Generate Typst documents with proper syntax for markup, math, scripting, and styling. Based on Typst v0.14.2 |

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
   $skill-installer install https://github.com/buYoung/skills/tree/main/skills/skill-maker
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

### skill-maker

This skill guides you through the process of creating a new AI agent skill. It requires a mandatory input validation step to ensure all necessary details are gathered before generation begins.

#### Required Information
You will be asked to provide the following details:
- Purpose: The specific task or problem the skill automates.
- Scope: Choice between general-purpose or domain-specific.
- Domain: Target language, framework, or tool (if applicable).
- Trigger: Concrete situations where the skill should be invoked.
- Input/Output: Clear definition of inputs and expected outputs.
- Resources: Any scripts, reference docs, or assets needed.

For detailed sufficiency criteria, refer to [input_validation.md](skills/skill-maker/references/input_validation.md).

#### Examples
- Initial Request: "Create a new skill for automated code review" (Triggers clarification loop)
- Complete Request:
  > Create a new skill with following details:  
  > - Purpose: Automated code review for TypeScript projects  
  > - Scope: Domain-specific  
  > - Domain: TypeScript, Node.js  
  > - Trigger: Triggered manually or during PR review process  
  > - Input/Output: Takes git diffs as input and generates inline comments as output  
  > - Resources: Refer to the project's `.eslintrc.js` and `STYLE_GUIDE.md`  

## 📄 What is SKILL.md?

`SKILL.md` defines tools (capabilities) and skills usable by AI agents. It is compatible with Claude Skills and provides structured instructions for AI to perform specific tasks effectively.

## 🤝 Contributing

This project is open source. Bug reports, feature suggestions, and PRs are always welcome.

## 📝 License

MIT License
