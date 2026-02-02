# AGENTS.md

## 1. Overview

A collection of AI agent skills providing structured capabilities for efficient developer-AI collaboration. Each skill defines what an agent can do or knows, enabling consistent task automation.

## 2. Folder Structure

- `skills/`: Individual skill packages, each self-contained with documentation and references.
    - `<skill-name>/SKILL.md`: Entry point defining capabilities, tools, and domains.
    - `<skill-name>/references/`: Detailed technical specifications and domain knowledge.
- `doc/`: Repository-level documentation and guidelines.
    - `SKILL_GUIDELINES.md`: Authoring standards for creating new skills.
- `.windsurf/skills/`: IDE-specific skill integrations.

## 3. Core Behaviors & Patterns

- **Capability-focused content**: SKILL.md defines "what the agent can do" (knowledge, tools, syntax), never "how it should behave."
- **Modular structure**: Each skill is isolated with its own `references/` for detailed specs.
- **YAML frontmatter**: Every SKILL.md requires `name` (max 64 chars, kebab-case) and `description` (max 1024 chars).
- **Progressive disclosure**: High-level index in SKILL.md, deep-dive details in references.

## 4. Conventions

- **Naming**: Skill directories use `kebab-case` (e.g., `agents-md-generator`, `kysely-converter`).
- **File structure**: `SKILL.md` as entry point, `references/` for detailed docs, optional `scripts/`, `assets/`.
- **Tone**: Objective, descriptive language ("Is", "Has", "Supports"); avoid imperative rules.
- **Documentation language**: English for SKILL.md content; Korean responses when interacting with users.

## 5. Working Agreements

- Respond in Korean (keep tech terms in English, never translate code blocks)
- Create tests/lint only when explicitly requested
- Build context by reviewing related usages and patterns before editing
- Prefer simple solutions; avoid unnecessary abstraction
- Ask for clarification when requirements are ambiguous
- Minimal changes; preserve public APIs
- New functions/modules: single-purpose, colocated with related code
- External dependencies: only when necessary, explain why
- If the operation fails due to file existence while using write_to_file, execute replace_file_content instead.