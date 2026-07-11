# Briefset Mode

`task-brief-creator-caveman` defaults to producing **one implementation work plan per invocation**.
Briefset mode is the alternative path: a **parent execution-management plan** plus N **independently executable child plans**, used when a single task naturally splits into multiple execution contexts.

The saved parent and every saved child use caveman full mode for body prose only.
Their `Open Questions` bodies stay in normal prose, as do Stage 4 tables, Stage 6 reports, and every chat surface.
Both parent and child plans preserve the same facts, bullets, section depth, execution relationships, and completion rules as their normal-mode equivalents; caveman changes register, never content or structure.
Section headers, title lines, child paths, checklist markers, and the Auto-Clarity carve-outs in `caveman-style.md` stay verbatim.

The trigger is **coordination across multiple execution contexts**, not "this work is big".
Independent completion criteria, mixed work types, ordered dependencies, parallelizable waves, or shared conflict hotspots that need coordination — those are the signals.
Distinct entry-point files are supporting evidence only unless they map to independent work units.
If strong coordination signals are absent, stay in single-brief mode no matter how long the input is.

---

## When To Select Briefset Mode

Select briefset mode only when the input describes multiple independently executable work units, not just many edits.
A good quick test: can you write two or more natural child-brief titles, each with its own acceptance criteria and entry point, without inventing scope?
If not, stay in single-brief mode.

Strong selection signals:

- A predecessor's output is a precondition for a successor.
- The user asks for phases, waves, sequential PRs, independently runnable PRs, or explicit parallel work.
- Parallel-execution capability needs to be tracked explicitly.
- Work types are mixed in a way that changes downstream behavior (e.g., a `refactor` child followed by a `feat` child).
- Multiple independently executable subtasks share a common conflict surface — i18n bundles, shared types, schema, route table, top-level config files.
- A single brief would force `Scope`, `Acceptance Criteria`, or `Related Files / Entry Points` to fork into unrelated topics.

Supporting signals, not sufficient alone:

- Many files, many directories, or several related edit points.
- A large file or large codebase area.
- Distinct entry-point files that all serve one cohesive goal.
- Long user input.
- User phrasing like "split this up" without execution-context evidence.

Default to single-brief mode when the work has one goal, one outcome, and one coherent implementation path, even if it touches multiple files.
Examples: one bug fix across five related files; one refactor that needs coordinated updates in several call sites; one feature that naturally touches UI, state, and API glue.

When strong signals are present, select briefset mode and explain the evidence before Stage 2.
When signals are absent, select single-brief mode.
Ask only when the choice depends on a user-owned delivery boundary, independently owned release unit, or scope decision that the code and input cannot settle.

When the target area already contains both single-brief and briefset contracts, review both surfaces even if the user asked about only one visible symptom.
Always check:

- Whether a single-brief rule also applies to child briefs.
- Whether parent validation is intentionally looser than child validation, or whether the difference is a contract gap.
- Whether parent and child filename rules match the validator's actual checks.
- Whether save order resolves final child paths before the parent references them.
- Whether Stage 5.5, Stage 5.6, and Stage 5.7 apply to parent and children in the documented order.

Put only the briefset issues that are necessary for the current work in scope.
Record independent briefset hardening as `[deferred]` when it is real but not required for the requested fix.

### Secondary decomposition (when bloated)

The criteria above answer *"can this work split at all?"*.
They do not answer *"once it can, where exactly do we cut?"*.
That second question is the **Bloat Decomposition Rules (BDR)** layer in `references/bloat-decomposition.md`.

Run BDR only after the primary filter has produced a candidate child list.
If any candidate child triggers two or more of the bloat signals B1–B5 defined in `bloat-decomposition.md`, apply BDR's split rules (S1–S5) and keep-together rules (K1–K2) before locking the decomposition.
Primary filter answers *"can this split at all?"*; BDR answers *"where exactly to cut."*
Do not split because a single child needs several execution stages; stage count is not an execution-context signal or a bloat signal.

**User phrasing is not itself a trigger.** Phrases like "다중브리프", "briefset", "multi-brief", or "split this into multiple briefs" do not by themselves engage briefset mode.
If the user explicitly requests briefset mode but none of the criteria above apply, select single-brief mode and explain that one execution context does not justify a parent.
Ask only if the request also establishes a user-owned delivery boundary that is not visible in the code or input.
A one-child briefset is always a collapse target.

