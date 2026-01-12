# Skills

[![GitHub](https://img.shields.io/badge/GitHub-buYoung%2Fskills-blue?logo=github)](https://github.com/buYoung/skills)

**Skills** is a collection of AI agent skills designed for efficient collaboration between developers and AI coding assistants. Each skill provides structured capabilities that AI agents can leverage to perform specific tasks.

## Prerequisites

Some skills require external tools to be installed:

| Skill | Required Tools |
|-------|----------------|
| agents-md-generator | [ripgrep (rg)](https://github.com/BurntSushi/ripgrep), [tokei](https://github.com/XAMPPRocky/tokei) |

## 🚀 Available Skills

| Skill | Description |
|-------|-------------|
| [agents-md-generator](skills/agents-md-generator/) | Automatically sets up project structure and generates metadata files like `AGENTS.md` for AI collaboration |
| [kysely-converter](./skills/kysely-converter/) | Converts database queries and schemas using Kysely |

## 📖 How to Use

### Codex

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
