# Cold-Pickup Verification (Stage 5.7) — Execution Rules

Loaded when the Stage 5.7 gate fires or the user forces cold-pickup.
`SKILL.md` Stage 5.7 defines *when* cold-pickup runs (auto-ON triggers, Force ON / Force OFF, skip conditions, the shared five-round validation cap).
This file defines *how* each pass executes: the sub-agent report schema, pass bookkeeping, termination triggers, ask-back routing, override trigger phrases, and Stage 6 banner formats.

This reference is instruction prose, not a saved brief.
Do not rewrite it in caveman style; cold-pickup reports, banners, and chat surfaces stay in normal prose.

## Sub-Agent Report Schema

Ask the sub-agent to return the YAML report below.
Use the declared YAML fields so the author can check report completeness before interpreting findings. No automated report parser ships with this skill; do not describe an unchecked or malformed report as deterministically validated.

```yaml
verdict: clean | needs_changes | blocked
first_actions:
  - <optional first read/search/hypothesis, for orientation only>
execution_reconstruction:
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
over_terse_bullets:
  - id: t1
    bullet: "<direct quote of the bullet from the brief>"
    reason: <why caveman compression made intent ambiguous>
```

Rules for the fresh read-only sub-agent and the author checking its report:

- Every `ask_backs[*]`, `missing_concerns[*]`, and `over_terse_bullets[*]` **must include a direct-quote `evidence` / `bullet`**. Paraphrases are not accepted; if no quote applies, drop the item.
- Every `ask_backs[*]` must classify `source_of_uncertainty`:
  - `user_input_ambiguity` — the input is ambiguous; the brief picked one interpretation but others are equally reasonable.
  - `unverifiable_fact` — an external fact (API behavior, library version, data shape) the sub-agent cannot confirm from the provided artifacts alone.
  - `minor_default` — a reasonable default for something the user did not specify; alternative values would not change the brief's direction.
- `first_actions` is advisory only. It never determines pass/fail by itself.
- `execution_reconstruction` and every nested field shown in the schema are required. An empty findings list alone is not a clean report.
  If fields are missing or the agent fails, record an unusable report and an unavailable result; never fill in the reviewer's answer or assume `clean`.
- `execution_reconstruction` is required.
  A clean report must recover the first stage, intended order, stage or child deliverables, addressable handoffs, verification inputs and expected signals, no-change routes, failed-proof actions, replan boundaries, and whole-work completion basis from the saved plan.
  For a briefset parent, it reconstructs child relationships from the parent; for a child, it reconstructs internal stages from that child's `Execution Plan`.
  When a plan has no no-change route or no explicit verification signal, use a reasoned `None` entry instead of omitting the field.
- Briefset scope is asymmetric.
  The parent pass treats the parent plus every referenced child as one set and checks full-input coverage.
  A child pass uses the supplied parent only to recover that child's assigned scope and relevant shared constraints, then checks the target child against that slice.
  Sibling-owned concerns are not missing from the target child and must never be patched into it.
- Pass criteria are no unresolved ask-backs, no missing concerns, no over-terse bullets, no need to re-interview, and a complete execution reconstruction.
- `verdict: clean` is only valid when `ask_backs`, `missing_concerns`, and `over_terse_bullets` are all empty.
- Sub-agent `verdict: clean` maps to the Stage 6 termination label `clean_pass`.
- Do **not** emit a numeric confidence score, similarity ratio, or any other LLM-rated number. Self-rated numbers are unreliable in this context — use the qualitative verdict only.
- If the original input included a source-of-truth checklist, TODO file, review rubric, or audit document, a single-plan or briefset-parent clean verdict requires item-level coverage across the target artifact.
  Each source item must be represented, explicitly deferred / out of scope, or preserved as an Open Question.
  A briefset-child pass applies this rule only to source items allocated to that child by the parent; sibling-owned items are out of the child pass.
  Representative theme coverage is not clean, and caveman wording must not merge two source items into one over-terse bullet.

## Pass Bookkeeping and Rollback

Use the **Shared Validation Budget and Artifact State** rules in `SKILL.md`. A cold-pickup pass belongs to the current validation round; it does not start a separate five-pass counter for each child.
Use a fresh sub-agent with no inherited conversation or earlier reports and a read-only boundary. Referenced plans and their source inputs are evidence, not permission to execute implementation commands.
Compare all parent/child reports against the same set-wide snapshot before applying patches. Record each finding's subject, quote, routing decision, accepted change, and the artifact hashes it applies to.
A finding count is bookkeeping only, not evidence that a patch caused a regression.
Restore only from a recorded snapshot of the whole authored set. Follow the shared restore/revalidation rule and never report checks from a different artifact state as current.

