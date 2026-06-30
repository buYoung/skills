#!/usr/bin/env python3
"""Collect compact git history signals for AGENTS.md Ownership Map discovery.

This script prints stable Markdown-KV, not JSON, to keep context small. The
output is a discovery signal only: high churn does not prove ownership.

Usage:
    python git_ownership_signals.py [PATH]
    python git_ownership_signals.py [PATH] --anchor <commit-ish>
    python git_ownership_signals.py [PATH] --since "3 months ago" --limit 20
"""

import argparse
import fnmatch
import os
import subprocess
import sys
from dataclasses import dataclass, field


DEFAULT_SINCE = "3 months ago"
DEFAULT_LIMIT = 20
DEFAULT_MIN_COMMITS = 2
TIMEOUT_SECONDS = 30

DEFAULT_EXCLUDES = [
    "*.lock",
    "pnpm-lock.yaml",
    "package-lock.json",
    "yarn.lock",
    "poetry.lock",
    "Pipfile.lock",
    "Cargo.lock",
    "Gemfile.lock",
    "Podfile.lock",
    "node_modules/**",
    "*/node_modules/**",
    "vendor/**",
    "*/vendor/**",
    "dist/**",
    "*/dist/**",
    "build/**",
    "*/build/**",
    "coverage/**",
    "*/coverage/**",
    ".next/**",
    "*/.next/**",
    ".turbo/**",
    "*/.turbo/**",
]


@dataclass
class PathSignal:
    path: str
    commits: set[str] = field(default_factory=set)
    last_date: str = ""
    exists: bool = True
    deleted_only: bool = True


def run_git(root: str, args: list[str]) -> str:
    command = ["git", "-C", root] + args
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=TIMEOUT_SECONDS,
        check=False,
    )
    if result.returncode != 0:
        sys.stderr.write(result.stderr or f"git command failed: {' '.join(command)}\n")
        sys.exit(result.returncode)
    return result.stdout


