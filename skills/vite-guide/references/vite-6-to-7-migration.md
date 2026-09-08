# Vite 6 to 7 Migration

## Read When

Read only for an explicitly authorized Vite 6→7 migration. Do not use for ordinary Vite 7 tasks or propose another major.

## Collect Inputs

Collect resolved Vite 6 source, target authorization, the target package Node engine and current runtime evidence, Sass legacy API, removed `splitVendorChunkPlugin`, `build.target`, `transformIndexHtml`, plugin compatibility, entry/env/build/deploy impacts, and existing dev/build/preview/deployment evidence.

## Decision Sequence and Table

1. Build pass/fail/not-applicable inventory. 2. Apply Node support predicate. 3. Fix blockers one at a time. 4. Run existing verification. 5. Report arrival and unresolved findings.

| Item | Selection | Action | Related guidance |
|---|---|---|---|
| Target runtime satisfies the actual package contract | pass | Preserve exact evidence | none |
| Target-runtime evidence absent/unsupported | investigate | Resolve metadata; defer only unsupported execution or dependent choices | none |
| Removed/deprecated config/API | fail/not-applicable | Migrate authorized blocker; reverify locally | none |
| Plugin compatibility unknown/fails | investigate | Inspect peer contracts, source, and supported replacements | none |
| Entry/env remains after arrival | related work | Preserve evidence | [client runtime](vite-client-runtime.md) |
| Chunk/plugin remains after arrival | related work | Preserve evidence | [build/plugins](vite-build-plugins.md) |
| Deployment remains after arrival | related work | Preserve evidence | [deployment](vite-deployment.md) |

## Actions and Prohibitions

Fix Node, removed APIs, target/Sass/hooks/plugins in order. Do not mix unrelated redesign, hide removed APIs, or propose Vite 8.

## Uncertainty and Regressions

Investigate incompatible plugins, unconfirmed items, and failed builds. Defer unsupported runtime execution and unresolved consumer choices; do not declare arrival while required checks remain unconfirmed. Restore a prior working step if a proposed migration change regresses behavior.

## Verify

Run existing dev/build and applicable preview/deployment checks. Declare Vite 7 arrival only when all blocking inventory items and required commands pass.

## Result and Related Guidance

Report the itemized migration evidence, exact target runtime contract, and unverified checks. Use [client runtime](vite-client-runtime.md), [build/plugins](vite-build-plugins.md), [deployment](vite-deployment.md), or [SSR integration](vite-ssr.md) during the migration as needed. No preflight or prior-stage report is required.

Fact source: [Vite 7 migration guide](https://v7.vite.dev/guide/migration).
