# Brief Template

This file holds the canonical executable implementation work-plan template that the skill emits into `docs/briefs/YYYY-MM-DD-<type>-<slug>.md`: nine required H2 sections plus an optional `Constraints` section, with per-section writing guidance.

The emitted **output artifact is in English, written in caveman full mode** (body prose only).
Caveman compression applies to body prose — section headers, the title `# [<type>] <title>`, the `## Work Type` value, code blocks, paths, identifiers, error strings, the `- [ ]` checklist marker, and the `- N/A — <reason>` escape token all stay verbatim.
See `caveman-style.md` for the full list of Auto-Clarity carve-outs and conversion rules.

The **chat interaction language follows the user's input** — Korean input gets a Korean reply, English input gets an English reply — but that is the chat layer, not the saved document.
**Chat is always normal prose, never caveman.**

Per-section "Good" / "Bad" examples below describe the *technical contract* (specificity, measurability, concreteness) — those are what survive caveman conversion.
The "Caveman OK" line under each example shows the same contract emitted in caveman full mode.

---

## Raw Template (emit required sections, filled)

```markdown
# [<type>] <title>

## Work Type
<type>

## Current State (As-Is)
- [confirmed] <fact> — Evidence: <stable file/symbol/heading/command locator>
- [inferred] <judgement or risk> — Confirm by: <specific investigation or command>

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

## Execution Plan
### Stage 1 — <name>
- Starts when: <precondition>
- Work: <bounded outcome, not a low-level implementation prescription>
- Deliverable: <artifact or state handed forward>
- Ends when:
  - [ ] <stage completion criterion>
- Handoff: <next stage or overall verification, including what it receives>
- Replan when: <condition, or None — <reason>>
- Worker decision: <optional bounded, reversible implementation choice>

## Side Effect Checkpoints
- [ ] <checkable item>
- [ ] <checkable item>

## Acceptance Criteria
- [ ] <measurable criterion>
- [ ] <measurable criterion>

## Open Questions
- [non-blocking] <question> — Default: <safe fallback>; Reconfirm before: <stage or milestone>
```

When no user-owned question remains, replace the sample question with `- None — <reason>`.

## Optional Constraints Block

Insert this block between `Scope` and `Related Files / Entry Points` only when task-specific constraints exist.
The emitted heading is `## Constraints`, not `## Constraints (optional)`.

```markdown
## Constraints
- <task-specific constraint>
```

## Type-Conditional Sections

Three of the ten work types require an **additional H2 section** between `Current State (As-Is)` and `Desired Outcome (To-Be)`.
The section captures the type-specific input the downstream agent needs to honor that type's behavior profile (see `work-types.md`).

| Work Type | Required Section | What it captures |
|---|---|---|
| `fix` | `## Reproduction` | Steps to reproduce, environment, frequency, observed vs expected behavior |
| `perf` | `## Baseline Measurement` | Current measurement, method, environment, target improvement |
| `refactor` | `## Behavior Contract` | Which tests / specs / observable behaviors lock the existing behavior; how preservation is verified |

The other seven types (`feat`, `chore`, `docs`, `test`, `style`, `build`, `ci`) use the nine required sections only.

If the section legitimately has nothing concrete to capture (e.g., a visual regression `fix` whose entire repro is "open the page"), write a single bullet:

```markdown
## Reproduction
- N/A — single-step visual regression; reproduce by opening Settings → Appearance.
```

Do not omit the section — `validate_brief.py` checks for its presence.
The `- N/A — <reason>` form is the explicit escape hatch; a bare `- N/A` without reason is rejected.
The validator requires the exact em dash form for `- N/A — <reason>` and `- None — <reason>`; plain hyphens and en dashes are rejected.

---

## Section-by-Section Guide

### Title line — `# [<type>] <title>`

- `<type>` is one of the ten Conventional Commits types (see `work-types.md`).
- `<title>` is a single concrete sentence fragment — not a restatement of the type.
  - Good: `[feat] Introduce global hotkey system`
  - Bad: `[feat] Feature addition` (too generic — says nothing)
- Keep under ~60 chars so it fits in editor tabs and PR titles.

### § Work Type

Just the bare type token: `refactor`, `feat`, etc. No prose.
This exists as a separate section (not just the title tag) because downstream tooling may parse it directly.

### § Current State (As-Is)

Short factual description of how things are today.
This is the baseline the `Desired Outcome (To-Be)` will be compared against.

