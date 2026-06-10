# Stage 4 User Decision Table

`task-brief-creator` closes residual ambiguity through one policy: first gather enough codebase context in Stage 3, then present every remaining user-owned decision in a Markdown decision table.
The user reviews concrete recommended changes, not vague questions.

This is the only Stage 4 path.
Do not run a pre-review guessing interview.
Do not hide decisions in prose.
If the codebase can answer a technical fact, resolve it before asking.
If the decision is about product intent, scope, acceptance threshold, risk tolerance, sequencing, or ownership, ask the user with the table format below.

For user-decision questions, use this exact table shape:

```markdown
| 순번 | 내용 | 수정 추천안 | 근거 |
|---|---|---|---|
| 1 | <decision the user must make> | <recommended change to apply to the brief> | <input/codebase evidence and risk> |
```

Keep these four headers exactly as written, even when the surrounding conversation is not Korean.
They are the stable decision-table contract: number, decision content, recommended change, and rationale.

---

## Decision Collection

Before presenting the table, build a decision register from Stage 3 review notes plus residual input gaps.
The register drives what goes into the table.

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

- A row is only worth asking if the user must decide something.
  If a node maps to "general background", drop it — Stage 4 is not a context-gathering interview.
- Each row maps to a concrete brief change: add, remove, narrow, broaden, split, defer, keep as `Open Questions`, or delegate to the downstream agent.
- If one decision changes whether another is relevant, state the dependency in `근거` and order the rows parent-before-child.
  After the user answers, prune irrelevant rows before applying changes.
- If a node can be answered by reading the codebase, mark it *codebase-resolvable* and resolve it before the table.
  Technical facts do not become user questions.
- Product intent, business rules, future scope, acceptance thresholds, sequencing preferences, and ownership decisions are **not** codebase-resolvable.
  Code findings can support the recommendation, but the user still decides.

---

## Codebase Precedence Flow

Stage 4 honors the explore-first rule.
For each candidate decision, run this check before adding a row:

```
Can a narrow codebase probe answer this node?
├─ YES → run the probe within the carry-over budget.
│        ├─ Probe resolves the node →
│        │  Do not ask. Carry the result into the brief or into
│        │  the `근거` for a related user-owned decision.
│        └─ Probe inconclusive →
│           Add a table row if the user can decide; otherwise keep
│           the uncertainty in `Open Questions`.
└─ NO  → Add a table row when the node is user-owned.
```

### Carry-over budget

Stage 3's review budget (~15 reads / ~10 queries) is a soft limit across the entire codebase pass.
Stage 4 inherits any unused budget plus a small additional cap reserved for branch probes:

| Source | Soft cap |
|---|---|
| Stage 3 unused | whatever remains |
| Stage 4 additional | ~5 reads / ~3 queries |

Per-node ceiling: 1–2 queries per branch probe.
If a single node would need a deep dive, that is a signal the question belongs to the user, not the codebase.

When the carry-over budget is exhausted, stop running probes and ask the user only for user-owned decisions.
Technical unknowns that neither the current budget nor the user can answer belong in `Open Questions`.
Do not silently continue exploring.

---

## Decision Table Rules

User-facing Stage 4 questions go through a Markdown table.
Use the host's structured user-input tool when available; otherwise send the table in chat and explicitly ask the user to approve, edit, or answer by row number.

Each row follows this contract:

- **`순번`** — stable row number.
  The user can answer "1 OK, 2 change to..." without quoting the whole table.
- **`내용`** — the actual decision the user must make.
  Phrase it as a decision question, not as background.
- **`수정 추천안`** — the concrete change you recommend applying to the brief.
  This can be "include in scope", "exclude from scope", "split into a child brief", "keep as Open Questions", or "delegate to downstream agent".
- **`근거`** — concise evidence from the input, codebase review, existing patterns, or risk.
  Mention paths or symbols when they are the reason for the recommendation.

Rules:

