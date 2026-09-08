# Vite 7 to 8 Migration

## Read When

Read only for an explicitly authorized Vite 7→8 migration. Do not use for ordinary Vite 8 work, a Vite 6 source, or framework-owned Vite dependency upgrades.

## Collect Inputs

Collect resolved Vite 7 source and Vite 8 target, the target package Node engine and current runtime evidence, package-manager/lockfile ownership, direct versus staged migration tolerance, browser support contract, optional UI-framework identity, and existing dev/build/preview/deployment evidence. Inventory `rolldown-vite`, `esbuild`/`optimizeDeps.esbuildOptions`, `rollupOptions`, minifiers, CommonJS resolution, non-ESM outputs, JS API consumers, plugin hooks/module types, custom transforms, and every plugin's exact Vite/Rolldown support.

## Decision Sequence and Table

1. Build a `pass|migrate|compatibility-debt|blocking|not-applicable` inventory. 2. Choose direct or staged arrival before changing dependencies. 3. Isolate the Rolldown change for complex builds. 4. Fix one blocker at a time. 5. Verify arrival and report remaining evidence gaps.

| Observation | Selection | Action | Related guidance |
|---|---|---|---|
| Node evidence absent/unsupported | investigate | Read target package metadata; defer only unsupported execution or dependent choices | none |
| Default build with compatible plugins and no custom esbuild/Rollup behavior | direct migration | Upgrade Vite, then verify the same paths | none |
| Complex build, custom transforms/plugins, or output-sensitive config | staged migration | Consider a temporary Vite 7 `rolldown-vite` trial when useful and still compatible; existing source/output evidence may be sufficient for direct migration | none |
| Default browser target no longer covers consumers | blocking contract | Set an explicit supported target or stop for product decision | none |
| Compatibility layer converts an old option and output passes | compatibility debt | Record deprecation; migrate to native Oxc/Rolldown key only within authority | none |
| Unsupported esbuild transform/minify feature or Rolldown output/hook | blocking | Select a documented replacement or stop | none |
| CJS default import, main-field, external `require`, UMD/IIFE, or JS API error shape is used | semantic audit | Verify the exact consumer before declaring arrival | none |
| Vite 8 object `manualChunks` or deprecated function form remains | native splitting migration | Replace evidenced need with Rolldown `codeSplitting`; remeasure output | [build/plugins](vite-build-plugins.md) |
| UI-framework plugin major/config is separately implicated | plugin integration | Keep Vite core arrival reversible; preserve exact framework/plugin/config evidence | [build/plugins](vite-build-plugins.md) |
| Entry/env/asset/diagnostics remains after arrival | related work | Preserve version and arrival evidence | [client runtime](vite-client-runtime.md) |
| Deployment remains after arrival | related work | Preserve topology and arrival evidence | [deployment](vite-deployment.md) |

## Actions and Prohibitions

Keep Vite core arrival, bundler isolation, and any UI-framework plugin major as separately reversible stages. Prefer Vite 8 native `oxc`, `optimizeDeps.rolldownOptions`, `build.rolldownOptions`, and `worker.rolldownOptions` contracts when authorized; do not mistake automatic conversion for long-term config ownership. Do not add `esbuild` merely to silence a warning, preserve `legacy.inconsistentCjsInterop` as a permanent fix, combine unrelated redesign, claim Rolldown performance without the same-condition comparison, or upgrade a framework plugin incidentally.

## Uncertainty and Regressions

Investigate unsupported transforms/hooks, CJS/output differences, incompatible plugins, and failed checks. Defer execution on an unsupported Node runtime and choices that need an unresolved browser or framework contract. Do not declare arrival from unverified semantics; repair the isolated difference or restore the last working dependency/config step.

## Removed APIs and SSR Audit

Check URL-based `import.meta.hot.accept` usage: Vite 8 removed that deprecated form; use a module id. Audit plugins for unsupported `shouldTransformCachedModule`, `resolveImportMeta`, `renderDynamicImport`, and `resolveFileUrl` hooks and select supported replacements for their actual purpose. Do not describe the entire HMR API as removed. The separate `handleHotUpdate` → `hotUpdate` transition is listed as a future migration, not a removed hook in Vite 8; check the target version's [HMR migration status](https://vite.dev/changes/hotupdate-hook).

For SSR, inspect both build entries, production imports, manifest consumers, externalized `require` semantics, conditional exports, and target runtime. Preserve a working `ssrLoadModule` integration; changing bundlers does not require switching to Environment API. Use [SSR integration](vite-ssr.md) for the full path.

## Verify

Run the existing install/dependency, dev, production build, and applicable preview/deployment paths. Compare entry/HMR, dependency optimization, dynamic imports/chunks, JS and CSS output/minification, CJS imports, workers/library formats when present, plugin hooks, source maps, and framework-plugin smoke behavior. Establish specialized framework Compiler/runtime semantics from current configuration and framework guidance before adapter validation. Do not declare Vite 8 arrival from a successful config load alone.

## Result and Related Guidance

Report the chosen migration path, inventory, exact versions, reversible dependency/config changes, verification, and compatibility debt. Read [client runtime](vite-client-runtime.md), [build/plugins](vite-build-plugins.md), [deployment](vite-deployment.md), or [SSR integration](vite-ssr.md) when the migration crosses those topics. Reconstruct evidence from current source when earlier migration reports are absent.

Fact sources: [Vite 8 announcement](https://vite.dev/blog/announcing-vite8) and [Vite 8 migration](https://vite.dev/guide/migration).
