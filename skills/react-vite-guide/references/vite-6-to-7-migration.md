# Vite 6 to 7 Migration

## Read When

Read only for an explicitly authorized Vite 6→7 migration. Do not use for ordinary Vite 7 tasks or propose another major.

## Collect Inputs

Collect resolved Vite 6 source, target authorization, the common validated target-runtime preflight evidence, Sass legacy API, removed `splitVendorChunkPlugin`, `build.target`, `transformIndexHtml`, plugin compatibility, entry/env/build/deploy impacts, and existing dev/build/preview/deployment evidence.

## Decision Sequence and Table

1. Build pass/fail/not-applicable inventory. 2. Apply Node support predicate. 3. Fix blockers one at a time. 4. Run existing verification. 5. Declare arrival or hand off only remaining owners.

| Item | Selection | Action | Handoff |
|---|---|---|---|
| Validated target-runtime preflight present | pass | Preserve exact evidence | none |
| Target-runtime evidence absent/blocked | blocking | Stop before config edits | none |
| Removed/deprecated config/API | fail/not-applicable | Migrate authorized blocker; reverify locally | none |
| Plugin compatibility unknown/fails | blocking | Do not continue | none |
| Entry/env remains after arrival | owner handoff | Preserve evidence | [client runtime](vite-7-client-runtime.md) |
| Chunk/plugin remains after arrival | owner handoff | Preserve evidence | [build/plugins](vite-7-build-plugins.md) |
| Deployment remains after arrival | owner handoff | Preserve evidence | [deployment](vite-7-deployment.md) |

## Actions and Prohibitions

Fix Node, removed APIs, target/Sass/hooks/plugins in order. Do not mix unrelated redesign, hide removed APIs, or propose Vite 8.

## Stop or Roll Back

Stop on unsupported Node, incompatible plugin, unconfirmed blocking item, or failed build/runtime. Roll back the last migration step before continuing.

## Verify

Run existing dev/build and applicable preview/deployment checks. Declare Vite 7 arrival only when all blocking inventory items and required commands pass.

## Return and Handoff

Return itemized arrival evidence. After pass, route only unresolved owner work to [client runtime](vite-7-client-runtime.md), [build/plugins](vite-7-build-plugins.md), or [deployment](vite-7-deployment.md); otherwise `next_reference: none`.

Fact source: [Vite migration guide](https://vite.dev/guide/migration.html).
