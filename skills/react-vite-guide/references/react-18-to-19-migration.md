# React 18 to 19 Departure Migration

## Read When

Read only for an explicitly authorized React 18→19 migration departure audit. Do not use for ordinary React 18 work or React 19 arrival changes.

## Collect Inputs

Collect resolved React 18 minor, 18.3 warnings when available, root APIs, deprecated/removed API call sites, JSX transform, types, string refs, legacy context, function `propTypes/defaultProps`, cleanup findings, public consumers, and existing build/runtime evidence.

## Decision Sequence and Table

1. Inventory each departure item. 2. Classify before editing. 3. Fix authorized blockers under React 18. 4. Verify. 5. Handoff only when no blocker remains.

| Observation | Selection | Action | Handoff |
|---|---|---|---|
| Verified compatible item | ready | Preserve evidence | none |
| 18.3 warning/known arrival blocker | must-fix | Fix if authorized; reverify locally | none |
| Public consumer break | blocked public | Do not decide here | [structure/public API](react-structure-public-api.md) |
| Evidence unavailable | unconfirmed | Do not declare ready | none |
| Warning/build/runtime failure remains | blocking | Stop migration | none |

## Actions and Prohibitions

Produce an itemized `ready|must-fix-before-arrival|unconfirmed|blocking` inventory. Do not add React 19 component, Action, Promise, or Compiler features during departure cleanup.

## Stop or Roll Back

Stop for unresolved blockers, failed verification, unsupported consumers, or missing authorization. Roll back a cleanup that breaks React 18 behavior.

## Verify

Run existing build/runtime checks and confirm warnings, root/JSX/types, cleanup, and affected consumers. Failed items return to classification.

## Return and Handoff

On pass, send normalized versions, inventory, call sites, warnings, and verification to [React 19 migration](react-19-migration.md). Otherwise `next_reference: none`; public-break evidence may go to [structure/public API](react-structure-public-api.md).

Fact source: [React 19 upgrade guide](https://react.dev/blog/2024/04/25/react-19-upgrade-guide).
