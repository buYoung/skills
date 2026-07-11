#!/usr/bin/env python3
"""Validate a task-brief Markdown file against the template contract.

Usage:
    python3 validate_brief.py <path-to-brief.md>
    python3 validate_brief.py --repo-root <repository-root> <path-to-brief.md>
    python3 validate_brief.py docs/briefs/2026-04-23-feat-global-hotkey.md

Exit codes:
    0 - All checks pass with no warnings
    1 - One or more required checks failed, or a warning was reported
    2 - File not found or unreadable

What this script checks (STRUCTURAL ONLY):
    - Filename matches YYYY-MM-DD-<type>-<slug>.md pattern with a real
        calendar date
    - Title line: `# [<type>] <title>`
    - Type is one of the 10 Conventional Commits types
    - Title-prefix type matches the `## Work Type` value
    - All nine required H2 sections present, each exactly once, in the
        canonical template order, including `## Execution Plan`
    - Type-conditional sections present, populated, and positioned
        between `Current State (As-Is)` and `Desired Outcome (To-Be)`:
        fix      → `## Reproduction`
        perf     → `## Baseline Measurement`
        refactor → `## Behavior Contract`
    - `## Scope` has `### In Scope` and `### Out of Scope` H3s
    - Required sections contain at least one content bullet
    - `## Current State (As-Is)` bullets use `[confirmed]` / `[inferred]`
    - `## Execution Plan` has unique, consecutively numbered stages with the
        required start, work, deliverable, completion, handoff, and replan fields
    - `## Side Effect Checkpoints` and `## Acceptance Criteria` use `- [ ]` checklist format
    - `## Open Questions` is populated with either `None — <reason>` or
        structured non-blocking user questions with a default and reconfirm point
    - `## Related Files / Entry Points` contains at least one path-shaped
        inline-code entry; non-proposed paths and root filenames exist on disk
        (skipped only when `(proposed)` appears immediately after that path
        token; tokens starting with `/` only warn — they are often routes, not
        files)
    - Optional constraints use `## Constraints`, sit between `## Scope`
        and `## Related Files / Entry Points`, and are non-empty

What this script does NOT check (intentionally — content quality is the user's
judgment call at Stage 6):
    - Whether As-Is / To-Be bullets are concrete vs. vague
    - Whether `[confirmed]` / `[inferred]` classifications are truthful
    - Whether execution stages are correctly ordered or their handoffs work
    - Whether a non-blocking question's default and reconfirm point are safe
    - Whether Out-of-Scope entries are real guardrails vs. filler
    - Whether `Related Files / Entry Points` choices are *good* entry points
        (the path-existence check only catches fabricated paths, not poor ones)
    - Whether Acceptance Criteria are measurable
    - Whether the type-conditional section's content is sufficient

This is a structural smoke test for Stage 5, not a substitute for human review.
"""

from __future__ import annotations

import datetime
import re
import sys
from pathlib import Path

USAGE = (
    "Usage: validate_brief.py [--repo-root <repository-root>] "
    "<path-to-brief.md>"
)

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
    "Execution Plan",
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

# Type-conditional sections required between As-Is and To-Be.
TYPE_REQUIRED_SECTION = {
    "fix": "Reproduction",
    "perf": "Baseline Measurement",
    "refactor": "Behavior Contract",
}
TYPE_CONDITIONAL_SECTIONS = set(TYPE_REQUIRED_SECTION.values())

