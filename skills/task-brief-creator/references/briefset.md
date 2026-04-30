# Briefset Mode

`task-brief-creator` defaults to producing **one brief per invocation**.
Briefset mode is the alternative path: a **parent execution-management
document** plus N **independently executable child briefs**, used when a
single task naturally splits into multiple execution contexts.

The trigger is **multiple execution contexts**, not "this work is big".
Independent completion criteria, distinct entry-point files, mixed work
types, ordered dependencies, parallelizable waves, or shared conflict
hotspots that need coordination — those are the signals. If those signals
are absent, stay in single-brief mode no matter how long the input is.

---

## When To Enter Briefset Mode

Enter briefset mode if **one or more** of the following apply strongly:

- Each subtask can carry its own independent completion criteria.
- Each subtask touches a distinct primary change area or entry-point file.
- Work types are mixed (e.g., a `refactor` followed by a `feat`).
- A predecessor's output is a precondition for a successor.
- Parallel-execution capability needs to be tracked explicitly.
- Multiple subtasks share a common conflict surface — i18n bundles,
  shared types, schema, route table, top-level config files.
- A single brief would force `Scope`, `Acceptance Criteria`, or
  `Related Files / Entry Points` to fork into unrelated topics.

If none apply, stay single-brief. Long input alone never triggers
briefset mode — input length is not a proxy for execution-context count.

