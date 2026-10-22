# Provider and MCP integration recipes

Read this when the package registers a model provider or an MCP server, or calls classifier models. These APIs run inside ordinary Pi extensions and follow their loading, trust, dependency, and lifecycle contracts ([extensions](extensions.md), [packaging](packaging.md), [operations](operations.md)). Endpoint URLs, model IDs, authentication methods, and protocol behavior must come from the actual service; the example values below are not live configurations.

## Contents

- [Model providers](#model-providers)
- [MCP servers](#mcp-servers)

## Model providers

### Choose a registration form

- Use `models.json` when the request only adds static models behind an already supported API and needs no distributable extension.
- For a package-owned provider, register it in the extension factory so that it exists when Pi selects a model at startup.
- Use a `ProviderConfig` when the endpoint speaks a supported protocol and the package does not own authentication, discovery, filtering, or streaming. For a new integration that owns any of those, prefer a complete `Provider`.

### Register a compatible endpoint

```ts
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  pi.registerProvider("acme", {
    baseUrl: "https://api.example.com/v1",
    apiKey: "$ACME_API_KEY",
    api: "openai-completions",
    models: [{
      id: "replace-with-model-id",
      name: "Acme Model",
      reasoning: false,
      input: ["text"],
      cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
      contextWindow: 32768,
      maxTokens: 4096,
    }],
  });
}
```

Replace the endpoint, ID, context and output limits, modalities, reasoning support, and per-million-token costs with verified service values. The zeros are placeholders, not a claim that the model is free. Use compatibility flags only for confirmed protocol differences.

`registerProvider(name, ProviderConfig)` supports:

| Field | Purpose |
|---|---|
| `name` | Optional display name |
| `baseUrl`, `headers` | Endpoint and additional request headers |
| `apiKey` | Literal, `$ENV`/`${ENV}` interpolation, or leading `!command` resolver |
| `api` | Provider-level API type; models can override it |
| `authHeader` | Adds a Bearer authorization header for the resolved key |
| `models` | Provider model list; supplying it replaces the existing chat, image, and classifier models |
| `refreshModels(ctx)` | Returns updated model definitions asynchronously |
| `streamSimple` | Custom streaming adapter for when built-in protocols do not fit |
| `images`, `classifiers` | Operation implementations keyed by API |
| `oauth` | Legacy login, refresh, and access-token resolution contract |

- Overriding only an existing provider's endpoint or headers keeps its models. Supplying `models` replaces them.
- `unregisterProvider(name)` removes the dynamic registration and restores any built-in behavior it replaced.
- A chat model has `id`, `name`, `input`, `cost`, `reasoning`, `contextWindow`, and `maxTokens`; an omitted `type` means `"chat"`. An image model uses `type: "image"` plus `output`. A classifier uses `type: "classifier"` plus `contextWindow`. Non-chat APIs also need the matching operation implementation.

**An invalid registration stops startup.** Pi queues `registerProvider` calls during loading and validates them only after every extension factory finishes. An invalid registration then makes a fresh CLI startup exit with code 1, and a `try`/`catch` around the call inside the factory cannot intercept it. Before testing, make sure that:

- `streamSimple` comes with `api`;
- every supplied model resolves an `api` (at model level, or at provider level for chat models) and a `baseUrl` (at model level, at provider level, or from the provider's existing models).

### Classifier image input and compatibility

Pi `v1.4.0` supports image input for System One classifiers through the `typesafe-system-one` and `cloudflare-workers-ai-system-one` APIs. Extensions call `ctx.modelRegistry.classify(model, { state, questions, images }, options)`; codemode exposes the corresponding `models.classify()` call. This is classification, not image generation or chat.

- Require the selected model's `input` to include `"image"`. An image-capable API does not make every model multimodal. Public `images` entries use base64 image content with `data` and `mimeType`; extension callers use Pi AI's `ImageContent` shape, including `type: "image"`.
- Check `result.stopReason` and `errorMessage`; a resolved classifier result is not necessarily a successful classification. Pass the caller's cancellation through the options when calling from an extension.
- Classifier models registered by an extension accept `compat` on the model. In `models.json`, provider-level `compat` applies to existing classifier models; `models` and `modelOverrides` entries are chat-only. Do not place classifier overrides under `modelOverrides`.

`compat.imageInput` selects the actual service's wire format:

| Value | Service and input contract |
|---|---|
| `"assets"` | TypeSafe and Jev on Workers AI: PNG/JPEG assets, referenced by name before the JSON state |
| `"images"` | Clef on Workers AI: PNG/JPEG/WebP data URLs, at most four images; JSON state remains separate |
| `"state-image-urls"` | OpenRouter: `image_url` parts before the JSON state; the serving model validates supported images |

`compat.sendImageOptInHeader` controls `TypeSafe-Danger-Zone-Images: true`. TypeSafe's own experimental image API requires it; the built-in Workers AI and OpenRouter routes do not. Defaults are detected from the API, provider, endpoint, and model ID, while explicit compatibility values take precedence.

Keep built-in model compatibility metadata when only overriding an endpoint. For a custom proxy that hides the upstream service's identity, set the appropriate compatibility fields explicitly. OpenRouter can accept a TypeSafe-shaped request without an error while silently dropping its assets, so verify the final image-bearing payload rather than treating a successful response as proof that images were used. Use these wire shapes through the built-in adapters instead of pre-encoding them into the public `images` argument.

### Register a complete provider

For a new integration that owns authentication, discovery, filtering, or streaming, prefer `pi.registerProvider(provider)` with a complete `Provider`. Do not use the internal `registerNativeProvider`.

At this revision, the factories come from these entry points:

```ts
import { createProvider, envApiKeyAuth } from "@earendil-works/pi-ai";
import { openAICompletionsApi } from "@earendil-works/pi-ai/compat";
```

- `compat` is one specific public compatibility entry point, not permission to import arbitrary host subpaths.
- The extension loader maps `compat` as a transitional entry point; its source describes it as kept "until compat is removed". Keep these imports in one module so that a later migration stays local.
- API factories such as `openAICompletionsApi` are not TypeScript exports of the `@earendil-works/pi-ai` core root.
- `@earendil-works/pi-ai/models` is also a public entry point, mapped by both the Node loader and bundled virtual modules at the reference revision. These loader mappings are included in `v1.4.0`, not the `v1.3.0` release; do not assume the older release can load this import from an extension. It exports model-service APIs such as `createModels`, not the legacy global catalog helpers. Inside a session, prefer `ctx.modelRegistry` when the operation should use that session's configured providers and credentials; creating a separate service does not inherit them.
- Declare the `@earendil-works/pi-ai` peer. The bundled runtime-load check exposes an import that is unavailable on the installed target; report an incompatibility if it cannot load.

```ts
const provider = createProvider({
  id: "acme",
  name: "Acme",
  auth: { apiKey: envApiKeyAuth("Acme API key", ["ACME_API_KEY"]) },
  models: [{
    id: "replace-with-model-id",
    name: "Acme Model",
    provider: "acme",
    api: "openai-completions",
    baseUrl: "https://api.example.com/v1",
    reasoning: false,
    input: ["text"],
    cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
    contextWindow: 32768,
    maxTokens: 4096,
  }],
  api: openAICompletionsApi(),
});
pi.registerProvider(provider);
```

Put this fragment inside the factory, with the imports above and verified service values. Full provider model objects need `provider`, `api`, and `baseUrl`, unlike the shorter `ProviderConfig` model list.

`createProvider` accepts `id`, an optional name, endpoint, and headers, `auth`, static `models`, an optional `fetchModels`, optional model filters, and at least one concrete implementation in `api`, `images`, or `classifiers`. Its dynamic fetch helper handles restoring and publishing catalogs.

A manually implemented provider has a synchronous `getModels()` that never throws, plus streaming methods. It needs authentication semantics even for a keyless service, because the resolver still reports whether the service is configured.

### Authentication and discovery contracts

The complete-provider and `ProviderConfig` contracts differ:

| Area | Complete `Provider` | `ProviderConfig` |
|---|---|---|
| Model refresh | `refreshModels(ctx): Promise<void>`; publish state with `ctx.publish({ update, persist? })` | `refreshModels(ctx)` returns an array of model definitions |
| Login | `auth.oauth.login(interaction, options?)` | `oauth.login(callbacks)` |
| Refresh credential | `auth.oauth.refresh(credential, signal)` | `oauth.refreshToken(credentials, signal)` |
| Resolve auth | `auth.oauth.toAuth(credential)` | `oauth.getApiKey(credentials)` |

- Native login and refresh return an `OAuthCredential` with `type: "oauth"`.
- Native `toAuth` resolves an auth object with fields such as `apiKey`, `headers`, or `baseUrl`; the legacy `getApiKey` returns a string. Do not mix the two contracts' method placement or return shapes.
- The refresh context supplies `credential`, stored catalog data, `allowNetwork`, `force`, `signal`, the effective `baseUrl`, and `publish`. Restore cached models when offline, honor `allowNetwork: false`, keep the last good catalog on failure, and pass cancellation to I/O.
- Use Pi's login and credential storage. Do not put access tokens, refresh tokens, or authorization headers in package files, session messages, or ordinary logs.
- Provider-scoped environment variables and request headers must survive request conversion.

### Preserve request identity and telemetry

Pi `v1.4.0` includes client identity in Pi AI's public API:

- `ProviderRequestOptions.identity` is a `ClientIdentity` with optional `userAgent`, `attribution`, and `version`. `userAgent` accepts `"detailed"`, `"short"`, or `{ custom: string }`. `attribution: null` explicitly disables inherited attribution.
- `createModels({ identity })` sets request defaults. `withClientIdentity(models, identity)` wraps an existing model service; per-request identity fields override the wrapper, which overrides the service defaults. `mergeClientIdentity` merges fields and skips `undefined`.
- Plain Pi AI defaults to a detailed `User-Agent` and no attribution. Agent loops add Pi attribution by default; the coding-agent request path instead derives it from its install-telemetry setting. Do not hard-code Pi attribution into a package's adapter.
- When delegating to a built-in API, forward `options.identity`. When implementing HTTP directly, `getIdentityHeaders(model, options?.identity)` supplies defaults below model, provider, and request headers. Honor explicit overrides and `null` suppression rather than re-adding removed headers. `before_provider_headers` runs before those API-level defaults, so its observers need not see every final wire header.
- Request instrumentation uses `options.telemetry` (a span), not the removed `telemetryContext` option. Preserve it when forwarding options. Pi AI's `createModels` streaming path records request and usage observations; do not start duplicate request instrumentation around the same delegated call.

These fields affect real request behavior. A provider load is not proof that an adapter forwards them; inspect the final request and instrumentation in an applicable local check.

### Implement a custom wire protocol

Reuse a built-in API implementation whenever possible. A custom `streamSimple(model, context, options?)` must return an `AssistantMessageEventStream` **immediately**, not a Promise, and do its asynchronous request work behind that stream.

The normalized `TranscriptContext` stores system prompts and tool declarations in messages:

- Read them with `getCurrentSystemPrompt(context.messages)` and `getCurrentTools(context.messages)`, not the obsolete `context.systemPrompt` or `context.tools`.
- Use `collapseSystemMessages(context)` for services that cannot accept intermediate system messages.

Implement this sequence:

1. Create an assistant message with role, API, provider, model, timestamp, empty content, zeroed usage and cost, and `stopReason: "pending"`.
2. Prepare the request. Await `options?.onPayload?.(payload, model)`, and use its return value as the replacement when it is not `undefined`.
3. Send the request with the supplied signal, headers, environment, identity, telemetry span, and request options. Call `await options?.onResponse?.({ status, headers }, model)` as soon as the response arrives, before consuming its body.
4. Emit `start` before any content event.
5. For each parsed provider event, await `options?.onProviderStreamEvent?.(providerEvent, model)` before normalizing it. Treat that input as read-only data owned by the adapter.
6. Update content blocks before emitting balanced start, delta, and end events for text, thinking, and tool calls. `partial` references shared evolving state. Parse tool-call arguments by `toolcall_end`.
7. Fill in accurate usage, cost, and the terminal stop reason. Emit exactly one `done` or `error`, then close the stream.

A setup failure can end with `error` before `start`. Cancellation ends with `stopReason: "aborted"`, an `errorMessage`, and an error event whose reason is `"aborted"`. Do not drop tool calls, request hooks, or usage fields silently just to make ordinary text output work.

Verify authentication failure, empty, text, and tool responses, cancellation, timeouts, and reload separately from registration success. The package format cannot establish that a third-party server follows its claimed wire protocol.

## MCP servers

A package can declare an existing MCP server without shipping its own connector or the MCP SDK; Pi's built-in MCP extension makes the connection.

### Declare an HTTP server

```ts
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  pi.registerMcpServer("acme_docs", {
    url: "https://mcp.example.com/mcp",
    headers: { Authorization: "Bearer ${ACME_DOCS_TOKEN}" },
    exposure: "deferred",
    description: "Search Acme documentation.",
    timeout: 60,
  });
}
```

The endpoint and token variable are placeholders. HTTP transport means streamable HTTP; the legacy SSE transport is not supported.

### Declare a bundled stdio server

Use an absolute path to the packaged script:

```ts
import { fileURLToPath } from "node:url";

// Inside the extension factory, for an entry in extensions/:
pi.registerMcpServer("acme_local", {
  command: "node",
  args: [fileURLToPath(new URL("../server/index.js", import.meta.url))],
  env: { ACME_MODE: "readonly" },
  exposure: "deferred",
  timeout: 60,
});
```

This requires a real shipped `server/index.js` and an available Node executable. Add `server/` and its dependencies to the distribution. Pi resolves a relative MCP `cwd` from the session working directory, so package-owned paths should be absolute.

### Configuration fields

| Configuration | Fields |
|---|---|
| Common | `enabled`, `exposure`, `description`, `toolExposure`, `timeout` |
| stdio | `command`, optional `args`, `env`, `cwd` |
| HTTP | `url`, optional `headers`, `oauth`, `auth` |

- `timeout` is in **seconds**, defaults to 60, and progress notifications reset it. `pi.exec` uses milliseconds instead.
- `exposure` is `"codemode"` (the default), `"deferred"`, `"direct"`, or `"hidden"`. Do not pass a normal tool's `"model-only"` exposure here.
- `toolExposure` selects tools by their original server names or by `*` patterns. Exact names take precedence, and the first matching pattern wins.

### Names and failures

- Pi names generated tools `mcp__<server>__<tool>`, and hyphens in a server name become underscores. Do not register both `a-b` and `a_b`.
- Give server names a package prefix, as with tool names.
- `registerMcpServer` throws inside the factory when the configuration is invalid or when another extension already registered the same server name. That error fails extension loading and stops a fresh CLI startup.
- A tool that calls these MCP tools through `ctx.executeTool()` declares `reachesTools` returning the `mcp__<server>` namespace or full tool names, not the bare server name; see [extensions](extensions.md#tool-composition-and-mutable-state).

### Session declarations and authentication

- A registered server is a session declaration, not a write to `mcp.json`. Register it again on every extension load.
- A server with the same name in file-based configuration takes precedence over the extension registration. The `mcp.json` reader and editor accept a leading UTF-8 BOM at this revision; extension registrations themselves are objects, not JSON text.
- Optional OAuth settings include `clientId`, `clientSecret`, `callbackPort`, `callbackUrl`, `scope`, `clientName`, `clientRegistration: "dcr" | "cimd"`, and `authServerMetadataUrl`. Follow the actual server's flow and the configuration the user provides; registration alone does not check authentication.

### Connectors only: `mcp_servers_change`

Only a package that implements an MCP connector should subscribe to `mcp_servers_change` and read `pi.getMcpServers()`. A passive subscription can make Pi think a connector exists and suppress its otherwise useful warning about disconnected servers.