BULLET_RE = re.compile(r"^\s*-\s+.+")
CHECKLIST_ITEM_RE = re.compile(r"^\s*-\s+\[[ xX]\]\s+.+")
INLINE_CODE_RE = re.compile(r"`([^`]+)`")
LINE_NUM_SUFFIX_RE = re.compile(r"(?::\d+(?:-\d+)?)+$")
# `- None — <reason>` and `- N/A — <reason>` are exact contract forms.
# Bare values and alternate dash separators fail so generated briefs do not
# drift from the template text.
BARE_NA_RE = re.compile(r"^\s*-\s+N/A\s*(?:[—–-]\s*)?$")
BARE_NONE_RE = re.compile(r"^\s*-\s+None\s*(?:[—–-]\s*)?$")
NA_WITH_REASON_RE = re.compile(r"^\s*-\s+N/A\s+—\s+\S+")
NONE_WITH_REASON_RE = re.compile(r"^\s*-\s+None\s+—\s+\S+")
# Detection is intentionally case-insensitive so `none` cannot bypass the
# exact `None — <reason>` acceptance regex below.
NONE_BULLET_PREFIX_RE = re.compile(
    r"^\s*-\s+None(?:\s|$)", re.IGNORECASE
)
OUT_OF_SCOPE_PREFIX_RE = re.compile(r"^\s*-\s+\[(hard|deferred)\]\s+.+")
# A bare root path is otherwise indistinguishable from an identifier. Accept
# only a safe basename shape here; `validate_entry_paths` then treats it as a
# path only in a path position, when it already exists, or when it is marked
# `(proposed)`. This catches fake first-token paths without turning later code
# symbols into missing files.
ROOT_FILE_RE = re.compile(r"^[A-Za-z0-9._-]+\.[a-z0-9][a-z0-9._-]*$")
ROOT_EXTENSIONLESS_BASENAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
CURRENT_STATE_PREFIX_RE = re.compile(
    r"^\s*-\s+\[(confirmed|inferred)\]\s+\S+"
)
EXECUTION_STAGE_RE = re.compile(r"^Stage\s+([1-9]\d*)\s+—\s+\S.*$")
EXECUTION_REQUIRED_FIELDS = [
    "Starts when",
    "Work",
    "Deliverable",
    "Ends when",
    "Handoff",
    "Replan when",
]
EXECUTION_STAGE_CHECK_RE = re.compile(r"^\s+-\s+\[[ xX]\]\s+\S+")
NONE_VALUE_WITH_REASON_RE = re.compile(r"^None\s+—\s+\S+")
# Detection is intentionally case-insensitive; accepted output remains the
# case-sensitive `NONE_VALUE_WITH_REASON_RE` form.
NONE_VALUE_PREFIX_RE = re.compile(r"^None(?:\s|$)", re.IGNORECASE)
NON_BLOCKING_QUESTION_RE = re.compile(
    r"^\s*-\s+\[non-blocking\]\s+\S.+\s+—\s+Default:\s+\S.+;\s+"
    r"Reconfirm before:\s+\S.+$",
)

REPORT_SYMBOLS = "✓⚠✗—–≤"


def ensure_unicode_safe_output() -> None:
    """Keep report symbols from crashing on non-UTF-8 stdout/stderr.

    If the active stream cannot encode the symbols this script prints
    (e.g. PYTHONIOENCODING=ascii), switch its error handler to
    "replace" so output degrades gracefully instead of raising
    UnicodeEncodeError.
    """
    for stream in (sys.stdout, sys.stderr):
        encoding = getattr(stream, "encoding", None)
        try:
            REPORT_SYMBOLS.encode(encoding or "ascii")
        except (UnicodeEncodeError, LookupError):
            if hasattr(stream, "reconfigure"):
                stream.reconfigure(errors="replace")


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
        if self.failures or self.warnings:
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


