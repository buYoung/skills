# README.md Integration Specification

Defines the format for updating repository README.md with skill entries.

## Updated Sections

### Prerequisites Section

Row format for skills with external tool dependencies:

```markdown
| {skill-name} | {tool1}, {tool2} |
```

Row format for skills without dependencies:

```markdown
| {skill-name} | None |
```

### Available Skills Section

Row format:

```markdown
| [{skill-name}](skills/{skill-name}/) | {description from frontmatter} |
```

### How to Use Section

Installation example format:

```markdown
$skill-installer install https://github.com/{owner}/{repo}/tree/main/skills/{skill-name}
```

## Field Mappings

- **Skill name**: SKILL.md frontmatter `name`
- **Description**: SKILL.md frontmatter `description`
- **Prerequisites**: Skill's external dependencies (tools, CLIs, APIs)
