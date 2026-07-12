# React 19 Component API Compatibility

## Read When

Read for resolved React 19 ref prop/provider syntax or React 19.2 `Activity`/`useEffectEvent`. Exclude general public API, state, and Effect ownership.

## Collect Inputs

Collect resolved major/minor, app/library/mixed consumers, supported range, public contract, ref/provider call sites/types, and state/Effect owner evidence for 19.2 features.

## Decision Sequence and Table

1. Gate major/minor. 2. Classify consumers or feature signal. 3. Select compatibility form. 4. Edit or report. 5. Verify and return to owner.

| Observation | Selection | Action | Handoff |
|---|---|---|---|
| New React 19-only app ref/provider code | React 19 form | Ref prop/provider shorthand may be used | none |
| Existing stable or mixed public contract | compatibility form | Preserve `forwardRef`/`useContext` when required | [structure/public API](react-structure-public-api.md) |
| Minor ≥19.2, Activity state owner unresolved | Activity owner handoff | Do not apply boundary yet | [state/data](react-state-data.md) |
| Minor ≥19.2, Activity reveal/recovery UI unresolved | Activity UI handoff | Preserve state-owner evidence | [async UI](react-async-ui.md) |
| Minor ≥19.2, Effect needs latest non-reactive value | Effect Event candidate | Separate only non-reactive read | [Hooks/Effects](react-hooks-effects.md) |
| Minor <19.2/unconfirmed, initial request | not applicable | Do not suggest gated API | none |
| Minor <19.2/unconfirmed, caller evidence present | not applicable | Preserve gate result | return_to_caller |
| Dependency avoidance is goal | blocked | Fix Effect ownership | [Hooks/Effects](react-hooks-effects.md) |

## Actions and Prohibitions

Change implementation/types together. Do not universally replace compatibility APIs, use Effect Event to suppress synchronization, pass it outside the Effect, or use gated APIs without a resolved minor.

## Stop or Roll Back

Stop on unknown consumer range, unapproved break, unsupported minor/tooling, or missing state/Effect owner evidence. Roll back on type/runtime/lifecycle regression.

## Verify

Verify types, ref attach/cleanup, provider scope/update, consumers, Activity state/lifecycle, or Effect synchronization as selected.

## Return and Handoff

Return compatibility evidence to [structure/public API](react-structure-public-api.md), Activity evidence to [state/data](react-state-data.md) or [async UI](react-async-ui.md), and Effect Event evidence to [Hooks/Effects](react-hooks-effects.md).

Fact source: [React 19.2](https://react.dev/blog/2025/10/01/react-19-2).
