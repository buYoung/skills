#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";

const [, , fixtureArg, resultArg, ...optionArgs] = process.argv;
if (!fixtureArg || !resultArg) {
  console.error("Usage: node validate_preservation.mjs <fixture-root> <result-root> [--exact-tree] [--allow-change=<relative-path>]");
  process.exit(2);
}

const isExactTree = optionArgs.includes("--exact-tree");
const invalidOptions = optionArgs.filter((value) => value !== "--exact-tree" && !value.startsWith("--allow-change="));
if (invalidOptions.length > 0 || (isExactTree && optionArgs.some((value) => value.startsWith("--allow-change=")))) {
  console.error("Use only --exact-tree or --allow-change=<relative-path> options, not both");
  process.exit(2);
}

function normalizedRelative(value) {
  const normalized = value.replaceAll("\\", "/");
  if (!normalized || normalized.startsWith("/") || normalized.split("/").some((part) => !part || part === "." || part === "..")) {
    throw new Error(`Invalid relative path: ${value}`);
  }
  return normalized;
}

let allowedChanges;
try {
  allowedChanges = new Set(optionArgs.filter((value) => value.startsWith("--allow-change=")).map((value) => normalizedRelative(value.slice("--allow-change=".length))));
} catch (error) {
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(2);
}

function requireRoot(label, value) {
  const resolved = path.resolve(value);
  if (!fs.existsSync(resolved)) throw new Error(`${label} root is missing: ${resolved}`);
  const stat = fs.lstatSync(resolved);
  if (stat.isSymbolicLink() || !stat.isDirectory()) throw new Error(`${label} root is not a real directory: ${resolved}`);
  return { resolved, real: fs.realpathSync(resolved) };
}

function areDistinctAndNonNested(left, right) {
  const relative = path.relative(left, right);
  return left !== right && relative.startsWith("..") && !path.isAbsolute(relative);
}

function collectTree(root, current = root, items = new Map()) {
  for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
    const absolute = path.join(current, entry.name);
    const relative = path.relative(root, absolute).split(path.sep).join("/");
    const stat = fs.lstatSync(absolute);
    if (stat.isSymbolicLink()) throw new Error(`Symbolic link is not allowed: ${relative}`);
    if (stat.isDirectory()) {
      items.set(relative, { type: "directory" });
      collectTree(root, absolute, items);
    } else if (stat.isFile()) {
      items.set(relative, { type: "file", content: fs.readFileSync(absolute) });
    } else {
      throw new Error(`Special file is not allowed: ${relative}`);
    }
  }
  return items;
}

let fixture;
let result;
let fixtureTree;
let resultTree;
try {
  fixture = requireRoot("fixture", fixtureArg);
  result = requireRoot("result", resultArg);
  if (!areDistinctAndNonNested(fixture.real, result.real) || !areDistinctAndNonNested(result.real, fixture.real)) {
    throw new Error("fixture and result roots must be distinct, non-nested directories");
  }
  fixtureTree = collectTree(fixture.resolved);
  resultTree = collectTree(result.resolved);
  if (![...fixtureTree.values()].some((item) => item.type === "file")) throw new Error(`fixture root contains no files: ${fixture.resolved}`);
  if (![...resultTree.values()].some((item) => item.type === "file")) throw new Error(`result root contains no files: ${result.resolved}`);
} catch (error) {
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(2);
}

const expectations = [];
for (const [relative, item] of fixtureTree) {
  const output = resultTree.get(relative);
  if (item.type === "directory") {
    expectations.push({ text: `Preserve directory ${relative}`, passed: output?.type === "directory", evidence: output?.type === "directory" ? "Directory remains" : "Directory was removed or replaced" });
  } else if (allowedChanges.has(relative)) {
    expectations.push({ text: `Keep allowed-to-change file ${relative} present`, passed: output?.type === "file", evidence: output?.type === "file" ? "File remains" : "File was removed or replaced" });
  } else {
    const passed = output?.type === "file" && item.content.equals(output.content);
    expectations.push({ text: `Preserve ${relative} byte-for-byte`, passed, evidence: passed ? `${relative} is unchanged` : `${relative} changed, is missing, or has the wrong type` });
  }
}

if (isExactTree) {
  const fixturePaths = [...fixtureTree.keys()].sort();
  const resultPaths = [...resultTree.keys()].sort();
  const passed = JSON.stringify(fixturePaths) === JSON.stringify(resultPaths) && fixturePaths.every((relative) => fixtureTree.get(relative)?.type === resultTree.get(relative)?.type);
  expectations.push({ text: "Preserve the complete tree", passed, evidence: passed ? "No path was created, deleted, renamed, or type-changed" : `fixture=${JSON.stringify(fixturePaths)} result=${JSON.stringify(resultPaths)}` });
}

console.log(JSON.stringify({ expectations }, null, 2));
process.exit(expectations.every((item) => item.passed) ? 0 : 1);
