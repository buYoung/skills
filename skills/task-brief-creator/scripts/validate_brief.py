#!/usr/bin/env python3
"""Validate a task-brief Markdown file against the template contract.

Usage:
    python3 validate_brief.py <path-to-brief.md>
    python3 validate_brief.py docs/briefs/2026-04-23-feat-global-hotkey.md

Exit codes:
    0 - All required checks pass (warnings allowed)
    1 - One or more required checks failed
    2 - File not found or unreadable

What this script checks (STRUCTURAL ONLY):
    - Filename matches YYYY-MM-DD-<type>-<slug>.md pattern
    - Title line: `# [<type>] <title>`
    - Type is one of the 10 Conventional Commits types
    - Title-prefix type matches the `## Work Type` value
    - All required H2 sections present
    - `## Scope` has `### In Scope` and `### Out of Scope` H3s
    - Required sections contain at least one content bullet
    - `## Side Effect Checkpoints` and `## Acceptance Criteria` use `- [ ]` checklist format
    - `## Open Questions` is populated (questions or "None")
    - Optional constraints use `## Constraints`

What this script does NOT check (intentionally — content quality is the user's
judgment call at Stage 6):
    - Whether As-Is / To-Be bullets are concrete vs. vague
    - Whether Out-of-Scope entries are real guardrails vs. filler
    - Whether entry points under `Related Files / Entry Points` are legitimate
    - Whether Acceptance Criteria are measurable

This is a structural smoke test for Stage 6, not a substitute for human review.
"""

import re
import sys
from pathlib import Path

VALID_TYPES = [
    "feat", "fix", "refactor", "perf", "chore",
    "docs", "test", "style", "build", "ci",
]

SLUG_MAX_LENGTH = 40

FILENAME_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2})-("
    + "|".join(VALID_TYPES)
    + r")-([a-z0-9][a-z0-9-]*?)(-v\d+)?\.md$"
)

TITLE_RE = re.compile(
    r"^# \[(" + "|".join(VALID_TYPES) + r")\]\s+(.+?)\s*$"
)

REQUIRED_SECTIONS = [
    "Work Type",
    "Current State (As-Is)",
    "Desired Outcome (To-Be)",
    "Scope",
    "Related Files / Entry Points",
    "Side Effect Checkpoints",
    "Acceptance Criteria",
    "Open Questions",
]

CHECKLIST_SECTIONS = [
    "Side Effect Checkpoints",
    "Acceptance Criteria",
]

OPTIONAL_SECTIONS = {"Constraints"}
LEGACY_OPTIONAL_SECTIONS = {"Constraints (optional)"}

BULLET_RE = re.compile(r"^\s*-\s+.+")
CHECKLIST_ITEM_RE = re.compile(r"^\s*-\s+\[[ xX]\]\s+.+")


class Report:
    def __init__(self) -> None:
        self.failures: list[str] = []
        self.warnings: list[str] = []
        self.passes: list[str] = []

    def fail(self, msg: str) -> None:
        self.failures.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def ok(self, msg: str) -> None:
        self.passes.append(msg)

    def render(self) -> str:
        lines: list[str] = []
        for msg in self.passes:
            lines.append(f"  ✓ {msg}")
        for msg in self.warnings:
            lines.append(f"  ⚠  {msg}")
        for msg in self.failures:
            lines.append(f"  ✗ {msg}")
        lines.append("")
        if self.failures:
            lines.append(
                f"FAIL - {len(self.failures)} structural issue(s), "
                f"{len(self.warnings)} warning(s)."
            )
        else:
            lines.append(
                f"PASS - structural checks OK "
                f"({len(self.warnings)} warning(s))."
            )
        return "\n".join(lines)


def parse_sections(text: str) -> tuple[dict[str, list[str]], dict[str, dict[str, list[str]]]]:
    """Split body into H2 sections and (for each) H3 subsections.

    Returns:
        h2_bodies: { section_title: [non-subsection lines] }
        h3_bodies: { h2_title: { h3_title: [lines] } }
    """
    h2_bodies: dict[str, list[str]] = {}
    h3_bodies: dict[str, dict[str, list[str]]] = {}

    current_h2: str | None = None
    current_h3: str | None = None

    for raw_line in text.splitlines():
        if raw_line.startswith("# "):
            # Title line — ignored here (handled separately).
            continue
        if raw_line.startswith("## "):
            current_h2 = raw_line[3:].strip()
            current_h3 = None
            h2_bodies.setdefault(current_h2, [])
            h3_bodies.setdefault(current_h2, {})
            continue
        if raw_line.startswith("### ") and current_h2 is not None:
            current_h3 = raw_line[4:].strip()
            h3_bodies[current_h2].setdefault(current_h3, [])
            continue
        if current_h2 is None:
            continue
        if current_h3 is not None:
            h3_bodies[current_h2][current_h3].append(raw_line)
        else:
            h2_bodies[current_h2].append(raw_line)

    return h2_bodies, h3_bodies


def has_content_line(lines: list[str]) -> bool:
    """True if any line has non-whitespace content (beyond headers)."""
    return any(line.strip() for line in lines)


def count_bullets(lines: list[str]) -> int:
    return sum(1 for line in lines if BULLET_RE.match(line))


