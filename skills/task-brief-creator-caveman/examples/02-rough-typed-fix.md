# Example 02 — Rough typed input → `fix` (iOS Safari login bug)

Single-line typed input. Skill clears the four-anchor gate (PROBLEM,
GOAL implicit, SCOPE narrow, TARGET findable), then leans on the `fix`
behavior profile to shape Acceptance Criteria around reproduction.

**What this example produces:** a saved brief with a pinned `Reproduction`
that lets a coding agent pin the failure *before* touching code.
Where a new regression test is mentioned, the example assumes the user
allowed that test during Stage 4; otherwise the brief would require an
existing test or manual repro path instead. Treat the saved brief as
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
the remaining user-owned decisions needed to make a `fix` plan safe:
reproduction evidence, scope boundaries, and permission for new regression coverage.
The author selects `fix` from the explicit defect and routes patch-versus-remove into Stage 1 evidence plus a bounded Worker decision.

| 순번 | 내용 | 수정 추천안 | 근거 |
|---|---|---|---|
| 1 | Reproduction detail | Provide the observed environment so it can be pinned in `## Reproduction`: exact iOS Safari version and device, the failing test account (no literal password — name where the secret lives), the observed error surface, and how often it reproduces. | `fix` plans need a reproducible failing state before implementation. The codebase can identify the likely validation site, but only the user can supply the observed environment, account, and frequency. |
| 2 | Out of Scope boundary | Lock both the broader validation-chain refactor and the `/api/login` request/response contract out of scope. | Stage 3 found both adjacent to the suspected line. Touching them would widen the defect fix into unrelated behavior change. |
| 3 | Regression coverage permission | Allow one Cypress case that proves the failure before the fix and passes afterward. | Repository policy requires user permission before adding a new test case. |

User: approve rows 2-3; for row 1 the user supplies the values —
iOS Safari 17 on iPhone 14 via BrowserStack, QA account
`qa+iossafari@example.com` whose password contains `@` (stored in the
1Password item "QA iOS Safari"), "invalid credentials" toast, 5/5
attempts on fresh sessions, reproducing on both the `main` dev build
and the current production build.

### Termination

All user-owned decisions are decided. `Reproduction` is pinned from the
user's row-1 answer, while PR #211 investigation becomes Stage 1 work with
a bounded Worker decision. Stage 5 follows.

---

## Output (`docs/briefs/2026-04-23-fix-ios-safari-login-at-symbol.md`)

```markdown
# [fix] iOS Safari login fails when password contains `@`

## Work Type
fix

## Current State (As-Is)
- [confirmed] Login flow reject valid credentials on iOS Safari when password contain `@`; same credentials succeed elsewhere — Evidence: pinned BrowserStack reproduction below.
- [inferred] `validatePassword()` raw `decodeURIComponent` call likely interaction site — Confirm by: isolate step against pinned failure and inspect PR #211 contract.

## Reproduction
- Steps: open `/login` on iOS Safari 17, then enter known-valid QA account `qa+iossafari@example.com` whose password contain `@` (password: see 1Password item "QA iOS Safari"), then tap "Log in".
- Observed: form return "invalid credentials" toast; no network error in dev tools.
- Expected: same credentials succeed (verified working on desktop Safari 17, Chrome 124, Firefox 125 against same backend).
- Environment: iOS Safari 17 on iPhone 14 (BrowserStack); reproduce against `main` branch dev build and current production build.
- Frequency: always — 5/5 attempts on fresh session.

## Desired Outcome (To-Be)
- Login succeed on iOS Safari 17 with passwords containing `@`, match desktop browser behavior.
- Validation chain stay structurally the same; only offending step change.
- User-approved Cypress regression case capture bug so it cannot silently return.

## Scope
### In Scope
- Fix validation step in `src/auth/validation.ts` that mishandle `@` on iOS Safari.
- Add user-approved Cypress E2E case that exercise failing input.
### Out of Scope
- [hard] Refactor or restructure validation chain beyond offending step.
- [hard] Change `/api/login` request or response contract.
- [deferred] Review other characters that may have similar issues — separate brief if found.

## Related Files / Entry Points
- `src/auth/validation.ts:34` — `validatePassword()`; suspected `decodeURIComponent` interaction with `@` on iOS Safari.
- `src/auth/LoginForm.tsx` — submission handler; call `validatePassword` before POSTing.
- `cypress/e2e/login.cy.ts` — add regression case here.
- PR #211 — introduced `decodeURIComponent` cleanup; check original motivation before remove outright.

## Execution Plan
### Stage 1 — Pin failure and validation contract
- Starts when: Documented BrowserStack environment and referenced QA credential available.
- Work: Reproduce failure and establish input contract PR #211 intended to preserve.
- Deliverable: Pinned failing case plus evidence identifying smallest compatible correction boundary.
- Ends when:
  - [ ] Documented failure reproduces on unfixed code and PR #211 purpose is recorded.
- Handoff: Stage 2 receives pinned failure and compatibility boundary.
- Replan when: Failure does not reproduce or evidence points outside `validatePassword()`.
- Worker decision: Patch or remove decoding step from evidence, while URL-significant passwords and login API contract stay compatible.

### Stage 2 — Correct and verify login path
- Starts when: Stage 1 provides pinned failure and compatibility boundary.
- Work: Apply bounded validation correction and exercise user-approved regression coverage.
- Deliverable: Corrected login path with red-to-green evidence and cross-browser results.
- Ends when:
  - [ ] Pinned iOS Safari case passes and adjacent URL-significant password cases remain valid.
- Handoff: Overall verification receives corrected path, regression evidence, and compatibility results.
- Replan when: Smallest correction requires `/api/login` contract or validation-chain structure change.

## Side Effect Checkpoints
- [ ] Existing `valid login` Cypress case still pass (no regression on happy path).
- [ ] Passwords containing other URL-significant characters (`%`, `+`, `&`) still validate correctly on all browsers.
- [ ] Original motivation for `decodeURIComponent` step (per PR #211) remain addressed, or explicitly noted as obsolete.

## Acceptance Criteria
- [ ] Because user approved new test coverage for this fix, new Cypress case in `cypress/e2e/login.cy.ts` reproduce failure on unfixed code before fix applied.
- [ ] New case pass after fix on same iOS Safari target.
- [ ] Manual verification on iOS Safari 17 with QA account's `@`-containing password result in successful login.
- [ ] Full Cypress suite stay green.

## Open Questions
- None — no user-owned decision remains; patch-versus-remove is bounded by Stage 1 evidence and compatibility constraints.
```

