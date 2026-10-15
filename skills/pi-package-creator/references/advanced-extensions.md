# Events, session state, UI, and dynamic resources

Read only the sections for features the package needs. For providers and MCP, continue to [integrations](integrations.md).

## Contents

- [How event handlers run](#how-event-handlers-run)
- [Choose an event](#choose-an-event)
- [Return shapes that differ from ordinary patches](#return-shapes-that-differ-from-ordinary-patches)
- [Input, tool, and continuation handlers](#input-tool-and-continuation-handlers)
- [Session state](#session-state)
- [Dynamic resource discovery](#dynamic-resource-discovery)
- [UI and terminal components](#ui-and-terminal-components)

## How event handlers run

Handlers run one after another in registration and load order, with no automatic timeout. When a handler throws, Pi usually reports the error and runs the remaining handlers. `tool_call` and `user_bash` are deliberate exceptions: a thrown error blocks the tool call or shell command, because continuing could run an operation the handler meant to stop.

Use the exact event names the target supports. Some request and event surfaces changed after `v1.2.0`, so do not infer an event's payload from its name alone.

## Choose an event

### Session lifecycle

| Event | Use and contract |
|---|---|
| `session_start` | Initialize the current session and reconstruct branch state. Also fires after a reload or session replacement. |
| `session_shutdown` | Release session resources. It can mean a reload or session replacement, not only process exit, so make cleanup idempotent. |
| `session_before_switch`, `session_before_fork`, `session_before_tree`, `session_before_compact` | Influence the matching operation. Return `undefined` when not participating; `{}` can erase a previous handler's result. |
| `session_tree`, `session_compact`, `session_compact_failed` | Observe navigation and compaction outcomes. A switch or fork shows up as the new session's `session_start`; there are no `session_switch` or `session_fork` events. |
| `session_info_changed` | Observe session metadata changes. |
| `resources_discover` | Return additional `skillPaths`, `promptPaths`, or `themePaths`. Fires after session start. |

### Agent runs and model requests

| Event | Use and contract |
|---|---|
| `before_agent_start` | Adjust per-run prompt options or supply context. Distinguish `messageType: "user"` from `"custom"`. |
| `agent_start` | Observe the start of an agent run. |
| `context` | Transform conversation messages before a model call; system messages are restored afterward. |
| `context_with_system` | Transform the complete request messages, including system messages. Preserve required system and tool metadata yourself. |
| `before_provider_request` | Inspect or replace the provider request payload. |
| `before_provider_headers`, `after_provider_response` | Inspect or change request headers, then observe the response status and headers. |
| `provider_stream_event` | Observe parsed provider stream events; treat adapter-owned data as read-only. |
| `cache_warming_decision` | Inspect the warm/miss cost, continuation probability, and current action; return `{ action: "warm" \| "stop" }` to override the action. |

### Messages, tools, and turns

| Event | Use and contract |
|---|---|
| `message_start`, `message_update`, `message_end` | Observe message progress. A message boundary does not mean the session finished. |
| `tool_call` | Inspect or block calls; return `{ block: true, reason }` to block. A thrown error also blocks. |
| `tool_result` | Transform tool results. Replacing only `content` drops the old structured content. |
| `tool_execution_start`, `tool_execution_update`, `tool_execution_end` | Observe execution progress and completion, including nested call identifiers. |
| `turn_start`, `turn_end` | Observe a model turn. `turn_end` can contribute entries and request continuation. |
| `agent_before_settle` | Final continuation boundary, with `{ entries?, continue? }`. |
| `agent_end` | The low-level loop ended; retry, compaction, or queued work may remain. |
| `agent_settled` | All follow-up work settled; includes `aborted`. |

### Input, UI, model, trust, and MCP

| Event | Use and contract |
|---|---|
| `ui_prompt_start`, `ui_prompt_end` | Observe the lifetime of a UI prompt. |
| `input` | Handle or transform input before skill and template expansion. |
| `user_bash` | Intercept an interactive shell request. Return `undefined` for local execution, or exactly one of `{ operations }` (a custom executor) and `{ result }` (completed output). The first such return wins. Any other value is an error and blocks the command. |
| `model_select` | Observe a model change. |
| `thinking_level_select` | Observe a thinking-level change. |
| `project_trust` | Take part in the trust decision from a personal extension. Project extensions load too late. |
| `mcp_servers_change` | Only for an MCP connector that implements connections; see [integrations](integrations.md). |

## Return shapes that differ from ordinary patches

| Handler | Exact contract |
|---|---|
| `before_provider_request` | Return the replacement payload itself, not `{ payload: replacement }`. Return `undefined` to keep the payload. |
| `before_provider_headers` | Mutate `event.headers` in place; return values are ignored. Assign `null` to delete a header. |
| `after_provider_response` | Observe `event.status` and `event.headers`. This hook cannot replace the body. |
| `project_trust` | Return `{ trusted: "yes" \| "no" \| "undecided", remember? }`. A handler that does not participate still returns `trusted: "undecided"`, not `undefined`. |
| `message_end` | Return `{ message }` to replace the final message, keeping its original role. |
| `session_before_switch` | Return `{ cancel: true }` to cancel, or `undefined` to leave earlier decisions alone. |
| `session_before_fork` | Optional `{ cancel }`. The type also declares `skipConversationRestore`, but no code at this revision reads it; do not rely on it. |
| `session_before_compact` | Optional `{ cancel, compaction }`, where a custom compaction supplies a valid compaction result. |
| `session_before_tree` | Optional cancellation, summary, custom summarization instructions, replacement mode, or label. |

`project_trust` is a specialized contract that runs before the session; its context is not a normal extension context. Keep its decision tied to the trust policy explicitly requested for the package.

## Input, tool, and continuation handlers

### Transform input and prompts

```ts
pi.on("input", async (event) => {
  if (event.text.trim() === "acme help") {
    return {
      action: "transform",
      text: "Explain the Acme package's available tools.",
      images: event.images,
    };
  }
  return { action: "continue" };
});
```

- `action: "handled"` stops further input processing.
- Transforms chain in handler order. Keep the images when transforming input that contains them.
- Check the event's source so that your extension does not keep recapturing input it generated itself.

In `before_agent_start`:

- Read `event.prompt` only when `event.messageType === "user"`. The `"custom"` variant has `event.message` instead.
- Modify `event.systemPromptOptions` when an additive option is enough. Returning `systemPrompt` replaces the whole prompt; it does not append.
- Pi collects returned custom messages.

`context` changes the request context, not the permanent session history. `context_with_system` runs afterward and is more invasive: Pi reports removal of the leading system message as an error but does not repair it automatically. Preserve tool declarations, relevant intermediate system messages, and required instructions.

### Inspect tool calls and results

```ts
pi.on("tool_call", async (event) => {
  if (event.toolName === "acme_delete_record") {
    return { block: true, reason: "Record deletion is disabled in this package mode." };
  }
});
```

This example shows the return shape for a policy. Implement only the policy the user requested.

Changes to `event.input` happen in place, and Pi does not validate the input again afterward. Prefer producing valid tool input in the first place; if a handler rewrites it, keep the complete tool schema contract.

To redact results, handle `content`, `details`, and `structuredContent`. `tool_result` patches compose in order, and a patch that replaces only `content` discards the old `structuredContent`.

### Control continuation

In `turn_end` and `agent_before_settle`, returned `entries` replace the current proposal. To append, return `entries: [...event.entries, newEntry]`. A later explicit `continue` value can replace an earlier one.

Give every continuation policy a finite stopping condition. Check the outcome, `event.context.canContinue`, and queued work where available; an unconditional `continue: true` can loop the model without end. Send final notifications from `agent_settled`, not `agent_end`.

## Session state

Choose storage by how long the data must live:

| Lifetime or purpose | Mechanism |
|---|---|
| Disposable runtime cache | Factory closure, rebuilt for each runtime |
| Tool-specific persisted state | Tool result `details` |
| Session state the model does not see | `pi.appendEntry(customType, data)` |
| Session context the model also sees | `pi.sendMessage({ customType, content, display, details })` |
| Cross-session user data | Documented storage outside installed package directories |

Restore state from the **current branch**, not from every entry the session ever recorded. Otherwise navigating to an earlier branch can inherit state from a different conversation.

This complete extension persists a small counter:

```ts
import type {
  ExtensionAPI,
  ExtensionContext,
} from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  let count = 0;

  function restore(ctx: ExtensionContext) {
    count = 0;
    for (const entry of ctx.sessionManager.getBranch()) {
      if (entry.type !== "custom" || entry.customType !== "acme-counter") continue;
      const data = entry.data as { count?: unknown } | undefined;
      if (typeof data?.count === "number" && Number.isSafeInteger(data.count)) {
        count = data.count;
      }
    }
  }

  pi.on("session_start", (_event, ctx) => restore(ctx));
  pi.on("session_tree", (_event, ctx) => restore(ctx));

  pi.registerCommand("acme-count", {
    description: "Increment this branch's Acme counter",
    handler: async () => {
      count += 1;
      pi.appendEntry("acme-counter", { count });
      pi.sendMessage({
        customType: "acme-counter-result",
        content: `Counter: ${count}`,
        display: true,
      });
    },
  });
}
```

The entry type carries the package prefix. More complex data needs a schema version and compatible restoration logic. Keep secrets out of ordinary session history.

Use the new handler context each time. After a reload or session replacement, a captured `ctx` or `pi` from the old runtime is invalid. For `newSession`, `fork`, or `switchSession`, do follow-up work in the API's `withSession: async (newCtx) => ...` callback, and return after the operation instead of continuing with the old context.

Manage each session resource through this lifecycle:

1. Initialize it in `session_start` or lazily on first use.
2. Keep its cleanup handle in the runtime closure.
3. In `session_shutdown`, stop, cancel, or close it, and clear the handle.
4. After a reload, initialize it again in the new runtime.

Do not use module-global singleton state to communicate across packages. Use `pi.events` for shared event communication; namespace the event names, and release subscriptions when their lifecycle ends.

## Dynamic resource discovery

Static resources belong in the manifest. Use dynamic discovery only when the paths truly depend on runtime configuration:

```ts
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { fileURLToPath } from "node:url";

export default function (pi: ExtensionAPI) {
  const skillRoot = fileURLToPath(new URL("../generated-skills/", import.meta.url));
  pi.on("resources_discover", () => ({
    skillPaths: [skillRoot],
  }));
}
```

This example assumes an entry in `extensions/` and an existing `generated-skills/` directory that is packaged or generated.

- A relative returned path resolves against the session working directory, not the extension file. Compute absolute package-owned paths from `import.meta.url`.
- Return `promptPaths` or `themePaths` the same way.
- A reload discards earlier dynamic results and discovers them again.
- Include dynamic assets in the tarball; dynamic discovery does not make unpublished files available.
- Dynamic paths are appended after resources already discovered. Because the first discovered name wins, a dynamic skill, prompt, or theme loses to an existing resource with the same name.

## UI and terminal components

`ctx.mode` is exactly one of `"tui"`, `"rpc"`, `"json"`, or `"print"`; text-print output uses `"print"`, not `"text"`.

- Use `ctx.hasUI` for dialogs that RPC can also serve.
- Require `ctx.mode === "tui"` for terminal-only rendering. RPC can have `hasUI === true` without a terminal.
- In print and JSON modes, confirmation returns false, and selection or input can return `undefined`. Treat those as cancellation or as an explicitly documented noninteractive default.

For simple UI, prefer:

- `ctx.ui.notify(message, "info" | "warning" | "error")`
- `await ctx.ui.confirm(title, message)`
- `await ctx.ui.select(title, options)`
- `await ctx.ui.input(title, placeholder)`
- `ctx.ui.setStatus("acme-status", text)`; pass `undefined` to clear.
- `ctx.ui.setWidget("acme-widget", lines)`; pass `undefined` to clear.

A minimal terminal dialog inside a command handler:

```ts
// Add @earendil-works/pi-tui as a "*" peer.
import { matchesKey, truncateToWidth } from "@earendil-works/pi-tui";

// Inside handler(_args, ctx):
if (ctx.mode !== "tui") return;
const accepted = await ctx.ui.custom<boolean>((_tui, _theme, _keys, done) => ({
  render: (width) => [
    truncateToWidth("Acme: Enter to continue, Escape to cancel.", width),
  ],
  invalidate() {},
  handleInput(data) {
    if (matchesKey(data, "enter")) done(true);
    else if (matchesKey(data, "escape")) done(false);
  },
}));
```

- The custom factory returns a component with `render(width): string[]` and `invalidate()`. Input handling, mouse handling, and `dispose()` are optional.
- Every rendered line must fit its visible width. Use `truncateToWidth`, `visibleWidth`, or `wrapTextWithAnsi` from `pi-tui`.
- After changing component state, invalidate its cache and call `tui.requestRender()`.
- Finish with `done(value)`; hiding an overlay does not resolve `custom()`.
- Dispose timers and listeners.
- When wrapping input components, forward focus so that cursor placement and IME input stay correct.
