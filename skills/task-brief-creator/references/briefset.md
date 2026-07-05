# Briefset Mode

`task-brief-creator` defaults to producing **one brief per invocation**.
Briefset mode is the alternative path: a **parent execution-management document** plus N **independently executable child briefs**, used when a single task naturally splits into multiple execution contexts.

The trigger is **coordination across multiple execution contexts**, not "this work is big".
Independent completion criteria, mixed work types, ordered dependencies, parallelizable waves, or shared conflict hotspots that need coordination — those are the signals.
Distinct entry-point files are supporting evidence only unless they map to independent work units.
If strong coordination signals are absent, stay in single-brief mode no matter how long the input is.

---

## When To Recommend Briefset Mode

Recommend briefset mode only when the input describes multiple independently executable work units, not just many edits.
A good quick test: can you write two or more natural child-brief titles, each with its own acceptance criteria and entry point, without inventing scope?
If not, stay in single-brief mode.

Strong recommendation signals:

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

When strong signals are present, do not enter briefset mode silently.
Recommend it and ask the user to choose before Stage 2.
If the user chooses single-brief despite the recommendation, proceed single-brief and record any ordering or PR constraints explicitly.

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

**User phrasing is not itself a trigger.** Phrases like "다중브리프", "briefset", "multi-brief", or "split this into multiple briefs" do not by themselves engage briefset mode.
If the user explicitly requests briefset mode but none of the criteria above apply, halt at Stage 1 and ask one short question — e.g. *"I see only one execution context here; what makes you want to split?
If it's just file count, single-brief is the supported answer."* — before drafting.
Honoring phrasing alone produces a 1-child briefset, which this document explicitly calls out as a collapse target ("If you find a parent that reads like a single brief with a table of contents, collapse it back to single-brief mode.").
Once the user confirms a real execution-context split exists, proceed in briefset mode normally.

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
- The set-slug ≤15 limit is advisory — the validator emits a warning only.
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

```markdown
# Brief Set: <title>

## Purpose
- <why this brief set exists — one or two bullets, no implementation detail>

## Child Briefs
- [ ] `docs/briefs/2026-04-30-feat-checkout-i18n-01-message-keys.md` — <child title>; exists because <reason>
- [ ] `docs/briefs/2026-04-30-feat-checkout-i18n-02-cart-copy.md` — <child title>; exists because <reason>

## Execution Order
- Wave 1: `docs/briefs/2026-04-30-feat-checkout-i18n-01-message-keys.md`, `docs/briefs/2026-04-30-feat-checkout-i18n-02-cart-copy.md` can run in parallel.
- Wave 2: `docs/briefs/2026-04-30-fix-checkout-i18n-03-validation-copy.md` starts after `docs/briefs/2026-04-30-feat-checkout-i18n-01-message-keys.md` is complete.

## Dependencies
- `docs/briefs/2026-04-30-fix-checkout-i18n-03-validation-copy.md` depends on `docs/briefs/2026-04-30-feat-checkout-i18n-01-message-keys.md` because <reason>.
- `docs/briefs/2026-04-30-feat-checkout-i18n-02-cart-copy.md` has no dependencies.

## Parallelization
- `docs/briefs/2026-04-30-feat-checkout-i18n-01-message-keys.md` and `docs/briefs/2026-04-30-feat-checkout-i18n-02-cart-copy.md` can run in parallel — they touch separate entry points.
- `docs/briefs/2026-04-30-fix-checkout-i18n-03-validation-copy.md` must not run in parallel with another child that edits `<conflict path>`.

## Conflict Hotspots
- `<path>` — only one child brief should edit this at a time.

## Shared Constraints
- <constraint shared by all child briefs, or "None — <reason>">

## Global Acceptance Criteria
- [ ] <set-level completion criterion>
- [ ] <integration-level criterion>

## Open Questions
- <question, or "None — <reason>">
```

### Section guidance

- **Purpose** — why the umbrella exists.
  Not what each child does.
- **Child Briefs** — checklist (`- [ ]`).
  The **only** place status lives.
  Tick the box when the child is complete.
  The *exists because* clause is a discipline check: if a child cannot articulate why it exists, fold it back into a sibling.
- **Execution Order** — wave-based ordering.
  Group siblings that can run together; separate dependent work into a later wave.
- **Dependencies** — explicit predecessor → successor edges with the *why*.
  Reference only children of this set; never reference another briefset (no recursion).
- **Parallelization** — distinct from `Dependencies`.
  A child can be dependency-free and still be unsafe to parallelize because it edits a shared file.
  Call out both can-parallel and must-not-parallel cases.
- **Conflict Hotspots** — concrete paths under shared editing pressure. i18n message bundles, shared schemas, top-level config, route tables, generated barrel files default to hotspots.
- **Shared Constraints** — constraints that apply to every child.
  Per-child constraints stay inside the child brief.
