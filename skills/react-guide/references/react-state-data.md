# React State and Data Ownership

## Read When

Read for derived/local/lifted state, URL/store/reducer/Context, editable drafts, server-data ownership, request lifetime, cache, abort, revalidation, or retry. Use the related async UI and React 19 references when presentation or syntax also matters.

## Collect Inputs

Collect existing source of truth, consumers/shareability, transitions, preservation/reset, update frequency, router/store/server-state owners, request initiator, cache/dedup/cancel/revalidate/error/retry behavior.

## Decision Sequence and Table

1. Draw the source-of-truth/request-owner map. 2. Remove competing copies. 3. Select one owner. 4. Move reads/writes/lifecycle. 5. Verify and return owner evidence.

| Observation | Selection | Action | Related guidance |
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

## Uncertainty and Regressions

Competing copies, stale responses, and unclear Promise lifetime are investigation targets. Recover the intended source of truth from current usages. Defer only unresolved draft/save/conflict or cache policy decisions; repair regressions in navigation, notification, ordering, and revalidation.

## Stable External-Store Contract

With `useSyncExternalStore`, `subscribe` must return an unsubscribe function and keep a stable identity when the store/key is unchanged. `getSnapshot` must return the same value by `Object.is` until the observed data changes: do not allocate a fresh object on every read. Return immutable snapshots, or cache an immutable view of mutable data. Scope subscribers to the data they render so a row update need not invalidate the collection shell.

When a store already exposes suitable collection and per-item subscriptions, narrow the component's subscription first. Preserve the notification and snapshot meaning of every existing public store method; removing notifications from a broad subscription can break other consumers even if the optimized screen no longer uses it. Fix an incompatible snapshot at the affected consumer/adapter boundary when the store's public contract must stay intact.

For SSR, supply `getServerSnapshot` with the same initial data on the server and during client hydration, then let live snapshots reflect later changes. See [external-store subscription](https://react.dev/reference/react/useSyncExternalStore) and [SSR and hydration](react-ssr-hydration.md) for transfer and request isolation.

## Verify

Verify source-of-truth uniqueness, forward/back navigation, transitions, preservation/reset, provider update breadth, deduplication, abort/stale responses, retry, revalidation, failure, and draft behavior.

## Result and Related Guidance

Explain the source of truth, request lifetime, and preservation/reset decisions. Combine [Hooks/Effects](react-hooks-effects.md), [structure/public API](react-structure-public-api.md), [async UI](react-async-ui.md), and [React 19 Actions](react-19-actions-async.md) when needed. Initial server data and snapshots also require [SSR and hydration](react-ssr-hydration.md).

Fact source: [choosing state structure](https://react.dev/learn/choosing-the-state-structure).
