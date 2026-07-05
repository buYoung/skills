# Example 01 — PM paste → `feat` (dark mode in settings)

Long-form input from a PM. Skill runs Stage 3 codebase review to refine
`Current State (As-Is)`, then the Stage 4 decision table to lock down
`Out of Scope` and `Acceptance Criteria`.

**What this example produces:** a saved brief that a coding agent can pick up
without re-reading the PM spec, without asking which `ThemeProvider` to extend,
and without guessing the flag name. Read the saved brief at the bottom as the
*work instruction* — every other section here is meta, explaining how the
skill arrived at it.

---

## Input (pasted by user)

```
[Settings] Dark mode

Background: users have asked for dark mode in our weekly NPS open-text
field for the past 3 quarters. Top recurring request.

What we want:
- Dark color scheme for the Settings screen first (rest of app later).
- Toggle inside Settings → Appearance section.
- Persist user preference across sessions.
- Default = follow OS-level theme.

Constraints:
- Don't ship a separate theme provider library — use what we already have.
- Engineering wants this behind a flag for one release before defaulting on.

Out of scope:
- Theming for the rest of the app — separate epic, owned by mobile team.

Open: should the toggle in Settings show a third "system" option, or
just light/dark and rely on OS detection?
```

---

## Codebase Review Notes (Stage 3)

Inline `rg` / `Read`, ~6 reads / 4 greps:

- `src/settings/SettingsScreen.tsx` — Settings entry point. `Appearance`
  section already exists with one row for "Compact mode". Pattern for
  adding a row + persisted toggle is established.
- `src/theme/ThemeProvider.tsx` — existing theme provider. Currently a
  single `lightTheme` object, no `darkTheme`. `useTheme()` hook returns
  the active theme. No OS-theme detection yet.
- `src/storage/userPrefs.ts` — `useUserPref<T>(key, default)` hook handles
  persistence (localStorage on web, AsyncStorage on RN). Pattern for
  adding a new pref is one new key constant.
- `src/feature-flags/flags.ts` — flag system based on env + remote
  override. Adding `flag.darkMode` is a one-line addition.
- No existing OS theme detection. `window.matchMedia('(prefers-color-scheme: dark)')`
  on web; `Appearance.getColorScheme()` on RN.

---

## Stage 4 — User Decision Table

The skill first uses the Stage 3 codebase review to resolve technical
facts. It asks the user only for decisions that remain user-owned:
product intent, scope boundaries, acceptance thresholds, and risk
tolerance.

| 순번 | 내용 | 수정 추천안 | 근거 |
|---|---|---|---|
| 1 | Work type to write into the brief | Keep `feat`. | The PM input adds a new Settings row and a user-visible dark-mode capability. This is not only styling or internal plumbing. |
| 2 | Theme selector shape | Use System / Light / Dark, default = System. | The input says default should follow the OS theme, and the open question asks whether System should be explicit. An explicit System option prevents hidden behavior. |
| 3 | Scope boundary for existing theme consumers | Add an Out of Scope line: do not modify existing `useTheme()` consumers outside Settings. | Probe found 17 `useTheme()` consumers outside Settings and no dark-aware variants. Without this guardrail, a downstream agent may widen the diff into unrelated screens. |
| 4 | Acceptance criterion for first paint | Include "when pref = System, active theme matches OS preference on first paint." | Stage 3 found no OS-theme detection currently wired. The first-paint case is the likely regression point for the new System default. |
| 5 | Side effect checkpoints | Keep checkpoints for Compact mode, disabled flag state, and OS theme switching while pref = System. | Those are the adjacent behaviors most likely to regress based on `SettingsScreen.tsx`, `flags.ts`, and the missing OS-listener path. |

User: approve rows 1-5.

### Termination

All user-owned decisions are decided. Technical facts resolved by the
codebase review are not re-asked. One residual implementation tradeoff
still carries forward to `Open Questions`: per-platform OS-theme listener
teardown.

---

## Output (`docs/briefs/2026-04-23-feat-dark-mode-settings.md`)

