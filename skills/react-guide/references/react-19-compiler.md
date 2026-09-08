# React 19 Compiler Compatibility

## Read When

Read for React 19 Compiler explanation, config, compatibility, and diagnostics. Performance adoption needs a baseline/hypothesis; existing compatibility repair can use current source and diagnostics. Use build-tool guidance for adapter configuration.

## Collect Inputs

Collect resolved React 19, Compiler version, mode, target/runtime, build-integration identity, config, diagnostics, escape hatches, existing production build, optional measurements, and rollback point.

## Decision Sequence and Table

1. Distinguish performance adoption from compatibility repair. 2. Compare React config/runtime compatibility. 3. Select retain/minimal fix/build integration. 4. Verify production diagnostics. 5. Report the supported conclusions.

| Observation | Selection | Action | Related guidance |
|---|---|---|---|
| Existing compatible config | retain | No incidental changes | none |
| Evidenced compatibility mismatch | minimal fix | Change only mismatch | none |
| React config is valid but the build adapter is incompatible | build integration | Preserve mode/options/diagnostics without changing adapter here | build-tool guidance |
| Performance adoption lacks baseline | blocked | Do not enable/remove memoization | none |
| Unsupported plugin/runtime or build fails | rollback/stop | Restore prior config | none |

## Actions and Prohibitions

Preserve purity, Compiler options, and existing escape hatches. An explicit compatibility task may validate an existing Compiler without a performance baseline, but may not enable it or claim an improvement. Do not incidentally enable Compiler, bulk-remove memoization, use directives to hide impurity, select adapters without build-tool guidance, or decide performance here.

## Uncertainty and Regressions

Investigate unresolved versions and existing runtime/build failures without adopting unverified APIs. Defer performance adoption without a representative baseline, while continuing compatibility repair. Revert newly introduced incompatible configuration.

## Verify

Run existing production build and diagnostics, exercise behavior, and return results; use the same metric for a performance keep/rollback decision.

## Result and Related Guidance

Report compatibility, configuration, and diagnostics. Use [render performance](react-render-performance.md) for measured outcomes and build-tool guidance for adapter mismatches. No caller identity or prior handoff record is required.

Fact sources: [React Compiler introduction](https://react.dev/learn/react-compiler/introduction) and [Compiler installation](https://react.dev/learn/react-compiler/installation).
