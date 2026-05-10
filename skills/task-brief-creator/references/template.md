# Brief Template

This file holds the canonical template that the skill emits into
`docs/briefs/YYYY-MM-DD-<type>-<slug>.md`: eight required H2 sections plus an
optional `Constraints` section, with per-section writing guidance.

The emitted **output artifact is in English** (section headers and body
content). The **chat interaction language follows the user's input** — Korean
input gets a Korean reply, English input gets an English reply — but that is
the chat layer, not the saved document.

---

## Raw Template (emit required sections, filled)

```markdown
# [<type>] <title>

## Work Type
<type>

## Current State (As-Is)
- <bullet>
- <bullet>

## Desired Outcome (To-Be)
- <bullet>
- <bullet>

## Scope
### In Scope
- <bullet>
### Out of Scope
- <bullet>

## Related Files / Entry Points
- `<path>` — <one-line purpose>
- PR #<n> — <one-line purpose>

## Side Effect Checkpoints
- [ ] <checkable item>
- [ ] <checkable item>

## Acceptance Criteria
- [ ] <measurable criterion>
- [ ] <measurable criterion>

## Open Questions
- <question, or "None — <reason>">
```

## Optional Constraints Block

Insert this block between `Scope` and `Related Files / Entry Points` only when
task-specific constraints exist. The emitted heading is `## Constraints`, not
`## Constraints (optional)`.

```markdown
## Constraints
- <task-specific constraint>
```

## Type-Conditional Sections

Three of the ten work types require an **additional H2 section** between
`Current State (As-Is)` and `Desired Outcome (To-Be)`. The section captures
the type-specific input the downstream agent needs to honor that type's
behavior profile (see `work-types.md`).

| Work Type | Required Section | What it captures |
|---|---|---|
| `fix` | `## Reproduction` | Steps to reproduce, environment, frequency, observed vs expected behavior |
| `perf` | `## Baseline Measurement` | Current measurement, method, environment, target improvement |
| `refactor` | `## Behavior Contract` | Which tests / specs / observable behaviors lock the existing behavior; how preservation is verified |

The other seven types (`feat`, `chore`, `docs`, `test`, `style`, `build`,
`ci`) use the eight required sections only.

If the section legitimately has nothing concrete to capture (e.g., a visual
regression `fix` whose entire repro is "open the page"), write a single
bullet:

```markdown
## Reproduction
- N/A — single-step visual regression; reproduce by opening Settings → Appearance.
```

Do not omit the section — `validate_brief.py` checks for its presence. The
`- N/A — <reason>` form is the explicit escape hatch; a bare `- N/A` without
reason is rejected.

---

## Section-by-Section Guide

### Title line — `# [<type>] <title>`

- `<type>` is one of the ten Conventional Commits types
  (see `work-types.md`).
- `<title>` is a single concrete sentence fragment — not a restatement of the
  type.
  - Good: `[feat] Introduce global hotkey system`
  - Bad: `[feat] Feature addition` (too generic — says nothing)
- Keep under ~60 chars so it fits in editor tabs and PR titles.

### § Work Type

Just the bare type token: `refactor`, `feat`, etc. No prose. This exists as
a separate section (not just the title tag) because downstream tooling may
parse it directly.

### § Current State (As-Is)

Short factual description of how things are today. This is the baseline the
`Desired Outcome (To-Be)` will be compared against.

- Use as many bullets as the task needs, but keep each bullet to one coherent
  unit of current context.
- Concrete: name the function, the module, the UX behavior.
  - Good: `LoginForm` validates email only `onBlur` — users don't see the error
    until they try to submit.
  - Bad: Login UX is not great.
- No judgment language ("bad", "ugly", "messy") unless it's literally the
  thing being fixed. Say what is, not what you feel about it.
- If a background context line is essential, the first bullet may carry it —
  do not create a separate "Background" section.
- Preserve structural facts that change the coding route. If the input or a
  referenced spec names architecture layers, data models, function/API groups,
  settings, event flows, or platform boundaries that affect edit locations,
  call order, responsibility boundaries, or verification, give each distinct
  implementation obligation its own bullet instead of abstracting it into
  "related logic" or "platform work".

### § Reproduction (`fix` only)

A pinned reproduction is the most expensive thing a `fix` agent has to
recover if it isn't in the brief. Capture it explicitly so the agent can
write a failing test before patching.

Cover, at minimum:

- **Steps** — minimal sequence that triggers the bug.
- **Environment** — browser/OS/runtime version, build, branch, data
  fixture, anything that matters for the repro.
- **Frequency** — always / intermittent (with conditions) / once seen.
- **Observed vs expected** — what actually happens, what should happen.

Examples:

- Good: `Steps: load /login on iOS Safari 17, type password "foo@bar", submit. Result: "invalid credentials" toast. Expected: successful login.`
- Good: `Frequency: intermittent — repros ~30% on cold session, never after a successful login in the same browser.`
- Bad: `Sometimes login fails.` (no steps, no environment, not actionable)

