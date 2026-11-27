# Example 01 — PM paste → `feat` (dark mode in settings)

Long-form input from a PM. Skill runs Stage 3 codebase review to refine `Current State (As-Is)`, then the Stage 4 decision table to lock down `Out of Scope` and `Acceptance Criteria`.

**What this example produces:** a saved brief that names the `ThemeProvider` to extend, the `flag.darkMode` gate, and the Settings-only scope, so a coding agent can start without re-reading the PM spec.

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

- `src/settings/SettingsScreen.tsx` — Settings entry point. `Appearance` section already exists with one row for "Compact mode". Pattern for adding a row + persisted toggle is established.
- `src/theme/ThemeProvider.tsx` — existing theme provider. Currently a single `lightTheme` object, no `darkTheme`. `useTheme()` hook returns the active theme. No OS-theme detection yet.
- `src/storage/userPrefs.ts` — `useUserPref<T>(key, default)` hook handles persistence (localStorage on web, AsyncStorage on RN). Pattern for adding a new pref is one new key constant.
- `src/feature-flags/flags.ts` — flag system based on env + remote override. Adding `flag.darkMode` is a one-line addition.
- No existing OS theme detection. `window.matchMedia('(prefers-color-scheme: dark)')` on web; `Appearance.getColorScheme()` on RN.

---

## Stage 4 — User Decision Table

The author selects `feat` from the explicit new capability and derives the side-effect checks from the reviewed integrations.

| 순번 | 내용 | 수정 추천안 | 근거 |
|---|---|---|---|
| 1 | Theme selector shape | Use System / Light / Dark, default = System. | The input says default should follow the OS theme, and the open question asks whether System should be explicit. An explicit System option prevents hidden behavior. |
| 2 | Scope boundary for existing theme consumers | Add an Out of Scope line: do not modify existing `useTheme()` consumers outside Settings. | Code search found 17 `useTheme()` consumers outside Settings and no dark-aware variants. Without this guardrail, a downstream agent may widen the diff into unrelated screens. |
| 3 | Acceptance criterion for first paint | Include "when pref = System, active theme matches OS preference on first paint." | The repository has no OS-theme detection wired yet. The first-paint case is the likely regression point for the new System default. |

User: approve rows 1-3.

### Termination

All user-owned decisions are decided. Technical facts resolved by the codebase review are not re-asked. The listener-lifecycle choice is bounded as a reversible `Worker decision` in Stage 1.

---

## Output (`docs/briefs/2026-04-23-feat-dark-mode-settings.md`)

```markdown
# [feat] Dark mode toggle in Settings

## Work Type
feat

## Current State (As-Is)
- [confirmed] As of `4f9c2e1` on `main`, `ThemeProvider` expose only `lightTheme`; `useTheme()` always return it — Evidence: `src/theme/ThemeProvider.tsx` provider value.
- [confirmed] Settings → Appearance has one row (`Compact mode`) — Evidence: `SettingsScreen` Appearance section.
- [confirmed] No OS-theme detection wired — Evidence: repo search for `matchMedia` and `Appearance.getColorScheme` found no theme integration.

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

## Execution Plan
### Stage 1 — Establish the theme preference contract
- Starts when: Existing provider, preference hook, and flag pattern confirmed.
- Work: Establish gated System / Light / Dark state preserving old light-only path when disabled.
- Deliverable: Persisted preference and provider contract ready for Settings surface.
- Ends when:
  - [ ] Three values, System default, and disabled-flag behavior share one stable contract.
- Handoff: Stage 2 receives persisted preference and provider contract.
- Replan when: Existing consumers require contract change outside Settings-only scope.
- Worker decision: Attach OS-theme listener only while System active unless provider lifecycle makes always-on listener simpler without behavior change.

### Stage 2 — Wire Settings Theme row
- Starts when: Stage 1 provides persisted preference and provider contract.
- Work: Expose three-option Theme row and connect gated provider behavior.
- Deliverable: Settings Theme row wired to gated provider, ready for verification.
- Ends when:
  - [ ] Theme row persists changes and updates Settings without reload.
- Handoff: Overall verification receives wired Theme row and persisted state.
- Replan when: First-paint OS detection cannot avoid light-theme flash inside provider boundary.

## Side Effect Checkpoints
- [ ] Existing `Compact mode` toggle in Settings → Appearance still toggle and persist.
- [ ] With `flag.darkMode = false`, Settings UI identical to before this change (no Theme row visible).
- [ ] Switching OS theme while pref = System repaint Settings screen without reload.

## Acceptance Criteria
- [ ] Theme row in Settings → Appearance offer System / Light / Dark; choice persist across reload.
- [ ] When pref = System, active theme match OS preference on first paint (no flash of light theme).
- [ ] Selecting Light or Dark updates Settings without a full-screen reload; verify both selections using the existing Settings scenario.
- [ ] Production builds with `flag.darkMode = false`: no dark-mode code paths reachable from UI.

## Open Questions
- None — no user-owned decision remains; listener lifecycle is bounded Worker decision in Stage 1.
```

---

## Stage 6 — Save Report

> Saved — `docs/briefs/2026-04-23-feat-dark-mode-settings.md` (`feat`: Dark mode toggle in Settings; structural validation passed; content validation passed — content and intent self-check passed, caveman parity OK). Open it and let me know if anything needs editing.

## Picked Up Cold — Coding Agent's First Actions

A coding agent receiving only the saved brief above should be able to act without further questions. From the brief alone:

1. Open `src/theme/ThemeProvider.tsx` (named in `Related Files / Entry Points`) and add `darkTheme` next to the existing `lightTheme`, mirroring its token names 1:1 (per `Constraints`).
2. Add `flag.darkMode` to `src/feature-flags/flags.ts`, default `false` in production (per `Desired Outcome (To-Be)`).
3. Add the Theme row in `src/settings/SettingsScreen.tsx`'s Appearance section, gated behind `flag.darkMode`, offering System / Light / Dark (per `In Scope` and `Desired Outcome (To-Be)`).
4. Wire persistence through `useUserPref` in `src/storage/userPrefs.ts` (per `Related Files / Entry Points`).

---

## Notes

- **Why `feat` and not `chore` or `refactor`** — adding `darkTheme` and a new Settings row is a user-visible capability that did not exist. Even though most of the work is plumbing, the user-facing surface change is the load-bearing test.
