---
name: system-prompt-creator
description: A skill that analyzes user requirements to generate production-ready system prompts. It determines whether a single or multi-prompt architecture is needed and queries for missing information if requirements are insufficient.
---

# System Prompt Creator

Generates ready-to-use system prompts based on user requirements.

## Trigger

`Create a system prompt`

## Input

```yaml
- field: Purpose/Role
  description: The core task the AI agent will perform
  required: true
- field: Domain Context
  description: Background information, terminology, and rules of the target domain
  required: true
- field: Expected Output
  description: The form and format of the final deliverable
  required: true
- field: Constraints
  description: Tone, safety, length, prohibitions, etc.
  required: false
```

## Input Sufficiency Criteria

- **Purpose**: Specific task description (cannot be just a category name)
- **Domain**: Information that identifies the target area of work
- **Expected Output**: Information to determine what the final deliverable is
- **Complexity Judgment**: Information to decide whether a single or multi-prompt is needed

**If insufficient**: Early termination → Query specifically for missing items

## Output

- **System prompt(s)**: 1 to N production-ready system prompts
- **Architecture description**: Relationships and data flow between prompts in a multi-prompt setup

## Core Knowledge

- **Prompt Structure**: Structural building blocks and assembly order of a system prompt. See [prompt_structure.md](references/prompt_structure.md)
- **Quality Criteria**: Quality standards and checklists for production-ready prompts. See [quality_criteria.md](references/quality_criteria.md)
- **Multi-Prompt Architecture**: Design patterns for cases requiring N prompts. See [multi_prompt_architecture.md](references/multi_prompt_architecture.md)
- **Data Format Selection**: Accuracy comparison of different formats when including data in prompts. See [data_format_selection.md](references/data_format_selection.md)