- Use as many bullets as the task needs, but keep each bullet to one coherent unit of current context.
- Anchor the snapshot: have the first bullet record the reference point — `as of <short-sha> on <branch>` — so the facts have a fixed baseline when the brief is consumed later.
- Concrete: name the function, the module, the UX behavior.
  - Good: `LoginForm` validates email only `onBlur` — users don't see the error until they try to submit.
  - Bad: Login UX is not great.
  - Caveman OK: `` `LoginForm` validate email on blur only. User no see error till submit attempt. ``
- No judgment language ("bad", "ugly", "messy") unless it's literally the thing being fixed.
  Say what is, not what you feel about it.
- If a background context line is essential, the first bullet may carry it — do not create a separate "Background" section.
- Preserve structural facts that change the coding route.
  If the input or a referenced spec names architecture layers, data models, function/API groups, settings, event flows, or platform boundaries that affect edit locations, call order, responsibility boundaries, or verification, give each distinct implementation obligation its own bullet instead of abstracting it into "related logic" or "platform work".
- Prefix every load-bearing top-level bullet with exactly `[confirmed]` or `[inferred]`:
  - `[confirmed]`: cite file / section / symbol / command proving stable fact.
  - `[inferred]`: state judgement or likely failure mode and name investigation, fixture, or command that confirms it.
  - Do not rely on line number alone; pair it with section heading, symbol, nearby literal text, or validator message.
- Keep `[confirmed]`, `[inferred]`, `Evidence:`, and `Confirm by:` tokens clear under caveman conversion.
  Classification accuracy is content-review responsibility; structural validator checks only prefix shape.

### § Reproduction (`fix` only)

A pinned reproduction is the most expensive thing a `fix` agent has to recover if it isn't in the brief.
Capture it explicitly so the agent can pin the failure before patching, using existing tests or manual reproduction first.
Add a new failing test only when the user or repository rules allow new tests.

Cover, at minimum:

- **Steps** — minimal sequence that triggers the bug.
- **Environment** — browser/OS/runtime version, build, branch, data fixture, anything that matters for the repro.
- **Frequency** — always / intermittent (with conditions) / once seen.
- **Observed vs expected** — what actually happens, what should happen.

Never embed real credentials or secrets in a brief — reference their location instead (env var name, vault/1Password item).

Examples:

- Good: `Steps: load /login on iOS Safari 17, type password "foo@bar", submit. Result: "invalid credentials" toast. Expected: successful login.`
- Good: `Frequency: intermittent — repros ~30% on cold session, never after a successful login in the same browser.`
- Bad: `Sometimes login fails.` (no steps, no environment, not actionable)
- Caveman OK (order kept): `Steps: load /login on iOS Safari 17, type password "foo@bar", then submit. Result: "invalid credentials" toast. Expected: success.`
- Caveman OK (frequency): `Frequency: intermittent — ~30% on cold session, never after success in same browser.`

If the bug is a visual regression where the entire repro is one navigation step, the `- N/A — <reason>` escape hatch is acceptable.

**Step-order note:** caveman compression here keeps `then` / `next` / `before` / `after` whenever step order matters.
Do not collapse three steps into a single conjunction-less fragment.

### § Baseline Measurement (`perf` only)

A `perf` brief without a baseline is wishful thinking.
The downstream agent cannot measure improvement against an unstated starting point, and "felt faster" is not a verification path.

Cover:

- **Current measurement** — concrete number with units (`p95 = 420ms`, `bundle = 312KB gzipped`, `cold start = 1.8s`).
- **Method** — how the number was obtained (tool, scenario, sample size).
- **Environment** — hardware / network / build target / dataset.
- **Target improvement** — desired delta or absolute target.
  State both the metric and the threshold.

Examples:

- Good: `Current: TTFB p95 = 420ms over 1000 requests, measured locally with k6 on M1 Pro, dev build. Target: p95 ≤ 250ms on the same setup.`
- Good: `Current: production bundle = 312KB gzipped (rollup-plugin-visualizer, main branch HEAD). Target: ≤ 280KB gzipped without removing public exports.`
- Bad: `It's slow.` (not measurable)
- Bad: `Improve performance significantly.` (no baseline, no target)
- Caveman OK: `Current: TTFB p95 = 420ms over 1000 req, k6 local on M1 Pro, dev build. Target: p95 ≤ 250ms same setup.`

If the user cannot give a baseline, push back during Stage 4.
Do not invent a number.

### § Behavior Contract (`refactor` only)

A refactor preserves behavior by definition.
The contract section names the behavior that must stay invariant and the artifacts that lock it — so the downstream agent has something concrete to verify against, not a vibe.

