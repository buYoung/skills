# Cold-Pickup Verification (Stage 5.7) — Execution Rules

Loaded when the Stage 5.7 gate fires or the user forces cold-pickup.
`SKILL.md` Stage 5.7 defines *when* cold-pickup runs (auto-ON triggers, Force ON / Force OFF, skip conditions, the 5-pass hard cap).
This file defines *how* each pass executes: the sub-agent report schema, pass bookkeeping, termination triggers, ask-back routing, override trigger phrases, and Stage 6 banner formats.

This reference is instruction prose, not a saved brief.
Do not rewrite it in caveman style; cold-pickup reports, banners, and chat surfaces stay in normal prose.

## Sub-Agent Report Schema

Ask the sub-agent to return the YAML report below.
Free-form prose is not accepted — the report is parsed deterministically.

```yaml
verdict: clean | needs_changes | blocked
first_actions:
  - <optional first read/search/hypothesis, for orientation only>
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

Rules enforced on the sub-agent:

- Every `ask_backs[*]`, `missing_concerns[*]`, and `over_terse_bullets[*]` **must include a direct-quote `evidence` / `bullet`**. Paraphrases are not accepted; if no quote applies, drop the item.
- Every `ask_backs[*]` must classify `source_of_uncertainty`:
  - `user_input_ambiguity` — the input is ambiguous; the brief picked one interpretation but others are equally reasonable.
  - `unverifiable_fact` — an external fact (API behavior, library version, data shape) the sub-agent cannot confirm from the two inputs alone.
  - `minor_default` — a reasonable default for something the user did not specify; alternative values would not change the brief's direction.
- `first_actions` is advisory only. It never determines pass/fail by itself; the pass criteria are no unresolved ask-backs, no missing concerns, no over-terse bullets, no need to re-interview, and enough completion criteria to know when the work is done.
- `verdict: clean` is only valid when `ask_backs`, `missing_concerns`, and `over_terse_bullets` are all empty.
- Sub-agent `verdict: clean` maps to the Stage 6 termination label `clean_pass`.
- Do **not** emit a numeric confidence score, similarity ratio, or any other LLM-rated number. Self-rated numbers are unreliable in this context — use the qualitative verdict only.
- If the original input included a source-of-truth checklist, TODO file, review rubric, or audit document, a clean verdict requires item-level coverage.
  Each source item must be represented in the brief, explicitly deferred / out of scope, or preserved as an Open Question.
  Representative theme coverage is not clean, and caveman wording must not merge two source items into one over-terse bullet.

## Pass Bookkeeping and Rollback

- At the start of every pass, snapshot the currently saved brief to a scratch copy outside the repository (e.g. `cp docs/briefs/<file>.md "${TMPDIR:-/tmp}/<file>.pass-N.bak"`), so the Regression and Oscillation triggers below can restore a previous pass mechanically instead of reconstructing it from memory.
- Keep a three-line scratch note per pass — pass number, unrejected finding count, accepted patch count — so termination triggers are evaluated from records, not recall.
- Delete the snapshots and notes when the loop terminates. Never stage or commit them.

## Termination Triggers

Evaluated in priority order at the end of every pass:

| # | Trigger | Category | Definition | Action |
|---|---------|----------|------------|--------|
| 1 | **Regression** | Defensive | This pass's report has *more* unrejected `ask_backs` + `missing_concerns` + `over_terse_bullets` than the previous pass. | Roll back the brief to the previous pass's snapshot, stop. |
| 2 | **Oscillation** | Convergence | The same finding has been accepted → rejected → accepted (or vice versa) across passes (uses the rejection log from routing). | Adopt the brief from the pass where the oscillating finding was last rejected, stop. |
| 3 | **Stable findings** | Convergence | The set of unrejected `ask_backs` + `missing_concerns` + `over_terse_bullets` is semantically identical to the previous pass (yes/no judgement — **no similarity scores**; if ambiguous, treat as not-equivalent and continue). | Stop. Surface residuals as Stage 6 comments. |
| 4 | **Clean pass** | Positive | `verdict: clean` with empty `ask_backs`, `missing_concerns`, and `over_terse_bullets`. | Stop. Adopt the current brief. |
| 5 | **No-op pass** | Convergence | Routing produced **zero** accepted items this pass (everything rejected as disagreement / scope / weak evidence). | Stop. Adopt the current brief. |
| 6 | **Hard cap** | Fallback | Pass count reached 5. | Stop. Surface residuals as Stage 6 comments. |

Regression is evaluated first because rolling back must outrank optimistic "one more pass might help" instinct. Hard cap is the fallback — not a preferred outcome.

**Pass condition (normal termination):** trigger 4 (Clean pass). Triggers 1, 2, 3, 5, 6 stop the loop but signal residual concerns that Stage 6 must surface.

## Routing `ask_backs`

Classify before deciding to patch:

| `source_of_uncertainty` | `affects_direction` | Action |
|---|---|---|
| `user_input_ambiguity` | `true` | Surface in `Open Questions` for the user — chat-only while the brief is in flight, decision-table row when already saved. Never invent the answer in `Edit`. |
| `user_input_ambiguity` | `false` | State the default assumption in the relevant section; patch in place. |
| `unverifiable_fact` | (any) | Main verifies directly (codebase check, doc read) or rewrites the bullet as a hedge. **Never ask the user** — this is the main agent's job. |
| `minor_default` | (any) | Patch in place with the assumption stated. |

**Disagreement vs drift.** The sub-agent sees the original input and the brief but not the Stage 3 register or Stage 4 decisions, so it cannot know which items the user locked.
Before applying the routing table above, if an ask-back's subject matches the `내용` of a row in the Stage 4 decision table the user already answered, treat it as **disagreement** — chat-only comment, no patch.
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
When source-of-truth input exists, route omitted source items even if the sub-agent reports only a representative sample.
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

**Snapshot semantics.** Stage 4 always runs as a user decision table (see `## Modes` in SKILL.md), so `stage-4-rows=0` in the auto-skip snapshot always means *Stage 4 ran and produced no user-decision rows*, never "Stage 4 was skipped". Likewise `open-questions=none` means the `Open Questions` section consists solely of `- None — <reason>`. And `type=<type>` in an auto-skip snapshot is always a type *outside* `{fix, perf, refactor}` — if it were inside, that trigger would have fired and the run would not have been skipped.

