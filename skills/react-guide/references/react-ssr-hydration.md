# React SSR and Hydration

## Read When

Read for React 18/19 server rendering, Suspense streaming, server/client entry points, hydration mismatches, or initial data and external-store snapshots. Work within the existing host; framework-specific APIs, RSC/Server Functions implementation, and custom runtime construction are outside this guide.

## Establish the Rendering Contract

Inspect the exact `react`/`react-dom` versions, server export selected by the runtime/bundler, Node versus Web Streams support, rendered container/document, client entry, asset URLs, data loading, request lifetime, and error reporting. Check minor-specific exports and options before copying current documentation: the streaming APIs arrived in React 18, but current Node exports and newer React 19 features must not be assumed for every older minor. Prefer the Node API for a Node host. See the [React 18 upgrade guide](https://react.dev/blog/2022/03/08/react-18-upgrade-guide) and [server API overview](https://react.dev/reference/react-dom/server).

## Select Output and Streaming Behavior

| Host or requirement | API and behavior |
|---|---|
| Node writable response | `renderToPipeableStream` returns `pipe` and `abort`. Send the shell from `onShellReady`; Suspense content follows. |
| Host consuming Web Streams | Await `renderToReadableStream`; resolution means the shell is ready. Return the stream using the host's response API. |
| Complete output before delivery | Use `onAllReady` or await the readable stream's `allReady`; waiting removes progressive delivery. |
| Existing non-streaming response | `renderToString` returns immediately; it neither streams nor waits for suspended data, and may output a fallback. |
| Non-interactive HTML | `renderToStaticMarkup` cannot be hydrated. Keep it for output that does not need React interactivity. |
| React 19 static generation | `react-dom/static` prerender APIs wait for data; they are distinct from progressive request streaming. Do not adopt newer resume APIs without an exact version and task need. |

For Node streaming, put durable layout outside Suspense and choose useful fallback boundaries. Set headers/status before `pipe`. Supply the real client entry through `bootstrapScripts` or `bootstrapModules` as appropriate to the built output. See [renderToPipeableStream](https://react.dev/reference/react-dom/server/renderToPipeableStream).

For Web Streams, catch rejection before returning a response; use the stream's `allReady` only when complete output is required. Its `signal` option aborts rendering. A runtime having a global `ReadableStream` does not alone prove that the installed React server export and host adapter support this path. See [renderToReadableStream](https://react.dev/reference/react-dom/server/renderToReadableStream).

Non-streaming output can remain appropriate for a synchronous, preloaded tree. Do not replace it merely because streaming exists; explain the waiting/interactivity tradeoff when a change is needed. See [renderToString](https://react.dev/reference/react-dom/server/renderToString), [renderToStaticMarkup](https://react.dev/reference/react-dom/server/renderToStaticMarkup), and [static APIs](https://react.dev/reference/react-dom/static).

## Errors, HTTP Status, and Request Lifetime

On Node, `onShellError` handles failure before the shell is available; send the host's fallback response there. Use `onError` for diagnostics, including errors React can recover from. A failure inside a Suspense boundary can leave its fallback for a client retry; a client Error Boundary does not set the server's HTTP status. Once streaming starts, status and headers cannot be revised for later errors. Preserve this distinction when selecting a pre-shell error status. See [stream errors and status](https://react.dev/reference/react-dom/server/renderToPipeableStream#setting-the-status-code).

Connect render cancellation to the existing request deadline/disconnect lifecycle using `abort()` or the readable renderer's `signal`, and release request-local timers/listeners on completion. Aborting React rendering does not automatically cancel application data fetches; wire their own cancellation lifecycle too. If the connection remains usable, aborted pending boundaries may finish on the client; a disconnected client cannot receive that recovery. Investigate completion and abort independently for concurrent requests.

## Hydration and Initial Data

Use `hydrateRoot` for matching server-rendered content and `createRoot` for an empty client-rendered container. Hydrate the same container or document and component tree that produced the HTML. Server output and the first client render must match; avoid early `root.render`, nondeterministic dates/randomness, locale differences, invalid HTML nesting, and render-time `window` branches. Capture `onRecoverableError`; check the installed version before using newer root error callbacks. `suppressHydrationWarning` is a narrow escape hatch for unavoidable leaf differences, not a repair strategy. See [hydrateRoot](https://react.dev/reference/react-dom/client/hydrateRoot).

Pass the same `identifierPrefix` to the server renderer and `hydrateRoot` when `useId` prefixes are configured. Multiple roots need distinct prefixes per root, consistent across server and client; matching prefixes cannot compensate for a different component tree. Keep `useId` for ID relationships, not list keys. See [useId](https://react.dev/reference/react/useId).

Trace initial data from the request to the rendered props/store, serialized HTML payload, client bootstrap, and hydration. Use the same captured data throughout; initialize live updates afterward. Serialize only intended public data with the host's HTML-safe serializer; raw `JSON.stringify` embedded in a script is not safe for arbitrary strings containing `</script>`. Keep secrets out of the payload.

For external stores, `getServerSnapshot` runs on the server and during hydration. It must read the transferred initial snapshot, while `getSnapshot` represents live client data afterward. Keep the initial snapshot fixed even if live state changes before a delayed boundary hydrates. Snapshot references must remain stable until their observed data changes; see [state/data](react-state-data.md) and [useSyncExternalStore](https://react.dev/reference/react/useSyncExternalStore).

The hydration and snapshot contracts imply request isolation: construct mutable stores/data caches per request, rather than mutating a module-global user store. A client store may live for that client root's lifetime. Avoid sharing request data between concurrent users or roots. Browser-only imports must not execute on the server; use a client-only entry or deferred import where necessary. Browser preferences can be applied after hydration while keeping the initial output stable; see [Hooks/Effects](react-hooks-effects.md).

## Verify and Report

Check server render, first hydration, subsequent interactions, stable IDs, client store updates, and preserved drafts. Exercise overlapping requests with different initial data, live changes before hydration completes, shell failure, delayed boundary failure, and cancellation where relevant. Check actual response status and delivery timing when claiming streaming behavior.

Separate static/source checks, store-level execution, real React hydration, and host/deployment observations. Report what ran and what remains unverified. Use [async UI](react-async-ui.md) for fallbacks/retry and build-tool guidance for dev loaders, emitted client/server entry points, manifests, and asset serving.
