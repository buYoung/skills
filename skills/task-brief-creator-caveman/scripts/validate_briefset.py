#!/usr/bin/env python3
"""Validate a briefset parent Markdown file plus its referenced child briefs.

Usage:
    python3 validate_briefset.py <path-to-parent-brief.md>
    python3 validate_briefset.py --repo-root <repository-root> <path-to-parent-brief.md>
    python3 validate_briefset.py docs/briefs/2026-04-30-briefset-checkout-i18n.md

Exit codes:
    0 - All checks pass on parent and every referenced child with no warnings
    1 - One or more required checks failed, or a warning was reported
    2 - File not found or unreadable

What this script checks (STRUCTURAL ONLY):

  Parent file:
    - Filename matches YYYY-MM-DD-briefset-<set-slug>.md (with optional -vN)
      with a real calendar date
    - Title line: `# Brief Set: <title>`
    - Required H2 sections present exactly once, in canonical order:
        Purpose, Child Briefs, Execution Order, Dependencies,
        Parallelization, Conflict Hotspots, Shared Constraints,
        Global Acceptance Criteria, Open Questions
    - `## Child Briefs` uses `- [ ]` / `- [x]` checklist format
    - `## Global Acceptance Criteria` uses `- [ ]` / `- [x]` checklist format
    - Populated: Purpose, Execution Order, Dependencies, Parallelization,
        Conflict Hotspots, Shared Constraints, Open Questions
        (`- None — <reason>` if genuinely none)
    - Every top-level `## Child Briefs` bullet carries the child path in inline
        code; nested bullets never count toward the child minimum
    - Every child reference is the exact repo-relative
        `docs/briefs/<child>.md` path; absolute paths and `..` escapes fail
    - Each exact referenced child path exists on disk; duplicates validate once
    - No referenced child is itself a briefset parent (no recursion)
    - `## Execution Order` references every listed child exactly once
    - Every execution-order entry names a concrete deliverable location
    - Coordination sections use top-level bullets; prose-only bodies fail
    - Every dependency edge names its predecessor, successor, deliverable path,
        format, readiness check, verification input, and expected signal; the
        predecessor wave must be earlier than the successor wave
    - Every parallel or serialized entry describes exactly one child pair and
        declares its own non-empty `Join when:` condition
    - The same child pair cannot be both parallel and serialized, and a
        dependency pair cannot be declared parallel
    - Every conflict hotspot uses a pairwise access contract; a serialized
        hotspot cannot contradict a parallel declaration
    - Every child stage names a verification action, inputs, and expected
        signal; Stage 1 also names its no-change route and evidence handoff
    - Child filenames use `<set-slug>-NN-<child-slug>` order and share the
        parent's date

  Child files:
    - Each referenced child re-runs `validate_brief.py`'s structural checks

Like `validate_brief.py`, this script does not judge content quality —
whether the decomposition is sensible, whether dependencies are correct,
whether parallel joins are safe, whether acceptance criteria are measurable.
The Stage 5.5–5.7 executability checks and Stage 6 human review cover that.
"""

from __future__ import annotations

import datetime
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# Reuse the single-brief validator's primitives.
sys.path.insert(0, str(Path(__file__).parent))
from validate_brief import (  # noqa: E402
    BARE_NONE_RE,
    BULLET_RE,
    CHECKLIST_ITEM_RE,
    EXECUTION_STAGE_RE,
    FILENAME_RE as CHILD_FILENAME_RE,
    INLINE_CODE_RE,
    NONE_BULLET_PREFIX_RE,
    NONE_WITH_REASON_RE,
    NONE_VALUE_PREFIX_RE,
    NONE_VALUE_WITH_REASON_RE,
    NON_BLOCKING_QUESTION_RE,
    Report,
    ensure_unicode_safe_output,
    infer_repo_root,
    looks_like_path,
    parse_sections,
    top_level_bullets,
    validate_entry_paths as validate_child_entry_paths,
    validate_filename as validate_child_filename,
    validate_sections as validate_child_sections,
    validate_title as validate_child_title,
)

USAGE = (
    "Usage: validate_briefset.py [--repo-root <repository-root>] "
    "<path-to-parent-brief.md>"
)

PARENT_FILENAME_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2})-briefset-([a-z0-9][a-z0-9-]*?)(-v\d+)?\.md$"
)

PARENT_TITLE_RE = re.compile(r"^# Brief Set:\s+(.+?)\s*$")

# Soft guideline from references/briefset.md. The finding remains a warning,
# but every warning makes this checker return failure so generated output must
# be clean before it is accepted.
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

FIXED_PARENT_BULLET_SECTIONS = [
    "Execution Order",
    "Dependencies",
    "Parallelization",
    "Conflict Hotspots",
]

CHILD_PATH_RE = re.compile(r"`([^`]+\.md)`")
CHILD_REFERENCE_PREFIX = ("docs", "briefs")