def parse_sections(
    text: str,
) -> tuple[
    dict[str, list[str]],
    dict[str, dict[str, list[str]]],
    list[str],
    dict[str, list[str]],
]:
    """Split body into H2 sections and (for each) H3 subsections.

    Returns:
        h2_bodies: { section_title: [non-subsection lines] }
        h3_bodies: { h2_title: { h3_title: [lines] } }
        h2_titles: H2 titles in document order, duplicates included
        h3_titles_by_h2: H3 titles in document order, duplicates included
    """
    h2_bodies: dict[str, list[str]] = {}
    h3_bodies: dict[str, dict[str, list[str]]] = {}
    h2_titles: list[str] = []
    h3_titles_by_h2: dict[str, list[str]] = {}

    current_h2: str | None = None
    current_h3: str | None = None

    for raw_line in text.splitlines():
        if raw_line.startswith("# "):
            # Title line — ignored here (handled separately).
            continue
        if raw_line.startswith("## "):
            current_h2 = raw_line[3:].strip()
            current_h3 = None
            h2_titles.append(current_h2)
            h2_bodies.setdefault(current_h2, [])
            h3_bodies.setdefault(current_h2, {})
            h3_titles_by_h2.setdefault(current_h2, [])
            continue
        if raw_line.startswith("### ") and current_h2 is not None:
            current_h3 = raw_line[4:].strip()
            h3_titles_by_h2[current_h2].append(current_h3)
            h3_bodies[current_h2].setdefault(current_h3, [])
            continue
        if current_h2 is None:
            continue
        if current_h3 is not None:
            h3_bodies[current_h2][current_h3].append(raw_line)
        else:
            h2_bodies[current_h2].append(raw_line)

    return h2_bodies, h3_bodies, h2_titles, h3_titles_by_h2


def has_content_line(lines: list[str]) -> bool:
    """True if any line has non-whitespace content (beyond headers)."""
    return any(line.strip() for line in lines)


def count_bullets(lines: list[str]) -> int:
    return sum(1 for line in lines if BULLET_RE.match(line))


def top_level_bullets(lines: list[str]) -> list[str]:
    """Return bullets that begin at column zero, excluding nested notes."""
    return [line for line in lines if BULLET_RE.match(line) and not line[:1].isspace()]


def validate_execution_plan(
    h3: dict[str, dict[str, list[str]]],
    h3_titles_by_h2: dict[str, list[str]],
    report: Report,
) -> None:
    """Validate only the machine-checkable shape of execution stages."""
    stages = h3.get("Execution Plan", {})
    stage_titles = h3_titles_by_h2.get("Execution Plan", [])
    if not stage_titles:
        report.fail(
            "`## Execution Plan` must contain at least one "
            "`### Stage N — <name>` subsection."
        )
        return

    seen_stage_titles: set[str] = set()
    duplicate_stage_titles: list[str] = []
    for stage_title in stage_titles:
        if stage_title in seen_stage_titles and stage_title not in duplicate_stage_titles:
            duplicate_stage_titles.append(stage_title)
        seen_stage_titles.add(stage_title)
    for stage_title in duplicate_stage_titles:
        report.fail(
            f"Duplicate execution stage `### {stage_title}` — each stage heading "
            "must appear exactly once."
        )

    stage_numbers: list[int] = []
    for stage_title in stage_titles:
        stage_match = EXECUTION_STAGE_RE.match(stage_title)
        if not stage_match:
            report.fail(
                f"Execution-plan subsection `### {stage_title}` must match "
                "`### Stage N — <name>`."
            )
            continue
        stage_numbers.append(int(stage_match.group(1)))

    for stage_title, lines in stages.items():
        if not EXECUTION_STAGE_RE.match(stage_title):
            continue

        field_positions: dict[str, list[int]] = {
            field: [] for field in EXECUTION_REQUIRED_FIELDS
        }
        for position, line in enumerate(lines):
            for field in EXECUTION_REQUIRED_FIELDS:
                if line.startswith(f"- {field}:"):
                    field_positions[field].append(position)

        for field, positions in field_positions.items():
            if not positions:
                report.fail(
                    f"`### {stage_title}` is missing `- {field}:`."
                )
            elif len(positions) > 1:
                report.fail(
                    f"`### {stage_title}` repeats `- {field}:`; "
                    "each required field appears once."
                )

        if any(len(positions) != 1 for positions in field_positions.values()):
            continue

        ordered_positions = [field_positions[field][0] for field in EXECUTION_REQUIRED_FIELDS]
        if ordered_positions != sorted(ordered_positions):
            report.fail(
                f"`### {stage_title}` fields are out of order; use "
                "Starts when, Work, Deliverable, Ends when, Handoff, Replan when."
            )

        for field in ("Starts when", "Work", "Deliverable", "Handoff", "Replan when"):
            line = lines[field_positions[field][0]]
            value = line.split(":", 1)[1].strip()
            if not value:
                report.fail(f"`### {stage_title}` has an empty `{field}` value.")
            if (
                field == "Replan when"
                and NONE_VALUE_PREFIX_RE.match(value)
                and not NONE_VALUE_WITH_REASON_RE.match(value)
            ):
                report.fail(
                    f"`### {stage_title}` uses `Replan when: None` without "
                    "the exact `None — <reason>` form."
                )

        ends_position = field_positions["Ends when"][0]
        handoff_position = field_positions["Handoff"][0]
        if lines[ends_position].strip() != "- Ends when:":
            report.fail(
                f"`### {stage_title}` must use bare `- Ends when:` followed "
                "by an indented checklist."
            )
        stage_checks = [
            line
            for line in lines[ends_position + 1 : handoff_position]
            if EXECUTION_STAGE_CHECK_RE.match(line)
        ]
        if not stage_checks:
            report.fail(
                f"`### {stage_title}` has no indented `- [ ]` completion item "
                "between `Ends when` and `Handoff`."
            )

        worker_decisions = [
            line for line in lines if line.startswith("- Worker decision:")
        ]
        if len(worker_decisions) > 1:
            report.fail(
                f"`### {stage_title}` repeats `- Worker decision:`; "
                "combine the bounded choice into one field."
            )
        elif worker_decisions and not worker_decisions[0].split(":", 1)[1].strip():
            report.fail(
                f"`### {stage_title}` has an empty `Worker decision` value."
            )

    expected_numbers = list(range(1, len(stage_titles) + 1))
    if stage_numbers != expected_numbers:
        report.fail(
            "`## Execution Plan` stage numbers must start at 1 and be consecutive "
            f"in document order; found {stage_numbers}."
        )
    else:
        report.ok(
            f"`## Execution Plan` has {len(stage_numbers)} consecutively numbered "
            "stage(s) with required structural fields."
        )


