# Step 1: Input Analysis & Clarification Loop

Parse user input and validate required information. Loop until sufficient.

## Required Information Checklist

| Item | Check | Question if Missing |
|------|-------|---------------------|
| Purpose | What problem does this skill solve? | "What task should this skill automate or support?" |
| Scope | General-purpose or domain-specific? | "Is this skill intended to be general-purpose (applicable across domains) or specialized for a specific domain (e.g., language, framework, platform)?" |
| Domain | Target technology/framework specified? | "What language/framework/tool is this for?" |
| Trigger | When should the skill activate? | "In what situations should this skill be invoked?" |
| Input/Output | Clear inputs and expected outputs? | "What input does it receive and what output does it produce?" |
| Resources | Need scripts/references/assets? | "Are there scripts to execute or reference docs needed?" |

### Scope Clarification

- **General-purpose**: Skill applies broadly without assuming specific technology stack
- **Domain-specific**: Skill is optimized for a particular language, framework, or platform

This distinction affects how the skill content should be written:
- General-purpose skills use abstract patterns and technology-agnostic guidance
- Domain-specific skills include concrete syntax, APIs, and tool-specific details

## Sufficiency Criteria

| Item | Minimum Requirement |
|------|---------------------|
| Purpose | Specific problem statement, not just a category name |
| Scope | Explicit choice between general-purpose or domain-specific |
| Domain | If domain-specific: language/framework/platform explicitly named; if general-purpose: "N/A" or broad applicability stated |
| Trigger | At least one concrete invocation scenario |
| Input/Output | Both defined explicitly, use "none" if not applicable |
| Resources | Explicit "none needed" or specific list of required resources |

## Loop Logic

1. Parse input → extract purpose, scope, domain, trigger, I/O, resources
2. Check each required item against sufficiency criteria
3. If any missing or insufficient → generate clarification questions → wait for response → repeat
4. If all sufficient → proceed to Step 2
