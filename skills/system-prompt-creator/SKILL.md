---
name: system-prompt-creator
description: Generate system prompts from user requirements, with application guidance and request-derived evaluation materials. Use when asked to create, design, or draft a system prompt for an LLM bot, assistant, classifier, router, or explicitly requested multi-step pipeline (e.g. "create a system prompt", "시스템 프롬프트 만들어줘", "분류기 프롬프트 짜줘"). Defaults to a model-neutral single prompt; checks official guidance for a named model/provider. Supports revisions during the current creation task and current-agent simulations only after approval of concrete cases and scope. Not for standalone refinement/review of an existing prompt, one-off user prompts, agent definition files, CLAUDE.md/AGENTS.md, or skill definitions.
---

# System Prompt Creator

Create prompts that implement the user's requirements and can be applied and evaluated. The
evaluation target is the **generated system prompt's behavior against the user's requirements**,
not this skill's writing style or a generic prompt-quality score.

## Scope

Create a new system prompt or a requested set of stage prompts. Revisions and comparisons within
that creation task are supported. Standalone review or optimization of an existing prompt,
one-off user messages, agent/skill definition files, and image/video prompts are outside scope.

## Workflow

1. **Recover requirements from the conversation.** Identify purpose, runtime inputs, expected
   output, constraints, domain policies, and usage environment. Record material requirements
   with IDs and their source wording; distinguish user requirements, delegated design choices,
   and disclosed defaults. Do not ask again for supplied information.
2. **Resolve consequential gaps.** Apply the clarification gate below. Ask focused questions
   only for decisions that change correctness or integration; retain known requirements while
   waiting. Do not issue a finished prompt or invented expected answers while such gaps remain.
3. **Choose the configuration.** Default to one model-neutral prompt. Honor explicitly requested
   stages, branches, or loops; read
   [multi_prompt_architecture.md](references/multi_prompt_architecture.md) when those apply.
   Multiple output fields alone do not require multiple prompts.
4. **Assemble and explain application.** Read
   [prompt_structure.md](references/prompt_structure.md). Separate stable instructions, live
   user requests, and source material. Read
   [data_format_selection.md](references/data_format_selection.md) when embedding structured
   data or defining a stage contract. If a model/provider is named, read only the applicable
   parts of [model_guidance.md](references/model_guidance.md), check current official sources,
   and cite any resulting adaptation. Do not silently switch the requested target.
5. **Check requirement fidelity.** Read
   [quality_criteria.md](references/quality_criteria.md). Check that policies, examples, output
   values, input placement, and stage contracts agree with the request. This is a document
   review, not an execution result.
6. **Prepare evaluation materials.** Read
   [evaluation.md](references/evaluation.md). Derive concrete cases and grading criteria from
   requirements, their interactions, and plausible failures; there is no fixed case quota.
   Include coverage and limitations. Initially mark results `not_run`.
7. **Deliver, then simulate only with approval.** Provide the output below before requesting
   simulation approval. Show the exact cases, prompt versions, run scope, and current-agent
   limitation. Approval of prompt creation or evaluation-material preparation is not simulation
   approval. Execute only the approved scope; otherwise leave results `not_run` and finish the
   deliverable. Follow the result-preservation and comparison rules in the evaluation reference.

## Clarification Gate

Use what is present in the conversation before deciding something is missing.

| Information | Ask when | Proceed when |
|---|---|---|
| Purpose and runtime input | The task or what the model receives is unclear enough to change its behavior | The transformation and input source are identifiable |
| Closed outputs | Required labels, exact keys/types, or label definitions are missing or contradictory | They are provided, or the user explicitly delegates designing a new taxonomy/schema |
| Business policy | Eligibility, priorities, cutoffs, category overlap, or consequential exception behavior is unspecified | The rule is provided or design of that rule is explicitly delegated |
| Integration | The output must match an existing API/schema but its contract is absent | The contract is supplied; or a new contract is explicitly requested for design |
| Presentation | A required channel/format has consequences for acceptance | Ordinary tone, headings, or length can use stated defaults without changing the task |
| Environment | A required capability depends on the target API, tools, or message interface | No target is specified: deliver a model-neutral prompt with generic input placement |

Delegation permits a proposed design, not fabricated facts about an existing system. Label
designed taxonomies, policies, and schemas as proposals and keep them consistent across the
prompt, usage note, and evaluation materials. "Just get it going" is not authority to invent an
existing API or company policy.

Fallbacks and tie-breaks are task decisions. Preserve the allowed outputs; do not add `Other`,
`unknown`, `neutral`, a refusal, or a human-escalation route merely to complete a template. Ask
about a missing consequential rule, or design it when delegated. For open-ended tasks, a stated
default such as acknowledging absent source information can be appropriate without inventing
business policy.

### Examples of the Gate

- **Proceed with defaults:** "Summarize weekly sales-call transcripts; keep it simple." Use a
  concise summary format, disclose it, and ground the summary in the transcript. Do not require
  a sales methodology or invent deal stages and qualification rules.
- **Ask for labels:** "Classify tickets as JSON with category and confidence." Ask for the
  taxonomy and relevant decision rules; the JSON keys are already known.
- **Proceed with delegation:** "Design a small taxonomy for our new helpdesk; choose the labels
  and an ambiguity rule." Propose that design, identify it as delegated, and use the same rules
  in evaluation cases.
- **Ask for an existing contract:** "Extract, validate, then format exactly as our quoting API
  expects." The three stages are clear; request the API schema and any missing mapping/error
  policy. Do not substitute a guessed payload and describe it as compatible.
- **Ask about a conflict:** "Return exactly positive or negative; use neutral for mixed reviews."
  Resolve the allowed-label conflict before generating the classifier or its expected answers.

## Output Contract

By default, deliver all three items in the user's requested language (otherwise the request's
language); use the target audience's language for the generated prompt when specified.

1. **Copyable prompt(s).** Each complete system prompt has its own fenced block. Keep usage
   notes and evaluation materials outside the prompt. For multiple prompts, label stages and
   include their input/output contracts, routing, error propagation, and loop termination.
2. **Short application guidance.** Identify where stable instructions and runtime inputs go,
   required variables and their meanings/types, source-material boundaries, and any required
   tools, API settings, or supplied policy data. Distinguish verified target settings from
   generic guidance; say when no provider-specific configuration has been selected. Disclose
   presentation defaults and delegated choices. Explain architecture only as much as needed.
3. **Request-derived evaluation materials.** Include requirement IDs and source wording,
   observable success criteria, concrete inputs and needed conversation context, exact expected
   answers or acceptable-output rubrics, failure conditions, case-selection reasons, a coverage
   map, result records, and unverified requirements/limitations. Use the evaluation reference's
   reusable layouts. Expected outputs are not observed outputs.

Respect an explicit request to omit or narrow evaluation materials; briefly state the resulting
unverified scope without forcing an evaluation workflow. Do not certify production suitability
from a generated prompt, checklist, or current-agent simulation, even if asked for a finished
prompt. Creating materials does not authorize any run.

When a prompt changes during creation, retain the prior prompt text/version and compare shared
requirements using the same inputs and criteria. Record improved / unchanged / worsened /
indeterminate with evidence, never hypothetical prior results. A new prompt has no previous
run; its first authorized execution becomes the baseline.