def validate_filename(path: Path, report: Report) -> str | None:
    """Return the type parsed from the filename, or None on failure."""
    match = FILENAME_RE.match(path.name)
    if not match:
        report.fail(
            f"Filename '{path.name}' does not match "
            "YYYY-MM-DD-<type>-<slug>.md (with optional -vN suffix)."
        )
        return None
    _, file_type, slug, _ = match.groups()
    report.ok(f"Filename format OK (type='{file_type}').")
    if len(slug) > SLUG_MAX_LENGTH:
        report.fail(
            f"Filename slug '{slug}' is {len(slug)} chars; "
            f"maximum is {SLUG_MAX_LENGTH}."
        )
    return file_type


def validate_title(
    first_line: str, file_type: str | None, report: Report
) -> tuple[str | None, str | None]:
    match = TITLE_RE.match(first_line)
    if not match:
        report.fail(
            "Title line must match `# [<type>] <title>` "
            "with a valid Conventional Commits type."
        )
        return None, None
    title_type, title_text = match.groups()
    if not title_text.strip():
        report.fail("Title text after `[<type>]` is empty.")
        return title_type, None
    report.ok(f"Title line OK (type='{title_type}', title='{title_text.strip()}').")
    if file_type is not None and title_type != file_type:
        report.fail(
            f"Filename type '{file_type}' does not match title type "
            f"'{title_type}'."
        )
    return title_type, title_text.strip()


def validate_sections(
    h2: dict[str, list[str]],
    h3: dict[str, dict[str, list[str]]],
    title_type: str | None,
    report: Report,
) -> None:
    # 1. Required sections present.
    for name in REQUIRED_SECTIONS:
        if name not in h2:
            report.fail(f"Missing required section `## {name}`.")
        else:
            report.ok(f"Section `## {name}` present.")

    # 2. `Work Type` value check.
    if "Work Type" in h2:
        value_lines = [line.strip() for line in h2["Work Type"] if line.strip()]
        if not value_lines:
            report.fail("`## Work Type` section is empty.")
        else:
            declared_type = value_lines[0]
            if declared_type not in VALID_TYPES:
                report.fail(
                    f"`## Work Type` value '{declared_type}' is not one of the "
                    f"10 Conventional Commits types."
                )
            else:
                report.ok(f"`## Work Type` value '{declared_type}' is valid.")
                if title_type is not None and declared_type != title_type:
                    report.fail(
                        f"Title type '[{title_type}]' does not match "
                        f"`## Work Type` value '{declared_type}'."
                    )

    # 3. Non-empty bullet content for narrative sections.
    for name in [
        "Current State (As-Is)",
        "Desired Outcome (To-Be)",
        "Related Files / Entry Points",
    ]:
        if name not in h2:
            continue
        if count_bullets(h2[name]) == 0:
            report.fail(f"Section `## {name}` has no bullet items.")
        else:
            report.ok(f"Section `## {name}` has content bullets.")

    # 4. `Scope` must have In Scope and Out of Scope subsections with bullets.
    if "Scope" in h2:
        subs = h3.get("Scope", {})
        for sub_name in ("In Scope", "Out of Scope"):
            if sub_name not in subs:
                report.fail(f"`## Scope` is missing `### {sub_name}` subsection.")
                continue
            if count_bullets(subs[sub_name]) == 0:
                report.fail(f"`### {sub_name}` under `## Scope` has no bullets.")
            else:
                report.ok(f"`### {sub_name}` has content bullets.")

    # 5. Checklist sections must use `- [ ]` format.
    for name in CHECKLIST_SECTIONS:
        if name not in h2:
            continue
        body = h2[name]
        bullets = [line for line in body if BULLET_RE.match(line)]
        if not bullets:
            report.fail(f"Section `## {name}` has no items.")
            continue
        non_checklist = [b for b in bullets if not CHECKLIST_ITEM_RE.match(b)]
        if non_checklist:
            report.fail(
                f"Section `## {name}` contains {len(non_checklist)} non-checklist "
                f"bullet(s); expected `- [ ]` / `- [x]` format."
            )
        else:
            report.ok(f"Section `## {name}` uses `- [ ]` checklist format.")

    # 6. Open Questions must be populated.
    if "Open Questions" in h2:
        body = [line.strip() for line in h2["Open Questions"] if line.strip()]
        if not body:
            report.fail(
                "`## Open Questions` is empty — write `- None` if genuinely none."
            )
        else:
            report.ok("`## Open Questions` populated.")

    # 7. Optional section sanity (warn only).
    for section_name in h2.keys():
        if section_name in REQUIRED_SECTIONS:
            continue
        if section_name in OPTIONAL_SECTIONS:
            continue
        if section_name in LEGACY_OPTIONAL_SECTIONS:
            report.warn(
                "Use `## Constraints` instead of "
                "`## Constraints (optional)` in emitted briefs."
            )
            continue
        report.warn(
            f"Unexpected section `## {section_name}` — not in the template."
        )


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: validate_brief.py <path-to-brief.md>", file=sys.stderr)
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
    print(f"Validating: {path}")
    print()

    file_type = validate_filename(path, report)
    title_type, _ = validate_title(lines[0] if lines else "", file_type, report)
    h2, h3 = parse_sections(text)
    validate_sections(h2, h3, title_type, report)

    print(report.render())
    return 1 if report.failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
