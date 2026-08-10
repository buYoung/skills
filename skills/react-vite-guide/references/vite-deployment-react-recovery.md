# Vite Deployment and React Recovery Integration

## Read When

Read only when a reproduced Vite 7/8 stale or removed chunk requires React async recovery UI, user-work preservation, focus, or announcement behavior. Do not use for a base/cache problem without React UI work or for an ordinary React render failure.

## Collect Inputs

Collect `caller_skill`, resolved versions, deployment topology, `base`, asset retention, current-HTML cache policy, `vite:preloadError` reproduction with an already-open client, reload-loop guard, React failure/recovery owner, unsaved work, visible fallback/message, retry/reload control, focus target, announcement need, and rollback point.

## Decision Sequence and Table

1. Require deployment reproduction. 2. Fix base/cache ownership before UI. 3. Require the React recovery/work-preservation model. 4. Coordinate one bounded recovery. 5. Verify the actual topology and return.

| Observation | Selection | Action | Next skill |
|---|---|---|---|
| Base/cache/asset-retention evidence is absent | Vite owner first | Do not add React reload behavior | `vite-guide` |
| React failure owner or work-preservation policy is absent | React owner first | Do not finalize recovery UI | `react-guide` |
| Base mismatch explains failure | base correction first | Return topology evidence without a React workaround | `vite-guide` |
| Old chunks are retained/versioned | no recovery integration | Preserve deployment model and React state | return to caller |
| Removed chunk is reproduced and silent bounded recovery is safe | coordinated recovery | Pair current-HTML cache with one guarded preload-error recovery | return to caller |
| User-visible decision or unsaved work exists | explicit recovery UI | Preserve work, explain recovery, and require deliberate retry/reload | return to caller |
| Focus/announcement behavior is unresolved | accessibility owner | Preserve failure/recovery meaning | `react-guide` |
| Handler loops or loses work | rollback | Restore the last passing deployment/UI behavior | return to caller |

## Actions and Prohibitions

Vite owns base/cache/chunk availability; React owns visible state, work preservation, and accessibility. Do not use an Error Boundary reset as stale-chunk repair, add a global reload without reproduction/current HTML guarantee, move focus on every render, announce ambiguous status, or treat `vite preview` as deployment evidence.

## Verify

In the actual deployment topology, verify direct/refresh routes at `base`, cache headers, an already-open old client, one bounded recovery attempt, preserved or explicitly warned work, visible recovery state, keyboard/focus behavior, and announcement behavior when required.

## Return and Handoff

Return deployment reproduction, React recovery model, cache/reload coordination, work policy, accessibility result, and rollback evidence. Missing Vite evidence goes to `vite-guide`; missing React evidence goes to `react-guide`; otherwise return to the exact caller.

Fact sources: [Vite 7 static deployment](https://v7.vite.dev/guide/static-deploy), [Vite 8 static deployment](https://vite.dev/guide/static-deploy), [React Error Boundaries](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary), and [React DOM common components](https://react.dev/reference/react-dom/components/common).