---

## Naming Convention

```text
docs/briefs/YYYY-MM-DD-briefset-<set-slug>.md                        # parent
docs/briefs/YYYY-MM-DD-<type>-<set-slug>-NN-<child-slug>.md          # children
```

- `<set-slug>` — kebab-case, ≤15 chars, names the umbrella initiative.
- `NN` — zero-padded execution-order index (`01`, `02`, …).
  The number hints the intended starting wave but is not authoritative; the parent's `Execution Order` section is.
- `<child-slug>` — kebab-case, ≤15 chars, names the child subtask.
- The combined child slug `<set-slug>-NN-<child-slug>` must remain ≤40 chars so the existing `validate_brief.py` slug check passes.

Enforcement levels:

- The combined slug budget (≤40 chars) is machine-enforced — `validate_brief.py` reports a FAIL when exceeded.
- The set-slug ≤15 limit is advisory, but the validator reports a warning when it is exceeded. A warning makes the overall validation fail, so shorten it before accepting the briefset.
- Child filename consistency with the parent (same date and exact `<set-slug>-NN-<child-slug>` order) is machine-enforced by `validate_briefset.py`.

**Examples:**

```text
docs/briefs/2026-04-30-briefset-checkout-i18n.md
docs/briefs/2026-04-30-feat-checkout-i18n-01-message-keys.md
docs/briefs/2026-04-30-feat-checkout-i18n-02-cart-copy.md
docs/briefs/2026-04-30-fix-checkout-i18n-03-validation-copy.md
```

Filename collisions are resolved with `-v2`, `-v3`, … on the parent and on each child independently — the same rule as single-brief mode.
Do not overwrite existing files.

---

## Parent Brief Template

The parent **manages execution** — it is not itself a work instruction.
Implementation lives in the children.

The template below uses normal prose for readability.
Convert only its saved body-prose values to caveman full mode; keep headings, paths, field labels, checklists, and `Open Questions` in their protected forms.

```markdown
# Brief Set: <title>

## Purpose
- <why this brief set exists — one or two bullets, no implementation detail>

## Child Briefs
- [ ] `docs/briefs/2026-04-30-feat-checkout-i18n-01-message-keys.md` — <child title>; exists because <reason>
- [ ] `docs/briefs/2026-04-30-feat-checkout-i18n-02-cart-copy.md` — <child title>; exists because <reason>

## Execution Order
- Wave 1 — `docs/briefs/2026-04-30-feat-checkout-i18n-01-message-keys.md`: Start: <precondition>; Deliverable: <child output>; Location: `<repo-relative handoff path>` (proposed); Done: <child completion signal>; Handoff: <recipient and what it receives>.
- Wave 2 — `docs/briefs/2026-04-30-fix-checkout-i18n-03-validation-copy.md`: Start: <predecessor deliverable is available>; Deliverable: <child output>; Location: `<repo-relative handoff path>` (proposed); Done: <child completion signal>; Handoff: <join or global verification and what it receives>.

## Dependencies
- Predecessor: `docs/briefs/2026-04-30-feat-checkout-i18n-01-message-keys.md`; Deliverable path: `<repo-relative handoff path>` (proposed); Format: <minimum fields or state shape>; Successor: `docs/briefs/2026-04-30-fix-checkout-i18n-03-validation-copy.md`; Starts when: <consumption precondition>; Verify: `<exact command or bounded inspection>`; Inputs: <concrete input path, fixture, range, or target>; Expected: <observable exit code, output token, state, or threshold>.

## Parallelization
- Can run together: `docs/briefs/<child-a>.md` and `docs/briefs/<child-b>.md` — <independence evidence>. Join when: <both deliverables and required checks are available>.
- Must not overlap: `docs/briefs/<child-c>.md` and `docs/briefs/<child-d>.md` — serialize <owner/order or merge rule> because <shared-state reason>. Join when: <serialized edits are integrated and verified>.

## Conflict Hotspots
- `<path>` — Children: `docs/briefs/<child-c>.md`, `docs/briefs/<child-d>.md`; Access: serialized; Owner: `docs/briefs/<child-c>.md`; Rule: <write order or merge rule>.
- `<path>` — Children: `docs/briefs/<child-a>.md`, `docs/briefs/<child-b>.md`; Access: parallel-safe; Rule: <non-overlapping ownership partition and join rule>.

## Shared Constraints
- <constraint shared by all child briefs, or "None — <reason>">

## Global Acceptance Criteria
- [ ] <set-level completion criterion>
- [ ] <integration-level criterion>

## Open Questions
- <"[non-blocking] <question> — Default: <safe fallback>; Reconfirm before: <stage or milestone>", or "None — <reason>">
```

