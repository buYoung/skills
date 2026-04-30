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
    - Populated: Purpose, Execution Order, Parallelization,
        Conflict Hotspots, Shared Constraints, Open Questions
    - Each referenced child path exists on disk
    - No referenced child is itself a briefset parent (no recursion)
    - Inline-code paths in `## Dependencies` only reference children
        listed in `## Child Briefs`

  Child files:
    - Each referenced child re-runs `validate_brief.py`'s structural checks

Like `validate_brief.py`, this script does not judge content quality —
whether the decomposition is sensible, whether dependencies are correct,
whether acceptance criteria are measurable. Stage 6 human review covers
that.
"""

import re
import sys
from pathlib import Path

# Reuse the single-brief validator's primitives.
sys.path.insert(0, str(Path(__file__).parent))
from validate_brief import (  # noqa: E402
    BULLET_RE,
    CHECKLIST_ITEM_RE,
    Report,
    parse_sections,
    validate_filename as validate_child_filename,
    validate_sections as validate_child_sections,
    validate_title as validate_child_title,
)

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


def validate_parent_filename(path: Path, report: Report) -> str | None:
    match = PARENT_FILENAME_RE.match(path.name)
    if not match:
        report.fail(
            f"Parent filename '{path.name}' does not match "
            "YYYY-MM-DD-briefset-<set-slug>.md (with optional -vN)."
        )
        return None
    _, set_slug, _ = match.groups()
    report.ok(f"Parent filename format OK (set-slug='{set_slug}').")
    if len(set_slug) > SET_SLUG_MAX_LENGTH:
        report.warn(
            f"Parent set-slug '{set_slug}' is {len(set_slug)} chars; "
            f"references/briefset.md guideline is ≤{SET_SLUG_MAX_LENGTH} "
            "to leave room for the child half of the combined slug."
        )
    return set_slug


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

    # 3. Populated sections must contain content (write `- None` if truly empty).
    for name in POPULATED_PARENT_SECTIONS:
        if name not in h2:
            continue
        if not any(line.strip() for line in h2[name]):
            report.fail(
                f"`## {name}` is empty — write `- None` if genuinely none."
            )

    # 4. Warn on unexpected sections.
    for section_name in h2.keys():
        if section_name in REQUIRED_PARENT_SECTIONS:
            continue
        report.warn(
            f"Unexpected section `## {section_name}` — "
            "not in the briefset template."
        )


def extract_child_paths(child_briefs_lines: list[str]) -> list[str]:
    """Pull inline-code paths from `## Child Briefs` bullets."""
    out: list[str] = []
    for line in child_briefs_lines:
        if not BULLET_RE.match(line):
            continue
        match = CHILD_PATH_RE.search(line)
        if match:
            out.append(match.group(1))
    return out


def resolve_child_path(parent_path: Path, raw_path: str) -> Path | None:
    """Resolve a child path against cwd then against the parent's directory."""
    candidate = Path(raw_path)
    if candidate.is_absolute() and candidate.is_file():
        return candidate
    cwd_path = Path.cwd() / candidate
    if cwd_path.is_file():
        return cwd_path
    sibling_path = parent_path.parent / candidate.name
    if sibling_path.is_file():
        return sibling_path
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
    raw_paths = extract_child_paths(body)
    if not raw_paths:
        # Section presence + checklist shape already reported by
        # validate_parent_sections; just flag the missing inline-code
        # references here.
        if any(BULLET_RE.match(line) for line in body):
            report.fail(
                "`## Child Briefs` bullets must include the child path in "
                "inline code, e.g. `` `docs/briefs/<child>.md` ``."
            )
        return []

    if len(raw_paths) < 2:
        report.warn(
            "Briefset has only 1 child — consider single-brief mode instead."
        )

    resolved: list[Path] = []
    for raw in raw_paths:
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


def validate_child_brief(child_path: Path, report: Report) -> None:
    """Run validate_brief.py's checks on a single child, prefix messages."""
    text = child_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    label = f"child `{child_path.name}`"
    if not lines:
        report.fail(f"{label}: file is empty.")
        return

    sub = Report()
    file_type = validate_child_filename(child_path, sub)
    title_type, _ = validate_child_title(lines[0], file_type, sub)
    h2, h3 = parse_sections(text)
    validate_child_sections(h2, h3, title_type, sub)

    for msg in sub.failures:
        report.fail(f"{label}: {msg}")
    for msg in sub.warnings:
        report.warn(f"{label}: {msg}")
    if not sub.failures:
        report.ok(f"{label}: structural checks OK.")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(
            "Usage: validate_briefset.py <path-to-parent-brief.md>",
            file=sys.stderr,
        )
        return 2
    path = Path(argv[1])
    if not path.is_file():
        print(f"File not found: {path}", file=sys.stderr)
        return 2
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines:
        print("File is empty.", file=sys.stderr)
        return 1

    report = Report()
    print(f"Validating briefset: {path}")
    print()

    validate_parent_filename(path, report)
    validate_parent_title(lines[0], report)
    h2, _ = parse_sections(text)
    validate_parent_sections(h2, report)

    child_paths = validate_child_briefs_section(path, h2, report)
    validate_dependencies_references(h2, child_paths, report)

    if child_paths:
        print(f"Validating {len(child_paths)} child brief(s)...")
        print()
        for cp in child_paths:
            validate_child_brief(cp, report)

    print(report.render())
    return 1 if report.failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
