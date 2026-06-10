#!/usr/bin/env python3
"""Validate a briefset parent Markdown file plus its referenced child briefs.

Usage:
    python3 validate_briefset.py <path-to-parent-brief.md>
    python3 validate_briefset.py docs/briefs/2026-04-30-briefset-checkout-i18n.md

Exit codes:
    0 - Required checks pass on parent and every referenced child
    1 - One or more required checks failed
    2 - File not found or unreadable

What this script checks (STRUCTURAL ONLY):

  Parent file:
    - Filename matches YYYY-MM-DD-briefset-<set-slug>.md (with optional -vN)
    - Title line: `# Brief Set: <title>`
    - Required H2 sections present:
        Purpose, Child Briefs, Execution Order, Dependencies,
        Parallelization, Conflict Hotspots, Shared Constraints,
        Global Acceptance Criteria, Open Questions
    - `## Child Briefs` uses `- [ ]` / `- [x]` checklist format
    - `## Global Acceptance Criteria` uses `- [ ]` / `- [x]` checklist format
    - Populated: Purpose, Execution Order, Dependencies, Parallelization,
        Conflict Hotspots, Shared Constraints, Open Questions
        (`- None — <reason>` if genuinely none)
    - Every `## Child Briefs` bullet carries the child path in inline code
    - Each referenced child path exists on disk (resolved against the
        parent's directory before the cwd); duplicates validate once
    - No referenced child is itself a briefset parent (no recursion)
    - Inline-code paths in `## Dependencies` only reference children
        listed in `## Child Briefs`
    - Child filenames share the parent's date and set-slug and carry a
        zero-padded `NN` sequence segment (warn-only on mismatch)

  Child files:
    - Each referenced child re-runs `validate_brief.py`'s structural checks

Like `validate_brief.py`, this script does not judge content quality —
whether the decomposition is sensible, whether dependencies are correct,
whether acceptance criteria are measurable. Stage 6 human review covers
that.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Reuse the single-brief validator's primitives.
sys.path.insert(0, str(Path(__file__).parent))
from validate_brief import (  # noqa: E402
    BARE_NONE_RE,
    BULLET_RE,
    CHECKLIST_ITEM_RE,
    FILENAME_RE as CHILD_FILENAME_RE,
    NONE_WITH_REASON_RE,
    Report,
    ensure_unicode_safe_output,
    parse_sections,
    validate_entry_paths as validate_child_entry_paths,
    validate_filename as validate_child_filename,
    validate_sections as validate_child_sections,
    validate_title as validate_child_title,
)

USAGE = "Usage: validate_briefset.py <path-to-parent-brief.md>"

PARENT_FILENAME_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2})-briefset-([a-z0-9][a-z0-9-]*?)(-v\d+)?\.md$"
)

PARENT_TITLE_RE = re.compile(r"^# Brief Set:\s+(.+?)\s*$")

# Soft guideline from references/briefset.md. Warn-only — combined
# child slug `<set-slug>-NN-<child-slug>` is the hard limit (≤40 chars,
# enforced by validate_brief.py); this just keeps room for the child
# half of the slug.
SET_SLUG_MAX_LENGTH = 15

REQUIRED_PARENT_SECTIONS = [
    "Purpose",
    "Child Briefs",
    "Execution Order",
    "Dependencies",
    "Parallelization",
    "Conflict Hotspots",
    "Shared Constraints",
    "Global Acceptance Criteria",
    "Open Questions",
]

CHECKLIST_PARENT_SECTIONS = [
    "Child Briefs",
    "Global Acceptance Criteria",
]

POPULATED_PARENT_SECTIONS = [
    "Purpose",
    "Execution Order",
    "Dependencies",
    "Parallelization",
    "Conflict Hotspots",
    "Shared Constraints",
    "Open Questions",
]

CHILD_PATH_RE = re.compile(r"`([^`]+\.md)`")

# Zero-padded execution-order segment in a child slug, e.g. `-01-`.
CHILD_SEQUENCE_RE = re.compile(r"(?:^|-)\d{2}(?:-|$)")


def validate_parent_filename(path: Path, report: Report) -> tuple[str, str] | None:
    """Return (date, set-slug) parsed from the parent filename, or None."""
    match = PARENT_FILENAME_RE.match(path.name)
    if not match:
        report.fail(
            f"Parent filename '{path.name}' does not match "
            "YYYY-MM-DD-briefset-<set-slug>.md (with optional -vN)."
        )
        return None
    parent_date, set_slug, _ = match.groups()
    report.ok(f"Parent filename format OK (set-slug='{set_slug}').")
    if len(set_slug) > SET_SLUG_MAX_LENGTH:
        report.warn(
            f"Parent set-slug '{set_slug}' is {len(set_slug)} chars; "
            f"references/briefset.md guideline is ≤{SET_SLUG_MAX_LENGTH} "
            "to leave room for the child half of the combined slug."
        )
    return parent_date, set_slug


def validate_parent_title(first_line: str, report: Report) -> str | None:
    match = PARENT_TITLE_RE.match(first_line)
    if not match:
        report.fail("Title line must match `# Brief Set: <title>`.")
        return None
    title = match.group(1).strip()
    if not title:
        report.fail("Title text after `Brief Set:` is empty.")
        return None
    report.ok(f"Title line OK (title='{title}').")
    return title


def validate_parent_sections(h2: dict[str, list[str]], report: Report) -> None:
    # 1. Required sections present.
    for name in REQUIRED_PARENT_SECTIONS:
        if name not in h2:
            report.fail(f"Missing required section `## {name}`.")
        else:
            report.ok(f"Section `## {name}` present.")

    # 2. Checklist sections must use `- [ ]`.
    for name in CHECKLIST_PARENT_SECTIONS:
        if name not in h2:
            continue
        body = h2[name]
        bullets = [line for line in body if BULLET_RE.match(line)]
        if not bullets:
            report.fail(f"`## {name}` has no items.")
            continue
        non_checklist = [b for b in bullets if not CHECKLIST_ITEM_RE.match(b)]
        if non_checklist:
            report.fail(
                f"`## {name}` contains {len(non_checklist)} non-checklist "
                "bullet(s); expected `- [ ]` / `- [x]` format."
            )
        else:
            report.ok(f"`## {name}` uses `- [ ]` checklist format.")

    # 3. Populated sections must contain content (write `- None — <reason>`
    #    if truly empty).
    for name in POPULATED_PARENT_SECTIONS:
        if name not in h2:
            continue
        body = [line.strip() for line in h2[name] if line.strip()]
        if not body:
            report.fail(
                f"`## {name}` is empty — write `- None — <reason>` if genuinely none."
            )
        elif any(BARE_NONE_RE.match(line) for line in body):
            report.fail(
                f"`## {name}` uses bare `- None` — write `- None — <reason>`."
            )
        elif any(
            line.lower().startswith("- none") and not NONE_WITH_REASON_RE.match(line)
            for line in body
        ):
            report.fail(
                f"`## {name}` uses `None` without an em dash reason — "
                f"write `- None — <reason>`."
            )

    # 4. Warn on unexpected sections.
    for section_name in h2.keys():
        if section_name in REQUIRED_PARENT_SECTIONS:
            continue
        report.warn(
            f"Unexpected section `## {section_name}` — "
            "not in the briefset template."
        )


def extract_child_paths(child_briefs_lines: list[str]) -> tuple[list[str], list[str]]:
    """Pull inline-code paths from `## Child Briefs` bullets.

    Returns:
        paths: inline-code `.md` paths in document order (duplicates kept)
        pathless_bullets: top-level bullets carrying no inline-code path
    """
    paths: list[str] = []
    pathless_bullets: list[str] = []
    for line in child_briefs_lines:
        if not BULLET_RE.match(line):
            continue
        match = CHILD_PATH_RE.search(line)
        if match:
            paths.append(match.group(1))
        elif not line[:1].isspace():
            pathless_bullets.append(line.strip())
    return paths, pathless_bullets


def resolve_child_path(parent_path: Path, raw_path: str) -> Path | None:
    """Resolve a child path against the parent's directory before the cwd.

    Order: absolute path as-is → sibling file in the parent's directory →
    repo-root-relative when the parent sits under docs/briefs/ → cwd.
    Parent-first resolution keeps an unrelated cwd from supplying a
    same-named unrelated file.
    """
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate if candidate.is_file() else None
    parent_directory = parent_path.resolve().parent
    candidates = [parent_directory / candidate.name]
    if (
        parent_directory.name == "briefs"
        and parent_directory.parent.name == "docs"
    ):
        candidates.append(parent_directory.parent.parent / candidate)
    candidates.append(Path.cwd() / candidate)
    for resolved in candidates:
        if resolved.is_file():
            return resolved
    return None


def validate_child_briefs_section(
    parent_path: Path,
    h2: dict[str, list[str]],
    report: Report,
) -> list[Path]:
    """Validate `## Child Briefs` and return resolved on-disk child paths."""
    if "Child Briefs" not in h2:
        return []
    body = h2["Child Briefs"]
    raw_paths, pathless_bullets = extract_child_paths(body)
    for bullet in pathless_bullets:
        report.fail(
            "`## Child Briefs` bullet has no `path` in backticks — the "
            f"child cannot be validated: '{bullet[:70]}'. Reference the "
            "child as inline code, e.g. `` `docs/briefs/<child>.md` ``."
        )
    if not raw_paths:
        return []

    unique_paths: list[str] = []
    warned_duplicates: set[str] = set()
    for raw in raw_paths:
        if raw not in unique_paths:
            unique_paths.append(raw)
        elif raw not in warned_duplicates:
            warned_duplicates.add(raw)
            report.warn(
                f"`## Child Briefs` lists '{raw}' more than once — "
                "validating it once."
            )

    if len(unique_paths) < 2:
        report.warn(
            "Briefset has only 1 child — consider single-brief mode instead."
        )

    resolved: list[Path] = []
    for raw in unique_paths:
        path = resolve_child_path(parent_path, raw)
        if path is None:
            report.fail(f"Referenced child brief not found on disk: '{raw}'.")
            continue
        if PARENT_FILENAME_RE.match(path.name):
            report.fail(
                f"Referenced child '{raw}' is itself a briefset parent — "
                "nested briefsets are not allowed."
            )
            continue
        resolved.append(path)
    return resolved


def validate_dependencies_references(
    h2: dict[str, list[str]],
    child_paths: list[Path],
    report: Report,
) -> None:
    """Check that inline-code paths in Dependencies refer to listed children."""
    if "Dependencies" not in h2:
        return
    body = h2["Dependencies"]
    referenced = {
        match.group(1)
        for line in body
        for match in CHILD_PATH_RE.finditer(line)
    }
    if not referenced:
        # Acceptable: dependencies may be expressed in prose without inline
        # code (e.g., "no dependencies"). Nothing to cross-check.
        return
    child_basenames = {p.name for p in child_paths}
    for ref in referenced:
        if Path(ref).name in child_basenames:
            continue
        report.fail(
            f"`## Dependencies` references '{ref}', which is not listed in "
            "`## Child Briefs`."
        )


def validate_child_filename_consistency(
    child_path: Path,
    parent_date: str,
    set_slug: str,
    report: Report,
) -> None:
    """Warn when a child filename drifts from the parent's naming convention.

    Children should follow YYYY-MM-DD-<type>-<set-slug>-NN-<child-slug>.md
    with the parent's date and set-slug. Warn-only — mismatches are
    suspicious but not structurally fatal.
    """
    match = CHILD_FILENAME_RE.match(child_path.name)
    if not match:
        return  # validate_brief's filename check already fails this case.
    child_date, _, child_slug, _ = match.groups()
    label = f"child `{child_path.name}`"
    if child_date != parent_date:
        report.warn(
            f"{label}: filename date '{child_date}' differs from the "
            f"parent's date '{parent_date}'."
        )
    if set_slug not in child_slug:
        report.warn(
            f"{label}: slug does not contain the parent set-slug "
            f"'{set_slug}' (expected `<set-slug>-NN-<child-slug>`)."
        )
    if not CHILD_SEQUENCE_RE.search(child_slug):
        report.warn(
            f"{label}: slug has no zero-padded `NN` sequence segment "
            "(expected `<set-slug>-NN-<child-slug>`)."
        )


def validate_child_brief(child_path: Path, report: Report) -> None:
    """Run validate_brief.py's checks on a single child, prefix messages."""
    label = f"child `{child_path.name}`"
    try:
        text = child_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        report.fail(f"{label}: cannot read file — {error}")
        return
    lines = text.splitlines()
    if not lines:
        report.fail(f"{label}: file is empty.")
        return

    sub = Report()
    file_type = validate_child_filename(child_path, sub)
    title_type, _ = validate_child_title(lines[0], file_type, sub)
    h2, h3, h2_titles = parse_sections(text)
    validate_child_sections(h2, h3, h2_titles, title_type, sub)
    validate_child_entry_paths(h2, child_path, sub)

    for msg in sub.failures:
        report.fail(f"{label}: {msg}")
    for msg in sub.warnings:
        report.warn(f"{label}: {msg}")
    if not sub.failures:
        report.ok(f"{label}: structural checks OK.")