### Section guidance

- **Purpose** — why the umbrella exists.
  Not what each child does.
- **Child Briefs** — checklist (`- [ ]`).
  The **only** place status lives.
  Every child is one top-level checklist bullet; nested child paths do not count.
  Tick the box when the child is complete.
  The *exists because* clause is a discipline check: if a child cannot articulate why it exists, fold it back into a sibling.
- **Execution Order** — wave-based ordering and the authoritative source for each child's start, deliverable, deliverable location, done signal, and handoff.
  Group siblings that can run together; separate dependent work into a later wave.
  `Done` names an observable child completion signal, not merely "work complete" or "checks pass" without identifying which result is read.
  Use the shown field labels and casing exactly. Put every entry in one top-level bullet, with no prose before or between entries; do not put unquoted semicolons in `Start`, `Deliverable`, or `Done` values because semicolons separate fields.
- **Dependencies** — one fixed predecessor → addressable deliverable → successor edge per bullet.
  Every edge names one repo-relative deliverable path, its minimum format or state shape, the successor start condition, and a reproducible verification action with concrete inputs and an expected signal.
  Keep the edge on one logical bullet, use each shown field label and casing exactly, and do not put unquoted semicolons inside field values; semicolons outside the inline `Verify` action are the fixed field separators.
  Use `(proposed)` immediately after a deliverable path that the work will create.
  Repeat the exact path in the predecessor child's `Deliverable` / `Handoff` and in the successor child's first-stage `Starts when`; a name such as "verified result" without an address is not a handoff.
  When there are no edges, use one `- None — <reason>` bullet; do not list dependency-free children as pseudo-edges.
  Reference only children of this set; never reference another briefset (no recursion).
- **Parallelization** — distinct from `Dependencies`.
  A child can be dependency-free and still be unsafe to parallelize because it edits a shared file.
  Use each child's finalized full `docs/briefs/...md` path, describe exactly one pair per bullet, call out both can-parallel and must-not-parallel cases, and name `Join when` for each pair.
  Never place three children in one pair declaration and never declare the same pair both ways.
  A direct predecessor/successor pair cannot be `Can run together`.
  Short labels or basenames do not establish child membership.
  Put every pair in one top-level bullet with the exact `Can run together:`, `Must not overlap:`, and `Join when:` labels; do not add prose before or between entries.
- **Conflict Hotspots** — concrete paths under shared editing pressure, expressed one child pair at a time.
  Use `Access: serialized` plus a full-path `Owner` and write-order rule when the pair must not overlap.
  Use `Access: parallel-safe` only when the `Rule` names a non-overlapping ownership partition and a join rule.
  A pair cannot be `Can run together` while any hotspot marks that same pair `serialized`.
  List writers, not read-only consumers, in `Children`.
  i18n message bundles, shared schemas, top-level config, route tables, and generated barrel files default to hotspots.
  Put every hotspot in one top-level bullet and preserve the exact `Children:`, `Access:`, `Owner:`, and `Rule:` labels and casing; do not add prose before or between entries.
- **Shared Constraints** — constraints that apply to every child.
  Per-child constraints stay inside the child brief.
- **Global Acceptance Criteria** — set-level "done" criteria, including integration-level checks no individual child can verify alone.
  Each command-based item names the command, complete target/input, and expected exit/output/state; each manual item names the inspected artifact and expected observation.
  For a no-match success, also prove the intended target population was non-empty and fully scanned.
- **Open Questions** — set-level non-blocking user decisions only, using the structured default/reconfirm form.
  Per-child questions live in the child's `Open Questions`, but Stage 4 must still surface user-owned ones during the per-child residuals step of the decision table.

If a section legitimately has nothing, write `- None — <reason>` with a one-line reason rather than leaving the section empty.

---

## Child Brief Rules

