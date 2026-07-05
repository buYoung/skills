# Example 06 — Caveman-style `feat` brief

Demonstrates the caveman full-mode register for the saved brief while
keeping every chat / interview / status surface in normal prose. Same
shape as `01-pm-paste-feat.md`, simpler input, output rewritten in
caveman.

---

## Input (pasted by user, English)

> We need a global hotkey system in the desktop app. Today, key bindings
> only work when the app window is focused. We want users to be able to
> trigger 5 default shortcuts (capture, cancel, next, prev, open
> settings) even when the app is in the background. Settings should
> expose an editor for these shortcuts. Tauri v2 plugin only. Windows
> and macOS must ship together; Linux can come later.

---

## Stage 1 — Ambiguity Gate

| Anchor | Derivable? |
|---|---|
| PROBLEM | yes — shortcuts only work when focused |
| GOAL | yes — shortcuts work backgrounded; Settings editor |
| SCOPE | yes — desktop app hotkey subsystem |
| TARGET | yes — Tauri v2 plugin, Settings UI, hotkey module |

4/4 anchors → **CONTINUE**. No briefset signal — single execution
context.

## Stage 2 — Work Type

`feat` (new behavior surface). Explicit in input. No confirmation
needed.

## Stage 3 — Codebase Review (notes)

- `src/hotkeys/useHotkey.ts` — current in-app hotkey hook, focus-bound.
- `src-tauri/Cargo.toml` — plugin dependency point.
- PR #128 — prior Tauri v1 attempt (closed); useful prior-art reference.

Three concrete entry points → save threshold met.

## Stage 4 — User Decision Table (chat is normal prose, never caveman)

| 순번 | 내용 | 수정 추천안 | 근거 |
|---|---|---|---|
| 1 | Default shortcut combinations finality | Flag the five default combinations as draft in `Open Questions`; implementer may propose defaults, product confirms before merge. | Input names five shortcut actions but does not provide concrete key combinations. Codebase review cannot decide product defaults. |
| 2 | Linux behavior for unavailable global-hotkey support | Show the shortcut-editing section as disabled with an explanatory tooltip. | Linux is out of scope for shipping, but Settings may still render in shared UI paths. Disabled state makes the missing capability explicit. |

User: approve rows 1-2.

Decision table closed. Move to Stage 5.

---

## Stage 5 — Saved Brief (caveman full mode)

```markdown
# [feat] Global hotkey system

## Work Type
feat

## Current State (As-Is)
- Key bindings in `src/hotkeys/useHotkey.ts` fire only while app window has focus.
- App in background → shortcut no register. User must focus window first.
- No persistent shortcut-editing UI in Settings.

## Desired Outcome (To-Be)
- OS-level global shortcut invoke app action even while app backgrounded.
- Settings expose section where user change each shortcut combo.
- 5 default shortcut wired: capture / cancel / next / prev / open settings.

## Scope
### In Scope
- Integrate Tauri v2 global-hotkey plugin.
- Define 5 default shortcut combo (provisional draft — product to confirm).
- Add shortcut-editing section to Settings UI (Linux: disabled state + tooltip when plugin unavailable).
### Out of Scope
- [deferred] Multi-profile shortcut set — future brief.
- [deferred] Conflict detection vs OS-default shortcut.
- [hard] Tauri v1 fallback path — v2 only.

## Constraints
- Tauri v2 plugin only — v1 alternative not on table.
- Windows + macOS ship together. Linux best-effort, ship after.
- macOS accessibility permission flow must not block first launch — defer prompt to first hotkey use.

## Related Files / Entry Points
- `src/hotkeys/useHotkey.ts` — current in-app hotkey impl; need coexistence path with global hotkey.
- `src-tauri/Cargo.toml` — plugin dep add here.
- `src/settings/SettingsScreen.tsx` (proposed) — new shortcut-editing section host.
- PR #128 — last year Tauri v1 attempt; PR desc capture prior constraints worth ref.

## Side Effect Checkpoints
- [ ] Existing in-app hotkey still fire when window focused (no regression).
- [ ] macOS accessibility permission prompt appear once, on first hotkey use, not at app launch.
- [ ] Linux build with plugin unavailable: Settings section render disabled + tooltip; no crash.
- [ ] Plugin registration failure → app no crash; user-visible error in Settings.

## Acceptance Criteria
- [ ] All 5 default shortcut fire successfully while app backgrounded on Windows + macOS.
- [ ] Shortcut edit in Settings UI apply immediately, no app restart.
- [ ] Release build: hotkey registration complete ≤ 100ms of plugin init.
- [ ] Linux: Settings section render disabled with tooltip "global hotkey unsupported on this system" when plugin reports unavailable.

## Open Questions
- Are the 5 default key combos finalized by product, or is the implementer proposing a draft that product confirms before merge? (Current assumption: implementer proposes the draft and product confirms before merge.)
- Should conflict detection against OS-default shortcuts be in scope for this brief, or deferred to a follow-up?
```

Validator: passes structurally (`-v` not needed for this run, no
collisions). The `(proposed)` marker on
`src/settings/SettingsScreen.tsx` exempts it from path-existence
check.

---

## Stage 6 — Save report (chat, normal prose)

> Saved — `docs/briefs/2026-05-05-feat-global-hotkey-system.md`
> (`feat`: Global hotkey system; structural validation passed;
> downstream interpretation aligned; content self-check passed — major
> input concerns reflected, caveman parity held;
> cold-pickup `clean_pass` after 1 pass — no ask-backs, no missing
> concerns, no over-terse bullets). Body is in caveman full mode per
> skill spec. Open it and let me know if anything reads ambiguously —
> caveman compresses prose, not contracts, but human review catches
> what compression should have backed off on.

(Stage 5.7 ran because two Stage 4 decision rows and a populated
`Open Questions` both fired the auto-ON gate.)

---

## Picked Up Cold (downstream agent orientation)

A coding agent opening the saved brief without prior context:

1. Reads `# [feat] Global hotkey system` + `## Work Type: feat` →
   knows behavior profile is "new surface, additive."
2. Reads `## Current State (As-Is)` → confirms today's hotkey is
   focus-bound and routes to `src/hotkeys/useHotkey.ts`.
3. Reads `## Desired Outcome (To-Be)` → end state is 5 backgrounded
   shortcuts + Settings editor.
4. Reads `## Constraints` → Tauri v2 only, no v1 fallback,
   permission prompt must defer.
5. Reads `## Out of Scope` → does not invest in conflict detection or
   multi-profile.
6. Routes to `src/hotkeys/useHotkey.ts`, `src-tauri/Cargo.toml`,
   PR #128, and the proposed `src/settings/SettingsScreen.tsx`.

This section is commentary only, not part of the saved brief template.
It shows that caveman style preserved the same routing facts, completion
criteria, and open decisions; the goal is content preservation in a
different register, not token reduction.

---

## Notes — what this example demonstrates

- Body prose is caveman full; section headers, the title format, code
  paths, identifiers, PR numbers, the `(proposed)` marker, and the
  `- [ ]` checklist marker are all preserved verbatim.
- Constraints section keeps `≤ 100ms` and `Tauri v2 plugin only`
  precision — caveman compressed the connective tissue, not the
  threshold.
- Acceptance Criteria stayed measurable; checklist items survive
  caveman because they were already concrete.
- The Linux fallback note (`disabled with tooltip "global hotkey
  unsupported on this system"`) keeps the literal tooltip string
  verbatim — error / UI strings are an Auto-Clarity carve-out.
- Stage 4 interview, Stage 6 save report, and this `Notes` section are
  all in normal prose. Caveman never crosses into chat.
