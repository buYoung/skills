# Step 6: README.md Update

Update repository README.md with new skill information.

## User Confirmation

Before proceeding, ask the user:

> "Would you like to update the repository README.md with the new skill information? (yes/no)"

- **If yes**: Continue with the sections below
- **If no**: Skip this step and proceed to the next step

## Sections to Update

### 1. Prerequisites

Add row if external tools required:

```markdown
| {skill-name} | {tool1}, {tool2} |
```

If no external tools needed, add:

```markdown
| {skill-name} | None |
```

### 2. Available Skills

Add row with skill link and description from frontmatter:

```markdown
| [{skill-name}](skills/{skill-name}/) | {description from frontmatter} |
```

### 3. How to Use

Ensure Codex installation example reflects the skill:

```markdown
$skill-installer install https://github.com/buYoung/skills/tree/main/skills/{skill-name}
```
