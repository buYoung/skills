#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import { existsSync, globSync } from "node:fs";
import { lstat, mkdir, readFile, realpath, writeFile } from "node:fs/promises";
import { dirname, isAbsolute, join, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";
import { createWorkspace, importPublic, isolatedEnv, locatePiRoot, readJson } from "./lib/runtime.mjs";
import { validateTheme } from "./lib/theme.mjs";

const TYPES = ["extensions", "skills", "prompts", "themes"];
const HOSTS = ["@earendil-works/pi-ai", "@earendil-works/pi-agent-core", "@earendil-works/pi-coding-agent", "@earendil-works/pi-tui", "typebox"];
const SCRIPT = fileURLToPath(import.meta.url);
const sorted = (values) => [...values].sort();
const portable = (path) => path.split(sep).join("/");
const isObject = (value) => value !== null && typeof value === "object" && !Array.isArray(value);
const checks = [];

function check(name, ok, detail) {
  checks.push({ name, status: ok ? "pass" : "fail", ...(detail === undefined ? {} : { detail }) });
}

function skip(name, detail) {
  checks.push({ name, status: "skipped", detail });
}

function notApplicable(name, detail) {
  checks.push({ name, status: "not_applicable", detail });
}

function recommend(name, ok, detail) {
  checks.push({ name, status: ok ? "pass" : "warning", detail });
}

function same(actual, expected) {
  return JSON.stringify(sorted(actual)) === JSON.stringify(sorted(expected));
}

function safeRelative(path) {
  return typeof path === "string" && path.length > 0 && !isAbsolute(path)
    && !path.split(/[\\/]/).includes("..");
}

function parseArgs(args) {
  if (!args.length || args.includes("--help")) {
    console.log("Usage: node validate-package.mjs <package-dir> [--expect inventory.json] [--runtime] [--pack] [--pi-root installed-pi-root] [--report report.json] [--timeout-ms 30000]");
    process.exit(args.includes("--help") ? 0 : 2);
  }
  const options = { packageDir: resolve(args.shift()), timeoutMs: 30000 };
  while (args.length) {
    const key = args.shift();
    if (["--runtime", "--pack"].includes(key)) options[key.slice(2)] = true;
    else if (["--expect", "--pi-root", "--report", "--timeout-ms"].includes(key) && args.length) {
      const value = args.shift();
      if (key === "--timeout-ms") options.timeoutMs = Number(value);
      else options[{ "--expect": "expectPath", "--pi-root": "piRoot", "--report": "reportPath" }[key]] = resolve(value);
    } else throw new Error(`Unknown option or missing value: ${key}`);
  }
  if (!Number.isInteger(options.timeoutMs) || options.timeoutMs < 1) throw new Error("--timeout-ms must be a positive integer");
  return options;
}

function validateExpectations(expected) {
  if (!isObject(expected)) throw new Error("Inventory must be a JSON object");
  for (const key of ["resources", "names"]) {
    if (expected[key] !== undefined && !isObject(expected[key])) throw new Error(`${key} must be an object`);
  }
  const allowed = { resources: TYPES, names: ["tools", "commands", "flags", "skills", "prompts", "themes"] };
  for (const [group, keys] of Object.entries(allowed)) {
    for (const [key, values] of Object.entries(expected[group] ?? {})) {
      if (!keys.includes(key) || !Array.isArray(values) || values.some((value) => typeof value !== "string")) {
        throw new Error(`Invalid inventory ${group}.${key}`);
      }
    }
  }
  for (const key of ["requiredFiles", "forbiddenFiles"]) {
    if (expected[key] !== undefined && (!Array.isArray(expected[key]) || !expected[key].every(safeRelative))) {
      throw new Error(`${key} must contain package-relative file paths`);
    }
  }
  for (const paths of Object.values(expected.resources ?? {})) {
    if (!paths.every(safeRelative)) throw new Error("Resource inventory paths must stay inside the package");
  }
  for (const key of Object.keys(expected)) {
    if (!["resources", "names", "requiredFiles", "forbiddenFiles"].includes(key)) throw new Error(`Unknown inventory key: ${key}`);
  }
}

async function checkManifest(packageDir, manifest, options) {
  if (manifest === undefined) {
    if (options.pack) check("npm package.json", false, "An npm artifact requires package.json.");
    else notApplicable("package.json metadata", "A local package may use conventional discovery without package.json.");
    return;
  }
  check("package.json object", isObject(manifest));
  if (!isObject(manifest)) return;
  if (options.pack) {
    check("npm package identity", typeof manifest.name === "string" && manifest.name.length > 0 && typeof manifest.version === "string" && manifest.version.length > 0, "An npm artifact needs a name and version; npm checks publishability separately.");
    recommend("gallery discovery keyword", Array.isArray(manifest.keywords) && manifest.keywords.includes("pi-package"), "The pi-package keyword enables gallery discovery; it is not required for package loading or npm packing.");
  } else {
    notApplicable("npm metadata and gallery discovery", "No npm artifact check selected; local loading does not require npm name/version or a gallery keyword.");
  }
  if (manifest.pi?.extensions?.length || existsSync(join(packageDir, "extensions"))) {
    recommend("ES module authoring convention", manifest.type === "module", "type: module is an authoring recommendation. A different or omitted value is not by itself a Pi load error.");
  }
  if (manifest.pi === undefined) {
    notApplicable("explicit resource manifest", "Conventional discovery is valid; runtime inventory establishes its surface.");
  } else {
    check("pi manifest object", isObject(manifest.pi));
    if (isObject(manifest.pi)) {
      for (const type of TYPES) {
        const entries = manifest.pi[type];
        if (entries === undefined) {
          if (existsSync(join(packageDir, type))) {
            recommend(`explicit ${type} boundary`, false, "This field is omitted but a conventional directory exists. Check whether settings filters expose unintended resources.");
          } else {
            notApplicable(`pi.${type}`, "No field or conventional directory for this resource type; providing it is optional.");
          }
          continue;
        }
        check(`pi.${type} string array`, Array.isArray(entries) && entries.every((entry) => typeof entry === "string"));
        if (!Array.isArray(entries)) continue;
        for (const entry of entries.filter((entry) => typeof entry === "string")) {
          const path = /^[!+-]/.test(entry) ? entry.slice(1) : entry;
          check(`${type} portable path: ${entry}`, safeRelative(path));
          if (!safeRelative(path) || /^[!+-]/.test(entry)) continue;
          const matches = /[*?]/.test(path) ? globSync(path, { cwd: packageDir }) : [path].filter((value) => existsSync(resolve(packageDir, value)));
          check(`${type} existing candidate: ${entry}`, matches.length > 0, "Candidate existence only; the Pi runtime decides discovery and filtering.");
          for (const match of matches) {
            const target = await realpath(resolve(packageDir, match));
            check(`${type} contained resource: ${match}`, !relative(packageDir, target).split(sep).includes(".."), "Published resources must not depend on an outside symlink target.");
          }
        }
      }
    }
  }
  for (const host of HOSTS) {
    check(`host not bundled as runtime dependency: ${host}`, !manifest.dependencies?.[host] && !manifest.optionalDependencies?.[host] && !(manifest.bundleDependencies ?? manifest.bundledDependencies ?? []).includes?.(host));
    if (manifest.peerDependencies?.[host] !== undefined) check(`wildcard host peer: ${host}`, manifest.peerDependencies[host] === "*");
  }
  skip("semantic import and bundle inspection", "Review imports for undeclared runtime dependencies, unsupported host subpaths, and bundled host copies. Static checks do not parse TypeScript or compiled bundles.");
}

async function checkFiles(packageDir, expected) {
  for (const file of expected.requiredFiles ?? []) {
    check(`required source file: ${file}`, existsSync(resolve(packageDir, file)));
  }
  for (const file of expected.forbiddenFiles ?? []) {
    check(`forbidden source file absent: ${file}`, !existsSync(resolve(packageDir, file)));
  }
}

async function checkThemes(packageDir, paths) {
  if (paths === undefined) {
    skip("theme contract", "Theme applicability is unknown; supply an inventory or run the Pi resource check.");
    return;
  }
  for (const path of paths) {
    try {
      const value = await readJson(resolve(packageDir, path));
      const errors = validateTheme(value);
      check(`strict bundled theme contract: ${path}`, errors.length === 0, errors);
    } catch (error) {
      check(`strict bundled theme contract: ${path}`, false, String(error));
    }
  }
  if (!paths.length) notApplicable("theme contract", "This package provides no themes; a theme is not required.");
}

async function runtimeWorker(input) {
  const workspace = await createWorkspace();
  process.env.PI_CODING_AGENT_DIR = workspace.agentDir;
  process.env.PI_OFFLINE = "1";
  const sdk = await importPublic(input.piRoot);
  const metadata = await readJson(join(input.piRoot, "package.json"));
  for (const key of ["DefaultResourceLoader", "DefaultPackageManager", "SettingsManager"]) {
    if (typeof sdk[key] !== "function") throw new Error(`Pi ${metadata.version} does not expose required public SDK export ${key}`);
  }
  const settings = sdk.SettingsManager.inMemory({ packages: [] }, { projectTrusted: false });
  const loader = new sdk.DefaultResourceLoader({
    cwd: workspace.cwd, agentDir: workspace.agentDir, settingsManager: settings,
    additionalExtensionPaths: [input.packageDir],
    noExtensions: true, noSkills: true, noPromptTemplates: true, noThemes: true, noContextFiles: true,
  });
  await loader.reload();
  const extensions = loader.getExtensions();
  const diagnostics = [
    ...extensions.errors, ...(extensions.warnings ?? []),
    ...loader.getSkills().diagnostics, ...loader.getPrompts().diagnostics, ...loader.getThemes().diagnostics,
  ];
  const names = {
    tools: extensions.extensions.flatMap((entry) => [...entry.tools.keys()]),
    commands: extensions.extensions.flatMap((entry) => [...entry.commands.keys()]),
    flags: extensions.extensions.flatMap((entry) => [...entry.flags.keys()]),
    skills: loader.getSkills().skills.map((entry) => entry.name),
    prompts: loader.getPrompts().prompts.map((entry) => entry.name),
    themes: loader.getThemes().themes.map((entry) => entry.name),
  };
  async function selection(entry) {
    const manager = new sdk.DefaultPackageManager({
      cwd: workspace.cwd, agentDir: workspace.agentDir,
      settingsManager: sdk.SettingsManager.inMemory({ packages: [entry] }, { projectTrusted: false }),
    });
    const resolved = await manager.resolve();
    const inventory = {};
    for (const type of TYPES) {
      const paths = [];
      for (const resource of resolved[type]) {
        if (!resource.enabled || !resource.metadata.packageRoot) continue;
        if (await realpath(resource.metadata.packageRoot) !== input.packageDir) continue;
        paths.push(portable(relative(input.packageDir, resource.path)));
      }
      inventory[type] = sorted(paths);
    }
    return inventory;
  }
  const resources = await selection(input.packageDir);
  const objectResources = await selection({ source: input.packageDir });
  const filterChecks = [{ name: "string/object resource parity", ok: TYPES.every((type) => same(resources[type], objectResources[type])), actual: objectResources }];
  const wildcardResources = await selection({ source: input.packageDir, ...Object.fromEntries(TYPES.map((type) => [type, ["*"]])) });
  filterChecks.push({ name: "wildcard filters expose no extra resources", ok: TYPES.every((type) => same(resources[type], wildcardResources[type])), actual: wildcardResources });
  for (const type of TYPES) {
    if (objectResources[type].length === 0) {
      filterChecks.push({ name: `disable only ${type}`, status: "not_applicable", detail: "No resources of this type to disable." });
      continue;
    }
    const disabled = await selection({ source: input.packageDir, [type]: [] });
    filterChecks.push({
      name: `disable only ${type}`,
      ok: disabled[type].length === 0 && TYPES.filter((other) => other !== type).every((other) => same(disabled[other], objectResources[other])),
      actual: disabled,
    });
  }
  return { version: metadata.version, node: process.version, workspace: workspace.root, diagnostics, names, resources, filterChecks };
}

async function runRuntime(options) {
  const scratch = await createWorkspace();
  const inputPath = join(scratch.root, "input.json");
  const resultPath = join(scratch.root, "runtime.json");
  await writeFile(inputPath, JSON.stringify({ packageDir: options.packageDir, piRoot: options.piRoot, resultPath }));
  const child = spawnSync(process.execPath, [SCRIPT, "--worker", inputPath], {
    encoding: "utf8", timeout: options.timeoutMs, maxBuffer: 2 * 1024 * 1024,
    killSignal: "SIGKILL",
    cwd: scratch.cwd, env: isolatedEnv({ PI_CODING_AGENT_DIR: scratch.agentDir }),
  });
  check("Pi resource worker completed", child.status === 0 && existsSync(resultPath), child.error?.message ?? (child.status !== 0 ? child.stderr || child.stdout : undefined));
  if (!existsSync(resultPath)) return undefined;
  const result = await readJson(resultPath);
  if (result.error) {
    check("Pi runtime load", false, result.error);
    return undefined;
  }
  check("Pi resource diagnostics", result.diagnostics.length === 0, result.diagnostics);
  for (const item of result.filterChecks) {
    if (item.status === "not_applicable") notApplicable(item.name, item.detail);
    else check(item.name, item.ok, item.ok ? undefined : item.actual);
  }
  // relative(packageDir, packageDir) is "": Pi resolved the package directory itself as an extension.
  if (result.resources.extensions.includes("")) {
    check("no implicit package-directory extension", false, "No pi manifest entry or conventional resource directory exists, so Pi loaded the package directory itself through its root index file. Only a local string-form source uses that fallback; npm and git installs and object-form settings entries load nothing. Declare pi.extensions or move the entry to extensions/.");
  }
  return result;
}

async function packPackage(options, expected) {
  const workspace = await createWorkspace("pi-package-pack-");
  const packDir = join(workspace.root, "archive");
  await mkdir(packDir);
  const child = spawnSync("npm", ["pack", "--ignore-scripts", "--json", "--pack-destination", packDir, "--cache", join(workspace.root, "npm-cache")], {
    cwd: options.packageDir, env: isolatedEnv(), encoding: "utf8", timeout: options.timeoutMs, maxBuffer: 4 * 1024 * 1024,
  });
  check("npm pack", child.status === 0, child.error?.message ?? (child.status !== 0 ? child.stderr : undefined));
  if (child.status !== 0) return undefined;
  const output = JSON.parse(child.stdout);
  if (output.length !== 1) throw new Error("Expected one npm package; run this command from the actual package directory, not a multi-package workspace root.");
  const info = output[0];
  const packedFiles = info.files.map((file) => file.path);
  const required = new Set([...(expected.requiredFiles ?? []), ...Object.values(expected.resources ?? {}).flat()]);
  for (const file of required) check(`packed file: ${file}`, packedFiles.includes(file.replace(/^\.\//, "")));
  for (const file of expected.forbiddenFiles ?? []) check(`forbidden packed file absent: ${file}`, !packedFiles.includes(file));
  const extractionDir = join(workspace.root, "extracted");
  await mkdir(extractionDir);
  const archive = resolve(packDir, info.filename);
  const extracted = spawnSync("tar", ["-xzf", archive, "-C", extractionDir], { encoding: "utf8", timeout: options.timeoutMs, env: isolatedEnv() });
  check("archive extraction (system tar)", extracted.status === 0, extracted.error?.message ?? (extracted.status !== 0 ? extracted.stderr : undefined));
  const packageDir = join(extractionDir, "package");
  if (extracted.status === 0) {
    for (const file of required) {
      const source = resolve(options.packageDir, file);
      const target = resolve(packageDir, file);
      if (existsSync(source) && existsSync(target) && (await lstat(source)).isFile()) {
        check(`packed contents unchanged: ${file}`, (await readFile(source)).equals(await readFile(target)));
      }
    }
  }
  skip("extracted artifact runtime and behavior", `Repeat validation and tool tests with packageDir=${packageDir}. Install declared production dependencies there first when needed; this command never installs dependencies.`);
  return { archive, packageDir, files: packedFiles };
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  options.packageDir = await realpath(options.packageDir);
  const expected = options.expectPath ? await readJson(options.expectPath) : {};
  validateExpectations(expected);
  const manifestPath = join(options.packageDir, "package.json");
  const manifest = existsSync(manifestPath) ? await readJson(manifestPath) : undefined;
  await checkManifest(options.packageDir, manifest, options);
  await checkFiles(options.packageDir, expected);
  let runtime;
  if (options.runtime) {
    try {
      options.piRoot = await locatePiRoot(options.packageDir, options.piRoot);
      runtime = await runRuntime(options);
    } catch (error) {
      check("target Pi runtime available", false, String(error));
    }
  } else skip("Pi runtime load, names, and filters", "Use --runtime with the installed target Pi.");
  if (runtime) {
    for (const [group, actual] of [["resources", runtime.resources], ["names", runtime.names]]) {
      for (const [key, values] of Object.entries(expected[group] ?? {})) {
        check(`exact ${group}.${key} inventory`, same(actual[key], values), { expected: values, actual: actual[key] });
      }
    }
  }
  if (!options.expectPath) skip("intent inventory", "Provide --expect to detect silently missing resources and names. A diagnostic-free load is not evidence of completeness.");
  await checkThemes(options.packageDir, runtime?.resources.themes ?? expected.resources?.themes);
  const artifact = options.pack ? await packPackage(options, expected) : undefined;
  if (!options.pack) notApplicable("packed artifact", "No npm artifact check selected; use --pack for npm delivery or a requested tarball.");
  const report = {
    status: checks.some((item) => item.status === "fail") ? "fail" : "pass",
    scope: "Requested resource inventory and applicable structure/loading/filtering checks. Theme checks apply only to provided themes; --pack selects npm artifact checks. This is not a complete behavioral test.",
    packageDir: options.packageDir, checks, runtime, artifact,
    limits: [
      "Factories execute with process access. Environment filtering and resource isolation are not a security sandbox.",
      "No live model, provider, MCP, command/UI, prompt expansion, live session reload, project trust, registry, or git-update check.",
      "The theme authoring check rejects invalid unused variables, export colors, and reserved built-in names even when Pi may defer or tolerate them.",
      "No TypeScript compiler, full import analysis, arbitrary custom integration checks, or proof of dependency freshness.",
    ],
  };
  if (options.reportPath) {
    await mkdir(dirname(options.reportPath), { recursive: true });
    await writeFile(options.reportPath, JSON.stringify(report, null, 2) + "\n");
  }
  console.log(JSON.stringify(report, null, 2));
  process.exitCode = report.status === "fail" ? 1 : 0;
}

if (process.argv[2] === "--worker") {
  const input = await readJson(process.argv[3]);
  try {
    await writeFile(input.resultPath, JSON.stringify(await runtimeWorker(input), null, 2));
    process.exit(0); // Factories may leave timers; this worker is a bounded load check.
  } catch (error) {
    await writeFile(input.resultPath, JSON.stringify({ error: String(error) }));
    process.exit(1);
  }
} else {
  main().catch((error) => {
    console.error(String(error));
    process.exitCode = 2;
  });
}
