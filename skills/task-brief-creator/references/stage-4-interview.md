# Stage 4 Interview

`task-brief-creator` closes every residual gap through a single
interview policy: build a decision tree from Stage 3 findings and
residual input gaps, walk top-down asking one question at a time,
attach a recommended answer to every question, and prefer a narrow
codebase probe over a user question whenever the node is
codebase-resolvable.

This is the only Stage 4 path. There is no separate "batched mode" toggle.

The shape exists because brief-quality failure modes cluster at
**dependency-tangled decisions**. Out of Scope can only be drawn after
In Scope is decided. Behavior Contract only matters once the type is
locked. A briefset's per-child Acceptance Criteria are meaningless
before decomposition is settled. Walking the tree top-down resolves
each layer before the next layer's questions exist, so the user is
never asked to answer "what should be true at completion?" before
"what is the work type, actually?".

The interview style — one question at a time, recommended answer
attached, codebase explored before the user is asked — is adapted
from the standalone `grill-me` skill. In `task-brief-creator` the
policy is the default Stage 4 behavior, not an opt-in mode. Even
when only one or two nodes remain, they are walked sequentially;
the interview never collapses into a single batched prompt.

---

## Decision Tree Construction

Before asking the first question, build a decision tree from Stage 3
review notes plus residual gaps in the input. The tree drives the
interview order.

Standard single-brief root layout:

```
Work Type (provisional)
└─ Desired Outcome (To-Be)
   ├─ In Scope boundary
   │  └─ Out of Scope guardrails
   ├─ Acceptance Criteria
   ├─ Side Effect Checkpoints
   └─ Type-conditional input (only if type is fix/perf/refactor)
      ├─ fix      → Reproduction
      ├─ perf     → Baseline Measurement
      └─ refactor → Behavior Contract
Residual Open Questions (only those a codebase probe cannot resolve)
```

Briefset root layout:

```
Decomposition validity (which children, why each exists)
└─ Per-child work types
   └─ Execution order
      ├─ Parallelization
      ├─ Conflict hotspots
      └─ Per-child residuals
         ├─ child Acceptance Criteria
         ├─ child Out of Scope
         └─ child Open Questions
```

Tree-construction rules:

- A child branch is only worth walking if its parent answer leaves it
  ambiguous. If the parent answer **prunes** the child, skip the
  child entirely — do not ask the user about something already
  decided.
- Each node maps to exactly one section in the brief (or one row in
  the briefset parent). If a node maps to "general background", drop
  it — Stage 4 is not a context-gathering interview.
- If a node can be answered by reading the codebase, mark it
  *codebase-resolvable* before walking. Codebase precedence (below)
  applies before any user question.

---

## Codebase Precedence Flow

Stage 4 honors the explore-first rule. For each tree node, run this
check before asking the user:

```
Can a narrow codebase probe answer this node?
├─ YES → run the probe within the carry-over budget.
│        ├─ Probe resolves the node →
│        │  Skip the user question OR ask a short
│        │  confirmation: "I checked X and it looks like
│        │  Y — does that match your intent?"
│        └─ Probe inconclusive →
│           Fall through to the user question with
│           the partial finding stated as context.
└─ NO  → Ask the user question with a recommended answer.
```

### Carry-over budget

Stage 3's review budget (~15 reads / ~10 queries) is a soft limit
across the entire codebase pass. Stage 4 inherits any unused budget
plus a small additional cap reserved for branch probes:

| Source | Soft cap |
|---|---|
| Stage 3 unused | whatever remains |
| Stage 4 additional | ~5 reads / ~3 queries |

Per-node ceiling: 1–2 queries per branch probe. If a single node would
need a deep dive, that is a signal the question belongs to the user,
not the codebase.

When the carry-over budget is exhausted, stop running probes and ask
the user for the rest. Do not silently continue exploring.

---

## One-at-a-Time Question Rules

Walk questions go through `AskUserQuestion` (or its host equivalent).
Each question follows this contract:

- **One question per round.** No batching, no follow-up packed into
  the same prompt. The next question fires only after the previous
  answer arrives. This holds regardless of how few residual nodes
  remain — a single-node tree fires one round, a two-node tree fires
  two sequential rounds.
