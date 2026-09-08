# Vite 7/8 Build and Plugins

## Read When

Read for resolved Vite 7 or 8 dynamic import/chunk/import graph, CSS/modulepreload, `import.meta.glob`, Rollup/Rolldown splitting, plugin capability, or measured dev/build performance. Combine UI-framework guidance for rendering/Compiler semantics with this reference for adapters. Use deployment, migration, or SSR guidance when implicated.

## Collect Inputs

Identify the relevant `chunk`, `plugin`, or `dev-performance` paths and exact Vite/Node/plugin versions. For `chunk`, collect production bundle, active bundler/config key, import/module owner, fixed interaction, cache/deploy requirement, rollback point, optional framework-boundary evidence, and optional performance or migration evidence. For `plugin`, collect the capability gap, existing chain, exact Vite/bundler compatibility, maintenance/config cost, fallback/rollback, authority, and optional migration evidence. For `dev-performance`, collect the exact startup/full-reload/HMR symptom and baseline, module/request counts, browser cache/extensions/proxy conditions, plugin timing evidence, experimental-version pin, third-party plugin compatibility, and rollback point.

## Decision Sequence and Table

1. Select one responsibility. 2. Apply the exact version/bundler gate. 3. Compare current/built-in behavior. 4. Select one minimum action. 5. Run responsibility-specific verification.

| Observation | Selection | Action | Related guidance |
|---|---|---|---|
| UI-framework lazy path lacks boundary/interaction/baseline | inspect framework behavior | Read framework guidance and gather current evidence | framework guidance |
| UI-framework lazy boundary evidence is present | output evaluation | Preserve its boundary and metric; compare version-native output | none |
| Generic path lacks module owner/interaction/baseline | blocked | Do not invent a framework boundary | none |
| Generic default output meets goal | retain defaults | No manual splitting | none |
| Vite 7 measured cache/initial/shared-dependency problem | minimal Rollup split | Change one evidenced `build.rollupOptions.output.manualChunks` boundary | none |
| Vite 8 measured cache/initial/shared-dependency problem | minimal Rolldown split | Prefer one evidenced `codeSplitting` rule; do not add deprecated `manualChunks` | none |
| Migration requires a splitting change | migration-owned split | Apply one native Rolldown rule, compare output, preserve arrival evidence | none |
| Framework-owned chunk output regresses | rollback | Restore Vite config and return output evidence | none |
| Generic chunk regression | rollback | Restore config/boundary | none |
| Built-in/current config solves plugin gap | no new plugin | Use existing capability | none |
| Existing compatible plugin solves gap | configure existing | Minimum config edit | none |
| Framework-specific plugin semantics are unresolved | framework owner first | Preserve exact Vite/bundler/plugin evidence | framework guidance |
| Vite 7 with `@vitejs/plugin-react` v6 requested | blocked compatibility | Keep a Vite 7-compatible plugin or complete Vite 8 arrival first | none |
| Vite 8 with compatible `@vitejs/plugin-react` v5 | staged retain | Keep v5 unless a separate plugin-major need is authorized | none |
| `@vitejs/plugin-react` v6 replaces existing inline Babel or Compiler config | external Babel adapter | Use authorized `@rolldown/plugin-babel`; preserve the existing Compiler options for `reactCompilerPreset` | none |
| Plugin lacks exact Vite/bundler compatibility or authority | blocked | Return user decision need | none |
| Dev slowness lacks a comparable baseline or simpler cause audit | measure first | Check browser, resolver, barrels, plugins, and warmup evidence | none |
| Vite 8.1+ bundled-dev trial is authorized, pinned, and compatible | reversible experiment | Enable only for the measured large-module path | none |
| Bundled-dev plugin/feature incompatibility or neutral result | rollback | Restore unbundled dev | none |

## Actions and Prohibitions

