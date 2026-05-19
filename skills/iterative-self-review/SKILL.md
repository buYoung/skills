---
name: iterative-self-review
description: "Always use this skill before sending any user-facing main-agent response. It is the integrated clean-context verification loop for all response types: code changes, document edits, design proposals, ordinary answers, summaries, plans, recommendations, explanations, and file-change reports. The main agent drafts the current response, a clean-context sub-agent verifies only the applicable user requirements plus that current response, and the main agent revises and re-verifies until every blocker/major issue is gone and only minor residuals remain. If the user explicitly asks to verify only a specific part, use this skill on only that requested scope and pass only that scoped context to the sub-agent. Trigger even when the user did not explicitly ask for review, verification, or a second pass."
---

# Iterative Self-Review

A controlled loop where the main agent owns the answer and, when the user explicitly asks for verification or review, a clean-context sub-agent performs blind verification before the response is surfaced to the user. The sub-agent never edits the artifact, never writes the final response, and never receives anything beyond the applicable user input and the current main-agent response.

The loop guards against two failure modes:

- The main agent over-trusting its first draft.
- The verifier being biased by hidden hints, prior findings, or the main agent's reasoning.

## When to use

Use this skill only when the user explicitly asks for verification, review, re-checking, proof, cross-checking, or another second-pass quality gate. Do not run this skill automatically for ordinary conversation or routine task completion.

When invoked, treat all of the following as `current_response` artifacts:

- Code work and file-change reports.
- Documents, design proposals, specifications, and plans.
- Ordinary prose answers, summaries, recommendations, and explanations.
- Claims that work was done, files contain something, or a conclusion follows from inspected material.

If the user explicitly narrows verification to one part (for example, "이 파일만 검증해줘", "요약 부분만 봐줘", "3번 항목만 확인해줘"), construct `{{USER_INPUT}}` from only the user utterances needed to define that requested scope and pass only the corresponding part of `{{MAIN_RESPONSE}}`. Do not let unrelated conversation context broaden the review.

## Core principles

1. **Independent context contract.** The sub-agent receives exactly two textual inputs: the applicable user requirements and the current response. Blocked: prior findings, the main agent's reasoning, planning, routing intent, evaluation-criteria summaries. Not blocked: reality — read-only access to cited artifacts is required so response claims can be verified. "No other context" means no main-agent context, not "no tools".
2. **Immutable base block.** Within one verification session, the applicable user requirements, verification criteria, tool policy, and output schema remain byte-identical across rounds. Only the current response changes. If the user adds a new requirement, update the base block once and treat that as the new baseline.
3. **Sub-agent tool scope.** Allowed: read-only inspection tools only. Forbidden: edits, writes, shell file utilities, state-mutating commands, user dialog, asking for more context, calling other agents, WebSearch, arbitrary browsing. Scope is bounded by **claim-linkage**: trace dependencies as far as needed to verify a specific claim, stop the moment the trace no longer maps to a claim. Full wrapper-vs-reality and cross-platform tool rules live in `sub_agent_prompt_template.md`.
4. **Inspection manifest is mandatory.** Every cited artifact must have an `artifact_inspections` record. Intentionally skipped artifacts should be listed in `skipped_artifacts`. A `clean` verdict without complete manifest coverage is invalid. Schema and enforcement live in `report_format.md`.
5. **No numeric confidence.** LLM-rated confidence scores, similarity ratios, and thresholds are unreliable. Use qualitative signals and deterministic counts only.
6. **Evidence-mandatory findings.** Every issue, missing item, and unverified assertion must include a direct quote. Findings without evidence are downgraded.
7. **User clarification is a main-agent decision.** The sub-agent flags ambiguity; the main agent decides whether to ask.
8. **Sub-agent reports to the main agent only.** It never speaks to the user, never composes the final answer, never asks for additional context.

## Role split