```markdown
# [feat] Dark mode toggle in Settings

## Work Type
feat

## Current State (As-Is)
- `ThemeProvider` expose only `lightTheme`; `useTheme()` always return it.
- Settings → Appearance has one row (`Compact mode`); pattern set for adding more.
- No OS-theme detection wired anywhere in codebase.

## Desired Outcome (To-Be)
- Settings → Appearance show Theme row with three options: System / Light / Dark (default = System).
- `ThemeProvider` resolve active theme from user pref; when pref = System, follow OS color scheme.
- Selected pref persist across sessions via `useUserPref`.
- Behavior gated by `flag.darkMode`; default off in production for one release before turn on.

## Scope
### In Scope
- Add `darkTheme` alongside `lightTheme` in `src/theme/`.
- Extend `ThemeProvider` to resolve System / Light / Dark.
- Add Theme row to `SettingsScreen.tsx` Appearance section.
- Add `flag.darkMode` and gate new row + provider behavior on it.
### Out of Scope
- [hard] Restyling any screen other than Settings — rest of app keep light palette.
- [hard] Modifying any existing `useTheme()` consumer outside Settings screen.
- [deferred] Theming for mobile app shell — separate epic owned by mobile team.

## Constraints
- Do not introduce new theming library — extend existing `ThemeProvider`.
- `darkTheme` token names must mirror `lightTheme` 1:1 (no new token names).

## Related Files / Entry Points
- `src/settings/SettingsScreen.tsx` — Appearance section; add Theme row here.
- `src/theme/ThemeProvider.tsx` — extend to resolve System / Light / Dark.
- `src/storage/userPrefs.ts` — `useUserPref` hook for persistence.
- `src/feature-flags/flags.ts` — add `flag.darkMode`.

## Side Effect Checkpoints
- [ ] Existing `Compact mode` toggle in Settings → Appearance still toggle and persist.
- [ ] With `flag.darkMode = false`, Settings UI identical to before this change (no Theme row visible).
- [ ] Switching OS theme while pref = System repaint Settings screen without reload.

## Acceptance Criteria
- [ ] Theme row in Settings → Appearance offer System / Light / Dark; choice persist across reload.
- [ ] When pref = System, active theme match OS preference on first paint (no flash of light theme).
- [ ] Toggling between Light and Dark update Settings screen within one render frame (no full-screen reload).
- [ ] Production builds with `flag.darkMode = false`: no dark-mode code paths reachable from UI.

## Open Questions
- Should the per-platform OS-theme listener be torn down when the user's preference leaves `System`, or stay always-on? (Keeping it on is cheap; deferring this to reviewer judgment.)
```

---

## Post-Save Verification Summary

This example focuses on the saved brief shape.
In a live run, Stage 5.5, Stage 5.6, and Stage 5.7 still run after the
file is written and structurally validated.
Because Stage 4 produced user-decision rows, Stage 5.7 cold-pickup is
auto-ON unless the user explicitly disables it; the final Stage 6 banner
would report the structural validator, downstream interpretation,
content self-check, caveman parity, and cold-pickup outcome together.

## Picked Up Cold — Coding Agent's First Actions

A coding agent receiving only the saved brief above should be able to act
without further questions. From the brief alone:

1. Open `src/theme/ThemeProvider.tsx` (named in `Related Files / Entry Points`)
   and add `darkTheme` next to the existing `lightTheme`, mirroring its token
   names 1:1 (per `Constraints`).
2. Add `flag.darkMode` to `src/feature-flags/flags.ts`, default `false` in
   production (per `Desired Outcome (To-Be)`).
3. Add the Theme row in `src/settings/SettingsScreen.tsx`'s Appearance
   section, gated behind `flag.darkMode`, offering System / Light / Dark
   (per `In Scope` and `Desired Outcome (To-Be)`).
4. Wire persistence through `useUserPref` in `src/storage/userPrefs.ts`
   (per `Related Files / Entry Points`).

The agent does **not** touch other `useTheme()` consumers (per `Out of
Scope`), does not introduce a new theming library (per `Constraints`), and
does not need to re-interview the PM about the third "system" option — the
brief locked it down.

---

## Notes

- **Why `feat` and not `chore` or `refactor`** — adding `darkTheme` and a
  new Settings row is a user-visible capability that did not exist. Even
  though most of the work is plumbing, the user-facing surface change is
  the load-bearing test.
- **Why the Out-of-Scope list got two extra entries beyond the PM input** —
  the codebase review surfaced `useTheme()` consumers outside Settings.
  Without an explicit guardrail, a downstream agent might helpfully
  cascade-restyle them and blow the scope. This is exactly the case the
  Out-of-Scope section was designed to catch.
- **Why the second Acceptance Criterion ("no flash of light theme")
  exists** — it was not in the PM input, but it is the kind of
  measurable end-state criterion that prevents a downstream agent from
  declaring "done" while the experience is broken. Stage 3 surfaced the
  missing OS-theme detection, and decision-table row 4 turned that gap
  into the first-paint criterion the user approved.
- **Why the Open Question stayed in** — the listener-teardown question is
  a real tradeoff with no clear right answer from the brief alone.
  Leaving it in `Open Questions` is correct; pushing the user for a
  decision would be premature.