- **Global Acceptance Criteria** — set-level "done" criteria, including integration-level checks no individual child can verify alone.
- **Open Questions** — set-level questions only.
  Per-child questions live in the child's `Open Questions`, but Stage 4 must still surface user-owned ones during the per-child residuals step of the decision table.

If a section legitimately has nothing, write `- None — <reason>` with a one-line reason rather than leaving the section empty.

---

## Child Brief Rules

- Children follow `references/template.md` exactly — the same eight required H2 sections, same per-section guidance, same writing rules.
- Children include their own `Acceptance Criteria` (independent), `Side Effect Checkpoints`, and `Open Questions`.
- Child `Open Questions` must come from codebase-review uncertainty, user-provided uncertainty, or unresolved Stage 4 answers.
  Use `- None — <reason>` only when the child is genuinely unambiguous.
- Children **do not** carry status.
  Status is parent-only.
- Children **do not** spawn further children.
  A child cannot become a parent.
  If a child's scope grows mid-flow, escalate by re-planning the parent rather than nesting.
- A child must be executable on its own.
  If a downstream agent reading only the child brief cannot start work, the child is missing context that should not have been hidden in the parent.

---

## Workflow Adaptations

The single-brief stages in `SKILL.md` still apply.
The diffs:

### Stage 1 — Ambiguity Gate

After scoring the four anchors, also check the recommendation criteria above.
If the input clearly maps onto multiple execution contexts, recommend briefset mode and ask the user to choose before Stage 2.
The anchor halt rule is unchanged — an underspecified briefset request halts just like an underspecified single-brief request.

### Stage 2 — Work Type Selection

The parent has no `Work Type` section — skip type selection for it.
Plan a provisional type per child instead.
Mixed types across children is an expected, supported case; do not flatten them to a single type just to keep the set "consistent".

### Stage 3 — Codebase Review

Run one combined review pass, but tag findings and uncertainties with the specific parent or child they will land in.
Track uncertainties as candidate `Open Questions` during the review; do not silently resolve them or drop them just because they are child-specific.
Each child's `Related Files / Entry Points` should be a distinct slice — if two children point at the same primary entry point, they probably collapse into one.
Track shared contracts separately from child-local findings.
If an id, key, event, schema, persisted value, generated file, route, command, or payload is used by more than one child or by existing consumers outside the briefset, put that contract in the parent `Shared Constraints` or `Global Acceptance Criteria`, then repeat only the child-specific verification inside the affected child.

When reviewing an existing briefset-capable skill or generator, tag findings as one of:

- Parent-only.
- Child-only.
- Shared parent/child contract.
- Validator/documentation mismatch.
- Deferred hardening.

This prevents briefset concerns from disappearing in one run and over-expanding the work in the next.

### Stage 4 — User Decision Table

Stage 4 in briefset mode follows the same decision-table policy described in `stage-4-interview.md`.
The table is rooted at decomposition validity — that is the highest-leverage parent decision in a briefset, and locking it first prunes most downstream rows.
Put user-owned decisions into the four-column table (`순번`, `내용`, `수정 추천안`, `근거`) in this order:

1. **Decomposition** — confirm or revise the child list, each entry carrying a recommended *exists because* clause.
   If a plausible alternative would collapse two children, split one into two, or add/drop a child, give that decision its own row.
   If the candidate child list shows ≥ 2 bloat signals from `bloat-decomposition.md`, apply BDR before tabling decomposition decisions.
   Apply K1 (atomic change unit) **before** generating cuts — K1 short-circuits, so atomic candidates never split.
   Then run S1–S5 on the surviving candidates and apply K2 (shared failure-path cohesion) to prune the resulting cuts.
   See `bloat-decomposition.md` Application Order for the authoritative sequence.
2. **Per-child work types** — confirm the provisional type per surviving child when the type changes downstream behavior (e.g., `refactor` vs `feat`).
   If the type is obvious and does not change execution behavior, carry it forward without asking.
3. **Execution order and parallelization** — add rows for wave order or parallelization choices the user owns.
   Probe shared imports / shared files first, then cite the result in `근거`.
4. **Conflict hotspots** — add rows for candidate hotspots that require a coordination decision.
   Do not enumerate speculative hotspots.
5. **Per-child residuals** — only after the topology is locked, table each child's user-owned `Acceptance Criteria`, `Out of Scope`, and unresolved `Open Questions`.
   Codebase-review uncertainties tagged in Stage 3 are surfaced here and routed to *answer now*, *keep in Open Questions*, or *delegate to downstream agent*.
   Low-risk wording, local implementation choices, and reversible sequencing choices should usually become a recommendation in the parent or child brief instead of an `Open Questions` row.

Briefset Stage 4 still respects the carry-over codebase budget.
A parent-level branch probe (e.g., "does `i18n/messages.ko.json` import from any other child's entry point?") counts against the same budget as Stage 3.

### Stage 5 — Save + Validate

Save in this order:

