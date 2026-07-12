# React State and Data Ownership

## Read When

Read for derived/local/lifted state, URL/store/reducer/Context, editable drafts, server-data ownership, request lifetime, cache, abort, revalidation, or retry. Exclude UI presentation and React 19 API syntax.

## Collect Inputs

Collect existing source of truth, consumers/shareability, transitions, preservation/reset, update frequency, router/store/server-state owners, request initiator, cache/dedup/cancel/revalidate/error/retry behavior, and caller leaf.

## Decision Sequence and Table

1. Draw the source-of-truth/request-owner map. 2. Remove competing copies. 3. Select one owner. 4. Move reads/writes/lifecycle. 5. Verify and return owner evidence.

| Observation | Selection | Action | Handoff |
|---|---|---|---|
| Derivable value without measured cost | derived | Remove mirrored state | none |
| Derivable value with measured render cost | derived/performance evidence | Remove mirror; preserve metric | [render performance](react-render-performance.md) |
| Shareable/navigation state | URL/router | Keep URL authoritative | none |
| Existing cross-tree client owner | existing store | Use its subscription contract | none |
| One UI owner | local state | Colocate | none |
| Siblings coordinate one fact | lifted state | Move to common owner | none |
| Complex event transitions | reducer | Centralize event-named transitions | none |
| Distant React-owned consumers | narrow Context | Transport owner state | none |
| Remote cache/revalidate/failure | server-state owner | Keep router/server layer authoritative | [async UI](react-async-ui.md) |
| Synchronous editable divergence | editable draft | Define initialize/cancel/reset | none |
| Async editable draft | editable draft | Define initialize/save/cancel/conflict/reset | [async UI](react-async-ui.md) |
| React 19 Action or Promise candidate | API compatibility | Preserve owner evidence | [React 19 Actions/async](react-19-actions-async.md) |

## Actions and Prohibitions

Move reads, writes, transitions, reset, abort, retry, and revalidation with the selected owner. Do not mirror URL/store/server state, make Context a state owner, create requests during render, or use memoization as a request cache.

## Stop or Roll Back

Stop on competing owners, unknown Promise lifetime, undefined draft/save/reset, or irreconcilable cache/retry behavior. Roll back if navigation, subscribers, stale-response ordering, or revalidation regresses.

## Verify

Verify source-of-truth uniqueness, forward/back navigation, transitions, preservation/reset, provider update breadth, deduplication, abort/stale responses, retry, revalidation, failure, and draft behavior.

## Return and Handoff

Return the owner map and lifecycle evidence. For request Effects, return abort/stale/retry evidence to [Hooks/Effects](react-hooks-effects.md). For component separation, return state/reset evidence to [structure/public API](react-structure-public-api.md). Route visible states to [async UI](react-async-ui.md); route only React 19 API compatibility to [React 19 Actions/async](react-19-actions-async.md). Use the caller identity in handoff evidence so only the requesting leaf resumes.

Fact source: [choosing state structure](https://react.dev/learn/choosing-the-state-structure).
