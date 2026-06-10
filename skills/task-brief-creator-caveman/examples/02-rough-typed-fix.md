# Example 02 — Rough typed input → `fix` (iOS Safari login bug)

Single-line typed input. Skill clears the four-anchor gate (PROBLEM,
GOAL implicit, SCOPE narrow, TARGET findable), then leans on the `fix`
behavior profile to shape Acceptance Criteria around reproduction.

**What this example produces:** a saved brief with a pinned `Reproduction`
that lets a coding agent commit a failing test *before* touching code —
the load-bearing discipline of `fix`-type work. Treat the saved brief as
the work instruction; the meta sections show how a one-line input got
ground enough to support it.

---

## Input (typed by user)

```
login breaks on iOS Safari when password contains `@`
```

---

## Codebase Review Notes (Stage 3)

Inline `rg` / `Read`, ~5 reads / 6 greps:

- `src/auth/LoginForm.tsx` — form submission handler. Calls
  `validatePassword()` then POSTs to `/api/login`.
- `src/auth/validation.ts:34` — `validatePassword()` runs a
  `decodeURIComponent` on the input as part of a defensive cleanup that
  was added in PR #211. **Hypothesis:** on iOS Safari, the keyboard
  inserts `@` as a literal that interacts badly with this decode step
  (`%` being absent makes the call mostly a no-op except in edge cases
  involving lone `%` characters near `@`). Needs reproduction to confirm.
- `cypress/e2e/login.cy.ts` — existing E2E suite. Has a "valid login"
  case but no characters-in-password edge cases.
- No iOS Safari-specific test harness; team uses BrowserStack on demand.

---

## Stage 4 — User Decision Table

Stage 3 already pins the suspected interaction site. Stage 4 asks for
the remaining user-owned decisions needed to make a `fix` brief safe:
reproduction evidence, scope boundaries, and the treatment of one
reviewer-owned unknown.

| 순번 | 내용 | 수정 추천안 | 근거 |
|---|---|---|---|
| 1 | Work type to write into the brief | Keep `fix`. | The input names a defect: login rejects valid credentials on iOS Safari. |
| 2 | Reproduction detail | Provide the observed environment so it can be pinned in `## Reproduction`: exact iOS Safari version and device, the failing test account (no literal password — name where the secret lives), the observed error surface, and how often it reproduces. | `fix` briefs need a reproducible failing state before implementation. The codebase can identify the likely validation site, but only the user can supply the observed environment, account, and frequency. |
| 3 | Out of Scope boundary | Lock both the broader validation-chain refactor and the `/api/login` request/response contract out of scope. | Stage 3 found both adjacent to the suspected line. Touching them would widen the defect fix into unrelated behavior change. |
| 4 | Acceptance criteria ordering | Require a red Cypress reproduction first, then the fix, then iOS Safari manual verification and full suite pass. | Reproduction-first criteria make the defect non-regression explicit for downstream agents. |
| 5 | Side effect checkpoints | Keep checks for the existing valid-login case, URL-significant password characters, and the PR #211 motivation. | `%`, `+`, and `&` share the same risk surface as `@` because `decodeURIComponent` is the suspected interaction site. |
| 6 | PR #211 remove-vs-patch decision | Carry this as an `Open Questions` item for the reviewer instead of deciding it in the brief. | The original motivation is not recoverable from the current input or code probe, and the downstream reviewer owns whether the cleanup remains necessary. |

User: approve rows 1 and 3-6; for row 2 the user supplies the values —
iOS Safari 17 on iPhone 14 via BrowserStack, QA account
`qa+iossafari@example.com` whose password contains `@` (stored in the
1Password item "QA iOS Safari"), "invalid credentials" toast, 5/5
attempts on fresh sessions, reproducing on both the `main` dev build
and the current production build.

### Termination

All user-owned decisions are decided. `Reproduction` is pinned from the
user's row-2 answer, and the reviewer-owned PR #211 decision is
explicitly carried forward as an `Open Questions` item. Stage 5
follows.

---

## Output (`docs/briefs/2026-04-23-fix-ios-safari-login-at-symbol.md`)