def validate_filename(path: Path, report: Report) -> str | None:
    """Return the type parsed from the filename, or None on failure."""
    match = FILENAME_RE.match(path.name)
    if not match:
        report.fail(
            f"Filename '{path.name}' does not match "
            "YYYY-MM-DD-<type>-<slug>.md (with optional -vN suffix)."
        )
        return None
    date_string, file_type, slug, _ = match.groups()
    try:
        datetime.date.fromisoformat(date_string)
    except ValueError:
        report.fail(
            f"Filename date '{date_string}' is not a real calendar date "
            "(YYYY-MM-DD)."
        )
    else:
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
    h2_titles: list[str],
    h3_titles_by_h2: dict[str, list[str]],
    title_type: str | None,
    report: Report,
) -> None:
    expected_conditional = TYPE_REQUIRED_SECTION.get(title_type)

    # 1. Required sections present.
    for name in REQUIRED_SECTIONS:
        if name not in h2:
            report.fail(f"Missing required section `## {name}`.")
        else:
            report.ok(f"Section `## {name}` present.")

    # 2. Each H2 section must appear exactly once.
    seen_titles: set[str] = set()
    duplicated_titles: list[str] = []
    for title in h2_titles:
        if title in seen_titles and title not in duplicated_titles:
            duplicated_titles.append(title)
        seen_titles.add(title)
    for title in duplicated_titles:
        report.fail(
            f"Duplicate section `## {title}` — a brief must contain each "
            "section exactly once."
        )

    # 3. Sections must follow the canonical template order. Unknown extra
    #    sections are not position-checked (they only warn, below).
    first_index: dict[str, int] = {}
    for position, title in enumerate(h2_titles):
        first_index.setdefault(title, position)
    failures_before_order = len(report.failures)
    present_required = [name for name in REQUIRED_SECTIONS if name in first_index]
    for previous_name, current_name in zip(present_required, present_required[1:]):
        if first_index[current_name] < first_index[previous_name]:
            report.fail(
                f"Section `## {current_name}` is out of order — the template "
                f"places it after `## {previous_name}`."
            )
    if "Constraints" in first_index:
        scope_position = first_index.get("Scope")
        related_position = first_index.get("Related Files / Entry Points")
        constraints_position = first_index["Constraints"]
        if (
            scope_position is not None and constraints_position < scope_position
        ) or (
            related_position is not None and constraints_position > related_position
        ):
            report.fail(
                "Section `## Constraints` is out of order — the template "
                "places it between `## Scope` and "
                "`## Related Files / Entry Points`."
            )
    if expected_conditional is not None and expected_conditional in first_index:
        as_is_position = first_index.get("Current State (As-Is)")
        to_be_position = first_index.get("Desired Outcome (To-Be)")
        conditional_position = first_index[expected_conditional]
        if (
            as_is_position is not None and conditional_position < as_is_position
        ) or (
            to_be_position is not None and conditional_position > to_be_position
        ):
            report.fail(
                f"Section `## {expected_conditional}` is out of order — the "
                "template places it between `## Current State (As-Is)` and "
                "`## Desired Outcome (To-Be)`."
            )
    if len(present_required) >= 2 and len(report.failures) == failures_before_order:
        report.ok("Section order matches the canonical template.")

    # 4. `Work Type` value check.
    if "Work Type" in h2:
        value_lines = [line.strip() for line in h2["Work Type"] if line.strip()]
        if not value_lines:
            report.fail("`## Work Type` section is empty.")
        else:
            declared_type = value_lines[0]
            if len(value_lines) > 1:
                report.warn(
                    "`## Work Type` has extra prose after the type token — "
                    "the template says the bare type token only."
                )
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

    # 5. Non-empty bullet content for narrative sections.
    for name in [
        "Current State (As-Is)",
        "Desired Outcome (To-Be)",
        "Related Files / Entry Points",
    ]:
        if name not in h2:
            continue
        if not top_level_bullets(h2[name]):
            report.fail(f"Section `## {name}` has no top-level bullet items.")
        else:
            report.ok(f"Section `## {name}` has content bullets.")

    if "Current State (As-Is)" in h2:
        current_state_bullets = top_level_bullets(h2["Current State (As-Is)"])
        unlabeled_bullets = [
            line for line in current_state_bullets if not CURRENT_STATE_PREFIX_RE.match(line)
        ]
        if unlabeled_bullets:
            report.fail(
                "`## Current State (As-Is)` contains "
                f"{len(unlabeled_bullets)} bullet(s) without a `[confirmed]` or "
                "`[inferred]` prefix."
            )
        elif current_state_bullets:
            report.ok(
                "`## Current State (As-Is)` distinguishes confirmed facts "
                "from inferred findings."
            )

    if "Execution Plan" in h2:
        validate_execution_plan(h3, h3_titles_by_h2, report)

    # 6. `Scope` must have In Scope and Out of Scope subsections with bullets.
    if "Scope" in h2:
        subs = h3.get("Scope", {})
        for sub_name in ("In Scope", "Out of Scope"):
            if sub_name not in subs:
                report.fail(f"`## Scope` is missing `### {sub_name}` subsection.")
                continue
            if not top_level_bullets(subs[sub_name]):
                report.fail(
                    f"`### {sub_name}` under `## Scope` has no top-level bullets."
                )
            else:
                report.ok(f"`### {sub_name}` has content bullets.")
        out_of_scope_bullets = [
            line.strip()
            for line in subs.get("Out of Scope", [])
            if BULLET_RE.match(line)
        ]
        malformed_none_bullets = [
            line
            for line in out_of_scope_bullets
            if NONE_BULLET_PREFIX_RE.match(line)
            and not NONE_WITH_REASON_RE.match(line)
        ]
        if malformed_none_bullets:
            report.fail(
                "`### Out of Scope` uses a `None` variant outside the exact "
                "`- None — <reason>` form."
            )
        prefix_candidates = [
            line
            for line in out_of_scope_bullets
            if not NONE_BULLET_PREFIX_RE.match(line)
        ]
        if prefix_candidates and not any(
            OUT_OF_SCOPE_PREFIX_RE.match(line) for line in prefix_candidates
        ):
            report.warn(
                "`### Out of Scope` has no `[hard]` or `[deferred]` "
                "classified bullet. This is allowed, but classified guardrails "
                "make exclusions clearer for downstream coding agents."
            )

    # 7. Checklist sections must use `- [ ]` format. Indented sub-bullets
    #    under a checklist item (e.g. `  - note: ...`) are allowed notes;
    #    only top-level bullets must use the checklist form.
    for name in CHECKLIST_SECTIONS:
        if name not in h2:
            continue
        body = h2[name]
        top_bullets = top_level_bullets(body)
        if not top_bullets:
            report.fail(f"Section `## {name}` has no top-level checklist items.")
            continue
        non_checklist = [
            bullet for bullet in top_bullets if not CHECKLIST_ITEM_RE.match(bullet)
        ]
        if non_checklist:
            report.fail(
                f"Section `## {name}` contains {len(non_checklist)} non-checklist "
                f"bullet(s); expected `- [ ]` / `- [x]` format."
            )
        else:
            report.ok(f"Section `## {name}` uses `- [ ]` checklist format.")

    # 8. Open Questions must be populated and remain executable when unanswered.
    if "Open Questions" in h2:
        body = [line.strip() for line in h2["Open Questions"] if line.strip()]
        if not body:
            report.fail(
                "`## Open Questions` is empty — write `- None — <reason>` if genuinely none."
            )
        else:
            question_bullets = [
                line for line in body if BULLET_RE.match(line) and not line[:1].isspace()
            ]
            non_bullet_content = [line for line in body if not BULLET_RE.match(line)]
            none_bullets = [
                line
                for line in question_bullets
                if NONE_BULLET_PREFIX_RE.match(line)
            ]
            if non_bullet_content:
                report.fail("`## Open Questions` must contain bullets only.")
            elif none_bullets:
                if len(question_bullets) != 1:
                    report.fail(
                        "`## Open Questions` cannot mix `- None — <reason>` "
                        "with question bullets."
                    )
                elif BARE_NONE_RE.match(none_bullets[0]):
                    report.fail(
                        "`## Open Questions` uses bare `- None` — write "
                        "`- None — <reason>` so the absence of questions is explicit."
                    )
                elif not NONE_WITH_REASON_RE.match(none_bullets[0]):
                    report.fail(
                        "`## Open Questions` uses `None` without the exact em dash "
                        "reason form — write `- None — <reason>`."
                    )
                else:
                    report.ok("`## Open Questions` closes with a reasoned `None`.")
            else:
                malformed_questions = [
                    line
                    for line in question_bullets
                    if not NON_BLOCKING_QUESTION_RE.match(line)
                ]
                if not question_bullets:
                    report.fail("`## Open Questions` has no bullet items.")
                elif malformed_questions:
                    report.fail(
                        "`## Open Questions` contains "
                        f"{len(malformed_questions)} question bullet(s) outside the "
                        "`- [non-blocking] <question> — Default: <fallback>; "
                        "Reconfirm before: <stage>` contract."
                    )
                else:
                    report.ok(
                        "`## Open Questions` contains structured non-blocking "
                        "user decisions."
                    )

    # 9. Type-conditional section (fix → Reproduction, perf → Baseline
    #    Measurement, refactor → Behavior Contract). Required for the
    #    matching type, and the section's body must be non-empty. The
    #    explicit escape hatch is `- N/A — <reason>`; a bare `- N/A`
    #    without reason is rejected.
    if expected_conditional is not None:
        if expected_conditional not in h2:
            report.fail(
                f"Type `{title_type}` requires `## {expected_conditional}` "
                "section between `Current State (As-Is)` and "
                "`Desired Outcome (To-Be)`."
            )
        else:
            body = [line for line in h2[expected_conditional] if line.strip()]
            if not body:
                report.fail(
                    f"`## {expected_conditional}` is empty — populate it, or "
                    "write `- N/A — <reason>` if genuinely none."
                )
            else:
                bullets = [line for line in body if BULLET_RE.match(line)]
                non_bullet_content = [line for line in body if not BULLET_RE.match(line)]
                if non_bullet_content:
                    report.fail(
                        f"`## {expected_conditional}` contains non-bullet content — "
                        "use bullets, or the single bullet `- N/A — <reason>`."
                    )
                elif any(BARE_NA_RE.match(line) for line in bullets):
                    report.fail(
                        f"`## {expected_conditional}` uses bare `- N/A` — "
                        "the escape hatch is `- N/A — <reason>` (em dash + reason)."
                    )
                elif any(
                    line.lstrip().casefold().startswith("- n/a")
                    and not NA_WITH_REASON_RE.match(line)
                    for line in bullets
                ):
                    report.fail(
                        f"`## {expected_conditional}` uses `N/A` without the exact "
                        "em dash reason form — write `- N/A — <reason>`."
                    )
                elif any(NA_WITH_REASON_RE.match(line) for line in bullets) and len(bullets) != 1:
                    report.fail(
                        f"`## {expected_conditional}` cannot mix the "
                        "`- N/A — <reason>` escape hatch with other bullets."
                    )
                else:
                    report.ok(
                        f"Section `## {expected_conditional}` present and populated."
                    )

    # 10. `## Constraints`, when present, must carry content — the template
    #     says to omit the section entirely when there are no constraints.
    if "Constraints" in h2 and not has_content_line(h2["Constraints"]):
        report.fail(
            "`## Constraints` is present but empty — the template says to "
            "omit the section entirely when there are no constraints."
        )

    # 11. Optional section sanity (warn only).
    for section_name in h2.keys():
        if section_name in REQUIRED_SECTIONS:
            continue
        if section_name in OPTIONAL_SECTIONS:
            continue
        if section_name == expected_conditional:
            continue  # validated above
        if section_name in LEGACY_OPTIONAL_SECTIONS:
            report.warn(
                "Use `## Constraints` instead of "
                "`## Constraints (optional)` in emitted briefs."
            )
            continue
        if section_name in TYPE_CONDITIONAL_SECTIONS:
            report.warn(
                f"Section `## {section_name}` is the conditional section for "
                f"a different work type — current type is `{title_type}`."
            )
            continue
        report.warn(
            f"Unexpected section `## {section_name}` — not in the template."
        )