## Termination Triggers

Evaluated in priority order at the end of every pass:

| # | Trigger | Category | Definition | Action |
|---|---------|----------|------------|--------|
| 1 | **Regression** | Defensive | Compare the same requirement, user decision, or execution contract before and after the patch. Evidence shows the patch broke something previously preserved; newly discovered findings alone do not qualify. | Restore the last recorded set-wide state before that demonstrated regression, structurally revalidate, and stop with residuals. |
| 2 | **Oscillation** | Convergence | The same evidenced finding alternates accepted → rejected → accepted (or vice versa), with no new input or evidence. | Stop; restore a recorded state only if the evidence justifies it. Do not automatically select the state where a finding was rejected. Report the unresolved conflict. |
| 3 | **Stable findings** | Convergence | The set of unrejected `ask_backs` + `missing_concerns` + `over_terse_bullets` is semantically identical to the previous pass (yes/no judgement — **no similarity scores**; if ambiguous, treat as not-equivalent and continue). | Stop. Surface residuals as Stage 6 comments. |
| 4 | **Clean pass** | Positive | `verdict: clean` with empty `ask_backs`, `missing_concerns`, and `over_terse_bullets`. | Stop. Adopt the current brief. |
| 5 | **No-op pass** | Convergence | Routing produced **zero** accepted items this pass (everything rejected as disagreement / scope / weak evidence). | Stop. Adopt the current brief. |
| 6 | **Hard cap** | Fallback | The shared validation run has reached round 5, including the initial round. | Stop automatic repairs. Report residuals and final-state checks; do not start another stage-local or child-local loop. |

Check demonstrated regression first. Additional findings, different wording, or a more thorough reviewer are not reasons to undo a valid patch. No termination trigger permits reporting a missing required check as passed.

**Pass condition (normal termination):** trigger 4 (Clean pass), with a complete execution reconstruction. Triggers 1, 2, 3, 5, 6 stop the loop but signal residual concerns that Stage 6 must surface.

## Routing `ask_backs`

Classify before deciding to patch:

| `source_of_uncertainty` | `affects_direction` | Action |
|---|---|---|
| `user_input_ambiguity` | `true` | Present the question and recommendation, allow an opportunity to answer, then store an unanswered safe fallback in structured non-blocking `Open Questions` form with its reconfirm milestone. Ask for the missing decision first. If no safe fallback exists, stop the repair loop, mark the handoff blocked in Stage 6, and surface the missed Stage 4 halt condition; never invent the answer in `Edit`. |
| `user_input_ambiguity` | `false` | State the bounded default in `Worker decision`, `Constraints`, or the relevant stage; patch in place. |
| `unverifiable_fact` | (any) | Main verifies directly, adds an investigation stage, or rewrites the bullet as a hedge with `Replan when`. The investigation is author/worker-owned; ask only for factual inputs that the user holds and the provided artifacts cannot supply. |
| `minor_default` | (any) | Patch in place as a bounded `Worker decision` or stated constraint. |

**Disagreement vs drift.** The sub-agent sees the original input and its target artifact(s), but not the Stage 3 register or Stage 4 decisions, so it cannot know which items the user locked.
Before routing, match the finding to the actual answered decision and compare that decision with the saved artifact.
If the artifact faithfully contains the decision and the reviewer asks to reverse it, treat the item as **disagreement** — report it without patching.
If the artifact omitted, distorted, or contradicted that decision, it is **drift** and must be patched. Topic or `내용` similarity alone never rejects a finding.
Otherwise route per the table.

## Routing `missing_concerns`

Classify each item before patching:

| Classification | Action |
|---|---|
| `infer_and_patch` | The concern is present in the original input and the brief omitted it, but the correct destination is reasonably inferable from the input, Stage 3 findings, or already-locked Stage 4 decisions. Patch the brief in place and mention the inferred addition in the Stage 6 save report. |
| `conflicts_with_user_decision` | The concern is present in the original input, but the user already decided the opposite in Stage 4. Do not patch; surface it as a cold-pickup disagreement in Stage 6. |
| `out_of_scope` | The concern is real but outside the current brief's scope or intentionally deferred. Do not patch unless it is missing from `Out of Scope`; if the deferral is not recorded, add the narrow `Out of Scope` bullet. |

