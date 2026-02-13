# Input Analysis & Clarification Loop

Defines the required validation process before skill generation begins.

## Purpose

This is the **first mandatory step** in skill creation. Parse user input and validate required information through iterative clarification until all criteria are met.

## Required Information Checklist

```yaml
- item: Purpose
  check: What specific problem does this skill solve? Is the core value clear?
  question_if_missing: "What specific problem does this skill solve? Describe the concrete task it automates or the knowledge it provides (e.g., 'Automates unit test generation', 'Refactors legacy code', 'Provides mandatory backend coding conventions for code structure')."
- item: Scope
  check: Project-specific or universally applicable?
  question_if_missing: "Is this skill tied to a specific project structure or tech stack, or is it a universal utility usable in any project? (e.g., project-specific: depends on monorepo layout; universal: works with any codebase)"
- item: Domain
  check: Target technology/framework specified?
  question_if_missing: "What language/framework/tool is this for?"
- item: Input/Output
  check: Clear input format and output format defined?
  question_if_missing: "What is the input format and output format? (e.g., Input: File Path, String, JSON, Diff, Natural Language Prompt / Output: Markdown file, Code snippet, JSON, CLI output)"
- item: Resources
  check: Need scripts/references/assets?
  question_if_missing: "Are there scripts to execute or reference docs needed?"
```

## Scope Clarification

```yaml
- scope_type: Universal
  description: Skill works in any project regardless of structure or tech stack
  content_style: Abstract patterns, technology-agnostic guidance
  example: "Markdown linter, git commit message generator"
- scope_type: Project-specific
  description: Skill depends on a particular project structure, language, or platform
  content_style: Concrete syntax, APIs, tool-specific details
  example: "Next.js App Router migration, monorepo AGENTS.md generator"
```

## Sufficiency Criteria

- **Purpose**: Specific problem statement with clear value proposition, not just a category name (e.g., "code review" → "Automates TypeScript code review by analyzing diffs against style guide")
- **Scope**: Explicit choice between project-specific (tied to a structure/stack) or universal (any project)
- **Domain**: If project-specific: language/framework/platform explicitly named; if universal: "N/A" or broad applicability stated
- **Input/Output**: Both formats defined explicitly (e.g., "Diff → inline comments", "File Path → Markdown"), use "none" if not applicable
- **Resources**: Explicit "none needed" or specific list of required resources

## Loop Logic

```text
1. Parse input → extract purpose, scope, domain, I/O, resources
2. Check each required item against sufficiency criteria
3. If any missing or insufficient → generate clarification questions → wait for response → repeat
4. If all sufficient → proceed to skill generation
```

## Validation Examples

### Insufficient Input

```text
User: "Create a skill for code review"

Missing:
- Scope: Project-specific or universal?
- Domain: Which language/framework?
- Input/Output: What data format?

Response: "To create this skill, I need more details:
1. Is this tied to a specific project structure/tech stack, or usable in any project?
2. What language/framework is this for (e.g., TypeScript, Python)?
3. What is the input format (e.g., Diff, File Path, JSON) and output format (e.g., Markdown, inline comments)?"
```

### Sufficient Input

```text
User: "Create a TypeScript code review skill that activates on PR reviews, 
takes diff input, and outputs inline comments following our style guide"

✅ Purpose: Automates TypeScript code review by analyzing diffs against style guide
✅ Scope: Universal (works with any TypeScript project)
✅ Domain: TypeScript
✅ Input/Output: Diff → inline comments
✅ Resources: Style guide reference needed

→ Proceed to skill generation
```
