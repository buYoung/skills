# Work Types (Conventional Commits)

The work type is a load-bearing field in the implementation work plan.
It changes how the downstream coding agent approaches the task — not just how the commit is labeled.

A `refactor` agent obsesses over behavior preservation and writes a before/after diff.
A `fix` agent starts by reproducing the bug.
A `perf` agent measures first and second-guesses micro-optimizations.
One token flips the behavior profile.
Classify it from the input and codebase whenever the evidence is clear; do not turn an obvious technical classification into a user decision.

---

## The Ten Types

| Type | Meaning | Downstream agent behavior profile |
|---|---|---|
| `feat` | New feature — user-visible capability that did not exist. | Discovery-oriented; asks about UX edge cases; uses existing verification first; adds tests only when the user or repo rules allow it. |
| `fix` | Bug fix — existing behavior is wrong. | Reproduction-first; pins the failure before patching, using existing tests or manual repro first; adds a failing test only when allowed. |
| `refactor` | Structural change with **no behavior change**. | Behavior-preservation obsessed; relies on existing tests as the contract. |
| `perf` | Performance improvement. | Measurement-first; baseline before, benchmark after; rejects un-measured "optimizations". |
| `chore` | Build / dependency / config / misc maintenance. | Low-ceremony; skims; no test expectation unless logic moved. |
| `docs` | Documentation-only change. | Editorial pass; no code execution expected. |
| `test` | Adding or fixing tests. | Coverage-oriented; does not change production code. |
| `style` | Formatting, whitespace, semicolons — no logic effect. | Tool-driven (formatter); reviews diff for accidental logic drift. |
| `build` | Build system / package manager change. | Verifies clean build on all supported targets after change. |
| `ci` | CI config change. | Verifies pipeline still green on a dry-run branch. |

---

## Required Additional Section per Type

The work type changes downstream agent behavior.
The brief makes that change *possible* by carrying type-specific input the agent needs.
Three types require an extra H2 section between `Current State (As-Is)` and `Desired Outcome (To-Be)`:

| Type | Required Section | Why this section, for this type |
|---|---|---|
| `fix` | `## Reproduction` | The reproduction-first profile needs the repro pinned (steps, environment, frequency, observed vs expected) — not buried in As-Is. The agent verifies against this section, using existing checks first and adding a failing test only when allowed. |
| `perf` | `## Baseline Measurement` | The measurement-first profile needs the baseline number stated explicitly (current measurement, method, environment, target). Without it, "improvement" is unverifiable. |
| `refactor` | `## Behavior Contract` | The behavior-preservation profile needs the contract named: which observable behaviors must stay invariant, which tests / specs / artifacts lock them, how preservation is verified. |

The other seven types (`feat`, `chore`, `docs`, `test`, `style`, `build`, `ci`) use the nine required sections only, including `Execution Plan`.

When the section legitimately has nothing concrete to capture (e.g., a visual-regression `fix` whose entire repro is "open the page"), the brief may use a single bullet: `- N/A — <one-line reason>`.
The section itself must still be present; `validate_brief.py` checks for it.

See `template.md` for the per-section writing guidance and examples.

Tie the type-conditional section to the first execution stage:

- `fix` — Stage 1 starts from the documented reproduction inputs and ends with the failure pinned or a named replan condition.
- `perf` — Stage 1 starts from the measurement method and ends with a confirmed baseline on the stated environment.
- `refactor` — Stage 1 starts from the behavior contract and ends with the preservation baseline verified before structural edits begin.

Do not let a worker skip these gates and jump directly to implementation.

---

## Classification Tips

### When the user says "refactor" but describes behavior change

Reclassify from the described outcome and explain the mismatch.
A refactor *by definition* preserves behavior.
If the user says "refactor the auth middleware to also log failed attempts", the logging is a `feat`.
Options to surface:

- Split into two briefs: a pure `refactor` followed by a `feat`.
  Splitting means applying the briefset criteria in `briefset.md`; select briefset mode when the execution-context split is clear, otherwise keep a single brief with type `feat`.
- Reclassify the whole thing as `feat` and note the refactor as an implementation detail.

Ask the user only when resolving the mismatch requires a user-owned scope or behavior choice, such as whether logging is actually part of the requested outcome.

### `feat` vs `fix` — when behavior "should have worked"

If the user says "login should support SSO but doesn't" — that's `feat`, not `fix`.
`fix` is reserved for behavior that *was previously working* or that the spec explicitly promised and the code broke.
A never-implemented capability is `feat`.

Gray zone: if a prior release implicitly promised a capability (e.g., the marketing page claimed it), the user may reasonably want `fix`.
Probe the spec or release evidence first; ask only if the promised behavior itself is a user-owned interpretation.

### Reverts are written as `fix`

Reverts are intentionally not a separate work type.
Write a revert as `fix` — the current behavior is wrong — and name the offending commit/PR in `Constraints`.

### `chore` vs `build` vs `ci`

- `build` = anything that changes how artifacts are produced (webpack config, `Cargo.toml` dependencies, Dockerfile for the shipped image).
- `ci` = anything that changes how CI runs (GitHub Actions workflows, deploy pipelines, test orchestration in CI only).
- `chore` = everything else that's maintenance (dependency bumps that don't change build config, gitignore updates, editor config).

When in doubt, pick the more specific of the three — `build` and `ci` trigger more focused verification behaviors than `chore`.

### `perf` vs `refactor`

If the change is motivated by speed/memory but happens to also reorganize code, it's `perf`.
The performance framing pulls in measurement discipline that `refactor` does not demand.
Only use `refactor` when speed is genuinely not the goal.

Tiebreak: `perf` applies only when the deliverable itself is a measured improvement of existing behavior; a new capability with a performance budget is `feat`, with the budget recorded in `Constraints`.

### `style` is narrower than it sounds

`style` is for changes a formatter would make — whitespace, quote style, trailing commas, semicolons.
Renaming a variable is **not** `style`; it's `refactor` (structural change without behavior change).

---

## Author Selection Pattern

The plan author owns work-type classification when the code and input make it evident.

- **Explicit type from user, evidence agrees** → use it.
- **Explicit type from user, evidence conflicts** → classify by the requested outcome and record the mismatch in the plan-authoring report.
  Ask only if the conflict hides a user-owned behavior or scope decision.
- **Implicit type, high-confidence** → assign it without a confirmation round-trip.
- **Implicit type, low-confidence but technically resolvable** → probe the codebase or put the distinction into the first `Execution Plan` stage as an investigation with a `Replan when` boundary.
- **Implicit type depends on user intent** → ask the underlying product or scope decision in Stage 4, then derive the type from the answer.

Do not ask the user to choose among commit labels when the real uncertainty is technical.
Do not store type uncertainty in `Open Questions`; the saved plan must already carry the work type and the execution behavior it activates.
