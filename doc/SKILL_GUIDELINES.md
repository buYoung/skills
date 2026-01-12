# SKILL.md and Reference Directory Creation Guidelines

This document provides guidelines for structuring and writing `SKILL.md` and its subdirectory `references/`. These files serve as the definition of the agent's **Capabilities** (Knowledge, Tools, Syntax, Domains).

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

The capability documentation should follow a modular structure to maintain maintainability and context efficiency.

```text
root/
├── SKILL.md                # Entry point and high-level capability summary
└── references/             # Detailed technical specifications and domain knowledge
    ├── <domain>.md         # Specific domain capabilities (e.g., auth.md, ui_components.md)
    ├── <tool>.md           # Tool-specific syntax/usage (e.g., react_query.md)
    └── <syntax>.md         # Language or DSL specs (e.g., regex_patterns.md)
```

### 2.1 YAML Frontmatter (Required)

Every `SKILL.md` file **must** begin with a YAML frontmatter block containing the following required fields:

| Field | Constraints |
| :--- | :--- |
| `name` | Max 64 characters. Lowercase letters, numbers, and hyphens only. Must not start or end with a hyphen. |
| `description` | Max 1024 characters. Non-empty. Describes what the skill does and when to use it. |

**Example:**

```yaml
---
name: agents-md-generator
description: Analyze repository structure and generate standardized AGENTS.md files that serve as contributor guides for AI agents.
---
```

### 2.2 `SKILL.md` (Root File)
- Acts as an **Index** or **Table of Contents**.
- Briefly lists the domains, languages, frameworks, and key libraries the agent is proficient in.
- Links to specific files in the `./references/` directory for deep-dive information.
- **Do not** put massive code blocks here; keep it high-level.

### 2.3 `./references/` (Subdirectory)
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

## 4. Anti-Patterns (What to Avoid)

DO NOT include instructions on how the agent should interact with the user or format its output.

- **Bad:** "When using the date library, always format as ISO 8601." (Rule)
- **Good:** "The `DateUtils` library provides an `toISO()` method for ISO 8601 formatting." (Capability)

- **Bad:** "Ask the user for the file path if it's missing." (Workflow)
- **Good:** "The `readFile` function throws an error if the path argument is null." (System Constraint)

## 5. Template Examples

### 5.1 `SKILL.md` Example

```markdown
# Agent Capabilities

## Core Stack
- **Framework**: Next.js 14 (App Router)
- **Styling**: Tailwind CSS
- **State Management**: Zustand

## Domain Knowledge
- **Authentication**: Capability to handle JWT flows. See [./references/auth.md](./references/auth.md).
- **UI Components**: Knowledge of the custom design system. See [./references/ui_components.md](./references/ui_components.md).
```

### 5.2 `./references/ui_components.md` Example (Frontend/UI Domain)

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

### 5.3 `./references/data_processing.md` Example (Logic/Utility Domain)

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
