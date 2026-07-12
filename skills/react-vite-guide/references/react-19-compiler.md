# React 19 Compiler Compatibility

## Read When

Read only for explicit React 19 Compiler config/compatibility/diagnostics work with baseline/hypothesis evidence from the render-performance leaf.

## Collect Inputs

Collect resolved React 19, Compiler/plugin versions, mode, target/runtime, config, diagnostics, escape hatches, existing production build, measurement handoff, and rollback point.

## Decision Sequence and Table

1. Require performance handoff. 2. Compare config/runtime/plugin compatibility. 3. Select retain/minimal fix/stop. 4. Verify production build/diagnostics. 5. Return for same-metric decision.

| Observation | Selection | Action | Handoff |
|---|---|---|---|
| Existing compatible config | retain | No incidental changes | [render performance](react-render-performance.md) |
| Evidenced compatibility mismatch | minimal fix | Change only mismatch | [render performance](react-render-performance.md) |
| Baseline/task absent | blocked | Do not enable/remove memoization | [render performance](react-render-performance.md) |
| Unsupported plugin/runtime or build fails | rollback/stop | Restore prior config | [render performance](react-render-performance.md) |

## Actions and Prohibitions

Preserve purity and existing escape hatches. Do not incidentally enable Compiler, bulk-remove memoization, use directives to hide impurity, or decide performance here.

## Stop or Roll Back

Stop on missing baseline, unresolved versions, incompatible plugin/runtime, or diagnostics/build failure. Restore prior config before return.

## Verify

Run existing production build and diagnostics, exercise behavior, and return results; the caller owns same-metric keep/rollback.

## Return and Handoff

Return compatibility/config/diagnostic evidence only to [render performance](react-render-performance.md).

Fact source: [React Compiler introduction](https://react.dev/learn/react-compiler/introduction).