| Role | Responsibilities | Forbidden |
|------|-----------------|-----------|
| **Main agent** | Draft answer, call sub-agent, parse report, route findings, revise, decide termination, ask user when needed, write final response with metadata | Pass prior findings, reasoning, or criteria summaries to the sub-agent |
| **Sub-agent** | Blind review, emit YAML report, quote evidence, classify unverified assertions | Edit the answer, write the final response, ask the user, request more context, invent context |

## Workflow

### Step 1 — Initial draft
Write the best current response. This is iteration 0's `current_response`. The response may be code-related, document-related, a plan, a summary, a file-change report, or ordinary prose.

### Step 2 — Blind sub-agent call
Invoke the sub-agent with the prompt body from [sub_agent_prompt_template.md](references/sub_agent_prompt_template.md). The template takes exactly two variables: `{{USER_INPUT}}` and `{{MAIN_RESPONSE}}`. Add nothing else.

`{{USER_INPUT}}` is **not "the user's last message"** — it is **the applicable substantive task request that serves as the reference point for verification**. When the user explicitly narrows verification, include only the user utterances that define that scope. When the most recent user message is a meta-trigger (skill re-invocation, "한번 더", "again", greetings, plain acknowledgements, or any message with no task information), reconstruct the slot by chronologically excerpting only the user's own utterances from earlier in the conversation. The reconstructed block must consist solely of verbatim user quotes — no main-agent summaries or interpretations. The canonical definition of the reconstruction rules and procedure lives in the Call-site notes of `sub_agent_prompt_template.md`.

The seven review axes are inlined in the prompt. Their intent and scope guards live in [verification_criteria.md](references/verification_criteria.md).

### Step 3 — Parse the report
The sub-agent emits the YAML schema in [report_format.md](references/report_format.md). Validate per that file's enforcement rules; re-call the sub-agent when the report is invalid. After two consecutive invalid reports the `verifier_invalid_report` defensive trigger fires (see `termination_triggers.md`).

### Step 4 — Route findings
Route each item per [routing_rules.md](references/routing_rules.md). Key branches:

- Regular issues and missing items: accept or reject. **Always log the reason for rejection** — required for stable-findings and oscillation detection.
- `scope_creep` issues: do not silently apply or remove them. Defer them to the user-decision phase unless they also contain a `blocker` or `major` correctness problem.
- `unverified_assertions`:
  - `user_input_ambiguity` + `affects_direction=true` → ask user only after any accepted non-minor fixes have been re-verified.
  - `unverifiable_fact` → main verifies directly or hedges. **Never ask the user.**
  - `minor_default` or `affects_direction=false` → use a reasonable default, state the assumption.

### Step 5 — Two-phase loop

#### Phase A — Auto-fix and re-verify

- If any accepted `blocker` or `major` issue, missing requirement, or direction-affecting unverified assertion can be resolved by the main agent, revise the response.
- When this iteration accepted at least one fix, do **not** surface user-decision items yet. Spawn the next verification round immediately with the immutable base block and the updated `{{MAIN_RESPONSE}}`.
- Phase A exits only after a round produces zero accepted non-minor fixes.

#### Phase B — User-decision items

- Surface `minor` items as residual information when useful.
- Surface `scope_creep` as a keep/remove decision.
- Surface unresolved `user_input_ambiguity` items that affect direction as direct questions.
- If the user's answer causes any response or artifact change, return to Phase A and re-verify before finalizing.

### Step 5.5 — Routing-completion gate
Per the canonical definition in [routing_rules.md](references/routing_rules.md). Positive triggers cannot fire while routed items remain unresolved.

### Step 6 — Evaluate termination
At the end of every iteration, evaluate the termination triggers in the priority order defined in [termination_triggers.md](references/termination_triggers.md). The first trigger that fires ends the loop.

