---
name: system-prompt-creator
description: A skill that analyzes user requirements to generate system prompts ready for evaluation. It determines whether a single or multi-prompt architecture is needed and queries for missing information if requirements are insufficient. Use when asked to create, design, or draft a system prompt for an LLM-powered bot, assistant, classifier, router, or multi-step prompt pipeline (e.g. "create a system prompt", "시스템 프롬프트 만들어줘", "분류기 프롬프트 짜줘"). Not for refining an existing prompt, one-off user prompts, agent definition files, CLAUDE.md/AGENTS.md, or Claude Code skill definitions.
---

# System Prompt Creator

Generates ready-for-evaluation system prompts based on user requirements.

## Trigger

Representative requests (not exhaustive — the frontmatter description is the routing surface):

- "Create a system prompt for ..." / "I need a system prompt that ..."
- "Design the prompts for this LLM pipeline ..." (multi-step flow)
- "시스템 프롬프트 만들어줘", "분류기/라우터 프롬프트 짜줘"

### Out of scope

- Refining or reviewing an existing system prompt the user already has
- One-off user prompts (a single message to paste into a chat)
- Agent definition files, CLAUDE.md / AGENTS.md, or Claude Code skill definitions
- Image/video generation prompts

## Workflow

1. **Collect input** — map the request onto the Input fields below.
2. **Sufficiency gate** — apply the Input Sufficiency Criteria and the generate-vs-clarify gate.
   If a required field is missing, terminate early and ask for the specific field(s).
3. **Decide the architecture** — single prompt is the default. Read
   [multi_prompt_architecture.md](references/multi_prompt_architecture.md) (Architecture Design
   Process) only when the request describes intermediate artifacts, branching, iteration, or
   input splitting.
4. **Assemble the prompt(s)** — always read
   [prompt_structure.md](references/prompt_structure.md) for blocks and assembly order. Read
   [data_format_selection.md](references/data_format_selection.md) only when embedding data
   inside a prompt or defining an inter-prompt data contract.
5. **Quality check** — verify every item of the Readiness Checklist in
   [quality_criteria.md](references/quality_criteria.md); for classification/routing/extraction
   prompts the Disambiguation Rules (scope guard + tie-break) are required.
6. **Deliver with a validation note** — per the Output contract below, based on
   [evaluation.md](references/evaluation.md).

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

Single vs multi-prompt is **derived by the skill** from the fields above (explicit steps,
branching, or iteration the user described) — do not ask the user to choose an architecture;
ask only when their described processing flow is contradictory.

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

- **Insufficient → clarify (do NOT fabricate).** Request: *"Give me a system prompt for a bot
  that turns our weekly sales-call transcripts into summaries — nothing fancy, just get it
  going."* Purpose is partial, but Domain Context (sales methodology, deal stages, terminology,
  what matters in a call) and Expected Output (summary structure/length/destination) are absent.
  ✅ Withhold the prompt and ask specifically for those two fields. ❌ Emit a finished prompt
  that invents the summary structure and domain rules — even under an "assumptions you can
  override" caveat. *"I now have everything I need"* is the rationalization to catch; a breezy
  *"just get it going"* does not supply the missing fields.
- **Sufficient but terse → proceed (do NOT over-ask).** Request: *"auto-tag GitHub issues as one of
  bug/feature-request/docs/question/duplicate, else triage; output just the tag — that's all i need,
  set it up."* Terse, but the closed label set (the required Domain Context for a classifier) and
  the Expected Output are both present. ✅ Generate the single prompt now. ❌ Ask the user for the
  category taxonomy or "more domain context" — it was already supplied. Casual or brief wording is
  not insufficient input.

## Output

Deliverable shape: the architecture decision (single, or the pattern name) with a one-paragraph
rationale → each system prompt in its own fenced code block, labeled by stage → for multi-prompt
setups, the inter-prompt data contract → the validation note. Write the generated prompt in the
language the target model will serve end users in (default: the language of the user's request).

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
