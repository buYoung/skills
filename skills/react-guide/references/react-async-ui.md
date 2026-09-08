# React Async UI and Recovery

## Read When

Read for route/feature lazy, Suspense, loading/background/empty/error states, Error Boundary, retry/reset, or user-visible stale-chunk recovery. Use related state, API, build-tool, and accessibility guidance when those concerns affect the solution.

## Collect Inputs

Collect async-owner evidence, route/feature weight/frequency, initial bundle evidence, natural wait/recovery unit, success/loading/background/empty/error/retry states, failure source, existing boundary, reset condition, and user-work preservation.

## Decision Sequence and Table

1. Inspect the existing data owner and request lifetime. 2. Model states and recovery unit. 3. Select eager/lazy and boundary placement. 4. Implement or report. 5. Verify presentation and relevant build behavior.

| Observation | Selection | Action | Related guidance |
|---|---|---|---|
| Request/cache owner absent | owner first | Do not place final data boundary | [state/data](react-state-data.md) |
| React 19 Promise candidate | API gate | Preserve owner/lifetime evidence | [React 19 Actions/async](react-19-actions-async.md) |
| First-screen/small frequent code | eager | Keep synchronous | none |
| Infrequent route or heavy optional feature | React lazy boundary | Preserve module-scope lazy, fallback, recovery, and fixed metric; inspect build-output evidence | build-tool guidance |
| No cost/recovery evidence | no split | Return non-application | none |
| Initial pending | initial loading | Show scoped fallback | [accessibility](react-accessibility.md) |
| Stable content revalidates | background state | Preserve content and signal work | [accessibility](react-accessibility.md) |
| Successful zero result | empty | Show no-result meaning/action | [accessibility](react-accessibility.md) |
| Event/ordinary async failure | task-owned error | Explicit retry/rollback at owner | [accessibility](react-accessibility.md) |
| Render/lazy failure | Error Boundary | Use nearest meaningful existing boundary | [accessibility](react-accessibility.md) |
| Stale build chunk suspected | deployment owner first | Do not use boundary reset as repair; preserve work/recovery evidence | deployment guidance |

## Actions and Prohibitions

Write the state model before UI, place fallback/boundary/recovery together, preserve stable content/work, and declare lazy at module scope. Do not confuse empty/error, use Error Boundary for event callbacks, retry without an owner, or create a fake lazy split without evidence.

Distinguish refresh of the same entity from navigation to a different entity key. Preserve visible data and drafts during same-key refresh, but do not render the previous entity as the newly selected one. Check data-key consistency during render (or use an intentional keyed boundary); resetting old data only in a passive Effect can expose one stale commit before the reset runs. Ignore superseded results independently of this render-time check.

## Uncertainty and Regressions

Investigate absent retry/reset behavior and incomplete loading/error states as defects. Defer only an unresolved recovery or user-work policy choice. Correct or revert lazy changes that regress transfer, duplication, interaction, or recovery.

## SSR Suspense Boundaries

A streaming server can send the initial shell with Suspense fallbacks and reveal later content as it becomes ready. An Effect fetch does not make a server-rendered subtree suspend. Resolve data with the existing data integration or preload the initial data; do not invent an ad hoc Promise cache in render. Server stream failures and HTTP status timing differ from client Error Boundaries. Use [SSR and hydration](react-ssr-hydration.md) for shell, abort, and hydration behavior.

## Verify

Exercise every modeled state, repeated failure, retry/reset that changes the failure condition, state/work preservation, fallback, real navigation, and build measurement. Return to selection on failure.

## Result and Related Guidance

Report the states, boundary, recovery, and lazy-loading decision. A bundle claim needs build-output evidence for the same interaction; stale-chunk recovery also needs deployment evidence. Read [state/data](react-state-data.md), [React 19 Actions](react-19-actions-async.md), [accessibility](react-accessibility.md), and [SSR and hydration](react-ssr-hydration.md) as relevant.

Fact sources: [lazy](https://react.dev/reference/react/lazy), [Suspense](https://react.dev/reference/react/Suspense), and [Error Boundaries](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary).