EXECUTION_ORDER_ENTRY_RE = re.compile(
    r"^-\s+Wave\s+(?P<wave>[1-9]\d*)\s+—\s+`(?P<child>[^`]+)`:\s+"
    r"Start:\s+(?P<start>[^;]*[^\s;][^;]*);\s+"
    r"Deliverable:\s+(?P<deliverable>[^;]*[^\s;][^;]*);\s+"
    r"Location:\s+`(?P<location>[^`]+)`(?P<proposed>\s+\(proposed\))?;\s+"
    r"Done:\s+(?P<done>[^;]*[^\s;][^;]*);\s+"
    r"Handoff:\s+(?P<handoff>[^;]*[^\s;][^;]*)$",
)

DEPENDENCY_EDGE_RE = re.compile(
    r"^-\s+Predecessor:\s+`(?P<predecessor>[^`]+)`;\s+"
    r"Deliverable path:\s+`(?P<deliverable>[^`]+)`"
    r"(?P<proposed>\s+\(proposed\))?;\s+"
    r"Format:\s+(?P<format>[^;]*[^\s;][^;]*);\s+"
    r"Successor:\s+`(?P<successor>[^`]+)`;\s+"
    r"Starts when:\s+(?P<starts_when>[^;]*[^\s;][^;]*);\s+"
    r"Verify:\s+`(?P<verify>[^`]+)`;\s+"
    r"Inputs:\s+(?P<inputs>[^;]*[^\s;][^;]*);\s+"
    r"Expected:\s+(?P<expected>[^;]*[^\s;][^;]*)$",
)

PARALLELIZATION_PREFIX_RE = re.compile(
    r"^-\s+(?P<mode>Can run together|Must not overlap):\s+",
)

HOTSPOT_ENTRY_RE = re.compile(
    r"^-\s+`(?P<path>[^`]+)`(?P<proposed>\s+\(proposed\))?\s+—\s+"
    r"Children:\s+(?P<children>.+?);\s+"
    r"Access:\s+(?P<access>serialized|parallel-safe);\s+"
    r"(?:(?:Owner:\s+`(?P<owner>[^`]+)`;\s+))?"
    r"Rule:\s+(?P<rule>\S.*?)\.?$",
)

BRIEFSET_STAGE_VERIFY_RE = re.compile(
    r"^-\s+Verify:\s+`[^`]+`;\s+Inputs:\s+\S.*?;\s+Expected:\s+\S.*$",
)


@dataclass(frozen=True)
class DependencyEdge:
    predecessor: str
    successor: str
    deliverable_path: str


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
    try:
        datetime.date.fromisoformat(parent_date)
    except ValueError:
        report.fail(
            f"Parent filename date '{parent_date}' is not a real calendar date "
            "(YYYY-MM-DD)."
        )
    else:
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


def validate_parent_sections(
    h2: dict[str, list[str]], h2_titles: list[str], report: Report
) -> None:
    # 1. Required sections present.
    for name in REQUIRED_PARENT_SECTIONS:
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
            f"Duplicate section `## {title}` — a briefset parent must contain "
            "each section exactly once."
        )

    # 3. Required parent sections must follow the canonical order.
    first_index: dict[str, int] = {}
    for position, title in enumerate(h2_titles):
        first_index.setdefault(title, position)
    failures_before_order = len(report.failures)
    present_required = [
        name for name in REQUIRED_PARENT_SECTIONS if name in first_index
    ]
    for previous_name, current_name in zip(present_required, present_required[1:]):
        if first_index[current_name] < first_index[previous_name]:
            report.fail(
                f"Section `## {current_name}` is out of order — the template "
                f"places it after `## {previous_name}`."
            )
    if len(present_required) >= 2 and len(report.failures) == failures_before_order:
        report.ok("Parent section order matches the canonical template.")

    # 4. Checklist sections must use `- [ ]`.
    for name in CHECKLIST_PARENT_SECTIONS:
        if name not in h2:
            continue
        body = h2[name]
        bullets = top_level_bullets(body)
        if not bullets:
            report.fail(f"`## {name}` has no top-level items.")
            continue
        non_checklist = [b for b in bullets if not CHECKLIST_ITEM_RE.match(b)]
        if non_checklist:
            report.fail(
                f"`## {name}` contains {len(non_checklist)} non-checklist "
                "bullet(s); expected `- [ ]` / `- [x]` format."
            )
        else:
            report.ok(f"`## {name}` uses `- [ ]` checklist format.")

    # 5. Populated sections must contain content (write `- None — <reason>`
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
            NONE_BULLET_PREFIX_RE.match(line)
            and not NONE_WITH_REASON_RE.match(line)
            for line in body
        ):
            report.fail(
                f"`## {name}` uses `None` without the exact em dash reason form — "
                f"write `- None — <reason>`."
            )

    if "Open Questions" in h2:
        body = [line.strip() for line in h2["Open Questions"] if line.strip()]
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
            report.fail("Parent `## Open Questions` must contain bullets only.")
        elif not question_bullets:
            report.fail("Parent `## Open Questions` has no bullet items.")
        elif none_bullets and len(question_bullets) != 1:
            report.fail(
                "Parent `## Open Questions` cannot mix `- None — <reason>` "
                "with question bullets."
            )
        elif not none_bullets:
            malformed_questions = [
                line
                for line in question_bullets
                if not NON_BLOCKING_QUESTION_RE.match(line)
            ]
            if malformed_questions:
                report.fail(
                    "Parent `## Open Questions` contains "
                    f"{len(malformed_questions)} question bullet(s) outside the "
                    "structured non-blocking question contract."
                )

    # 6. Warn on unexpected sections.
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
        if not BULLET_RE.match(line) or line[:1].isspace():
            continue
        match = CHILD_PATH_RE.search(line)
        if match:
            paths.append(match.group(1))
        else:
            pathless_bullets.append(line.strip())
    return paths, pathless_bullets


