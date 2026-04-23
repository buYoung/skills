# Brief Template

This file holds the canonical nine-section template that the skill emits into
`docs/briefs/YYYY-MM-DD-<type>-<slug>.md`, plus per-section writing guidance.

The emitted **output artifact is in English** (section headers and body
content). The **chat interaction language follows the user's input** — Korean
input gets a Korean reply, English input gets an English reply — but that is
the chat layer, not the saved document.

---

## Raw Template (emit verbatim, filled)

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

## Constraints (optional)
- <bullet or delete section>

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
- <question, or "None">
```

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

- 2–5 bullets. Longer means the skill is drifting into background exposition —
  cut it.
- Concrete: name the function, the module, the UX behavior.
  - Good: `LoginForm` validates email only `onBlur` — users don't see the error
    until they try to submit.
  - Bad: Login UX is not great.
- No judgment language ("bad", "ugly", "messy") unless it's literally the
  thing being fixed. Say what is, not what you feel about it.
- If a background context line is essential, the first bullet may carry it —
  do not create a separate "Background" section.

### § Desired Outcome (To-Be)

The state at completion. This is what tells the downstream agent when to
stop.

- 2–5 bullets, mirror-structured against `Current State (As-Is)` where
  possible.
- Describe observable end-state, not implementation steps.
  - Good: `LoginForm` email error shows live while the user is typing.
  - Bad: Refactor `LoginForm` to detect email change via `useEffect`.
- Steps belong to the downstream agent's plan, not the brief.

### § Scope

Two subsections — **In Scope** and **Out of Scope**. Out of Scope is the
higher-leverage one: it stops the downstream agent from being helpfully
wrong.

- **In Scope** — 1–5 bullets, concrete surface area. If `In Scope` and
  `Desired Outcome (To-Be)` are saying the same thing, drop `In Scope` and
  keep the `Desired Outcome (To-Be)` bullets as the scope boundary.
- **Out of Scope** — 1–5 bullets, each a specific thing the agent might
  otherwise assume is in play.
  - Good: Do not change the `PaymentService` interface — other teams depend
    on it.
  - Bad: Don't touch unrelated code. (too generic — every brief has this)

If the task is legitimately narrow and there's no realistic adjacent
overreach, write `- None — self-contained.` Do not pad.

### § Constraints (optional)

**Task-specific constraints only.** Repository-global rules (style, linting,
tone, language conventions) live in CLAUDE.md / AGENTS.md and must not be
duplicated here.

Examples of what belongs:

- Must not break the existing public API of `UserProfile.serialize()`.
- Bundle size increase ≤ 5KB gzipped.
- Mobile Safari 15+ must still work.

If none, omit the section entirely — do not write `None`.

### § Related Files / Entry Points

The most expensive thing a coding agent does on a large codebase is figure
out where to start. This section eliminates that cost.

Each entry is `` `<path>` — <one-line purpose> ``. Acceptable entry shapes:

- File path: `` `src/auth/LoginForm.tsx` — email validation logic lives here.``
- Function reference: `` `handleLogin()` in `src/auth/LoginForm.tsx:42` — validation trigger.``
- PR number: `PR #142 — last year's refactor in the same area — reference approach.`
- Related brief: `docs/briefs/2026-03-12-refactor-auth.md — prerequisite work.`

Rules:

- Paths must exist in the repo as of the codebase review step. Never invent.
- If the codebase review did not turn up a solid path, leave it out and add
  an Open Question instead — e.g., "Need to confirm where the session storage
  entry point lives."
- 2–6 entries is typical. More than 8 usually means the brief is too broad —
  consider splitting.

### § Side Effect Checkpoints

Checklist format (`- [ ]`). Each item is something the downstream agent can
actually verify in the verification pass.

- Good: `- [ ] Login E2E test still passes (cypress/e2e/login.cy.ts).`
- Good: `- [ ] Existing session cookie format stays compatible — existing users do not need to re-login.`
- Bad: `- [ ] No effect on other features.` (unverifiable, pure wish)

Aim for 2–5 checkpoints. Derive them from:

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

2–6 criteria. If the user cannot give concrete criteria, push back during
Stage 4 — do not invent them.

### § Open Questions

Things that are not yet decided. This is the safety valve that prevents
the downstream agent from silently guessing.

- Surface every uncertainty caught during codebase review here (e.g., "Two
  parallel implementations exist — which one should we extend?").
- Write as questions, not statements.
- If there genuinely are none, write `- None`.

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

## Constraints (optional)
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