- Do not use a generic `추가/수정?` prompt as the only question when any user-owned decision remains.
- Do not collapse multiple unrelated decisions into one row.
- If a list-shaped section (`Acceptance Criteria`, `Side Effect Checkpoints`, `Constraints`, candidate `Open Questions`) contains multiple user-owned tradeoffs, make one row per tradeoff.
- If the list is already fully determined by the input and codebase, no table row is needed; write it directly into the brief.
- If the table has many rows, group them by section in the `내용` text, but keep the four-column table shape.
- After the user answers, apply the decision to the draft brief plan.
  If an answer invalidates later rows, drop or revise those rows before continuing.
- If a saved single brief or briefset contains `Open Questions` that require user decisions, present those items after save using the same four-column table and patch the saved file after the user answers.

---

## Termination Conditions

Stop the Stage 4 loop when **any** of these is true:

- Every mandatory user-owned decision is decided (the brief can be drafted).
- The user explicitly stops (`stop`, `enough`, `그만`, `충분해`, `done`).
- Carry-over codebase budget is exhausted **and** every remaining node is unanswerable by the user without external input — record those as `Open Questions` and continue to Stage 5.
- A pending answer requires information neither the codebase nor the user has at hand (e.g., a product decision owned by someone else).
  Record the dependency in `Open Questions`, mark the brief as blocked on that input, and continue.

After termination, proceed to Stage 5 (save + structural validate) and Stage 5.5 (content-level self-check) exactly as documented in `SKILL.md`, then cold-pickup verification (Stage 5.6) when its gate fires.
Stage 4 does not change the saved-brief structure.

---

## Output Identity

The decision table is a **behavior variant of the brief-authoring pipeline**, not an output variant.
The saved brief still follows `references/template.md` exactly:

- Eight required H2 sections (`Work Type`, `Current State (As-Is)`, `Desired Outcome (To-Be)`, `Scope`, `Related Files / Entry Points`, `Side Effect Checkpoints`, `Acceptance Criteria`, `Open Questions`).
- Type-conditional H2 (`Reproduction` / `Baseline Measurement` / `Behavior Contract`) when the type demands it.
- Optional `Constraints` block between `Scope` and `Related Files / Entry Points` when task-specific constraints exist.
- Briefset parent + children when briefset mode is also active.

`scripts/validate_brief.py` and `scripts/validate_briefset.py` apply unchanged.
A brief that fails the validator failed for the same reasons regardless of which Stage 4 path produced it.

---

## Briefset Interaction

Briefset mode uses the same decision-table policy.
Decomposition is usually the highest-value user decision, and parent topology often contributes several table rows: decomposition validity, ordering, parallelization, conflict hotspots, and per-child residual decisions.

Workflow notes:

- Put briefset decisions in the same four-column table.
  Use `내용` to identify whether the row belongs to the parent or to a child.
- Per-child `Acceptance Criteria` and `Out of Scope` decisions come after the parent topology is locked.
  Asking them earlier produces guardrails for children that may not survive the decomposition decision.
- Children inherit decision-table question output but are still saved as standard child briefs (`validate_briefset.py` covers them transitively).

---

## Anti-patterns

Do not:

- **Use the decision table on a halt-eligible input.** Two missing anchors do not become four answered anchors through a long table; they become a confidently wrong brief.
  Halt at Stage 1 first.
- **Skip codebase precedence to "save round-trips".** The whole point is asking only the questions that need asking.
  If a probe could answer it, run the probe.
- **Hide dependent decisions inside one vague row.** When one decision's answer reshapes another's relevance, make the dependency explicit in `근거` and be ready to prune or revise later rows after the user answers.
- **Ask the same question twice with different framings.** If the user gave a clear answer, accept it and move on.
  Repeated asks signal the agent did not believe the user, which is corrosive.
- **Drop `수정 추천안`.** A naked "what do you want?" offloads the design problem to the user.
- **Loop forever.** Honor the termination conditions.
  Residual ambiguity that is not user-owned belongs in `Open Questions`, not in another table round.

---

## Why This Shape

The decision table optimizes for **visible decision ownership**.
The agent does the codebase work first, then shows the user only the decisions the user actually owns, with a concrete recommended change and evidence.
This prevents two failure modes: asking speculative questions before understanding the code, and silently burying decisions inside `Open Questions` or generic "add/change?" prompts.

The four-column table also makes post-save `Open Questions` actionable.
If a single brief or a briefset still contains user-decision questions, the user sees the same shape after save and the agent patches the saved file after the answers land.