def infer_repo_root(brief_path: Path) -> Path:
    """Best-effort guess at the repo root.

    If the brief sits at <root>/docs/briefs/<file>.md, return <root>.
    Otherwise fall back to cwd. Path-existence checks are best-effort
    and skipped silently if the root cannot be located.
    """
    abs_brief = brief_path.resolve()
    parent = abs_brief.parent
    if parent.name == "briefs" and parent.parent.name == "docs":
        return parent.parent.parent
    return Path.cwd()


def looks_like_path(s: str, allow_extensionless_root: bool = True) -> bool:
    """Treat inline-code as a path candidate when it is path-shaped.

    Slash-bearing entries and bare root filenames with a conventional
    lowercase extension are always paths. Safe extensionless basenames are
    allowed for structured artifact locations. In `Related Files / Entry
    Points`, the caller adds context before treating such a basename as a
    path, so later code symbols remain symbols.
    """
    return (
        "/" in s
        or bool(ROOT_FILE_RE.match(s))
        or (
            allow_extensionless_root
            and (
                bool(ROOT_EXTENSIONLESS_BASENAME_RE.match(s))
            )
        )
    )


def has_adjacent_proposed_marker(line: str, match_end: int) -> bool:
    """Return true only when `(proposed)` immediately follows this path token."""
    return bool(
        re.match(r"^\s*\(proposed\)(?=\s|$|[—–,.;:])", line[match_end:])
    )


