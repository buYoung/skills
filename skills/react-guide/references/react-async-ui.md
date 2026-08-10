# React Async UI and Recovery

## Read When

Read for route/feature lazy, Suspense, loading/background/empty/error states, Error Boundary, retry/reset, or user-visible stale-chunk recovery. Exclude request/cache ownership, React 19 Promise syntax, build-tool output, and accessibility mechanics.

## Collect Inputs

Collect async-owner evidence, route/feature weight/frequency, initial bundle evidence, natural wait/recovery unit, success/loading/background/empty/error/retry states, failure source, existing boundary, reset condition, and user-work preservation.

## Decision Sequence and Table

1. Require owner evidence for data work. 2. Model states and recovery unit. 3. Select eager/lazy and boundary placement. 4. Implement or report. 5. Verify and hand off presentation/build concerns.

| Observation | Selection | Action | Handoff |
|---|---|---|---|
| Request/cache owner absent | owner first | Do not place final data boundary | [state/data](react-state-data.md) |
| React 19 Promise candidate | API gate | Preserve owner/lifetime evidence | [React 19 Actions/async](react-19-actions-async.md) |
| First-screen/small frequent code | eager | Keep synchronous | none |
| Infrequent route or heavy optional feature | React lazy boundary | Preserve module-scope lazy, fallback, recovery, and fixed metric; request build-output evidence | external build owner |
| No cost/recovery evidence | no split | Return non-application | none |
| Initial pending | initial loading | Show scoped fallback | [accessibility](react-accessibility.md) |
| Stable content revalidates | background state | Preserve content and signal work | [accessibility](react-accessibility.md) |
| Successful zero result | empty | Show no-result meaning/action | [accessibility](react-accessibility.md) |
| Event/ordinary async failure | task-owned error | Explicit retry/rollback at owner | [accessibility](react-accessibility.md) |
| Render/lazy failure | Error Boundary | Use nearest meaningful existing boundary | [accessibility](react-accessibility.md) |
| Stale build chunk suspected | deployment owner first | Do not use boundary reset as repair; preserve work/recovery evidence | external deployment owner |

## Actions and Prohibitions

Write the state model before UI, place fallback/boundary/recovery together, preserve stable content/work, and declare lazy at module scope. Do not confuse empty/error, use Error Boundary for event callbacks, retry without an owner, or create a fake lazy split without evidence.

## Stop or Roll Back

Stop when owner, reset/retry, recovery unit, or user-work policy is unknown. Roll back lazy when returned build output regresses initial transfer, duplication, interaction, or recovery.

## Verify

Exercise every modeled state, repeated failure, retry/reset that changes the failure condition, state/work preservation, fallback, real navigation, and returned build measurement. Return to selection on failure.

## Return and Handoff

Return state model, boundary, recovery, lazy decision, and verification. A bundle claim also requires returned build-output evidence for the same interaction; a stale-chunk failure requires deployment-owner evidence. Internal owners remain [state/data](react-state-data.md), [React 19 Actions/async](react-19-actions-async.md), and [accessibility](react-accessibility.md).

Fact sources: [lazy](https://react.dev/reference/react/lazy), [Suspense](https://react.dev/reference/react/Suspense), and [Error Boundaries](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary).
