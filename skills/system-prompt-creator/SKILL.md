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
- **Domain**: Information that identifies the target area of work. For classification, routing,
  labeling, or extraction-to-fixed-schema tasks, the **closed label set / category taxonomy /
  output schema keys are REQUIRED domain context** — a classifier or router whose output space is
  unknown cannot be specified, so a missing label set is a hard blocker, not a detail to assume.
- **Expected Output**: Information to determine what the final deliverable is
- **Complexity Judgment**: Information to decide whether a single or multi-prompt is needed

**If insufficient**: Early termination → Query specifically for the missing item(s).

### Generate-vs-clarify gate

Before producing any prompt, check each required field: **is it present, or am I about to
fabricate it?** If a closed-output element would have to be invented — enum values, a routing
taxonomy, fixed schema keys, allowed categories — **stop and ask for it** rather than emitting a
deliverable with an "assumptions" caveat. A fabricated closed-output value silently corrupts
correctness, so for closed-output systems the gate favors clarification over a polished guess. A
stronger drafting instinct is not a license to skip this check.

## Output

- **System prompt(s)**: 1 to N system prompts ready for evaluation
- **Architecture description**: Relationships and data flow between prompts in a multi-prompt setup
- **Validation note**: A generated prompt is not "production-ready" until measured against a test
  set. Recommend the success-criteria → dataset → grading → baseline → regression loop in
  [evaluation.md](references/evaluation.md).

## Core Knowledge

- **Prompt Structure**: Structural building blocks and assembly order of a system prompt. See [prompt_structure.md](references/prompt_structure.md)
- **Quality Criteria**: Quality standards and checklists for production-ready prompts. See [quality_criteria.md](references/quality_criteria.md)
- **Multi-Prompt Architecture**: Design patterns for cases requiring N prompts. See [multi_prompt_architecture.md](references/multi_prompt_architecture.md)
- **Data Format Selection**: Accuracy comparison of different formats when including data in prompts. See [data_format_selection.md](references/data_format_selection.md)
- **Evaluation**: How to validate a generated prompt with a test set (success criteria, dataset, grading, baseline, regression). See [evaluation.md](references/evaluation.md)