If the bug is a visual regression where the entire repro is one navigation
step, the `- N/A — <reason>` escape hatch is acceptable.

### § Baseline Measurement (`perf` only)

A `perf` brief without a baseline is wishful thinking. The downstream agent
cannot measure improvement against an unstated starting point, and "felt
faster" is not a verification path.

Cover:

- **Current measurement** — concrete number with units (`p95 = 420ms`,
  `bundle = 312KB gzipped`, `cold start = 1.8s`).
- **Method** — how the number was obtained (tool, scenario, sample size).
- **Environment** — hardware / network / build target / dataset.
- **Target improvement** — desired delta or absolute target. State both
  the metric and the threshold.

Examples:

- Good: `Current: TTFB p95 = 420ms over 1000 requests, measured locally with k6 on M1 Pro, dev build. Target: p95 ≤ 250ms on the same setup.`
- Good: `Current: production bundle = 312KB gzipped (rollup-plugin-visualizer, main branch HEAD). Target: ≤ 280KB gzipped without removing public exports.`
- Bad: `It's slow.` (not measurable)
- Bad: `Improve performance significantly.` (no baseline, no target)

If the user cannot give a baseline, push back during Stage 4. Do not invent
a number.

### § Behavior Contract (`refactor` only)

A refactor preserves behavior by definition. The contract section names the
behavior that must stay invariant and the artifacts that lock it — so the
downstream agent has something concrete to verify against, not a vibe.

Cover:

- **Locked behavior** — what externally observable behavior must not
  change (public API shape, return values, side-effect order, performance
  envelope, error semantics).
- **Contract artifacts** — the tests / specs / type signatures / golden
  files that serve as the regression net.
- **Verification method** — how preservation is checked (test suite to
  run, snapshot to diff, manual scenario).

Examples:

- Good: `Locked: public methods of UserService (signature, return shape, thrown errors). Contract: src/user/__tests__/UserService.test.ts must pass unchanged. Verification: full suite plus three manual scenarios in docs/qa/user-service.md.`
- Good: `Locked: rendered DOM of <Cart /> for the three fixture carts. Contract: existing Storybook snapshots. Verification: chromatic diff = 0.`
- Bad: `Don't break anything.` (not a contract)
- Bad: `Tests still pass.` (which tests? what do they actually pin?)

If existing tests do not cover the behavior the refactor must preserve,
that gap belongs in `Open Questions` — and may push back into expanding
test coverage before the refactor proceeds.

### § Desired Outcome (To-Be)

The state at completion. This is what tells the downstream agent when to
stop.

- Use as many bullets as the task needs, mirror-structured against `Current
  State (As-Is)` where possible.
- Describe observable end-state, not implementation steps.
  - Good: `LoginForm` email error shows live while the user is typing.
  - Bad: Refactor `LoginForm` to detect email change via `useEffect`.
- Steps belong to the downstream agent's plan, not the brief.
- Preserve structural target facts that direct implementation. If completion
  depends on a specific layer split, data shape, API list, setting, event
  sequence, or platform behavior, state that end-state as its own bullet or
  move exact constraints into `## Constraints`.

### § Scope

Two subsections — **In Scope** and **Out of Scope**. Out of Scope is the
higher-leverage one: it stops the downstream agent from being helpfully
wrong.

- **In Scope** — concrete surface area the agent is allowed to change. If
  `In Scope` and `Desired Outcome (To-Be)` are saying the same thing, rewrite
  `In Scope` as the boundary of where the change applies.
- **Out of Scope** — specific things the agent might otherwise assume are in
  play.
  - Good: Do not change the `PaymentService` interface — other teams depend
    on it.
  - Bad: Don't touch unrelated code. (too generic — every brief has this)
- Prefix out-of-scope bullets when the distinction matters:
  - `[hard]` means the agent must not touch this in this brief.
  - `[deferred]` means valid follow-up work, intentionally excluded now.
- Do not put implementation judgment in `Out of Scope`. If the agent may choose
  between valid implementation approaches, put that bounded choice in
  `Constraints`. If the user must decide, put it in `Open Questions`.

If the task is legitimately narrow and there's no realistic adjacent
overreach, write `- None — self-contained.` Do not pad.

### § Constraints

**Task-specific constraints only.** Repository-global rules (style, linting,
tone, language conventions) live in CLAUDE.md / AGENTS.md and must not be
duplicated here.

Examples of what belongs:

- Must not break the existing public API of `UserProfile.serialize()`.
- Bundle size increase ≤ 5KB gzipped.
- Mobile Safari 15+ must still work.
- Agent may choose between two implementation paths only when both satisfy the
  listed constraints; name the required behavior, risk, and verification.