Cover:

- **Locked behavior** — what externally observable behavior must not change (public API shape, return values, side-effect order, performance envelope, error semantics).
- **Contract artifacts** — the tests / specs / type signatures / golden files that serve as the regression net.
- **Verification method** — how preservation is checked (test suite to run, snapshot to diff, manual scenario).

Examples:

- Good: `Locked: public methods of UserService (signature, return shape, thrown errors). Contract: src/user/__tests__/UserService.test.ts must pass unchanged. Verification: full suite plus three manual scenarios in docs/qa/user-service.md.`
- Good: `Locked: rendered DOM of <Cart /> for the three fixture carts. Contract: existing Storybook snapshots. Verification: chromatic diff = 0.`
- Bad: `Don't break anything.` (not a contract)
- Bad: `Tests still pass.` (which tests? what do they actually pin?)
- Caveman OK: `` Locked: public methods of `UserService` (signature, return shape, thrown errors). Contract: `src/user/__tests__/UserService.test.ts` pass unchanged. Verification: full suite + 3 manual scenarios in `docs/qa/user-service.md`. ``

If existing tests do not cover behavior the refactor must preserve, record verification gap in first investigation stage or `Side Effect Checkpoints`.
Expanding test coverage is allowed only when the user or repository rules permit it.

### § Desired Outcome (To-Be)

The state at completion.
This is what tells the downstream agent when to stop.

- Use as many bullets as the task needs, mirror-structured against `Current State (As-Is)` where possible.
- Describe observable end-state, not implementation steps.
  - Good: `LoginForm` email error shows live while the user is typing.
  - Bad: Refactor `LoginForm` to detect email change via `useEffect`.
  - Caveman OK: `` `LoginForm` show email error live as user type. ``
- Put ordered work in `Execution Plan`; keep low-level implementation prescriptions out of both sections.
  `Desired Outcome (To-Be)` states observable end state; each execution stage states bounded outcome and handoff.
- Preserve structural target facts that direct implementation.
  If completion depends on a specific layer split, data shape, API list, setting, event sequence, or platform behavior, state that end-state as its own bullet or move exact constraints into `## Constraints`.
- If code already has an internal completion signal, keep it distinct from user's success goal when they are not same thing.
  Example: event firing, status row changing, or validator passing may prove workflow advanced; it may not prove user understood new UX, operator can recover failure, or downstream consumer sees intended data.
  Put internal signal in `Current State (As-Is)` / `Side Effect Checkpoints`; put desired user or operator result here.

### § Scope

Two subsections — **In Scope** and **Out of Scope**.
Out of Scope is the higher-leverage one: it stops the downstream agent from being helpfully wrong.

- **In Scope** — concrete surface area the agent is allowed to change.
  If `In Scope` and `Desired Outcome (To-Be)` are saying the same thing, rewrite `In Scope` as the boundary of where the change applies.
  For review-style plans, put only must-fix findings and tightly coupled checks here.
  Do not move every valid finding into `In Scope` just because review found it.
- **Out of Scope** — specific things the agent might otherwise assume are in play.
  - Good: Do not change the `PaymentService` interface — other teams depend on it.
  - Bad: Don't touch unrelated code.
    (too generic — every brief has this)
  - Caveman OK: `` Do not change `PaymentService` interface — other team depend on it. ``
- Prefix out-of-scope bullets when the distinction matters:
  - `[hard]` means the agent must not touch this in this brief.
  - `[deferred]` means valid follow-up work, intentionally excluded now.
- Do not put implementation judgment in `Out of Scope`.
  If the agent may choose between valid implementation approaches, put that bounded choice in `Constraints`.
  If the user must decide, put it in `Open Questions`.

If the task is legitimately narrow and there's no realistic adjacent overreach, write `- None — self-contained.` Do not pad.

When input is review, audit, TODO list, or broad cleanup request, triage findings before writing this section:

- Must fix now — directly required for user's requested outcome.
- Check while here — cheap, tightly coupled verification that prevents must-fix work from drifting.
- Deferred — real issues that should not expand this brief.

Use `[deferred]` bullets for third group.
If user must choose whether deferred item becomes must-fix, save it in `Open Questions` only when a safe non-blocking default and reconfirm milestone exist; otherwise halt before writing.

### § Constraints

**Task-specific constraints only.** Repository-global rules (style, linting, tone, language conventions) live in CLAUDE.md / AGENTS.md and must not be duplicated here.

