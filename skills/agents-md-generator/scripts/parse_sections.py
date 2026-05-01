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
                            update mode should insert these at their numerical
                            position relative to other standard sections

Only the first occurrence of any standard heading is treated as standard;
duplicates are preserved as-is. This matches references/update_strategy.md.

Usage:
    python parse_sections.py FILE [--doc-type single_repo|monorepo_root]
"""

import argparse
import json
import re
import sys


SINGLE_REPO_STANDARD = [
    "## 1. Overview",
    "## 2. Folder Structure",
    "## 3. Core Behaviors & Patterns",
    "## 4. Conventions",
    "## 5. Working Agreements",
]

MONOREPO_ROOT_STANDARD = [
    "## 1. Overview",
    "## 2. Folder Structure",
    "## 3. Working Agreements",
]


def parse_sections(text: str):
    lines = text.splitlines()
    sections = []
    preamble_end = None
    current = None
    for i, line in enumerate(lines):
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

    standard = SINGLE_REPO_STANDARD if args.doc_type == "single_repo" else MONOREPO_ROOT_STANDARD
    sections, preamble_end = parse_sections(text)

    seen = set()
    for s in sections:
        is_std = s["title"] in standard and s["title"] not in seen
        if is_std:
            seen.add(s["title"])
        s["is_standard"] = is_std

    result = {
        "doc_type": args.doc_type,
        "preamble_end_line": preamble_end,
        "sections": sections,
        "missing_standard": [t for t in standard if t not in seen],
    }
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