This section is optional. If none, omit the section entirely — do not write
`None`.

### § Related Files / Entry Points

The most expensive thing a coding agent does on a large codebase is figure
out where to start. This section eliminates that cost.

Each entry should tell the agent where to start, what action starts there, and
why that entry matters. A useful entry routes the first edit or first read; a
weak entry only says the file is "related".
Acceptable entry shapes:

- File path: `` `src/auth/LoginForm.tsx` — start at email validation branch before changing submit gating.``
- Function reference: `` `handleLogin()` in `src/auth/LoginForm.tsx:42` — start here to route validation trigger changes.``
- PR number: `PR #142 — last year's refactor in the same area — reference approach.`
- Related brief: `docs/briefs/2026-03-12-refactor-auth.md — prerequisite work.`
- Proposed new path: `` `src/auth/sessionStore.ts` (proposed) — new module location confirmed by user.``

Rules:

- Existing paths must exist in the repo as of the codebase review step.
- Proposed new paths are allowed only when the user confirms them or the target
  directory / naming pattern is clear from the repo.
- Never invent PR numbers, existing paths, or prior briefs.
- If the review does not turn up at least one concrete entry point, ask the
  user before saving. Do not emit an empty `Related Files / Entry Points`
  section.

### § Side Effect Checkpoints

Checklist format (`- [ ]`). Each item checks whether the agent's own changes
affected another behavior, surface, contract, integration, or workflow.

- Good: `- [ ] Login E2E test still passes (cypress/e2e/login.cy.ts).`
- Good: `- [ ] Existing session cookie format stays compatible — existing users do not need to re-login.`
- Bad: `- [ ] No effect on other features.` (unverifiable, pure wish)

Derive checkpoints from:

1. The codebase review — what modules share code with the target area?
2. Known integrations — what external services / teams touch this surface?
3. User's answers during Stage 4.

### § Acceptance Criteria

Measurable completion criteria. Checklist format. Distinct from `Desired
Outcome (To-Be)`: `Desired Outcome` describes the end state; `Acceptance
Criteria` describe how to verify the end state is reached.

- Good: `- [ ] Error message appears after 500ms debounce while the user is typing the email.`
- Good: `- [ ] Lighthouse Performance score ≥ 90 (mobile).`
- Bad: `- [ ] UX feels better.`
- Bad: `- [ ] All tests pass.` (empty — tests always have to pass)

If the user cannot give concrete criteria, push back during Stage 4 — do not
invent them.

### § Open Questions

Things that are not yet decided. This is the safety valve that prevents
the downstream agent from silently guessing.

- Surface every uncertainty caught during codebase review here (e.g., "Two
  parallel implementations exist — which one should we extend?").
- Write as questions, not statements.
- If there genuinely are none, write `- None — <reason>`, e.g.
  `- None — no user-owned decisions remain; implementation choices are bounded in Constraints.`

---

## Worked Example

```markdown
# [feat] Introduce global hotkey system

## Work Type
feat

## Current State (As-Is)
- Key bindings in `src/hotkeys/useHotkey.ts` only fire while the app window has focus.
- When the app is in the background, shortcuts do not register — users must focus the window first.

## Desired Outcome (To-Be)
- OS-level registered global shortcuts invoke app actions even while the app is backgrounded.
- The Settings screen exposes a section where users can change each shortcut combination.

## Scope
### In Scope
- Integrate the Tauri global-hotkey plugin.
- Define the 5 default shortcuts (capture / cancel / next / prev / open settings).
- Add a shortcut-editing section to the Settings UI.
### Out of Scope
- Multi-profile shortcut sets (separate future brief).
- Conflict detection against OS-default shortcuts (deferred).

## Constraints
- Tauri v2 plugin only — v1 alternatives are not on the table.
- Windows and macOS must ship together. Linux is best-effort / later.

## Related Files / Entry Points
- `src/hotkeys/useHotkey.ts` — current in-app hotkey implementation; needs a coexistence path with global hotkeys.
- `src-tauri/Cargo.toml` — where the plugin dependency gets added.
- PR #128 — last year's Tauri v1 attempt; the PR description captures prior constraints worth referencing.

## Side Effect Checkpoints
- [ ] Existing in-app hotkeys still work (no regression).
- [ ] macOS accessibility permission prompt appears only once, on first launch.
- [ ] When global hotkey registration fails, the app does not crash and the Settings screen shows an error.

## Acceptance Criteria
- [ ] All 5 default shortcuts fire successfully while the app is backgrounded.
- [ ] Shortcut edits in the Settings UI apply immediately without a restart.
- [ ] In a release build, hotkey registration completes within ≤ 100ms of app launch.

## Open Questions
- Are the 5 default key combinations finalized by product, or do we need to propose a draft?
- On Linux, if support is unavailable, should the Settings section be hidden or shown as disabled?
```
