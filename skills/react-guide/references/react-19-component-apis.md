# React 19 Component API Compatibility

## Read When

Read for resolved React 19 ref prop/provider syntax or React 19.2 `Activity`/`useEffectEvent`. Use public API, state, and Effect guidance when these semantics are involved.

## Collect Inputs

Collect resolved major/minor, app/library/mixed consumers, supported range, public contract, ref/provider call sites/types, and state/Effect owner evidence for 19.2 features. For `useEffectEvent`, also collect the existing `eslint-plugin-react-hooks` version/config evidence without creating new lint setup.

## Decision Sequence and Table

1. Gate major/minor. 2. Classify consumers or feature signal. 3. Select compatibility form. 4. Edit or report. 5. Verify the affected behavior.

| Observation | Selection | Action | Related guidance |
|---|---|---|---|
| New React 19-only app ref/provider code | React 19 form | Ref prop/provider shorthand may be used | none |
| Existing stable or mixed public contract | compatibility form | Preserve `forwardRef`/`useContext` when required | [structure/public API](react-structure-public-api.md) |
| Minor ≥19.2, Activity state owner unresolved | Activity state decision | Do not apply boundary yet | [state/data](react-state-data.md) |
| Minor ≥19.2, Activity reveal/recovery UI unresolved | Activity UI decision | Preserve state-owner evidence | [async UI](react-async-ui.md) |
| Minor ≥19.2, Effect needs latest non-reactive value | Effect Event candidate | Separate only non-reactive read | [Hooks/Effects](react-hooks-effects.md) |
| Minor <19.2 or unresolved | gated API unavailable/unconfirmed | Use compatible alternatives; investigate an unknown minor | none |
| Dependency avoidance is goal | blocked | Fix Effect ownership | [Hooks/Effects](react-hooks-effects.md) |

## Actions and Prohibitions

Change implementation/types together. A `useEffectEvent` change must preserve compatible Hooks lint behavior; update an existing lint dependency/config only within authority. Do not universally replace compatibility APIs, use Effect Event to suppress synchronization, pass it outside the Effect, create lint setup incidentally, or use gated APIs without a resolved minor.

## Uncertainty and Regressions

Continue investigating unknown consumers, tooling, and lifecycle defects. Defer only an unsupported or unconfirmed version-specific API or unresolved public break; repair or revert regressions in types/runtime/lifecycle.

## Verify

Verify types, ref attach/cleanup, provider scope/update, consumers, Activity state/lifecycle, or Effect synchronization as selected. For `useEffectEvent`, run the existing Hooks lint path when available and confirm it does not add the Effect Event to the dependency list.

## Result and Related Guidance

Explain compatibility and affected behavior, using [structure/public API](react-structure-public-api.md), [state/data](react-state-data.md), [async UI](react-async-ui.md), or [Hooks/Effects](react-hooks-effects.md) as needed.

Fact source: [React 19.2](https://react.dev/blog/2025/10/01/react-19-2).
