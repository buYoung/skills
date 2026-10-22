# Extension implementation contracts

Read this before writing or changing an extension. [The starter extension](../assets/starter/extensions/index.ts) is a complete example of a tool, a command, and a flag with a separate helper module. For events, session state, terminal UI, and dynamic resources, continue to [advanced extensions](advanced-extensions.md); for providers, classifier calls, and MCP, to [integrations](integrations.md).

## Contents

- [Factory, imports, and registration](#factory-imports-and-registration)
- [Tools](#tools)
- [Commands, flags, and shortcuts](#commands-flags-and-shortcuts)
- [Names, collisions, and startup failures](#names-collisions-and-startup-failures)

## Factory, imports, and registration

```ts
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";

export default function (pi: ExtensionAPI) {
  pi.registerTool({
    name: "acme_echo",
    label: "Acme Echo",
    description: "Return supplied text unchanged.",
    promptSnippet: "Return supplied text unchanged",
    promptGuidelines: ["Use acme_echo only when an exact echo is useful."],
    parameters: Type.Object({
      text: Type.String({ description: "Text to return unchanged" }),
    }),
    async execute(_toolCallId, params, signal, _onUpdate, _ctx) {
      signal?.throwIfAborted();
      return {
        content: [{ type: "text", text: params.text }],
        details: { echoed: params.text },
      };
    },
  });
}
```

- The default export is a function that returns `void` or `Promise<void>`. Pi waits for factories one after another, with no built-in time limit. Keep registration deterministic and finite.
- Start processes, sockets, timers, and watchers at session start or on first use, not at module top level.
- Import `Type` from `typebox`, not from `pi-coding-agent`.
- Prefer exports from the public package root. Do not deep-import `src` or `dist`. Check any public subpath used by an advanced integration against the target runtime; loader aliases do not establish that a subpath is public.
- An inline `pi.registerTool({...})` infers parameter types. For a definition stored separately or shared in an array, wrap it in the public `defineTool({...})` helper from `pi-coding-agent` to keep that inference.

### What you can call while the factory runs

Register everything here: `on`, `registerTool`, `registerCommand`, `registerFlag`, `registerShortcut`, message renderers, providers, and MCP configuration. Pi parses flags after registration, so read flag values inside handlers instead of freezing `getFlag()` while the factory runs.

Session-dependent actions are not ready during loading. These include message sending, `appendEntry`, `getActiveTools`, `getAllTools`, `setActiveTools`, `getCommands`, `getSettings`, `setModel`, and related session and model operations. Calling them too early throws `Extension runtime not initialized...`. `setModel` instead returns a Promise rejected with that error, so an unawaited call fails silently.

`pi.exec` and `pi.events` can technically work during loading. Starting external work there, however, also affects package commands and help output. Initialize optional services later, report their failures when they are used, and keep unrelated features usable.

## Tools

### Definition fields

| Field | Contract |
|---|---|
| `name` | Unique machine identifier; use a package prefix such as `acme_` |
| `label` | Human-readable UI label |
| `description` | Explains the task, inputs, and important limits to the model |
| `parameters` | Object schema, including `Type.Object({})` for no inputs |
| `execute` | Async function that returns the result |

All five fields are required. Useful optional fields include `promptSnippet`, `promptGuidelines`, `outputSchema`, `executionMode`, `exposure`, `defaultActive`, and rendering hooks; use only options the target API provides.

```text
execute(toolCallId, params, signal, onUpdate, ctx)
```

The third argument is the optional `AbortSignal`, the fourth the optional progress callback, and the fifth the `ExtensionToolContext`. Do not copy examples written for a different signature.

### Results

A result has `content` and `details`. Use `details: undefined` when there is nothing to keep.

- `content` can hold text and image blocks. The model sees `content`, so always give it an understandable text result.
- `details` holds machine-readable data for renderers and session reconstruction.
- When you declare `outputSchema`, also return matching `structuredContent`. Structured output does not replace the text result.

### Failure, cancellation, and progress

Report a failure in one of two ways: throw, or return top-level `isError: true`:

```ts
return {
  content: [{ type: "text", text: "The requested record was not found." }],
  details: { code: "not_found" },
  isError: true,
};
```

Text that says "error", or a `details.error` field, without a throw or top-level `isError` still counts as a successful result. Do not turn cancellation into a successful fallback.

Pass `signal` to downstream I/O, and check whether it is already aborted. For a timeout, combine it with the caller's signal instead of replacing the caller's cancellation:

```ts
const timeoutSignal = AbortSignal.timeout(5000);
const requestSignal = signal
  ? AbortSignal.any([signal, timeoutSignal])
  : timeoutSignal;
const response = await fetch(url, { signal: requestSignal });
```

This fragment belongs inside `execute`, with `url` supplied by the feature. These APIs are available under Pi's Node requirement at this revision.

`onUpdate?.({ content, details })` publishes interim output in the same shape as the final result. Send updates while the execution is pending; Pi ignores updates sent after completion.

### Subprocesses

Pass an executable and an argument array:

```ts
const result = await pi.exec("git", ["status", "--short"], {
  cwd: ctx.cwd,
  signal,
  timeout: 5000,
});
if (result.killed || result.code !== 0) {
  return {
    content: [{ type: "text", text: result.stderr || "git status failed" }],
    details: { exitCode: result.code, killed: result.killed },
    isError: true,
  };
}
return {
  content: [{ type: "text", text: result.stdout || "No local changes." }],
  details: { exitCode: result.code },
};
```

- `pi.exec` uses `shell: false`, so pipes and redirects are not interpreted.
- Its timeout is in **milliseconds**.
- Pass the session's `ctx.cwd`.
- Do not join user input into a shell command to shorten the code.
- If the package needs Git, document Git as a prerequisite.

### Bound model-facing output

Git status, search results, directory listings, logs, and HTTP responses can grow with their input. Bound their text before returning it, on failure paths too. A process timeout limits elapsed time, not output size.

The public `truncateHead` and `truncateTail` helpers default to 2000 lines or 50 KiB, whichever comes first. Their result includes `.content`, `.truncated`, and the original and output sizes.

Copy [bounded-output.ts](../assets/patterns/bounded-output.ts) into the generated package's `lib/` directory and include it in `files`. The helper:

- returns small output unchanged;
- truncates large output and saves the complete text in a private file outside the package checkout;
- takes an optional third argument that chooses what survives: `"head"` (the default) keeps the beginning, for listings and file contents; `"tail"` keeps the end, for logs and command output whose errors and final results come last;
- in head mode, still returns a byte-bounded prefix when the first line alone exceeds the byte limit. Pi's `truncateHead` by itself returns empty content in that case.

Call the helper in the shared execution path so the tool and any direct command return the same bounded text:

```ts
import { prepareModelOutput } from "../lib/bounded-output.ts";

// Inside execute, after collecting stdout/stderr:
const output = await prepareModelOutput(result.stdout || result.stderr, signal);
return {
  content: [{ type: "text", text: output.text }],
  details: {
    truncated: output.truncated,
    fullOutputPath: output.fullOutputPath,
    exitCode: result.code,
  },
  isError: result.killed || result.code !== 0,
};
```

- Choose the right combined diagnostic text before you pass it to the helper; do not hide a useful error behind unrelated stdout.
- Do not append the unbounded text again after truncating, including in a custom message that will later enter model context.
- With `structuredContent`, keep its declared data contract intact. Design pagination or file references for large data instead of silently cutting a JSON value.
- Verify both many-line and single-line oversized output. Confirm that the text stays within budget, still contains a meaningful portion of the output, and that the saved file equals the original.
- Document that the complete-output file is temporary.

This pattern bounds model-facing content after collection. A process or network stream whose output may be unbounded also needs a cap while collecting, or a strategy that streams to a file.

### Tool composition and mutable state

`ctx.executeTool(name, args, options?)` inherits the outer tool's abort signal by default. It returns an outcome with `toolCall`, `result`, `isError`, and an optional duration. A failed tool does not necessarily reject the Promise, so inspect `outcome.isError`.

For a tool that reaches MCP tools, declare `reachesTools(input)` on its definition:

- Return `"all"` when a call can reach any server, for example by searching or enumerating tools.
- Otherwise return words that contain the target MCP namespace `mcp__<server>`, such as `["mcp__acme_docs"]`, or a full tool name such as `"mcp__acme_docs__search"`. Hyphens in a server name become underscores.
- Do not return a bare server name such as `"acme_docs"`. Before the outer tool runs, the built-in MCP extension waits only for servers whose namespace appears inside a returned word. A bare name contains no namespace, so nothing waits, and a nested call made while that server is still connecting can fail as an unknown tool.

`ctx.executeTool()` alone does not wait for registration. Use the current `ctx.tools` catalog to discover callable tools instead of assuming that every loaded name is available in the current exposure.

In Pi `v1.4.0`, packages embedding SDK sessions with the built-in `codemode` share worker capacity across all sessions in that process: two workers by default, configurable with a positive integer `PI_CODEMODE_MAX_WORKERS`. At capacity, scripts queue in arrival order for at most 60 seconds or their shorter `timeout_ms`; that wait counts toward the script deadline. The `v1.3.0` release rejects at capacity instead of queuing. A canceled worker retains its slot until it exits. Do not hold every slot while awaiting another in-process session that itself needs codemode. A queued timeout fails without running the script; it does not prove that the requested operation executed.

Set `executionMode: "sequential"` on a tool whose shared mutable state cannot tolerate parallel calls. For file mutations, wrap the whole read/modify/write transaction, not only the final write, in the public `withFileMutationQueue(absolutePath, async () => ...)` helper.

`registerTool()` refreshes runtime tools after initialization; there is no public `pi.refreshTools()` method. Do not register repeated copies of a tool on every session event when a single factory registration works.

### Tool activation across resume and tree navigation

Pi `v1.4.0` restores the branch's recorded tool additions and removals, including records before compaction. With default tool selection, an extension tool that the branch never mentioned is treated as newly registered: it activates only for `direct` or `model-only` exposure and when `defaultActive` is not `false`. A tool the branch removed stays inactive. Built-in tools follow `defaultTools` instead.

Recorded tools that are allowed but not yet registered, such as tools from an MCP server still connecting, remain pending and activate when they register. At startup, explicit tool selection takes precedence over transcript restoration; `--tools +name`/`-name` modifiers apply to the restored selection. Tree navigation restores the target branch while respecting the effective tool allowlist and exclusions. Do not unconditionally reactivate every tool from `session_start`, which would undo the branch's removals. Check resumed sessions and `/tree`, not just a fresh session.

## Commands, flags, and shortcuts

```ts
pi.registerFlag("acme-compact", {
  type: "boolean",
  description: "Use compact Acme output",
  default: false,
});

pi.registerCommand("acme-status", {
  description: "Show Acme runtime status",
  handler: async (_args, ctx) => {
    const compact = pi.getFlag("acme-compact") === true;
    pi.sendMessage({
      customType: "acme-status",
      content: compact ? "Acme ready." : `Acme ready in ${ctx.cwd}.`,
      display: true,
    });
  },
});
```

- Register command names without the leading `/` and flag names without `--`.
- A command requires a function `handler`.
- Flag types are `"string"` or `"boolean"`, and a declared default must have the matching type.

Shortcuts take a `KeyId`, not a command name:

```ts
pi.registerShortcut("ctrl+shift+a", {
  description: "Show Acme status",
  handler: async (ctx) => {
    if (ctx.hasUI) ctx.ui.notify("Acme ready.", "info");
  },
});
```

Check the current built-in bindings before choosing a shortcut. A key cannot carry a package prefix.

Commands receive an `ExtensionCommandContext` with operations such as `waitForIdle`, `newSession`, `switchSession`, `fork`, and `reload`. Tools and lifecycle handlers do not receive these command-only methods.

```ts
pi.registerCommand("acme-reload", {
  description: "Reload Pi resources",
  handler: async (_args, ctx) => {
    await ctx.reload();
    return;
  },
});
```

Stop using the old context after a reload or session replacement. Do not queue the string `/acme-reload` through `sendUserMessage` and expect it to run this command; Pi can treat a programmatic message as plain text.

## Names, collisions, and startup failures

| Collision | Behavior at this revision |
|---|---|
| Two extensions register the same tool or flag | CLI startup fails; reload and the SDK keep the first registration and report errors |
| Extension tool uses a built-in tool name | Replaces the built-in tool without a warning |
| Extension commands share a name | They become `/name:1`, `/name:2`, and so on |
| Command matches a built-in interactive command | Can be skipped in autocomplete; do not rely on ambiguous dispatch |
| Shortcuts collide | Fixed built-ins win; configurable built-ins can be overridden; the later extension shortcut wins |
| Skill, prompt, or theme names collide | The first discovered name wins, with a collision diagnostic |

Installed package resources generally come after local resources, while temporary `-e` packages come earlier. Do not design around a rule that packages always lose.

### Replacing built-ins

Pi has replaceable built-in extensions. Registering names such as `codemode`, `tool_search`, or the `mcp` command can suppress an entire built-in extension when Pi detects an external replacement. Use those names only for an intentional, documented replacement.

To replace a built-in tool:

1. Get its public definition factory, for example `createReadToolDefinition`.
2. Spread the original definition and override only the intended behavior.
3. Preserve the input schema, result metadata, rendering, and cancellation.
4. Describe the replacement in the package README.

These factories take the working directory as their first argument and fix it when called, but the extension factory has no session context. Create the delegate inside `execute` from `ctx.cwd`, not from a `process.cwd()` captured at load time, so relative paths follow the current session. The shorter `createReadTool` returns an `AgentTool` without the definition-level prompt and rendering information, so re-registering it as an extension cannot preserve those fields.

Pi `v1.4.0`'s built-in `grep` runs ripgrep with `--no-config`, so `RIPGREP_CONFIG_PATH` cannot silently change its regex, literal, or filtering behavior. Preserve that boundary when wrapping the built-in; a separate custom search tool may expose different behavior explicitly.

### What stops CLI startup

Each of these makes a fresh CLI startup exit with code 1:

- Factory import errors and invalid default exports.
- Tool or flag conflicts between extensions.
- Errors thrown by a registration call inside the factory, such as `registerMcpServer` with an invalid configuration or with a server name that another extension already registered.
- Invalid provider registrations. Pi validates queued `registerProvider` calls only after every factory finishes, so a `try`/`catch` around the call cannot intercept the failure. [Integrations](integrations.md) lists the required fields.

Runtime event errors are usually reported while execution continues, but `tool_call` and `user_bash` errors block their operation. A successful reload does not replace a fresh-start check.
