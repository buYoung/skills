# React Render Performance

## Read When

Read for rerender diagnosis, subscription breadth, `memo`/`useMemo`/`useCallback`, Compiler-related optimization, Profiler evidence, or a performance claim. Exclude API compatibility and async/chunk boundary ownership.

## Collect Inputs

Fix the user interaction, symptom, metric, environment/data, baseline, prop/reference changes, calculation cost, subscription breadth, current memoization/Compiler status, hypothesis, and rollback point.

## Decision Sequence and Table

1. Capture baseline. 2. Fix owner/Effect/subscription causes first. 3. Choose the smallest reversible change. 4. Compare the same condition. 5. Keep or roll back.

| Observation | Selection | Action | Handoff |
|---|---|---|---|
| State owner or broad subscription causes work | root-cause fix | Do not add memoization | [state/data](react-state-data.md) |
| Effect lifecycle causes work | root-cause fix | Do not add memoization | [Hooks/Effects](react-hooks-effects.md) |
| No measured bottleneck | no memo | Return non-application finding | none |
| Stable props, costly child render | `memo` | Memoize narrow child; compare locally | none |
| Costly pure calculation | `useMemo` | Cache calculation; compare locally | none |
| Measured identity contract | `useCallback` | Stabilize callback; compare locally | none |
| Structural skip is clearer | component extraction | Preserve profile evidence | [structure/public API](react-structure-public-api.md) |
| React 18 Compiler compatibility needed | version check | Pass baseline/config evidence | [React 18 runtime](react-18-runtime-compatibility.md) |
| React 19 Compiler compatibility needed | version check | Pass baseline/config evidence | [React 19 Compiler](react-19-compiler.md) |
| Lazy/chunk claim | boundary then output | Pass interaction/baseline | [async UI](react-async-ui.md) |

## Actions and Prohibitions

Use React Profiler for render work, browser Performance for main thread/layout, Network for requests, and existing production bundle output for chunks. Do not add performance-only memoization without baseline, suppress Effect dependencies, bulk-remove memoization because Compiler exists, change comparison conditions, or add analyzer dependencies.

## Stop or Roll Back

Without representative measurement, do not claim improvement; return an unverified hypothesis only. Roll back neutral, regressed, or incorrect changes.

## Verify

Repeat the same interaction/metric/environment, then check correctness. Compiler or chunk handoffs must return diagnostics/output before keep/rollback. A missing comparison returns to input collection.

## Return and Handoff

Return baseline, hypothesis, change/finding, comparison, correctness, and keep/rollback. Allowed leaves: [structure/public API](react-structure-public-api.md), [async UI](react-async-ui.md), [React 18 runtime](react-18-runtime-compatibility.md), [React 19 Compiler](react-19-compiler.md), or [Vite build/plugins](vite-7-build-plugins.md) after an async boundary decision.

Fact source: [React Profiler](https://react.dev/reference/react/Profiler).
