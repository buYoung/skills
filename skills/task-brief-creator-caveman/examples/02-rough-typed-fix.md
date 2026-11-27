# Example 02 — Rough typed input → `fix` (iOS Safari login bug)

Single-line typed input. Skill clears the four-anchor gate (PROBLEM,
GOAL implicit, SCOPE narrow, TARGET findable), then leans on the `fix`
behavior profile to shape Acceptance Criteria around reproduction.

**What this example produces:** a saved brief with a pinned `Reproduction`
that lets a coding agent pin the failure *before* touching code.
Where a new regression test is mentioned, the example assumes the user
allowed that test during Stage 4; otherwise the brief would require an
existing test or manual repro path instead.

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
- `src/auth/validation.ts:34` — `validatePassword()` calls
  `decodeURIComponent` on raw input, added in PR #211. This is an
  investigation lead, not a demonstrated iOS-specific cause. Capture the
  actual input and failure before attributing the bug to decoding; `@`
  alone does not establish a malformed percent-encoding sequence.
- `cypress/e2e/login.cy.ts` — existing E2E suite. Has a "valid login"
  case but no characters-in-password edge cases.
- No iOS Safari-specific test harness; team uses BrowserStack on demand.

---

## Stage 4 — User Decision Table

Stage 3 already pins the suspected interaction site.
The author selects `fix` from the explicit defect and routes patch-versus-remove into Stage 1 evidence plus a bounded Worker decision.

| 순번 | 내용 | 수정 추천안 | 근거 |
|---|---|---|---|
| 1 | Reproduction detail | Provide the observed environment so it can be pinned in `## Reproduction`: exact iOS Safari version and device, the failing test account (no literal password — name where the secret lives), the observed error surface, and how often it reproduces. | `fix` plans need a reproducible failing state before implementation. The codebase can identify the likely validation site, but only the user can supply the observed environment, account, and frequency. |
| 2 | Out of Scope boundary | Lock both the broader validation-chain refactor and the `/api/login` request/response contract out of scope. | Both sit next to the suspected line in `validatePassword()`. Touching them would widen the defect fix into unrelated behavior change. |
| 3 | Regression coverage permission | Allow one Cypress case for the shared password-submission contract on a supported desktop browser; retain BrowserStack iPhone Safari verification for the reported device-specific failure. | Repository policy requires user permission before adding a new test case. |

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
- [confirmed] `validatePassword()` run `decodeURIComponent` on raw password before `LoginForm.tsx` post to `/api/login` — Evidence: `validatePassword()` in `src/auth/validation.ts` and submit handler in `src/auth/LoginForm.tsx`.
- [inferred] Valid credentials containing `@` rejected on iOS Safari 17 — Confirm by: run `Reproduction` steps against unfixed code in Stage 1.
- [inferred] That `decodeURIComponent` step is likely interaction site with `@` — Confirm by: compare pinned failure before and after isolating that step and inspect PR #211's contract.

## Reproduction
- Steps: open `/login` on iOS Safari 17, enter known-valid QA account `qa+iossafari@example.com` whose password contains `@` (password: see 1Password item "QA iOS Safari"), tap "Log in".
- Observed: form returns "invalid credentials" toast.
- Expected: known-valid QA account can log in; Stage 1 records actual comparison-browser results without assuming them.
- Environment: iOS Safari 17 on iPhone 14 (BrowserStack); reproduces against `main` branch dev build and current production build.
- Frequency: always — 5/5 attempts on fresh session.

## Desired Outcome (To-Be)
- Login succeeds on iOS Safari 17 with passwords containing `@`, while preserving successful login behavior on comparison browsers.
- validation chain stays structurally same; only offending step changes.
- approved Cypress case covers shared password-submission contract on supported browser; actual iOS Safari evidence verifies reported failure.

## Scope
### In Scope
- Fix validation step in `src/auth/validation.ts` that mishandles `@` on iOS Safari.
- Add approved Cypress case for evidenced shared submission contract; do not claim it reproduces iPhone-only failure.
### Out of Scope
- [hard] Refactoring or restructuring validation chain beyond offending step.
- [hard] Changing `/api/login` request or response contract.
- [deferred] Reviewing other characters that may have similar issues — separate brief if found.

