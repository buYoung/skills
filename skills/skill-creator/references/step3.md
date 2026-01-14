# Step 3: Content Scoping

Apply Progressive Disclosure principle to distribute content.

## Content Distribution

| Content Type | Location |
|--------------|----------|
| Core workflow, selection guidance | SKILL.md body |
| Detailed specs, schemas, examples | references/ |
| Executable automation code | scripts/ |
| Templates, images, boilerplate | assets/ |

## Key Rules

- SKILL.md body < 500 lines
- No duplicate information between SKILL.md and references
- Reference files must be linked from SKILL.md with clear usage context
- References one level deep only (no nested references)
- Reference files >100 lines must include table of contents
