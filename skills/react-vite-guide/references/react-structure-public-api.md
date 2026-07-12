# React Structure and Public API

## Read When

Read for component/module separation, composition/variants, feature folders, import direction, exports, consumers, or public compatibility. Exclude state, Effect, lazy, and version syntax decisions; hand those off.

## Collect Inputs

Collect change axes, UI meaning, callers, render/state/Effect owners, import graph, exports/external consumers, and props/ref/event/DOM/accessibility/state-reset contracts.

## Decision Sequence and Table

1. List candidate boundaries and consumer impact. 2. Hand off crossed state/Effect ownership before extraction. 3. Select the narrowest boundary. 4. Edit or record a finding. 5. Verify and return.

| Observation | Selection | Action | Handoff |
|---|---|---|---|
| Candidate crosses state/reset owner | defer | Preserve candidate; decide owner first | [state/data](react-state-data.md) |
| Candidate crosses lifecycle owner | defer | Preserve candidate; decide setup/cleanup first | [Hooks/Effects](react-hooks-effects.md) |
| One owner, no independent meaning | keep | Record no extraction | none |
| Named one-feature UI unit | local component | Extract beside caller | none |
| Stable repeated contract | shared component | Define minimal composition/props; classify locally | none |
| Independent domain/import direction | feature module | Create explicit boundary/export; classify locally | none |
| Natural wait unit with cost evidence | lazy module candidate | Preserve boundary evidence | [async UI](react-async-ui.md) |
| React 18 external ref/Context contract | stable/compatible public | Preserve behavior/adapter | [React 18 runtime](react-18-runtime-compatibility.md) |
| React 19 external ref/Context contract | stable/compatible public | Preserve behavior/adapter | [React 19 component APIs](react-19-component-apis.md) |
| External contract without version syntax change | stable public | Preserve behavior | none |
| Approved break absent | blocked breaking | Do not edit | none |

## Actions and Prohibitions

Update callers, imports, state position, lifecycle placement, and exports together. Classify props/ref/events, reset, DOM/a11y meaning, and import path separately. Do not split by line count, speculate on reuse, create cycles/broad barrels, or move owner code before handoff evidence returns.

## Stop or Roll Back

Stop for unknown consumers, unapproved break, missing owner evidence, or ambiguous import direction. Roll back when coupling grows, state resets, subscription lifecycle changes, or an import cycle appears.

## Verify

Verify all callers/consumers, types/runtime behavior, state preservation/reset, Effect setup/cleanup counts, import direction/cycles, bundle-visible imports, and DOM/a11y contract. Return to input collection on mismatch.

## Return and Handoff

Return boundary candidates, selected boundary, consumer compatibility classification, and verification. Allowed next leaves: [state/data](react-state-data.md), [Hooks/Effects](react-hooks-effects.md), [async UI](react-async-ui.md), [React 18 runtime](react-18-runtime-compatibility.md), or [React 19 component APIs](react-19-component-apis.md). A returning owner decision resumes this leaf once with new evidence.

Fact source: [Thinking in React](https://react.dev/learn/thinking-in-react).
