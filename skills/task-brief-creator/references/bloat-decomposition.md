# Bloat Decomposition Rules (BDR)

BDR is the **secondary** decomposition layer that runs *after* the briefset primary filter (the "independently executable work unit" rule) has already cleared a candidate child list.
The primary filter answers *"can this work split at all?"*.
BDR answers *"once it can, where exactly do we cut?"*.

A child brief that passes the primary filter can still be bloated — mixing contracts and policies, blocking several execution waves, bundling unrelated failure modes.
The downstream coding agent then inherits a too-fat brief or a wrongly-merged set, and the brief stops being an executable work instruction.
BDR is the judgement layer that prevents that failure mode.

BDR is **not** a structural rule.
The structural validators (`validate_brief.py`, `validate_briefset.py`) already reject empty children, missing sections, and malformed checklists — that is the only machine-checkable side of decomposition.
BDR is what the human or agent author runs in their head before saving.

---

## When to use

Apply BDR only after the primary filter has produced a candidate child list.
Inside that list, evaluate each child against the bloat signals below.

- If a candidate child triggers ≥ 2 bloat signals, run BDR on it.
- If every candidate child triggers ≤ 1 signal, skip BDR — the primary filter is sufficient.
- Never run BDR before the primary filter.
  Splitting a child that has not yet earned its own existence multiplies underspecified briefs.

BDR also applies in **single-brief mode** when the input passes the ambiguity gate but the resulting single brief, once mentally drafted, triggers ≥ 2 bloat signals.
In that case BDR's split rules become a recommendation to switch into briefset mode — surface that recommendation to the user before saving.

---

## Split rules

Each rule has a **Signal** (when to suspect this cut) and a **Correction** (the cut to apply).
Split rules are **priority-ordered (S1 → S5), strongest first**: if S1 fires on a candidate, do not evaluate S2–S5 for that candidate.
Keep-together rules below override every split rule.

### S1 — Contract-First

- Signal: The candidate sits at a wave-graph node that blocks two or more downstream waves because it owns a stable surface (data model, state vocabulary, trait signature, command/event name) that those waves wait on.
- Correction: Lift the contract into its own brief and place it in an earlier wave.
  The contract child unblocks downstream consumers; the policy / algorithm child that consumes the contract iterates without re-touching it.

### S2 — Model vs Pipeline

- Signal: The candidate evolves a data model (struct, schema, persisted shape, state envelope) *and* the pipeline / orchestration / policy that operates on it in the same brief.
- Correction: Split into one model-and-persistence child and one pipeline-and-policy child.
  Model child stabilises the shape; pipeline child wires consumers to the new shape and clarifies migration ordering (model-first vs pipeline-first) instead of hiding it inside one bullet.

### S3 — Lifecycle Boundary

- Signal: The candidate crosses a **temporal pair** of lifecycle stages with different execution times and different failure modes — `capture/restore`, `save/sync`, `build/deploy`, `register/invoke`, `setup/teardown` — and each side has its own verification path.
- Correction: Split by lifecycle stage.
  If both sides share a model, lift that shared model into a separate contract brief (S1) so each lifecycle child can evolve independently.

### S4 — Failure-Mode

- **Same failure reason is a stronger criterion than same files touched.** File conflict is a secondary signal; the failure mode is the essence.
- Signal: The candidate's acceptance criteria mix unrelated failure modes — serialization failure, external-API rejection, race condition, validation error, state-corruption recovery, user-facing copy vs ops alerting — whose mitigation paths diverge.
- Correction: Split along failure-mode boundaries.
  If file conflict remains across the split, resolve it with sequencing or locks, not by re-merging the failure modes.

### S5 — Cross-cutting Isolation

- Signal: The candidate's `Related Files / Entry Points` spans two or more domain directories where one is an obvious side-branch from the main domain (shared registry, i18n, telemetry, feature flags, accessibility, logging, persistence/sync glue).
- Correction: Lift the side-branch (cross-cutting) work into its own brief so other consumers can land against the same surface without forking it.
  The cross-cut child usually becomes a precondition for the feature-specific child.

---

## Keep-together rules