- Children follow `references/template.md` exactly — the same nine required H2 sections, same per-section guidance, same writing rules.
- The parent is authoritative for relationships among children; each child's `Execution Plan` is authoritative for stages inside that child.
- Children also follow `references/caveman-style.md`; preserve stage count, field order, checklist depth, and every content obligation while shortening only prose values.
- Children include their own `Acceptance Criteria` (independent), `Side Effect Checkpoints`, and `Open Questions`.
- Child `Open Questions` contains only Stage 4-approved non-blocking user decisions with a safe default and reconfirm milestone.
  Use `- None — <reason>` when no user-owned decision remains.
- Children **do not** carry status.
  Status is parent-only.
- Children **do not** spawn further children.
  A child cannot become a parent.
  If a child's scope grows mid-flow, escalate by re-planning the parent rather than nesting.
- A child must be executable on its own.
  If a downstream agent reading only the child brief cannot start work, the child is missing context that should not have been hidden in the parent.
- Every child stage adds this briefset-only verification field immediately after `Deliverable`:

  ```markdown
  - Verify: `<exact command or bounded inspection>`; Inputs: <concrete path, fixture, range, or target>; Expected: <observable exit code, output token, state, or threshold>
  ```

  Do not invent a command the repository does not support; use a bounded inspection and name its input and expected observation instead.
- Every child's first stage adds these fields after `Work` and before `Deliverable`:

  ```markdown
  - No-op when: <observable condition proving no edits are needed, or None — <reason>>
  - No-op handoff: <recipient receives evidence at `<repo-relative path>`, or None — <reason>>
  ```

  A valid no-change route still produces addressable evidence and tells the parent whether successors continue, skip, or replan.
  For verification-only or evidence-only child, `Replan when` names failed proof and next action: stop successors, return to parent, activate bounded correction plus re-verification work, and recalculate topology and handoffs before resume.
  If a no-change route is impossible, use the reasoned `None` form for both fields.
- For every parent dependency edge, repeat the exact deliverable path in a producer `Deliverable`, `Handoff`, or `No-op handoff` field and in the successor's first-stage `Starts when` field.
  The producer states the minimum format; the successor states what it requires before starting.

---

## Workflow Adaptations

The single-brief stages in `SKILL.md` still apply.
The diffs:

### Stage 1 — Ambiguity Gate

After scoring the four anchors, also check the selection criteria above.
If the input clearly maps onto multiple execution contexts, select briefset mode before Stage 2 and record the evidence.
If topology depends on a user-owned delivery or scope boundary, ask that underlying decision instead of asking the user to choose an output format.
The anchor halt rule is unchanged — an underspecified briefset request halts just like an underspecified single-brief request.

### Stage 2 — Work Type Selection

The parent has no `Work Type` section — skip type selection for it.
Determine the type per child from the input and codebase.
Mixed types across children is an expected, supported case; do not flatten them to a single type just to keep the set "consistent".

### Stage 3 — Codebase Review

Run one combined review pass, but tag findings and uncertainties with the specific parent or child they will land in.
Track user-owned uncertainties as candidate questions during the review.
Route technical unknowns into the affected child's investigation stage, `Worker decision`, or `Replan when`; do not silently resolve or drop them.
Each child's `Related Files / Entry Points` should be a distinct slice — if two children point at the same primary entry point, they probably collapse into one.
Track shared contracts separately from child-local findings.
If an id, key, event, schema, persisted value, generated file, route, command, or payload is used by more than one child or by existing consumers outside the briefset, put that contract in the parent `Shared Constraints` or `Global Acceptance Criteria`, then repeat only the child-specific verification inside the affected child.

Before locking the child list, run an **already-satisfied gate** against current code and current verification signals:

- Remove a candidate child when its full desired outcome and acceptance boundary are already confirmed and it has no remaining edit, integration, or evidence-producing work.
- Move an already-existing predecessor artifact directly into each surviving successor's `Current State` and first-stage `Starts when`; do not retain a child whose only job would be rediscovering it.
- If no active children remain, create no briefset and report `no-work-needed` with the inspected paths, verification action, and observed signal.
- If one active child remains, collapse to single-plan mode.
- If two or more remain, keep briefset mode.
- If the user explicitly requested a saved verification record despite an already-satisfied outcome, keep a verification-only plan and make the no-change route explicit; do not invent edits.
  If proof fails, plan stops successors and gives parent explicit correction, re-verification, topology, and handoff recalculation route. Bare condition not enough.

When only part of a child's requested outcome may already be satisfied, keep the child but give Stage 1 an observable `No-op when` condition and an addressable `No-op handoff`.
This `no-work-needed` result is unrelated to Stage 5.7's `No-op pass` termination trigger.

