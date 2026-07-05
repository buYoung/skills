#!/usr/bin/env python3
"""Parse an existing AGENTS.md and emit a section map for update mode.

Output is a JSON object with:
    - doc_type            : the standard set used for matching
    - preamble_end_line   : 0-based line index of the first '## ' heading
                            (everything before this line is preamble and must
                            be preserved verbatim)
    - sections            : list of {title, start_line, end_line, is_standard}
                            in document order; line indices are 0-based and
                            inclusive
    - missing_standard    : standard headings that did not appear in the file;
                            backward-compatible union of missing required and
                            missing optional standard headings
    - missing_required_standard
                          : required standard headings that did not appear and
                            should be inserted during update mode
    - missing_optional_standard
                          : optional standard headings that did not appear and
                            should be inserted only with fresh content
    - optional_standard   : standard headings that are evidence-gated and
                            should not be inserted without fresh content

Only the first occurrence of any canonical standard heading is the replacement
target. Duplicate current or legacy headings for the same canonical standard are
managed duplicates and should be omitted during reassembly unless the user moves
their content to a custom section. Legacy standard headings are treated as
managed and include their replacement heading in canonical_title. Lines inside
fenced code blocks (``` or ~~~) are never treated as section headings. This
matches references/update_strategy.md.

Usage:
    python parse_sections.py FILE [--doc-type single_repo|monorepo_root]
"""

import argparse
import json
import re
import sys


SINGLE_REPO_STANDARD = [
    "## 1. Overview",
    "## 2. Ownership Map",
    "## 3. Core Behaviors & Patterns",
    "## 4. Conventions",
    "## 5. Working Agreements",
]

MONOREPO_ROOT_STANDARD = [
    "## 1. Overview",
    "## 2. Ownership Map",
    "## 3. Working Agreements",
]

SINGLE_REPO_LEGACY = {
    "## 2. Folder Structure": "## 2. Ownership Map",
}

MONOREPO_ROOT_LEGACY = {
    "## 2. Folder Structure": "## 2. Ownership Map",
}

OPTIONAL_STANDARD = {
    "## 2. Ownership Map",
}


_FENCE_OPEN = re.compile(r"^ {0,3}(`{3,}|~{3,})")
_FENCE_CLOSE = re.compile(r"^ {0,3}(`{3,}|~{3,})\s*$")


def parse_sections(text: str):
    lines = text.splitlines()
    sections = []
    preamble_end = None
    current = None
    fence_marker = None
    for i, line in enumerate(lines):
        if fence_marker is not None:
            close = _FENCE_CLOSE.match(line)
            if (close and close.group(1)[0] == fence_marker[0]
                    and len(close.group(1)) >= len(fence_marker)):
                fence_marker = None
            continue
        fence_open = _FENCE_OPEN.match(line)
        if fence_open:
            fence_marker = fence_open.group(1)
            continue
        if re.match(r"^##\s", line):
            if preamble_end is None:
                preamble_end = i
            if current is not None:
                current["end_line"] = i - 1
                sections.append(current)
            current = {"title": line.rstrip(), "start_line": i, "end_line": None}
    if current is not None:
        current["end_line"] = len(lines) - 1
        sections.append(current)
    if preamble_end is None:
        preamble_end = len(lines)
    return sections, preamble_end


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", help="Path to existing AGENTS.md")
    parser.add_argument("--doc-type", choices=["single_repo", "monorepo_root"],
                        default="single_repo",
                        help="Standard heading set to match against (default: single_repo)")
    args = parser.parse_args()

    try:
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        sys.stderr.write(f"Cannot read {args.file}: {e}\n")
        sys.exit(2)
    except UnicodeDecodeError as e:
        sys.stderr.write(f"{args.file} is not valid UTF-8: {e}\n")
        sys.exit(2)

    standard = SINGLE_REPO_STANDARD if args.doc_type == "single_repo" else MONOREPO_ROOT_STANDARD
    legacy = SINGLE_REPO_LEGACY if args.doc_type == "single_repo" else MONOREPO_ROOT_LEGACY
    standard_lookup = {title: title for title in standard}
    standard_lookup.update(legacy)
    sections, preamble_end = parse_sections(text)

    seen = set()
    for s in sections:
        canonical_title = standard_lookup.get(s["title"])
        is_duplicate_standard = canonical_title is not None and canonical_title in seen
        is_std = canonical_title is not None
        s["canonical_title"] = canonical_title
        s["is_legacy_standard"] = canonical_title is not None and s["title"] != canonical_title
        s["is_optional_standard"] = canonical_title in OPTIONAL_STANDARD if canonical_title else False
        s["is_duplicate_standard"] = is_duplicate_standard
        if canonical_title is not None and not is_duplicate_standard:
            seen.add(canonical_title)
        s["is_standard"] = is_std

    missing_required = [t for t in standard if t not in seen and t not in OPTIONAL_STANDARD]
    missing_optional = [t for t in standard if t not in seen and t in OPTIONAL_STANDARD]
    result = {
        "doc_type": args.doc_type,
        "preamble_end_line": preamble_end,
        "sections": sections,
        "missing_standard": missing_required + missing_optional,
        "missing_required_standard": missing_required,
        "missing_optional_standard": missing_optional,
        "optional_standard": [t for t in standard if t in OPTIONAL_STANDARD],
    }
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
