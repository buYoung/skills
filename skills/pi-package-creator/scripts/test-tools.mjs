#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import { mkdir, readFile, realpath, rm, stat, writeFile } from "node:fs/promises";
import { basename, dirname, isAbsolute, join, relative, resolve, win32 } from "node:path";
import { fileURLToPath } from "node:url";
import {
  createWorkspace,
  importPublic,
  isolatedEnv,
  locatePeerRoot,
  locatePiRoot,
} from "./lib/runtime.mjs";

const RESULT_PREFIX = "__PI_TOOL_TEST_RESULT__";
const LINGER_MARKER = "__PI_TOOL_TEST_LINGERED__";
const EXIT_GRACE_MS = 2000;
const LINGER_FAILURE = `The case process was still alive ${EXIT_GRACE_MS} ms after session_shutdown and session disposal; ` +
  "an extension left a timer, watcher, socket, or child process active. Release it in session_shutdown.";
const DEFAULT_TIMEOUT_MS = 20000;
const MAX_CAPTURE_BYTES = 4 * 1024 * 1024;
const LIMITS = [
  "Conversational assistant responses come from an in-memory fixture; the harness does not verify external I/O performed by the tool itself.",
  "Calls session.agent.prompt: session.prompt input expansion, before_agent_start, and agent_settled are not exercised.",
  "Provider, virtual-model, and MCP registrations require separate integration checks.",
  "Runs in print mode; interactive UI and command-driven session replacement are not verified.",
  "Temporary directories and a restricted environment are configuration isolation, not an operating-system sandbox.",
  "An aborted run does not by itself prove that a tool cancelled its downstream operation.",
  "Each case starts a new session and issues one top-level tool call; cross-call state and multi-call batch scheduling require dedicated integration cases.",
];

class UnsupportedCase extends Error {}

function isObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function requireValue(condition, message) {
  if (!condition) throw new Error(message);
}

function rejectUnknown(value, allowed, location) {
  for (const key of Object.keys(value)) {
    requireValue(allowed.includes(key), `${location}: unsupported field "${key}"`);
  }
}

function relativeFixturePath(value, location) {
  requireValue(typeof value === "string" && value.length > 0, `${location}: expected a relative path`);
  requireValue(!isAbsolute(value) && !win32.isAbsolute(value), `${location}: absolute paths are not allowed`);
  requireValue(!value.includes("\0") && !value.split(/[\\/]/).includes(".."), `${location}: invalid relative path`);
  requireValue(value !== "." && value !== "./", `${location}: expected a file path`);
  return value;
}

function strings(value, location) {
  const values = typeof value === "string" ? [value] : value;
  requireValue(Array.isArray(values) && values.every((entry) => typeof entry === "string"),
    `${location}: expected a string or an array of strings`);
  return values;
}

