# Content Specification

Defines the content classification for skill documentation.

## Content Classification

```yaml
- category: Focus
  capability: Static knowledge, syntax, API specs
  behavior: Workflows, preferences, restrictions
- category: Keywords
  capability: "Is", "Has", "Supports", "Consists of"
  behavior: "Always", "Never", "Should", "Must"
- category: Subject
  capability: Definition, Syntax, Parameters, Version
  behavior: Formatting rules, interaction patterns
```

## Capability Examples

- **"Always format dates as ISO 8601"**: "`DateUtils.toISO()` provides ISO 8601 formatting"
- **"Ask user for file path if missing"**: "`readFile()` throws error if path is null"
- **"Never use deprecated APIs"**: "`v2` API is current; `v1` API deprecated since 2024"

## Recommended Body Sections

The Markdown body after frontmatter has no format restrictions, but the following sections are recommended:

- **Step-by-step instructions**: Guide agents through task execution
- **Examples of inputs and outputs**: Concrete usage patterns
- **Common edge cases**: Known pitfalls and how to handle them

The full SKILL.md body loads when the skill activates. Consider splitting longer content into referenced files.

## Content Types

```yaml
- type: Syntax & Usage
  description: Exact usage patterns of code, commands, DSLs
  location: SKILL.md or references/
- type: Interface Specifications
  description: Function signatures, component props, API schemas
  location: references/
- type: Data Models
  description: Entity relationships, state definitions
  location: references/
- type: Environment/Versions
  description: Supported versions, compatibility matrix
  location: SKILL.md
- type: Logic & Transformations
  description: Deterministic input-to-output mappings
  location: references/
```

## Size Constraints

- **SKILL.md body**: <500 lines
- **Reference files >100 lines**: Table of contents required
- **Reference nesting**: One level deep from SKILL.md only

## Anti-Patterns

- **Duplicate Information**: Same content in SKILL.md and references
- **Deeply Nested References**: References linking to other references
- **Behavior as Capability**: Using capability language to describe rules
- **Context Bloat**: Large code blocks in SKILL.md instead of references
- **Missing Links**: Reference files not linked from SKILL.md