```markdown
# [fix] iOS Safari login fails when password contains `@`

## Work Type
fix

## Current State (As-Is)
- Login flow reject valid credentials on iOS Safari when password contain `@`; same credentials succeed in every other tested browser.
- `validatePassword()` in `src/auth/validation.ts` call `decodeURIComponent` on raw input — likely interaction site (per Stage 3 review).

## Reproduction
- Steps: open `/login` on iOS Safari 17, then enter known-valid QA account `qa+iossafari@example.com` whose password contain `@` (password: see 1Password item "QA iOS Safari"), then tap "Log in".
- Observed: form return "invalid credentials" toast; no network error in dev tools.
- Expected: same credentials succeed (verified working on desktop Safari 17, Chrome 124, Firefox 125 against same backend).
- Environment: iOS Safari 17 on iPhone 14 (BrowserStack); reproduce against `main` branch dev build and current production build.
- Frequency: always — 5/5 attempts on fresh session.

## Desired Outcome (To-Be)
- Login succeed on iOS Safari 17 with passwords containing `@`, match desktop browser behavior.
- Validation chain stay structurally the same; only offending step change.
- Regression test capture bug so it cannot silently return.

## Scope
### In Scope
- Fix validation step in `src/auth/validation.ts` that mishandle `@` on iOS Safari.
- Add Cypress E2E case that exercise failing input.
### Out of Scope
- [hard] Refactor or restructure validation chain beyond offending step.
- [hard] Change `/api/login` request or response contract.
- [deferred] Review other characters that may have similar issues — separate brief if found.

## Related Files / Entry Points
- `src/auth/validation.ts:34` — `validatePassword()`; suspected `decodeURIComponent` interaction with `@` on iOS Safari.
- `src/auth/LoginForm.tsx` — submission handler; call `validatePassword` before POSTing.
- `cypress/e2e/login.cy.ts` — add regression case here.
- PR #211 — introduced `decodeURIComponent` cleanup; check original motivation before remove outright.

## Side Effect Checkpoints
- [ ] Existing `valid login` Cypress case still pass (no regression on happy path).
- [ ] Passwords containing other URL-significant characters (`%`, `+`, `&`) still validate correctly on all browsers.
- [ ] Original motivation for `decodeURIComponent` step (per PR #211) remain addressed, or explicitly noted as obsolete.

## Acceptance Criteria
- [ ] New Cypress case in `cypress/e2e/login.cy.ts` reproduce failure on unfixed code (commit it red first, then fix).
- [ ] New case pass after fix on same iOS Safari target.
- [ ] Manual verification on iOS Safari 17 with QA account's `@`-containing password result in successful login.
- [ ] Full Cypress suite stay green.

## Open Questions
- Is the `decodeURIComponent` step introduced in PR #211 still needed for any class of input it was meant to defend against, or should it be removed entirely instead of patched? Defer to PR review if unclear.
```

---

## Picked Up Cold — Coding Agent's First Actions

A coding agent receiving only the saved brief should reach a red test in
under 30 minutes. From the brief alone:

1. Spin up the documented repro environment (BrowserStack, iOS Safari 17,
   account `qa+iossafari@example.com` with the password from the
   1Password item "QA iOS Safari", per `Reproduction`).
   Confirm the failure on `main` to verify the repro is real.
2. Add a Cypress case in `cypress/e2e/login.cy.ts` (named in `Related
   Files / Entry Points` and required by `Acceptance Criteria` #1) that
   exercises the failing input. **Commit it red.**
3. Open `src/auth/validation.ts:34` (named in `Related Files / Entry
   Points` with the suspected interaction site already noted) and read
   PR #211's motivation before patching, per the open question.
4. Patch the offending step. The new Cypress case must flip green; full
   suite stays green (per `Acceptance Criteria` and `Side Effect
   Checkpoints`).

The agent does **not** restructure the validation chain (per `Out of
Scope`), does not change the `/api/login` contract (per `Out of Scope`),
and does not need to ask the user for the repro account — the brief
names the account and where its password lives.

---

## Notes

- **Why the Acceptance Criteria lead with "commit a red test first"** —
  the `fix` behavior profile mandates reproduction-first. Without that
  guardrail, a downstream agent can ship a "fix" that does not actually
  cover the original failure mode, leaving the bug latent. Pinning the
  failing test as Acceptance Criterion #1 makes that mistake structurally
  impossible.
- **Why Side Effect Checkpoint #2 lists URL-significant characters** —
  `decodeURIComponent` is the suspect. Anything that would change its
  behavior risks regressing other passwords. The downstream agent needs
  to deliberately verify, not assume.
- **Why the password is a 1Password reference, not a literal** — briefs
  are committed artifacts, and the template forbids embedding real
  credentials; the brief references the secret's location instead. The
  load-bearing fact for this bug — the password contains `@` — is stated
  explicitly, so nothing the downstream agent needs is lost.
- **Why Open Questions kept the "remove vs. patch" question** — the
  brief writer does not have authority to decide whether PR #211's
  defensive code is still needed. Leaving the question open lets the
  downstream agent (or PR reviewer) make the call with full context,
  rather than the brief committing to a path the original author may
  push back on.
- **Why the four-anchor check passed despite a one-line input** — PROBLEM
  (login fails), GOAL (login should succeed) is implicit, SCOPE (login
  flow on iOS Safari with `@` in password — narrow), TARGET (the auth
  module — Stage 3 confirms `validation.ts`). All four derivable, no
  halt needed.
