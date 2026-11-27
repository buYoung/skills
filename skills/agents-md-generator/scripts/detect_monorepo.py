#!/usr/bin/env python3
"""Detect whether a directory is a monorepo and emit the marker type(s).

Marker rules mirror references/monorepo_detection.md. Some markers (package.json,
settings.gradle*, pom.xml, Cargo.toml, pyproject.toml, hatch.toml) are only
conclusive when an inner field/section is present, so this script reads each
candidate file before classifying. Matching is comment- and structure-aware (JSON
parse for package.json, line-level TOML/Gradle scanning, XML comments removed for
pom.xml) to avoid false positives from comments, string values, detached
`[workspace]` tables, or Hatch environments that declare no workspace members.
Package discovery itself is left to the agent — formats vary too much for a
single parser to be worth maintaining here.

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


_GRADLE_TOKEN = re.compile(
    r"(?P<COMMENT>//[^\n]*|/\*.*?\*/)"
    r"|(?P<STRING>\"\"\".*?\"\"\"|'''.*?'''|\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*')"
    r"|(?P<NEWLINE>\n)"
    r"|(?P<IDENTIFIER>[A-Za-z_$][\w$]*)"
    r"|(?P<SYMBOL>[^\s])",
    re.DOTALL,
)


def gradle_include_projects(tokens: list, start: int) -> set:
    """Read literal include arguments without evaluating Gradle expressions."""
    while start < len(tokens) and tokens[start][0] == "NEWLINE":
        start += 1
    if start == len(tokens):
        return set()
    has_parentheses = tokens[start][1] == "("
    if has_parentheses:
        start += 1
    projects = set()
    is_expecting_project = True
    for token_index in range(start, len(tokens)):
        kind, value = tokens[token_index]
        if kind == "NEWLINE":
            if has_parentheses or is_expecting_project:
                continue
            return projects
        if has_parentheses and value == ")":
            return projects
        if not has_parentheses and value in (";", "}"):
            return projects
        if value == "," and not is_expecting_project:
            is_expecting_project = True
            continue
        if kind == "STRING" and is_expecting_project:
            # Interpolation and non-literal expressions are outside this static
            # detector. Triple-quoted strings are consumed as tokens so example
            # declarations inside them cannot become real include calls.
            if value.startswith(('"""', "'''")) or "$" in value or "\\" in value:
                return set()
            project = value[1:-1].lstrip(":")
            if not project:
                return set()
            projects.add(project)
            is_expecting_project = False
            continue
        return set()
    return set() if has_parentheses else projects


def gradle_has_includes(path: str) -> bool:
    # A single `include ':app'` is the standard single-app Android layout, not a
    # monorepo; require 2+ included projects (or any composite build).
    tokens = [(match.lastgroup, match.group())
              for match in _GRADLE_TOKEN.finditer(_read(path))
              if match.lastgroup != "COMMENT"]
    projects = set()
    for i, (kind, value) in enumerate(tokens):
        if kind != "IDENTIFIER" or value not in ("include", "includeBuild"):
            continue
        if i > 0 and tokens[i - 1][1] not in ("\n", ";", "{", "}"):
            continue
        if value == "includeBuild":
            next_index = i + 1
            while next_index < len(tokens) and tokens[next_index][0] == "NEWLINE":
                next_index += 1
            if next_index < len(tokens) and (
                tokens[next_index][1] == "(" or tokens[next_index][0] == "STRING"
            ):
                return True
        else:
            projects.update(gradle_include_projects(tokens, i + 1))
    return len(projects) >= 2


_XML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)


def pom_declares_subprojects(path: str) -> bool:
    # POM 4.1.0 (Maven 4) uses <subprojects>; <modules> is deprecated there but
    # remains the Maven 3 form.
    text = _XML_COMMENT.sub("", _read(path))
    return "<modules>" in text or "<subprojects>" in text


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


_TOML_KEY_SEGMENT = r"(?:[A-Za-z0-9_-]+|\"[^\"]*\"|'[^']*')"
_TOML_DOTTED_KEY = rf"{_TOML_KEY_SEGMENT}(?:\s*\.\s*{_TOML_KEY_SEGMENT})*"
_TOML_TABLE_HEADER = re.compile(rf"^\[\[?\s*({_TOML_DOTTED_KEY})\s*\]\]?$")
_TOML_KEY_VALUE = re.compile(rf"^({_TOML_DOTTED_KEY})\s*=\s*(.*)$")
_INLINE_MEMBERS = re.compile(r"^\{.*\bmembers\s*=")


