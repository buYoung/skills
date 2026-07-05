# SKILL.md and Reference Directory Creation Guidelines

This document provides guidelines for structuring and writing `SKILL.md` and its bundled resources. These files serve as the definition of the agent's **Capabilities** (Knowledge, Tools, Syntax, Domains).

## 1. Core Philosophy

The content must strictly define **"What the agent can do"** or **"What the agent knows."**
It must **NOT** define "How the agent should behave."

| Category | ✅ Include (Capabilities) | ❌ Exclude (Behavior/Rules) |
| :--- | :--- | :--- |
| **Focus** | Static knowledge, syntax, API specs, library features, business logic | Workflows, preferences, restrictions, formatting rules |
| **Keywords** | Definition, Syntax, Parameters, Version, Compatibility, Inputs/Outputs | Always, Never, Should, Must, Don't |
| **Example** | "The `Button` component accepts `primary` and `secondary` variants." | "Always use the `primary` variant for submit buttons." |
| **Example** | "The `calculateTax` function supports VAT and Sales Tax modes." | "Check the user's location before calculating tax." |

## 2. File Structure

### 2.1 Anatomy of a Skill

```text
skill-name/
├── SKILL.md                # Entry point: YAML frontmatter + instructions (required)
└── Bundled Resources (optional)
    ├── scripts/            # Executable code for deterministic/repetitive tasks
    ├── references/         # Docs loaded into context as needed
    └── assets/             # Files used in output (templates, icons, fonts)
```

- **`SKILL.md`**: Entry point. YAML frontmatter(name, description) + high-level capability summary.
- **`scripts/`**: Bundled scripts for tasks the model would otherwise reinvent every invocation. If test runs show the model independently writing similar helper scripts repeatedly, that's a strong signal to bundle the script here.
- **`references/`**: Detailed technical specifications and domain knowledge files.
- **`assets/`**: Static files used in output generation (templates, icons, fonts, etc.).

### 2.2 YAML Frontmatter (Required)

Every `SKILL.md` file **must** begin with a YAML frontmatter block containing the following required fields:

| Field | Constraints |
| :--- | :--- |
| `name` | Max 64 characters. Lowercase letters, numbers, and hyphens only. Must not start or end with a hyphen. |
| `description` | Max 1024 characters. Non-empty. Describes what the skill does **and when to use it**. This is the primary triggering mechanism. |
| `compatibility` | (Optional) Required tools, dependencies. Rarely needed. |

**Example:**

```yaml
---
name: agents-md-generator
description: Analyze repository structure and generate standardized AGENTS.md files that serve as contributor guides for AI agents.
---
```

#### Description Writing Best Practices

The `description` field is the primary mechanism that determines whether Claude invokes a skill. All "when to use" information goes here, not in the body.

- Include both **what the skill does** AND **specific contexts for when to use it**.
- Be slightly "pushy" in listing trigger contexts — Claude tends to under-trigger skills.
- List adjacent keywords and related scenarios so the skill triggers in edge cases.

**Bad:** `"How to build a simple fast dashboard to display internal data."`

**Good:** `"How to build a simple fast dashboard to display internal data. Use this skill whenever the user mentions dashboards, data visualization, internal metrics, or wants to display any kind of company data, even if they don't explicitly ask for a 'dashboard.'"`

### 2.3 Progressive Disclosure

Skills use a three-level loading system to manage context efficiently:

| Level | What | When Loaded | Size Guideline |
| :--- | :--- | :--- | :--- |
| **1. Metadata** | `name` + `description` | Always in context | ~100 words |
| **2. SKILL.md body** | Markdown instructions | When skill triggers | < 500 lines ideal |
| **3. Bundled resources** | `references/`, `scripts/`, `assets/` | As needed | Unlimited (scripts can execute without loading) |

**Key patterns:**
- Keep SKILL.md under 500 lines. If approaching this limit, add hierarchy with clear pointers to reference files.
- Reference files clearly from SKILL.md with guidance on **when** to read them.
- For large reference files (>300 lines), include a table of contents.

### 2.4 `SKILL.md` (Root File)
- Acts as an **Index** or **Table of Contents**.
- Briefly lists the domains, languages, frameworks, and key libraries the agent is proficient in.
- Links to specific files in the `./references/` directory for deep-dive information.
- **Do not** put massive code blocks here; keep it high-level.

### 2.5 Domain Organization

When a skill supports multiple domains or frameworks, organize by variant so Claude reads only the relevant reference file:

```text
cloud-deploy/
├── SKILL.md              # Workflow + selection logic
└── references/
    ├── aws.md
    ├── gcp.md
    └── azure.md
```

### 2.6 `./references/` (Subdirectory)
- Contains detailed markdown files for specific topics.
- Examples of file granularities:
  - `api_endpoints.md` (Backend API definitions)
  - `design_system.md` (UI/UX Component specs)
  - `business_rules.md` (Core business logic formulas)

