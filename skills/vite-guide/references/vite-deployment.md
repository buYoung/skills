# Vite 7/8 Deployment Recovery

## Read When

Read for resolved Vite 7 or 8 subpath/base, cache headers, stale removed chunks, `vite:preloadError`, reload loops, or old-client recovery. Use build guidance for chunk tuning and framework guidance for user-visible recovery semantics.

## Collect Inputs

Inspect the exact Vite version and collect deployment topology, `base`, asset retention, HTML cache policy, direct/refresh behavior, stale-chunk reproduction with an open old client, current handler, unsaved work, and reload-loop guard.

## Decision Sequence and Table

1. Reproduce topology/failure. 2. Fix base first. 3. Decide whether reload recovery is necessary. 4. Change cache/reload together. 5. Verify deployment and user-visible recovery together.

| Observation | Selection | Action | Related guidance |
|---|---|---|---|
| Base mismatch | base correction | Fix `base`/`BASE_URL` owner | none |
| Old chunks retained/versioned | no reload recovery | Preserve model | none |
| Old chunks removed/reproduced, no additional UI work | coordinated recovery | Pair preload-error handling with current-HTML cache | none |
| Old chunks removed, reproduced, and user-visible recovery is needed | recovery UI integration | Preserve topology/cache/reload evidence | framework guidance |
| Loop/work policy undefined | blocked | Do not add global reload | none |
| Focus/announcement behavior is needed | recovery UI integration | Preserve failure/recovery evidence | framework guidance |

## Actions and Prohibitions

Protect unsaved work and bound reload attempts. Do not use Error Boundary reset as stale-chunk repair, add reload without reproduction/current HTML guarantee, change chunk strategy here, or use preview as deployment evidence.

## Uncertainty and Regressions

Investigate unknown topology and missing recovery behavior. Do not add automatic reload until its loop guard, current-HTML path, and work-preservation behavior are understood. Repair existing handlers that silently lose work or loop, and distinguish local inspection from actual deployment evidence.

## Taking Responsibility for Preload Errors

`vite:preloadError` exposes the original import failure as `event.payload`. Calling `event.preventDefault()` suppresses Vite's rethrow; it does not repair the missing chunk. Call it only when this handler actually takes responsibility for recovery or explicit error presentation. A logging-only listener, rejected recovery attempt, or unsaved-work branch with no alternative feedback must leave the error observable. Preserve a visible path when bounded reload is exhausted. See [load-error handling](https://vite.dev/guide/build#load-error-handling).

Dispatching a `CustomEvent` alone does not prove that anyone handled it. Suppress the original error only after a recovery/UI handler explicitly accepts responsibility, or a bounded reload is actually selected. If that handler is absent, declines, or throws, keep the failure observable. Check the no-listener, unsaved-work, storage-failure, and exhausted-guard paths as well as successful recovery.

Coordinate current HTML cache policy with retained/versioned hashed assets and a recovery guard that survives reloads. Protect drafts before any reload and reset/rotate the guard only after confirmed successful boot. Verify SSR HTML and referenced client assets belong to the same release when applicable.

Define what confirms successful boot before wiring guard removal. Entry-module evaluation, registering the error handler, `DOMContentLoaded`, or `pageshow` alone does not prove the application and the failing lazy path recovered. Keep the attempt recorded across a fresh page context until an explicit application/recovery acknowledgement or a verified release change justifies clearing/rotating it. If another layer owns that acknowledgement, expose the integration contract and report the missing connection; do not simulate success inside bootstrap. Check a reload followed by the same failure before acknowledgement, and a later release after acknowledged recovery.

## Verify

Verify direct/refresh routes at base, cache headers, already-open old client, one bounded recovery, and preserved or explicitly warned user work in the actual deployment topology.

## Result and Related Guidance

Report deployment reproduction, caching, bounded recovery, and verification limits. Use framework guidance for visible recovery/focus/announcements and [SSR integration](vite-ssr.md) for built server loading, manifests, and client assets. Use an actual handoff only when the task imposes an ownership restriction.

Fact sources: [Vite 7 static deployment](https://v7.vite.dev/guide/static-deploy) and [Vite 8 static deployment](https://vite.dev/guide/static-deploy).