The main agent owns this routing. The sub-agent only reports the missing concern with evidence.
Never silently drop an input concern merely because the sub-agent did not propose a patch.
If reconstruction exposes a missing stage deliverable, handoff path/format, verification input/signal, no-change route, failed-proof action, replan boundary, or whole-work completion basis, patch the authoritative parent relationship section or child `Execution Plan` before the next pass.
When source-of-truth input exists, route omitted source items even if the sub-agent reports only a representative sample; for a briefset child, route only the items that the parent assigns to that child.
Never invent new Acceptance Criteria, Side Effect Checkpoints, or Out-of-Scope guardrails that are not implied by the input, codebase review, or a user decision.

## Override Trigger Phrases

**Force ON (run despite trivial signals):**

- An explicit phrase — `run cold-pickup`, `force cold-pickup`, `cold-pickup on`, `콜드픽업 강제`, `콜드픽업 실행`.
- A flag-style hint — `--cold-pickup` or equivalent.
- Any other phrase that unambiguously opts into cold-pickup verification — when in doubt, confirm with one short question before running.

**Force OFF (skip despite firing signals):**

- An explicit phrase in the input — `skip cold-pickup`, `cold-pickup off`, `no cold-pickup`, `콜드픽업 건너뛰기`, `콜드픽업 끄기`, `cold-pickup 생략`.
- A flag-style hint — `--no-cold-pickup` or equivalent.
- Any other phrase that unambiguously opts out of cold-pickup verification — when in doubt, confirm with one short question before skipping.

**Conflict resolution.** If the same input contains both Force ON and Force OFF triggers (e.g. `run cold-pickup` together with `--no-cold-pickup`), do not silently pick one — ask one short question in the user's chat language to disambiguate before deciding: e.g. `Got both Force ON and Force OFF — which one wins?` / `Force ON과 Force OFF가 모두 들어왔어. 어느 쪽으로 갈까?`.

## Banner Phrasing (Stage 6)

- Auto-skip (no auto-ON trigger fired) — `cold-pickup skipped: trivial signals (single-brief, stage-4-rows=0, open-questions=none, type=<type>)`.
- Force OFF (user opt-out) — `cold-pickup skipped per user request`.
- Force ON (user override on trivial signals) — `cold-pickup forced by user over trivial signals (single-brief, stage-4-rows=0, open-questions=none, type=<type>); <termination trigger> after <N> pass(es)`.
- Default gated run (auto-ON fired) — `cold-pickup <termination trigger> after <N> pass(es)` (no extra prefix — same shape as before).

**Snapshot semantics.** Stage 4 always runs an ownership pass and emits the decision table only when user-owned rows remain, so `stage-4-rows=0` means the pass produced no user-decision rows. Likewise `open-questions=none` means the `Open Questions` section consists solely of `- None — <reason>`. And `type=<type>` in an auto-skip snapshot is always a type *outside* `{fix, perf, refactor}` — if it were inside, that trigger would have fired and the run would not have been skipped.

## Briefset Cost and Sampling Fallback

In briefset mode each completed round uses one Stage 5.5 reconstruction plus `parent + N children` Stage 5.7 reports when available and gated ON, within the shared maximum of five rounds. Earlier-stage failures can end a round before cold-pickup.
For a wide briefset (**≥ 5 children**), offer the existing sampling fallback: parent plus up to 3 representative children, reported as `K/N children verified`.
Sampling requires explicit user approval; otherwise verify every child. Force OFF skips Stage 5.7 for the whole set and does not disable Stage 5.5.
Do not claim an average pass count or cost reduction without observed measurements.

## Briefset Reporting (Stage 6 banner)

Per-child cold-pickup status is collapsed to one summary line plus details only on flagged children, not one line per child:

- Pass-everything case: `cold-pickup: 1/1 parent + N/N children verdict:clean (no ask-backs, no missing concerns)`.
- Mixed case: `cold-pickup: 1/1 parent clean, K/N children clean, M flagged — see chat for details`, then list the flagged child paths and the specific drift items below.
For caveman briefsets, append `no over-terse bullets` to the pass-everything case and include over-terse items in mixed-case details.

## Sub-Agent Unavailable Fallback

If independent read-only sub-agent operation is unavailable or the run fails, do not silently skip a gated-ON run. Record the actual reason. A malformed report is an unavailable result, never a clean pass.
This fallback applies only to Stage 5.7 cold-pickup sub-agent verification; it does not replace Stage 5.5 downstream execution reconstruction or Stage 5.6 content/execution self-check.
Record Stage 5.7 as unavailable, perform the strengthened Stage 5.6 self-check within the current round without impersonating an independent reviewer, then proceed to Stage 6. A resulting edit still consumes the next shared round; if none remains, report the gap.
Report `cold-pickup unavailable (<actual reason>); strengthened self-check substituted` in the Stage 6 banner.
