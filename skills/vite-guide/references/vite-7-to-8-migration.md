# Vite 7 to 8 Migration

## Read When

Read only for an explicitly authorized Vite 7→8 migration. Do not use for ordinary Vite 8 work, a Vite 6 source, or framework-owned Vite dependency upgrades.

## Collect Inputs

Collect resolved Vite 7 source and Vite 8 target, common validated Node preflight evidence, package-manager/lockfile ownership, direct versus staged migration tolerance, browser support contract, optional UI-framework identity, and existing dev/build/preview/deployment evidence. Inventory `rolldown-vite`, `esbuild`/`optimizeDeps.esbuildOptions`, `rollupOptions`, minifiers, CommonJS resolution, non-ESM outputs, JS API consumers, plugin hooks/module types, custom transforms, and every plugin's exact Vite/Rolldown support.

## Decision Sequence and Table

1. Build a `pass|migrate|compatibility-debt|blocking|not-applicable` inventory. 2. Choose direct or staged arrival before changing dependencies. 3. Isolate the Rolldown change for complex builds. 4. Fix one blocker at a time. 5. Verify arrival, then hand off only remaining owners.

| Observation | Selection | Action | Handoff |
|---|---|---|---|
| Validated Node preflight absent/blocked | blocking | Stop before dependency/config edits | none |
| Default build with compatible plugins and no custom esbuild/Rollup behavior | direct migration | Upgrade Vite, then verify the same paths | none |
| Complex build, custom transforms/plugins, or output-sensitive config | staged migration | Trial Vite 7 via `rolldown-vite`, isolate differences, then move to Vite 8 | none |
| Default browser target no longer covers consumers | blocking contract | Set an explicit supported target or stop for product decision | none |
| Compatibility layer converts an old option and output passes | compatibility debt | Record deprecation; migrate to native Oxc/Rolldown key only within authority | none |
| Unsupported esbuild transform/minify feature or Rolldown output/hook | blocking | Select a documented replacement or stop | none |
| CJS default import, main-field, external `require`, UMD/IIFE, or JS API error shape is used | semantic audit | Verify the exact consumer before declaring arrival | none |
| Vite 8 object `manualChunks` or deprecated function form remains | native splitting migration | Replace evidenced need with Rolldown `codeSplitting`; remeasure output | [build/plugins](vite-build-plugins.md) |
| UI-framework plugin major/config is separately implicated | integration handoff | Keep Vite core arrival reversible; preserve exact framework/plugin/config evidence | `react-vite-guide` when React |
| Entry/env/asset/diagnostics remains after arrival | owner handoff | Preserve version and arrival evidence | [client runtime](vite-client-runtime.md) |
| Deployment remains after arrival | owner handoff | Preserve topology and arrival evidence | [deployment](vite-deployment.md) |

## Actions and Prohibitions

Keep Vite core arrival, bundler isolation, and any UI-framework plugin major as separately reversible stages. Prefer Vite 8 native `oxc`, `optimizeDeps.rolldownOptions`, `build.rolldownOptions`, and `worker.rolldownOptions` contracts when authorized; do not mistake automatic conversion for long-term config ownership. Do not add `esbuild` merely to silence a warning, preserve `legacy.inconsistentCjsInterop` as a permanent fix, combine unrelated redesign, claim Rolldown performance without the same-condition comparison, or upgrade a framework plugin incidentally.

## Stop or Roll Back

Stop on unsupported Node/browser contract, incompatible plugin or framework owner, unverified CJS/output semantics, missing dependency authority, unsupported transform/hook/output, or failed build/runtime. In a staged path, restore the last passing dependency/config stage before investigating the isolated difference.

## Verify

Run the existing install/dependency, dev, production build, and applicable preview/deployment paths. Compare entry/HMR, dependency optimization, dynamic imports/chunks, JS and CSS output/minification, CJS imports, workers/library formats when present, plugin hooks, source maps, and framework-plugin smoke behavior. Specialized framework compiler/runtime evidence remains an integration handoff. Do not declare Vite 8 arrival from a successful config load alone.

## Return and Handoff

Return the migration path, itemized inventory, exact versions, dependency/config stages, verification, rollback point, and compatibility debt. After arrival, route only unresolved Vite owner work to [client runtime](vite-client-runtime.md), [build/plugins](vite-build-plugins.md), or [deployment](vite-deployment.md). A React plugin seam uses `next_skill: react-vite-guide`; another framework returns its integration-owner need.

Fact sources: [Vite 8 announcement](https://vite.dev/blog/announcing-vite8) and [Vite 8 migration](https://vite.dev/guide/migration).