These **override every split rule**.
A candidate cut suggested by S1–S5 must not be made if either keep-together rule applies.

### K1 — Atomic Change Unit

- If two pieces of work, once split, would leave data or state **lost or corrupted** because they were not changed together, they are a single atomic change unit and stay together.
- Signal: splitting forces the downstream agent to repeat the same edit in two children, or leaves the codebase in a non-deployable intermediate state, or breaks a round-trip (write then read) because only one side was updated.
- Examples: storage root + sync snapshot; serde defaults + schema version; migration step + reverse migration; rename + the call-site updates that the rename invalidates.

### K2 — Shared Failure-Path Cohesion

- If two pieces of work share the **same diagnosis path, the same retry policy, the same user-facing error**, splitting them fragments the failure response and they stay together.
- Signal: the operational runbook for "this went wrong in production" would have to reference both children to be useful.
- Examples: a concurrency lock and the execution orchestration it protects; a database write and its compensating undo write inside the same transactional boundary.

K1 and K2 enter the application order at different points:

- **K1 short-circuits before S1–S5.** If the candidate is an atomic change unit, skip the split rules entirely — no S-rule can override that.
- **K2 prunes after S1–S5.** Once S1–S5 produce a candidate cut, walk that cut against K2 and drop it if its two halves share the same failure path.

The asymmetry is intentional: K1 is a property of the *candidate*, so checking it before generating cuts saves work; K2 is a property of each *individual cut*, so it can only be checked after a cut exists.

---

## Bloat detection signals

A candidate child fits BDR when **≥ 2** of the following signals fire simultaneously.
One signal alone is not enough — every non-trivial child trips at least one, so a 1-signal cutoff would over-trigger and force noisy splits.

- **B1 — Conflict hotspots.** The candidate's `Related Files / Entry Points` covers four or more files, or four or more files would be edited under the cut.
- **B2 — Mixed acceptance criteria.** The candidate's acceptance criteria mix items belonging to different execution waves, or items belonging to different failure modes (no shared verification path).
- **B3 — Blocks multiple waves.** The candidate sits as a precondition for two or more downstream children that themselves run in different execution waves.
- **B4 — Hard one-sentence "Exists because".** The candidate's `Exists because` cannot be stated in one sentence without conjunctions like "and / plus / also."
- **B5 — Outsized vs siblings.** The candidate's draft file size is at least 1.5× the median sibling brief size in the same briefset.

Size alone is **not** a split rationale.
B5 is a by-product signal — it only justifies a split in conjunction with one of B1–B4 (the ≥ 2 cutoff enforces this).

---

## Application order

1. **Primary filter.** Confirm the candidate child list already clears the briefset primary filter (the "independently executable work unit" rule).
   If a candidate fails the primary filter, fold it back before applying BDR.
2. **Bloat detection.** For each surviving candidate, count B1–B5 signals.
   Stop if every candidate has ≤ 1 signal.
3. **K1 pre-check.** Before considering any split, ask whether the candidate is an atomic change unit (K1).
   If yes, do not split — even if S1–S5 would suggest it.
4. **S1–S5 in priority order — first match wins.** Evaluate split rules top-down.
   **The first S-rule that fires produces the cut; S-rules below it are not evaluated for that candidate.**
   S1 is the strongest criterion (wave-graph blocker); S5 is the weakest (cross-cutting cleanup).
5. **K2 re-check.** Walk the chosen cut against K2.
   Drop the cut if its two halves share the same failure path.
6. **Apply the surviving cut.** Replace the original candidate with the post-cut children.
7. **Re-run bloat detection** on each new child.
   If a child still triggers ≥ 2 signals, BDR can iterate, but cap iteration depth at **two passes per candidate** (each child has its own iteration budget).
   Beyond that the input is probably too fat to ship in a single briefset and the user should be told.
   As a separate global sanity check: if the post-BDR child count exceeds ~8, surface a "briefset is unusually wide; consider splitting the umbrella" comment to the user — that scale typically signals an under-scoped umbrella, not a successful decomposition.

---

## One-line summary

A brief owns **one contract to stabilise** *or* **one executable behavior** — except when work that must change together to preserve data/state, or that shares the same failure path, must stay inside that brief.
