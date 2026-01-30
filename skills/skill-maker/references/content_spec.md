# Content Specification

Defines the content classification for skill documentation.

## Content Classification

| Category | ✅ Capability (Include) | ❌ Behavior (Exclude) |
|----------|------------------------|----------------------|
| Focus | Static knowledge, syntax, API specs | Workflows, preferences, restrictions |
| Keywords | "Is", "Has", "Supports", "Consists of" | "Always", "Never", "Should", "Must" |
| Subject | Definition, Syntax, Parameters, Version | Formatting rules, interaction patterns |

## Capability Examples

| ❌ Behavior | ✅ Capability |
|------------|--------------|
| "Always format dates as ISO 8601" | "`DateUtils.toISO()` provides ISO 8601 formatting" |
| "Ask user for file path if missing" | "`readFile()` throws error if path is null" |
| "Never use deprecated APIs" | "`v2` API is current; `v1` API deprecated since 2024" |

## Content Types

| Type | Description | Location |
|------|-------------|----------|
| Syntax & Usage | Exact usage patterns of code, commands, DSLs | SKILL.md or references/ |
| Interface Specifications | Function signatures, component props, API schemas | references/ |
| Data Models | Entity relationships, state definitions | references/ |
| Environment/Versions | Supported versions, compatibility matrix | SKILL.md |
| Logic & Transformations | Deterministic input-to-output mappings | references/ |

## Size Constraints

| Item | Limit |
|------|-------|
| SKILL.md body | <500 lines |
| Reference files >100 lines | Table of contents required |
| Reference nesting | One level deep from SKILL.md only |

## Anti-Patterns

| Pattern | Description |
|---------|-------------|
| Duplicate Information | Same content in SKILL.md and references |
| Deeply Nested References | References linking to other references |
| Behavior as Capability | Using capability language to describe rules |
| Context Bloat | Large code blocks in SKILL.md instead of references |
| Missing Links | Reference files not linked from SKILL.md |
