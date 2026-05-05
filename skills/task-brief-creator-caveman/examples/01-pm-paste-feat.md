# Example 01 — PM paste → `feat` (dark mode in settings)

Long-form input from a PM. Skill runs Stage 3 codebase review to refine
`Current State (As-Is)`, then Stage 4 interview to lock down `Out of Scope`
and `Acceptance Criteria`.

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

## Stage 4 Walk (one question per round)

The skill walks the decision tree built from Stage 3 findings plus
residual gaps in the PM input. For each node it first runs the
codebase-precedence check; if a probe resolves the node, the user
question is skipped or downgraded to a one-line confirmation.

Tree:

```
Work Type (provisional: feat)
└─ Desired Outcome (To-Be)
   ├─ Toggle UX (PM open question — System option vs. Light/Dark only)
   ├─ In Scope / Out of Scope boundary
   │  └─ `useTheme()` consumer guardrail (codebase-resolvable)
   ├─ Acceptance Criteria
   │  └─ Flash-of-light edge case (derived from OS-detection gap in Stage 3)
   └─ Side Effect Checkpoints
      ├─ Existing Compact mode toggle
      └─ flag.darkMode default state
Open Questions (only those a probe cannot answer)
```

### Round 1 — Work Type confirmation

> Reading the PM input as `feat` — new theme + a new Settings row
> that didn't exist before. Right call?
>
> 1. **`feat` (Recommended)** — user-visible capability that didn't exist.
> 2. `chore` — mostly plumbing under existing UI.
> 3. `style` — purely visual.
>
> *I'd go with 1; the new Settings row is the load-bearing surface
> change even though most of the work is plumbing.*

User: **1**.

### Round 2 — Toggle UX (PM open question)

PM left this open and no codebase probe applies — pure design call.

> Third "system" option vs. light/dark only. Three options is the
> safer default — explicit override for users who want a fixed theme
> regardless of OS, and matches your "default = follow OS" line.
>
> 1. **System / Light / Dark, default = System (Recommended)**
> 2. Light / Dark only, follow OS implicitly (no UI for "follow OS")
> 3. System / Light / Dark, default = Light (don't auto-darken on first launch)
>
> *I'd go with 1.*

User: **1**.

### Round 3 — `useTheme()` consumer guardrail (codebase-resolved)

Codebase-precedence probe: `rg "useTheme\(" -t tsx src/` → 17 consumer
sites outside Settings. Spot-read of two confirmed none have a dark
variant. Probe outcome: a downstream agent that helpfully
cascade-restyles those sites would blow the scope. Worth pinning Out
of Scope explicitly.

> Probe found 17 `useTheme()` consumer sites outside Settings, none
> dark-aware. To keep this brief scoped to Settings only, I'd add an
> Out of Scope line: "do not modify any existing `useTheme()`
> consumer outside the Settings screen". Otherwise a downstream agent
> may cascade.
>
> 1. **Add the guardrail (Recommended)**
> 2. Skip — trust the agent to stay narrow
> 3. Expand scope — pull in 1–2 other surfaces (which?)
>
> *Answer 3 only if you actually want to widen this brief.*

User: **1**.

### Round 4 — Acceptance Criteria draft

> Acceptance Criteria draft, three from the PM bullets plus one from
> the OS-detection gap surfaced in Stage 3:
>
> - [ ] Theme row in Settings → Appearance offers System / Light / Dark
>       and the choice persists across reload.
> - [ ] Toggling between Light and Dark updates the Settings screen
>       within one render frame (no full-screen reload).
> - [ ] In production builds with `flag.darkMode = false`, no
>       dark-mode code paths are reachable from the UI.
> - [ ] When pref = System, the active theme matches the OS preference
>       on first paint (no flash of light theme).
>
> Stage 3 found no OS-theme detection wired anywhere — that means a
> fresh load with pref = System will probably flash light before
> resolving the OS preference. The fourth criterion pins that.
>
> 1. **All four (Recommended)** — flash-of-light is a silent
>    regression class downstream agents miss.
> 2. First three only — flash acceptable for v1.
> 3. Different framing for #4.

User: **1**.

### Round 5 — Side Effect Checkpoints

> Side Effect Checkpoints from review:
>
> - [ ] Existing `Compact mode` toggle in Settings → Appearance still
>       toggles and persists.
> - [ ] With `flag.darkMode = false`, Settings UI is identical to
>       before this change (no Theme row visible).
> - [ ] Switching OS theme while pref = System repaints the Settings
>       screen without a reload.
>
> Add or change?

User: 👍 — looks good as-is.

### Termination

All mandatory nodes decided, user answers consistent, codebase probe
resolved one node before it became a real question (consumer reach
in Round 3). One residual question carries forward to `Open
Questions` (per-platform OS-theme listener teardown — a real tradeoff
with no clear right answer from the brief alone). Stage 5 follows.

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
- Restyling any screen other than Settings — rest of app keep light palette.
- Modifying any existing `useTheme()` consumer outside Settings screen.
- Theming for mobile app shell — separate epic owned by mobile team.

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
- **Why the fourth Acceptance Criterion ("no flash of light theme") got
  added in Round 4** — it was not in the PM input, but it is the kind of
  measurable end-state criterion that prevents a downstream agent from
  declaring "done" while the experience is broken. The walk surfaced it
  as part of the Acceptance Criteria draft after recognizing the
  OS-theme detection gap from Stage 3.
- **Why the Open Question stayed in** — the listener-teardown question is
  a real tradeoff with no clear right answer from the brief alone.
  Leaving it in `Open Questions` is correct; pushing the user for a
  decision would be premature.
