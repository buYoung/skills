---
name: system-prompt-creator
description: A skill that analyzes user requirements to generate system prompts ready for evaluation. It determines whether a single or multi-prompt architecture is needed and queries for missing information if requirements are insufficient.
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

### Worked examples: clarify vs proceed

The clarify-vs-generate call is the same judgment in both directions — terse wording is not the
signal; the presence of the required fields is.

- **Insufficient → clarify (do NOT fabricate).** Request: *"I need a system prompt for a bot that
  helps our CX agents draft replies — that's basically it, set it up."* Purpose is partial, but
  Domain Context (policies, refund/cancellation rules, tone, product terms) and Expected Output
  (reply format/length/channel) are absent. ✅ Withhold the prompt and ask specifically for those
  two fields. ❌ Emit a finished prompt that invents policies/tone/format — even under an
  "assumptions you can override" caveat. *"I now have everything I need"* is the rationalization to
  catch; a breezy *"just set it up"* does not supply the missing fields.
- **Sufficient but terse → proceed (do NOT over-ask).** Request: *"auto-tag GitHub issues as one of
  bug/feature-request/docs/question/duplicate, else triage; output just the tag — that's all i need,
  set it up."* Terse, but the closed label set (the required Domain Context for a classifier) and
  the Expected Output are both present. ✅ Generate the single prompt now. ❌ Ask the user for the
  category taxonomy or "more domain context" — it was already supplied. Casual or brief wording is
  not insufficient input.

## Output

- **System prompt(s)**: 1 to N system prompts ready for evaluation
- **Architecture description**: Relationships and data flow between prompts in a multi-prompt setup
- **Validation note**: A generated prompt is not "production-ready" until measured against a test
  set. Recommend the success-criteria → dataset → grading → baseline → regression loop in
  [evaluation.md](references/evaluation.md). **Even if the user explicitly asks for a
  "production-ready" / "finished" / "ship-it-today" prompt, do not certify it as such.** Deliver the
  prompt, label it *ready for evaluation*, and keep the brief, non-blocking validation step — the
  user's wording does not waive it.
  - ✅ "Here's the prompt, ready for you to evaluate — smoke-test it on ~10 real inputs before you trust it."
  - ❌ "Here is the production-ready prompt." / "This passes the checklist and is ready to ship today."

## Core Knowledge

- **Prompt Structure**: Structural building blocks and assembly order of a system prompt. See [prompt_structure.md](references/prompt_structure.md)
- **Quality Criteria**: Quality standards and readiness checklists for prompts. See [quality_criteria.md](references/quality_criteria.md)
- **Multi-Prompt Architecture**: Design patterns for cases requiring N prompts. See [multi_prompt_architecture.md](references/multi_prompt_architecture.md)
- **Data Format Selection**: Accuracy comparison of different formats when including data in prompts. See [data_format_selection.md](references/data_format_selection.md)
- **Evaluation**: How to validate a generated prompt with a test set (success criteria, dataset, grading, baseline, regression). See [evaluation.md](references/evaluation.md)