When reviewing an existing briefset-capable skill or generator, tag findings as one of:

- Parent-only.
- Child-only.
- Shared parent/child contract.
- Validator/documentation mismatch.
- Deferred hardening.

This prevents briefset concerns from disappearing in one run and over-expanding the work in the next.

### Stage 4 — User Decision Table

Stage 4 in briefset mode follows the same user-ownership policy described in `stage-4-interview.md`.
The author locks decomposition, child types, execution order, dependencies, parallelization, and conflict rules when the code and input make them evident.
Put only user-owned decisions into the four-column table (`순번`, `내용`, `수정 추천안`, `근거`) in this order:

1. **User-owned topology constraints** — ask only when independently owned delivery units, release boundaries, or scope ownership would change the child list.
   Each child still carries an *exists because* clause.
   If the candidate child list shows ≥ 2 bloat signals from `bloat-decomposition.md`, apply BDR before tabling decomposition decisions.
   Apply K1 (atomic change unit) **before** generating cuts — K1 short-circuits, so atomic candidates never split.
   Then run S1–S5 on the surviving candidates and apply K2 (shared failure-path cohesion) to prune the resulting cuts.
   See `bloat-decomposition.md` Application Order for the authoritative sequence.
2. **Execution order and parallelization** — add rows only for wave order or parallelization preferences the user owns.
   Probe shared imports / shared files first, then cite the result in `근거`.
3. **Per-child residuals** — only after the topology is locked, table each child's user-owned `Acceptance Criteria` thresholds, `Out of Scope`, and unresolved non-blocking `Open Questions`.
   Technical uncertainty, low-risk wording, local implementation choices, and reversible sequencing choices become an investigation stage, `Worker decision`, `Replan when`, constraint, or author-selected default.

Briefset Stage 4 still respects the carry-over codebase budget.
A parent-level branch probe (e.g., "does `i18n/messages.ko.json` import from any other child's entry point?") counts against the same budget as Stage 3.

### Stage 5 — Save + Validate

Save in this order:

1. Ensure `docs/briefs/` exists.
2. Resolve child filename collisions first, then write each child brief to its final path (so the parent can reference final filenames, not provisional names).

   When writing child plans, populate `Open Questions` only with Stage 4-approved non-blocking user decisions in the structured default/reconfirm form.
   Do not add technical or reviewer-owned questions after the table closes just to fill the section.
   If no such user decision remains, write `- None — <reason>`.

3. Resolve the parent filename collision, then write the parent brief with the finalized child paths.
4. Filename collisions use `-v2`, `-v3`, … on the parent and on each child independently.
5. Run `scripts/validate_brief.py` on each child as a sanity check (optional — the briefset validator covers this transitively).
6. Run `scripts/validate_briefset.py` on the parent.
   It re-runs child structural validation, so a single parent invocation covers the whole set.
   Run the validator from the skill package directory (the directory containing SKILL.md, referred to as `<skill-dir>`):

   ```bash
   python3 <skill-dir>/scripts/validate_briefset.py \
     docs/briefs/<parent-filename>.md
   ```

   When the briefset files live in an isolated artifact directory but their entry-point and handoff paths belong to another checkout, pass that checkout explicitly:

   ```bash
   python3 <skill-dir>/scripts/validate_briefset.py \
     --repo-root <repository-root> \
     <artifact-root>/docs/briefs/<parent-filename>.md
   ```

On exit 1, repair the affected parent or child file and rerun `validate_briefset.py` without asking the user.
If the same structural cause still fails after two repair attempts, leave the files in place and report the residual failure in Stage 6.
Treat exit 2 as an I/O failure and investigate or retry the save.

### Stage 5.5 — Downstream Interpretation Check (briefset)

Run the downstream execution-reconstruction check from `SKILL.md` Stage 5.5 against the **parent briefset file only**.
The sub-agent receives a natural work-start request with the parent path, not each child path, and no original user request or validation rubric.
Its explanation must recover which child starts first, child order, every handoff path and minimum format, each verification input and expected signal, every no-change branch, parallel joins, conflict ownership, and the global completion basis.
If the reconstruction drops a child, changes execution order, misses an addressable deliverable/handoff, loses a no-change route, cannot state a verification input and expected signal, broadens scope, or misses a parent constraint, patch the parent or affected child, re-run `validate_briefset.py`, and re-enter the validation chain at Stage 5.5.
Treat a relationship that became unclear through caveman compression as execution drift; restore normal prose under Auto-Clarity instead of weakening the relationship.

