# Example 01 — PM paste → `feat` (dark mode in settings)

Long-form input from a PM. Skill runs Stage 3 codebase review to refine
`Current State (As-Is)`, then Stage 4 interview to lock down `Out of Scope`
and `Acceptance Criteria`.

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

## Interview Exchange (Stage 4)

Skill batched five questions:

1. **Type confirmation** — proposed `feat`. User confirmed.
2. **Toggle UX** — open question from PM: third "system" option vs.
   light/dark only. → User picked **three options: System / Light /
   Dark**, default = System.
3. **Out of Scope additions** — proposed adding "do not modify
   `ThemeProvider` consumers outside the Settings screen" so the agent
   does not cascade-restyle other screens. → User accepted.
4. **Acceptance Criteria** — drafted three measurable criteria from the
   PM bullets; user added a fourth: "no flash of light theme on initial
   load when System=Dark."
5. **Side Effect Checkpoints** — surfaced from review: existing
   `Compact mode` toggle in the same section must keep working;
   feature flag default = off in production.

---

## Output (`docs/briefs/2026-04-23-feat-dark-mode-settings.md`)

```markdown
# [feat] Dark mode toggle in Settings

## Work Type
feat

## Current State (As-Is)
- `ThemeProvider` exposes only `lightTheme`; `useTheme()` always returns it.
- Settings → Appearance has one row (`Compact mode`); pattern is established for adding more.
- No OS-theme detection wired anywhere in the codebase.

## Desired Outcome (To-Be)
- Settings → Appearance shows a Theme row with three options: System / Light / Dark (default = System).
- `ThemeProvider` resolves the active theme from the user pref; when pref = System, it follows the OS color scheme.
- The selected pref persists across sessions via `useUserPref`.
- Behavior is gated by `flag.darkMode`; default off in production for one release before turning on.

## Scope
### In Scope
- Add `darkTheme` alongside `lightTheme` in `src/theme/`.
- Extend `ThemeProvider` to resolve System / Light / Dark.
- Add the Theme row to `SettingsScreen.tsx`'s Appearance section.
- Add `flag.darkMode` and gate the new row + provider behavior on it.
### Out of Scope
- Restyling any screen other than Settings — the rest of the app keeps the light palette.
- Modifying any existing `useTheme()` consumer outside the Settings screen.
- Theming for the mobile app shell — separate epic owned by the mobile team.

## Constraints (optional)
- Do not introduce a new theming library — extend the existing `ThemeProvider`.
- `darkTheme` token names must mirror `lightTheme` 1:1 (no new token names).

## Related Files / Entry Points
- `src/settings/SettingsScreen.tsx` — Appearance section; add Theme row here.
- `src/theme/ThemeProvider.tsx` — extend to resolve System / Light / Dark.
- `src/storage/userPrefs.ts` — `useUserPref` hook for persistence.
- `src/feature-flags/flags.ts` — add `flag.darkMode`.

## Side Effect Checkpoints
- [ ] Existing `Compact mode` toggle in Settings → Appearance still toggles and persists.
- [ ] With `flag.darkMode = false`, Settings UI is identical to before this change (no Theme row visible).
- [ ] Switching OS theme while pref = System repaints the Settings screen without a reload.

## Acceptance Criteria
- [ ] Theme row in Settings → Appearance offers System / Light / Dark and the choice persists across reload.
- [ ] When pref = System, the active theme matches the OS preference on first paint (no flash of light theme).
- [ ] Toggling between Light and Dark updates the Settings screen within one render frame (no full-screen reload).
- [ ] In production builds with `flag.darkMode = false`, no dark-mode code paths are reachable from the UI.

## Open Questions
- Should the per-platform OS-theme listener be torn down when the pref leaves System, or always-on? (Cheap to keep on; defer to reviewer.)
```

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
- **Why the fourth Acceptance Criterion ("no flash of light theme") got
  added late** — it was not in the PM input, but it is the kind of
  measurable end-state criterion that prevents a downstream agent from
  declaring "done" while the experience is broken. Surfaced it during
  the interview after recognizing the OS-theme detection gap from Stage 3.
- **Why the Open Question stayed in** — the listener-teardown question is
  a real tradeoff with no clear right answer from the brief alone.
  Leaving it in `Open Questions` is correct; pushing the user for a
  decision would be premature.
