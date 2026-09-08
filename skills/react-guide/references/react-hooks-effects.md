# React Hooks and Effects

## Read When

Read for custom Hook extraction/non-extraction, duplicated lifecycle, unnecessary Effect, event/render relocation, subscription/timer/browser API, or a request Effect. Combine with state/data guidance for requests and version guidance for gated Effect APIs.

## Collect Inputs

Distinguish Hook extraction from Effect lifecycle work. For `hook-extraction`, collect call sites, cohesion, shared-state expectation, dependencies, and cleanup. For `effect-lifecycle`, collect external system, reactive reads, trigger/event origin, setup/cleanup, dependency suppression, and request signals. Do not require request evidence for Hook-only review.

## Decision Sequence and Table

1. Select the responsibility before its inputs. 2. For a remote-request Effect, inspect its data owner and lifetime. 3. Select extraction or relocation/synchronization. 4. Edit or report. 5. Run responsibility-specific verification and return.

| Observation | Selection | Action | Related guidance |
|---|---|---|---|
| One-line logic or JSX | no extraction | Keep local; return finding | none |
| Pure reusable calculation | plain function | Extract without Hook prefix | none |
| Reused cohesive stateful/external logic | custom Hook | Move API/dependencies/cleanup together | none |
| Shared-state expectation | shared owner | Do not create Hook | [state/data](react-state-data.md) |
| Derived value, owner unchanged | render derivation | Remove Effect/state copy | none |
| Derived value requires owner change | owner decision | Do not move state yet | [state/data](react-state-data.md) |
| User-event work, no visible async failure | event handler | Move to initiating handler | none |
| User-event work with visible async failure | event handler | Move work and preserve failure evidence | [async UI](react-async-ui.md) |
| Remote request/cache/retry/stale result | data-owner decision | Do not retain as generic Effect | [state/data](react-state-data.md) |
| Subscription/timer/browser/imperative API | external synchronization | Keep complete dependencies and cleanup | none |
| Different synchronization reasons | split Effects | Separate setup/cleanup pairs | none |
| React 19.2 Effect Event candidate | version gate | Preserve Effect evidence | [React 19 component APIs](react-19-component-apis.md) |

## Actions and Prohibitions

Name the external system, relocate non-Effect work, remove obsolete state, and keep setup/cleanup symmetric. Do not extract JSX/one-line duplication, hide state sharing in a Hook, call Hooks conditionally, suppress dependencies, or classify network requests as generic APIs.

## Uncertainty and Regressions

Missing dependencies, asymmetric cleanup, and absent stale-response protection are defects to investigate and repair. When intended request ownership or shared-state behavior is genuinely unresolved, defer that choice and continue diagnosis. Revert an extraction that unintentionally changes independent state or lifecycle behavior.

## Development Re-execution and Server Rendering

Effects synchronize after commit; they do not run during server rendering. A root Strict Mode development check performs an extra setup → cleanup → setup cycle to expose missing cleanup. It is not evidence that production always runs an Effect twice. Current React also distinguishes Strict Mode on only a subtree from root-level initial Effect re-execution; check the installed version and boundary placement. Preserve cleanup and complete dependencies instead of adding a run-once ref to hide the probe. See [Strict Mode](https://react.dev/reference/react/StrictMode).

Browser APIs can be used in client Effects or event handlers, but a module-level browser access still executes during an SSR import. Keep the server and first client render deterministic; defer browser-only differences until after hydration using [SSR and hydration](react-ssr-hydration.md).

## Verify

For `hook-extraction`, verify call sites, independent state, dependencies, cleanup, and returned API. For `effect-lifecycle`, verify setup/cleanup cycles, subscriptions, event timing, and, for requests, abort/stale ordering, retry, and competing owners.

## Result and Related Guidance

Explain the extraction or synchronization decision and lifecycle evidence. Read [state/data](react-state-data.md) for request/cache/cancellation behavior, [component APIs](react-19-component-apis.md) for Effect Events, and [SSR and hydration](react-ssr-hydration.md) for server execution and initial browser output.

Fact sources: [custom Hooks](https://react.dev/learn/reusing-logic-with-custom-hooks) and [Effects](https://react.dev/learn/you-might-not-need-an-effect).
