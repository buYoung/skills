#!/usr/bin/env node
"use strict";

const { spawnSync, execFileSync } = require("node:child_process");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const ROOT = path.resolve(__dirname, "..", "..");
const PROMPT_TEMPLATE_PATH = path.join(__dirname, "changelog-prompt.md");

const CHANGELOG_FILES = [
  { language: "en", file: path.join(ROOT, "CHANGELOG.md") },
  { language: "ko", file: path.join(ROOT, "CHANGELOG.ko.md") }
];

function fail(message) {
  process.stderr.write(`[write-changelog] ${message}\n`);
  process.exit(1);
}

function ensureCodexAvailable() {
  const result = spawnSync("codex", ["--version"], {
    stdio: ["ignore", "pipe", "pipe"],
    encoding: "utf8"
  });
  if (result.error && result.error.code === "ENOENT") {
    fail(
      "codex CLI not found on PATH. Install OpenAI Codex CLI and re-run release. " +
        "(release was aborted before any commit/tag.)"
    );
  }
  if (result.status !== 0) {
    fail(
      `codex --version exited with status ${result.status}. ` +
        `stderr: ${(result.stderr || "").trim() || "(empty)"}`
    );
  }
}

function git(args) {
  return execFileSync("git", args, { cwd: ROOT, encoding: "utf8" });
}

function collectCommits(previousTag) {
  const range = previousTag ? `${previousTag}..HEAD` : null;
  const args = [
    "log",
    "--no-merges",
    "--reverse",
    "--pretty=format:- %s%n%b%n----COMMIT-END----"
  ];
  if (range) args.push(range);
  const raw = git(args);
  const trimmed = raw
    .split("----COMMIT-END----")
    .map((entry) => entry.trim())
    .filter(Boolean)
    .join("\n\n");
  return trimmed || "(no commits found in range)";
}

function readChangelogSample(file) {
  if (!fs.existsSync(file)) return "(no prior changelog available)";
  const content = fs.readFileSync(file, "utf8");
  const versionSections = content.match(/## \[[^\]]+\][\s\S]*?(?=\n## \[|$)/g);
  if (!versionSections) return "(no prior version sections in changelog)";
  const realSections = versionSections.filter(
    (section) => !/^## \[Unreleased\]/i.test(section.trim())
  );
  if (realSections.length === 0) return "(this will be the first tagged release)";
  return realSections.slice(0, 2).join("\n\n");
}

function buildPrompt({ template, version, previousTag, commits, sample, language }) {
  return template
    .replaceAll("${VERSION}", version)
    .replaceAll("${PREVIOUS_TAG}", previousTag || "(none — first release)")
    .replaceAll("${COMMITS}", commits)
    .replaceAll("${SAMPLE}", sample)
    .replaceAll("${LANGUAGE}", language);
}

function runCodex(prompt) {
  const tmpFile = path.join(
    os.tmpdir(),
    `codex-changelog-${process.pid}-${Date.now()}-${Math.random().toString(36).slice(2)}.md`
  );
  try {
    const result = spawnSync(
      "codex",
      [
        "exec",
        "--cd", ROOT,
        "--sandbox", "read-only",
        "--ask-for-approval", "never",
        "--ephemeral",
        "--color", "never",
        "--output-last-message", tmpFile,
        "-"
      ],
      {
        input: prompt,
        encoding: "utf8",
        stdio: ["pipe", "pipe", "inherit"]
      }
    );
    if (result.status !== 0) {
      fail(
        `codex exec exited with status ${result.status}. ` +
          `Release aborted before any commit/tag.`
      );
    }
    if (!fs.existsSync(tmpFile)) {
      fail("codex exec finished but no output file was written. Release aborted.");
    }
    const body = fs.readFileSync(tmpFile, "utf8").trim();
    if (!body) {
      fail("codex exec produced an empty changelog body. Release aborted.");
    }
    return body;
  } finally {
    if (fs.existsSync(tmpFile)) {
      try { fs.unlinkSync(tmpFile); } catch { /* ignore */ }
    }
  }
}

function todayIso() {
  const d = new Date();
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

function insertVersionSection(filePath, version, body) {
  const date = todayIso();
  const newSectionHeader = `## [${version}] - ${date}`;
  const fresh = `## [Unreleased]\n\n${newSectionHeader}\n\n${body}\n`;

  let content = fs.existsSync(filePath) ? fs.readFileSync(filePath, "utf8") : "";

  if (!content.trim()) {
    fail(`${path.relative(ROOT, filePath)} is missing or empty. Cannot insert section.`);
  }

  const unreleasedRegex = /## \[Unreleased\]\s*\n*/i;
  if (!unreleasedRegex.test(content)) {
    fail(
      `${path.relative(ROOT, filePath)} has no [Unreleased] section. ` +
        `Add "## [Unreleased]" so the script knows where to insert new releases.`
    );
  }

  content = content.replace(unreleasedRegex, fresh + "\n");
  fs.writeFileSync(filePath, content, "utf8");
}

function main() {
  const [, , latestTagArg, versionArg] = process.argv;

  const version = (versionArg || "").trim();
  if (!version) {
    fail("Usage: write-changelog.js <latestTag> <version>");
  }

  const previousTag = (latestTagArg || "").trim();
  const previousTagForGit = previousTag && previousTag !== "0.0.0" ? previousTag : null;

  ensureCodexAvailable();

  const template = fs.readFileSync(PROMPT_TEMPLATE_PATH, "utf8");
  const commits = collectCommits(previousTagForGit);

  for (const { language, file } of CHANGELOG_FILES) {
    const sample = readChangelogSample(file);
    const prompt = buildPrompt({ template, version, previousTag: previousTagForGit, commits, sample, language });
    process.stdout.write(`[write-changelog] generating ${language} via codex exec...\n`);
    const body = runCodex(prompt);
    insertVersionSection(file, version, body);
    process.stdout.write(`[write-changelog] wrote ${path.relative(ROOT, file)}\n`);
  }

  process.stdout.write("[write-changelog] done. release-it will commit these files next.\n");
}

main();
