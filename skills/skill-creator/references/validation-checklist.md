# Validation Checklist

Detailed validation rules for skill creation.

## Frontmatter Validation

| Field | Rule |
|-------|------|
| `name` | ≤64 characters, lowercase letters/digits/hyphens only, no leading/trailing hyphens |
| `description` | ≤1024 characters, non-empty, describes what skill does AND when to use it |

## Content Validation

### Capability vs Behavior

| ✅ Capability (Include) | ❌ Behavior (Exclude) |
|------------------------|----------------------|
| Static knowledge, syntax, API specs | Workflows, preferences, restrictions |
| "Is", "Has", "Supports", "Consists of" | "Always", "Never", "Should", "Must" |
| Definition, Syntax, Parameters | Formatting rules, interaction patterns |

**Examples:**

| ❌ Bad (Behavior) | ✅ Good (Capability) |
|------------------|---------------------|
| "Always format dates as ISO 8601" | "`DateUtils.toISO()` provides ISO 8601 formatting" |
| "Ask user for file path if missing" | "`readFile()` throws error if path is null" |

### Size Limits

| Item | Limit |
|------|-------|
| SKILL.md body | <500 lines |
| Reference files >100 lines | Must include table of contents |
| Reference nesting | One level deep from SKILL.md only |

## Structure Validation

### Required Files

- `SKILL.md` with YAML frontmatter

### Optional Directories

| Directory | Purpose | When to Include |
|-----------|---------|-----------------|
| `scripts/` | Executable code | Deterministic reliability needed, repeated code |
| `references/` | Documentation | Detailed specs, schemas, domain knowledge |
| `assets/` | Output resources | Templates, images, boilerplate for final output |

### Forbidden Files

Do NOT create:
- README.md
- INSTALLATION_GUIDE.md
- QUICK_REFERENCE.md
- CHANGELOG.md
- Any auxiliary documentation

## Anti-Patterns

1. **Duplicate Information** - Content in both SKILL.md and references
2. **Deeply Nested References** - References linking to other references
3. **Behavior Disguised as Capability** - Using capability language for rules
4. **Context Bloat** - Large code blocks in SKILL.md instead of references
5. **Missing Reference Links** - Reference files not linked from SKILL.md
