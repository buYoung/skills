# React Compiler and Vite Plugin Integration

## Read When

Read only for React 18/19 Compiler integration with Vite 7/8, `@vitejs/plugin-react`, inline Babel, `@rolldown/plugin-babel`, or a Vite 7→8 plugin-arrival decision. Do not use to adopt React Compiler without a React owner decision or to migrate Vite core without a React plugin concern.

## Collect Inputs

Collect `caller_skill`, resolved React/Vite/Node versions, `@vitejs/plugin-react` version, Vite core migration stage, existing inline Babel config, Compiler version/mode/target/runtime/options, `react-compiler-runtime` when React 18, plugin order/filter, dependency authority, production diagnostics/output, rollback point, and optional performance baseline.

## Decision Sequence and Table

1. Validate React target/runtime ownership. 2. Validate Vite/plugin compatibility. 3. Keep Vite core and plugin-major stages separately reversible. 4. Adapt only invalidated integration. 5. Verify production diagnostics and return.

| Observation | Selection | Action | Next skill |
|---|---|---|---|
| Compiler target/runtime/mode owner is unresolved | React owner first | Do not change build integration | `react-guide` |
| Vite/plugin version or active build integration is unresolved | Vite owner first | Do not change Compiler config | `vite-guide` |
| Vite 7 with `@vitejs/plugin-react` v6 requested | blocked compatibility | Keep a Vite 7-compatible plugin or complete authorized Vite 8 arrival first | return to caller |
| Vite 8 core arrival with compatible `@vitejs/plugin-react` v5 | staged retain | Keep v5 unless a separate plugin-major need is authorized | return to caller |
| Plugin v6 has non-Compiler inline Babel transforms | external Babel integration | Move only existing transforms to authorized `@rolldown/plugin-babel` with preserved order/filter | return to caller |
| Plugin v6 has React Compiler config | Compiler preset integration | Use authorized `@rolldown/plugin-babel` and `reactCompilerPreset`; preserve Compiler options | return to caller |
| React 18 Compiler under plugin v6 | React 18 compatibility | Preserve target `'18'` and `react-compiler-runtime` | return to caller |
| Existing integration remains compatible | retain | Do not rewrite config or remove memoization incidentally | return to caller |
| Diagnostics/build/runtime fails | rollback/stop | Restore the last passing plugin/config stage | return to caller |

## Actions and Prohibitions

React owns Compiler semantics; Vite owns plugin execution and output. `@vitejs/plugin-react` v6 removes inline Babel and requires Vite 8, while v5 can remain during Vite 8 core arrival. Do not combine the Vite core major, React plugin major, and Compiler adoption into one irreversible step; install dependencies without authority; change Compiler mode/options accidentally; or claim performance without a same-condition baseline.

## Verify

Run the existing Vite production build and Compiler diagnostics, inspect plugin order/filter and transformed output, exercise React Refresh in development, and verify target/runtime behavior. A performance caller also repeats its fixed metric before keep/rollback.

## Return and Handoff

Return exact versions, migration stage, target/runtime, plugin/Babel integration, diagnostics, output, and rollback point. Missing React evidence goes to `react-guide`; missing Vite evidence goes to `vite-guide`; otherwise return to the exact caller.

Fact sources: [React Compiler installation](https://react.dev/learn/react-compiler/installation), [React Compiler target](https://react.dev/reference/react-compiler/target), [Vite 8 announcement](https://vite.dev/blog/announcing-vite8), and [`@vitejs/plugin-react` changelog](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react/CHANGELOG.md).
