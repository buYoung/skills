# React 19 Arrival Migration

## Read When

Read to implement, explain, or validate React 19 migration. Reuse departure findings when available or reconstruct them from current source. Read component, Action, or Compiler guidance only when implicated.

## Collect Inputs

Collect or reconstruct [departure](react-18-to-19-migration.md) evidence, resolved React 19.x, modern JSX transform, removed-API/type/root call sites, warnings, and existing build/runtime results.

## Decision Sequence and Table

1. Inspect available departure and current-source evidence. 2. Inspect JSX, root, removed APIs, types, warnings, build, runtime in order. 3. Classify. 4. Fix authorized blockers. 5. Return arrival result.

| Observation | Selection | Action | Related guidance |
|---|---|---|---|
| Departure and arrival checks pass | fixed | Record arrival | none |
| Removed API/type/root warning | blocking | Fix if authorized; reverify locally | none |
| Item absent | not-applicable | Record inspected scope | none |
| Prior report absent | inspect current source | Reconstruct removed API, compatibility, and runtime evidence | none |
| Structural/public impact found | owner evidence | Preserve affected callers | [structure/public API](react-structure-public-api.md) |

## Actions and Prohibitions

Change only migration blockers. Do not adopt unrelated features, run style-only conversions, or create new test tooling.

## Uncertainty and Regressions

A missing departure report does not prevent migration work. Diagnose removed APIs, warnings, and build/runtime failures from current evidence. Defer an unresolved public break; revert destination changes that violate the intended migration contract.

## Verify

Verify JSX/root/types, removed API absence, warnings, existing build, and runtime. Failed checks return to the classified blocker.

## Result and Related Guidance

Report migration changes, unresolved blockers, and verified versus unverified checks. Use [structure/public API](react-structure-public-api.md) for public impact and [SSR and hydration](react-ssr-hydration.md) for `hydrateRoot`, streaming, initial data, and removed legacy server APIs.