function validateCase(testCase, index) {
  const at = `cases[${index}]`;
  requireValue(isObject(testCase), `${at}: expected an object`);
  rejectUnknown(testCase,
    ["name", "tool", "args", "files", "setupCommands", "flags", "expect", "abortAfterMs"], at);
  for (const key of ["name", "tool"]) {
    requireValue(typeof testCase[key] === "string" && testCase[key].trim(), `${at}.${key}: expected a nonempty string`);
  }
  if (testCase.files !== undefined) {
    requireValue(isObject(testCase.files), `${at}.files: expected a path-to-string object`);
    for (const [path, content] of Object.entries(testCase.files)) {
      relativeFixturePath(path, `${at}.files`);
      requireValue(typeof content === "string", `${at}.files.${path}: expected a string`);
    }
  }
  if (testCase.setupCommands !== undefined) {
    requireValue(Array.isArray(testCase.setupCommands), `${at}.setupCommands: expected an array`);
    for (const [commandIndex, command] of testCase.setupCommands.entries()) {
      const commandAt = `${at}.setupCommands[${commandIndex}]`;
      requireValue(isObject(command), `${commandAt}: expected an object`);
      rejectUnknown(command, ["command", "args"], commandAt);
      requireValue(typeof command.command === "string" && command.command.length > 0,
        `${commandAt}.command: expected a nonempty string`);
      requireValue(command.args === undefined ||
        (Array.isArray(command.args) && command.args.every((arg) => typeof arg === "string")),
      `${commandAt}.args: expected an array of strings`);
    }
  }
  if (testCase.flags !== undefined) {
    requireValue(isObject(testCase.flags), `${at}.flags: expected an object`);
    for (const [name, value] of Object.entries(testCase.flags)) {
      requireValue(name.length > 0 && !name.startsWith("--"), `${at}.flags: names omit "--"`);
      requireValue(typeof value === "boolean" || typeof value === "string",
        `${at}.flags.${name}: expected a boolean or string`);
    }
  }
  if (testCase.abortAfterMs !== undefined) {
    requireValue(Number.isSafeInteger(testCase.abortAfterMs) && testCase.abortAfterMs >= 0,
      `${at}.abortAfterMs: expected a nonnegative integer`);
  }
  requireValue(isObject(testCase.expect), `${at}.expect: expected assertions`);
  const expected = testCase.expect;
  rejectUnknown(expected, [
    "isError", "aborted", "textIncludes", "textExcludes", "details",
    "maxTextBytes", "maxTextLines", "fullOutputPathDetail", "fullOutputEqualsFile",
  ], `${at}.expect`);
  requireValue(typeof expected.isError === "boolean", `${at}.expect.isError: a boolean is required`);
  if (expected.aborted !== undefined) {
    requireValue(typeof expected.aborted === "boolean", `${at}.expect.aborted: expected a boolean`);
  }
  for (const key of ["textIncludes", "textExcludes"]) {
    if (expected[key] !== undefined) strings(expected[key], `${at}.expect.${key}`);
  }
  if (expected.maxTextBytes !== undefined) {
    requireValue(Number.isSafeInteger(expected.maxTextBytes) && expected.maxTextBytes >= 0,
      `${at}.expect.maxTextBytes: expected a nonnegative integer`);
  }
  if (expected.maxTextLines !== undefined) {
    requireValue(Number.isSafeInteger(expected.maxTextLines) && expected.maxTextLines >= 0,
      `${at}.expect.maxTextLines: expected a nonnegative integer`);
  }
  if (expected.fullOutputPathDetail !== undefined) {
    requireValue(typeof expected.fullOutputPathDetail === "string" &&
      expected.fullOutputPathDetail.split(".").every(Boolean),
    `${at}.expect.fullOutputPathDetail: expected a dot-separated path relative to details`);
  }
  if (expected.fullOutputEqualsFile !== undefined) {
    relativeFixturePath(expected.fullOutputEqualsFile, `${at}.expect.fullOutputEqualsFile`);
    requireValue(expected.fullOutputPathDetail !== undefined,
      `${at}.expect.fullOutputEqualsFile requires fullOutputPathDetail`);
  }
  return testCase;
}

function substitute(value, workspace) {
  if (typeof value === "string") {
    return value.replaceAll("{{cwd}}", workspace.cwd).replaceAll("{{name}}", basename(workspace.cwd));
  }
  if (Array.isArray(value)) return value.map((entry) => substitute(entry, workspace));
  if (isObject(value)) {
    return Object.fromEntries(Object.entries(value).map(([key, entry]) => [key, substitute(entry, workspace)]));
  }
  return value;
}

function partialMatch(actual, expected, path = "details") {
  if (Array.isArray(expected)) {
    requireValue(Array.isArray(actual) && actual.length === expected.length, `${path}: array shape differs`);
    expected.forEach((value, index) => partialMatch(actual[index], value, `${path}[${index}]`));
  } else if (isObject(expected)) {
    requireValue(isObject(actual), `${path}: expected an object`);
    for (const [key, value] of Object.entries(expected)) {
      requireValue(Object.hasOwn(actual, key), `${path}.${key}: missing property`);
      partialMatch(actual[key], value, `${path}.${key}`);
    }
  } else {
    requireValue(Object.is(actual, expected), `${path}: value differs from the expected fixture`);
  }
}

function detailAt(details, path) {
  return path.split(".").reduce((value, key) =>
    value !== null && typeof value === "object" && Object.hasOwn(value, key) ? value[key] : undefined, details);
}

async function containedFile(path, root, label) {
  const actualPath = await realpath(path);
  const actualRoot = await realpath(root);
  const suffix = relative(actualRoot, actualPath);
  requireValue(suffix !== "" && suffix !== ".." && !suffix.startsWith(`..${process.platform === "win32" ? "\\" : "/"}`) &&
    !isAbsolute(suffix), `${label}: file must remain inside the isolated workspace`);
  requireValue((await stat(actualPath)).isFile(), `${label}: expected a regular file`);
  return actualPath;
}

