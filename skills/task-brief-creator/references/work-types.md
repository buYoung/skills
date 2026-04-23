# Work Types (Conventional Commits)

The work type is the single most load-bearing field in the brief. It changes
how the downstream coding agent approaches the task — not just how the commit
is labeled.

A `refactor` agent obsesses over behavior preservation and writes a before/after
diff. A `fix` agent starts by reproducing the bug. A `perf` agent measures
first and second-guesses micro-optimizations. One token flips the behavior
profile. Classifying correctly is worth the one clarifying question it may
cost.

---

## The Ten Types

| Type | Meaning | Downstream agent behavior profile |
|---|---|---|
| `feat` | New feature — user-visible capability that did not exist. | Discovery-oriented; asks about UX edge cases; expects new tests. |
| `fix` | Bug fix — existing behavior is wrong. | Reproduction-first; writes a failing test before patching. |
| `refactor` | Structural change with **no behavior change**. | Behavior-preservation obsessed; relies on existing tests as the contract. |
| `perf` | Performance improvement. | Measurement-first; baseline before, benchmark after; rejects un-measured "optimizations". |
| `chore` | Build / dependency / config / misc maintenance. | Low-ceremony; skims; no test expectation unless logic moved. |
| `docs` | Documentation-only change. | Editorial pass; no code execution expected. |
| `test` | Adding or fixing tests. | Coverage-oriented; does not change production code. |
| `style` | Formatting, whitespace, semicolons — no logic effect. | Tool-driven (formatter); reviews diff for accidental logic drift. |
| `build` | Build system / package manager change. | Verifies clean build on all supported targets after change. |
| `ci` | CI config change. | Verifies pipeline still green on a dry-run branch. |

---

## Classification Tips

### When the user says "refactor" but describes behavior change

Push back. A refactor *by definition* preserves behavior. If the user says
"refactor the auth middleware to also log failed attempts", the logging is a
`feat`. Options to surface:

- Split into two briefs: a pure `refactor` followed by a `feat`.
- Reclassify the whole thing as `feat` and note the refactor as an
  implementation detail.

### `feat` vs `fix` — when behavior "should have worked"

If the user says "login should support SSO but doesn't" — that's `feat`, not
`fix`. `fix` is reserved for behavior that *was previously working* or that
the spec explicitly promised and the code broke. A never-implemented
capability is `feat`.

Gray zone: if a prior release implicitly promised a capability (e.g., the
marketing page claimed it), the user may reasonably want `fix`. Confirm.

### `chore` vs `build` vs `ci`

- `build` = anything that changes how artifacts are produced (webpack
  config, `Cargo.toml` dependencies, Dockerfile for the shipped image).
- `ci` = anything that changes how CI runs (GitHub Actions workflows,
  deploy pipelines, test orchestration in CI only).
- `chore` = everything else that's maintenance (dependency bumps that
  don't change build config, gitignore updates, editor config).

When in doubt, pick the more specific of the three — `build` and `ci`
trigger more focused verification behaviors than `chore`.

### `perf` vs `refactor`

If the change is motivated by speed/memory but happens to also reorganize
code, it's `perf`. The performance framing pulls in measurement discipline
that `refactor` does not demand. Only use `refactor` when speed is genuinely
not the goal.

### `style` is narrower than it sounds

`style` is for changes a formatter would make — whitespace, quote style,
trailing commas, semicolons. Renaming a variable is **not** `style`; it's
`refactor` (structural change without behavior change).

---

## Confirmation Question Pattern

When the type is not explicit in the input, ask one question during Stage 2.
Use the user's chat language.

**English:**

> I'd like to classify this as `<inferred>` — does that match? The type
> changes how the downstream agent works — e.g. `refactor` focuses on
> behavior preservation, `fix` starts from a reproduction. Tell me if a
> different type fits better.

**Korean:**

> 작업 유형을 `<inferred>`로 잡을 생각인데 맞아? 유형에 따라 에이전트
> 접근 방식이 달라져서 — 예를 들어 `refactor`면 동작 보존에 집중하고
> `fix`면 재현부터 시작해. 다른 유형이 더 적절하면 말해줘.

Offer 2–3 alternatives if the classification was close. Do not list all ten
— that's noise.
