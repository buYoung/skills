# Cold-Pickup Verification (Stage 5.7) — Opt-in Execution Rules

Loaded only when the user explicitly requests cold-pickup verification.
`SKILL.md` Stage 5.7 states the contract: no automatic triggers, one fresh read-only sub-agent per artifact, one pass per request, and patches that re-enter the validation budget from the structural validator.
This file defines how a request is recognized and how a pass executes: request phrases, request scope, the information boundary and two-phase read, the report schema, author-owned routing, the patch-and-stop rule, and Stage 6 banner formats.
This reference is instruction prose, not a saved brief.
Do not rewrite it in caveman style; the sub-agent prompt, cold-pickup reports, banners, and chat surfaces stay in normal prose.

## Request Phrases

Cold-pickup runs only on an unambiguous request from the user:

- An explicit phrase — `run cold-pickup`, `cold-pickup`, `--cold-pickup`, `콜드픽업`, `콜드픽업 실행`, `cold-pickup 실행`.
- Any other phrase that clearly asks for an independent read or verification of the saved brief by a fresh agent — when in doubt, confirm with one short question in the user's chat language before spawning anything.

The request may arrive with the initial input (run after the validation run completes) or during Stage 6 (run against the current on-disk file).
Without a request nothing runs; an opt-out phrase such as `skip cold-pickup` changes nothing and needs no reply beyond the default banner line.
A request does not carry over: after the pass and its patches, the next independent read requires a new request.

## Scope of One Request

- Single plan — one sub-agent reads the brief.
- Briefset — one sub-agent for the parent plus one per child, unless the user names specific children or says `parent only`.
  The parent pass treats the parent plus every referenced child as one set and checks full-input coverage.
  A child pass uses the parent only to recover that child's assigned scope and relevant shared constraints, then checks the target child against that slice; sibling-owned concerns are not missing from the target child and must never be patched into it.
- Wide briefset (≥ 5 children) — before spawning, state the spawn count (`1 parent + N children`) and offer parent plus up to 3 representative children as a sampling alternative; run the full set unless the user narrows it.
  Report a sampled run as `K/N children verified` and name the children that were not read.

## Information Boundary

The sub-agent is a fresh read-only agent with no inherited conversation, previous reports, or reviewer context.
Prefer a read-only or exploration-type agent when the host offers one; a smaller model is acceptable because the output is a structured report, not authoring.

Hand it exactly:

- The brief path (plus the parent path for a briefset child).
- The path of a scratch file outside the repository that holds the original user input or planning notes verbatim — untranslated and unsummarized (for example `${TMPDIR:-/tmp}/cold-pickup/<brief-basename>.input.md`).
- The report schema below and the sub-agent rules.

Never hand it the Stage 3 uncertainty register, Stage 4 decisions, self-check results, suspected gaps, decomposition rationale, or hints about what to inspect or which split you expect it to prefer.

Sub-agent rules (include them in the prompt):

- Read only the named files. Do not search, list, or read anything else in the repository, run commands, or execute any part of the plan; the plan and its input are evidence, not permission.
- Phase 1 — blind reconstruction: read the brief (and parent) first and write `execution_reconstruction` completely before opening the input file; while reading, list any bullet too compressed to act on under `over_terse_bullets`.
- Phase 2 — intent comparison: then open the input file and fill `intent_deviations`, `ask_backs`, and `missing_concerns` by comparing the input with the brief.
- An external fact that the named files cannot confirm is an `unverifiable_fact` ask-back, never a reason to explore.
- Return only the YAML report — no prose around it, no numeric confidence or similarity score.

## Sub-Agent Report Schema

