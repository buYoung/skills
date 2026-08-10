# React Accessibility

## Read When

Read for controls/forms/navigation, keyboard/focus/name, async announcement, recovery focus, reduced motion, or custom widgets. Exclude async-state meaning and public compatibility classification.

## Collect Inputs

Collect control/status semantics, native candidate, keyboard model, focus owner/order, name/label relation, async-state evidence, announcement need, zoom, motion, and public consumers when DOM semantics change.

## Decision Sequence and Table

1. Identify semantic purpose. 2. Select native element. 3. Add only required ARIA. 4. Define focus/announcement. 5. Verify observed behavior.

| Observation | Selection | Action | Handoff |
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

## Stop or Roll Back

Stop custom-widget work on incomplete keyboard/focus ownership. Roll back DOM changes that break consumers or observed keyboard/name/focus behavior.

## Verify

Observe keyboard-only flow, focus order/visibility, accessible names/relations, status/error feedback, recovery focus, zoom, and reduced motion. Do not report assumed compliance.

## Return and Handoff

Return semantic choice and observed results. Handoff async-state meaning to [async UI](react-async-ui.md) or public semantic impact to [structure/public API](react-structure-public-api.md); otherwise `next_reference: none`.

Fact source: [React DOM common components](https://react.dev/reference/react-dom/components/common).