### Stage 5.6 — Content-Level Self-Check (briefset)

Run the self-check from `SKILL.md` Stage 5.6 on the **parent** and on **every child** independently.
Briefset mode adds one parent-specific coverage rule:

- **Parent decomposition coverage:** every input-implied execution context maps to a child brief.
  If the input describes 4 work units and the parent lists 3 children, the missing unit must either become a 4th child or be explicitly justified as folded into an existing child (with the *exists because* clause updated).
  A folded unit's distinct concerns — acceptance criteria, edge cases, constraints, side-effect checkpoints — must reappear in the absorbing child's matching sections; folding is where requirement depth is most often silently lost, so verify the migration here.
  Each child also survives a BDR pass from `bloat-decomposition.md` — no child triggers ≥ 2 bloat signals, and no atomic-change-unit (K1) was split.
  If either fails, re-decompose before saving.
- **Parent contract coverage:** shared contracts discovered during Stage 3 appear in parent `Shared Constraints`, `Conflict Hotspots`, or `Global Acceptance Criteria`.
  Children may add local checks, but the parent must carry the cross-child compatibility rule so parallel work cannot silently break it.
- **Handoff address parity:** every dependency edge has one repo-relative deliverable path and minimum format; the exact path appears in the predecessor's output/no-change handoff and the successor's first-stage start condition.
  A child name, result label, branch nickname, or prose such as "when the verified result is available" is not an address.
- **Coordination consistency:** each parallelization and hotspot item describes one child pair; no pair is both parallel and serialized; no direct dependency pair is parallel; a `parallel-safe` hotspot names the ownership partition and join rule.
- **No-change safety:** already-satisfied candidates were removed or collapsed before save, while every surviving child's Stage 1 says how to prove no edits are needed, where that evidence goes, and who performs bounded correction/re-verification if proof fails.
  A no-change branch must still tell successors whether to continue, skip, or replan.
- **Verification concreteness:** every child stage and parent dependency edge names a repository-supported command or bounded inspection, its concrete inputs, and an observable expected signal such as an exit code, output token, created state, or threshold.
  A command that expects no matches also names the target population so an empty or wrong input cannot masquerade as success.
- **Deferred coverage:** valid findings excluded from the current briefset appear as `[deferred]` in the parent when they affect the whole initiative, or in the relevant child when they affect only that child.
  Do not drop a finding merely because it is outside the chosen child boundaries.

Each child runs all items in the standard Stage 5.6 self-check from `SKILL.md`, including execution-stage continuity and whole-work completion separation, but its input-coverage boundary is the scope allocated to that child by the parent plus relevant shared constraints.
Sibling-owned concerns from the umbrella input are not missing from the target child; parent decomposition coverage checks them across the set.
If the parent or any child fails any Stage 5.6 self-check item, fix the affected file in place, re-run `validate_briefset.py`, and re-enter the validation chain at Stage 5.5.
Run caveman parity on the parent and every child: the parent must retain every child, dependency, ordering edge, parallel join, conflict hotspot, shared constraint, and global acceptance criterion from its normal-mode equivalent; each child must retain every normal-mode fact, bullet, stage, field, and checklist level.
Do not skip the child self-check on the assumption "the parent covers it" — children are independently executable, so they are independently completeness-checked.

### Stage 5.7 — Cold-Pickup Verification (briefset)

Briefset mode is an auto-ON trigger for the Stage 5.7 cold-pickup verification in `SKILL.md`: the **parent and every child** run their own cold-pickup pass.
The parent pass receives the original input and parent path and checks the set as a whole, following the referenced children when needed.
Each child pass receives the original input, parent path, and one child path; use the parent as the scope-allocation map, and do not treat sibling-owned work as missing from the target child.
For briefsets with 5 or more children, the agent may offer the user a sampling fallback — parent plus up to 3 representative children — instead of the full set.
Force OFF from the user skips cold-pickup for the whole set.
The Stage 6 banner reports `K/N children verified` alongside the parent outcome.

### Stage 6 — Review + Iterate