For trigger #5 (Stable findings), invoke the **equivalence-judge sub-agent** as defined in `termination_triggers.md` — a separate single-shot sub-agent that takes only the two issue sets and answers yes/no. This is distinct from the verification sub-agent and exists to keep equivalence judgments independent of the main agent's self-bias.

User clarification is **not** a termination trigger — it is a Phase B routing branch (pause → ask → resume from Step 1 without resetting the iteration counter).

### Step 7 — Continue or finalize
If no trigger fires, loop to Step 2. Otherwise, go to Step 8.

### Step 8 — Final response with termination metadata
Append the termination block defined in [termination_triggers.md](references/termination_triggers.md):

```yaml
termination:
  trigger: clean_pass | severity_floor | regression | verifier_invalid_report | sub_agent_failure | oscillation | stable_findings | no_progress | no_op
  iterations: <count>
  residual_issues:
    - severity: minor
      problem: <one-line description>
  rejected_findings:
    - problem: <one-line description>
      reason: scope_creep | redundant | factually_wrong | weak_evidence
  user_decisions:
    - question: <asked>
      answer: <user's answer>
  failure_log:
    - type: transient | permanent
      cause: <one-line description>
      attempt: <number>
```

Only `clean_pass` and `severity_floor` represent successful termination. Surface every other trigger to the user — do not hide them behind a normal-looking response.

## Design checklist

- [ ] Sub-agent prompt contains only `{{USER_INPUT}}` and `{{MAIN_RESPONSE}}` — no other variables.
- [ ] When the user explicitly narrowed verification, `{{USER_INPUT}}` and `{{MAIN_RESPONSE}}` include only the requested scope.
- [ ] On rounds 2+, the user-input, verification-criteria, tool-policy, and output-schema blocks are byte-identical to the first round unless the user added a requirement.
- [ ] `{{USER_INPUT}}` is not filled with only a meta-trigger one-liner (e.g., "한번 더", "/iterative-self-review"); it contains the substantive request reconstructed from the user's own utterances.
- [ ] The reconstructed `{{USER_INPUT}}` consists solely of verbatim user-utterance quotes — no main-agent summaries or interpretations.
- [ ] No prior iteration data passed to the sub-agent.
- [ ] Sub-agent has read-only tool access only and is bound by claim-linkage scope.
- [ ] Sub-agent report includes `artifact_inspections` for every cited artifact, or an explicit failed inspection record.
- [ ] Sub-agent report includes skipped artifacts or areas when it intentionally did not inspect them.
- [ ] Every issue/missing has an `evidence` direct quote (otherwise downgraded).
- [ ] Every `unverified_assertions` item has `source_of_uncertainty` and `affects_direction`.
- [ ] No confidence scores, thresholds, or similarity ratios used anywhere.
- [ ] Stable-findings equivalence uses the dedicated yes/no equivalence-judge sub-agent — never a numeric score.
- [ ] Termination triggers evaluated in the documented priority order.
- [ ] Step 5.5 routing-completion gate passed before any Positive trigger is allowed to fire.
- [ ] `user_input_ambiguity` + `affects_direction=true` routes to a user question only after accepted non-minor fixes have been re-verified.
- [ ] Final response includes the termination metadata block.

## Reference files

| File | When to read |
|------|--------------|
| [sub_agent_prompt_template.md](references/sub_agent_prompt_template.md) | Step 2 — exact prompt body to paste into the sub-agent call (canonical wrapper-vs-reality rules) |
| [verification_criteria.md](references/verification_criteria.md) | Step 2 — seven review axes and their scope guards |
| [report_format.md](references/report_format.md) | Step 3 — YAML schema, evidence/uncertainty enforcement, manifest enforcement (canonical) |
| [routing_rules.md](references/routing_rules.md) | Step 4 / Step 5.5 — accept/reject routing, `unverified_assertions` routing, routing-completion gate (canonical) |
| [termination_triggers.md](references/termination_triggers.md) | Step 6 — nine triggers, priority order, equivalence-judge call, metadata schema |
