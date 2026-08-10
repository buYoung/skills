# React 19 Compiler Compatibility

## Read When

Read only for explicit React 19 Compiler config/compatibility/diagnostics work with baseline/hypothesis evidence from the render-performance leaf or an explicit existing-Compiler compatibility task. Build-tool adapter work stays outside this leaf.

## Collect Inputs

Collect resolved React 19, Compiler version, mode, target/runtime, build-integration identity, config, diagnostics, escape hatches, existing production build, exact caller, optional measurement handoff, and rollback point.

## Decision Sequence and Table

1. Require a performance or compatibility caller. 2. Compare React config/runtime compatibility. 3. Select retain/minimal fix/integration handoff/stop. 4. Verify production diagnostics. 5. Return to the exact caller.

| Observation | Selection | Action | Handoff |
|---|---|---|---|
| Existing compatible config | retain | No incidental changes | return_to_caller |
| Evidenced compatibility mismatch | minimal fix | Change only mismatch | return_to_caller |
| React config is valid but the build adapter is incompatible | external build handoff | Preserve mode/options/diagnostics without changing adapter here | external build owner |
| Performance caller lacks baseline/task | blocked | Do not enable/remove memoization | return_to_caller |
| Unsupported plugin/runtime or build fails | rollback/stop | Restore prior config | return_to_caller |

## Actions and Prohibitions

Preserve purity, Compiler options, and existing escape hatches. An explicit compatibility task may validate an existing Compiler without a performance baseline, but may not enable it or claim an improvement. Do not incidentally enable Compiler, bulk-remove memoization, use directives to hide impurity, decide build-tool adapters, or decide performance here.

## Stop or Roll Back

Stop on missing caller evidence, unresolved versions, incompatible runtime, or diagnostics/build failure. Performance adoption also stops without a baseline. Restore prior React config before return.

## Verify

Run existing production build and diagnostics, exercise behavior, and return results; the caller owns same-metric keep/rollback.

## Return and Handoff

Return compatibility/config/diagnostic evidence to [render performance](react-render-performance.md) or the exact caller. Return adapter mismatches as external build-owner requirements.

Fact sources: [React Compiler introduction](https://react.dev/learn/react-compiler/introduction) and [Compiler installation](https://react.dev/learn/react-compiler/installation).