Examples of what belongs:

- Must not break the existing public API of `UserProfile.serialize()`.
- Bundle size increase ≤ 5KB gzipped.
- Mobile Safari 15+ must still work.
- Agent may choose between two implementation paths only when both satisfy the listed constraints; name the required behavior, risk, and verification.
- Existing saved records with `status: "pending"` must still load without migration.
- Existing event name `payment:retry-scheduled` and payload fields remain compatible unless requester explicitly approves breaking change.

This section is optional.
If none, omit the section entirely — do not write `None`.

### § Related Files / Entry Points

The most expensive thing a coding agent does on a large codebase is figure out where to start.
This section eliminates that cost.

Each entry should tell the agent where to start, what action starts there, and why that entry matters.
A useful entry routes the first edit or first read; a weak entry only says the file is "related".
Acceptable entry shapes:

- File path: `` `src/auth/LoginForm.tsx` — start at email validation branch before changing submit gating.``
- Function reference: `` `handleLogin()` in `src/auth/LoginForm.tsx:42` — start here to route validation trigger changes.``
- PR number: `PR #142 — last year's refactor in the same area — reference approach.`
- Related brief: `docs/briefs/2026-03-12-refactor-auth.md — prerequisite work.`
- Proposed new path: `` `src/auth/sessionStore.ts` (proposed) — new module location confirmed by user.``
- Root file path: `` `package.json` — inspect existing scripts before naming verification commands.``

Rules:

- At least one top-level bullet must contain a path-shaped inline-code entry such as `` `src/auth/LoginForm.tsx` `` or a confirmed `` `src/auth/sessionStore.ts` (proposed) ``.
  Plain-text paths, PR-only bullets, and symbol-only bullets do not satisfy the structural entry-point requirement because the validator cannot check them.
- Existing paths must exist in the repo as of the codebase review step.
- Proposed new paths are allowed only when the user confirms them or the target directory / naming pattern is clear from the repo.
- The proposed marker is the exact literal token `(proposed)` placed immediately after the inline-code path — variants like `(proposed edit)` or `(proposed path)` are not recognized by the structural validator, and a marker later in the line does not skip validation for earlier paths.
- Root filenames such as `package.json` and `README.md` are checked on disk just like slash-bearing paths. A safe extensionless basename such as `LICENSE`, `Makefile`, `Dockerfile`, or `Pipfile` is checked when it is the first inline-code token, already exists at the repository root, or carries the exact adjacent `(proposed)` marker. This makes a made-up first entry fail while later code symbols such as `STANDARD_SECTIONS` remain symbols; use `()` for code symbols.
- Prefer stable locators over bare line numbers.
  Good: `` `validate_entry_paths()` in `scripts/validate_brief.py` — tighten `(proposed)` handling.``
  Risky: `` `scripts/validate_brief.py:570` — fix this.``
  Line numbers may appear, but pair them with section, symbol, or nearby literal token.
- Never invent PR numbers, existing paths, or prior briefs.
- If the review does not turn up at least one concrete entry point, ask the user before saving.
  Do not emit an empty `Related Files / Entry Points` section.

### § Execution Plan

This is authoritative implementation sequence for single plan and each briefset child.
Fresh coding agent must recover first stage, intended order, stage deliverables, handoffs, replan boundaries, and point where overall verification begins.

Use one or more consecutively numbered H3 stages in this exact field order:

```markdown
### Stage N — <name>
- Starts when: <precondition>
- Work: <bounded outcome, not a low-level implementation prescription>
- Deliverable: <artifact or state handed forward>
- Ends when:
  - [ ] <stage completion criterion>
- Handoff: <next stage or overall verification, including what it receives>
- Replan when: <condition, or None — <reason>>
```

Add `- Worker decision: <bounded reversible implementation choice>` only when worker genuinely owns local choice.
Keep choice inside user scope, constraints, and compatibility envelope; never delegate product decision or breaking change.
For a briefset child, augment this base shape with the mandatory `No-op when`, `No-op handoff`, and per-stage `Verify` / `Inputs` / `Expected` fields in `references/briefset.md`; the parent validator checks those additions transitively.

Rules:

- Start Stage 1 from concrete precondition: confirmed baseline, available dependency, or named input.
- State `Work` as bounded stage outcome, not exact edits, functions, or implementation recipe.
- Name `Deliverable`: pinned reproduction, stable contract, migrated state, integrated surface, or verification evidence.
- Make every verification action reproducible: name repository-supported command or bounded inspection, concrete input/target, and observable expected signal.
  If repository does not establish command, use bounded inspection instead of inventing one.