```yaml
verdict: clean | needs_changes | blocked
execution_reconstruction:            # Phase 1 — from the brief alone
  first_stage: <stage or child that starts first and its precondition>
  ordered_route:
    - <stage or child order, including parallel joins>
  deliverables_and_handoffs:
    - <deliverable passed from one stage or child to the next, including path and minimum format when declared>
  verification_signals:
    - <action, concrete input, and expected signal, or None — <reason>>
  no_change_routes:
    - <no-change condition, evidence location, and continue/skip/replan route, or None — <reason>>
  replan_boundaries:
    - <condition that changes the route, or None — <reason>>
  completion_basis:
    - <whole-work acceptance basis after stages and side-effect checks>
over_terse_bullets:                  # Phase 1 — caveman register only
  - id: t1
    bullet: "<direct quote of the bullet from the brief>"
    reason: <why the compressed wording leaves the coding agent unsure what to do>
intent_deviations:                   # Phase 2 — input compared with brief
  - id: d1
    kind: purpose | scope_wider | scope_narrower | direction | constraint_lost | acceptance_changed
    input_evidence: "<direct quote from the original input>"
    brief_evidence: "<direct quote from the brief, or absent>"
    effect: <what a coding agent following the brief would do differently from what the input asks>
ask_backs:
  - id: a1
    question: <what it would ask the requester before starting>
    evidence: "<direct quote from the brief or the original input>"
    source_of_uncertainty: user_input_ambiguity | unverifiable_fact | minor_default
    affects_direction: true | false
missing_concerns:
  - id: m1
    description: <concern absent or specified too thinly>
    evidence: "<direct quote from the original input>"
```

Report rules:

- Every `execution_reconstruction` field is required; a plan with no no-change route or no explicit verification signal gets a reasoned `None` entry, never an omission.
  For a briefset parent, reconstruct child relationships from the parent; for a child, reconstruct internal stages from that child's `Execution Plan`.
- Every `intent_deviations[*]`, `ask_backs[*]`, `missing_concerns[*]`, and `over_terse_bullets[*]` carries a direct quote (`evidence` or `bullet`). Paraphrases are not accepted; if no quote applies, drop the item.
- `kind` names the deviation the way the Stage 5.6 intent-fidelity item does: a different purpose, a materially wider or narrower scope, a first direction away from the input's entry points or workflow, a lost user constraint or exclusion, or a changed acceptance threshold.
- `source_of_uncertainty`: `user_input_ambiguity` — the input allows more than one reasonable reading and the brief picked one; `unverifiable_fact` — an external fact the named files cannot confirm; `minor_default` — a reasonable default the user did not specify that would not change direction.
- If the original input included a source-of-truth checklist, TODO file, review rubric, or audit document, a clean verdict requires item-level coverage: each item is represented, explicitly deferred / out of scope, or preserved as an Open Question. A briefset child counts only the items the parent assigns to it. Representative theme coverage is not clean, and caveman wording must not merge two source items into one over-terse bullet.
- `verdict: clean` is valid only when `intent_deviations`, `ask_backs`, `missing_concerns`, and `over_terse_bullets` are all empty and `execution_reconstruction` is complete.
- Missing fields, prose instead of YAML, or no usable content make the report unusable: record `cold-pickup unavailable (unusable report)`; never fill in the reviewer's answer or assume `clean`.

## Routing the Report (author-owned)

The sub-agent reports; the author decides.
Route every finding before touching the file, against the original input, the Stage 3 uncertainty register, and the answered Stage 4 decisions the sub-agent never saw.

