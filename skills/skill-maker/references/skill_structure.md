# Skill Structure Specification

Defines the file structure for AI agent skill packages.

## Directory Layout

```text
{skill-name}/
├── SKILL.md                # Required: Entry point with YAML frontmatter
├── references/             # Optional: Detailed technical specifications
│   └── {domain}.md
├── scripts/                # Optional: Executable automation code
│   └── {script}.{ext}
└── assets/                 # Optional: Templates, images, boilerplate
    └── {resource}.{ext}
```

## Progressive Disclosure

Skills use progressive disclosure to manage agent context efficiently:

```yaml
- stage: Discovery
  what_loads: "`name` + `description` from frontmatter only"
  purpose: Agent identifies relevant skills at startup without loading full content
- stage: Activation
  what_loads: "Full `SKILL.md` body"
  purpose: Agent reads instructions when a task matches the skill's description
- stage: Execution
  what_loads: "`references/`, `scripts/`, `assets/` as needed"
  purpose: Agent loads detailed specs or runs bundled code on demand
```

This model drives key structural decisions:

- **Frontmatter `description`** must be self-sufficient for matching — agents see nothing else during Discovery
- **SKILL.md body** acts as a lightweight index pointing to references, not a dump of all content
- **Reference nesting is one level deep** — agents load referenced files directly from SKILL.md, never from other references

## Directory Purposes

```yaml
- directory: references/
  purpose: Detailed specs, schemas, domain knowledge
  inclusion_criteria: Multi-domain or >100 lines of specs
- directory: scripts/
  purpose: Executable code for deterministic tasks
  inclusion_criteria: Repeated code patterns, reliability requirements
- directory: assets/
  purpose: Templates, images, boilerplate for output
  inclusion_criteria: Final deliverable resources needed
```

## Structure Selection Criteria

- **Simple (<100 lines, single domain)**: SKILL.md only
- **Medium (multi-domain or detailed specs)**: SKILL.md + references/
- **Complex (executable code + docs + templates)**: SKILL.md + references/ + scripts/ + assets/

## File References

- **Path format**: Relative paths from skill root (e.g., `references/spec.md`, `scripts/extract.py`)
- **Depth limit**: One level deep from SKILL.md — no references linking to other references
- **Link style**: Markdown links in SKILL.md body (e.g., `[spec](references/spec.md)`)

## Excluded Files

The following files are not part of skill packages:

- README.md
- INSTALLATION_GUIDE.md
- QUICK_REFERENCE.md
- CHANGELOG.md
- Auxiliary documentation files
