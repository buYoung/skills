# React Hooks and Effects

## Read When

Read for custom Hook extraction/non-extraction, duplicated lifecycle, unnecessary Effect, event/render relocation, subscription/timer/browser API, or a request Effect. Exclude request ownership and version-gated Effect APIs.

## Collect Inputs

First set `responsibility` to `hook-extraction` or `effect-lifecycle`. For `hook-extraction`, collect call sites, cohesion, shared-state expectation, dependencies, cleanup, and caller. For `effect-lifecycle`, collect external system, reactive reads, trigger/event origin, setup/cleanup, dependency suppression, request signals, and caller. Do not require request evidence for Hook-only review.

## Decision Sequence and Table

1. Select the responsibility before its inputs. 2. For a remote-request Effect only, obtain data-owner evidence. 3. Select extraction or relocation/synchronization. 4. Edit or report. 5. Run responsibility-specific verification and return.

| Observation | Selection | Action | Handoff |
|---|---|---|---|
| One-line logic or JSX | no extraction | Keep local; return finding | none |
| Pure reusable calculation | plain function | Extract without Hook prefix | none |
| Reused cohesive stateful/external logic | custom Hook | Move API/dependencies/cleanup together | none |
| Shared-state expectation | shared owner | Do not create Hook | [state/data](react-state-data.md) |
| Derived value, owner unchanged | render derivation | Remove Effect/state copy | none |
| Derived value requires owner change | owner handoff | Do not move state yet | [state/data](react-state-data.md) |
| User-event work, no visible async failure | event handler | Move to initiating handler | none |
| User-event work with visible async failure | event handler | Move work and preserve failure evidence | [async UI](react-async-ui.md) |
| Remote request/cache/retry/stale result | data-owner handoff | Do not retain as generic Effect | [state/data](react-state-data.md) |
| Subscription/timer/browser/imperative API | external synchronization | Keep complete dependencies and cleanup | none |
| Different synchronization reasons | split Effects | Separate setup/cleanup pairs | none |
| React 19.2 Effect Event candidate | version gate | Preserve Effect evidence | [React 19 component APIs](react-19-component-apis.md) |

## Actions and Prohibitions

Name the external system, relocate non-Effect work, remove obsolete state, and keep setup/cleanup symmetric. Do not extract JSX/one-line duplication, hide state sharing in a Hook, call Hooks conditionally, suppress dependencies, or classify network requests as generic APIs.

## Stop or Roll Back

For `hook-extraction`, stop only on unresolved shared-state owner or extraction cleanup/dependency ambiguity. For `effect-lifecycle`, stop on unresolved external/request owner, asymmetric cleanup, missing reactive dependencies, or—only for a remote request—absent abort/stale-response contract. Roll back extraction when call sites lose independent state or lifecycle behavior changes.

## Verify

For `hook-extraction`, verify call sites, independent state, dependencies, cleanup, and returned API. For `effect-lifecycle`, verify setup/cleanup cycles, subscriptions, event timing, and only after request handoff, abort/stale ordering, retry, and competing owners.

## Return and Handoff

Return extraction/Effect decision and lifecycle evidence. A request Effect sends initiator/cache/cancel/retry evidence to [state/data](react-state-data.md); returned owner evidence resumes this leaf. If invoked by structure work, return setup/cleanup ownership to [structure/public API](react-structure-public-api.md).

Fact sources: [custom Hooks](https://react.dev/learn/reusing-logic-with-custom-hooks) and [Effects](https://react.dev/learn/you-might-not-need-an-effect).