- Put stage-local completion only under `Ends when` as one or more indented checklist items.
- Make `Handoff` name next stage or overall verification and deliverable received.
- Use `Replan when` for discovery invalidating route. Name next owner/action, not only condition. If none useful, use `None — <reason>`.
- In verification-only or no-change stage, failed proof stops dependent work and returns to owning plan for bounded correction, re-verification, and relationship recalculation before resume.
- Put technical uncertainty into investigation stage or `Replan when`; never into `Open Questions`.
- Keep `Acceptance Criteria` out of stages. Evaluate only after all required stages and side-effect checks finish.

**Auto-Clarity:** Preserve every stage, field label, field order, indented checklist, handoff referent, replan condition, path, command, input, and expected signal exactly enough to remain mechanically and semantically recoverable.
Caveman may shorten prose values only; it may not merge fields, remove a stage, flatten `Ends when`, drop briefset no-op or verification fields, or turn stage order into implication.
If compression obscures precondition, sequence, ownership, or delivery, keep that field value in normal prose.

### § Side Effect Checkpoints

Checklist format (`- [ ]`).
Each item checks whether the agent's own changes affected another behavior, surface, contract, integration, or workflow.

- Good: `- [ ] Login E2E test still passes (cypress/e2e/login.cy.ts).`
- Good: `- [ ] Existing session cookie format stays compatible — existing users do not need to re-login.`
- Bad: `- [ ] No effect on other features.` (unverifiable, pure wish)

Derive checkpoints from:

1. The codebase review — what modules share code with the target area?
2. Known integrations — what external services / teams touch this surface?
3. User's answers during Stage 4.

Always add explicit checkpoints for contracts that codebase review shows must remain stable:

- Persisted identifiers, status values, and storage formats.
- Public API shapes, CLI flags, route names, schema fields, event names, and cross-process payloads.
- i18n keys, analytics event names, generated files, and config keys consumed outside edited module.

Avoid generic compatibility language.
Name contract and expected preservation behavior.

### § Acceptance Criteria

Measurable whole-work completion criteria, evaluated only after every required execution stage and side-effect checkpoint is complete.
Checklist format.
Distinct from `Desired Outcome (To-Be)`: `Desired Outcome` describes the end state; `Acceptance Criteria` describe how to verify the end state is reached.
Distinct from `Execution Plan`: stage completion belongs under each stage's `Ends when`; do not duplicate local gates here.

- Good: `- [ ] Error message appears after 500ms debounce while the user is typing the email.`
- Good: `- [ ] Lighthouse Performance score ≥ 90 (mobile).`
- Bad: `- [ ] UX feels better.`
- Bad: `- [ ] All tests pass.` (empty — tests always have to pass)
- If task has both internal pass condition and user / operator success condition, include both as separate criteria.
  Good: ``- [ ] `job.completed` emit only after export file written.``
  Good: `- [ ] Success toast tell operator where to find exported file.`
  Bad: `- [ ] Export works.` (collapses system completion and operator usability)
- When the verification command is not obvious from the repo, name it inline (e.g. `npx cypress run --spec ...`).
- For validator or workflow-contract fixes, include one small proof path when allowed:
  - Good: `- [ ] Sample Related Files bullet with one proposed path and one fake existing path fails validation for fake path.`
  - Good: `- [ ] Existing validator scripts pass on saved plan exercising changed rule.`
  - Bad: `- [ ] Validator stricter.` (no observable proof)
- Do not require new test files, fixture files, or automation unless user or repository rules allow them.
  If malformed sample is needed only to prove behavior, specify temporary or scratch-only use when repository permits; do not commit unless explicitly requested.

If the user cannot give concrete criteria, push back during Stage 4 — do not invent them.

### § Open Questions

Non-blocking decisions only user owns and that can safely use stated default until named reconfirmation point.
This section stays in normal prose. It is not parking lot for technical unknowns, reviewer preferences, or reversible implementation choices.

- Allow only product behavior, scope, compatibility breaks, external ownership, acceptance thresholds, or other user-owned choices.
- Use this exact normal-prose form for every saved question:

  ```markdown
  - [non-blocking] <question> — Default: <safe fallback>; Reconfirm before: <stage or milestone>
  ```

