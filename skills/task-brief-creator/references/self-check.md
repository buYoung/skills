# Self-Check Checklists (Stage 5 and Stage 5.6)

`SKILL.md` decides when each checklist runs, the two-pass self-check budget, and how failures are reported. This file holds the checklist items:

- [Pre-Save Checklist](#pre-save-checklist) — before invoking `Write` in Stage 5.
- [Stage 5.6 Content and Intent Checklist](#stage-56-content-and-intent-checklist) — after the structural validator, against the file as saved on disk.
- [Post-Run Checklist](#post-run-checklist-before-the-stage-6-banner) — immediately before the Stage 6 banner.

For briefset mode, `briefset.md` adds the parent-specific Stage 5.6 checks.

---

## Pre-Save Checklist

Self-check before invoking `Write` in Stage 5. The structural validator catches format errors after the fact; this list catches content gaps it cannot see.

- [ ] Filename matches `YYYY-MM-DD-<type>-<slug>.md`.
- [ ] `<type>` is one of the ten Conventional Commits types.
- [ ] Title on line 1 matches `# [<type>] <title>`.
- [ ] `Current State (As-Is)` and `Desired Outcome (To-Be)` are both populated and distinguishable.
- [ ] Every load-bearing current-state bullet starts with `[confirmed]` or `[inferred]`; confirmed facts cite stable evidence and inferred findings name what will confirm them.
- [ ] Existing contracts that must not change are named concretely: ids, keys, event names, API shapes, schemas, file formats, persisted values, commands, or generated outputs.
- [ ] If internal completion and user / operator success differ, both are represented in the brief and verification does not confuse one for the other.
- [ ] If type is `fix` / `perf` / `refactor`, the type-conditional section (`Reproduction` / `Baseline Measurement` / `Behavior Contract`) is present and populated — `- N/A — <reason>` if genuinely none.
- [ ] `Out of Scope` has at least one specific entry (or an explicit "None — self-contained." with rationale). Prefix every top-level exclusion with `[hard]` for must-not-touch guardrails or `[deferred]` for follow-up work; a sole `- None — <reason>` is the alternative.
- [ ] Broad review findings have been triaged into must-fix / check-while-here / deferred; the brief does not ask the downstream agent to fix every valid concern discovered during review.
- [ ] If the brief asks the downstream agent to prove a validator or workflow bug, the verification path uses existing scripts or temporary scratch artifacts only when repository / user rules allow them.
- [ ] `Acceptance Criteria` are measurable (checkable, not aspirational).
- [ ] `Related Files / Entry Points` entries are existing repo paths, verified references, or confirmed proposed paths. Paths under inline-code that are not yet created carry the exact literal token `(proposed)` immediately after that path so the structural validator does not flag them as fabricated — variants like `(proposed edit)` are not recognized, and a marker elsewhere in the line does not skip path validation. At least one top-level entry contains a path-shaped inline-code token; plain-text paths do not count. Each entry routes the agent's first read or first edit, not just "related file" context.
- [ ] `Execution Plan` has consecutive `### Stage N — <name>` stages; every stage contains `Starts when`, bounded `Work`, `Deliverable`, indented `Ends when` checks, `Handoff`, and `Replan when` in order.
- [ ] Each stage handoff supplies the next stage's start, and stage-local `Ends when` checks are distinct from whole-work `Acceptance Criteria` evaluated after all stages and side-effect checks.
- [ ] `Open Questions` contains only structured non-blocking user decisions in `- [non-blocking] <question> — Default: <safe fallback>; Reconfirm before: <stage or milestone>` form, or `- None — <reason>` after one active judgement pass.

---

## Stage 5.6 Content and Intent Checklist

The brief is a work instruction, not a summary. Any concern that existed in the input must survive into the brief — possibly reshaped into the right section, never silently dropped. Run this checklist against the saved file plus the original input and the Stage 3 / Stage 4 findings:

- [ ] **Reader-centred writing:** apply the reader check in `plain-language.md` to the saved artifact. The required information is easy to locate, the action and conditions are clear, and the next step is usable; authoring tools and workflow narration do not appear in the plan.
- [ ] **Intent fidelity:** read the saved file as a stranger would and compare it with the original input and the answered Stage 4 decisions. The work purpose is the same; the scope is neither materially wider nor narrower; the first stage and entry points point where the input points; every user constraint, exclusion, and acceptance threshold survives; the brief assumes no work the input did not intend. A user-locked Stage 4 decision counts as intent even when it differs from the raw input.
- [ ] **Input coverage:** every distinct concern named in the input, including referenced spec section headings that change the coding route, maps to at least one bullet or stage somewhere in the brief (In Scope, Out of Scope, Related Files, Execution Plan, Constraints, Side Effect Checkpoints, Acceptance Criteria, or structured non-blocking Open Questions, depending on the concern's shape). If a spec section is intentionally not implemented now, it appears in `Out of Scope` as `[hard]` or `[deferred]`, or in `Open Questions` only when a non-blocking user decision has a safe default. Two unrelated implementation or verification obligations are never merged into one bullet.
- [ ] **Source-of-truth coverage:** if the user supplied a checklist, TODO file, review rubric, audit notes, or other source-of-truth document, every listed item is represented in the saved brief, explicitly deferred / out of scope, or saved as a structured non-blocking user question. Representative theme coverage is not enough.
- [ ] **Scope triage:** every discovered concern is either must-fix in this brief, a tightly coupled check, explicitly deferred / out of scope, or left for a user decision. The brief does not turn a broad review into an unbounded implementation task.
- [ ] **Stage 3 coverage:** every primary entry point or major affected area surfaced during the codebase review appears in `Related Files / Entry Points`, and every technical uncertainty is resolved or routed into an investigation stage, `Worker decision`, or `Replan when` boundary.
- [ ] **Contract preservation:** existing contracts discovered in Stage 3 that must not change are named in `Constraints`, `Side Effect Checkpoints`, or `Acceptance Criteria`; compatibility-sensitive changes are not hidden behind generic wording.
- [ ] **Success split:** when internal completion and user / operator success are different, both are represented; the brief does not treat an event firing, validator passing, or state transition as proof that the user's goal was achieved unless that is actually the goal.
- [ ] **Section depth:** no section was reduced to a single bullet when the input or Stage 3 findings contain multiple distinct concerns for it. Sections expand to fit the work; they are not capped.
- [ ] **No content compression:** no bullet was shortened by dropping qualifiers, quantities, units, thresholds, versions, environment conditions, or ordering words (`only on cold start`, `≤ 5KB gzipped`, `iOS Safari 17+`, `after move end`). "Executable, not discursive" is a *prose* rule, not a *content* rule.
- [ ] **Evidence clarity:** every load-bearing current-state bullet uses `[confirmed]` or `[inferred]`; confirmed facts cite stable evidence, inferred risks name what will confirm them, and line numbers are not the only locator.
- [ ] **Execution continuity:** Stage 1 has a concrete precondition; stage numbers are consecutive; every stage has a bounded outcome, deliverable, local completion checks, explicit handoff, and replan boundary; each handoff gives the next stage what its `Starts when` requires.
- [ ] **Already-satisfied discipline:** the plan does not force an edit when current evidence already satisfies the requested outcome; full satisfaction exited as `no-work-needed` unless the user explicitly requested a verification record, partial satisfaction has a bounded no-change route, and a failed proof stops dependents and names the correction/re-verification owner.
- [ ] **Verification concreteness:** every named verification action comes from repository evidence or is a bounded inspection, identifies its exact input/target, and states an observable expected signal. When success means no matches, the plan also identifies the population being checked so an empty or wrong input cannot pass accidentally.
- [ ] **Completion separation:** stage-local completion appears only under `Ends when`; whole-work `Acceptance Criteria` are evaluated after all required stages and side-effect checkpoints finish.
- [ ] **Handoff readiness:** a downstream coding agent reading only the brief can recover the first stage, order, deliverables, handoffs, replan conditions, and whole-work completion judgement without re-interviewing the requester. If a re-interview would be needed, identify the thin section and patch it.
- [ ] **Question discipline:** every `Open Questions` item is genuinely user-owned. Every saved question is non-blocking and names a safe default plus reconfirm milestone; move technical and reversible choices into investigation, `Worker decision`, `Replan when`, constraints, or deferred scope. If `Open Questions` says `None`, the brief has made the necessary calls instead of hiding them.

---

## Post-Run Checklist (before the Stage 6 banner)

Evaluated after Stage 5.6 (and Stage 5.7 when the user requested it) has run, immediately before reporting the Stage 6 banner — these items cannot be checked before `Write`.

- [ ] Stage 5.6 ran against the file as saved on disk, within two passes; a gap left after the budget is reported as incomplete, never as passed.
- [ ] No verification sub-agent was spawned without an explicit user request for cold-pickup.
- [ ] When the user requested cold-pickup, Stage 5.7 ran once per artifact as the reference describes, or the banner names the documented `unavailable` reason; when they did not, the banner reports the checks actually run without an optional-check line.
- [ ] Stage 6 banner reflects what actually ran — no check is reported from an earlier artifact state.
- [ ] Any edit after Stage 5.6, Stage 5.7, or Stage 6 re-ran the structural validator and then Stage 5.6 before the banner was reported.
