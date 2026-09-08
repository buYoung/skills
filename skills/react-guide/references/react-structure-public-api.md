# React Structure and Public API

## Read When

Read for component/module separation, composition/variants, feature folders, import direction, exports, consumers, or public compatibility. Read state, Effect, async, or compatibility guidance when the boundary affects those behaviors.

## Collect Inputs

Collect change axes, UI meaning, callers, render/state/Effect owners, import graph, exports/external consumers, and props/ref/event/DOM/accessibility/state-reset contracts.

## Decision Sequence and Table

1. List candidate boundaries and consumer impact. 2. Resolve affected state/Effect ownership using the related guidance. 3. Select the narrowest boundary. 4. Edit or record a finding. 5. Verify and return.

| Observation | Selection | Action | Related guidance |
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

Update callers, imports, state position, lifecycle placement, and exports together. Classify props/ref/events, reset, DOM/a11y meaning, and import path separately. Do not split by line count, speculate on reuse, create cycles/broad barrels, or move state/lifecycle code without understanding its behavior.

## Uncertainty and Regressions

Investigate unknown consumers and import direction before changing their contracts. Defer a breaking compatibility choice until its intended behavior is clear; continue independent work. Repair unintended resets, lifecycle changes, or cycles, and revert a proposed extraction if it caused them.

## Component Identity and State Preservation

React associates state with a component type and position in the rendered tree; keys refine identity among siblings. Keep component definitions at module scope. A nested definition creates a new type on each parent render and can remount a child, losing drafts, focus, and subscriptions. Stable list keys come from data identity, not array position, random values, or `useId`. A changed key intentionally resets a subtree; use it only when reset is the desired behavior.

Check conditional branches, wrapper changes, and temporary loading returns when a refactor loses state. Keeping the same JSX text does not guarantee the same rendered position. See [preserving and resetting state](https://react.dev/learn/preserving-and-resetting-state).

## Verify

Verify all callers/consumers, types/runtime behavior, state preservation/reset, Effect setup/cleanup counts, import direction/cycles, bundle-visible imports, and DOM/a11y contract. Return to input collection on mismatch.

## Result and Related Guidance

Report the selected boundary, consumer impact, and verification relevant to the request. Use [state/data](react-state-data.md), [Hooks/Effects](react-hooks-effects.md), [async UI](react-async-ui.md), or version compatibility guidance as needed.

Fact source: [Thinking in React](https://react.dev/learn/thinking-in-react).
