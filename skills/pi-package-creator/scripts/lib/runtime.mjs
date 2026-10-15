import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { mkdir, mkdtemp, readFile, realpath } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const PI_PACKAGE = "@earendil-works/pi-coding-agent";

export async function readJson(path) {
  return JSON.parse((await readFile(path, "utf8")).replace(/^\uFEFF/, ""));
}

function ancestors(start) {
  const result = [];
  for (let dir = resolve(start); ; dir = dirname(dir)) {
    result.push(dir);
    if (dirname(dir) === dir) return result;
  }
}

export async function locatePiRoot(packageDir, explicitRoot) {
  const candidates = explicitRoot
    ? [resolve(explicitRoot)]
    : ancestors(packageDir).map((dir) => join(dir, "node_modules", PI_PACKAGE));
  if (!explicitRoot) {
    for (const command of ["npm", "pnpm"]) {
      const result = spawnSync(command, ["root", "-g"], {
        encoding: "utf8", timeout: 10000, env: isolatedEnv(),
      });
      if (result.status === 0 && result.stdout.trim()) {
        candidates.push(join(result.stdout.trim(), PI_PACKAGE));
      }
    }
  }
  for (const candidate of candidates) {
    try {
      const root = await realpath(candidate);
      if ((await readJson(join(root, "package.json"))).name === PI_PACKAGE) return root;
    } catch {}
  }
  throw new Error("Installed Pi SDK not found. Pass --pi-root /absolute/path/to/node_modules/@earendil-works/pi-coding-agent. Nothing was downloaded.");
}

export async function locatePeerRoot(piRoot, packageName) {
  for (const ancestor of ancestors(await realpath(piRoot))) {
    const candidate = join(ancestor, "node_modules", packageName);
    if (existsSync(join(candidate, "package.json"))) return realpath(candidate);
  }
  throw new Error(`Cannot locate installed host peer ${packageName} beside ${piRoot}`);
}

function importTarget(value) {
  if (typeof value === "string") return value;
  if (!value || typeof value !== "object" || Array.isArray(value)) return undefined;
  for (const [condition, target] of Object.entries(value)) {
    if (["node", "import", "default"].includes(condition)) {
      const selected = importTarget(target);
      if (selected) return selected;
    }
  }
  return undefined;
}

export async function importPublic(packageRoot) {
  const manifest = await readJson(join(packageRoot, "package.json"));
  const exports = manifest.exports;
  const target = exports
    ? importTarget(typeof exports === "object" && "." in exports ? exports["."] : exports)
    : manifest.main ?? "./index.js";
  if (!target) throw new Error(`${manifest.name} has no supported public import entry`);
  return import(pathToFileURL(resolve(packageRoot, target)).href);
}

export function isolatedEnv(extra = {}) {
  const env = {};
  for (const key of ["PATH", "Path", "SystemRoot", "WINDIR", "ComSpec", "PATHEXT", "TMPDIR", "TMP", "TEMP", "LANG", "LC_ALL", "TERM"]) {
    if (process.env[key] !== undefined) env[key] = process.env[key];
  }
  return { ...env, PI_OFFLINE: "1", ...extra };
}

export async function createWorkspace(prefix = "pi-package-check-") {
  const root = await mkdtemp(join(tmpdir(), prefix));
  const cwd = join(root, "work");
  const agentDir = join(root, "agent");
  await Promise.all([mkdir(cwd), mkdir(agentDir)]);
  return { root, cwd, agentDir };
}
