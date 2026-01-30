---
name: skill-maker
description: Generates AI agent skill packages with SKILL.md, optional bundled resources (scripts/, references/, assets/), and README.md integration.
---

# Skill Maker Capabilities

Skill generation tooling for AI agent capability packages.

## Core Capabilities

- **Skill Package Generation**: Creates complete skill directory structures
- **YAML Frontmatter Support**: Generates compliant frontmatter with name/description fields
- **Resource Bundling**: Supports scripts/, references/, assets/ subdirectories
- **README Integration**: Updates repository README.md with skill entries

## Supported Outputs

| Output Type | Description |
|-------------|-------------|
| `SKILL.md` | Entry point with YAML frontmatter and capability index |
| `references/` | Detailed technical specifications and domain knowledge |
| `scripts/` | Executable automation code |
| `assets/` | Templates, images, boilerplate files |

## Technical References

| Reference | Content |
|-----------|---------|
| [skill_structure.md](references/skill_structure.md) | File structure specifications and directory purposes |
| [frontmatter_spec.md](references/frontmatter_spec.md) | YAML frontmatter field constraints and examples |
| [content_spec.md](references/content_spec.md) | Capability vs behavior content classification |
| [readme_spec.md](references/readme_spec.md) | README.md update format and section specifications |
