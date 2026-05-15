---
name: iterative-self-review
description: Use this skill when the user explicitly asks for iterative answer refinement, blind sub-agent verification, independent validation, hallucination reduction, or repeated critique-and-revise cycles before finalizing a response or artifact. The main agent drafts the answer, a sub-agent reviews it blindly (only `user input + current answer`, no hints or history), reports back to the main agent only, and the loop stops on a combination of positive (clean verdict), convergence (stable findings, oscillation), defensive (regression), and user-clarification triggers.
---

# Iterative Self-Review

A controlled loop where the main agent owns the answer and a sub-agent performs blind verification. The sub-agent never edits the artifact, never writes the final response, and never receives anything beyond the user's original input and the current draft.

The loop guards against two failure modes:

- The main agent over-trusting its first draft.
- The verifier being biased by hidden hints, prior findings, or the main agent's reasoning.

## When to use

Use this skill when the user explicitly asks for one of:

- Iterative verification or repeated refinement before finalizing.
- A blind sub-agent, second-pass, or independent validation loop.
- A structured check for missing requirements, incorrect claims, logical problems, or risky assumptions.
- A final-answer quality gate with termination metadata.

Do not use this skill just because a task is difficult. If the user did not ask for a verification loop, handle the task normally.

## Core principles

1. **Blind input contract.** The sub-agent receives exactly two things: the user's original input and the current draft. No prior findings, no main-agent reasoning, no evaluation-criteria summaries beyond what is inlined in the sub-agent prompt itself.
2. **No numeric confidence.** LLM-rated confidence scores, similarity ratios, and thresholds are unreliable. Use qualitative signals and deterministic counts only.
3. **Evidence-mandatory findings.** Every issue, missing item, and unverified assertion must include a direct quote. Findings without evidence are downgraded.
4. **User clarification is a main-agent decision.** The sub-agent flags ambiguity; the main agent decides whether to ask.
5. **Sub-agent reports to the main agent only.** It never speaks to the user, never composes the final answer, never asks for additional context.

## Role split

| Role | Responsibilities | Forbidden |
|------|-----------------|-----------|
| **Main agent** | Draft answer, call sub-agent, parse report, route findings, revise, decide termination, ask user when needed, write final response with metadata | Pass prior findings, reasoning, or criteria summaries to the sub-agent |
| **Sub-agent** | Blind review, emit YAML report, quote evidence, classify unverified assertions | Edit the answer, write the final response, ask the user, request more context, invent context |

## Workflow

### Step 1 — Initial draft
Write the best current response. This is iteration 0's `current_response`.

### Step 2 — Blind sub-agent call
Invoke the sub-agent with the prompt body from [sub_agent_prompt_template.md](references/sub_agent_prompt_template.md). The template takes exactly two variables: `{{USER_INPUT}}` and `{{MAIN_RESPONSE}}`. Add nothing else.

The six review axes are inlined in the prompt. Their intent and scope guards live in [verification_criteria.md](references/verification_criteria.md).

### Step 3 — Parse the report
The sub-agent emits the YAML schema in [report_format.md](references/report_format.md). Validate on the spot:

- Any issue/missing without an `evidence` direct quote → downgrade per the report-format rules.
- Any `unverified_assertions[*]` missing `source_of_uncertainty` or `affects_direction` → ignore that item or re-call the sub-agent.

### Step 4 — Route findings
Route each item to *accept*, *reject*, or *ask user* per [routing_rules.md](references/routing_rules.md). Key branches:

- Regular issues: accept or reject. **Always log the reason for rejection** — required for stable-findings and oscillation detection.
- `unverified_assertions`:
  - `user_input_ambiguity` + `affects_direction=true` → ask user.
  - `unverifiable_fact` → main verifies directly or hedges. **Never ask the user.**
  - `minor_default` or `affects_direction=false` → use a reasonable default, state the assumption.

