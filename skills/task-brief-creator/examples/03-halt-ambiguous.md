# Example 03 — Halt on ambiguous input

The four-anchor check rejects the input. Skill responds with a halt message instead of producing a brief.

**What this example shows:** the most expensive failure mode of a brief generator is producing a *confident-looking* work instruction from underspecified input. A coding agent that picks up such a brief commits to the wrong problem framing and burns the entire implementation cycle. The halt is what protects the agent from that outcome.

---

## Input (typed by user)

```
clean up the auth stuff
```

---

## Anchor Check (Stage 1)

| Anchor | Derivable? | Reasoning |
|---|---|---|
| **PROBLEM** | ✗ | "Clean up" names no concrete defect, smell, or constraint. Could mean dead-code removal, restructuring, dependency upgrade, dead-route deletion, lint-fix, security tightening — any of these is "cleanup". The downstream agent has no way to choose. |
| **GOAL** | ✗ | No end-state is described. "Cleaner" is not a verifiable state. |
| **SCOPE** | ✗ | "Auth stuff" is gestural — does it mean the login UI, the session backend, the OAuth integration, the middleware, the password-reset flow, or all of them? |
| **TARGET** | ✗ | "Auth" is a domain hint, not a target. The repo plausibly has 5+ files matching the term, and Stage 3 review cannot disambiguate without a guiding intent (intent should come from the user, not be inferred). |

**Anchors present: 0 / 4** → **HALT**.

---

## Halt Response

The skill replies in the user's chat language. Both versions follow.

**English:**

> I can't ground a brief from this input alone. All four anchors are missing — I can't tell **what** is wrong (PROBLEM), **what** should be true at the end (GOAL), **which slice** of auth is in play (SCOPE), or **which files / subsystem** to target (TARGET).
>
> Could you add a couple of lines? A few prompts that usually unblock this:
> - Is there a specific behavior, smell, or risk you want to address? (e.g., "session tokens are being stored in localStorage and security wants them in HttpOnly cookies")
> - Is this scoped to a specific module? (e.g., login UI, the session middleware, the OAuth callback)
> - What does "done" look like to you?

**Korean:**

> 입력만으로는 브리핑 만들기 어려워. 무엇이 문제인지(PROBLEM), 끝나면 어떤 상태여야 하는지(GOAL), 인증 중 어느 부분이 대상인지(SCOPE), 어떤 파일이나 모듈을 건드리는지(TARGET)를 모두 알 수 없어.
>
> 한두 줄만 더 써 줄래? 이런 걸 알려 주면 바로 진행할 수 있어:
> - 고치고 싶은 구체적인 동작이나 코드 문제, 위험이 있어? (예: "세션 토큰이 localStorage에 저장돼 있는데 보안팀에서 HttpOnly 쿠키로 옮기길 원해")
> - 특정 모듈에 한정된 작업이야? (로그인 UI, 세션 미들웨어, OAuth 콜백 등)
> - 어떻게 되면 끝난 거야?

---

## Notes

- **Why this halts even though the user did say something** — word count is not a proxy for the four anchors. "Clean up the auth stuff" has intent (`cleanup`) but no actionable signal.
- **What additional input would flip this to CONTINUE** — any one of:
  - A concrete defect (PROBLEM) — "session tokens in localStorage" → 1 anchor present, still halt at 1/4.
  - A defect + a target (PROBLEM + TARGET) — "session tokens in localStorage in `src/auth/session.ts`" → 2 anchors, still halt (threshold is 3+).
  - A defect + an end state + a scope hint (PROBLEM + GOAL + SCOPE) — "session tokens are in localStorage; move them to HttpOnly cookies for the web app" → 3 anchors with TARGET missing. The gate does not CONTINUE on faith: it runs a narrow target probe first (a couple of `rg` queries such as `rg "localStorage" -t ts src` and `rg "setItem.*token"`). Here the probe surfaces `src/auth/session.ts` as a concrete entry point, so **CONTINUE**. Had the probe found no concrete entry point, the gate would still HALT and ask for the target area.
- **Why not just guess the most likely interpretation** — the cost of a wrong-framing brief is the entire downstream implementation cycle. The cost of pushing back is one round-trip with the user. The asymmetry is the whole point of the Ambiguity Gate.
- **What the skill does NOT do here** — it does not start a Stage 3 codebase review on the chance that reading `src/auth/*` will surface a likely intent. That would be the agent picking a problem for the user, which is exactly what the gate prevents.

---

## What the Halt Prevented — Sketch of a Fabricated Brief

If the skill had pushed past the gate, the most plausible (and most dangerous) output would have looked something like this — a brief that *reads* like a competent work instruction but commits to a problem the user did not state:

```markdown
# [refactor] Tidy auth module structure

## Work Type
refactor

## Current State (As-Is)
- `src/auth/` has accumulated overlapping helpers across login, session, OAuth, and password reset.
- Some files exceed 400 lines.

## Behavior Contract
- Locked: public exports of `src/auth/index.ts`.
- Contract artifacts: existing `src/auth/__tests__/*` suite.
- Verification: full suite green.

## Desired Outcome (To-Be)
- Auth modules are smaller and follow consistent naming.

## Scope
### In Scope
- Restructure files inside `src/auth/`.
### Out of Scope
- Behavior changes.

## Related Files / Entry Points
- `src/auth/` — entire directory.

## Side Effect Checkpoints
- [ ] Full test suite passes.

## Acceptance Criteria
- [ ] Files are smaller.
- [ ] Naming is consistent.

## Open Questions
- None
```

A coding agent picking this up would restructure `src/auth/`, land a 1500-line PR, and discover at review that the user actually wanted **session tokens moved out of localStorage for security** — a different problem, in different files, possibly a `feat` rather than a `refactor`.

(The sketch is also deliberately malformed *structurally*: it omits the required `## Execution Plan`, its load-bearing `Current State (As-Is)` bullets lack `[confirmed]` / `[inferred]`, its `Out of Scope` exclusion lacks `[hard]` / `[deferred]`, and its bare `- None` under `Open Questions` lacks `— <reason>`. `validate_brief.py` reports all four contract failures. The deeper failure is still the fabricated problem framing, which no structural validator can catch.)