function forbidOperation(name, observedOperations) {
  return () => {
    observedOperations.push(name);
    throw new UnsupportedCase(`Unsupported in the tool-only harness: ${name}`);
  };
}

async function runWorker(input) {
  const { testCase, packageDir, piRoot, workspace, timeoutMs } = input;
  validateCase(testCase, 0);
  const prepared = substitute(testCase, workspace);
  const startedAt = Date.now();
  for (const [path, content] of Object.entries(prepared.files ?? {})) {
    const target = join(workspace.cwd, relativeFixturePath(path, "files"));
    await mkdir(dirname(target), { recursive: true });
    await writeFile(target, content);
  }
  for (const command of prepared.setupCommands ?? []) {
    const result = spawnSync(command.command, command.args ?? [], {
      cwd: workspace.cwd,
      env: isolatedEnv({ PI_OFFLINE: "1", PI_CODING_AGENT_DIR: workspace.agentDir, TMPDIR: workspace.root }),
      timeout: Math.max(1, timeoutMs - (Date.now() - startedAt)),
      killSignal: "SIGKILL",
      maxBuffer: MAX_CAPTURE_BYTES,
      encoding: "utf8",
      shell: false,
    });
    requireValue(!result.error && result.status === 0,
      `Setup command failed: ${command.command}: ${result.error?.message ?? result.stderr?.slice(-2000) ?? `exit ${result.status}`}`);
  }
  let expectedFullOutput;
  if (prepared.expect.fullOutputEqualsFile !== undefined) {
    const expectedPath = await containedFile(
      join(workspace.cwd, relativeFixturePath(prepared.expect.fullOutputEqualsFile, "fullOutputEqualsFile")),
      workspace.cwd,
      "expected output",
    );
    expectedFullOutput = await readFile(expectedPath);
  }

  const sdk = await importPublic(piRoot);
  const ai = await importPublic(await locatePeerRoot(piRoot, "@earendil-works/pi-ai"));
  for (const name of ["fauxProvider", "fauxAssistantMessage", "fauxToolCall", "InMemoryCredentialStore"]) {
    if (typeof ai[name] !== "function") throw new UnsupportedCase(`Installed Pi AI lacks ${name}`);
  }
  const settingsManager = sdk.SettingsManager.inMemory({
    packages: [],
    cacheWarming: "off",
    compaction: { enabled: false },
    retry: { enabled: false },
  }, { projectTrusted: false });
  const loader = new sdk.DefaultResourceLoader({
    cwd: workspace.cwd,
    agentDir: workspace.agentDir,
    settingsManager,
    additionalExtensionPaths: [packageDir],
    noExtensions: true,
    noSkills: true,
    noPromptTemplates: true,
    noThemes: true,
    noContextFiles: true,
    systemPrompt: "Execute the deterministic local package test.",
    appendSystemPrompt: [],
  });
  await loader.reload();
  const loaded = loader.getExtensions();
  requireValue(loaded.errors.length === 0, `Extension load failed: ${JSON.stringify(loaded.errors)}`);
  if (loaded.runtime.pendingProviderRegistrations.length ||
      loaded.runtime.pendingNativeProviderRegistrations.length ||
      loaded.runtime.pendingVirtualModelRegistrations.length ||
      loaded.runtime.mcpServers.list().length) {
    throw new UnsupportedCase("Package registers providers, virtual models, or MCP servers; use its dedicated integration checks");
  }
  const registeredFlags = new Map(loaded.extensions.flatMap((extension) => [...extension.flags]));
  for (const [name, value] of Object.entries(prepared.flags ?? {})) {
    requireValue(registeredFlags.has(name), `Unknown extension flag: ${name}`);
    requireValue(typeof value === registeredFlags.get(name).type, `Wrong type for extension flag: ${name}`);
    loaded.runtime.flagValues.set(name, value);
  }

  const modelRuntime = await sdk.ModelRuntime.create({
    credentials: new ai.InMemoryCredentialStore(),
    modelsPath: null,
    refreshOnCreate: false,
    allowModelNetwork: false,
  });
  const unsupportedOperations = [];
  // No provider registration or auth discovery is needed for the local stream.
  for (const name of [
    "refresh", "getAuth", "checkAuth", "getAvailable", "getAllAvailable", "getAvailableOfType",
    "registerProvider", "registerNativeProvider", "unregisterProvider",
    "registerVirtualModel", "unregisterVirtualModel", "login", "logout",
    "setRuntimeApiKey", "removeRuntimeApiKey",
  ]) {
    if (typeof modelRuntime[name] === "function") {
      modelRuntime[name] = forbidOperation(`ModelRuntime.${name}`, unsupportedOperations);
    }
  }
  const faux = ai.fauxProvider({ provider: "package-test", api: "package-test-api" });
  const { session } = await sdk.createAgentSession({
    cwd: workspace.cwd,
    agentDir: workspace.agentDir,
    modelRuntime,
    model: faux.getModel(),
    thinkingLevel: "off",
    resourceLoader: loader,
    settingsManager,
    sessionManager: sdk.SessionManager.inMemory(workspace.cwd),
    noTools: "builtin",
  });
  session.agent.streamFunction = faux.provider.streamSimple;
  const extensionErrors = [];
  const eventCounts = {};
  let runSignal;
  let abortTimer;
  let abortTriggered = false;
  let targetStarted = false;
  let targetProgress = false;
  const toolCallId = "package-test-call";
  const unsubscribe = session.agent.subscribe((event, signal) => {
    runSignal = signal;
    if (event.toolCallId !== toolCallId) return;
    if (event.type === "tool_execution_update") targetProgress = true;
    if (event.type === "tool_execution_start") {
      targetStarted = true;
      if (prepared.abortAfterMs !== undefined) {
        abortTimer = setTimeout(() => {
          abortTriggered = true;
          session.agent.abort();
        }, prepared.abortAfterMs);
      }
    }
  });
  const unsubscribeSession = session.subscribe((event) => {
    eventCounts[event.type] = (eventCounts[event.type] ?? 0) + 1;
  });
  let toolResult;
  let finalAssistant;
  try {
    await session.bindExtensions({
      mode: "print",
      onError: (error) => extensionErrors.push(error),
      shutdownHandler: forbidOperation("ctx.shutdown", unsupportedOperations),
      commandContextActions: Object.fromEntries(
        ["waitForIdle", "newSession", "fork", "navigateTree", "switchSession", "reload"]
          .map((name) => [name, forbidOperation(`ctx.${name}`, unsupportedOperations)]),
      ),
    });
    if (unsupportedOperations.length) {
      throw new UnsupportedCase(`Unsupported operations requested: ${unsupportedOperations.join(", ")}`);
    }
    requireValue(extensionErrors.length === 0,
      `Extension startup failed: ${JSON.stringify(extensionErrors)}`);
    requireValue(session.getToolDefinition(prepared.tool), `Tool is not registered: ${prepared.tool}`);
    session.setActiveToolsByName([...session.getActiveToolNames(), prepared.tool]);
    requireValue(session.getActiveToolNames().includes(prepared.tool),
      `Tool cannot be activated for a model call: ${prepared.tool}`);
    const args = Object.hasOwn(prepared, "args") ? prepared.args : {};
    faux.setResponses([
      ai.fauxAssistantMessage([ai.fauxToolCall(prepared.tool, args, { id: toolCallId })], { stopReason: "toolUse" }),
      ai.fauxAssistantMessage("Local package test complete."),
    ]);
    await session.agent.prompt("Run the supplied local fixture.");
    toolResult = session.messages.findLast((message) =>
      message.role === "toolResult" && message.toolCallId === toolCallId);
    finalAssistant = session.messages.findLast((message) => message.role === "assistant");
  } finally {
    clearTimeout(abortTimer);
    unsubscribe();
    unsubscribeSession();
    try {
      await session.extensionRunner.emit({ type: "session_shutdown", reason: "quit" });
    } finally {
      session.dispose();
    }
  }
  if (unsupportedOperations.length) {
    throw new UnsupportedCase(`Unsupported operations requested: ${unsupportedOperations.join(", ")}`);
  }

  const aborted = runSignal?.aborted === true;
  const observed = {
    isError: toolResult ? toolResult.isError === true : null,
    aborted,
    targetStarted,
    targetProgress,
    abortTriggered,
    conversationalResponseSource: "in-memory fixture",
    localResponseCount: faux.state.callCount,
    eventCounts,
  };
  const failures = [];
  const check = (condition, message) => { if (!condition) failures.push(message); };
  check(extensionErrors.length === 0, `Extension errors: ${JSON.stringify(extensionErrors)}`);
  if (prepared.expect.aborted !== undefined) {
    check(aborted === prepared.expect.aborted, `Expected aborted=${prepared.expect.aborted}, observed ${aborted}`);
  } else {
    check(!aborted, "Run aborted unexpectedly; declare expect.aborted for a cancellation case");
  }
  if (toolResult) {
    check(typeof toolResult.isError === "boolean", "Final tool result does not contain a boolean isError");
    check(observed.isError === prepared.expect.isError,
      `Expected isError=${prepared.expect.isError}, observed ${observed.isError}`);
  } else {
    check(prepared.expect.aborted === true && aborted, "No finalized tool result was recorded");
    observed.isErrorAssertion = "No tool result; only the expected aborted-run assertion applies";
  }
  if (finalAssistant?.stopReason === "error" && !aborted) {
    failures.push(`Local assistant fixture failed: ${finalAssistant.errorMessage ?? "unknown error"}`);
  }
  const text = (toolResult?.content ?? []).filter((part) => part.type === "text").map((part) => part.text).join("\n");
  observed.textBytes = Buffer.byteLength(text, "utf8");
  observed.textLines = text === "" ? 0 : text.split("\n").length;
  for (const needle of strings(prepared.expect.textIncludes ?? [], "expect.textIncludes")) {
    check(text.includes(needle), `Tool text does not include ${JSON.stringify(needle)}`);
  }
  for (const needle of strings(prepared.expect.textExcludes ?? [], "expect.textExcludes")) {
    check(!text.includes(needle), `Tool text unexpectedly includes ${JSON.stringify(needle)}`);
  }
  if (prepared.expect.maxTextBytes !== undefined) {
    check(observed.textBytes <= prepared.expect.maxTextBytes,
      `Tool text is ${observed.textBytes} bytes; limit is ${prepared.expect.maxTextBytes}`);
  }
  if (prepared.expect.maxTextLines !== undefined) {
    check(observed.textLines <= prepared.expect.maxTextLines,
      `Tool text is ${observed.textLines} lines; limit is ${prepared.expect.maxTextLines}`);
  }
  if (Object.hasOwn(prepared.expect, "details")) {
    try { partialMatch(toolResult?.details, prepared.expect.details); } catch (error) { failures.push(error.message); }
  }
  if (prepared.expect.fullOutputPathDetail !== undefined) {
    try {
      const path = detailAt(toolResult?.details, prepared.expect.fullOutputPathDetail);
      requireValue(typeof path === "string" && isAbsolute(path), "Full-output detail must contain an absolute path");
      const outputPath = await containedFile(path, workspace.root, "full output");
      const output = await readFile(outputPath);
      observed.fullOutputBytes = output.length;
      if (expectedFullOutput !== undefined) {
        check(output.equals(expectedFullOutput), "Full output differs from the expected fixture file");
      }
    } catch (error) {
      failures.push(error.message);
    }
  }
  return {
    name: testCase.name,
    tool: testCase.tool,
    status: failures.length ? "fail" : "pass",
    durationMs: Date.now() - startedAt,
    failures,
    observed,
    warnings: loaded.warnings ?? [],
    limits: LIMITS,
  };
}

