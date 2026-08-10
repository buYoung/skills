# React 19 Actions and Async APIs

## Read When

Read for resolved React 19 Actions/form mutation or `use(Context|Promise)` compatibility. State/data owner and async presentation remain external owners.

## Collect Inputs

First set `responsibility` to exactly one of `actions-form`, `context-read`, or `promise-read`. Collect only that path's inputs:

- `actions-form`: resolved 19.x, form versus general mutation, owner evidence, result-state/descendant-pending/optimistic needs, duplicate submit, rollback, and retry.
- `context-read`: resolved 19.x, Context contract, call site, and public consumers.
- `promise-read`: resolved 19.x, owner evidence, Promise identity/cache/retry, Suspense, and Error Boundary.

## Decision Sequence and Table

1. Select the responsibility before collecting its inputs. 2. For `actions-form`, establish and preserve the canonical mutation owner first. 3. If that owner already satisfies every requested result/pending/optimistic behavior, return `retain owner`; otherwise select the exact unmet UI capability combination. 4. Edit or report. 5. Run only that path's verification and return.

| Observation | Selection | Action | Handoff |
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

## Stop or Roll Back

For `actions-form`, stop only on missing canonical mutation owner, indistinguishable requested UI needs, or required rollback/retry/reset. For `context-read`, stop only on unresolved public consumers. For `promise-read`, stop only on missing owner, identity, retry, Suspense, or Error Boundary. Roll back API composition that replaces the canonical owner or duplicates pending/error/data ownership.

## Verify

Verify only the selected responsibility. For Actions, confirm the original canonical mutation owner remains authoritative, then verify exactly the selected result/error state, form pending scope, optimistic confirm/rollback, retry, and reset. For Context, verify updates/consumers. For Promise, verify identity/rejection/fallback/new-resource retry.

## Return and Handoff

Return API selection and owner-specific evidence. Send owner gaps to [state/data](react-state-data.md), UI states/recovery to [async UI](react-async-ui.md), and public Context impact to [structure/public API](react-structure-public-api.md).

Fact sources: [`use`](https://react.dev/reference/react/use) and [`useActionState`](https://react.dev/reference/react/useActionState).
