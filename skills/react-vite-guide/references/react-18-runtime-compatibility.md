# React 18 Runtime Compatibility

## Read When

Read only for resolved React 18 root/unmount warnings, ref/Context syntax, or React 18 Compiler compatibility. Hydration/SSR returns a scope stop to `SKILL.md`. Migration inventory belongs elsewhere.

## Collect Inputs

Collect resolved `react/react-dom`, CSR entry/root calls, warnings/unmount owner, app/library/mixed consumers, supported range, public ref/Context contract, types, and—only from performance handoff—Compiler target/runtime/plugin/diagnostics and baseline.

## Decision Sequence and Table

1. Confirm major 18 and CSR. 2. Select root, ref/Context, or Compiler subpath. 3. Preserve consumers/owners. 4. Edit or report. 5. Verify and return.

| Observation | Selection | Action | Handoff |
|---|---|---|---|
| Modern CSR root | retain | No style-only change | none |
| Legacy root, migration authorized | modern root migration | Change entry/unmount together | none |
| Root owner unresolved | compatibility hold | Do not partially convert | none |
| React 18-only app ref/Context | React 18 syntax | Use `forwardRef`, `useContext`, `.Provider` as required | none |
| Library/mixed public consumers | preserve contract | Keep compatible surface | [structure/public API](react-structure-public-api.md) |
| Compiler baseline/config supplied | compatibility check | Preserve React 18 target/runtime; fix evidenced mismatch | [render performance](react-render-performance.md) |
| Compiler baseline/config absent | blocked | Do not enable/remove memoization | [render performance](react-render-performance.md) |

## Actions and Prohibitions

Change entry lifecycle or implementation/types atomically. Do not introduce React 19 syntax, hydration handling, partial root conversion, incidental Compiler enablement, or bulk memoization removal.

## Stop or Roll Back

Stop on mixed/unresolved versions, hydration scope, unknown consumers/root owner, public break without approval, unsupported Compiler/runtime, or build/runtime failure. Restore prior entry/config on failure.

## Verify

Verify entry build/runtime, warnings, unmount, types, ref attach/cleanup, provider scope/update, consumers, and Compiler production diagnostics when applicable.

## Return and Handoff

Return version/syntax/compatibility evidence. Public compatibility goes to [structure/public API](react-structure-public-api.md); Compiler diagnostics return to [render performance](react-render-performance.md). Migration readiness is not decided here.

Fact sources: [React DOM client APIs](https://react.dev/reference/react-dom/client) and [Compiler target](https://react.dev/reference/react-compiler/target).