def normalize_child_reference(raw_path: str) -> str | None:
    """Return the canonical repo-relative child path, or None when unsafe."""
    candidate = Path(raw_path.strip())
    if candidate.is_absolute() or ".." in candidate.parts:
        return None
    if len(candidate.parts) != 3 or candidate.parts[:2] != CHILD_REFERENCE_PREFIX:
        return None
    if candidate.suffix != ".md" or candidate.name in ("", ".md"):
        return None
    return candidate.as_posix()


def resolve_child_path(parent_path: Path, raw_path: str) -> Path | None:
    """Resolve only the exact normalized repo-relative child reference."""
    normalized = normalize_child_reference(raw_path)
    if normalized is None:
        return None
    parent_directory = parent_path.resolve().parent
    if (
        parent_directory.name == "briefs"
        and parent_directory.parent.name == "docs"
    ):
        repo_root = parent_directory.parent.parent
    else:
        repo_root = Path.cwd().resolve()
    expected_briefs_directory = (repo_root / "docs" / "briefs").resolve()
    resolved = (repo_root / normalized).resolve()
    try:
        resolved.relative_to(expected_briefs_directory)
    except ValueError:
        return None
    if resolved.parent != expected_briefs_directory:
        return None
    return resolved if resolved.is_file() else None


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
        report.fail(
            "Briefset must list at least 2 distinct child plans; found 0. "
            "Collapse one execution context to single-plan mode."
        )
        return []

    normalized_paths: list[str] = []
    for raw in raw_paths:
        normalized = normalize_child_reference(raw)
        if normalized is None:
            report.fail(
                f"Invalid child reference '{raw}' — use the exact repo-relative "
                "`docs/briefs/<child>.md` path; absolute paths, nested paths, "
                "and `..` escapes are not allowed."
            )
            continue
        normalized_paths.append(normalized)

    unique_paths: list[str] = []
    warned_duplicates: set[str] = set()
    for raw in normalized_paths:
        if raw not in unique_paths:
            unique_paths.append(raw)
        elif raw not in warned_duplicates:
            warned_duplicates.add(raw)
            report.warn(
                f"`## Child Briefs` lists '{raw}' more than once — "
                "validating it once."
            )

    if len(unique_paths) < 2:
        report.fail(
            "Briefset must list at least 2 distinct child plans; "
            f"found {len(unique_paths)}. Collapse one execution context to single-plan mode."
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


def normalize_artifact_path(raw_path: str) -> str | None:
    """Return a safe repo-relative handoff or hotspot path."""
    stripped = raw_path.strip()
    candidate = Path(stripped)
    if (
        not stripped
        or candidate.is_absolute()
        or stripped.startswith("~")
        or "://" in stripped
        or "\\" in stripped
        or ".." in candidate.parts
        or any(character in stripped for character in "*?[]")
        or not looks_like_path(stripped)
    ):
        return None
    if candidate.as_posix() in ("", "."):
        return None
    return candidate.as_posix()


def validate_artifact_path(
    raw_path: str,
    is_proposed: bool,
    repo_root: Path,
    label: str,
    report: Report,
) -> str | None:
    """Validate a stable repo-relative artifact locator and its existence."""
    normalized = normalize_artifact_path(raw_path)
    if normalized is None:
        report.fail(
            f"{label} uses invalid path '{raw_path}' — use a concrete "
            "repo-relative path without absolute, parent, home, URL, "
            "backslash, or glob syntax."
        )
        return None
    if not (repo_root / normalized).exists() and not is_proposed:
        report.fail(
            f"{label} path '{normalized}' does not exist under {repo_root}; "
            "append `(proposed)` immediately after the inline path when the "
            "work will create it."
        )
    return normalized


def joined_block_text(block: list[str]) -> str:
    return " ".join(line.strip() for line in block if line.strip())


def extract_coordination_children(
    text: str,
    child_references: set[str],
    section_name: str,
    entry_number: int,
    report: Report,
) -> list[str]:
    """Extract canonical child paths only from a fixed child-list field."""
    normalized_references: list[str] = []
    for match in INLINE_CODE_RE.finditer(text):
        raw_reference = match.group(1).strip()
        normalized = normalize_child_reference(raw_reference)
        if normalized is None:
            report.fail(
                f"`## {section_name}` entry {entry_number} uses invalid child "
                f"reference '{raw_reference}' — use the exact repo-relative "
                "`docs/briefs/<child>.md` path."
            )
            continue
        if normalized not in child_references:
            report.fail(
                f"`## {section_name}` entry {entry_number} references "
                f"'{normalized}', which is not listed in `## Child Briefs`."
            )
            continue
        normalized_references.append(normalized)
    return normalized_references


def validate_execution_order_contract(
    h2: dict[str, list[str]],
    child_references: set[str],
    repo_root: Path,
    report: Report,
) -> tuple[dict[str, str], dict[str, int]]:
    """Return validated child deliverable locations and wave numbers."""
    failures_before = len(report.failures)
    execution_references: list[str] = []
    execution_locations: dict[str, str] = {}
    execution_waves: dict[str, int] = {}
    wave_numbers: list[int] = []
    for entry_number, block in enumerate(
        top_level_bullet_blocks(h2.get("Execution Order", [])), start=1
    ):
        match = EXECUTION_ORDER_ENTRY_RE.match(joined_block_text(block))
        if not match:
            subject_match = CHILD_PATH_RE.search(joined_block_text(block))
            if subject_match:
                normalized_subject = normalize_child_reference(subject_match.group(1))
                if (
                    normalized_subject is not None
                    and normalized_subject in child_references
                ):
                    execution_references.append(normalized_subject)
            report.fail(
                f"`## Execution Order` entry {entry_number} must use "
                "`Wave N — <child>: Start: ...; Deliverable: ...; "
                "Location: `<path>` [(proposed)]; Done: ...; Handoff: ...`."
            )
            continue
        normalized_child = normalize_child_reference(match.group("child"))
        if normalized_child is None or normalized_child not in child_references:
            report.fail(
                f"`## Execution Order` entry {entry_number} names an unlisted "
                "or invalid child path."
            )
            continue
        normalized_location = validate_artifact_path(
            match.group("location"),
            bool(match.group("proposed")),
            repo_root,
            f"`## Execution Order` entry {entry_number} Location",
            report,
        )
        execution_references.append(normalized_child)
        wave_number = int(match.group("wave"))
        wave_numbers.append(wave_number)
        execution_waves[normalized_child] = wave_number
        if normalized_location is not None:
            execution_locations[normalized_child] = normalized_location

    for child_reference in sorted(child_references):
        occurrence_count = execution_references.count(child_reference)
        if occurrence_count == 0:
            report.fail(
                f"`## Execution Order` does not reference child '{child_reference}'."
            )
        elif occurrence_count > 1:
            report.fail(
                f"`## Execution Order` references child '{child_reference}' "
                f"{occurrence_count} times; list each child exactly once."
            )
    unique_waves = sorted(set(wave_numbers))
    if unique_waves and unique_waves != list(range(1, unique_waves[-1] + 1)):
        report.fail(
            "`## Execution Order` wave numbers must start at 1 and be "
            f"consecutive; found {unique_waves}."
        )
    if len(report.failures) == failures_before and child_references and all(
        execution_references.count(child_reference) == 1
        for child_reference in child_references
    ):
        report.ok(
            "`## Execution Order` references every child exactly once with "
            "a concrete deliverable location."
        )
    return execution_locations, execution_waves


def parse_dependency_edges(
    h2: dict[str, list[str]],
    child_references: set[str],
    repo_root: Path,
    execution_locations: dict[str, str],
    execution_waves: dict[str, int],
    report: Report,
) -> list[DependencyEdge]:
    """Parse fixed predecessor -> artifact -> successor contracts."""
    failures_before = len(report.failures)
    blocks = top_level_bullet_blocks(h2.get("Dependencies", []))
    if not blocks:
        report.fail(
            "`## Dependencies` must contain top-level bullets using the fixed "
            "edge contract or `- None — <reason>`."
        )
        return []
    if any(NONE_WITH_REASON_RE.match(block[0].strip()) for block in blocks):
        if len(blocks) != 1:
            report.fail(
                "`## Dependencies` cannot mix `- None — <reason>` with "
                "dependency edges."
            )
        return []

    edges: list[DependencyEdge] = []
    seen_pairs: set[tuple[str, str]] = set()
    for entry_number, block in enumerate(blocks, start=1):
        match = DEPENDENCY_EDGE_RE.match(joined_block_text(block))
        if not match:
            report.fail(
                f"`## Dependencies` entry {entry_number} must use the fixed "
                "`Predecessor; Deliverable path; Format; Successor; Starts "
                "when; Verify; Inputs; Expected` contract."
            )
            continue
        predecessor = normalize_child_reference(match.group("predecessor"))
        successor = normalize_child_reference(match.group("successor"))
        if predecessor is None or predecessor not in child_references:
            report.fail(
                f"`## Dependencies` entry {entry_number} has an invalid or "
                "unlisted predecessor."
            )
            continue
        if successor is None or successor not in child_references:
            report.fail(
                f"`## Dependencies` entry {entry_number} has an invalid or "
                "unlisted successor."
            )
            continue
        if predecessor == successor:
            report.fail(
                f"`## Dependencies` entry {entry_number} creates a self-dependency."
            )
            continue
        predecessor_wave = execution_waves.get(predecessor)
        successor_wave = execution_waves.get(successor)
        if (
            predecessor_wave is not None
            and successor_wave is not None
            and predecessor_wave >= successor_wave
        ):
            report.fail(
                f"`## Dependencies` entry {entry_number} places predecessor "
                f"wave {predecessor_wave} at or after successor wave "
                f"{successor_wave}."
            )
        pair = (predecessor, successor)
        if pair in seen_pairs:
            report.fail(
                f"`## Dependencies` repeats edge '{predecessor}' → '{successor}'."
            )
            continue
        seen_pairs.add(pair)
        deliverable_path = validate_artifact_path(
            match.group("deliverable"),
            bool(match.group("proposed")),
            repo_root,
            f"`## Dependencies` entry {entry_number} Deliverable path",
            report,
        )
        if deliverable_path is None:
            continue
        parent_location = execution_locations.get(predecessor)
        if parent_location is not None and parent_location != deliverable_path:
            report.fail(
                f"`## Dependencies` entry {entry_number} uses deliverable "
                f"'{deliverable_path}', but the predecessor's Execution Order "
                f"Location is '{parent_location}'."
            )
        edges.append(DependencyEdge(predecessor, successor, deliverable_path))

    if edges and len(report.failures) == failures_before:
        report.ok(
            f"`## Dependencies` defines {len(edges)} addressable handoff "
            "edge(s) with format and verification signals."
        )
    return edges


def parse_parallelization_contract(
    h2: dict[str, list[str]],
    child_references: set[str],
    dependency_edges: list[DependencyEdge],
    report: Report,
) -> tuple[set[frozenset[str]], set[frozenset[str]]]:
    """Return can-run and must-not-overlap child pairs."""
    blocks = top_level_bullet_blocks(h2.get("Parallelization", []))
    if not blocks:
        report.fail(
            "`## Parallelization` must contain top-level pair bullets or "
            "`- None — <reason>`."
        )
        return set(), set()
    if any(NONE_WITH_REASON_RE.match(block[0].strip()) for block in blocks):
        if len(blocks) != 1:
            report.fail(
                "`## Parallelization` cannot mix `- None — <reason>` with "
                "pair declarations."
            )
        return set(), set()

    can_run_pairs: set[frozenset[str]] = set()
    must_not_pairs: set[frozenset[str]] = set()
    for entry_number, block in enumerate(blocks, start=1):
        text = joined_block_text(block)
        prefix_match = PARALLELIZATION_PREFIX_RE.match(text)
        if not prefix_match:
            report.fail(
                f"`## Parallelization` entry {entry_number} must start with "
                "`Can run together:` or `Must not overlap:`."
            )
            continue
        if not re.search(r"Join when:\s+\S", text):
            report.fail(
                f"`## Parallelization` entry {entry_number} must include its "
                "own non-empty `Join when:` value."
            )
        if " — " not in text:
            report.fail(
                f"`## Parallelization` entry {entry_number} must separate "
                "the child pair from its evidence with an em dash."
            )
            continue
        child_segment = text[prefix_match.end() :].split(" — ", 1)[0]
        references = extract_coordination_children(
            child_segment,
            child_references,
            "Parallelization",
            entry_number,
            report,
        )
        if len(references) != 2 or len(set(references)) != 2:
            report.fail(
                f"`## Parallelization` entry {entry_number} must describe "
                "exactly one pair of two distinct children."
            )
            continue
        pair = frozenset(references)
        target = (
            can_run_pairs
            if prefix_match.group("mode") == "Can run together"
            else must_not_pairs
        )
        if pair in target:
            report.fail(
                f"`## Parallelization` repeats the same child pair in "
                f"entry {entry_number}."
            )
        target.add(pair)

    for pair in can_run_pairs & must_not_pairs:
        report.fail(
            "`## Parallelization` declares the same child pair both "
            f"parallel and serialized: {sorted(pair)}."
        )
    dependency_pairs = {
        frozenset((edge.predecessor, edge.successor)) for edge in dependency_edges
    }
    for pair in can_run_pairs & dependency_pairs:
        report.fail(
            "`## Parallelization` declares a predecessor/successor pair as "
            f"parallel: {sorted(pair)}."
        )
    return can_run_pairs, must_not_pairs


def validate_hotspot_contract(
    h2: dict[str, list[str]],
    child_references: set[str],
    repo_root: Path,
    can_run_pairs: set[frozenset[str]],
    report: Report,
) -> None:
    """Validate pairwise hotspot access and parallel consistency."""
    blocks = top_level_bullet_blocks(h2.get("Conflict Hotspots", []))
    if not blocks:
        report.fail(
            "`## Conflict Hotspots` must contain top-level pair bullets or "
            "`- None — <reason>`."
        )
        return
    if any(NONE_WITH_REASON_RE.match(block[0].strip()) for block in blocks):
        if len(blocks) != 1:
            report.fail(
                "`## Conflict Hotspots` cannot mix `- None — <reason>` "
                "with hotspot entries."
            )
        return

    serialized_pairs: set[frozenset[str]] = set()
    for entry_number, block in enumerate(blocks, start=1):
        match = HOTSPOT_ENTRY_RE.match(joined_block_text(block))
        if not match:
            report.fail(
                f"`## Conflict Hotspots` entry {entry_number} must use the "
                "fixed `path — Children; Access; [Owner;] Rule` contract."
            )
            continue
        validate_artifact_path(
            match.group("path"),
            bool(match.group("proposed")),
            repo_root,
            f"`## Conflict Hotspots` entry {entry_number}",
            report,
        )
        references = extract_coordination_children(
            match.group("children"),
            child_references,
            "Conflict Hotspots",
            entry_number,
            report,
        )
        if len(references) != 2 or len(set(references)) != 2:
            report.fail(
                f"`## Conflict Hotspots` entry {entry_number} must describe "
                "exactly one pair of two distinct children."
            )
            continue
        pair = frozenset(references)
        if match.group("access") == "serialized":
            owner = match.group("owner")
            normalized_owner = normalize_child_reference(owner or "")
            if normalized_owner is None or normalized_owner not in pair:
                report.fail(
                    f"`## Conflict Hotspots` entry {entry_number} with "
                    "`Access: serialized` must name one pair member as the "
                    "full-path `Owner`."
                )
            serialized_pairs.add(pair)

    for pair in can_run_pairs & serialized_pairs:
        report.fail(
            "A child pair is `Can run together` but a conflict hotspot marks "
            f"the same pair `Access: serialized`: {sorted(pair)}."
        )


def validate_coordination_references(
    h2: dict[str, list[str]],
    repo_root: Path,
    report: Report,
) -> tuple[list[DependencyEdge], dict[str, str]]:
    """Cross-check fixed coordination contracts across parent sections."""
    validate_fixed_parent_section_content(h2, report)
    if "Child Briefs" not in h2:
        return [], {}
    raw_children, _ = extract_child_paths(h2["Child Briefs"])
    child_references = {
        normalized
        for raw in raw_children
        if (normalized := normalize_child_reference(raw)) is not None
    }
    execution_locations, execution_waves = validate_execution_order_contract(
        h2, child_references, repo_root, report
    )
    dependency_edges = parse_dependency_edges(
        h2,
        child_references,
        repo_root,
        execution_locations,
        execution_waves,
        report,
    )
    can_run_pairs, _ = parse_parallelization_contract(
        h2, child_references, dependency_edges, report
    )
    validate_hotspot_contract(
        h2, child_references, repo_root, can_run_pairs, report
    )
    return dependency_edges, execution_locations


def validate_fixed_parent_section_content(
    h2: dict[str, list[str]], report: Report
) -> None:
    """Reject prose outside top-level bullets in fixed parent sections."""
    for section_name in FIXED_PARENT_BULLET_SECTIONS:
        saw_top_level_bullet = False
        for line in h2.get(section_name, []):
            if not line.strip():
                continue
            if BULLET_RE.match(line) and not line[:1].isspace():
                saw_top_level_bullet = True
                continue
            if not saw_top_level_bullet:
                report.fail(
                    f"`## {section_name}` has non-bullet content before the "
                    "first top-level bullet; put every fixed-format entry in "
                    "one top-level bullet."
                )
                continue
            if not line[:1].isspace():
                report.fail(
                    f"`## {section_name}` has non-bullet content outside a "
                    "top-level bullet; "
                    "put every fixed-format entry in one top-level bullet."
                )


def top_level_bullet_blocks(lines: list[str]) -> list[list[str]]:
    """Group each top-level bullet with its continuation and nested lines."""
    blocks: list[list[str]] = []
    current: list[str] | None = None
    for line in lines:
        if BULLET_RE.match(line) and not line[:1].isspace():
            if current is not None:
                blocks.append(current)
            current = [line]
        elif current is not None:
            current.append(line)
    if current is not None:
        blocks.append(current)
    return blocks


def validate_child_filename_consistency(
    child_path: Path,
    parent_date: str,
    set_slug: str,
    report: Report,
) -> None:
    """Fail when a child filename drifts from the parent's naming convention.

    Children should follow YYYY-MM-DD-<type>-<set-slug>-NN-<child-slug>.md
    with the parent's date and set-slug.
    """
    match = CHILD_FILENAME_RE.match(child_path.name)
    if not match:
        return  # validate_brief's filename check already fails this case.
    child_date, _, child_slug, _ = match.groups()
    label = f"child `{child_path.name}`"
    if child_date != parent_date:
        report.fail(
            f"{label}: filename date '{child_date}' differs from the "
            f"parent's date '{parent_date}'."
        )
    expected_slug_re = re.compile(
        rf"^{re.escape(set_slug)}-\d{{2}}-[a-z0-9][a-z0-9-]*$"
    )
    if not expected_slug_re.match(child_slug):
        report.fail(
            f"{label}: slug must follow `<set-slug>-NN-<child-slug>` with "
            f"set-slug '{set_slug}'."
        )


def validate_briefset_child_execution_contract(
    h3: dict[str, dict[str, list[str]]],
    h3_titles_by_h2: dict[str, list[str]],
    report: Report,
) -> None:
    """Validate briefset-only verification and no-change stage fields."""
    stages = h3.get("Execution Plan", {})
    stage_titles = [
        title
        for title in h3_titles_by_h2.get("Execution Plan", [])
        if EXECUTION_STAGE_RE.match(title)
    ]
    for stage_title in stage_titles:
        lines = stages.get(stage_title, [])
        verify_positions = [
            position
            for position, line in enumerate(lines)
            if line.startswith("- Verify:")
        ]
        if len(verify_positions) != 1:
            report.fail(
                f"`### {stage_title}` must contain exactly one briefset "
                "`- Verify: `<action>`; Inputs: <inputs>; Expected: <signal>` field."
            )
        else:
            verify_line = lines[verify_positions[0]]
            if not BRIEFSET_STAGE_VERIFY_RE.match(verify_line):
                report.fail(
                    f"`### {stage_title}` has a malformed `Verify` field; name "
                    "a bounded command or inspection, concrete inputs, and an "
                    "observable expected signal."
                )
            deliverable_positions = [
                position
                for position, line in enumerate(lines)
                if line.startswith("- Deliverable:")
            ]
            ends_positions = [
                position
                for position, line in enumerate(lines)
                if line.startswith("- Ends when:")
            ]
            if (
                len(deliverable_positions) == 1
                and len(ends_positions) == 1
                and not (
                    deliverable_positions[0]
                    < verify_positions[0]
                    < ends_positions[0]
                )
            ):
                report.fail(
                    f"`### {stage_title}` must place `Verify` after "
                    "`Deliverable` and before `Ends when`."
                )

    if not stage_titles:
        return
    first_stage_title = stage_titles[0]
    first_stage_lines = stages.get(first_stage_title, [])
    no_op_when_positions = [
        position
        for position, line in enumerate(first_stage_lines)
        if line.startswith("- No-op when:")
    ]
    no_op_handoff_positions = [
        position
        for position, line in enumerate(first_stage_lines)
        if line.startswith("- No-op handoff:")
    ]
    if len(no_op_when_positions) != 1:
        report.fail(
            f"`### {first_stage_title}` must contain exactly one "
            "`- No-op when:` field."
        )
    if len(no_op_handoff_positions) != 1:
        report.fail(
            f"`### {first_stage_title}` must contain exactly one "
            "`- No-op handoff:` field."
        )
    if len(no_op_when_positions) != 1 or len(no_op_handoff_positions) != 1:
        return

    no_op_when_line = first_stage_lines[no_op_when_positions[0]]
    no_op_handoff_line = first_stage_lines[no_op_handoff_positions[0]]
    no_op_when_value = no_op_when_line.split(":", 1)[1].strip()
    no_op_handoff_value = no_op_handoff_line.split(":", 1)[1].strip()
    when_is_none = bool(NONE_VALUE_PREFIX_RE.match(no_op_when_value))
    handoff_is_none = bool(NONE_VALUE_PREFIX_RE.match(no_op_handoff_value))
    if not no_op_when_value:
        report.fail(f"`### {first_stage_title}` has an empty `No-op when` value.")
    elif when_is_none and not NONE_VALUE_WITH_REASON_RE.match(no_op_when_value):
        report.fail(
            f"`### {first_stage_title}` must write `No-op when: None — <reason>` "
            "when a no-change route is impossible."
        )
    if not no_op_handoff_value:
        report.fail(
            f"`### {first_stage_title}` has an empty `No-op handoff` value."
        )
    elif handoff_is_none and not NONE_VALUE_WITH_REASON_RE.match(
        no_op_handoff_value
    ):
        report.fail(
            f"`### {first_stage_title}` must write "
            "`No-op handoff: None — <reason>` when no no-change evidence "
            "can be handed forward."
        )
    if when_is_none != handoff_is_none:
        report.fail(
            f"`### {first_stage_title}` must either define both the no-change "
            "condition and its handoff, or use reasoned `None` for both."
        )
    if not handoff_is_none:
        inline_locations = [
            match.group(1).strip()
            for match in INLINE_CODE_RE.finditer(no_op_handoff_value)
            if normalize_artifact_path(match.group(1)) is not None
        ]
        if not inline_locations:
            report.fail(
                f"`### {first_stage_title}` `No-op handoff` must name a "
                "path-shaped evidence location in inline code."
            )

    work_positions = [
        position
        for position, line in enumerate(first_stage_lines)
        if line.startswith("- Work:")
    ]
    deliverable_positions = [
        position
        for position, line in enumerate(first_stage_lines)
        if line.startswith("- Deliverable:")
    ]
    if len(work_positions) == 1 and len(deliverable_positions) == 1:
        expected_order = [
            work_positions[0],
            no_op_when_positions[0],
            no_op_handoff_positions[0],
            deliverable_positions[0],
        ]
        if expected_order != sorted(expected_order):
            report.fail(
                f"`### {first_stage_title}` must place `No-op when` and "
                "`No-op handoff` after `Work` and before `Deliverable`."
            )


def validate_child_brief(
    child_path: Path,
    report: Report,
    repo_root: Path,
) -> None:
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
    h2, h3, h2_titles, h3_titles_by_h2 = parse_sections(text)
    validate_child_sections(
        h2, h3, h2_titles, h3_titles_by_h2, title_type, sub
    )
    validate_child_entry_paths(h2, child_path, sub, repo_root)
    validate_briefset_child_execution_contract(h3, h3_titles_by_h2, sub)

    for msg in sub.failures:
        report.fail(f"{label}: {msg}")
    for msg in sub.warnings:
        report.warn(f"{label}: {msg}")
    if not sub.failures and not sub.warnings:
        report.ok(f"{label}: structural checks OK.")


def validate_dependency_handoffs(
    dependency_edges: list[DependencyEdge],
    child_paths: list[Path],
    report: Report,
) -> None:
    """Require each parent handoff path in its producer and consumer child."""
    child_path_map = {
        f"docs/briefs/{child_path.name}": child_path for child_path in child_paths
    }
    failures_before = len(report.failures)
    for edge in dependency_edges:
        predecessor_path = child_path_map.get(edge.predecessor)
        successor_path = child_path_map.get(edge.successor)
        if predecessor_path is None or successor_path is None:
            continue
        try:
            predecessor_text = predecessor_path.read_text(encoding="utf-8")
            successor_text = successor_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue  # The child-level read already reports the I/O failure.

        _, predecessor_h3, _, predecessor_h3_titles = parse_sections(
            predecessor_text
        )
        _, successor_h3, _, successor_h3_titles = parse_sections(successor_text)
        artifact_token = f"`{edge.deliverable_path}`"
        predecessor_lines = [
            line
            for stage_title in predecessor_h3_titles.get("Execution Plan", [])
            for line in predecessor_h3.get("Execution Plan", {}).get(stage_title, [])
            if line.startswith(
                ("- Deliverable:", "- Handoff:", "- No-op handoff:")
            )
        ]
        if not any(artifact_token in line for line in predecessor_lines):
            report.fail(
                f"Dependency producer '{edge.predecessor}' does not publish "
                f"the parent deliverable path {artifact_token} in a "
                "Deliverable, Handoff, or No-op handoff field."
            )

        predecessor_stage_titles = [
            title
            for title in predecessor_h3_titles.get("Execution Plan", [])
            if EXECUTION_STAGE_RE.match(title)
        ]
        if predecessor_stage_titles:
            predecessor_first_stage = predecessor_h3.get("Execution Plan", {}).get(
                predecessor_stage_titles[0], []
            )
            no_op_when_lines = [
                line
                for line in predecessor_first_stage
                if line.startswith("- No-op when:")
            ]
            no_op_handoff_lines = [
                line
                for line in predecessor_first_stage
                if line.startswith("- No-op handoff:")
            ]
            no_op_when_value = (
                no_op_when_lines[0].split(":", 1)[1].strip()
                if no_op_when_lines
                else ""
            )
            no_op_is_active = (
                bool(no_op_when_value)
                and not NONE_VALUE_PREFIX_RE.match(no_op_when_value)
            )
            if no_op_is_active and not any(
                artifact_token in line for line in no_op_handoff_lines
            ):
                report.fail(
                    f"Dependency producer '{edge.predecessor}' has an active "
                    f"no-change route but its `No-op handoff` does not publish "
                    f"parent deliverable path {artifact_token}."
                )

        successor_stage_titles = [
            title
            for title in successor_h3_titles.get("Execution Plan", [])
            if EXECUTION_STAGE_RE.match(title)
        ]
        successor_start_lines: list[str] = []
        if successor_stage_titles:
            successor_start_lines = [
                line
                for line in successor_h3.get("Execution Plan", {}).get(
                    successor_stage_titles[0], []
                )
                if line.startswith("- Starts when:")
            ]
        if not any(artifact_token in line for line in successor_start_lines):
            report.fail(
                f"Dependency consumer '{edge.successor}' does not name parent "
                f"deliverable path {artifact_token} in its first-stage "
                "`Starts when` field."
            )

    if dependency_edges and len(report.failures) == failures_before:
        report.ok(
            "Every dependency deliverable path is repeated in its producer "
            "and successor child execution plan."
        )


def parse_cli_arguments(argv: list[str]) -> tuple[Path, Path | None] | None:
    """Parse the parent path and optional repository-root override."""
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
    print(f"Validating briefset: {path}")
    print()

    parent_identity = validate_parent_filename(path, report)
    validate_parent_title(lines[0], report)
    h2, _, h2_titles, _ = parse_sections(text)
    validate_parent_sections(h2, h2_titles, report)

    effective_repo_root = (repo_root or infer_repo_root(path)).resolve()
    child_paths = validate_child_briefs_section(path, h2, report)
    dependency_edges, _ = validate_coordination_references(
        h2, effective_repo_root, report
    )

    if child_paths:
        print(f"Validating {len(child_paths)} child brief(s)...")
        print()
        for child_path in child_paths:
            if parent_identity is not None:
                parent_date, set_slug = parent_identity
                validate_child_filename_consistency(
                    child_path, parent_date, set_slug, report
                )
            validate_child_brief(child_path, report, effective_repo_root)
        validate_dependency_handoffs(dependency_edges, child_paths, report)

    print(report.render())
    return 1 if report.failures or report.warnings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
