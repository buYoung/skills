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

## Stage 4 Walk (one question per round)

The skill walks the decision tree. Stage 3 already pinned the
suspected interaction site; the walk's job is to lock the
reproduction-first discipline that `fix`-type briefs demand.

Tree:

```
Work Type (provisional: fix)
└─ Reproduction (mandatory for fix)
   └─ In Scope / Out of Scope boundary
      ├─ Validation chain refactor (touch or freeze?)
      └─ /api/login contract (touch or freeze?)
Acceptance Criteria (reproduction-first ordering)
Side Effect Checkpoints
Open Questions (PR #211 motivation — defer to reviewer)
```

### Round 1 — Work Type confirmation

> One-line input names a defect: login rejecting valid credentials on
> iOS Safari. That's `fix`. Confirm?
>
> 1. **`fix` (Recommended)** — defect with a defined repro.
> 2. `refactor` — restructure validation chain instead.
> 3. `chore` — small cleanup, no behavior claim.
>
> *I'd go with 1; "breaks" is defect language, not a planned restructure.*

User: **1**.

### Round 2 — Reproduction (mandatory for `fix`)

The `fix` profile mandates a populated `Reproduction` section. No
codebase probe can answer this — it's environment knowledge.

> Do you have a steady repro? `fix` briefs need one — without it the
> downstream agent can ship a "fix" that doesn't actually cover the
> failure mode. If you have one, I'll pin it; if not, the brief blocks
> here.
>
> 1. **Yes, share repro steps (Recommended)** — pin in `Reproduction`
> 2. No, only the description — block the brief until repro is captured
> 3. Reach for QA / a tester before continuing

User: **1** — iOS Safari 17, password `foo@bar` against the QA test
account `qa+iossafari@example.com`, "invalid credentials" toast every
time. Desktop Safari and Chrome are fine on the same backend. 5/5
attempts on a fresh session.

### Round 3 — Out of Scope boundary

Stage 3 surfaced two adjacent risks: refactoring the validation chain
and changing the `/api/login` contract. Both are tempting from the
fix site but would balloon the diff.

> Two adjacent surfaces I'd lock down in Out of Scope:
>
> 1. The validation chain itself — fix only the offending step.
> 2. The `/api/login` request/response contract.
>
> Without these guardrails a downstream agent may "tidy up while
> they're in there" and the diff doubles in size for no defect-fix
> reason.
>
> 1. **Lock both (Recommended)**
> 2. Lock validation chain only — let API contract be touched if needed
> 3. Lock API contract only — let validation chain be restructured
> 4. Lock neither

User: **1**.

### Round 4 — Acceptance Criteria draft (reproduction-first)

> Acceptance Criteria with reproduction-first ordering — first
> criterion is a red Cypress case, then the fix flips it green. That
> way the bug can never silently return.
>
> - [ ] A new Cypress case in `cypress/e2e/login.cy.ts` reproduces the
>       failure on the unfixed code (commit it red first, then fix).
> - [ ] The new case passes after the fix on the same iOS Safari target.
> - [ ] Manual verification on iOS Safari 17 with password `foo@bar`
>       results in successful login.
> - [ ] Full Cypress suite stays green.
>
> The "commit it red first" framing is the load-bearing one — it makes
> the regression-impossibility check structural, not a polite request.
>
> 1. **All four as drafted (Recommended)**
> 2. Drop the "commit red first" requirement — too prescriptive
> 3. Different framing — propose a replacement

User: **1**.

### Round 5 — Side Effect Checkpoints

> Side Effect Checkpoints — passwords with other URL-significant
> characters (`%`, `+`, `&`) sit at the same risk profile as `@`
> because `decodeURIComponent` is the suspected interaction site.
>
> - [ ] Existing `valid login` Cypress case still passes (no
>       regression on the happy path).
> - [ ] Passwords containing other URL-significant characters
>       (`%`, `+`, `&`) still validate correctly on all browsers.
> - [ ] The original motivation for the `decodeURIComponent` step
>       (per PR #211) remains addressed, or is explicitly noted as
>       obsolete.
>
> Add or change?

User: 👍 looks right.

### Round 6 — Open Question carry-forward

> The "remove vs. patch" call on PR #211 is a real one I don't have
> authority to make from the brief alone. I'd carry it as an Open
> Question for the PR reviewer rather than push for a decision here.
> Sound right?

User: 👍 yes, defer.

### Termination

All mandatory nodes decided, `Reproduction` section pinned (the
`fix`-type load-bearing input), user answers consistent, one residual
question explicitly carried forward. Stage 5 follows.

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
