# React 19 Component API Compatibility

## Read When

Read for resolved React 19 ref prop/provider syntax, React 19.2 `Activity`/`useEffectEvent`, or React 19.3 `<ViewTransition>`/`addTransitionType` and Fragment refs. Use public API, state, Effect, async UI, and accessibility guidance when these semantics are involved.

## Collect Inputs

Collect resolved major/minor, app/library/mixed consumers, supported range, public contract, ref/provider call sites/types, and state/Effect owner evidence for 19.2 features. For 19.3 features, collect the update that should animate and its trigger, the DOM node placement under `<ViewTransition>`, or the DOM children and listener/focus/observer need behind a Fragment ref. For `useEffectEvent`, also collect the existing `eslint-plugin-react-hooks` version/config evidence without creating new lint setup.

## Decision Sequence and Table

1. Gate major/minor. 2. Classify consumers or feature signal. 3. Select compatibility form. 4. Edit or report. 5. Verify the affected behavior.

| Observation | Selection | Action | Related guidance |
|---|---|---|---|
| New React 19-only app ref/provider code | React 19 form | Ref prop/provider shorthand may be used | none |
| Existing stable or mixed public contract | compatibility form | Preserve `forwardRef`/`useContext` when required | [structure/public API](react-structure-public-api.md) |
| Minor ≥19.2, Activity state owner unresolved | Activity state decision | Do not apply boundary yet | [state/data](react-state-data.md) |
| Minor ≥19.2, Activity reveal/recovery UI unresolved | Activity UI decision | Preserve state-owner evidence | [async UI](react-async-ui.md) |
| Minor ≥19.2, Effect needs latest non-reactive value | Effect Event candidate | Separate only non-reactive read | [Hooks/Effects](react-hooks-effects.md) |
| Minor ≥19.3, an update between UI states needs animation | View Transition candidate | Place `<ViewTransition>` before the animated subtree's first DOM node; trigger it through a Transition, `<Suspense>`, or `useDeferredValue`; add `addTransitionType` only to distinguish causes | [async UI](react-async-ui.md) |
| Minor ≥19.3, listeners, focus, or observers must cover a group without a wrapper element | Fragment ref | Pass a ref to an explicit `<Fragment>` and use its `FragmentInstance` methods; keep the DOM structure | [accessibility](react-accessibility.md) |
| Minor below the API's 19.2 or 19.3 gate, or unresolved | gated API unavailable/unconfirmed | Use compatible alternatives; investigate an unknown minor | none |
| Dependency avoidance is goal | blocked | Fix Effect ownership | [Hooks/Effects](react-hooks-effects.md) |

## Actions and Prohibitions

Change implementation/types together. A `useEffectEvent` change must preserve compatible Hooks lint behavior; update an existing lint dependency/config only within authority. Do not universally replace compatibility APIs, use Effect Event to suppress synchronization, pass it outside the Effect, create lint setup incidentally, call `document.startViewTransition` alongside `<ViewTransition>`, or use gated APIs without a resolved minor.

## Uncertainty and Regressions

Continue investigating unknown consumers, tooling, and lifecycle defects. Defer only an unsupported or unconfirmed version-specific API or unresolved public break; repair or revert regressions in types/runtime/lifecycle.

## Verify

Verify types, ref attach/cleanup, provider scope/update, consumers, Activity state/lifecycle, Effect synchronization, View Transition trigger/animation/reduced-motion behavior, or Fragment ref listener/focus/observer cleanup as selected. For `useEffectEvent`, run the existing Hooks lint path when available and confirm it does not add the Effect Event to the dependency list.

## Result and Related Guidance

Explain compatibility and affected behavior, using [structure/public API](react-structure-public-api.md), [state/data](react-state-data.md), [async UI](react-async-ui.md), [Hooks/Effects](react-hooks-effects.md), or [accessibility](react-accessibility.md) as needed.

Fact sources: [React 19.2](https://react.dev/blog/2025/10/01/react-19-2), [React 19.3](https://react.dev/blog/2026/09/09/react-19-3), [`<ViewTransition>`](https://react.dev/reference/react/ViewTransition), and [Fragment refs](https://react.dev/reference/react/Fragment#fragmentinstance).
