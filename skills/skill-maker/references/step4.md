# Step 4: Skill Generation

Generate complete skill structure.

## YAML Frontmatter (Required)

```yaml
---
name: {skill-name}  # lowercase, hyphens, <64 chars
description: {description}  # <1024 chars, clear trigger conditions
---
```

## Naming Convention

- Lowercase letters, digits, hyphens only
- No leading/trailing hyphens
- Verb-led phrases preferred (e.g., `convert-schema`, `generate-docs`)
- Namespace by tool when helpful (e.g., `gh-address-comments`)
- Folder name = skill name

## Body Content Rules

Define **Capabilities** (what agent can do/knows), NOT **Behavior** (how agent should act).

| ✅ Use | ❌ Avoid |
|--------|---------|
| "Is", "Has", "Supports", "Consists of" | "Always", "Never", "Should", "Must" |
| Definition, Syntax, Parameters | Workflows, preferences, restrictions |

**Examples:**

| ❌ Bad (Behavior) | ✅ Good (Capability) |
|------------------|---------------------|
| "Always format dates as ISO 8601" | "`DateUtils.toISO()` provides ISO 8601 formatting" |
| "Ask user for file path if missing" | "`readFile()` throws error if path is null" |