1. Ensure `docs/briefs/` exists.
2. Resolve child filename collisions first, then write each child brief to its final path (so the parent can reference final filenames, not provisional names).

   When writing child briefs, populate `Open Questions` from the Stage 3 uncertainty register and Stage 4 answers.
   Do not add new unreviewed questions after the Stage 4 decision table closes just to fill the section.
   If Stage 4 resolves every uncertainty for a child, write `- None — <reason>` with confidence that the child is genuinely unambiguous.

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

Treat structural failure the same way single-brief mode does: leave the file in place, surface the failure in Stage 6, let the user decide how to fix.
Do not delete or silently rewrite.

### Stage 5.5 — Downstream Interpretation Check (briefset)

Run the downstream interpretation check from `SKILL.md` Stage 5.5 against the **parent briefset file only**.
The sub-agent receives a natural work-start request with the parent path, not each child path, and no original user request or validation rubric.
If the interpretation drops a child, changes execution order, broadens scope, or misses a parent constraint, patch the parent or affected child, re-run `validate_briefset.py`, and re-enter the validation chain at Stage 5.5.

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
- **Deferred coverage:** valid findings excluded from the current briefset appear as `[deferred]` in the parent when they affect the whole initiative, or in the relevant child when they affect only that child.
  Do not drop a finding merely because it is outside the chosen child boundaries.

Each child runs the standard Stage 5.6 self-check from `SKILL.md`.
If the parent or any child fails any Stage 5.6 self-check item, fix the affected file in place, re-run `validate_briefset.py`, and re-enter the validation chain at Stage 5.5.
Do not skip the child self-check on the assumption "the parent covers it" — children are independently executable, so they are independently completeness-checked.

### Stage 5.7 — Cold-Pickup Verification (briefset)

Briefset mode is an auto-ON trigger for the Stage 5.7 cold-pickup verification in `SKILL.md`: the **parent and every child** run their own cold-pickup pass.
For briefsets with 5 or more children, the agent may offer the user a sampling fallback — parent plus up to 3 representative children — instead of the full set.
Force OFF from the user skips cold-pickup for the whole set.
The Stage 6 banner reports `K/N children verified` alongside the parent outcome.

### Stage 6 — Review + Iterate

Report the parent path, the child paths, the structural validator outcome (parent + per-child), the Stage 5.5 downstream interpretation outcome, the Stage 5.6 self-check outcome (parent + per-child), and the Stage 5.7 cold-pickup outcome — per-document verdicts collapsed to `K/N children verified` in the banner, or the skip reason when cold-pickup did not run.

If the parent or any child contains `Open Questions` that require a user decision, present a combined decision table immediately after the save report:

```markdown
| 순번 | 내용 | 수정 추천안 | 근거 |
|---|---|---|---|
| 1 | <parent or child path + Open Question requiring user decision> | <recommended patch to apply> | <why this cannot be delegated safely> |
```

After the user answers, patch the affected parent or child files in place, move resolved questions into the appropriate sections, leave only genuinely unresolved or delegated questions in `Open Questions`, then re-run `validate_briefset.py`, Stage 5.5, Stage 5.6, and the Stage 5.7 gate.
Iterate on disk via `Edit`; do not re-render the briefs into chat.

---

## Validator Scope

`scripts/validate_briefset.py` checks **structural** conformity only:

- Parent filename pattern, title shape (`# Brief Set: <title>`).
- Required parent sections present.
- `Child Briefs` and `Global Acceptance Criteria` use `- [ ]` format.
- `Execution Order`, `Dependencies`, `Parallelization`, `Open Questions`, `Purpose`, `Conflict Hotspots`, `Shared Constraints` are populated (write `- None — <reason>` if genuinely none).
- Each referenced child path exists on disk.
- No referenced child is itself a briefset parent (no recursion).
- Inline-code paths in `Dependencies` reference children listed in `Child Briefs`.
- Parent filename date is a real calendar date.
- Parent sections appear exactly once and in canonical order.
- Child filenames use the exact `<set-slug>-NN-<child-slug>` order and share the parent date.
- Every child passes `validate_brief.py`'s structural checks (re-run transitively).

Out of scope (still on the human reviewer):

- Whether the decomposition is sensible.
- Whether `Dependencies` and `Parallelization` correctly reflect reality.
- Whether `Conflict Hotspots` actually capture the shared edit surfaces.
- Whether `Global Acceptance Criteria` are measurable.

---

## Why This Shape

Splitting a brief into a parent + children is a structural answer to a **coordination** problem, not a length problem.
The parent makes coordination state legible — what runs in parallel, what blocks what, which file two children both want to touch.
The children stay single-purpose so a downstream agent can pick one up and execute it exactly the way it would execute a standalone brief.

If you find a parent that reads like a single brief with a table of contents, collapse it back to single-brief mode.
If you find a child that reads like a parent, the decomposition is wrong — re-plan rather than nesting.