## Related Files / Entry Points
- `src/auth/validation.ts:34` — `validatePassword()`; suspected `decodeURIComponent` interaction with `@` on iOS Safari.
- `src/auth/LoginForm.tsx` — submission handler; calls `validatePassword` before POSTing.
- `cypress/e2e/login.cy.ts` — add regression case here.
- PR #211 — introduced `decodeURIComponent` cleanup; check original motivation before removing it outright.

## Execution Plan
### Stage 1 — Pin the failure and validation contract
- Starts when: documented BrowserStack environment and referenced QA credential are available.
- Work: Reproduce failure and establish which input contract PR #211 intended to preserve.
- Deliverable: pinned BrowserStack iOS failure, recorded comparison-browser results, and evidence identifying smallest compatible correction boundary.
- Ends when:
  - [ ] documented failure reproduces on unfixed code and PR #211 motivation is recorded.
- Handoff: Stage 2 receives pinned failure and compatibility boundary.
- Replan when: failure does not reproduce or evidence points outside `validatePassword()`.
- Worker decision: Patch or remove decoding step according to pinned evidence, provided URL-significant passwords and login API contract remain compatible.

### Stage 2 — Correct and verify the login path
- Starts when: Stage 1 provides pinned failure and compatibility boundary.
- Work: Apply bounded validation correction and exercise user-approved regression coverage.
- Deliverable: corrected login path with iPhone Safari before/after evidence and supported-browser Cypress results.
- Ends when:
  - [ ] pinned iOS Safari case passes and adjacent URL-significant password cases remain valid.
- Handoff: Overall verification receives corrected path, regression evidence, and compatibility results.
- Replan when: smallest compatible correction requires changing `/api/login` contract or validation-chain structure.

## Side Effect Checkpoints
- [ ] Existing `valid login` Cypress case still passes (no regression on happy path).
- [ ] Passwords containing other URL-significant characters (`%`, `+`, `&`) still validate correctly on all browsers.
- [ ] original motivation for `decodeURIComponent` step (per PR #211) remains addressed, or is explicitly noted as obsolete.

## Acceptance Criteria
- [ ] reported failure is pinned on unfixed code in BrowserStack iPhone Safari before correction.
- [ ] approved Cypress case verifies shared password-submission contract on supported desktop browser; its results are not labeled iPhone Safari results.
- [ ] Manual verification on iOS Safari 17 with QA account's `@`-containing password results in successful login.
- [ ] Full Cypress suite stays green.

## Open Questions
- None — no user-owned decision remains; patch-versus-remove is bounded by Stage 1 evidence and compatibility constraints.
```

---

## Stage 6 — Save Report

> Saved — `docs/briefs/2026-04-23-fix-ios-safari-login-at-symbol.md` (`fix`: iOS Safari login fails when password contains `@`; structural validation passed; content validation passed — content and intent self-check passed, caveman parity OK).
> Open it and let me know if anything needs editing.

## Picked Up Cold — Coding Agent's First Actions

A coding agent receiving only the saved brief should be able to start,
verify, patch, and know when the fix is complete without asking for more
scope. From the brief alone:

1. Spin up the documented repro environment (BrowserStack, iOS Safari 17,
   account `qa+iossafari@example.com` with the password from the
   1Password item "QA iOS Safari", per `Reproduction`).
   Confirm the failure on `main` to verify the repro is real.
2. Record the shared password-submission contract and add the approved
   Cypress case on a supported desktop browser. Pin a red-to-green case
   there only if the observed cause reproduces there; keep the original
   iPhone Safari failure and its verification separate.
3. Open `src/auth/validation.ts:34` (named in `Related Files / Entry
   Points` with the suspected interaction site already noted) and read
   PR #211's motivation before patching, as required by Stage 1's investigation and bounded `Worker decision`.
4. Patch the offending step. The device-specific before/after check and the supported-browser Cypress case must pass; full
   suite stays green (per `Acceptance Criteria` and `Side Effect
   Checkpoints`).

---

## Notes

- **Why the Acceptance Criteria lead with the actual device reproduction** —
  the `fix` behavior profile requires reproduction-first on the affected
  target. The approved Cypress case is a separate supported-browser contract
  check: [Cypress browser support](https://docs.cypress.io/app/references/launching-browsers#webkit-experimental)
  covers experimental desktop WebKit, not iPhone Safari.
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
