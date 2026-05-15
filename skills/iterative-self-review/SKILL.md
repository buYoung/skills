---
name: iterative-self-review
description: Use this skill when the user explicitly asks for iterative answer refinement, blind sub-agent verification, independent validation, hallucination reduction, or repeated critique-and-revise cycles before finalizing a response or artifact. The main agent drafts the answer, a sub-agent reviews it blindly (only `user input + current answer`, no hints or history), reports back to the main agent only, and the loop stops on a combination of positive (clean verdict), convergence (stable findings, oscillation), defensive (regression, invalid verifier report), and user-clarification triggers.
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

1. **Independent context contract.** The sub-agent receives exactly two textual inputs: the user's original input and the current draft. Blocked: prior findings, the main agent's reasoning, planning, routing intent, evaluation-criteria summaries. Not blocked: reality — read-only access to the repository (Read, Glob, Grep; WebFetch for cited URLs only) is required so cited artifacts can be verified. "No other context" means no main-agent context, not "no tools".
2. **Sub-agent tool scope.** Allowed: Read, Glob, Grep (Serena search tools when available); WebFetch **only** for URLs cited in the draft. Forbidden: Edit, Write, shell execution (tests/builds), user dialog, asking for more context, calling other agents, WebSearch, arbitrary browsing. Scope is bounded by **claim-linkage**: trace dependencies as far as needed to verify a specific claim, stop the moment the trace no longer maps to a claim. Full wrapper-vs-reality rules live in `sub_agent_prompt_template.md`.
3. **Inspection manifest is mandatory.** Every cited artifact must have an `artifact_inspections` record. A `clean` verdict without complete manifest coverage is invalid. Schema and enforcement live in `report_format.md`.
4. **No numeric confidence.** LLM-rated confidence scores, similarity ratios, and thresholds are unreliable. Use qualitative signals and deterministic counts only.
5. **Evidence-mandatory findings.** Every issue, missing item, and unverified assertion must include a direct quote. Findings without evidence are downgraded.
6. **User clarification is a main-agent decision.** The sub-agent flags ambiguity; the main agent decides whether to ask.
7. **Sub-agent reports to the main agent only.** It never speaks to the user, never composes the final answer, never asks for additional context.

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
The sub-agent emits the YAML schema in [report_format.md](references/report_format.md). Validate per that file's enforcement rules; re-call the sub-agent when the report is invalid. After two consecutive invalid reports the `verifier_invalid_report` defensive trigger fires (see `termination_triggers.md`).

### Step 4 — Route findings
Route each item per [routing_rules.md](references/routing_rules.md). Key branches:

- Regular issues: accept or reject. **Always log the reason for rejection** — required for stable-findings and oscillation detection.
- `unverified_assertions`:
  - `user_input_ambiguity` + `affects_direction=true` → ask user.
  - `unverifiable_fact` → main verifies directly or hedges. **Never ask the user.**
  - `minor_default` or `affects_direction=false` → use a reasonable default, state the assumption.

### Step 5 — Revise or branch to user
- If routing produced a user-clarification item, pause the loop, ask the user (batch multiple questions into one turn), and resume from Step 1 once they answer. Do not reset the iteration counter.
- Otherwise, integrate accepted changes into a new `current_response`.

### Step 5.5 — Routing-completion gate
Per the canonical definition in [routing_rules.md](references/routing_rules.md). Positive triggers cannot fire while routed items remain unresolved.

### Step 6 — Evaluate termination
At the end of every iteration, evaluate the eight triggers in the priority order defined in [termination_triggers.md](references/termination_triggers.md). The first trigger that fires ends the loop.

For trigger #4 (Stable findings), invoke the **equivalence-judge sub-agent** as defined in `termination_triggers.md` — a separate single-shot sub-agent that takes only the two issue sets and answers yes/no. This is distinct from the verification sub-agent and exists to keep equivalence judgments independent of the main agent's self-bias.

User clarification is **not** a termination trigger — it is a routing branch (pause → ask → resume from Step 1 without resetting the iteration counter).

### Step 7 — Continue or finalize
If no trigger fires, loop to Step 2. Otherwise, go to Step 8.

### Step 8 — Final response with termination metadata
Append the termination block defined in [termination_triggers.md](references/termination_triggers.md):

```yaml
termination:
  trigger: clean_pass | severity_floor | regression | verifier_invalid_report | oscillation | stable_findings | no_op | hard_cap
  iterations: <count>
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

Only `clean_pass` and `severity_floor` represent successful termination. Surface every other trigger to the user — do not hide them behind a normal-looking response.

## Design checklist

- [ ] Sub-agent prompt contains only `{{USER_INPUT}}` and `{{MAIN_RESPONSE}}` — no other variables.
- [ ] No prior iteration data passed to the sub-agent.
- [ ] Sub-agent has read-only tool access (Read, Glob, Grep; WebFetch only for cited URLs) and is bound by claim-linkage scope.
- [ ] Sub-agent report includes `artifact_inspections` for every cited artifact, or an explicit failed inspection record.
- [ ] Every issue/missing has an `evidence` direct quote (otherwise downgraded).
- [ ] Every `unverified_assertions` item has `source_of_uncertainty` and `affects_direction`.
- [ ] No confidence scores, thresholds, or similarity ratios used anywhere.
- [ ] Stable-findings equivalence uses the dedicated yes/no equivalence-judge sub-agent — never a numeric score.
- [ ] Termination triggers evaluated in the documented priority order.
- [ ] Step 5.5 routing-completion gate passed before any Positive trigger is allowed to fire.
- [ ] `user_input_ambiguity` + `affects_direction=true` routes to a user question.
- [ ] Final response includes the termination metadata block.

## Reference files

| File | When to read |
|------|--------------|
| [sub_agent_prompt_template.md](references/sub_agent_prompt_template.md) | Step 2 — exact prompt body to paste into the sub-agent call (canonical wrapper-vs-reality rules) |
| [verification_criteria.md](references/verification_criteria.md) | Step 2 — six review axes and their scope guards |
| [report_format.md](references/report_format.md) | Step 3 — YAML schema, evidence/uncertainty enforcement, manifest enforcement (canonical) |
| [routing_rules.md](references/routing_rules.md) | Step 4 / Step 5.5 — accept/reject routing, `unverified_assertions` routing, routing-completion gate (canonical) |
| [termination_triggers.md](references/termination_triggers.md) | Step 6 — eight triggers, priority order, equivalence-judge call, metadata schema |