- Ensure default lets worker execute safely now and reconfirmation occurs before decision becomes irreversible.
- Default valid only until that point. If no answer when worker reaches it, stop before crossing boundary and ask user again.
- If no safe default exists, decision is blocking: halt Stage 4 and do not create file until user answers.
- Move codebase facts into investigation stages, reversible choices into `Worker decision`, invalidation conditions into `Replan when`, and fixed limits into `Constraints`.
- Do not leave decisions to reviewer or downstream worker.
- If there genuinely are none, write `- None — <reason>`, e.g. `- None — no user-owned decisions remain; implementation choices are bounded in Constraints.`
  The exact em dash form is required; the validator rejects a plain hyphen, an en dash, and bare `- None`.

---

## Worked Example

The example below is emitted in caveman full mode.
Headers, paths, identifiers, PR numbers, error strings, and the title-line format stay verbatim; body prose is compressed.

```markdown
# [feat] Introduce global hotkey system

## Work Type
feat

## Current State (As-Is)
- [confirmed] As of `<short-sha>` on `<branch>`, key bindings in `src/hotkeys/useHotkey.ts` fire only while app window focused — Evidence: `useHotkey()` registration branch.
- [confirmed] Background shortcuts no register — Evidence: existing manual hotkey scenario on `<short-sha>`.

## Desired Outcome (To-Be)
- OS-level global shortcut invoke app action even while app backgrounded.
- Settings screen expose section where user change each shortcut combo.

## Scope
### In Scope
- Integrate Tauri global-hotkey plugin.
- Define 5 default shortcut (capture / cancel / next / prev / open settings).
- Add shortcut-editing section to Settings UI.
### Out of Scope
- [deferred] Multi-profile shortcut set — separate future brief.
- [deferred] Conflict detection vs OS-default shortcut.

## Constraints
- Tauri v2 plugin only — v1 alternative not on table.
- Windows and macOS must ship together. Linux best-effort / later.

## Related Files / Entry Points
- `src/hotkeys/useHotkey.ts` — current in-app hotkey impl; need coexistence path with global hotkey.
- `src-tauri/Cargo.toml` — plugin dependency add here.
- PR #128 — last year Tauri v1 attempt; PR desc capture prior constraints worth ref.

## Execution Plan
### Stage 1 — Stabilize shortcut contract
- Starts when: Existing in-app shortcut behavior and five default actions confirmed.
- Work: Establish global registration surface without changing in-app action semantics.
- Deliverable: Registered shortcut contract and platform capability state for Settings integration.
- Ends when:
  - [ ] All five actions have stable identifiers, defaults, and failure reporting.
- Handoff: Stage 2 receives registered shortcut contract and platform capability state.
- Replan when: Tauri v2 plugin cannot preserve existing action contract on either required platform.

### Stage 2 — Expose editable shortcuts
- Starts when: Stage 1 provides shortcut contract and capability state.
- Work: Make shortcut combos editable through Settings while preserving registration and persistence behavior.
- Deliverable: Integrated Settings surface backed by global shortcut contract.
- Ends when:
  - [ ] Each supported shortcut can change and take effect without restart.
- Handoff: Stage 3 receives integrated Settings surface and persisted shortcut state.
- Replan when: Persisted edits cannot apply atomically with registration updates.

### Stage 3 — Verify platform behavior
- Starts when: Integrated Settings surface available on Windows and macOS builds.
- Work: Verify foreground compatibility, background registration, failure handling, and startup behavior across required platforms.
- Deliverable: Platform verification evidence ready for whole-work acceptance evaluation.
- Ends when:
  - [ ] Required platform scenarios and side-effect checkpoints have recorded results.
- Handoff: Overall verification receives completed implementation and platform evidence.
- Replan when: Platform permission or registration model requires user-visible behavior change.

## Side Effect Checkpoints
- [ ] Existing in-app hotkey still work (no regression).
- [ ] macOS accessibility permission prompt appear once only, on first launch.
- [ ] Global hotkey registration fail → app no crash; Settings screen show error.

## Acceptance Criteria
- [ ] All 5 default shortcut fire successfully while app backgrounded.
- [ ] Shortcut edit in Settings UI apply immediately, no restart.
- [ ] Release build: hotkey registration complete ≤ 100ms of app launch.

## Open Questions
- [non-blocking] On Linux, if support is unavailable, should the Settings section be hidden or shown as disabled? — Default: hide the unsupported section; Reconfirm before: Linux release scope is approved.
```

**Note:** the title line `# [feat] Introduce global hotkey system` keeps normal capitalization and articles because the title format is contract (validator parses `# [<type>] <title>`).
Title text is the one prose region in the brief that is *not* caveman-rewritten.
