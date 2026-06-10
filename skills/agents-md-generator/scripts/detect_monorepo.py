#!/usr/bin/env python3
"""Detect whether a directory is a monorepo and emit the marker type(s).

Marker rules mirror references/monorepo_detection.md. Some markers (package.json,
settings.gradle*, pom.xml, Cargo.toml, pyproject.toml) are only conclusive when an
inner field/section is present, so this script reads each candidate file before
classifying. Matching is comment- and structure-aware (JSON parse for package.json,
line-level TOML/Gradle scanning) to avoid false positives from comments, string
values, or detached `[workspace]` tables. Package discovery itself is left to the
agent — formats vary too much for a single parser to be worth maintaining here.

A `true` result is provisional: per SKILL.md Step 1, the workflow treats the repo
as a single document when package discovery finds fewer than 2 packages.

Usage:
    python detect_monorepo.py [PATH]    # default: current directory
"""

import argparse
import json
import os
import re
import sys


def _read(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def has_workspaces_field(path: str) -> bool:
    try:
        manifest = json.loads(_read(path))
    except json.JSONDecodeError:
        return False
    if not isinstance(manifest, dict):
        return False
    workspaces = manifest.get("workspaces")
    if isinstance(workspaces, dict):
        workspaces = workspaces.get("packages")
    return bool(workspaces)


_GRADLE_INCLUDE = re.compile(r"^\s*include[\s('\"]")
_GRADLE_INCLUDE_BUILD = re.compile(r"^\s*includeBuild[\s('\"]")


def gradle_has_includes(path: str) -> bool:
    # A single `include ':app'` is the standard single-app Android layout, not a
    # monorepo; require 2+ included projects (or any composite build).
    text = re.sub(r"/\*.*?\*/", "", _read(path), flags=re.DOTALL)
    project_count = 0
    for raw_line in text.splitlines():
        line = raw_line.split("//", 1)[0]
        if _GRADLE_INCLUDE_BUILD.match(line):
            return True
        if _GRADLE_INCLUDE.match(line):
            project_count += line.count(",") + 1
    return project_count >= 2


def pom_has_modules(path: str) -> bool:
    return "<modules>" in _read(path)


def cargo_has_workspace(path: str) -> bool:
    # An empty `[workspace]` table is the idiom for detaching a crate from a
    # parent workspace; only a `members` declaration marks a real workspace.
    in_workspace_table = False
    for raw_line in _read(path).splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("["):
            in_workspace_table = re.match(r"^\[workspace\]", line) is not None
            continue
        if in_workspace_table and re.match(r"^members\s*=", line):
            return True
    return False


_PYPROJECT_WORKSPACE_TABLES = (
    "[tool.hatch.envs",
    "[tool.uv.workspace",
    "[tool.rye.workspace",
)


def pyproject_has_workspace(path: str) -> bool:
    for raw_line in _read(path).splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if line.startswith(_PYPROJECT_WORKSPACE_TABLES):
            return True
    return False


# (filename, type_label, optional_predicate)
MARKERS = [
    ("pnpm-workspace.yaml", "pnpm-workspaces", None),
    ("lerna.json", "lerna", None),
    ("nx.json", "nx", None),
    ("turbo.json", "turborepo", None),
    ("rush.json", "rush", None),
    (".moon/workspace.yml", "moonrepo", None),
    ("go.work", "go-workspaces", None),
    ("WORKSPACE", "bazel", None),
    ("WORKSPACE.bazel", "bazel", None),
    ("MODULE.bazel", "bazel", None),
    (".buckconfig", "buck2", None),
    ("pants.toml", "pants", None),
    ("pants.ini", "pants", None),
    ("package.json", "npm-workspaces", has_workspaces_field),
    ("settings.gradle.kts", "gradle-multiproject", gradle_has_includes),
    ("settings.gradle", "gradle-multiproject", gradle_has_includes),
    ("pom.xml", "maven-multimodule", pom_has_modules),
    ("Cargo.toml", "cargo-workspaces", cargo_has_workspace),
    ("pyproject.toml", "python-workspaces", pyproject_has_workspace),
]


def detect(root: str):
    found = []
    for filename, type_label, predicate in MARKERS:
        path = os.path.join(root, filename)
        if not os.path.isfile(path):
            continue
        if predicate and not predicate(path):
            continue
        found.append({"marker": filename, "type": type_label})
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", default=".",
                        help="Directory to inspect (default: current directory)")
    args = parser.parse_args()

    if not os.path.isdir(args.path):
        sys.stderr.write(f"Not a directory: {args.path}\n")
        sys.exit(2)

    markers = detect(args.path)
    json.dump({"is_monorepo": bool(markers), "markers": markers}, sys.stdout)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
