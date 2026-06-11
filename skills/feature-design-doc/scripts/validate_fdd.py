#!/usr/bin/env python3
"""Validate the structural conformance of a Feature Design Doc.

Scope: structural checks only. This script does not evaluate the semantic
correctness of the content — that is the model's job.

Checks (this list is authoritative — SKILL.md defers to it):

  - YAML frontmatter: present; declares `doc-type: Feature Design Doc`;
    carries `created` and `last-verified` freshness metadata; `profile`
    value is valid (`full` default, or `compact`)
  - Required numbered sections present — full profile: 1-13;
    compact profile: 2, 3, 4, 7, 8, 9, 10, 12, 13 (1, 5, 6 become optional)
  - Required sections are not empty (heading present but no substantive body)
  - Section heading title drift from the canonical template (minor)
  - Numbered sections appearing out of document order (minor)
  - Duplicate numbered headings, and numbered subsections placed outside
    their parent section (critical — they make validation ambiguous)
  - Cross-cutting Concerns answered: subsections 11.1-11.6 (full profile,
    or compact docs that keep the subsections), or the condensed
    one-line-per-concern form (compact profile only); each concern needs
    real content or "Not applicable: <reason>" with a non-placeholder reason
  - Headings inside code fences are ignored, not parsed as sections

Optional sections (14 Platform Design, 15 Result Semantics, 16 Future
Extensions) are reported as present/absent without judgement, because their
trigger conditions are semantic. Unnumbered sections (`## Revision History`,
`## Appendix`) are not validated.

Not checked (the model's job): responsibility-map placement, implementation
leakage, factual accuracy against the codebase.

Usage:
    python3 scripts/validate_fdd.py <path-to-fdd.md>
    python3 scripts/validate_fdd.py <path-to-fdd.md> --format json
    python3 scripts/validate_fdd.py <path-to-fdd.md> --strict

Exit codes:
    0 — clean at the chosen threshold (default: no critical findings;
        with --strict: no critical and no major findings)
    1 — findings at or above the threshold
    2 — invocation error (file missing, etc.)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional


REQUIRED_SECTIONS: list[tuple[int, str]] = [
    (1, "Document Intent"),
    (2, "Background / Problem"),
    (3, "Feature Definition"),
    (4, "Goals & Non-Goals"),
    (5, "User Model & Core Concepts"),
    (6, "Relationship to Existing Features"),
    (7, "Primary User Flows"),
    (8, "Design"),
    (9, "Policy Decisions"),
    (10, "Alternatives Considered"),
    (11, "Cross-cutting Concerns"),
    (12, "Scope"),
    (13, "Risks & Open Questions"),
]

# Sections that drop from "required" to "optional" under `profile: compact`.
COMPACT_OPTIONAL: set[int] = {1, 5, 6}

OPTIONAL_SECTIONS: list[tuple[int, str]] = [
    (14, "Platform Design"),
    (15, "Result Semantics"),
    (16, "Future Extensions"),
]

CROSS_CUTTING: list[tuple[int, int, str]] = [
    (11, 1, "Security"),
    (11, 2, "Privacy"),
    (11, 3, "Permissions"),
    (11, 4, "Observability"),
    (11, 5, "Accessibility"),
    (11, 6, "Internationalization"),
]

H2_PATTERN = re.compile(r"^##\s+(\d+)\.\s+(.+?)\s*$")
H2_ANY_PATTERN = re.compile(r"^##\s+\S")
H3_PATTERN = re.compile(r"^###\s+(\d+)\.(\d+)\s+(.+?)\s*$")
FENCE_PATTERN = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
NOT_APPLICABLE_PATTERN = re.compile(
    r"^\s*[-*]\s*Not applicable\s*:\s*(.*?)\s*$", re.IGNORECASE
)
LOOSE_NA_PATTERN = re.compile(r"^\s*[-*]\s*Not applicable\b", re.IGNORECASE)
PLACEHOLDER_BULLET = re.compile(r"^\s*[-*]\s*\.{3}\s*$")
FRONTMATTER_PATTERN = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)


@dataclass
class Finding:
    severity: str  # "critical" | "major" | "minor"
    section: str
    message: str


@dataclass
class Report:
    file: str
    profile: str = "full"
    findings: list[Finding] = field(default_factory=list)
    optional_sections: dict[str, bool] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return not any(f.severity == "critical" for f in self.findings)

    @property
    def major_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "major")


@dataclass
class ParsedDoc:
    sections: dict[tuple[int, Optional[int]], tuple[str, int, list[str]]]
    structure_findings: list[Finding]


def parse_sections(text: str) -> ParsedDoc:
    """Parse numbered headings into (h2_num, h3_num_or_None) -> (title, line_no, body_lines).

    Fence-aware: headings inside ``` / ~~~ code fences are body text, not
    sections. Duplicate heading numbers and subsections outside their parent
    section are reported as critical structure findings; only the first
    occurrence of a key is kept.
    """
    sections: dict[tuple[int, Optional[int]], tuple[str, int, list[str]]] = {}
    structure_findings: list[Finding] = []
    lines = text.splitlines()
    current_key: Optional[tuple[int, Optional[int]]] = None
    current_title = ""
    current_start = 0
    current_body: list[str] = []
    current_h2_num: Optional[int] = None
    in_fence = False
    fence_char = ""
    fence_len = 0

    def flush() -> None:
        if current_key is not None:
            sections[current_key] = (current_title, current_start, list(current_body))

    for i, line in enumerate(lines, start=1):
        fence = FENCE_PATTERN.match(line)
        if fence:
            token = fence.group(1)
            if not in_fence:
                in_fence, fence_char, fence_len = True, token[0], len(token)
            elif token[0] == fence_char and len(token) >= fence_len:
                in_fence = False
            if current_key is not None:
                current_body.append(line)
            continue
        if in_fence:
            if current_key is not None:
                current_body.append(line)
            continue

        h2 = H2_PATTERN.match(line)
        h3 = H3_PATTERN.match(line)
        if h2:
            flush()
            num = int(h2.group(1))
            title = h2.group(2).strip()
            current_h2_num = num
            key = (num, None)
            if key in sections:
                structure_findings.append(
                    Finding(
                        "critical",
                        f"## {num}. {title}",
                        f"Duplicate section number at line {i} — only the first occurrence is validated.",
                    )
                )
                current_key = None
            else:
                current_key = key
                current_title = title
                current_start = i
                current_body = []
        elif h3:
            flush()
            parent, sub = int(h3.group(1)), int(h3.group(2))
            title = h3.group(3).strip()
            key = (parent, sub)
            if current_h2_num != parent:
                structure_findings.append(
                    Finding(
                        "critical",
                        f"### {parent}.{sub} {title}",
                        f"Subsection at line {i} sits outside its parent section — move it under '## {parent}.' (not counted as present).",
                    )
                )
                current_key = None
            elif key in sections:
                structure_findings.append(
                    Finding(
                        "critical",
                        f"### {parent}.{sub} {title}",
                        f"Duplicate subsection number at line {i} — only the first occurrence is validated.",
                    )
                )
                current_key = None
            else:
                current_key = key
                current_title = title
                current_start = i
                current_body = []
        elif H2_ANY_PATTERN.match(line):
            # Unnumbered H2 (## Appendix, ## Revision History) ends the numbered scope.
            flush()
            current_key = None
            current_h2_num = None
        elif current_key is not None:
            current_body.append(line)
    flush()
    return ParsedDoc(sections, structure_findings)


def is_substantive(body: list[str]) -> bool:
    """Body has at least one non-blank, non-blockquote, non-placeholder line."""
    for line in body:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(">"):
            continue
        if PLACEHOLDER_BULLET.match(line):
            continue
        if stripped in {"-", "*"}:
            continue
        return True
    return False


def is_real_reason(reason: str) -> bool:
    """A 'Not applicable' reason that is not a placeholder."""
    reason = reason.strip()
    if not reason or reason in {"...", "…"}:
        return False
    if re.fullmatch(r"\[.*\]", reason):  # template placeholder like [short reason]
        return False
    return True


def section_has_content(
    sections: dict[tuple[int, Optional[int]], tuple[str, int, list[str]]], num: int
) -> bool:
    """True if the section's own body or any of its subsections has substance."""
    for (h2, _sub), (_title, _line, body) in sections.items():
        if h2 == num and is_substantive(body):
            return True
    return False


def check_na_body(report: Report, label: str, body: list[str]) -> None:
    """Check one cross-cutting subsection body for the N/A contract."""
    strict = [m for line in body if (m := NOT_APPLICABLE_PATTERN.match(line))]
    loose_only = [
        line
        for line in body
        if LOOSE_NA_PATTERN.match(line) and not NOT_APPLICABLE_PATTERN.match(line)
    ]
    non_na_lines = [line for line in body if not LOOSE_NA_PATTERN.match(line)]
    has_other_content = is_substantive(non_na_lines)

    for m in strict:
        if not is_real_reason(m.group(1)):
            report.findings.append(
                Finding(
                    "major",
                    label,
                    "'Not applicable' has no reason — write 'Not applicable: <short reason>'.",
                )
            )
            break
    if loose_only:
        # A colonless "Not applicable" alongside real content is more likely
        # ordinary prose than a broken marker — downgrade to minor.
        severity = "minor" if has_other_content else "major"
        report.findings.append(
            Finding(
                severity,
                label,
                "'Not applicable' is missing the colon and reason — write 'Not applicable: <short reason>'."
                + (" (If this line is ordinary prose, ignore.)" if severity == "minor" else ""),
            )
        )
    if not strict and not loose_only and not is_substantive(body):
        report.findings.append(
            Finding(
                "critical",
                label,
                "Subsection is silent — provide content or 'Not applicable: <reason>'.",
            )
        )


def check_condensed_concern(report: Report, name: str, body: list[str]) -> None:
    """Check one concern in the compact-profile condensed list (bullet or table row)."""
    pattern = re.compile(
        rf"^\s*(?:[-*]\s*|\|\s*)?\*{{0,2}}{name}\*{{0,2}}\s*[:|]\s*(.*?)\s*\|?\s*$"
    )
    label = f"## 11. Cross-cutting Concerns — {name}"
    for line in body:
        m = pattern.match(line)
        if not m:
            continue
        remainder = m.group(1).strip()
        na = re.match(r"^Not applicable\s*(?::\s*(.*))?$", remainder, re.IGNORECASE)
        if na:
            if not is_real_reason(na.group(1) or ""):
                report.findings.append(
                    Finding(
                        "major",
                        label,
                        "'Not applicable' has no reason — write 'Not applicable: <short reason>'.",
                    )
                )
        elif not remainder or remainder in {"...", "…"}:
            report.findings.append(
                Finding(
                    "critical",
                    label,
                    "Concern is listed but unanswered — provide content or 'Not applicable: <reason>'.",
                )
            )
        return
    report.findings.append(
        Finding(
            "critical",
            label,
            f"Condensed Cross-cutting list is missing '{name}' — every concern must be answered.",
        )
    )


def validate(text: str, source: str) -> Report:
    parsed = parse_sections(text)
    sections = parsed.sections

    profile = "full"
    fm_findings: list[Finding] = []
    fm_match = FRONTMATTER_PATTERN.match(text)
    fm = fm_match.group(1) if fm_match else ""
    if not fm_match or not re.search(r"^[A-Za-z][\w-]*\s*:", fm, re.MULTILINE):
        fm_findings.append(
            Finding(
                "major",
                "frontmatter",
                "Missing YAML frontmatter (expected 'doc-type: Feature Design Doc' block at top).",
            )
        )
    else:
        if not re.search(
            r"""^doc-type\s*:\s*["']?Feature Design Doc["']?\s*$""", fm, re.MULTILINE
        ):
            fm_findings.append(
                Finding(
                    "minor",
                    "frontmatter",
                    "Frontmatter is present but does not declare 'doc-type: Feature Design Doc'.",
                )
            )
        for meta_key in ("created", "last-verified"):
            if not re.search(rf"^{meta_key}\s*:\s*\S", fm, re.MULTILINE):
                fm_findings.append(
                    Finding(
                        "minor",
                        "frontmatter",
                        f"Frontmatter is missing '{meta_key}' — future readers cannot judge freshness.",
                    )
                )
        profile_match = re.search(
            r"""^profile\s*:\s*["']?([\w-]+)["']?""", fm, re.MULTILINE
        )
        if profile_match:
            value = profile_match.group(1).lower()
            if value in {"full", "compact"}:
                profile = value
            else:
                fm_findings.append(
                    Finding(
                        "minor",
                        "frontmatter",
                        f"Unknown profile '{value}' — expected 'full' or 'compact'; validating as 'full'.",
                    )
                )

    report = Report(file=source, profile=profile)
    report.findings.extend(fm_findings)
    report.findings.extend(parsed.structure_findings)

    for num, expected_title in REQUIRED_SECTIONS:
        required_here = profile == "full" or num not in COMPACT_OPTIONAL
        key = (num, None)
        if key not in sections:
            if required_here:
                report.findings.append(
                    Finding(
                        "critical",
                        f"## {num}. {expected_title}",
                        "Required section is missing.",
                    )
                )
            else:
                report.optional_sections[
                    f"{num}. {expected_title} (compact-optional)"
                ] = False
            continue
        if not required_here:
            report.optional_sections[f"{num}. {expected_title} (compact-optional)"] = True
        actual_title = sections[key][0]
        if actual_title.lower().strip() != expected_title.lower().strip():
            report.findings.append(
                Finding(
                    "minor",
                    f"## {num}. {actual_title}",
                    f"Section title drifts from canonical: expected '{expected_title}'.",
                )
            )
        # Section 11's substance is judged by the cross-cutting checks below.
        if num != 11 and not section_has_content(sections, num):
            report.findings.append(
                Finding(
                    "major",
                    f"## {num}. {expected_title}",
                    "Section is present but has no substantive content.",
                )
            )

    h2_in_doc_order = [
        num
        for _line, num in sorted(
            (line, num)
            for (num, sub), (_t, line, _b) in sections.items()
            if sub is None
        )
    ]
    if h2_in_doc_order != sorted(h2_in_doc_order):
        report.findings.append(
            Finding(
                "minor",
                "document",
                "Numbered sections are out of order — keep the template's numbering sequence.",
            )
        )

    for num, expected_title in OPTIONAL_SECTIONS:
        key = (num, None)
        present = key in sections
        report.optional_sections[f"{num}. {expected_title}"] = present
        if present:
            actual_title = sections[key][0]
            if actual_title.lower().strip() != expected_title.lower().strip():
                report.findings.append(
                    Finding(
                        "minor",
                        f"## {num}. {actual_title}",
                        f"Section number {num} should be '{expected_title}' — do not renumber when omitting optional sections.",
                    )
                )

    has_subsections = any((parent, sub) in sections for parent, sub, _ in CROSS_CUTTING)
    if has_subsections or profile == "full":
        for parent, sub, name in CROSS_CUTTING:
            key = (parent, sub)
            if key not in sections:
                report.findings.append(
                    Finding(
                        "critical",
                        f"### {parent}.{sub} {name}",
                        "Cross-cutting subsection missing — silence is indistinguishable from oversight.",
                    )
                )
                continue
            check_na_body(report, f"### {parent}.{sub} {name}", sections[key][2])
    elif (11, None) in sections:
        # Compact profile, condensed one-line-per-concern form.
        body = sections[(11, None)][2]
        for _parent, _sub, name in CROSS_CUTTING:
            check_condensed_concern(report, name, body)
    # If section 11 is missing entirely, the required-section loop already
    # reported it as critical.

    return report


def format_text(report: Report) -> str:
    out: list[str] = []
    if report.passed:
        status = (
            "PASS"
            if report.major_count == 0
            else f"PASS ({report.major_count} major unresolved)"
        )
    else:
        status = "FAIL"
    out.append(f"[{status}] {report.file}")
    out.append(f"  Profile: {report.profile}")
    if not report.findings:
        out.append("  No structural findings.")
    else:
        buckets: dict[str, list[Finding]] = {"critical": [], "major": [], "minor": []}
        for f in report.findings:
            buckets.setdefault(f.severity, []).append(f)
        for sev in ("critical", "major", "minor"):
            items = buckets.get(sev, [])
            if not items:
                continue
            out.append(f"\n  {sev.upper()} ({len(items)}):")
            for f in items:
                out.append(f"    - [{f.section}] {f.message}")
    if report.optional_sections:
        out.append("\n  Optional sections:")
        for name, present in report.optional_sections.items():
            out.append(f"    - {name}: {'present' if present else 'absent'}")
    return "\n".join(out)


def format_json(report: Report) -> str:
    return json.dumps(
        {
            "file": report.file,
            "profile": report.profile,
            "passed": report.passed,
            "major_count": report.major_count,
            "findings": [asdict(f) for f in report.findings],
            "optional_sections": report.optional_sections,
        },
        indent=2,
        ensure_ascii=False,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Feature Design Doc structure (template conformance only)."
    )
    parser.add_argument("path", help="Path to the FDD markdown file.")
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on major findings too (default threshold: critical only).",
    )
    args = parser.parse_args()

    p = Path(args.path)
    if not p.is_file():
        print(f"error: file not found: {p}", file=sys.stderr)
        return 2

    text = p.read_text(encoding="utf-8")
    report = validate(text, str(p))

    if args.format == "json":
        print(format_json(report))
    else:
        print(format_text(report))

    failed = (not report.passed) or (args.strict and report.major_count > 0)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