## 3. Writing Guidelines

### 3.1 Content Requirements
All content must be factual and descriptive.

1.  **Syntax & Usage:** Exact usage patterns of code, commands, or DSLs.
2.  **Interface Specifications:** Function signatures, component props, API request/response schemas.
3.  **Data Models:** Entity relationships, state definitions, or data structures.
4.  **Environment/Versions:** Explicitly state supported versions (e.g., "Node.js 18+", "React 18 Hooks").
5.  **Logic & Transformations:** Deterministic input-to-output logic (e.g., "Input string 'A' transforms to Enum 'ALPHA'").

### 3.2 Tone & Style
- **Objective:** Use "Is", "Has", "Supports", "Consists of".
- **Descriptive:** Describe the mechanics of the capability.
- **Example-Driven:** Provide minimal, clear code snippets demonstrating the capability.

### 3.3 Writing Style Principles

#### Use Imperative Form
Prefer the imperative form in instructions. Direct commands are clearer and more concise than descriptive statements.

- **Bad:** `"The output should be formatted as JSON."`
- **Good:** `"Format the output as JSON."`

#### Explain the Why
Explain **why** things are important rather than relying on heavy-handed directives. LLMs have good theory of mind — when given reasoning, they go beyond rote instructions and produce better results.

- **Bad:** `"ALWAYS use semantic HTML elements. NEVER use div for interactive elements."`
- **Good:** `"Semantic HTML elements (button, nav, main) convey meaning to assistive technologies and improve accessibility. A div with a click handler lacks keyboard focus, ARIA role, and Enter/Space activation that a button provides natively."`

If you find yourself writing ALWAYS or NEVER in all caps, reframe by explaining the reasoning instead.

#### Keep It Lean
Remove content that isn't pulling its weight. Every line should earn its place. Prefer general principles over exhaustive enumerations — a well-explained concept covers more ground than a long list of specific cases.

#### Generalize, Don't Overfit
Write instructions that work across many prompts, not just a few examples. Avoid overly narrow, fiddly rules tied to specific scenarios. Use different metaphors or patterns if a concept is difficult to convey.

### 3.4 Writing Patterns

#### Defining Output Formats

```markdown
## Report structure
Use this template:
# [Title]
## Executive summary
## Key findings
## Recommendations
```

#### Examples Pattern

Include examples to clarify expected behavior. Format with Input/Output pairs:

```markdown
## Commit message format
**Example 1:**
Input: Added user authentication with JWT tokens
Output: feat(auth): implement JWT-based authentication
```

## 4. Security: Principle of Lack of Surprise

Skills must not contain malware, exploit code, or any content that could compromise system security. A skill's contents should not surprise the user in their intent if described.

## 5. Anti-Patterns (What to Avoid)

DO NOT include instructions on how the agent should interact with the user or format its output.

- **Bad:** "When using the date library, always format as ISO 8601." (Rule)
- **Good:** "The `DateUtils` library provides an `toISO()` method for ISO 8601 formatting." (Capability)

- **Bad:** "Ask the user for the file path if it's missing." (Workflow)
- **Good:** "The `readFile` function throws an error if the path argument is null." (System Constraint)

## 6. Template Examples

### 6.1 `SKILL.md` Example

```markdown
---
name: my-project-skill
description: Knowledge of the MyProject web application stack including Next.js 14 App Router, custom design system components, and JWT authentication flows. Use when working on MyProject codebase, its UI components, or auth-related features.
---

# Agent Capabilities

## Core Stack
- **Framework**: Next.js 14 (App Router)
- **Styling**: Tailwind CSS
- **State Management**: Zustand

## Domain Knowledge
- **Authentication**: Capability to handle JWT flows. See [./references/auth.md](./references/auth.md).
- **UI Components**: Knowledge of the custom design system. See [./references/ui_components.md](./references/ui_components.md).
```

### 6.2 `./references/ui_components.md` Example (Frontend/UI Domain)

```markdown
# UI Component Capabilities

Describes the available UI components and their properties.

## Button
- **Path**: `@/components/ui/Button`
- **Props**:
  - `variant`: 'solid' | 'outline' | 'ghost'
  - `size`: 'sm' | 'md' | 'lg'
- **Usage**: `<Button variant="solid">Click</Button>`

## Card
- **Capability**: Supports distinct header, content, and footer sections.
- **Structure**: Composed of `Card`, `CardHeader`, `CardContent`, `CardFooter`.
```

### 6.3 `./references/data_processing.md` Example (Logic/Utility Domain)

```markdown
# Data Processing Capabilities

Describes the utility functions available for data transformation.

## String Formatter
- **Function**: `formatCurrency(amount, currency)`
- **Capability**: Formats numbers into localized currency strings.
- **Support**: Supports 'USD', 'EUR', 'KRW'.

## Date Calculator
- **Function**: `addBusinessDays(date, days)`
- **Logic**: Skips weekends (Sat, Sun) when adding days.
```
