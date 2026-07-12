# React 19 Arrival Migration

## Read When

Read only to validate React 19 arrival with normalized evidence from the React 18 departure leaf. Do not auto-load component APIs, Actions, or Compiler.

## Collect Inputs

Collect [departure](react-18-to-19-migration.md) evidence, resolved React 19.x, modern JSX transform, removed-API/type/root call sites, warnings, and existing build/runtime results.

## Decision Sequence and Table

1. Validate departure handoff. 2. Inspect JSX, root, removed APIs, types, warnings, build, runtime in order. 3. Classify. 4. Fix authorized blockers. 5. Return arrival result.

| Observation | Selection | Action | Handoff |
|---|---|---|---|
| Departure and arrival checks pass | fixed | Record arrival | none |
| Removed API/type/root warning | blocking | Fix if authorized; reverify locally | none |
| Item absent | not-applicable | Record inspected scope | none |
| Departure/evidence absent | unconfirmed | Do not declare arrival; return blocked evidence | none |
| Structural/public impact found | owner evidence | Preserve affected callers | [structure/public API](react-structure-public-api.md) |

## Actions and Prohibitions

Change only migration blockers. Do not adopt unrelated features, run style-only conversions, or create new test tooling.

## Stop or Roll Back

Stop on missing departure evidence, blocking warning, build/runtime failure, or unresolved public break. Roll back destination edits that invalidate departure behavior without a migration decision.

## Verify

Verify JSX/root/types, removed API absence, warnings, existing build, and runtime. Failed checks return to the classified blocker.

## Return and Handoff

Return `fixed|blocking|not-applicable|unconfirmed` items and verification. Only named structural impact goes to [structure/public API](react-structure-public-api.md) or another exact owner leaf.