## Briefset Cost and Sampling Fallback

In briefset mode the total spawn count is `parent + N children`, multiplied by up to **5×** in the worst case when every file hits the hard cap.
In practice most files terminate earlier (Clean pass on pass 1, or Stable findings / No-op on pass 2–3), so the average is closer to `1.5×–2×`.
For a wide briefset (**≥ 5 children**), offer the user the sampling fallback before running: verify the parent plus up to 3 representative children, and report the banner as `K/N children verified`.
Sampling runs only with explicit user approval; the default remains parent + every child, and Force OFF skips the whole set.

## Briefset Reporting (Stage 6 banner)

Per-child cold-pickup status is collapsed to one summary line plus details only on flagged children, not one line per child:

- Pass-everything case: `cold-pickup: 1/1 parent + N/N children verdict:clean (no ask-backs, no missing concerns)`.
- Mixed case: `cold-pickup: 1/1 parent clean, K/N children clean, M flagged — see chat for details`, then list the flagged child paths and the specific drift items below.
For caveman briefsets, append `no over-terse bullets` to the pass-everything case and include over-terse items in mixed-case details.

## Sub-Agent Unavailable Fallback

If the host environment cannot spawn sub-agents, do not silently skip a gated-ON run.
This fallback applies only to Stage 5.7 cold-pickup sub-agent verification; it does not replace Stage 5.5 downstream interpretation or Stage 5.6 content self-check.
Record Stage 5.7 as unavailable, re-run the Stage 5.6 self-check with fresh eyes against only the original input plus the saved brief, then proceed to Stage 6.
Report `cold-pickup unavailable (no sub-agent support); strengthened self-check substituted` in the Stage 6 banner.