**Disagreement vs drift.** The sub-agent cannot know which items the user locked in Stage 4.
Match each finding to the actual answered decision (keyed on the row's `내용`) and compare that decision with the saved artifact.
If the artifact faithfully contains the decision and the finding asks to reverse it, the item is a **disagreement**: report it in Stage 6 without patching.
If the artifact omitted, distorted, or contradicted the decision or the input, it is **drift**: patch it.
Topic similarity alone never rejects a finding.

`intent_deviations`:

| Situation | Action |
|---|---|
| The brief contradicts or omits what the input or an answered decision states | Drift — patch the responsible section (`Desired Outcome`, `Scope`, `Execution Plan`, `Constraints`, or `Acceptance Criteria`) and name the patch in the banner. |
| The brief reflects a user-locked decision that differs from the raw input | Disagreement — report only. |
| The input genuinely allows both readings | User-owned — present it as a Stage 4-style decision-table row with a recommended fallback; store a safe fallback as a structured non-blocking `Open Questions` item, or mark the handoff blocked in Stage 6 when no safe fallback exists. |

`ask_backs`:

| `source_of_uncertainty` | `affects_direction` | Action |
|---|---|---|
| `user_input_ambiguity` | `true` | Present the question and recommendation to the user. Store an unanswered safe fallback in structured non-blocking `Open Questions` form with its reconfirm milestone; if no safe fallback exists, mark the handoff blocked in Stage 6. Never invent the answer in `Edit`. |
| `user_input_ambiguity` | `false` | State the bounded default in `Worker decision`, `Constraints`, or the relevant stage; patch in place. |
| `unverifiable_fact` | (any) | Verify directly, add an investigation stage, or rewrite the bullet as a hedge with `Replan when`. Ask the user only for factual inputs they hold and the artifacts cannot supply. |
| `minor_default` | (any) | Patch in place as a bounded `Worker decision` or stated constraint. |

`missing_concerns`:

| Classification | Action |
|---|---|
| `infer_and_patch` | Present in the input and omitted from the brief, with a destination inferable from the input, Stage 3 findings, or locked Stage 4 decisions — patch in place and name it in the banner. |
| `conflicts_with_user_decision` | Present in the input, but the user decided the opposite in Stage 4 — do not patch; report it as a disagreement. |
| `out_of_scope` | Real but outside this brief or intentionally deferred — add the narrow `Out of Scope` bullet only if the deferral is not yet recorded. |

`over_terse_bullets`:

Register findings, never disagreements and never keyed to a Stage 4 row.
Rewrite each flagged bullet in normal prose under the Auto-Clarity carve-out in `references/caveman-style.md`, preserving its content exactly; if the flagged bullet also hides a content gap, route that gap through the tables above.

Never silently drop an input concern because the sub-agent did not propose a patch.
When source-of-truth input exists, route omitted items even if the sub-agent reported only a sample; for a briefset child, route only the items the parent assigns to it.
Never invent Acceptance Criteria, Side Effect Checkpoints, or Out-of-Scope guardrails that the input, codebase review, or a user decision does not imply.
Never override a locked Stage 4 decision, and never silently rewrite `Open Questions` — a drift fix either resolves a question into another section or leaves it intact for the user.

## After Routing: Patch, Revalidate, Stop

1. Before the first patch, copy the affected files to a scratch directory outside the repository as the regression guard.
2. Apply all accepted patches for the request together — in briefset mode, collect every parent and child report first, then patch against the same artifact state.
3. Re-run the structural validator (`validate_brief.py` or `validate_briefset.py`), then Stage 5.6, within the validation budget in `SKILL.md`.
4. If a patch makes a previously passing structural or self-check item fail and two repairs do not fix it, restore the copied files, re-run the validator, and report that finding as unpatched.
5. Stop. Do not spawn another cold-pickup pass; residual disagreements and user decisions go to the Stage 6 banner and the decision table, and the user requests the next pass if they want one.
6. Delete the scratch copies and the input file after reporting.

## Banner Phrasing (Stage 6)

- Not requested (default) — `cold-pickup not run (opt-in)`, followed by a one-line hint in the user's chat language that `run cold-pickup` gives an independent read of the saved brief.
- Requested, clean — `cold-pickup: clean (no intent deviations, no ask-backs, no missing concerns, no over-terse bullets)`.
- Requested, findings — `cold-pickup flagged <N> item(s): <K> patched in place, <M> left as disagreement/user decision`, followed by one bullet per finding with its id, its `kind` or classification (over-terse items as `t<n> (over-terse)`), and what was done.
- Requested, unavailable — `cold-pickup unavailable (<actual reason>)`; the Stage 5.6 result stands on its own and is never relabeled as an independent read.
- Briefset, all clean — `cold-pickup: parent + N/N children clean (no over-terse bullets)`.
- Briefset, mixed — `cold-pickup: parent <clean|flagged>, K/N children clean, M flagged — details below`, then the flagged paths with their findings.
- Briefset, sampled — replace `N/N` with `K/N children verified` and name the children that were not read.