def validate_entry_paths(
    h2: dict[str, list[str]],
    brief_path: Path,
    report: Report,
    repo_root: Path | None = None,
) -> None:
    """Verify inline-code paths under `Related Files / Entry Points` exist.

    Skips a path only when `(proposed)` appears immediately after that
    inline-code token. PRs, URLs, and bare identifiers are not checked.
    Tokens starting with '/' (routes or absolute paths) only warn when
    missing — they are often URL routes, not repo files. Trailing `:N` /
    `:N-M` suffixes (also repeated, e.g. `:12:5`) are stripped before
    the disk check.
    """
    if "Related Files / Entry Points" not in h2:
        return
    effective_repo_root = (repo_root or infer_repo_root(brief_path)).resolve()
    path_reference_count = 0
    checked_path_count = 0
    proposed_path_count = 0
    unresolved = 0
    for line in top_level_bullets(h2["Related Files / Entry Points"]):
        for token_number, match in enumerate(INLINE_CODE_RE.finditer(line)):
            raw = match.group(1).strip()
            cleaned = LINE_NUM_SUFFIX_RE.sub("", raw)
            is_proposed = has_adjacent_proposed_marker(line, match.end())
            is_extensionless_basename = bool(
                ROOT_EXTENSIONLESS_BASENAME_RE.match(cleaned)
            )
            is_existing_extensionless_path = bool(
                is_extensionless_basename
                and (effective_repo_root / cleaned).exists()
            )
            if not looks_like_path(cleaned, allow_extensionless_root=False) and not (
                is_extensionless_basename
                and (
                    token_number == 0
                    or is_existing_extensionless_path
                    or is_proposed
                )
            ):
                continue
            path_reference_count += 1
            if is_proposed:
                proposed_path_count += 1
                continue
            checked_path_count += 1
            target = effective_repo_root / cleaned
            if target.exists():
                continue
            unresolved += 1
            if cleaned.startswith("/"):
                report.warn(
                    f"`## Related Files / Entry Points` references `{raw}`, "
                    f"which does not exist on disk — looks like a route or "
                    "absolute path; verify manually."
                )
            else:
                report.fail(
                    f"`## Related Files / Entry Points` references "
                    f"`{raw}`, but '{cleaned}' does not exist under "
                    f"{effective_repo_root}. Mark the bullet `(proposed)` if the path "
                    "is intended to be created by this work."
                )
    if path_reference_count == 0:
        report.fail(
            "`## Related Files / Entry Points` must contain at least one "
            "path-shaped inline-code entry; plain-text paths, PR-only bullets, "
            "and symbol-only bullets do not establish a validated entry point."
        )
    elif unresolved == 0:
        report.ok(
            "`## Related Files / Entry Points` has "
            f"{path_reference_count} path-shaped inline-code entry/entries "
            f"({checked_path_count} checked on disk, "
            f"{proposed_path_count} proposed)."
        )


