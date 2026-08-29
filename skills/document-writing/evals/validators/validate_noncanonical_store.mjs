#!/usr/bin/env node

import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";

const [, , fixtureArg, resultArg, ...extraArgs] = process.argv;
if (!fixtureArg || !resultArg || extraArgs.length > 0) {
  console.error("Usage: node validate_noncanonical_store.mjs <fixture-root> <result-root>");
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

function collectTree(root, current = root, files = []) {
  for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
    const absolute = path.join(current, entry.name);
    const relative = path.relative(root, absolute).split(path.sep).join("/");
    const stat = fs.lstatSync(absolute);
    if (stat.isSymbolicLink()) throw new Error(`Symbolic link is not allowed: ${relative}`);
    if (stat.isDirectory()) collectTree(root, absolute, files);
    else if (stat.isFile()) files.push(relative);
    else throw new Error(`Special file is not allowed: ${relative}`);
  }
  return files.sort();
}

function normalizedMeaning(content) {
  return content.replace(/^\s*<!--[\s\S]*?-->\s*$/gm, "").replace(/\s+/g, " ").trim();
}

function ownerIdentity(relative, content) {
  const frontmatter = content.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  const owner = frontmatter?.[1].match(/^\s*(?:storefront|store|owner|platform)\s*:\s*["']?([^\n"']+)/mi)?.[1];
  const heading = content.match(/^#\s+(.+?)\s*$/m)?.[1];
  const ref = relative.toLowerCase().replace(/\.(md|mdx|markdown)$/i, "");
  return [owner, heading, ref].filter(Boolean).join(" ").toLowerCase().replace(/[^a-z0-9]+/g, " ");
}

let fixture;
let result;
let fixtureFiles;
let resultFiles;
try {
  fixture = requireRoot("fixture", fixtureArg);
  result = requireRoot("result", resultArg);
  if (!isOutside(fixture.real, result.real) || !isOutside(result.real, fixture.real)) throw new Error("fixture and result roots must be distinct, non-nested directories");
  fixtureFiles = collectTree(fixture.resolved);
  resultFiles = collectTree(result.resolved);
  if (fixtureFiles.length === 0 || resultFiles.length === 0) throw new Error("fixture and result roots must each contain files");
} catch (error) {
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(2);
}

const existingRelative = "stores/play-store-assets.md";
const fixturePath = path.join(fixture.resolved, existingRelative);
const existingPath = path.join(result.resolved, existingRelative);
const indexPath = path.join(result.resolved, "index.md");
if (!fs.existsSync(fixturePath) || !fs.lstatSync(fixturePath).isFile() || !fs.existsSync(existingPath) || !fs.lstatSync(existingPath).isFile() || !fs.existsSync(indexPath) || !fs.lstatSync(indexPath).isFile()) {
  console.error("fixture/result must contain index.md and stores/play-store-assets.md regular files");
  process.exit(2);
}

const fixtureContent = fs.readFileSync(fixturePath, "utf8");
const existingContent = fs.readFileSync(existingPath, "utf8");
const indexContent = fs.readFileSync(indexPath, "utf8");
const duplicatePaths = [];
for (const relative of resultFiles.filter((item) => /\.(md|mdx|markdown)$/i.test(item))) {
  if (relative === existingRelative) continue;
  const identity = ownerIdentity(relative, fs.readFileSync(path.join(result.resolved, relative), "utf8"));
  if (identity.includes("google play") || identity.includes("play store") || identity.includes("googleplay") || identity.includes("playstore")) duplicatePaths.push(relative);
}

const unrelatedFixtureFiles = fixtureFiles.filter((relative) => relative !== existingRelative);
const unrelatedPreserved = unrelatedFixtureFiles.every((relative) => {
  const fixtureFile = path.join(fixture.resolved, relative);
  const resultFile = path.join(result.resolved, relative);
  return fs.existsSync(resultFile) && fs.lstatSync(resultFile).isFile() && fs.readFileSync(fixtureFile).equals(fs.readFileSync(resultFile));
});
const meaningfulChanged = normalizedMeaning(fixtureContent) !== normalizedMeaning(existingContent);
const preservesScreenshotPurpose = /screenshots?[\s\S]{0,180}(?:signed-in|in-app|product|app)[\s\S]{0,180}(?:experience|interface|screen|use)/i.test(existingContent);
const preservesClaimIntegrity = /claims?[\s\S]{0,180}(?:consistent|match|align)[\s\S]{0,180}(?:listing|review|package|product)/i.test(existingContent);
const protectedMeaningPreserved = preservesScreenshotPurpose && preservesClaimIntegrity;
const hasOfficialSource = /https:\/\/(?:support\.google\.com|developer\.android\.com)\//i.test(existingContent);
const hasVerificationDate = /(?:^|[^0-9])20\d{2}-\d{2}-\d{2}(?=$|[^0-9])/m.test(existingContent);
const hasSubstantiveUpdate = meaningfulChanged && protectedMeaningPreserved && hasOfficialSource && hasVerificationDate;
const outputIdentity = ownerIdentity(existingRelative, existingContent);
const indexLinksOwner = /\]\(stores\/play-store-assets\.md(?:#[^)]+)?\)/i.test(indexContent);
const ownerHasStorefrontMetadata = outputIdentity.includes("google play") || /\bgoogle\s+play\b/i.test(existingContent);
const expectedFiles = new Set(fixtureFiles);
const noUnexpectedFiles = resultFiles.length === expectedFiles.size && resultFiles.every((relative) => expectedFiles.has(relative));
const expectations = [
  { text: "Reuse the established non-canonical storefront path", passed: ownerHasStorefrontMetadata && indexLinksOwner, evidence: ownerHasStorefrontMetadata && indexLinksOwner ? "The existing path owns Google Play and index.md links it" : "The owner identity or index link is missing" },
  { text: "Make a source-backed storefront update without deleting protected meaning", passed: hasSubstantiveUpdate, evidence: hasSubstantiveUpdate ? `Asset-role meaning remains and official source/date were added (${crypto.createHash("sha256").update(normalizedMeaning(existingContent)).digest("hex").slice(0, 12)})` : `changed=${meaningfulChanged} meaning=${protectedMeaningPreserved} officialSource=${hasOfficialSource} verificationDate=${hasVerificationDate}` },
  { text: "Preserve all unrelated existing files", passed: unrelatedPreserved, evidence: unrelatedPreserved ? "All unrelated fixture files are byte-for-byte preserved" : "An unrelated fixture file changed, disappeared, or changed type" },
  { text: "Do not create another storefront owner", passed: duplicatePaths.length === 0 && noUnexpectedFiles, evidence: duplicatePaths.length === 0 && noUnexpectedFiles ? "No duplicate owner or unexpected document was added" : `duplicates=${JSON.stringify(duplicatePaths)} result=${JSON.stringify(resultFiles)}` },
];

console.log(JSON.stringify({ expectations }, null, 2));
process.exit(expectations.every((item) => item.passed) ? 0 : 1);