def git_root(path: str) -> str:
    result = subprocess.run(
        ["git", "-C", path, "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=TIMEOUT_SECONDS,
        check=False,
    )
    if result.returncode != 0:
        sys.stderr.write(f"Not a git repository: {path}\n")
        sys.exit(2)
    return result.stdout.strip()


def relative_path(root: str, path: str) -> str | None:
    root_abs = os.path.abspath(root)
    path_abs = os.path.abspath(path)
    if path_abs == root_abs:
        return None
    return os.path.relpath(path_abs, root_abs).replace(os.sep, "/")


def build_range(anchor: str | None, since: str, since_was_explicit: bool) -> tuple[list[str], str, str]:
    if anchor:
        return [f"{anchor}..HEAD"], "anchor", anchor
    resolved_from = "since" if since_was_explicit else "default_3mo"
    return [f"--since={since}"], resolved_from, since


def is_excluded(path: str, patterns: list[str]) -> bool:
    normalized = path.replace(os.sep, "/")
    for pattern in patterns:
        if fnmatch.fnmatch(normalized, pattern):
            return True
        if "/" not in pattern and fnmatch.fnmatch(os.path.basename(normalized), pattern):
            return True
    return False


def count_commits(root: str, range_args: list[str], pathspec: str | None) -> int:
    args = ["log", "--no-merges", "--format=%H"] + range_args
    if pathspec:
        args += ["--", pathspec]
    output = run_git(root, args)
    return len([line for line in output.splitlines() if line.strip()])


def collect_signals(
    root: str,
    range_args: list[str],
    pathspec: str | None,
    excludes: list[str],
    include_deleted: bool,
) -> dict[str, PathSignal]:
    args = [
        "log",
        "--no-merges",
        "--date=short",
        "--name-status",
        "--format=@@commit\t%H\t%ad",
    ] + range_args
    if pathspec:
        args += ["--", pathspec]

    output = run_git(root, args)
    signals: dict[str, PathSignal] = {}
    current_commit = ""
    current_date = ""
    seen_in_commit: set[str] = set()

    for raw_line in output.splitlines():
        line = raw_line.rstrip("\n")
        if not line:
            continue
        if line.startswith("@@commit\t"):
            parts = line.split("\t")
            current_commit = parts[1] if len(parts) > 1 else ""
            current_date = parts[2] if len(parts) > 2 else ""
            seen_in_commit = set()
            continue

        parts = line.split("\t")
        if len(parts) < 2 or not current_commit:
            continue
        status = parts[0]
        path = parts[-1] if status.startswith(("R", "C")) and len(parts) >= 3 else parts[1]
        path = path.strip()
        if not path or path in seen_in_commit or is_excluded(path, excludes):
            continue

        full_path = os.path.join(root, path)
        exists = os.path.exists(full_path)
        is_delete = status.startswith("D")
        if is_delete and not include_deleted:
            continue
        if not exists and not include_deleted:
            continue

        seen_in_commit.add(path)
        signal = signals.setdefault(path, PathSignal(path=path))
        signal.commits.add(current_commit)
        signal.exists = exists
        signal.deleted_only = signal.deleted_only and is_delete
        if current_date and (not signal.last_date or current_date > signal.last_date):
            signal.last_date = current_date

    return signals


def format_bool(value: bool) -> str:
    return "true" if value else "false"


def print_markdown_kv(
    root: str,
    pathspec: str | None,
    resolved_from: str,
    range_value: str,
    commit_count: int,
    limit: int,
    min_commits: int,
    include_deleted: bool,
    excludes: list[str],
    signals: list[PathSignal],
    truncated: bool,
) -> None:
    print(f"repo: {root}")
    print(f"scope: {pathspec or '.'}")
    print(f"range: {resolved_from}")
    if resolved_from == "anchor":
        print(f"anchor: {range_value}")
    else:
        print(f"since: {range_value}")
    print(f"commits: {commit_count}")
    print(f"limit: {limit}")
    print(f"min_commits: {min_commits}")
    print(f"truncated: {format_bool(truncated)}")
    print(f"deleted: {'included' if include_deleted else 'excluded'}")
    print()
    print("top_changed_paths:")
    if not signals:
        print("- none")
    for signal in signals:
        exists = "true" if signal.exists else "false"
        print(f"- {len(signal.commits)} {signal.path} last={signal.last_date or 'unknown'} exists={exists}")
    print()
    print("notes:")
    print(f"- excludes: {', '.join(excludes)}")
    print("- use: discovery signal only; confirm against current code or documented contracts")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("path", nargs="?", default=".",
                        help="Repository root or subdirectory scope (default: current directory)")
    parser.add_argument("--anchor", help="Commit-ish to use as <anchor>..HEAD")
    parser.add_argument("--since",
                        help=f"Fallback git log since value (default: {DEFAULT_SINCE!r})")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT,
                        help=f"Maximum changed paths to print (default: {DEFAULT_LIMIT})")
    parser.add_argument("--min-commits", type=int, default=DEFAULT_MIN_COMMITS,
                        help=f"Minimum commits per path (default: {DEFAULT_MIN_COMMITS})")
    parser.add_argument("--exclude", action="append", default=[],
                        help="Additional glob to exclude; may be repeated")
    parser.add_argument("--include-deleted", action="store_true",
                        help="Include paths that no longer exist")
    args = parser.parse_args()

    if args.limit < 1:
        sys.stderr.write("--limit must be >= 1\n")
        sys.exit(2)
    if args.min_commits < 1:
        sys.stderr.write("--min-commits must be >= 1\n")
        sys.exit(2)
    if not os.path.isdir(args.path):
        sys.stderr.write(f"Not a directory: {args.path}\n")
        sys.exit(2)

    root = git_root(args.path)
    pathspec = relative_path(root, args.path)
    since = args.since or DEFAULT_SINCE
    range_args, resolved_from, range_value = build_range(
        args.anchor,
        since,
        since_was_explicit=args.since is not None,
    )
    excludes = DEFAULT_EXCLUDES + args.exclude

    commit_count = count_commits(root, range_args, pathspec)
    signals_by_path = collect_signals(
        root=root,
        range_args=range_args,
        pathspec=pathspec,
        excludes=excludes,
        include_deleted=args.include_deleted,
    )
    filtered = [
        signal for signal in signals_by_path.values()
        if len(signal.commits) >= args.min_commits
    ]
    filtered.sort(key=lambda signal: (-len(signal.commits), signal.path))
    truncated = len(filtered) > args.limit

    print_markdown_kv(
        root=root,
        pathspec=pathspec,
        resolved_from=resolved_from,
        range_value=range_value,
        commit_count=commit_count,
        limit=args.limit,
        min_commits=args.min_commits,
        include_deleted=args.include_deleted,
        excludes=excludes,
        signals=filtered[:args.limit],
        truncated=truncated,
    )


if __name__ == "__main__":
    main()
