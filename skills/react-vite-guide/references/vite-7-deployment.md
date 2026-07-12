# Vite 7 Deployment Recovery

## Read When

Read for resolved Vite 7 subpath/base, cache headers, stale removed chunks, `vite:preloadError`, reload loops, or old-client recovery. Exclude chunk tuning and React boundary semantics.

## Collect Inputs

Receive the common Vite preflight record, then collect deployment topology, `base`, asset retention, HTML cache policy, direct/refresh behavior, stale-chunk reproduction with an open old client, current handler, unsaved work, and reload-loop guard.

## Decision Sequence and Table

1. Reproduce topology/failure. 2. Fix base first. 3. Decide whether reload recovery is necessary. 4. Change cache/reload together. 5. Verify and hand off user-visible needs.

| Observation | Selection | Action | Handoff |
|---|---|---|---|
| Base mismatch | base correction | Fix `base`/`BASE_URL` owner | none |
| Old chunks retained/versioned | no reload recovery | Preserve model | none |
| Old chunks removed/reproduced, no additional UI work | coordinated recovery | Pair preload-error handling with current-HTML cache | none |
| Old chunks removed, reproduced, and user-visible recovery needed | coordinated recovery | Pair preload-error handling with current-HTML cache | [async UI](react-async-ui.md) |
| Loop/work policy undefined | blocked | Do not add global reload | none |
| Focus/announcement needed | UI handoff | Preserve failure/recovery evidence | [accessibility](react-accessibility.md) |

## Actions and Prohibitions

Protect unsaved work and bound reload attempts. Do not use Error Boundary reset as stale-chunk repair, add reload without reproduction/current HTML guarantee, or use preview as deployment evidence.

## Stop or Roll Back

Stop on unresolved topology, missing reproduction, absent loop guard/current-HTML policy, or unknown work preservation. Roll back handlers that loop or lose work silently.

## Verify

Verify direct/refresh routes at base, cache headers, already-open old client, one bounded recovery, and preserved or explicitly warned user work.

## Return and Handoff

Return deployment reproduction/cache/reload evidence. User-visible fallback/recovery goes to [async UI](react-async-ui.md); focus/announcement evidence goes to [accessibility](react-accessibility.md).

Fact source: [Vite static deployment](https://vite.dev/guide/static-deploy.html).
