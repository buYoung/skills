# React Accessibility

## Read When

Read for controls/forms/navigation, keyboard/focus/name, async announcement, recovery focus, reduced motion, or custom widgets. Read async UI and public API guidance when status meaning or consumer compatibility is involved.

## Collect Inputs

Collect control/status semantics, native candidate, keyboard model, focus owner/order, name/label relation, async-state evidence, announcement need, zoom, motion, and public consumers when DOM semantics change.

## Decision Sequence and Table

1. Identify semantic purpose. 2. Select native element. 3. Add only required ARIA. 4. Define focus/announcement. 5. Verify observed behavior.

| Observation | Selection | Action | Related guidance |
|---|---|---|---|
| React 19 Action/form pending/error owner unresolved | owner/API first | Do not finalize announcements or pending semantics | [React 19 Actions/async](react-19-actions-async.md) |
| Native action/navigation/form element exists | native element | Use built-in semantics | none |
| Native semantics need extra state/relation | minimal ARIA | Add name/state/relation only | none |
| Invisible async change with known state meaning | status announcement | Scope `aria-live`/`aria-busy` | none |
| Async state meaning unresolved | state meaning first | Do not announce ambiguous status | [async UI](react-async-ui.md) |
| Validation/recovery orientation needed | managed focus | Focus summary/heading/first invalid field | none |
| No native widget fits | custom widget | Implement full keyboard/focus contract | none |
| Public DOM/semantic change | compatibility evidence | Preserve consumer impact | [structure/public API](react-structure-public-api.md) |

## Actions and Prohibitions

Preserve paste, zoom, visible focus, labels, image alternatives, and reduced motion. Do not use clickable generic containers, indiscriminate live regions, focus movement each render, or a custom widget when the full interaction cannot be owned.

## Uncertainty and Regressions

Investigate and fix incomplete keyboard/focus behavior in existing controls. Defer a new custom widget when its intended interaction remains undecided. Correct or revert DOM changes that regress consumer or accessibility behavior.

## Verify

Observe keyboard-only flow, focus order/visibility, accessible names/relations, status/error feedback, recovery focus, zoom, and reduced motion. Do not report assumed compliance.

## Result and Related Guidance

Report semantic choices and observed results, separating inspected markup from keyboard or assistive-technology behavior actually exercised. Use [async UI](react-async-ui.md) for status meaning and [structure/public API](react-structure-public-api.md) for public semantic changes.

Fact source: [React DOM common components](https://react.dev/reference/react-dom/components/common).
