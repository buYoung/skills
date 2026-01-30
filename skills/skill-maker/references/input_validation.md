# Input Analysis & Clarification Loop

Defines the required validation process before skill generation begins.

## Purpose

This is the **first mandatory step** in skill creation. Parse user input and validate required information through iterative clarification until all criteria are met.

## Required Information Checklist

| Item | Check | Question if Missing |
|------|-------|---------------------|
| Purpose | What problem does this skill solve? | "What task should this skill automate or support?" |
| Scope | General-purpose or domain-specific? | "Is this skill intended to be general-purpose (applicable across domains) or specialized for a specific domain (e.g., language, framework, platform)?" |
| Domain | Target technology/framework specified? | "What language/framework/tool is this for?" |
| Trigger | When should the skill activate? | "In what situations should this skill be invoked?" |
| Input/Output | Clear inputs and expected outputs? | "What input does it receive and what output does it produce?" |
| Resources | Need scripts/references/assets? | "Are there scripts to execute or reference docs needed?" |

## Scope Clarification

| Scope Type | Description | Content Style |
|------------|-------------|---------------|
| **General-purpose** | Skill applies broadly without assuming specific technology stack | Abstract patterns, technology-agnostic guidance |
| **Domain-specific** | Skill is optimized for a particular language, framework, or platform | Concrete syntax, APIs, tool-specific details |

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

```text
1. Parse input → extract purpose, scope, domain, trigger, I/O, resources
2. Check each required item against sufficiency criteria
3. If any missing or insufficient → generate clarification questions → wait for response → repeat
4. If all sufficient → proceed to skill generation
```

## Validation Examples

### Insufficient Input

```text
User: "Create a skill for code review"

Missing:
- Scope: General-purpose or domain-specific?
- Domain: Which language/framework?
- Trigger: When to invoke?
- Input/Output: What files/format?

Response: "To create this skill, I need more details:
1. Is this for a specific language (e.g., TypeScript, Python) or general-purpose?
2. What triggers this skill - PR review, on-demand, pre-commit?
3. What input format (diff, full file) and output format (comments, report)?"
```

### Sufficient Input

```text
User: "Create a TypeScript code review skill that activates on PR reviews, 
takes diff input, and outputs inline comments following our style guide"

✅ Purpose: Code review automation
✅ Scope: Domain-specific
✅ Domain: TypeScript
✅ Trigger: PR reviews
✅ Input/Output: Diff → inline comments
✅ Resources: Style guide reference needed

→ Proceed to skill generation
```
