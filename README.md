# Skills

[![GitHub](https://img.shields.io/badge/GitHub-buYoung%2Fskills-blue?logo=github)](https://github.com/buYoung/skills)

**Skills** is a collection of AI agent skills designed for efficient collaboration between developers and AI coding assistants. Each skill provides structured capabilities that AI agents can leverage to perform specific tasks.

## Prerequisites

Some skills require external tools to be installed:

| Skill | Required Tools |
|-------|----------------|
| agents-md-generator | [ripgrep (rg)](https://github.com/BurntSushi/ripgrep), [tokei](https://github.com/XAMPPRocky/tokei) |
| create-plan | None |
| skill-creator | None |

## 🚀 Available Skills

| Skill | Description |
|-------|-------------|
| [agents-md-generator](skills/agents-md-generator/) | Automatically sets up project structure and generates metadata files like `AGENTS.md` for AI collaboration |
| [kysely-converter](./skills/kysely-converter/) | Converts database queries and schemas using Kysely |
| [create-plan](skills/create-plan/) | Generate structured work plans before task execution. Collects context from user requirements, creates checklist-style plan files in the plan folder, and awaits user approval or modification before proceeding with implementation. |
| [skill-maker](skills/skill-maker/) | Create new AI agent skills following the SKILL.md guidelines with complete structure and README updates |
| [biz-opportunity-scout](skills/biz-opportunity-scout/) | Identify and validate profitable business opportunities by analyzing TAM/SAM/SOM, unit economics, competitive landscape, and PMF indicators with HTML report generation |

## 📖 How to Use

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
   $skill-installer install https://github.com/buYoung/skills/tree/main/skills/skill-creator
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

## 📄 What is SKILL.md?

`SKILL.md` defines tools (capabilities) and skills usable by AI agents. It is compatible with Claude Skills and provides structured instructions for AI to perform specific tasks effectively.

## 🤝 Contributing

This project is open source. Bug reports, feature suggestions, and PRs are always welcome.

## 📝 License

MIT License
