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

## Interview Exchange (Stage 4)

Skill batched four questions:

1. **Type confirmation** — proposed `fix`. User confirmed.
2. **Reproduction status** — asked whether the user has a steady repro.
   → User has it: iOS Safari 17, password `foo@bar`, form returns
   "invalid credentials" silently. Desktop Safari and Chrome work fine.
3. **Out of Scope** — proposed: do not refactor the validation chain,
   do not change the API contract. → User accepted.
4. **Acceptance Criteria** — drafted around reproduction-first: a
   failing test that captures the bug must exist before the patch, and
   pass after.

---

## Output (`docs/briefs/2026-04-23-fix-ios-safari-login-at-symbol.md`)

```markdown
# [fix] iOS Safari login fails when password contains `@`

## Work Type
fix

## Current State (As-Is)
- The login flow rejects valid credentials on iOS Safari when the password contains `@`; the same credentials succeed in every other tested browser.
- `validatePassword()` in `src/auth/validation.ts` calls `decodeURIComponent` on the raw input — likely interaction site (per Stage 3 review).

## Reproduction
- Steps: open `/login` on iOS Safari 17, enter a known-valid account whose password contains `@` (test account `qa+iossafari@example.com` / `foo@bar`), tap "Log in".
- Observed: form returns "invalid credentials" toast; no network error in dev tools.
- Expected: same credentials succeed (verified working on desktop Safari 17, Chrome 124, Firefox 125 against the same backend).
- Environment: iOS Safari 17 on iPhone 14 (BrowserStack); reproduces against `main` branch dev build and the current production build.
- Frequency: always — 5/5 attempts on a fresh session.

## Desired Outcome (To-Be)
- Login succeeds on iOS Safari 17 with passwords containing `@`, matching desktop browser behavior.
- The validation chain stays structurally the same; only the offending step changes.
- A regression test captures the bug so it cannot silently return.

## Scope
### In Scope
- Fix the validation step in `src/auth/validation.ts` that mishandles `@` on iOS Safari.
- Add a Cypress E2E case that exercises the failing input.
### Out of Scope
- Refactoring or restructuring the validation chain beyond the offending step.
- Changing the `/api/login` request or response contract.
- Reviewing other characters that may have similar issues — separate brief if found.

## Related Files / Entry Points
- `src/auth/validation.ts:34` — `validatePassword()`; suspected `decodeURIComponent` interaction with `@` on iOS Safari.
- `src/auth/LoginForm.tsx` — submission handler; calls `validatePassword` before POSTing.
- `cypress/e2e/login.cy.ts` — add the regression case here.
- PR #211 — introduced the `decodeURIComponent` cleanup; check the original motivation before removing it outright.

## Side Effect Checkpoints
- [ ] Existing `valid login` Cypress case still passes (no regression on the happy path).
- [ ] Passwords containing other URL-significant characters (`%`, `+`, `&`) still validate correctly on all browsers.
- [ ] The original motivation for the `decodeURIComponent` step (per PR #211) remains addressed, or is explicitly noted as obsolete.

## Acceptance Criteria
- [ ] A new Cypress case in `cypress/e2e/login.cy.ts` reproduces the failure on the unfixed code (commit it red first, then fix).
- [ ] The new case passes after the fix on the same iOS Safari target.
- [ ] Manual verification on iOS Safari 17 with password `foo@bar` results in successful login.
- [ ] Full Cypress suite stays green.

## Open Questions
- Is the `decodeURIComponent` step in PR #211 still needed for any input it actually defends against, or can it be removed entirely instead of patched? Defer to PR review if unclear.
```

---

## Picked Up Cold — Coding Agent's First Actions

A coding agent receiving only the saved brief should reach a red test in
under 30 minutes. From the brief alone:

1. Spin up the documented repro environment (BrowserStack, iOS Safari 17,
   account `qa+iossafari@example.com` / `foo@bar` per `Reproduction`).
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
ships it.

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