def parse_cli_arguments(argv: list[str]) -> tuple[Path, Path | None] | None:
    """Parse the brief path and optional repository-root override."""
    if len(argv) == 2:
        return Path(argv[1]), None
    if len(argv) == 4 and argv[1] == "--repo-root":
        return Path(argv[3]), Path(argv[2])
    return None


def main(argv: list[str]) -> int:
    ensure_unicode_safe_output()
    if len(argv) == 2 and argv[1] in ("-h", "--help"):
        print(USAGE)
        return 0
    parsed_arguments = parse_cli_arguments(argv)
    if parsed_arguments is None:
        print(USAGE, file=sys.stderr)
        return 2
    path, repo_root = parsed_arguments
    if repo_root is not None and not repo_root.is_dir():
        print(f"Repository root not found: {repo_root}", file=sys.stderr)
        return 2
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
    print(f"Validating: {path}")
    print()

    file_type = validate_filename(path, report)
    title_type, _ = validate_title(lines[0] if lines else "", file_type, report)
    h2, h3, h2_titles, h3_titles_by_h2 = parse_sections(text)
    validate_sections(
        h2, h3, h2_titles, h3_titles_by_h2, title_type, report
    )
    validate_entry_paths(h2, path, report, repo_root)

    print(report.render())
    return 1 if report.failures or report.warnings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
