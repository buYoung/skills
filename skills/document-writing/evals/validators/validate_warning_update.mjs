#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";

const [, , fixtureArg, resultArg, ...extraArgs] = process.argv;
if (!fixtureArg || !resultArg || extraArgs.length > 0) {
  console.error("Usage: node validate_warning_update.mjs <fixture-root> <result-root>");
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

function collectFiles(root, current = root, files = new Map()) {
  for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
    const absolute = path.join(current, entry.name);
    const relative = path.relative(root, absolute).split(path.sep).join("/");
    const stat = fs.lstatSync(absolute);
    if (stat.isSymbolicLink()) throw new Error(`Symbolic link is not allowed: ${relative}`);
    if (stat.isDirectory()) collectFiles(root, absolute, files);
    else if (stat.isFile()) files.set(relative, fs.readFileSync(absolute));
    else throw new Error(`Special file is not allowed: ${relative}`);
  }
  return files;
}

let fixture;
let result;
let fixtureFiles;
let resultFiles;
try {
  fixture = requireRoot("fixture", fixtureArg);
  result = requireRoot("result", resultArg);
  if (!areDistinctAndNonNested(fixture.real, result.real) || !areDistinctAndNonNested(result.real, fixture.real)) {
    throw new Error("fixture and result roots must be distinct, non-nested directories");
  }
  fixtureFiles = collectFiles(fixture.resolved);
  resultFiles = collectFiles(result.resolved);
  if (fixtureFiles.size === 0 || resultFiles.size === 0) throw new Error("fixture and result roots must each contain files");
} catch (error) {
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(2);
}

const tokenPath = "tokens.md";
const alertPath = "components/alert.md";
const expectedPaths = [...fixtureFiles.keys()].sort();
const actualPaths = [...resultFiles.keys()].sort();
const exactTree = JSON.stringify(expectedPaths) === JSON.stringify(actualPaths);

function text(files, relative) {
  const value = files.get(relative);
  return value ? value.toString("utf8") : "";
}

function replaceOnce(source, before, after) {
  const first = source.indexOf(before);
  if (first < 0 || source.indexOf(before, first + before.length) >= 0) return null;
  return `${source.slice(0, first)}${after}${source.slice(first + before.length)}`;
}

const fixtureTokens = text(fixtureFiles, tokenPath);
const resultTokens = text(resultFiles, tokenPath);
const expectedTokens = replaceOnce(fixtureTokens, "#E5A000", "#D97706");
const fixtureAlert = text(fixtureFiles, alertPath);
const resultAlert = text(resultFiles, alertPath);
const expectedAlert = replaceOnce(fixtureAlert, "#E5A000", "#D97706");

const tokensChangedExactly = expectedTokens !== null && resultTokens === expectedTokens;
const alertChangedExactly = expectedAlert !== null && resultAlert === expectedAlert;
const protectedPaths = expectedPaths.filter((relative) => relative !== tokenPath && relative !== alertPath);
const protectedPreserved = protectedPaths.every((relative) => {
  const fixtureValue = fixtureFiles.get(relative);
  const resultValue = resultFiles.get(relative);
  return fixtureValue !== undefined && resultValue !== undefined && fixtureValue.equals(resultValue);
});
const oldValueRemoved = !resultTokens.includes("#E5A000") && !resultAlert.includes("#E5A000");
const newValuePropagated = resultTokens.includes("#D97706") && resultAlert.includes("#D97706");

const expectations = [
  {
    text: "Preserve the exact document tree",
    passed: exactTree,
    evidence: exactTree ? "No file or directory was created, removed, or renamed" : `fixture=${JSON.stringify(expectedPaths)} result=${JSON.stringify(actualPaths)}`,
  },
  {
    text: "Change only the canonical warning token value",
    passed: tokensChangedExactly,
    evidence: tokensChangedExactly ? "tokens.md contains the single approved replacement" : "tokens.md differs beyond the approved #E5A000 to #D97706 replacement",
  },
  {
    text: "Propagate the warning value to the final alert consumer",
    passed: alertChangedExactly && oldValueRemoved && newValuePropagated,
    evidence: alertChangedExactly && oldValueRemoved && newValuePropagated ? "components/alert.md records #D97706 and no stale warning value remains" : `alertExact=${alertChangedExactly} oldRemoved=${oldValueRemoved} newPropagated=${newValuePropagated}`,
  },
  {
    text: "Preserve unrelated direction, approval, and component files byte-for-byte",
    passed: protectedPreserved,
    evidence: protectedPreserved ? `Preserved ${protectedPaths.join(", ")}` : "At least one protected file changed or disappeared",
  },
];

console.log(JSON.stringify({ expectations }, null, 2));
process.exit(expectations.every((item) => item.passed) ? 0 : 1);
