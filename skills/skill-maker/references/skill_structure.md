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

## Directory Purposes

| Directory | Purpose | Inclusion Criteria |
|-----------|---------|-------------------|
| `references/` | Detailed specs, schemas, domain knowledge | Multi-domain or >100 lines of specs |
| `scripts/` | Executable code for deterministic tasks | Repeated code patterns, reliability requirements |
| `assets/` | Templates, images, boilerplate for output | Final deliverable resources needed |

## Structure Selection Criteria

| Complexity | Structure |
|------------|-----------|
| Simple (<100 lines, single domain) | SKILL.md only |
| Medium (multi-domain or detailed specs) | SKILL.md + references/ |
| Complex (executable code + docs + templates) | SKILL.md + references/ + scripts/ + assets/ |

## Excluded Files

The following files are not part of skill packages:

- README.md
- INSTALLATION_GUIDE.md
- QUICK_REFERENCE.md
- CHANGELOG.md
- Auxiliary documentation files
