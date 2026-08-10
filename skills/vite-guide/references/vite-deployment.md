# Vite 7/8 Deployment Recovery

## Read When

Read for resolved Vite 7 or 8 subpath/base, cache headers, stale removed chunks, `vite:preloadError`, reload loops, or old-client recovery. Exclude chunk tuning and UI-framework recovery semantics.

## Collect Inputs

Receive the common Vite preflight record and exact Vite major/minor, then collect deployment topology, `base`, asset retention, HTML cache policy, direct/refresh behavior, stale-chunk reproduction with an open old client, current handler, unsaved work, and reload-loop guard.

## Decision Sequence and Table

1. Reproduce topology/failure. 2. Fix base first. 3. Decide whether reload recovery is necessary. 4. Change cache/reload together. 5. Verify and hand off user-visible needs.

| Observation | Selection | Action | Handoff |
|---|---|---|---|
| Base mismatch | base correction | Fix `base`/`BASE_URL` owner | none |
| Old chunks retained/versioned | no reload recovery | Preserve model | none |
| Old chunks removed/reproduced, no additional UI work | coordinated recovery | Pair preload-error handling with current-HTML cache | none |
| Old chunks removed, reproduced, and user-visible recovery is needed under React | integration handoff | Preserve topology/cache/reload evidence | `react-vite-guide` |
| Old chunks removed, reproduced, and another framework owns visible recovery | framework handoff | Preserve topology/cache/reload evidence | none |
| Loop/work policy undefined | blocked | Do not add global reload | none |
| Focus/announcement needed under React | integration handoff | Preserve failure/recovery evidence | `react-vite-guide` |
| Focus/announcement needed under another framework | framework handoff | Preserve failure/recovery evidence | none |

## Actions and Prohibitions

Protect unsaved work and bound reload attempts. Do not use Error Boundary reset as stale-chunk repair, add reload without reproduction/current HTML guarantee, change chunk strategy here, or use preview as deployment evidence.

## Stop or Roll Back

Stop on unresolved topology, missing reproduction, absent loop guard/current-HTML policy, unknown work preservation, or unsupported event behavior under the resolved version. Roll back handlers that loop or lose work silently.

## Verify

Verify direct/refresh routes at base, cache headers, already-open old client, one bounded recovery, and preserved or explicitly warned user work in the actual deployment topology.

## Return and Handoff

Return deployment reproduction/cache/reload evidence. For React 18/19 UI recovery, use `next_skill: react-vite-guide`; for another framework, return its framework-owner need without inventing UI semantics.

Fact sources: [Vite 7 static deployment](https://v7.vite.dev/guide/static-deploy) and [Vite 8 static deployment](https://vite.dev/guide/static-deploy).
