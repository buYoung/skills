# Stage 4 User Decision Table

`task-brief-creator` closes residual ambiguity through one policy: first gather enough codebase context in Stage 3, then present every remaining user-owned decision in a Markdown decision table.
The user reviews concrete recommended changes, not vague questions.

This is the only Stage 4 path.
Do not run a pre-review guessing interview.
Do not hide decisions in prose.
If the codebase can answer a technical fact, resolve it before asking.
If the decision is about product intent, scope, a compatibility break, external ownership, or an acceptance threshold, ask the user with the table format below.
Do not ask the user to settle work type, output mode, codebase facts, or reversible implementation choices when the input and repository make them clear.

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
Desired Outcome (To-Be)
   ├─ In Scope boundary
   │  └─ Out of Scope guardrails
   ├─ User-owned Acceptance Criteria thresholds
   └─ Type-conditional user input (only if type is fix/perf/refactor)
      ├─ fix      → Reproduction
      ├─ perf     → Baseline Measurement
      └─ refactor → Behavior Contract
Residual Open Questions (only non-blocking user-owned decisions with a safe default)
```

Briefset root layout:

```
User-owned topology constraints, when any
└─ Per-child residuals
   ├─ child Acceptance Criteria thresholds
   ├─ child Out of Scope boundaries
   └─ child Open Questions
```

Tree-construction rules:

- A row is only worth asking if the user must decide something.
  If a node maps to "general background", drop it — Stage 4 is not a context-gathering interview.
- Each row maps to a concrete brief change: add, remove, narrow, broaden, split, defer, or keep as a structured non-blocking `Open Questions` item with a safe default.
- If one decision changes whether another is relevant, state the dependency in `근거` and order the rows parent-before-child.
  After the user answers, prune irrelevant rows before applying changes.
- If a node can be answered by reading the codebase, mark it *codebase-resolvable* and resolve it before the table.
  If it needs deeper technical investigation, put that work into `Execution Plan` with a `Replan when` boundary.
  Technical facts do not become user questions.
- Product intent, business rules, future scope, acceptance thresholds, sequencing preferences, and ownership decisions are **not** codebase-resolvable.
  Code findings can support the recommendation, but the user still decides.
- Output mode and work type are author-owned when code and input make them evident.
- A reversible local approach is worker-owned and belongs in `Worker decision`, not the table.

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
│           Add a table row only if the underlying choice is user-owned;
│           otherwise add an investigation stage, `Worker decision`,
│           `Replan when`, constraint, or safe default.
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
If a technical node would need a deep dive, stop the authoring probe and route it into an `Execution Plan` investigation stage with a concrete deliverable and `Replan when` boundary.
Ask only when the unresolved node is a decision the user owns.

When the carry-over budget is exhausted, stop running probes and ask the user only for user-owned decisions.
Technical unknowns belong in a bounded investigation stage and must name what evidence changes the plan.
Do not put them in `Open Questions` or silently continue exploring.

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
  This can be "include in scope", "exclude from scope", or "keep as a structured non-blocking Open Question with this safe default".
- **`근거`** — concise evidence from the input, codebase review, existing patterns, or risk.
  Mention paths or symbols when they are the reason for the recommendation.

Rules:

- Do not use a generic `추가/수정?` prompt as the only question when any user-owned decision remains.
- Do not collapse multiple unrelated decisions into one row.
- If a list-shaped section (`Acceptance Criteria`, `Constraints`, candidate `Open Questions`) contains multiple user-owned tradeoffs, make one row per tradeoff.
- If the list is already fully determined by the input and codebase, no table row is needed; write it directly into the brief.
- If the table has many rows, group them by section in the `내용` text, but keep the four-column table shape.
- After the user answers, apply the decision to the draft brief plan.
  If an answer invalidates later rows, drop or revise those rows before continuing.
- A timeout, cancellation, or no response is not approval.
  For a non-blocking row that already names a safe fallback and reconfirmation point, activate that fallback, preserve the row in structured `Open Questions` form, and continue without another approval round.
  For any blocking row, halt without writing.
- If a saved single brief or briefset contains structured non-blocking `Open Questions`, present those items after save using the same four-column table and patch the saved file after the user answers.
- Never use a row to delegate a technical unknown to a reviewer or downstream worker.

---

## Termination Conditions

Proceed to Stage 5 only when **any** of these is true:

- Every mandatory user-owned decision is decided (the brief can be drafted).
- The user explicitly stops (`stop`, `enough`, `그만`, `충분해`, `done`) and no blocking user-owned decision remains; otherwise halt without writing.
- Every remaining user-owned decision is non-blocking, has a safe fallback, and has a reconfirmation point; save each one as `- [non-blocking] <question> — Default: <safe fallback>; Reconfirm before: <stage or milestone>`.

If a user-owned decision has no safe fallback and execution cannot continue without it, **HALT** in Stage 4 and create no file.
External ownership does not make a blocking decision safe to defer.
If the user does not answer, cancels, or lets structured input expire, apply the same split: non-blocking rows use their declared fallback and proceed to Stage 5; any blocking row halts without writing.
Silence never changes a row's ownership or counts as approval.

After a safe termination, proceed to Stage 5 (save + structural validate), Stage 5.5 (downstream execution reconstruction), and Stage 5.6 (content and executability self-check) exactly as documented in `SKILL.md`, then cold-pickup verification (Stage 5.7) when its gate fires.
Stage 4 does not change the saved-brief structure.

---

## Output Identity

The decision table is a **behavior variant of the brief-authoring pipeline**, not an output variant.
The saved brief still follows `references/template.md` exactly:

- Nine required H2 sections (`Work Type`, `Current State (As-Is)`, `Desired Outcome (To-Be)`, `Scope`, `Related Files / Entry Points`, `Execution Plan`, `Side Effect Checkpoints`, `Acceptance Criteria`, `Open Questions`).
- Type-conditional H2 (`Reproduction` / `Baseline Measurement` / `Behavior Contract`) when the type demands it.
- Optional `Constraints` block between `Scope` and `Related Files / Entry Points` when task-specific constraints exist.
- Briefset parent + children when briefset mode is also active.

`scripts/validate_brief.py` and `scripts/validate_briefset.py` apply unchanged.
A brief that fails the validator failed for the same reasons regardless of which Stage 4 path produced it.

---

## Briefset Interaction

Briefset mode uses the same decision-table policy.
The author determines decomposition, child types, ordering, parallelization, and conflict rules when the code and input make them evident.
Table only user-owned constraints that would change that topology, followed by per-child residual decisions.

Workflow notes:

- Put briefset decisions in the same four-column table.
  Use `내용` to identify whether the row belongs to the parent or to a child.
- Per-child user-owned `Acceptance Criteria` thresholds and `Out of Scope` decisions come after the parent topology is locked.
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
  Residual technical ambiguity belongs in an investigation stage, `Worker decision`, or `Replan when`, not in another table round or `Open Questions`.

---

## Why This Shape

The decision table optimizes for **visible decision ownership**.
The agent does the codebase work first, then shows the user only the decisions the user actually owns, with a concrete recommended change and evidence.
This prevents two failure modes: asking speculative questions before understanding the code, and silently burying decisions inside `Open Questions` or generic "add/change?" prompts.

The four-column table also makes post-save `Open Questions` actionable.
If a single brief or a briefset still contains user-decision questions, the user sees the same shape after save and the agent patches the saved file after the answers land.