function parseArguments(argv) {
  requireValue(argv.length >= 2,
    "Usage: node scripts/test-tools.mjs <package-dir> <cases.json> [--pi-root <path>] [--report <path>] [--timeout-ms <n>]");
  const options = { packageDir: resolve(argv[0]), casesPath: resolve(argv[1]), timeoutMs: DEFAULT_TIMEOUT_MS };
  for (let index = 2; index < argv.length; index += 2) {
    const option = argv[index];
    const value = argv[index + 1];
    requireValue(["--pi-root", "--report", "--timeout-ms"].includes(option) && value !== undefined,
      `Unknown or incomplete option: ${option}`);
    if (option === "--pi-root") options.piRoot = resolve(value);
    if (option === "--report") options.reportPath = resolve(value);
    if (option === "--timeout-ms") {
      options.timeoutMs = Number(value);
      requireValue(Number.isSafeInteger(options.timeoutMs) && options.timeoutMs > 0,
        "--timeout-ms must be a positive integer");
    }
  }
  return options;
}

async function main() {
  const options = parseArguments(process.argv.slice(2));
  const input = JSON.parse(await readFile(options.casesPath, "utf8"));
  if (!Array.isArray(input)) {
    requireValue(isObject(input), "Cases file must be an array or { cases: [...] }");
    rejectUnknown(input, ["cases"], "cases file");
  }
  const cases = Array.isArray(input) ? input : input.cases;
  requireValue(Array.isArray(cases) && cases.length > 0, "At least one test case is required");
  cases.forEach(validateCase);
  requireValue(new Set(cases.map((testCase) => testCase.name)).size === cases.length, "Case names must be unique");
  requireValue((await stat(options.packageDir)).isDirectory(), "package-dir must be a directory");
  const piRoot = await locatePiRoot(options.packageDir, options.piRoot);
  const results = [];
  for (const testCase of cases) {
    const workspace = await createWorkspace("pi-package-tool-test-");
    try {
      const workerInputPath = join(workspace.root, "input.json");
      await writeFile(workerInputPath, JSON.stringify({
        testCase, packageDir: options.packageDir, piRoot, workspace, timeoutMs: options.timeoutMs,
      }));
      const result = spawnSync(process.execPath, [
        fileURLToPath(import.meta.url), "--worker", workerInputPath,
      ], {
        cwd: workspace.cwd,
        env: isolatedEnv({ PI_OFFLINE: "1", PI_CODING_AGENT_DIR: workspace.agentDir, TMPDIR: workspace.root }),
        timeout: options.timeoutMs,
        killSignal: "SIGKILL",
        maxBuffer: MAX_CAPTURE_BYTES,
        encoding: "utf8",
      });
      const outputLines = result.stdout?.split("\n") ?? [];
      const marker = outputLines.findLast((line) => line.startsWith(RESULT_PREFIX));
      if (!result.error && result.status === 0 && marker) {
        const caseResult = JSON.parse(marker.slice(RESULT_PREFIX.length));
        if (outputLines.includes(LINGER_MARKER)) {
          caseResult.failures = [...(caseResult.failures ?? []), LINGER_FAILURE];
          if (caseResult.status === "pass") caseResult.status = "fail";
        }
        results.push(caseResult);
      } else {
        results.push({
          name: testCase.name,
          tool: testCase.tool,
          status: "fail",
          failures: [result.error?.message ?? `Worker exited with status ${result.status}, signal ${result.signal}`],
          diagnostics: result.stderr?.slice(-4000) ?? "",
          limits: LIMITS,
        });
      }
    } finally {
      await rm(workspace.root, { recursive: true, force: true });
    }
  }
  const summary = Object.fromEntries(["pass", "fail", "skipped"].map((status) =>
    [status, results.filter((result) => result.status === status).length]));
  const status = summary.fail > 0 ? "fail" : summary.skipped > 0 ? "incomplete" : "pass";
  const report = { schemaVersion: 1, status, packageDir: options.packageDir, piRoot, summary, cases: results, limits: LIMITS };
  const json = `${JSON.stringify(report, null, 2)}\n`;
  if (options.reportPath) {
    await mkdir(dirname(options.reportPath), { recursive: true });
    await writeFile(options.reportPath, json);
  }
  process.stdout.write(json);
  if (summary.fail > 0) process.exitCode = 1;
  else if (summary.skipped > 0) process.exitCode = 2;
}

if (process.argv[2] === "--worker") {
  let input;
  try {
    input = JSON.parse(await readFile(process.argv[3], "utf8"));
    const result = await runWorker(input);
    process.stdout.write(`${RESULT_PREFIX}${JSON.stringify(result)}\n`);
  } catch (error) {
    process.stdout.write(`${RESULT_PREFIX}${JSON.stringify({
      name: input?.testCase?.name,
      tool: input?.testCase?.tool,
      status: error instanceof UnsupportedCase ? "skipped" : "fail",
      failures: [error.message],
      limits: LIMITS,
    })}\n`);
  }
  // A clean case exits on its own. The unref'd timer fires only if another handle keeps it alive.
  setTimeout(() => {
    // Exit after the write flushes; piped stdout is asynchronous on some platforms.
    process.stdout.write(`${LINGER_MARKER}\n`, () => process.exit(0));
  }, EXIT_GRACE_MS).unref();
} else {
  main().catch((error) => {
    process.stderr.write(`${error.message}\n`);
    process.exitCode = 1;
  });
}