**User phrasing is not itself a trigger.** Phrases like "다중브리프",
"briefset", "multi-brief", or "split this into multiple briefs" do not
by themselves engage briefset mode. If the user explicitly requests
briefset mode but none of the criteria above apply, halt at Stage 1 and
ask one short question — e.g. *"I see only one execution context here;
what makes you want to split? If it's just file count, single-brief is
the supported answer."* — before drafting. Honoring phrasing alone
produces a 1-child briefset, which this document explicitly calls out
as a collapse target ("If you find a parent that reads like a single
brief with a table of contents, collapse it back to single-brief
mode."). Once the user confirms a real execution-context split exists,
proceed in briefset mode normally.

---

## Naming Convention

```text
docs/briefs/YYYY-MM-DD-briefset-<set-slug>.md                        # parent
docs/briefs/YYYY-MM-DD-<type>-<set-slug>-NN-<child-slug>.md          # children
```

- `<set-slug>` — kebab-case, ≤15 chars, names the umbrella initiative.
- `NN` — zero-padded execution-order index (`01`, `02`, …). The number
  hints the intended starting wave but is not authoritative; the
  parent's `Execution Order` section is.
- `<child-slug>` — kebab-case, ≤15 chars, names the child subtask.
- The combined child slug `<set-slug>-NN-<child-slug>` must remain
  ≤40 chars so the existing `validate_brief.py` slug check passes.

**Examples:**

```text
docs/briefs/2026-04-30-briefset-checkout-i18n.md
docs/briefs/2026-04-30-feat-checkout-i18n-01-message-keys.md
docs/briefs/2026-04-30-feat-checkout-i18n-02-cart-copy.md
docs/briefs/2026-04-30-fix-checkout-i18n-03-validation-copy.md
```

Filename collisions are resolved with `-v2`, `-v3`, … on the parent and
on each child independently — the same rule as single-brief mode. Do
not overwrite existing files.

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
- <question, or "None">
```

### Section guidance

- **Purpose** — why the umbrella exists. Not what each child does.
- **Child Briefs** — checklist (`- [ ]`). The **only** place status
  lives. Tick the box when the child is complete. The *exists because*
  clause is a discipline check: if a child cannot articulate why it
  exists, fold it back into a sibling.
- **Execution Order** — wave-based ordering. Group siblings that can
  run together; separate dependent work into a later wave.
- **Dependencies** — explicit predecessor → successor edges with the
  *why*. Reference only children of this set; never reference another
  briefset (no recursion).
- **Parallelization** — distinct from `Dependencies`. A child can be
  dependency-free and still be unsafe to parallelize because it edits
  a shared file. Call out both can-parallel and must-not-parallel
  cases.
- **Conflict Hotspots** — concrete paths under shared editing pressure.
  i18n message bundles, shared schemas, top-level config, route tables,
  generated barrel files default to hotspots.
- **Shared Constraints** — constraints that apply to every child.
  Per-child constraints stay inside the child brief.
- **Global Acceptance Criteria** — set-level "done" criteria, including
  integration-level checks no individual child can verify alone.
- **Open Questions** — set-level questions only. Per-child questions
  live in the child's `Open Questions`.

If a section legitimately has nothing, write `- None` with a one-line
reason rather than leaving the section empty.

---

## Child Brief Rules

- Children follow `references/template.md` exactly — the same eight
  required H2 sections, same per-section guidance, same writing rules.
- Children include their own `Acceptance Criteria` (independent),
  `Side Effect Checkpoints`, and `Open Questions`.
- Children **do not** carry status. Status is parent-only.
- Children **do not** spawn further children. A child cannot become a
  parent. If a child's scope grows mid-flow, escalate by re-planning
  the parent rather than nesting.
- A child must be executable on its own. If a downstream agent reading
  only the child brief cannot start work, the child is missing context
  that should not have been hidden in the parent.

---

## Workflow Adaptations

The single-brief stages in `SKILL.md` still apply. The diffs:

### Stage 1 — Ambiguity Gate

After scoring the four anchors, also check the briefset-mode criteria
above. If the input clearly maps onto multiple execution contexts,
plan for briefset mode and surface that intent before Stage 2. The
anchor halt rule is unchanged — an underspecified briefset request
halts just like an underspecified single-brief request.

### Stage 2 — Work Type Selection

The parent has no `Work Type` section — skip type selection for it.
Plan a provisional type per child instead. Mixed types across children
is an expected, supported case; do not flatten them to a single type
just to keep the set "consistent".

### Stage 3 — Codebase Review

Run one combined review pass, but tag findings with the specific child
each finding will land in. Each child's `Related Files / Entry Points`
should be a distinct slice — if two children point at the same primary
entry point, they probably collapse into one.

### Stage 4 — Active Interview (one batched round)

Ask once, not per child. The batch should cover:

- Is the proposed decomposition correct? (list children with one-line
  purposes)
- Any missing children? Any children that should merge?
- Is the execution order correct?
- Are the proposed parallel waves correct?
- Are there conflict hotspots beyond what's listed?
- Are the shared constraints and shared exclusions correct?
- For each child whose Acceptance Criteria are not yet concrete, what
  should fill them?

Use `AskUserQuestion` if available; otherwise present a numbered list
in chat. Do not drip questions one by one across multiple rounds — the
batch exists so the user can revise the decomposition as a whole.

### Stage 5 — Save + Validate

Save in this order:

1. Ensure `docs/briefs/` exists.
2. Write each child brief first (so the parent can reference them).
3. Write the parent brief.
4. Resolve filename collisions with `-v2`, `-v3`, … on the parent and
   on each child independently.
5. Run `scripts/validate_brief.py` on each child as a sanity check
   (optional — the briefset validator covers this transitively).
6. Run `scripts/validate_briefset.py` on the parent. It re-runs child
   structural validation, so a single parent invocation covers the
   whole set:

   ```bash
   python3 skills/task-brief-creator/scripts/validate_briefset.py \
     docs/briefs/2026-04-30-briefset-checkout-i18n.md
   ```

Treat structural failure the same way single-brief mode does: leave
the file in place, surface the failure in Stage 6, let the user
decide how to fix. Do not delete or silently rewrite.

### Stage 6 — Review + Iterate

Report the parent path, the child paths, and the validator outcome
(parent + per-child). Iterate on disk via `Edit`; do not re-render the
briefs into chat.

---

## Validator Scope

`scripts/validate_briefset.py` checks **structural** conformity only:

- Parent filename pattern, title shape (`# Brief Set: <title>`).
- Required parent sections present.
- `Child Briefs` and `Global Acceptance Criteria` use `- [ ]` format.
- `Execution Order`, `Parallelization`, `Open Questions`, `Purpose`,
  `Conflict Hotspots`, `Shared Constraints` are populated (write
  `- None` if genuinely none).
- Each referenced child path exists on disk.
- No referenced child is itself a briefset parent (no recursion).
- Inline-code paths in `Dependencies` reference children listed in
  `Child Briefs`.
- Every child passes `validate_brief.py`'s structural checks
  (re-run transitively).

Out of scope (still on the human reviewer):

- Whether the decomposition is sensible.
- Whether `Dependencies` and `Parallelization` correctly reflect
  reality.
- Whether `Conflict Hotspots` actually capture the shared edit
  surfaces.
- Whether `Global Acceptance Criteria` are measurable.

---

## Why This Shape

Splitting a brief into a parent + children is a structural answer to a
**coordination** problem, not a length problem. The parent makes
coordination state legible — what runs in parallel, what blocks what,
which file two children both want to touch. The children stay
single-purpose so a downstream agent can pick one up and execute it
exactly the way it would execute a standalone brief.

If you find a parent that reads like a single brief with a table of
contents, collapse it back to single-brief mode. If you find a child
that reads like a parent, the decomposition is wrong — re-plan rather
than nesting.