Report the parent path, the child paths, the structural validator outcome (parent + per-child), and a separate executability outcome covering Stage 5.5 execution reconstruction, Stage 5.6 self-check (parent + per-child), and Stage 5.7 cold-pickup — collapse per-document verdicts to `K/N children verified` where appropriate.
Keep this report in normal prose; caveman applies only inside the saved parent and child plan bodies.

If the parent or any child contains structured non-blocking `Open Questions`, present a combined decision table immediately after the save report:

```markdown
| 순번 | 내용 | 수정 추천안 | 근거 |
|---|---|---|---|
| 1 | <parent or child path + non-blocking user decision> | <recommended patch to apply> | <safe default and reconfirm milestone> |
```

After the user answers, patch the affected parent or child files in place, move resolved questions into the appropriate sections, leave only structured non-blocking user decisions in `Open Questions`, then re-run `validate_briefset.py`, Stage 5.5, Stage 5.6, and the Stage 5.7 gate.
If the user does not answer, cancels, or lets structured input expire, keep every declared fallback active and leave the corresponding questions unchanged; they do not block child execution before their named reconfirmation milestones.
Iterate on disk via `Edit`; do not re-render the briefs into chat.

---

## Validator Scope

`scripts/validate_briefset.py` checks **structural** conformity only:

- Parent filename pattern, title shape (`# Brief Set: <title>`).
- Required parent sections present.
- `Child Briefs` and `Global Acceptance Criteria` use `- [ ]` format.
- `Execution Order`, `Dependencies`, `Parallelization`, `Open Questions`, `Purpose`, `Conflict Hotspots`, `Shared Constraints` are populated (write `- None — <reason>` if genuinely none).
- `Child Briefs` lists at least two distinct top-level children; nested child paths never satisfy the minimum, and a zero- or one-child parent fails.
- Every child reference is the exact repo-relative `docs/briefs/<child>.md` path; absolute paths, nested paths, `..` escapes, short labels, and basename-only references fail.
- Each exact referenced child path exists on disk.
- No referenced child is itself a briefset parent (no recursion).
- `Execution Order` references every child exactly once as the subject of a wave entry, uses consecutive waves, and gives every child a repo-relative deliverable location.
- `Execution Order`, `Dependencies`, `Parallelization`, and `Conflict Hotspots` use top-level bullets only; any non-empty prose before or outside those bullets fails.
- Every non-empty `Dependencies` entry uses the fixed predecessor, deliverable path, format, successor, start, verification, inputs, and expected-signal fields.
- Each dependency path exists or carries the adjacent `(proposed)` marker, matches the predecessor's execution-order location, appears in the producer child's output/no-change handoff, and appears in the successor child's first-stage `Starts when`; the predecessor wave is strictly earlier than the successor wave.
- Every `Parallelization` entry describes exactly one pair, includes its own non-empty `Join when:`, and cannot mark a dependency pair parallel or declare one pair both ways.
- Every `Conflict Hotspots` entry describes exactly one pair with `serialized` or `parallel-safe` access; serialized entries name a full-path owner, and serialized hotspots cannot contradict a parallel declaration.
- Parent filename date is a real calendar date.
- Parent sections appear exactly once and in canonical order.
- Child filenames use the exact `<set-slug>-NN-<child-slug>` order and share the parent date.
- Every child passes `validate_brief.py`'s structural checks (re-run transitively), every child stage has `Verify` / `Inputs` / `Expected`, and every child Stage 1 has a paired `No-op when` / `No-op handoff` contract.
- `--repo-root` overrides the checkout used for entry-point, handoff, and hotspot path checks when briefs are validated from an isolated artifact tree.

Out of scope (still on the human reviewer):

- Whether the decomposition is sensible.
- Whether the declared dependency format contains the right domain fields or the verification signal proves readiness.
- Whether `Dependencies`, pairwise parallel rules, and hotspot access correctly reflect reality beyond the structural contradictions above.
- Whether `Conflict Hotspots` capture every shared edit surface.
- Whether `Global Acceptance Criteria` are measurable.

---

## Why This Shape

Splitting a brief into a parent + children is a structural answer to a **coordination** problem, not a length problem.
The parent makes coordination state legible — what runs in parallel, what blocks what, which file two children both want to touch.
The children stay single-purpose so a downstream agent can pick one up and execute it exactly the way it would execute a standalone brief.

If you find a parent that reads like a single brief with a table of contents, collapse it back to single-brief mode.
If you find a child that reads like a parent, the decomposition is wrong — re-plan rather than nesting.
