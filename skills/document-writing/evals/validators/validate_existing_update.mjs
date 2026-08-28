#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";

const [, , fixtureArg, resultArg, ...extraArgs] = process.argv;
if (!fixtureArg || !resultArg || extraArgs.length > 0) {
  console.error("Usage: node validate_existing_update.mjs <fixture-root> <result-root>");
  process.exit(2);
}

function requireRoot(label, value) {
  const resolved = path.resolve(value);
  if (!fs.existsSync(resolved)) throw new Error(`${label} root is missing: ${resolved}`);
  const stat = fs.lstatSync(resolved);
  if (stat.isSymbolicLink() || !stat.isDirectory()) throw new Error(`${label} root is not a real directory: ${resolved}`);
  return { resolved, real: fs.realpathSync(resolved) };
}

function isOutside(left, right) {
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
    } else throw new Error(`Special file is not allowed: ${relative}`);
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
  if (!isOutside(fixture.real, result.real) || !isOutside(result.real, fixture.real)) throw new Error("fixture and result roots must be distinct, non-nested directories");
  fixtureTree = collectTree(fixture.resolved);
  resultTree = collectTree(result.resolved);
  if (![...fixtureTree.values()].some((item) => item.type === "file") || ![...resultTree.values()].some((item) => item.type === "file")) throw new Error("fixture and result roots must each contain at least one file");
  if (fixtureTree.get("index.md")?.type !== "file") throw new Error("fixture must contain index.md");
} catch (error) {
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(2);
}

const expectations = [];
for (const [relative, item] of fixtureTree) {
  const output = resultTree.get(relative);
  if (item.type === "directory") {
    expectations.push({ text: `Preserve directory ${relative}`, passed: output?.type === "directory", evidence: output?.type === "directory" ? "Directory remains" : "Directory was removed or replaced" });
    continue;
  }
  if (relative === "index.md") continue;
  const passed = output?.type === "file" && item.content.equals(output.content);
  expectations.push({ text: `Preserve ${relative} byte-for-byte`, passed, evidence: passed ? `${relative} is unchanged` : `${relative} changed, is missing, or has the wrong type` });
}

const fixtureIndex = fixtureTree.get("index.md").content;
const resultIndex = resultTree.get("index.md");
const fixtureIndexLines = fixtureIndex.toString("utf8").split(/\r?\n/).filter((line) => line.trim().length > 0);
const resultIndexLines = resultIndex?.type === "file" ? resultIndex.content.toString("utf8").split(/\r?\n/) : [];
let sourceLine = 0;
for (const line of resultIndexLines) {
  if (line === fixtureIndexLines[sourceLine]) sourceLine += 1;
}
const indexPreservesOrderedContent = sourceLine === fixtureIndexLines.length;
expectations.push({ text: "Extend index.md without rewriting its existing content", passed: indexPreservesOrderedContent, evidence: indexPreservesOrderedContent ? "Every existing non-empty index line remains intact and ordered" : "Existing index content was rewritten or removed" });

const resultIndexText = resultIndex?.type === "file" ? resultIndex.content.toString("utf8") : "";
for (const relative of ["content.md", "accessibility.md"]) {
  const owner = resultTree.get(relative);
  const text = owner?.type === "file" ? owner.content.toString("utf8") : "";
  const hasPurpose = /^#\s+[^\s].{2,}$/m.test(text);
  const hasOwnedGuidance = /\b(must|should|avoid|provide|use|ensure|do not|must not)\b/i.test(text) || /[가-힣].{40,}/.test(text);
  const hasLinkedIndex = new RegExp(`\\]\\(${relative.replace(".", "\\.")}(?:#[^)]+)?\\)`).test(resultIndexText);
  const passed = text.trim().length >= 160 && hasPurpose && hasOwnedGuidance && hasLinkedIndex;
  expectations.push({ text: `Create a meaningful, indexed ${relative} owner document`, passed, evidence: passed ? `${relative} has substantive owned guidance and an index link` : `length=${text.trim().length} heading=${hasPurpose} guidance=${hasOwnedGuidance} linked=${hasLinkedIndex}` });
}

const expectedFiles = new Set([...fixtureTree.entries()].filter(([, value]) => value.type === "file").map(([key]) => key).concat(["content.md", "accessibility.md"]));
const resultFiles = [...resultTree.entries()].filter(([, value]) => value.type === "file").map(([key]) => key);
const onlyRequestedFiles = resultFiles.length === expectedFiles.size && resultFiles.every((relative) => expectedFiles.has(relative));
expectations.push({ text: "Create only the two requested owner files", passed: onlyRequestedFiles, evidence: onlyRequestedFiles ? "No unexpected file was added" : `result files=${JSON.stringify(resultFiles.sort())}` });

console.log(JSON.stringify({ expectations }, null, 2));
process.exit(expectations.every((item) => item.passed) ? 0 : 1);
