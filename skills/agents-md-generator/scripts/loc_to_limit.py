#!/usr/bin/env python3
"""Run tokei in a directory and map total LOC to the AGENTS.md character budget.

Usage:
    python loc_to_limit.py [PATH]              # runs tokei in PATH (default: .)
    tokei ... | python loc_to_limit.py --from-stdin
"""

import argparse
import json
import re
import shutil
import subprocess
import sys

EXCLUDES = ["*.json", "*.yaml", "*.yml", "*.md", "*.sh", "*.lock", "*.map", "*.svg"]

# (upper_bound_inclusive, scale_label, character_limit)
SCALE_TABLE = [
    (10_000, "Small", 10_000),
    (50_000, "Small-Medium", 12_000),
    (100_000, "Medium", 15_000),
    (500_000, "Medium-Large", 20_000),
    (1_000_000, "Large", 30_000),
    (float("inf"), "Extra-Large", 50_000),
]

INSTALL_HINT = (
    "tokei is not installed.\n"
    "https://github.com/XAMPPRocky/tokei Please install it from here and try again.\n"
)


def run_tokei(path: str) -> str:
    if shutil.which("tokei") is None:
        sys.stderr.write(INSTALL_HINT)
        sys.exit(2)
    cmd = ["tokei"]
    for pat in EXCLUDES:
        cmd += ["-e", pat]
    cmd.append(path)
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        sys.exit(result.returncode)
    return result.stdout


def parse_total_lines(tokei_output: str) -> int:
    for line in tokei_output.splitlines():
        m = re.match(r"\s*Total\s+\d+\s+(\d+)", line)
        if m:
            return int(m.group(1))
    raise ValueError("Could not find a 'Total' row in tokei output")


def loc_to_scale(loc: int):
    for upper, scale, limit in SCALE_TABLE:
        if loc <= upper:
            return scale, limit
    raise RuntimeError("unreachable")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", default=".",
                        help="Directory to measure (default: current directory)")
    parser.add_argument("--from-stdin", action="store_true",
                        help="Skip running tokei; read its raw output from stdin instead")
    args = parser.parse_args()

    output = sys.stdin.read() if args.from_stdin else run_tokei(args.path)
    loc = parse_total_lines(output)
    scale, limit = loc_to_scale(loc)
    json.dump({"loc": loc, "scale": scale, "character_limit": limit}, sys.stdout)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
