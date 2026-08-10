# Vite 7/8 Build and Plugins

## Read When

Read for resolved Vite 7 or 8 dynamic import/chunk/import graph, CSS/modulepreload, `import.meta.glob`, Rollup/Rolldown splitting, plugin capability, or measured dev/build performance. Exclude UI-framework boundary selection, framework-specific plugin integration, deployment recovery, migration inventory, and unmeasured optimization.

## Collect Inputs

First set `responsibility` to `chunk`, `plugin`, or `dev-performance`; receive the common Vite preflight record, exact Vite major/minor, optional UI-framework identity, and optional caller identity. For `chunk`, collect production bundle, active bundler/config key, import/module owner, fixed interaction, cache/deploy requirement, rollback point, optional framework-boundary evidence, and optional performance or migration evidence. For `plugin`, collect the capability gap, existing chain, exact Vite/bundler compatibility, maintenance/config cost, fallback/rollback, authority, and optional migration evidence. For `dev-performance`, collect the exact startup/full-reload/HMR symptom and baseline, module/request counts, browser cache/extensions/proxy conditions, plugin timing evidence, experimental-version pin, third-party plugin compatibility, and rollback point.

## Decision Sequence and Table

1. Select one responsibility. 2. Apply the exact version/bundler gate. 3. Compare current/built-in behavior. 4. Select one minimum action. 5. Run responsibility-specific verification.

| Observation | Selection | Action | Handoff |
|---|---|---|---|
| UI-framework lazy path lacks boundary/interaction/baseline | framework owner first | Do not change chunks or invent UI semantics | external framework owner |
| UI-framework lazy boundary evidence is present | output evaluation | Preserve its boundary and metric; compare version-native output | return_to_caller |
| Generic path lacks module owner/interaction/baseline | blocked | Do not invent a framework boundary | none |
| Generic default output meets goal | retain defaults | No manual splitting | none |
| Vite 7 measured cache/initial/shared-dependency problem | minimal Rollup split | Change one evidenced `build.rollupOptions.output.manualChunks` boundary | none |
| Vite 8 measured cache/initial/shared-dependency problem | minimal Rolldown split | Prefer one evidenced `codeSplitting` rule; do not add deprecated `manualChunks` | none |
| Vite migration caller supplies a required splitting change | migration-owned split | Apply one native Rolldown rule, compare output, preserve arrival evidence | return_to_caller |
| Framework-owned chunk output regresses | rollback | Restore Vite config and return output evidence | return_to_caller |
| Generic chunk regression | rollback | Restore config/boundary | none |
| Built-in/current config solves plugin gap | no new plugin | Use existing capability | none |
| Existing compatible plugin solves gap | configure existing | Minimum config edit | none |
| Framework-specific plugin semantics are unresolved | framework owner first | Preserve exact Vite/bundler/plugin evidence | external framework owner |
| Vite 7 with `@vitejs/plugin-react` v6 requested | blocked compatibility | Keep a Vite 7-compatible plugin or complete Vite 8 arrival first | none |
| Vite 8 with compatible `@vitejs/plugin-react` v5 | staged retain | Keep v5 unless a separate plugin-major need is authorized | none |
| `@vitejs/plugin-react` v6 replaces existing inline Babel or Compiler config | external Babel adapter | Use authorized `@rolldown/plugin-babel`; require caller-owned Compiler options for `reactCompilerPreset` | none |
| Plugin lacks exact Vite/bundler compatibility or authority | blocked | Return user decision need | none |
| Dev slowness lacks a comparable baseline or simpler cause audit | measure first | Check browser, resolver, barrels, plugins, and warmup evidence | none |
| Vite 8.1+ bundled-dev trial is authorized, pinned, and compatible | reversible experiment | Enable only for the measured large-module path | none |
| Bundled-dev plugin/feature incompatibility or neutral result | rollback | Restore unbundled dev | none |

## Actions and Prohibitions

For `chunk`, measure defaults before one reversible rule and preserve the active bundler's native config contract. Prohibit fake UI-framework boundaries, blanket vendor chunks, tiny first-screen splits, unanalyzable paths, Vite 7's removed `splitVendorChunkPlugin`, and Vite 8's unsupported object or deprecated function `manualChunks`. For `plugin`, prove the gap and compare built-in/current paths; prohibit installation without authority and require caller-supplied framework semantics before validating an adapter. Keep Vite core, framework-plugin major, and Compiler adoption separately reversible. For `dev-performance`, remove measurement confounders and inspect plugin/resolve work before an experimental bundled-dev trial; never present experimental behavior as a stable default.

## Stop or Roll Back

For `chunk`, stop only on missing path-specific owner/interaction/baseline and roll back on chunk/transfer/CSS/cache/interaction regression. For `plugin`, stop on missing gap/compatibility/authority/fallback and roll back on plugin dev/build/output regression. For `dev-performance`, stop on an unpinned or unsupported minor, missing baseline, third-party incompatibility, or absent rollback; roll back on startup/reload/HMR/correctness regression.

## Verify

For `chunk`, compare the same production interaction, graph, bytes, duplicates, CSS/modulepreload, cache, and trigger. For `plugin`, verify ordering, apply mode, dev/build, and output under the resolved Vite/bundler pair. For `dev-performance`, repeat the same cold start, full reload, and HMR interaction with browser/proxy conditions fixed, then verify plugin behavior and correctness.

## Return and Handoff

Generic chunk, plugin, and dev-performance work return with `next_reference: none`. Migration-owned or framework-owned work returns graph, diagnostics, and output evidence to the exact caller. Never reselect a caller-owned boundary, metric, or framework semantic.

Fact sources: [Vite 7 build options](https://v7.vite.dev/config/build-options), [Vite 8 build options](https://vite.dev/config/build-options), [Vite performance](https://vite.dev/guide/performance), [Vite 8 migration](https://vite.dev/guide/migration), [Vite 8.1 bundled dev](https://vite.dev/blog/announcing-vite8-1), and [`@vitejs/plugin-react` changelog](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react/CHANGELOG.md).
