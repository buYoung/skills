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
- [ ] `docs/briefs/<child-01>.md` — <child title>; exists because <reason>
- [ ] `docs/briefs/<child-02>.md` — <child title>; exists because <reason>

## Execution Order
- Wave 1: `<child-01>`, `<child-02>` can run in parallel.
- Wave 2: `<child-03>` starts after `<child-01>` is complete.

## Dependencies
- `<child-03>` depends on `<child-01>` because <reason>.
- `<child-02>` has no dependencies.

## Parallelization
- `<child-01>` and `<child-02>` can run in parallel — they touch separate entry points.
- `<child-03>` must not run in parallel with `<child-04>` — both touch `<conflict path>`.

## Conflict Hotspots
- `<path>` — only one child brief should edit this at a time.

## Shared Constraints
- <constraint shared by all child briefs, or "None">

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

### Stage 4 — User Decision Table

Stage 4 in briefset mode follows the same decision-table policy described in `stage-4-interview.md`.
The table is rooted at decomposition validity — that is the highest-leverage parent decision in a briefset, and locking it first prunes most downstream rows.
Put user-owned decisions into the four-column table (`순번`, `내용`, `수정 추천안`, `근거`) in this order:

1. **Decomposition** — confirm or revise the child list, each entry carrying a recommended *exists because* clause.
   If a plausible alternative would collapse two children, split one into two, or add/drop a child, give that decision its own row.
2. **Per-child work types** — confirm the provisional type per surviving child when the type changes downstream behavior (e.g., `refactor` vs `feat`).
   If the type is obvious and does not change execution behavior, carry it forward without asking.
3. **Execution order and parallelization** — add rows for wave order or parallelization choices the user owns.
   Probe shared imports / shared files first, then cite the result in `근거`.
4. **Conflict hotspots** — add rows for candidate hotspots that require a coordination decision.
   Do not enumerate speculative hotspots.
5. **Per-child residuals** — only after the topology is locked, table each child's user-owned `Acceptance Criteria`, `Out of Scope`, and unresolved `Open Questions`.
   Codebase-review uncertainties tagged in Stage 3 are surfaced here and routed to *answer now*, *keep in Open Questions*, or *delegate to downstream agent*.

Briefset Stage 4 still respects the carry-over codebase budget.
A parent-level branch probe (e.g., "does `i18n/messages.ko.json` import from any other child's entry point?") counts against the same budget as Stage 3.

### Stage 5 — Save + Validate

Save in this order:

1. Ensure `docs/briefs/` exists.
2. Write each child brief first (so the parent can reference them).

   When writing child briefs, populate `Open Questions` from the Stage 3 uncertainty register and Stage 4 answers.
   Do not add new unreviewed questions after the Stage 4 decision table closes just to fill the section.
   If Stage 4 resolves every uncertainty for a child, write `- None — <reason>` with confidence that the child is genuinely unambiguous.

3. Write the parent brief.
4. Resolve filename collisions with `-v2`, `-v3`, … on the parent and on each child independently.
5. Run `scripts/validate_brief.py` on each child as a sanity check (optional — the briefset validator covers this transitively).
6. Run `scripts/validate_briefset.py` on the parent.
   It re-runs child structural validation, so a single parent invocation covers the whole set:

   ```bash
   python3 skills/task-brief-creator/scripts/validate_briefset.py \
     docs/briefs/2026-04-30-briefset-checkout-i18n.md
   ```

Treat structural failure the same way single-brief mode does: leave the file in place, surface the failure in Stage 6, let the user decide how to fix.
Do not delete or silently rewrite.

### Stage 5.5 — Content-Level Self-Check (briefset)

Run the self-check from `SKILL.md` Stage 5.5 on the **parent** and on **every child** independently.
Briefset mode adds one parent-specific coverage rule:

- **Parent decomposition coverage:** every input-implied execution context maps to a child brief.
  If the input describes 4 work units and the parent lists 3 children, the missing unit must either become a 4th child or be explicitly justified as folded into an existing child (with the *exists because* clause updated).

Each child runs the standard 5-item self-check from `SKILL.md` Stage 5.5.
If any child fails the input-coverage or section-depth items, fix the child in place, re-run the briefset structural validator, and re-run the child's self-check.
Do not skip the child self-check on the assumption "the parent covers it" — children are independently executable, so they are independently completeness-checked.

### Stage 6 — Review + Iterate

Report the parent path, the child paths, the structural validator outcome (parent + per-child), and the Stage 5.5 self-check outcome (parent + per-child).

If the parent or any child contains `Open Questions` that require a user decision, present a combined decision table immediately after the save report:

```markdown
| 순번 | 내용 | 수정 추천안 | 근거 |
|---|---|---|---|
| 1 | <parent or child path + Open Question requiring user decision> | <recommended patch to apply> | <why this cannot be delegated safely> |
```

After the user answers, patch the affected parent or child files in place, move resolved questions into the appropriate sections, leave only genuinely unresolved or delegated questions in `Open Questions`, and re-run `validate_briefset.py` plus the Stage 5.5 self-check.
Iterate on disk via `Edit`; do not re-render the briefs into chat.

---

## Validator Scope

`scripts/validate_briefset.py` checks **structural** conformity only:

- Parent filename pattern, title shape (`# Brief Set: <title>`).
- Required parent sections present.
- `Child Briefs` and `Global Acceptance Criteria` use `- [ ]` format.
- `Execution Order`, `Parallelization`, `Open Questions`, `Purpose`, `Conflict Hotspots`, `Shared Constraints` are populated (write `- None — <reason>` if genuinely none).
- Each referenced child path exists on disk.
- No referenced child is itself a briefset parent (no recursion).
- Inline-code paths in `Dependencies` reference children listed in `Child Briefs`.
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
