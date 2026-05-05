#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");

const ROOT = path.resolve(__dirname, "..", "..");
const MARKETPLACE_PATH = path.join(ROOT, ".claude-plugin", "marketplace.json");

function fail(message) {
  process.stderr.write(`[bump-marketplace] ${message}\n`);
  process.exit(1);
}

function replaceMetadataVersion(raw, version) {
  const metadataRegex = /("metadata"\s*:\s*\{)([\s\S]*?)(\})/;
  const metadataMatch = raw.match(metadataRegex);
  if (!metadataMatch) {
    fail("could not locate metadata block in marketplace.json");
  }

  const versionRegex = /("version"\s*:\s*")([^"]*)(")/;
  const inner = metadataMatch[2];
  const versionMatch = inner.match(versionRegex);
  if (!versionMatch) {
    fail("could not locate metadata.version in marketplace.json");
  }

  const oldVersion = versionMatch[2];
  if (oldVersion === version) return { raw, oldVersion, changed: false };

  const newInner = inner.replace(versionRegex, `$1${version}$3`);
  const newRaw = raw.replace(
    metadataRegex,
    `${metadataMatch[1]}${newInner}${metadataMatch[3]}`
  );
  return { raw: newRaw, oldVersion, changed: true };
}

function main() {
  const [, , versionArg] = process.argv;
  const version = (versionArg || "").trim();
  if (!version) {
    fail("Usage: bump-marketplace.js <version>");
  }
  if (!/^[0-9A-Za-z.\-+]+$/.test(version)) {
    fail(`refusing unsafe version string: ${version}`);
  }
  if (!fs.existsSync(MARKETPLACE_PATH)) {
    fail(`${path.relative(ROOT, MARKETPLACE_PATH)} not found.`);
  }

  const raw = fs.readFileSync(MARKETPLACE_PATH, "utf8");
  const { raw: next, oldVersion, changed } = replaceMetadataVersion(raw, version);

  if (!changed) {
    process.stdout.write(`[bump-marketplace] already at ${version}, no change.\n`);
    return;
  }

  fs.writeFileSync(MARKETPLACE_PATH, next, "utf8");
  process.stdout.write(`[bump-marketplace] ${oldVersion} -> ${version}\n`);
}

main();
