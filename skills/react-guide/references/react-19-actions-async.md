# React 19 Actions and Async APIs

## Read When

Read for React 19 Actions/form mutation or `use(Context|Promise)` explanation, design, and compatibility. Preserve the data owner and combine async presentation guidance as needed.

## Collect Inputs

Distinguish `actions-form`, `context-read`, and `promise-read`; inspect each path involved in the request:

- `actions-form`: resolved 19.x, form versus general mutation, owner evidence, result-state/descendant-pending/optimistic needs, duplicate submit, rollback, and retry.
- `context-read`: resolved 19.x, Context contract, call site, and public consumers.
- `promise-read`: resolved 19.x, owner evidence, Promise identity/cache/retry, Suspense, and Error Boundary.

## Decision Sequence and Table

1. Select the responsibility before collecting its inputs. 2. For `actions-form`, establish and preserve the canonical mutation owner first. 3. If that owner already satisfies every requested result/pending/optimistic behavior, return `retain owner`; otherwise select the exact unmet UI capability combination. 4. Edit or report. 5. Run only that path's verification and return.

| Observation | Selection | Action | Related guidance |
|---|---|---|---|
| Actions path, mutation owner is unclear | owner first | Do not select an Action API | [state/data](react-state-data.md) |
| Actions path, canonical owner already satisfies all requested result/pending/optimistic behavior | retain owner | Do not add competing Action state | none |
| Synchronous event | event handler | Keep direct handler | none |
| Canonical owner clear; only result/error state is unmet | `useActionState` | Own result state without replacing mutation owner | [async UI](react-async-ui.md) |
| Canonical owner clear; only descendant pending status is unmet | `useFormStatus` | Read parent-form status without replacing mutation owner | [async UI](react-async-ui.md) |
| Canonical owner clear; only reversible optimistic projection is unmet | `useOptimistic` | Layer projection over canonical owner | [async UI](react-async-ui.md) |
| Canonical owner clear; result state and descendant pending are unmet, optimistic is not | composed form | `useActionState` owns result; `useFormStatus` reads pending | [async UI](react-async-ui.md) |
| Canonical owner clear; optimistic plus result and/or pending are unmet | composed optimistic | Select result/pending API by those needs; layer `useOptimistic` only for projection | [async UI](react-async-ui.md) |
| Context path, internal contract | `use(Context)` candidate | Convert only for required control flow | none |
| Context path, public/mixed contract | compatibility evidence | Do not convert before consumer decision | [structure/public API](react-structure-public-api.md) |
| Stable owner-managed Promise and boundaries | `use(Promise)` candidate | Consume existing resource | [async UI](react-async-ui.md) |
| Promise owner/lifetime/retry absent | blocked | Do not create in render | [state/data](react-state-data.md) |

## Actions and Prohibitions

Preserve the canonical mutation owner, then change only unmet pending/result/error/projection/rollback/reset UI responsibilities. Do not use form status outside its form or as result state, optimistic state as canonical data, add a competing mutation owner, use `use` inside `try/catch`, create requests in render, use memoization as cache, or treat Effect fetch as Suspense.

## Uncertainty and Regressions

Investigate missing ownership, Promise identity, boundaries, or rollback handling. Defer only API choices whose version or intended UI behavior remains unresolved. Correct API composition that duplicates data/pending/error ownership.

## Invocation Context and Form Scope

React 19 function-valued `<form action>` and `<button formAction>` run in an Action context. A plain function action receives `FormData`; a `useActionState` reducer receives `(previousState, payload)`, and its returned dispatcher can be passed to `action`. Successful function actions reset uncontrolled form fields, so account for draft/reset behavior. A URL-valued action follows browser navigation semantics. These client function APIs alone do not provide a server endpoint or pre-hydration server execution. See [form](https://react.dev/reference/react-dom/components/form).

When calling the `useActionState` dispatcher manually (for example from a button handler), wrap the call in `startTransition`; otherwise Action pending behavior is not established. A form action already supplies that context. In a custom async Transition, state updates after an `await` currently need another `startTransition` to be marked as transitions. Keep controlled text input updates urgent. See [useActionState](https://react.dev/reference/react/useActionState) and [startTransition](https://react.dev/reference/react/startTransition).

`useFormStatus` observes the nearest parent form's submission. Put it in a descendant component inside that form; a Hook in the component that creates the form cannot observe that newly returned form, and an unrelated direct mutation is not a form submission. See [useFormStatus](https://react.dev/reference/react-dom/hooks/useFormStatus).

Call the `useOptimistic` setter inside an Action/Transition, including a function form action. Its projection is temporary while the Action is pending; update the canonical base value on success so the confirmed result remains afterward. On failure, preserve or restore the canonical value and surface retry/error feedback. Do not treat the optimistic projection as persistence. See [useOptimistic](https://react.dev/reference/react/useOptimistic).

## Verify

Verify only the selected responsibility. For Actions, confirm the original canonical mutation owner remains authoritative, then verify exactly the selected result/error state, form pending scope, optimistic confirm/rollback, retry, and reset. For Context, verify updates/consumers. For Promise, verify identity/rejection/fallback/new-resource retry.

## Result and Related Guidance

Explain the API selection, invocation context, canonical owner, and verification. Use [state/data](react-state-data.md) for lifecycle gaps, [async UI](react-async-ui.md) for recovery, and [structure/public API](react-structure-public-api.md) for public Context impact. SSR does not turn a client Action into a Server Function.

Fact sources: [`use`](https://react.dev/reference/react/use) and [`useActionState`](https://react.dev/reference/react/useActionState).
