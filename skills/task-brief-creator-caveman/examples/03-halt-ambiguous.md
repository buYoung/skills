# Example 03 — Halt on ambiguous input

The four-anchor check rejects the input. Skill responds with a halt
message instead of producing a brief.

**What this example shows:** the most expensive failure mode of a brief
generator is producing a *confident-looking* work instruction from
underspecified input. A coding agent that picks up such a brief commits to
the wrong problem framing and burns the entire implementation cycle. The
halt is what protects the agent from that outcome.

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

> I can't ground a brief from this input alone. All four anchors are
> missing — I can't tell **what** is wrong (PROBLEM), **what** should be
> true at the end (GOAL), **which slice** of auth is in play (SCOPE), or
> **which files / subsystem** to target (TARGET).
>
> Could you add a couple of lines? A few prompts that usually unblock this:
> - Is there a specific behavior, smell, or risk you want to address?
>   (e.g., "session tokens are being stored in localStorage and security
>   wants them in HttpOnly cookies")
> - Is this scoped to a specific module? (e.g., login UI, the session
>   middleware, the OAuth callback)
> - What does "done" look like to you?

**Korean:**

> 입력만으로는 브리핑 만들기 어려워. 네 앵커가 전부 부족해 — **무엇이**
> 문제인지(PROBLEM), **끝났을 때 뭐가 사실이어야** 하는지(GOAL), 인증
> 영역의 **어느 슬라이스**가 대상인지(SCOPE), **어느 파일/서브시스템**을
> 건드리는지(TARGET) 다 잡히질 않아.
>
> 한두 줄만 더 얹어줄래? 막힘이 자주 풀리는 질문 몇 개:
> - 고치고 싶은 구체적인 동작/냄새/리스크가 있어?
>   (예: "세션 토큰이 localStorage에 저장돼 있는데 보안팀에서 HttpOnly
>   쿠키로 옮기길 원해")
> - 모듈이 특정돼 있어? (로그인 UI, 세션 미들웨어, OAuth 콜백 등)
> - "끝"이 어떤 모습이야?

---

## Notes

- **Why this halts even though the user did say something** — word count
  is not a proxy for the four anchors. "Clean up the auth stuff" has
  intent (`cleanup`) but no actionable signal. A brief produced from
  this would commit to a problem framing the user did not intend, and
  the downstream agent would build the wrong thing confidently.
- **What additional input would flip this to CONTINUE** — any one of:
  - A concrete defect (PROBLEM) — "session tokens in localStorage" → 1
    anchor present, still halt at 1/4.
  - A defect + a target (PROBLEM + TARGET) — "session tokens in
    localStorage in `src/auth/session.ts`" → 2 anchors, still halt
    (threshold is 3+).
  - A defect + an end state + a scope hint (PROBLEM + GOAL + SCOPE) —
    "session tokens are in localStorage; move them to HttpOnly cookies
    for the web app" → 3 anchors, **CONTINUE**. TARGET will be filled
    in Stage 3 codebase review.
- **Why not just guess the most likely interpretation** — the cost of a
  wrong-framing brief is the entire downstream implementation cycle.
  The cost of pushing back is one round-trip with the user. The
  asymmetry is the whole point of the Ambiguity Gate.
- **What the skill does NOT do here** — it does not start a Stage 3
  codebase review on the chance that reading `src/auth/*` will surface
  a likely intent. That would be the agent picking a problem for the
  user, which is exactly what the gate prevents.

---

## What the Halt Prevented — Sketch of a Fabricated Brief

If the skill had pushed past the gate, the most plausible (and most
dangerous) output would have looked something like this — a brief that
*reads* like a competent work instruction but commits to a problem the
user did not state:

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

A coding agent picking this up would happily restructure `src/auth/`,
land a 1500-line PR, and discover at review that the user actually
wanted **session tokens moved out of localStorage for security** — a
totally different problem, in different files, possibly a `feat`
rather than a `refactor`. The cost is the entire restructuring cycle
plus the rework. That is the asymmetry the halt protects against.
