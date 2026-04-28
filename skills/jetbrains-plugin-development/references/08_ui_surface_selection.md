# UI Surface Selection

Read this when choosing where plugin UI should live: settings page, dialog, tool window,
action, notification, status bar widget, custom editor, or embedded browser.

## Choosing the right UI surface

The platform layers three UI mechanisms on top of Swing; mixing them is normal, but each
has a default-recommended use. Picking the wrong surface produces UIs that fight the IDE's
look, miss free behaviour (theming, accessibility, "Find Action" search, keymap
integration), or duplicate work the platform already does.

**Decision rules:**

- **Input forms — settings pages, dialogs, anything where state binding to a model object
  is the central task → Kotlin UI DSL v2.** It is terse, gives you `bind*` /
  `validation*` / `enabledIf` for free, and matches the IDE's visual rhythm. See
  `08_ui_kotlin_ui_dsl.md`.
- **Tool windows and other "working surfaces" where the UI is a custom interactive view,
  not a state-bound form → custom Swing components from the IntelliJ Platform's `JB*`
  family.** `JBPanel`, `JBLabel`, `JBList`, `JBTable`, `JBSplitter`, `JBTabs`, etc.
  They inherit theming, retina rendering, focus traversal, accessibility, and Speed
  Search from the platform.
- **Anything triggered by menu, toolbar, context menu, or keyboard shortcut → Action
  System**, not a hand-placed `JButton`. Actions get keymap integration, "Find Action"
  search, dynamic enable/visible via `update()`, and consistent placement across IDE
  surfaces. See `02_runtime_actions.md`.
- **Standard `javax.swing.*` components → only as a fallback** when no platform replacement
  exists or you need a one-off custom render. Whenever a `JB*` analogue exists, prefer it.

**Verifying choices against the IDE itself:**

- **UI Inspector** — Enable Internal Mode (`Help | Edit Custom Properties...` → add
  `idea.is.internal=true`, restart), then `Ctrl+Alt+Click` on any IDE component (or
  `Tools | Internal Actions | UI | UI Inspector`). It surfaces the component's class
  hierarchy, client properties, layout constraints, and contributed `DataKey`s — the
  fastest way to discover *which* JB component a built-in IDE feature uses, then mirror
  that choice in your own code.
- **Plugin DevKit "Undesirable class usage" inspection** — at
  `Settings | Editor | Inspections | Plugin DevKit | Code | Undesirable class usage`.
  Flags `JTable` / `JList` / `JLabel` / `JComboBox` / `JBox` / etc. when a `JB*`
  replacement exists. Run it before declaring UI work done; treat its warnings as the
  authoritative "you should be using the JB widget" signal.
- **Avoid IntelliJ's `.form`-based UI Designer in Kotlin plugins.** It generates Java that
  is awkward to reach from Kotlin, doesn't compose cleanly with `panel { ... }`, and the
  platform recommends Kotlin UI DSL v2 for new code. UI Designer remains valid only for
  existing Java forms you are not rewriting.
