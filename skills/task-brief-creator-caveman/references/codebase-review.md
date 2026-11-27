# Codebase Review Rules (Stage 3)

`SKILL.md` Stage 3 sets the review purpose, budget, and search strategy.
This file holds the rules for what the review records: active judgement about nearby signals, evidence labels, contract preservation, source-of-truth inputs, what not to do, and the already-satisfied gate that runs before Stage 4.
This reference is instruction prose, not a saved plan; keep it in normal prose.

## Active Judgement

- Let the user's goal drive any extra probing.
  If the first code reads surface a nearby signal that could change the work direction — a dependency, style hook, comment, product doc, older brief, or unused surface that clearly belongs to the same feature — check just enough to decide how it affects the brief.
  Do not turn this into a mandatory repo-wide audit.
- Prefer a reasoned recommendation over asking the user.
  If a nearby signal is relevant but not required for the requested slice, encode the judgment in `Constraints`, `Out of Scope` as `[deferred]`, `Side Effect Checkpoints`, or `Acceptance Criteria`.
  Ask only when the choice changes product behavior, scope, ownership, or acceptance in a way the requester must own.
- Separate implementation completion from user / operator success when both exist.
  Code may already expose a pass condition, event, return value, validator status, or stored state that says "done"; the user-facing or operator-facing success may be different.
  Capture both when they matter: put the existing pass condition in `Current State (As-Is)` / `Side Effect Checkpoints`, and put the intended observable outcome in `Desired Outcome (To-Be)` / `Acceptance Criteria`.
- If a nearby signal is weak, mention it in the Stage 6 save report instead of bloating the brief.
  The brief stays executable; the report can carry useful "noticed while reviewing" context in normal prose.

## Evidence Discipline

- Mark load-bearing findings as **confirmed** when the codebase review directly verified them.
  A confirmed finding cites the file and a stable locator: section heading, function / class name, validator message, command output, or nearby quoted token.
  Line numbers are useful as secondary hints, but do not rely on line numbers alone because they drift after edits.
- Mark risk statements as **inferred** when they describe likely downstream behavior rather than a fact already present in a file.
  Name what would confirm the inference, such as a validator fixture, a targeted test run, or a specific command.
- Do not write an inferred risk as if it were a confirmed defect.
  Caveman output may sound terse, but the wording must still let the downstream agent tell evidence from judgment.
- Prefix every load-bearing `Current State (As-Is)` bullet with `[confirmed]` or `[inferred]`.
  Caveman keeps the evidence token and stable locator or probe explicit.
  The validator checks the label shape only; Stage 5.6 and human review own the truthfulness of the classification.

## Contract Discipline

- Name the existing contracts that must keep speaking the old shape while the change lands.
  Contracts can be public APIs, persisted ids, database rows, event names, config keys, file formats, CLI flags, i18n keys, analytics events, generated schemas, or cross-process payloads.
- Put contract-preservation facts in `Constraints` or `Side Effect Checkpoints`, not as vague `Out of Scope` filler.
  Good: `- [ ] Existing saved sessions with status "pending" still deserialize.`
  Bad: `- [ ] Do not break compatibility.`
- If the requested outcome requires changing a contract, surface the compatibility choice in Stage 4 unless the user already explicitly approved the break.

## Source-of-Truth Inputs

When the user provides a checklist, TODO file, review rubric, audit notes, or any document as the source of truth, do not turn it into a representative summary.

- Treat each listed item as a required concern until it is mapped, explicitly deferred / out of scope, or represented as a non-blocking user-owned Open Question with a safe default.
- Preserve the source's own dimensions, such as named variants, files, examples, sections, or checklist groups.
  Do not collapse them unless the user asks for a summary rather than an executable brief.
- Use searches only for literal terms that come from the user's source document or the target files being reviewed.
  Do not invent generic banned-pattern searches unless the user, repository rules, or source document defines those patterns.
- The saved brief does not need to expose an internal ledger, but Stage 5.6 must be able to trace each source item to a concrete bullet or checklist item.
  Caveman wording must not merge two source items into one bullet just to sound shorter.

If the source document is long, keep a private coverage ledger during review.
The ledger does not need to be saved, but every source item must end as one of: in scope, out of scope / deferred, execution stage, acceptance criterion, side-effect checkpoint, related file, constraint, or structured non-blocking open question.

## Do Not

- Read entire large files when symbolic / targeted-range reads suffice.
- Chase tangential code just to pad the brief.
  If it does not tighten `Current State (As-Is)` or `Related Files / Entry Points`, skip it.
- Make architectural claims the code does not support.
  If uncertain, label it `[inferred]` and route confirmation into an investigation stage or `Replan when` boundary.

## Already-Satisfied Gate

Before Stage 4, compare the full requested outcome and acceptance boundary against current code plus current verification signals.

- If all requested outcomes are confirmed, all acceptance checks already hold, and no edit, integration, migration, or evidence-producing work remains, create no plan.
  Report `no-work-needed` in normal chat prose in the user's language with the inspected paths, verification action, and observed signal, then stop.
- If the user explicitly asked for a saved verification record despite the already-satisfied state, create a verification-only plan that expects no edits and records the no-change evidence route.
  Its first stage must also say what happens if the proof fails: stop dependent work, return to the owning plan, activate bounded correction plus re-verification work, then re-run the briefset topology and handoffs before continuing.
- If only part of the outcome is already satisfied, keep the remaining work and make the no-change branch explicit instead of directing an unconditional edit.
- In briefset mode, re-run topology after this gate: zero active children means `no-work-needed`, one means single-plan mode, and two or more retain briefset mode. Follow `briefset.md` for the child and handoff rules.

This outcome is called `no-work-needed`.
