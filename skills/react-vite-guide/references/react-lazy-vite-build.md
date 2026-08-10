# React Lazy and Vite Build Integration

## Read When

Read only when a React 18/19 lazy or Suspense boundary and Vite 7/8 dynamic-import/chunk output must be decided together. Do not use for React async-state modeling without a bundle question or for generic Vite chunk tuning without a React boundary.

## Collect Inputs

Collect `caller_skill`, resolved versions, React module owner, module-scope `lazy` declaration, natural wait/recovery unit, fallback/Error Boundary/reset behavior, fixed user interaction, initial bundle and route/feature cost evidence, Vite production graph, active bundler/config owner, CSS/modulepreload behavior, cache requirement, same-condition baseline, and rollback point.

## Decision Sequence and Table

1. Validate the React boundary evidence. 2. Validate the Vite output evidence. 3. Preserve the caller's metric. 4. Select one reversible seam change. 5. Compare the same interaction and return.

| Observation | Selection | Action | Next skill |
|---|---|---|---|
| Natural wait/recovery unit or React owner is absent | React owner first | Do not create a split | `react-guide` |
| Production graph, active bundler, or baseline is absent | Vite owner first | Do not claim bundle benefit | `vite-guide` |
| First-screen/small/frequent unit | eager integration | Keep synchronous and preserve UI behavior | return to caller |
| Infrequent route/heavy optional unit with measured cost | lazy integration | Keep module-scope lazy boundary; ask Vite owner for native output | `vite-guide` |
| Vite output improves the fixed metric without CSS/duplicate/cache regression | keep | Preserve React recovery and Vite output evidence | return to caller |
| Output is neutral, regressed, or breaks recovery | rollback | Restore the last passing React/Vite seam | return to caller |

## Actions and Prohibitions

React owns the wait/recovery boundary; Vite owns the emitted graph and version-native splitting contract. Do not invent a React boundary to justify `manualChunks`/`codeSplitting`, tune chunks before a natural UI unit exists, move `lazy` inside render, compare different interactions, or let a bundler result remove required fallback/error behavior.

## Verify

Exercise the same navigation or feature interaction in a production build. Compare initial transfer, requested chunk, duplicates, CSS/modulepreload, cache behavior, fallback, failure, retry/reset, and preserved user work. Return measured output to the exact caller.

## Return and Handoff

Return the fixed metric, React boundary, Vite graph, comparison, correctness, and keep/rollback decision. Missing React evidence goes to `react-guide`; missing Vite evidence goes to `vite-guide`; otherwise `next_skill: return_to_caller` when a caller exists.

Fact sources: [React lazy](https://react.dev/reference/react/lazy), [React Suspense](https://react.dev/reference/react/Suspense), [Vite 7 build options](https://v7.vite.dev/config/build-options), and [Vite 8 build options](https://vite.dev/config/build-options).
