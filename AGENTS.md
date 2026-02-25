# AGENTS.md

## 1. Overview

This repository maintains reusable AI agent skills and supporting references for developer-AI collaboration tasks. Each skill package defines explicit capabilities in `SKILL.md` and details them through modular reference documents.

## 2. Folder Structure

- `skills/`: Primary skill packages.
    - `<skill-name>/SKILL.md`: Capability index with YAML frontmatter (`name`, `description`) and scoped sections.
    - `<skill-name>/references/`: Deep-dive specifications, syntax rules, and domain documents linked from `SKILL.md`.
    - `agents-md-generator/updates/`: Dated review artifacts and patch samples for skill revisions.
- `doc/`: Repository-level authoring policy.
    - `SKILL_GUIDELINES.md`: Capability-first writing rules and file structure standards.
- `.aiassistant/rules/`: Tooling-specific agent guidance overlays.
- `.windsurf/skills/`: IDE integration copies of selected skills.
- `README.md`: Skill catalog, installation flows, and activation examples.

## 3. Core Behaviors & Patterns

- **Progressive disclosure**: `SKILL.md` stays concise while linked `references/` files hold detailed specs and domain rules.
- **Capability-first documentation**: Skill docs consistently describe what the agent knows or supports, separating behavior policies into dedicated guidance files.
- **Frontmatter-driven metadata**: Skill entries use a consistent YAML frontmatter contract (`name`, `description`) for discoverability and validation.
- **Structured update trail**: Skill evolution is tracked through dated `updates/` directories containing patches and review notes.

## 4. Conventions

- **Naming**: Skill directory names use `kebab-case`; reference document filenames are topic-oriented and typically `snake_case`.
- **Document shape**: `SKILL.md` is the entry point, with relative markdown links to `references/` for deeper content.
- **Style**: Capability descriptions use concise, objective wording and avoid imperative behavior language inside skill specs.
- **Language split**: Repository documentation is written in English, while live agent-user interaction rules require Korean responses.

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