### Step 5 — Revise or branch to user
- If routing produced a user-clarification item, pause the loop, ask the user (batch multiple questions into one turn), and resume from Step 1 once they answer. Do not reset the iteration counter.
- Otherwise, integrate accepted changes into a new `current_response`.

### Step 6 — Evaluate termination
At the end of every iteration, evaluate the nine triggers in priority order from [termination_triggers.md](references/termination_triggers.md). The first trigger that fires ends the loop.

Priority groups:

| Priority | Trigger | Category |
|----------|---------|----------|
| 1 | Regression | Defensive |
| 2 | Oscillation | Convergence |
| 3 | Stable findings | Convergence |
| 4 | Clean pass | Positive |
| 5 | Severity floor | Positive |
| 6 | No-op iteration | Convergence |
| 7 | Diminishing returns | Convergence |
| 8 | User clarification needed | User-clarification |
| 9 | Hard cap (default: 8) | Fallback |

Category mapping to the original three-class spec (positive / convergence / defensive): Positive = `clean_pass`, `severity_floor`. Convergence = `oscillation`, `stable_findings`, `no_op`, `diminishing_returns`. Defensive = `regression`. The `user_clarification` and `hard_cap` triggers are safety branches outside the three-class loop end logic.

Regression is evaluated first because rollback must outrank any optimistic "one more pass might help" instinct. Convergence triggers come next because a non-progressing loop cannot be salvaged by continuing.

### Step 7 — Continue or finalize
If no trigger fires, loop to Step 2. Otherwise, go to Step 8.

### Step 8 — Final response with termination metadata
Append the termination block defined in [termination_triggers.md](references/termination_triggers.md). Schema:

```yaml
termination:
  trigger: clean_pass | severity_floor | user_clarified | regression | oscillation | stable_findings | no_op | diminishing_returns | hard_cap
  iterations: <count>
  classification: normal | defensive | hard_cap
  residual_issues:
    - severity: minor
      problem: <one-line description>
  rejected_findings:
    - problem: <one-line description>
      reason: scope_creep | redundant | factually_wrong | weak_evidence
  user_clarifications:
    - question: <asked>
      answer: <user's answer>
```

`classification: normal` only for `clean_pass`, `severity_floor`, `user_clarified`. `defensive` and `hard_cap` mean "automatic improvement has stalled" — surface this to the user; do not hide it. Use empty arrays for unused fields.

## Continue conditions

All of these must be true to run another iteration:

- No termination trigger fired (in particular, no Regression — Regression always ends the loop with rollback).
- The issues set changed semantically since the prior iteration (no Stable findings).
- The routing produced at least one accepted item (no No-op).
- Iteration count < hard cap.

## Design checklist

- [ ] Sub-agent prompt contains only `{{USER_INPUT}}` and `{{MAIN_RESPONSE}}` — no other variables.
- [ ] No prior iteration data passed to the sub-agent.
- [ ] Every issue/missing has an `evidence` direct quote (otherwise downgraded).
- [ ] Every `unverified_assertions` item has `source_of_uncertainty` and `affects_direction`.
- [ ] No confidence scores, thresholds, or similarity ratios used anywhere.
- [ ] Stable-findings comparison uses a yes/no LLM judge — never a numeric score.
- [ ] Termination triggers evaluated in the documented priority order.
- [ ] `user_input_ambiguity` + `affects_direction=true` routes to a user question.
- [ ] Final response includes the termination metadata block.

## Reference files

| File | When to read |
|------|--------------|
| [sub_agent_prompt_template.md](references/sub_agent_prompt_template.md) | Step 2 — exact prompt body to paste into the sub-agent call |
| [verification_criteria.md](references/verification_criteria.md) | Step 2 — six review axes and their scope guards |
| [report_format.md](references/report_format.md) | Step 3 — YAML schema and evidence/uncertainty enforcement |
| [routing_rules.md](references/routing_rules.md) | Step 4 — accept/reject and `unverified_assertions` routing |
| [termination_triggers.md](references/termination_triggers.md) | Step 6 — nine triggers, priority order, metadata schema |