def main(argv: list[str]) -> int:
    ensure_unicode_safe_output()
    if len(argv) == 2 and argv[1] in ("-h", "--help"):
        print(USAGE)
        return 0
    if len(argv) != 2:
        print(USAGE, file=sys.stderr)
        return 2
    path = Path(argv[1])
    if not path.is_file():
        print(f"File not found: {path}", file=sys.stderr)
        return 2
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        print(f"Cannot read {path}: {error}", file=sys.stderr)
        return 2
    lines = text.splitlines()
    if not lines:
        print("File is empty.", file=sys.stderr)
        return 1

    report = Report()
    print(f"Validating briefset: {path}")
    print()

    parent_identity = validate_parent_filename(path, report)
    validate_parent_title(lines[0], report)
    h2, _, _ = parse_sections(text)
    validate_parent_sections(h2, report)

    child_paths = validate_child_briefs_section(path, h2, report)
    validate_dependencies_references(h2, child_paths, report)

    if child_paths:
        print(f"Validating {len(child_paths)} child brief(s)...")
        print()
        for child_path in child_paths:
            if parent_identity is not None:
                parent_date, set_slug = parent_identity
                validate_child_filename_consistency(
                    child_path, parent_date, set_slug, report
                )
            validate_child_brief(child_path, report)

    print(report.render())
    return 1 if report.failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
