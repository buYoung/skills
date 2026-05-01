#!/usr/bin/env python3
"""Detect whether a directory is a monorepo and emit the marker type(s).

Marker rules mirror references/monorepo_detection.md. Some markers (package.json,
settings.gradle*, pom.xml, Cargo.toml, pyproject.toml) are only conclusive when an
inner field/section is present, so this script reads each candidate file before
classifying. Package discovery itself is left to the agent — formats vary too
much for a single parser to be worth maintaining here.

Usage:
    python detect_monorepo.py [PATH]    # default: current directory
"""

import argparse
import json
import os
import sys


def _read(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def has_workspaces_field(path: str) -> bool:
    return '"workspaces"' in _read(path)


def gradle_has_includes(path: str) -> bool:
    text = _read(path)
    return "include(" in text or "includeBuild(" in text or "\ninclude " in text


def pom_has_modules(path: str) -> bool:
    return "<modules>" in _read(path)


def cargo_has_workspace(path: str) -> bool:
    return "[workspace]" in _read(path)


def pyproject_has_workspace(path: str) -> bool:
    text = _read(path)
    return any(token in text for token in (
        "[tool.hatch.envs]",
        "[tool.uv.workspace]",
        "[tool.rye.workspace]",
    ))


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
