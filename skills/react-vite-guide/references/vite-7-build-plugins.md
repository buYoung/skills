# Vite 7 Build and Plugins

## Read When

Read for resolved Vite 7 dynamic import/chunk/import graph, CSS/modulepreload, `import.meta.glob`, Rollup `manualChunks`, or plugin capability. Exclude React boundary selection and general performance ownership.

## Collect Inputs

First set `responsibility` to `chunk` or `plugin`; receive the common Vite preflight record. For `chunk`, collect production bundle, import/module owner, fixed interaction, cache/deploy requirement, rollback point, optional async-boundary evidence, and optional performance baseline. For `plugin`, collect the capability gap, existing chain, Vite 7 compatibility, maintenance/config cost, fallback/rollback, and authority. Do not require chunk evidence for plugin work or plugin evidence for chunk work.

## Decision Sequence and Table

1. Select `chunk` or `plugin`. 2. For chunk only, classify `react-lazy-boundary` or `generic-dynamic-import`. 3. Compare current/built-in behavior. 4. Select the minimum action. 5. Run only responsibility-specific verification.

| Observation | Selection | Action | Handoff |
|---|---|---|---|
| React lazy path lacks boundary | blocked | Do not change chunks | [async UI](react-async-ui.md) |
| React lazy path lacks baseline | blocked | Do not change chunks | [render performance](react-render-performance.md) |
| Generic path lacks module owner/interaction/baseline | blocked | Do not invent React boundary | none |
| React chunk output completes | return result | Preserve measured output | return_to_caller |
| Generic default output meets goal | retain defaults | No manual chunk | none |
| Generic measured cache/initial/shared-dependency problem | minimal `manualChunks` | Change evidenced Rollup boundary | none |
| React chunk regression | rollback | Restore config/boundary | return_to_caller |
| Generic chunk regression | rollback | Restore config/boundary | none |
| Built-in/current config solves plugin gap | no/new plugin unnecessary | Use existing capability | none |
| Existing compatible plugin solves gap | configure existing | Minimum config edit | none |
| New plugin lacks authority/evidence | blocked | Return user decision need | none |

## Actions and Prohibitions

For `chunk`, measure defaults before one reversible rule; prohibit fake React boundaries, blanket vendor chunks, tiny first-screen splits, unanalyzable paths, and removed `splitVendorChunkPlugin`. For `plugin`, prove the gap and compare built-in/current paths; prohibit installation without authority.

## Stop or Roll Back

For `chunk`, stop only on missing path-specific owner/interaction/baseline and roll back on chunk/transfer/CSS/cache/interaction regression. For `plugin`, stop only on missing gap/compatibility/authority/fallback and roll back on plugin dev/build/output regression.

## Verify

For `chunk`, compare the same production interaction, graph, bytes, duplicates, CSS/modulepreload, cache, and trigger. For `plugin`, verify ordering, apply mode, dev/build, and output.

## Return and Handoff

Generic chunk and plugin work return with `next_reference: none`. React lazy output uses `return_to_caller`, which the decision record must resolve to the exact caller path received in handoff evidence: [render performance](react-render-performance.md) or [async UI](react-async-ui.md). Never reselect their boundary or metric.

Fact source: [Vite build options](https://vite.dev/config/build-options).