For `chunk`, measure defaults before one reversible rule and preserve the active bundler's native config contract. Prohibit fake UI-framework boundaries, blanket vendor chunks, tiny first-screen splits, unanalyzable paths, Vite 7's removed `splitVendorChunkPlugin`, and Vite 8's unsupported object or deprecated function `manualChunks`. For `plugin`, prove the gap and compare built-in/current paths; prohibit installation without authority and establish framework semantics from the current project and relevant framework guidance before validating an adapter. Keep Vite core, framework-plugin major, and Compiler adoption separately reversible. For `dev-performance`, remove measurement confounders and inspect plugin/resolve work before an experimental bundled-dev trial; never present experimental behavior as a stable default.

## Uncertainty and Regressions

Continue diagnosing output failures and compatibility gaps. Without a baseline, avoid speculative splitting and performance claims, but repair evidenced behavior/configuration defects. Defer unsupported or unconfirmed plugin/experimental choices and correct or revert regressions in output, CSS, caching, interaction, startup, or HMR.

## SSR Build and Analysis

A server build and a client build have different resolution, externalization, and asset responsibilities. Inspect both outputs with [SSR integration](vite-ssr.md); a working client dependency optimizer does not prove production server imports resolve. Preserve existing framework Compiler semantics while configuring the Vite adapter.

Build analysis through `devtools` has separate experimental, package, and build-mode conditions; see [runtime diagnostics](vite-client-runtime.md). Neither analysis output nor a successful config load establishes a performance gain without comparable measurements.

## Exact Adapter Compatibility

Before choosing plugin/adapter versions, inspect their actual `peerDependencies` together, including required transformation runtimes. Do not infer compatibility from a shared major label or choose a plausible-looking latest adapter. If installation is unavailable, use installed/lockfile metadata or official package/release evidence; mark unresolved combinations unconfirmed instead of presenting a guessed version as compatible.

For the Babel React Compiler path, check `@vitejs/plugin-react`, `@rolldown/plugin-babel`, `@babel/core`, and `babel-plugin-react-compiler` as one dependency chain. Preserve the existing explicit Compiler target and mode in `reactCompilerPreset`. Patch versions matter: plugin-react 6.0.0 declares the optional plugin-babel peer as `^0.1.7`, which does not admit 0.2.x; a later release broadens that range. Select a pair supported by the actual selected versions and ensure Babel core is provided. See the [upstream peer conflict](https://github.com/vitejs/vite-plugin-react/issues/1144), [plugin release history](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react/CHANGELOG.md), and [Babel Compiler integration](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react/README.md#babel-react-compiler).

## Verify

For `chunk`, compare the same production interaction, graph, bytes, duplicates, CSS/modulepreload, cache, and trigger. For `plugin`, verify ordering, apply mode, dev/build, and output under the resolved Vite/bundler pair. For `dev-performance`, repeat the same cold start, full reload, and HMR interaction with browser/proxy conditions fixed, then verify plugin behavior and correctness.

For package-based chunk filters, inspect both matching and non-matching module paths on POSIX and Windows. Match complete package names and subpaths, not a naming-family prefix: a rule for `react` and `react-dom` must not accidentally absorb unrelated `react-*` packages. Check overlapping group precedence against the required output boundary.

## Result and Related Guidance

Report the graph, adapter, diagnostics, or measured comparison relevant to the task. Use [migration](vite-7-to-8-migration.md), [deployment](vite-deployment.md), [SSR integration](vite-ssr.md), and framework guidance directly. Preserve established boundaries, options, and metrics unless the task requires changing them.

Fact sources: [Vite 7 build options](https://v7.vite.dev/config/build-options), [Vite 8 build options](https://vite.dev/config/build-options), [Vite performance](https://vite.dev/guide/performance), [Vite 8 migration](https://vite.dev/guide/migration), [Vite 8.1 bundled dev](https://vite.dev/blog/announcing-vite8-1), and [`@vitejs/plugin-react` changelog](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react/CHANGELOG.md).