- **Recommended answer first.** Always include a tentative answer
  marked `(Recommended)`. Phrase it as *"I think it's X because of
  the As-Is shape"*, never as *"what do you want?"*. The user revises
  or accepts; they do not author from scratch.
- **2–4 concrete options.** Prefer pick-from-list or yes/no framings
  over open prompts. If the answer space is genuinely open, write the
  recommendation plus 1–2 alternates and accept free-text override.
- **Verification check-in carve-out.** Two situations let the round
  close without numbered `(Recommended)` options, because the
  recommendation is already on screen and the user is reacting to it
  rather than authoring:
  - **List-shaped draft.** A complete multi-bullet draft of a
    list-shaped section (`Acceptance Criteria`, `Side Effect
    Checkpoints`, candidate `Open Questions`, draft `Constraints`)
    is itself the recommended answer. Closing with `Add or
    change?` / `추가/수정?` is allowed — the user accepts
    verbatim, marks up specific bullets, or replaces items inline.
  - **Prose-stated recommendation on a yes/no node.** When a single
    binary node has its recommendation explicitly stated in the
    surrounding prose ("I'd carry this forward as an Open
    Question…"), closing with `Sound right?` / `이대로 갈까?` is
    allowed. The prose carries the `(Recommended)` weight even
    without a numbered list.

  Both forms still satisfy "recommended answer first" — the user
  reviews a concrete proposal, never authors from scratch. The
  carve-out does **not** extend to multi-option branching decisions
  (work type, scope boundary, decomposition validity, execution
  order, conflict-hotspot inclusion, pick-from-list cases). Those
  still require explicit `(Recommended)`-marked options because the
  user needs to see the alternates to evaluate the recommendation.
- **State the upstream answer.** When a question depends on a
  previous answer, restate it: *"You picked `refactor`, so the
  Behavior Contract has to lock the existing test suite — which
  suite?"*. The user should not need to recall the chain.
- **Explain the codebase finding when the question is a
  confirmation.** If a probe pre-resolved the node, the question is
  no longer a real branch — it is verification. Keep it under one
  sentence: *"`PaymentService.charge` only writes to the local
  ledger; treating that as a hard boundary, agreed?"*.

Order of walking:

1. Walk top-down: parent before child. A child question is dead until
   its parent is decided.
2. Walk siblings in dependency order. If sibling A's answer changes
   sibling B's relevance, ask A first.
3. Re-prune the tree after every answer. If the answer eliminates
   later branches, drop them. The walk continues sequentially through
   whatever remains, even if pruning leaves only one or two nodes.
4. Surface residual `Open Questions` last. They are the leftovers
   the brief explicitly carries forward to the downstream agent — do
   not exhaust the user's patience trying to resolve everything in
   the interview.

---

## Termination Conditions

Stop the Stage 4 loop when **any** of these is true:

- Every mandatory tree node is decided (the brief can be drafted).
- The user explicitly stops (`stop`, `enough`, `그만`, `충분해`,
  `done`).
- Carry-over codebase budget is exhausted **and** every remaining
  node is unanswerable by the user without external input — record
  those as `Open Questions` and continue to Stage 5.
- A pending answer requires information neither the codebase nor the
  user has at hand (e.g., a product decision owned by someone else).
  Record the dependency in `Open Questions`, mark the brief as
  blocked on that input, and continue.

After termination, proceed to Stage 5 exactly as documented in
`SKILL.md`. Stage 4 does not change the saved-brief structure.

---

## Output Identity

The walk is a **behavior variant of the brief-authoring pipeline**, not
an output variant. The saved brief still follows
`references/template.md` exactly:

- Eight required H2 sections (`Work Type`, `Current State (As-Is)`,
  `Desired Outcome (To-Be)`, `Scope`, `Related Files / Entry Points`,
  `Side Effect Checkpoints`, `Acceptance Criteria`, `Open Questions`).
- Type-conditional H2 (`Reproduction` / `Baseline Measurement` /
  `Behavior Contract`) when the type demands it.
- Optional `Constraints` block between `Scope` and `Related Files /
  Entry Points` when task-specific constraints exist.
- Briefset parent + children when briefset mode is also active.

`scripts/validate_brief.py` and `scripts/validate_briefset.py` apply
unchanged. A brief that fails the validator failed for the same
reasons regardless of which Stage 4 path produced it.

---

## Briefset Interaction

Briefset mode and the branch walk compose naturally — decomposition
is itself the highest-value branch to walk one question at a time.
When briefset mode engages, expect the walk to dominate Stage 4: the
parent topology alone usually contributes 3+ unresolved nodes
(decomposition validity, ordering, conflict hotspots), and per-child
residuals add more on top.

Workflow notes:

- Replace any "one batched round" wording in older briefset
  documentation with the walk: decomposition → per-child work types →
  execution order → parallelization → conflict hotspots →
  per-child residuals.
- Per-child `Acceptance Criteria` and `Out of Scope` walk *after* the
  parent topology is locked. Walking them earlier produces guardrails
  for children that may not survive the decomposition decision.
- Children inherit walk-style interview output but are still saved as
  standard child briefs (`validate_briefset.py` covers them
  transitively).

---

## Anti-patterns

Do not:

- **Walk on a halt-eligible input.** Two missing anchors do not
  become four answered anchors through 30 single questions; they
  become a confidently wrong brief. Halt at Stage 1 first.
- **Skip codebase precedence to "save round-trips".** The whole point
  is asking only the questions that need asking. If a probe could
  answer it, run the probe.
- **Batch two or more *dependent* decisions into one prompt because
  "the tree is shallow" or "they're related".** When one decision's
  answer reshapes another's relevance, sequential walking is
  mandatory — a two-node tree of dependent decisions fires two
  rounds, not one combined round. Latency savings here reintroduce
  the dependency-tangle failure mode the walk exists to prevent.
  (Independent per-child confirmations under the briefset carve-out
  in `briefset.md` are *not* this anti-pattern — independence is
  the precondition that lets them share a prompt.)
- **Ask the same question twice with different framings.** If the
  user gave a clear answer, accept it and move on. Repeated asks
  signal the agent did not believe the user, which is corrosive.
- **Drop the recommended answer.** A naked "what do you want?" is
  not a branch walk — it is offloading the design problem to the
  user.
- **Loop forever.** Honor the termination conditions. Residual
  ambiguity belongs in `Open Questions`, not in a 17th interview
  round.

---

## Why This Shape

Sequential walking optimizes for **dependency resolution** — when
the wrong answer to question 2 makes question 7 meaningless, batching
all seven at once burns the user's effort and produces a
correspondingly muddled brief. Walking the tree node by node, with a
recommended answer at each step, moves the cognitive load back to the
agent (where it belongs) and lets the user act as a reviewer instead
of an author. Codebase precedence means the user is asked only when
the agent genuinely cannot find out for itself.

The walk is **uniformly sequential for dependent decisions** — there
is no "shallow tree" escape hatch that re-enables batching just
because the tree feels small. The reason is twofold. First, the
requirement (`grill-me`-style "ask one at a time") does not have a
small-tree carve-out for dependent nodes, and adding one quietly
drifts the behavior back toward the batched interview the walk was
meant to replace. Second, the per-round latency saved by batching
two trivial-looking dependent nodes is small compared to the cost
of a single misclassified pair that turns out to share a hidden
edge. The asymmetry favors sequential walking even when the
marginal round feels redundant.

The narrow exception is the briefset *independence-confirmed*
carve-out (see `briefset.md`): when the input maps 1:1 to children
and per-child decisions are demonstrably independent, decomposition
and per-child work types may be confirmed in a single batched
prompt. That carve-out is justified specifically because
independence is the precondition — not a small-tree heuristic —
and removing it would force the agent to invent ceremonial single
rounds for cases where there is no decision to walk.

If a walk feels like it is dragging — many sequential yes-or-no
confirmations, no real branch points — that is a signal that codebase
precedence under-fired (probes that could have resolved nodes were
not attempted) or that nodes were carried into Stage 4 that Stage 3
should have settled. Tighten the codebase pass next time, not the
walk policy.
