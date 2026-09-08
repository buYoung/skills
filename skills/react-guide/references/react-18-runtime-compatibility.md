# React 18 Runtime Compatibility

## Read When

Read for React 18 root/unmount warnings, ref/Context syntax, or Compiler compatibility. Use [SSR and hydration](react-ssr-hydration.md) for server roots and hydration; use migration guidance for an upgrade inventory.

## Collect Inputs

Collect resolved `react/react-dom`, rendering mode and entry/root calls, warnings/unmount owner, app/library/mixed consumers, supported range, public ref/Context contract, and types. For Compiler work, identify whether the task is performance adoption or existing compatibility repair, then collect Compiler target/runtime, build-integration identity, diagnostics, and rollback point.

## Decision Sequence and Table

1. Establish major 18 and the rendering mode. 2. Select root, ref/Context, or Compiler subpath. 3. Preserve consumers/owners. 4. Edit or report. 5. Verify and return.

| Observation | Selection | Action | Related guidance |
|---|---|---|---|
| Modern CSR root | retain | No style-only change | none |
| Legacy root, migration authorized | modern root migration | Change entry/unmount together | none |
| Root owner unresolved | compatibility hold | Do not partially convert | none |
| React 18-only app ref/Context | React 18 syntax | Use `forwardRef`, `useContext`, `.Provider` as required | none |
| Library/mixed public consumers | preserve contract | Keep compatible surface | [structure/public API](react-structure-public-api.md) |
| Compiler baseline/config supplied | compatibility check | Preserve React 18 target/runtime; fix evidenced mismatch | [render performance](react-render-performance.md) |
| Existing Compiler config needs build-adapter work | build integration | Preserve target `'18'`, `react-compiler-runtime`, options, and diagnostics | build-tool guidance |
| Compiler baseline/config absent | blocked | Do not enable/remove memoization | [render performance](react-render-performance.md) |

## Actions and Prohibitions

Change entry lifecycle or implementation/types atomically. Preserve Compiler target/runtime and use build-tool guidance for adapter configuration. Do not introduce React 19-only syntax, partial root conversion, incidental Compiler enablement, or bulk memoization removal.

## Uncertainty and Regressions

For mixed consumers, target the oldest supported runtime; do not treat a known mixed range as a reason to stop. Investigate unresolved root ownership, runtime mismatches, and build failures. Defer only version-sensitive or public breaking choices lacking evidence; fix or revert a change that introduced a regression.

## Verify

Verify entry build/runtime, warnings, unmount, types, ref attach/cleanup, provider scope/update, consumers, and Compiler production diagnostics when applicable.

## Result and Related Guidance

Report version and compatibility findings. Use [structure/public API](react-structure-public-api.md) for consumers, [render performance](react-render-performance.md) for measured outcomes, [SSR and hydration](react-ssr-hydration.md) for server roots, and build-tool guidance for adapters.

Fact sources: [React DOM client APIs](https://react.dev/reference/react-dom/client), [Compiler target](https://react.dev/reference/react-compiler/target), and [Compiler installation](https://react.dev/learn/react-compiler/installation).