---

## Post-Save Verification Summary

This example focuses on the saved brief shape.
In a live run, Stage 5.5, Stage 5.6, and Stage 5.7 still run after the
file is written and structurally validated.
Because the work type is `fix`, Stage 5.7 cold-pickup is auto-ON even if
the input is short; the final Stage 6 banner would report the structural
validation separately from execution reconstruction,
content/execution self-check, caveman parity, and cold-pickup outcome.

## Picked Up Cold — Coding Agent's First Actions

A coding agent receiving only the saved brief should be able to start,
verify, patch, and know when the fix is complete without asking for more
scope. From the brief alone:

1. Spin up the documented repro environment (BrowserStack, iOS Safari 17,
   account `qa+iossafari@example.com` with the password from the
   1Password item "QA iOS Safari", per `Reproduction`).
   Confirm the failure on `main` to verify the repro is real.
2. Add user-approved Cypress case in `cypress/e2e/login.cy.ts` (named in `Related
   Files / Entry Points` and required by `Acceptance Criteria` #1) that
   exercises failing input. Confirm it fails on unfixed code before
   patching.
3. Open `src/auth/validation.ts:34` (named in `Related Files / Entry
   Points` with the suspected interaction site already noted) and read
   PR #211's motivation before patching, as required by Stage 1's investigation and bounded `Worker decision`.
4. Patch the offending step. The new Cypress case must flip green; full
   suite stays green (per `Acceptance Criteria` and `Side Effect
   Checkpoints`).

The agent does **not** restructure the validation chain (per `Out of
Scope`), does not change the `/api/login` contract (per `Out of Scope`),
and does not need to ask the user for the repro account — the brief
names the account and where its password lives.

---

## Notes

- **Why the Acceptance Criteria lead with an approved regression check** —
  the `fix` behavior profile requires reproduction-first. Because the
  Stage 4 answer allows a new Cypress case, this example names that case.
  Without that permission, the brief would use an existing test or manual
  reproduction path instead.
- **Why Side Effect Checkpoint #2 lists URL-significant characters** —
  `decodeURIComponent` is the suspect. Anything that would change its
  behavior risks regressing other passwords. The downstream agent needs
  to deliberately verify, not assume.
- **Why the password is a 1Password reference, not a literal** — briefs
  are committed artifacts, and the template forbids embedding real
  credentials; the brief references the secret's location instead. The
  load-bearing fact for this bug — the password contains `@` — is stated
  explicitly, so nothing the downstream agent needs is lost.
- **Why "remove vs. patch" is not an Open Question** — PR #211 evidence
  makes this a technical investigation followed by a reversible worker
  choice. Stage 1 bounds it with compatibility checks and a replan condition.
- **Why the four-anchor check passed despite a one-line input** — PROBLEM
  (login fails), GOAL (login should succeed) is implicit, SCOPE (login
  flow on iOS Safari with `@` in password — narrow), TARGET (the auth
  module — Stage 3 confirms `validation.ts`). All four derivable, no
  halt needed.