def _toml_key_path(dotted_key: str) -> tuple:
    return tuple(segment.strip("\"'")
                 for segment in re.findall(_TOML_KEY_SEGMENT, dotted_key))


def toml_entries(path: str):
    """Yield (key_path, value) per table header (value None) and key line.

    Line-level scan, not a TOML parser: comments and multiline string bodies are
    skipped, and key paths are prefixed with the current table.
    """
    table = ()
    multiline_delimiter = None
    for raw_line in _read(path).splitlines():
        if multiline_delimiter is not None:
            if raw_line.count(multiline_delimiter) % 2 == 1:
                multiline_delimiter = None
            continue
        for delimiter in ('"""', "'''"):
            if raw_line.count(delimiter) % 2 == 1:
                multiline_delimiter = delimiter
        line = raw_line.split("#", 1)[0].strip()
        header = _TOML_TABLE_HEADER.match(line)
        if header:
            table = _toml_key_path(header.group(1))
            yield table, None
            continue
        key_value = _TOML_KEY_VALUE.match(line)
        if key_value:
            yield table + _toml_key_path(key_value.group(1)), key_value.group(2)


def _is_hatch_workspace_entry(key_path: tuple, value, prefix: tuple) -> bool:
    # Hatch 1.16+ workspaces are per environment: `workspace.members` under
    # `[tool.hatch.envs.<env>]` in pyproject.toml or `[envs.<env>]` in hatch.toml.
    # Other environment settings do not declare a workspace.
    if value is None or key_path[:len(prefix) + 1] != prefix + ("envs",):
        return False
    env_key = key_path[len(prefix) + 2:]
    return (env_key == ("workspace", "members")
            or (env_key == ("workspace",) and _INLINE_MEMBERS.match(value) is not None))


def pyproject_has_workspace(path: str) -> bool:
    for key_path, value in toml_entries(path):
        if key_path[:3] in (("tool", "uv", "workspace"), ("tool", "rye", "workspace")):
            return True
        if _is_hatch_workspace_entry(key_path, value, ("tool", "hatch")):
            return True
    return False


def hatch_toml_has_workspace(path: str) -> bool:
    return any(_is_hatch_workspace_entry(key_path, value, ())
               for key_path, value in toml_entries(path))


# (filename, type_label, optional_predicate)
MARKERS = [
    ("pnpm-workspace.yaml", "pnpm-workspaces", None),
    ("lerna.json", "lerna", None),
    ("nx.json", "nx", None),
    ("turbo.json", "turborepo", None),
    ("rush.json", "rush", None),
    # moon v2 accepts these workspace config formats; v1 read only .yml and .pkl.
    (".moon/workspace.yml", "moonrepo", None),
    (".moon/workspace.yaml", "moonrepo", None),
    (".moon/workspace.json", "moonrepo", None),
    (".moon/workspace.jsonc", "moonrepo", None),
    (".moon/workspace.toml", "moonrepo", None),
    (".moon/workspace.hcl", "moonrepo", None),
    (".moon/workspace.pkl", "moonrepo", None),
    ("go.work", "go-workspaces", None),
    # WORKSPACE files are legacy: disabled by default in Bazel 8, removed in 9.
    ("WORKSPACE", "bazel", None),
    ("WORKSPACE.bazel", "bazel", None),
    ("MODULE.bazel", "bazel", None),
    ("REPO.bazel", "bazel", None),
    (".buckconfig", "buck2", None),
    ("pants.toml", "pants", None),
    # Legacy Pants config; current Pants no longer reads pants.ini and uses TOML
    # configuration (pants.toml).
    ("pants.ini", "pants", None),
    ("package.json", "npm-workspaces", has_workspaces_field),
    ("settings.gradle.kts", "gradle-multiproject", gradle_has_includes),
    ("settings.gradle", "gradle-multiproject", gradle_has_includes),
    ("pom.xml", "maven-multimodule", pom_declares_subprojects),
    ("Cargo.toml", "cargo-workspaces", cargo_has_workspace),
    ("pyproject.toml", "python-workspaces", pyproject_has_workspace),
    ("hatch.toml", "python-workspaces", hatch_toml_has_workspace),
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
