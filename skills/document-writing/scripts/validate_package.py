#!/usr/bin/env python3
"""Validate the document-writing skill package structure.

Structural only: this script does not judge document quality, model routing,
external-source freshness, or whether an LLM opened a cited page.

Exit codes:
  0  package structure is valid
  1  validation failures were found
  2  invalid arguments or unreadable input
"""

from __future__ import annotations

import argparse
from datetime import date
import fnmatch
import hashlib
import json
import re
import shutil
import struct
import subprocess
import sys
import zlib
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import unquote, urlparse


EXIT_OK = 0
EXIT_VALIDATION = 1
EXIT_USAGE = 2

FRONTMATTER_RE = re.compile(r"\A---\n(?P<body>.*?)\n---(?:\n|\Z)", re.DOTALL)
LINK_RE = re.compile(r"\[[^\]]*\]\((?P<target>[^)]+)\)")
FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)

REQUIRED_PACKAGE_FILES = (
    "SKILL.md",
    "evals/evals.json",
    "evals/trigger-evals.json",
    "evals/production-evidence.json",
    "evals/production-suite.json",
    "evals/design-system-selection-evals.json",
    "evals/README.md",
    "evals/validators/validate_existing_update.mjs",
    "evals/validators/validate_preservation.mjs",
    "evals/validators/validate_noncanonical_store.mjs",
    "scripts/run_production_evals.py",
    "scripts/validate_eval_run.py",
    "scripts/test_eval_validators.py",
    "references/document-types/design-system/design-system-overview.md",
    "references/document-types/design-system/design-system-authoring.md",
    "references/document-types/design-system/design-system-review.md",
    "references/document-types/design-system/platform-adaptation.md",
    "references/document-types/design-system/storefront-research.md",
    "references/document-types/design-system/prebuilts/default.md",
    "references/document-types/design-system/prebuilts/app-store-page.md",
)

PRODUCTION_BEHAVIOR_IDS = (11, 19, 20, 21, 22, 23, 25, 26, 27, 28)
SELECTION_CASE_COUNT = 60
SELECTION_LABEL_COUNTS = {True: 30, False: 30}
SELECTION_LANGUAGE_COUNTS = {"ko": 30, "en": 18, "mixed": 12}
DIRECT_EVENT_NAMES = {
    "Read", "Write", "Edit", "Bash", "WebSearch", "WebFetch",
    "BrowserOpen", "MCP", "image_gen", "HarnessArtifactWrite",
}
CLARIFICATION_EVAL_IDS = {21, 26, 27}
EXECUTION_MODEL = "gpt-5.6-luna"
EXECUTION_REASONING_EFFORT = "medium"
HARD_GATE_NAMES = {
    "existing-document-preservation",
    "review-no-mutation",
    "collision-no-overwrite",
    "web-unavailable-no-hallucination",
}
REQUIRED_ARTIFACT_KINDS = {
    "behavior-results",
    "selection-results",
    "blind-comparison",
    "image-canary",
    "image-canary-document",
    "image-canary-generation",
    "image-canary-source",
    "review",
}
DIAGNOSTIC_REQUIRED_ARTIFACT_KINDS = REQUIRED_ARTIFACT_KINDS | {
    "measurement-summary",
    "integrity",
    "image-canary-manifest",
}

CRITICAL_EVALS = {
    11: "existing-design-system-preservation",
    14: "included-and-excluded-storefronts",
    19: "generic-storefront-discovery",
    20: "review-no-mutation",
    21: "collision-no-overwrite",
    22: "reuse-noncanonical-storefront-path",
    23: "mixed-prebuilt-output-sets",
    24: "mixed-document-and-asset-production",
    25: "web-unavailable-generic-storefront",
    26: "multifile-root-given-as-markdown",
    27: "collective-platform-ambiguity",
}

FIXTURE_REQUIRED_EVALS = {11, 20, 21, 22}

CRITICAL_CAPABILITY_CONTRACTS = {
    19: ({"web"}, set()),
    24: ({"web", "image-generation"}, set()),
    25: (set(), {"web"}),
}

NODE_VALIDATORS = (
    "evals/validators/validate_existing_update.mjs",
    "evals/validators/validate_preservation.mjs",
    "evals/validators/validate_noncanonical_store.mjs",
)

PYTHON_EVAL_SCRIPTS = (
    "scripts/run_production_evals.py",
    "scripts/validate_eval_run.py",
    "scripts/test_eval_validators.py",
)

@dataclass
class Report:
    failures: list[str] = field(default_factory=list)
    passes: list[str] = field(default_factory=list)

    def fail(self, message: str) -> None:
        self.failures.append(message)

    def ok(self, message: str) -> None:
        self.passes.append(message)

    def as_json(self) -> str:
        return json.dumps(
            {
                "valid": not self.failures,
                "failures": self.failures,
                "passes": self.passes,
            },
            ensure_ascii=False,
            indent=2,
        )

    def as_text(self) -> str:
        lines = [f"PASS: {item}" for item in self.passes]
        lines.extend(f"FAIL: {item}" for item in self.failures)
        lines.append(
            f"Summary: {len(self.passes)} passed, {len(self.failures)} failed"
        )
        return "\n".join(lines)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc


def read_json(path: Path) -> Any:
    try:
        return json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc


def is_within(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


def validate_required_files(skill_root: Path, report: Report) -> None:
    missing = [item for item in REQUIRED_PACKAGE_FILES if not (skill_root / item).is_file()]
    if missing:
        for item in missing:
            report.fail(f"required package file is missing: {item}")
        return
    report.ok(f"all {len(REQUIRED_PACKAGE_FILES)} required package files exist")


def validate_frontmatter(skill_root: Path, report: Report) -> None:
    skill_file = skill_root / "SKILL.md"
    content = read_text(skill_file)
    match = FRONTMATTER_RE.match(content)
    if not match:
        report.fail("SKILL.md has no valid YAML frontmatter boundary")
        return

    fields: dict[str, str] = {}
    for line in match.group("body").splitlines():
        if not line or line[0].isspace() or ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip()

    if fields.get("name") != skill_root.name:
        report.fail(
            f"frontmatter name must equal directory name {skill_root.name!r}"
        )
    elif not fields.get("description"):
        report.fail("frontmatter description must be a non-empty scalar")
    else:
        report.ok("SKILL.md frontmatter name and description are present")


def validate_eval_manifest(skill_root: Path, report: Report) -> None:
    path = skill_root / "evals/evals.json"
    payload = read_json(path)
    if not isinstance(payload, dict) or payload.get("skill_name") != skill_root.name:
        report.fail("evals/evals.json must name the owning skill")
        return

    evals = payload.get("evals")
    if not isinstance(evals, list) or not evals:
        report.fail("evals/evals.json must contain a non-empty evals array")
        return

    seen_ids: set[int] = set()
    seen_critical: set[int] = set()
    referenced_fixture_paths: set[str] = set()
    file_count = 0
    for index, item in enumerate(evals):
        label = f"evals[{index}]"
        if not isinstance(item, dict):
            report.fail(f"{label} must be an object")
            continue

        eval_id = item.get("id")
        if not isinstance(eval_id, int) or eval_id in seen_ids:
            report.fail(f"{label}.id must be a unique integer")
        else:
            seen_ids.add(eval_id)
            expected_name = CRITICAL_EVALS.get(eval_id)
            if expected_name is not None:
                seen_critical.add(eval_id)
                if item.get("eval_name") != expected_name:
                    report.fail(
                        f"{label}.eval_name must remain {expected_name!r}"
                    )

        for key in ("prompt", "expected_output"):
            if not isinstance(item.get(key), str) or not item[key].strip():
                report.fail(f"{label}.{key} must be a non-empty string")

        expectations = item.get("expectations")
        if not isinstance(expectations, list) or not expectations or not all(
            isinstance(value, str) and value.strip() for value in expectations
        ):
            report.fail(f"{label}.expectations must contain non-empty strings")

        capability_sets: dict[str, set[str]] = {}
        for key in ("required_capabilities", "denied_capabilities"):
            values = item.get(key, [])
            if not isinstance(values, list) or not all(
                isinstance(value, str) and value.strip() for value in values
            ):
                report.fail(f"{label}.{key} must be a string array when present")
                capability_sets[key] = set()
            elif len(values) != len(set(values)):
                report.fail(f"{label}.{key} contains duplicates")
                capability_sets[key] = set(values)
            else:
                capability_sets[key] = set(values)
        overlap = capability_sets["required_capabilities"] & capability_sets["denied_capabilities"]
        if overlap:
            report.fail(f"{label} both requires and denies capabilities: {sorted(overlap)}")
        expected_capabilities = CRITICAL_CAPABILITY_CONTRACTS.get(eval_id)
        if expected_capabilities is not None:
            required, denied = expected_capabilities
            if capability_sets["required_capabilities"] != required:
                report.fail(
                    f"{label}.required_capabilities must remain {sorted(required)}"
                )
            if capability_sets["denied_capabilities"] != denied:
                report.fail(
                    f"{label}.denied_capabilities must remain {sorted(denied)}"
                )

        files = item.get("files")
        if not isinstance(files, list) or not all(isinstance(value, str) for value in files):
            report.fail(f"{label}.files must be a string array")
            continue
        for relative in files:
            if not relative.startswith("evals/fixtures/"):
                report.fail(f"{label}.files must reference evals/fixtures/: {relative}")
            if relative in referenced_fixture_paths:
                report.fail(f"fixture path is referenced more than once: {relative}")
            else:
                referenced_fixture_paths.add(relative)
            resolved = (skill_root / relative).resolve()
            if not is_within(skill_root, resolved):
                report.fail(f"{label}.files escapes the skill root: {relative}")
            elif not resolved.is_file():
                report.fail(f"{label}.files does not exist: {relative}")
            else:
                file_count += 1
        if eval_id in FIXTURE_REQUIRED_EVALS and not files:
            report.fail(f"{label} is a critical fixture-backed eval and cannot have empty files")

    missing_critical = sorted(set(CRITICAL_EVALS) - seen_critical)
    if missing_critical:
        report.fail(f"critical production eval IDs are missing: {missing_critical}")

    actual_fixture_paths = {
        path.relative_to(skill_root).as_posix()
        for path in (skill_root / "evals/fixtures").rglob("*")
        if path.is_file()
    }
    if referenced_fixture_paths != actual_fixture_paths:
        missing = sorted(actual_fixture_paths - referenced_fixture_paths)
        stale = sorted(referenced_fixture_paths - actual_fixture_paths)
        report.fail(
            f"fixture manifest mismatch: unreferenced={missing}, missing={stale}"
        )

    if not report.failures:
        report.ok(f"{len(evals)} behavior evals and {file_count} fixture files are valid")


def validate_trigger_manifest(skill_root: Path, report: Report) -> None:
    path = skill_root / "evals/trigger-evals.json"
    payload = read_json(path)
    if not isinstance(payload, list) or not payload:
        report.fail("trigger-evals.json must contain a non-empty array")
        return

    queries: set[str] = set()
    positive = 0
    negative = 0
    for index, item in enumerate(payload):
        label = f"trigger-evals[{index}]"
        if not isinstance(item, dict):
            report.fail(f"{label} must be an object")
            continue
        query = item.get("query")
        should_trigger = item.get("should_trigger")
        if not isinstance(query, str) or not query.strip():
            report.fail(f"{label}.query must be a non-empty string")
        elif query in queries:
            report.fail(f"duplicate trigger query at {label}")
        else:
            queries.add(query)
        if not isinstance(should_trigger, bool):
            report.fail(f"{label}.should_trigger must be boolean")
        elif should_trigger:
            positive += 1
        else:
            negative += 1

    if positive == 0 or negative == 0:
        report.fail("trigger evals must include positive and negative cases")
    elif not report.failures:
        report.ok(
            f"{len(payload)} trigger evals are valid ({positive} positive, {negative} negative)"
        )


def validate_selection_manifest(skill_root: Path, report: Report) -> None:
    """Validate the balanced, realistic skill-selection benchmark input."""
    path = skill_root / "evals/design-system-selection-evals.json"
    payload = read_json(path)
    if not isinstance(payload, list):
        report.fail("design-system-selection-evals.json must contain an array")
        return
    if len(payload) != SELECTION_CASE_COUNT:
        report.fail(
            "design-system-selection-evals.json must contain exactly "
            f"{SELECTION_CASE_COUNT} cases"
        )

    ids: set[int] = set()
    labels = {True: 0, False: 0}
    languages = {language: 0 for language in SELECTION_LANGUAGE_COUNTS}
    for index, item in enumerate(payload):
        label = f"selection-evals[{index}]"
        if not isinstance(item, dict):
            report.fail(f"{label} must be an object")
            continue
        eval_id = item.get("id")
        if not isinstance(eval_id, int) or eval_id in ids:
            report.fail(f"{label}.id must be a unique integer")
        else:
            ids.add(eval_id)
        for field in ("query", "category", "rationale"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                report.fail(f"{label}.{field} must be a non-empty string")
        should_trigger = item.get("should_trigger")
        if not isinstance(should_trigger, bool):
            report.fail(f"{label}.should_trigger must be boolean")
        else:
            labels[should_trigger] += 1
        language = item.get("language")
        if language not in languages:
            report.fail(
                f"{label}.language must be one of "
                f"{sorted(SELECTION_LANGUAGE_COUNTS)}"
            )
        else:
            languages[language] += 1
        if not isinstance(item.get("high_risk"), bool):
            report.fail(f"{label}.high_risk must be boolean")

    if len(ids) == SELECTION_CASE_COUNT and ids != set(range(1, SELECTION_CASE_COUNT + 1)):
        report.fail(
            "selection eval IDs must be the complete range "
            f"1..{SELECTION_CASE_COUNT}"
        )
    if labels != SELECTION_LABEL_COUNTS:
        report.fail(
            "selection eval labels must be balanced at 30 positive and 30 negative "
            f"(got {labels[True]} positive, {labels[False]} negative)"
        )
    if languages != SELECTION_LANGUAGE_COUNTS:
        report.fail(
            "selection eval languages must be 30 ko, 18 en, and 12 mixed "
            f"(got {languages})"
        )
    if not report.failures:
        report.ok("60 balanced selection evals have complete metadata")


def validate_production_suite(skill_root: Path, report: Report) -> None:
    """Validate the deterministic run contract, not an LLM result."""
    path = skill_root / "evals/production-suite.json"
    payload = read_json(path)
    if not isinstance(payload, dict):
        report.fail("production-suite.json must contain an object")
        return
    if payload.get("schema_version") != 2:
        report.fail("production suite must use schema_version 2")
    if payload.get("skill_name") != skill_root.name:
        report.fail("production suite skill_name must name the owning skill")
    workspace = payload.get("workspace")
    if not isinstance(workspace, str) or not workspace.strip():
        report.fail("production suite workspace must be a non-empty string")

    behavior = payload.get("behavior")
    if not isinstance(behavior, dict):
        report.fail("production suite behavior must be an object")
        return
    if behavior.get("eval_manifest") != "evals/evals.json":
        report.fail("production suite behavior.eval_manifest must be evals/evals.json")
    repetitions = behavior.get("repetitions")
    if repetitions != 2:
        report.fail("production suite behavior.repetitions must be exactly 2")
    behavior_ids = behavior.get("eval_ids")
    if behavior_ids != list(PRODUCTION_BEHAVIOR_IDS):
        report.fail(
            "production suite behavior.eval_ids must be exactly "
            f"{list(PRODUCTION_BEHAVIOR_IDS)}"
        )

    configurations = behavior.get("configurations")
    if not isinstance(configurations, list) or not all(isinstance(item, dict) for item in configurations):
        report.fail("production suite behavior.configurations must be an array of objects")
    else:
        names = [item.get("name") for item in configurations]
        if names != ["with_skill", "without_skill"]:
            report.fail("production suite behavior.configurations must be exactly with_skill then without_skill")
        if any(not isinstance(item.get("source"), str) or not item["source"] for item in configurations):
            report.fail("production suite behavior configuration sources must be non-empty strings")
        elif configurations[0].get("source") != "working-tree":
            report.fail("with_skill configuration must snapshot the working tree")
        elif configurations[1].get("source") != "none" or "git_ref" in configurations[1]:
            report.fail("without_skill configuration must provide no skill source or git ref")
    fixture_destinations = behavior.get("fixture_destinations")
    if not isinstance(fixture_destinations, dict) or not fixture_destinations:
        report.fail("production suite behavior.fixture_destinations must be a non-empty object")
    case_contracts = behavior.get("case_contracts")
    expected_case_ids = {str(value) for value in PRODUCTION_BEHAVIOR_IDS}
    if not isinstance(case_contracts, dict) or set(case_contracts) != expected_case_ids:
        report.fail("production suite behavior.case_contracts must cover each production behavior ID exactly once")
    elif (
        case_contracts.get("25", {}).get("denied_capabilities") != ["web"]
        or case_contracts.get("25", {}).get("deny_write_tools") is not True
        or case_contracts.get("28", {}).get("denied_capabilities") != ["web"]
        or case_contracts.get("19", {}).get("allowed_change_paths") != ["docs", "docs/launch-assets", "docs/launch-assets/**"]
    ):
        report.fail("production suite must preserve custom-root and actual web-denied case controls")

    image_canary = payload.get("image_canary")
    expected_image_canary = {
        "eval_id": 24,
        "document_root": "docs/marketing/google-play",
        "artifact_name": "orbit-notes-feature-graphic-1024x500.png",
        "width": 1024,
        "height": 500,
        "has_alpha": False,
        "required_capabilities": ["web", "image-generation"],
    }
    if image_canary != expected_image_canary:
        report.fail("production suite image_canary must match the Google Play document-plus-PNG contract")

    selection = payload.get("selection")
    if not isinstance(selection, dict):
        report.fail("production suite selection must be an object")
    else:
        if selection.get("dataset") != "evals/design-system-selection-evals.json":
            report.fail("production suite selection.dataset must be design-system-selection-evals.json")
        if selection.get("repetitions") != 3:
            report.fail("production suite selection.repetitions must be 3")
        if selection.get("runner") != "codex-direct-independent-selection":
            report.fail("production suite selection.runner must use direct Codex selection")
        if selection.get("configuration") != "current":
            report.fail("production suite selection.configuration must be current")
        if selection.get("model") != EXECUTION_MODEL:
            report.fail(f"production suite selection.model must be {EXECUTION_MODEL!r}")
        if selection.get("reasoning_effort") != EXECUTION_REASONING_EFFORT:
            report.fail(f"production suite selection.reasoning_effort must be {EXECUTION_REASONING_EFFORT!r}")
        if selection.get("workers") != 3:
            report.fail("production suite selection.workers must be 3 independent Codex runs")
        for field in ("runner", "trigger_threshold"):
            if field not in selection:
                report.fail(f"production suite selection.{field} is required")

    runtime = payload.get("runtime")
    if not isinstance(runtime, dict):
        report.fail("production suite runtime must be an object")
    else:
        if not isinstance(runtime.get("command"), str) or not runtime["command"].strip():
            report.fail("production suite runtime.command must be a non-empty string")
        if runtime.get("model") != EXECUTION_MODEL:
            report.fail(f"production suite runtime.model must be {EXECUTION_MODEL!r}")
        if runtime.get("reasoning_effort") != EXECUTION_REASONING_EFFORT:
            report.fail(f"production suite runtime.reasoning_effort must be {EXECUTION_REASONING_EFFORT!r}")

    evidence = payload.get("evidence")
    if not isinstance(evidence, dict) or evidence.get("schema_version") != 2:
        report.fail("production suite evidence.schema_version must be 2")
    gates = evidence.get("gates") if isinstance(evidence, dict) else None
    if not isinstance(gates, dict):
        report.fail("production suite evidence.gates must be an object")
    else:
        hard_gates = gates.get("behavior_hard_gates")
        if not isinstance(hard_gates, list) or set(hard_gates) != HARD_GATE_NAMES:
            report.fail(
                "production suite evidence.gates.behavior_hard_gates must name every "
                "preservation, review, collision, and no-hallucination gate"
            )
        required_thresholds = {
            "macro_pass_rate_min": 0.90,
            "selection_precision_min": 0.95,
            "selection_recall_min": 0.95,
            "selection_specificity_min": 0.95,
            "high_risk_false_positives_max": 0,
            "blind_current_win_rate_min": 0.95,
            "blind_ties_count_as_current_wins": True,
        }
        for field, expected in required_thresholds.items():
            if gates.get(field) != expected:
                report.fail(
                    f"production suite evidence.gates.{field} must remain {expected!r}"
                )

    if not report.failures:
        report.ok("production suite matches the schema-v2 execution and hard-gate contract")


def validate_node_validators(skill_root: Path, report: Report) -> None:
    node = shutil.which("node")
    if node is None:
        report.fail("Node.js is required to syntax-check eval result validators")
        return
    for relative in NODE_VALIDATORS:
        result = subprocess.run(
            [node, "--check", str(skill_root / relative)],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            report.fail(f"invalid Node validator {relative}: {detail}")
    if not report.failures:
        report.ok(f"all {len(NODE_VALIDATORS)} eval result validators parse")


def validate_python_eval_scripts(skill_root: Path, report: Report) -> None:
    for relative in PYTHON_EVAL_SCRIPTS:
        path = skill_root / relative
        try:
            compile(read_text(path), str(path), "exec")
        except SyntaxError as exc:
            report.fail(f"invalid Python eval script {relative}: {exc.msg} at line {exc.lineno}")
    if not report.failures:
        report.ok(f"all {len(PYTHON_EVAL_SCRIPTS)} Python eval scripts parse")


def contract_digest(skill_root: Path) -> str:
    files = [skill_root / "SKILL.md"]
    files.extend(
        path
        for path in (skill_root / "scripts").glob("*.py")
        if path.name != "validate_fdd.py"
    )
    files.extend(
        (skill_root / "references" / "document-types" / "design-system").rglob("*.md")
    )
    files.extend(
        skill_root / "references" / "shared" / name
        for name in ("human-readable-writing.md", "source-grounding.md", "existing-document-edits.md")
    )
    files.extend((skill_root / "evals").rglob("*"))
    files = [
        path
        for path in files
        if path.is_file()
        and path.relative_to(skill_root).as_posix() != "evals/production-evidence.json"
        and path.relative_to(skill_root).as_posix() not in {
            "evals/evals.json",
            "evals/trigger-evals.json",
        }
        and not path.relative_to(skill_root).as_posix().startswith("evals/evidence/")
    ]
    digest = hashlib.sha256()
    for path in sorted(set(files)):
        relative = path.relative_to(skill_root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    eval_manifest = read_json(skill_root / "evals/evals.json")
    design_system_evals = {
        "skill_name": eval_manifest.get("skill_name"),
        "evals": [
            item
            for item in eval_manifest.get("evals", [])
            if isinstance(item, dict)
            and isinstance(item.get("id"), int)
            and 10 <= item["id"] <= 28
        ],
    }
    digest.update(b"evals/evals.design-system.json\0")
    digest.update(
        json.dumps(
            design_system_evals,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )
    digest.update(b"\0")
    return digest.hexdigest()


def is_sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def resolve_evidence_file(
    skill_root: Path,
    relative: Any,
    expected_hash: Any,
    label: str,
    report: Report,
) -> Path | None:
    if not isinstance(relative, str):
        report.fail(f"{label} must be an evals/evidence path")
        return None
    normalized = relative.replace("\\", "/")
    segments = normalized.split("/")
    if (
        relative != normalized
        or not normalized.startswith("evals/evidence/")
        or normalized.startswith("/")
        or any(segment in {"", ".", ".."} for segment in segments)
        or PurePosixPath(normalized).as_posix() != normalized
    ):
        report.fail(f"{label} must be a normalized path under evals/evidence/")
        return None
    evidence_root = (skill_root / "evals/evidence").resolve()
    resolved = (skill_root / normalized).resolve()
    if not is_within(evidence_root, resolved) or not resolved.is_file():
        report.fail(f"{label} must reference an existing regular evidence file")
        return None
    if not is_sha256(expected_hash):
        report.fail(f"{label} hash must be lowercase SHA-256")
        return None
    if hashlib.sha256(resolved.read_bytes()).hexdigest() != expected_hash:
        report.fail(f"{label} hash does not match the evidence file")
        return None
    return resolved


def inspect_png(path: Path) -> tuple[int, int, bool] | None:
    content = path.read_bytes()
    if not content.startswith(b"\x89PNG\r\n\x1a\n"):
        return None
    position = 8
    chunks: list[tuple[bytes, bytes]] = []
    while position < len(content):
        if position + 12 > len(content):
            return None
        length = struct.unpack(">I", content[position : position + 4])[0]
        chunk_type = content[position + 4 : position + 8]
        data_start = position + 8
        data_end = data_start + length
        crc_end = data_end + 4
        if crc_end > len(content):
            return None
        data = content[data_start:data_end]
        expected_crc = struct.unpack(">I", content[data_end:crc_end])[0]
        if (zlib.crc32(chunk_type + data) & 0xFFFFFFFF) != expected_crc:
            return None
        chunks.append((chunk_type, data))
        position = crc_end
        if chunk_type == b"IEND":
            break
    if position != len(content) or not chunks or chunks[0][0] != b"IHDR" or len(chunks[0][1]) != 13:
        return None
    if chunks[-1] != (b"IEND", b""):
        return None
    compressed = b"".join(data for chunk_type, data in chunks if chunk_type == b"IDAT")
    try:
        decoded = zlib.decompress(compressed)
    except zlib.error:
        return None
    if not decoded:
        return None
    width, height, bit_depth, color_type, compression, filter_method, interlace = struct.unpack(">IIBBBBB", chunks[0][1])
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(color_type)
    allowed_depths = {0: {1, 2, 4, 8, 16}, 2: {8, 16}, 3: {1, 2, 4, 8}, 4: {8, 16}, 6: {8, 16}}
    palette_chunks = [(index, data) for index, (chunk_type, data) in enumerate(chunks) if chunk_type == b"PLTE"]
    palette = palette_chunks[0][1] if len(palette_chunks) == 1 else None
    first_idat_index = next((index for index, (chunk_type, _data) in enumerate(chunks) if chunk_type == b"IDAT"), len(chunks))
    palette_valid = (
        palette is not None
        and 0 < len(palette) <= 768
        and len(palette) % 3 == 0
        and palette_chunks[0][0] < first_idat_index
        and len(palette) // 3 <= 2**bit_depth
    )
    if (
        channels is None
        or bit_depth not in allowed_depths.get(color_type, set())
        or compression != 0
        or filter_method != 0
        or interlace != 0
        or (color_type == 3 and not palette_valid)
    ):
        return None
    expected_bytes = height * (1 + ((width * channels * bit_depth + 7) // 8))
    if len(decoded) != expected_bytes:
        return None
    row_bytes = (width * channels * bit_depth + 7) // 8
    if any(decoded[row * (row_bytes + 1)] > 4 for row in range(height)):
        return None
    has_alpha = color_type in {4, 6} or any(chunk_type == b"tRNS" for chunk_type, _ in chunks)
    return width, height, has_alpha


def validated_manifest_files(payload: Any, label: str, report: Report) -> dict[str, str]:
    if not isinstance(payload, dict) or not isinstance(payload.get("files"), dict):
        report.fail(f"{label}.files must be an object")
        return {}
    normalized: dict[str, str] = {}
    for raw_path, digest in payload["files"].items():
        if not isinstance(raw_path, str):
            report.fail(f"{label} contains a non-string path")
            continue
        path = raw_path.replace("\\", "/")
        segments = path.split("/")
        if (
            raw_path != path
            or path.startswith("/")
            or re.match(r"^[A-Za-z]:", path)
            or any(segment in {"", ".", ".."} for segment in segments)
            or PurePosixPath(path).as_posix() != path
            or path in normalized
        ):
            report.fail(f"{label} contains an invalid or duplicate path: {raw_path}")
            continue
        if not is_sha256(digest):
            report.fail(f"{label} digest for {path} must be lowercase SHA-256")
            continue
        normalized[path] = digest
    if not is_sha256(payload.get("sha256")):
        report.fail(f"{label}.sha256 must be lowercase SHA-256")
    return normalized


def validated_manifest_tree_hash(payload: Any, files: dict[str, str], label: str, report: Report) -> str | None:
    entries = payload.get("entries") if isinstance(payload, dict) else None
    if not isinstance(entries, list):
        report.fail(f"{label}.entries must be an array")
        return None
    normalized_entries: list[dict[str, str]] = []
    entry_files: dict[str, str] = {}
    seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            report.fail(f"{label} contains an invalid entry")
            continue
        path = entry["path"].replace("\\", "/")
        segments = path.split("/")
        if (
            path != entry["path"]
            or any(segment in {"", ".", ".."} for segment in segments)
            or PurePosixPath(path).as_posix() != path
            or path in seen
        ):
            report.fail(f"{label} contains an invalid or duplicate entry path: {path}")
            continue
        seen.add(path)
        if entry.get("type") == "directory":
            normalized_entries.append({"path": path, "type": "directory"})
        elif entry.get("type") == "file" and is_sha256(entry.get("sha256")):
            digest = entry["sha256"]
            normalized_entries.append({"path": path, "type": "file", "sha256": digest})
            entry_files[path] = digest
        else:
            report.fail(f"{label} entry has an unsupported type or digest: {path}")
    if entry_files != files:
        report.fail(f"{label} entries do not match files")
    encoded = json.dumps(sorted(normalized_entries, key=lambda item: item["path"]), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def manifest_changed_paths(before: Any, after: Any) -> list[str]:
    """Return changed file paths from two published workspace manifests."""
    def state(payload: Any) -> dict[str, str]:
        entries = payload.get("entries", []) if isinstance(payload, dict) else []
        return {
            item["path"]: f"{item.get('type')}:{item.get('sha256', '')}"
            for item in entries
            if isinstance(item, dict) and isinstance(item.get("path"), str)
        }
    before_state = state(before)
    after_state = state(after)
    changed: list[str] = []
    for path in sorted(set(before_state) | set(after_state)):
        if before_state.get(path) == after_state.get(path):
            continue
        if (after_state.get(path) or before_state.get(path) or "").startswith("file:"):
            changed.append(path)
    return changed


def direct_event_paths(event: dict[str, Any]) -> list[str]:
    inputs = event.get("input") if isinstance(event.get("input"), dict) else {}
    values: list[str] = []
    for key in ("path", "file_path", "filename", "target"):
        value = inputs.get(key)
        if isinstance(value, str) and value.strip():
            values.append(value)
    raw_paths = inputs.get("paths")
    if isinstance(raw_paths, list):
        values.extend(value for value in raw_paths if isinstance(value, str) and value.strip())
    return values


def direct_event_path(event: dict[str, Any]) -> str | None:
    paths = direct_event_paths(event)
    return paths[0] if paths else None


def direct_event_is_workspace_mutation(event: dict[str, Any]) -> bool:
    """Match the runner's workspace-mutation classification, excluding harness writes."""
    name = event.get("name")
    if name in {"Write", "Edit"}:
        return True
    inputs = event.get("input") if isinstance(event.get("input"), dict) else {}
    if name == "MCP":
        return bool(re.search(
            r"\b(?:write|edit|create|update|delete|remove|mutat)\w*\b",
            json.dumps(inputs, ensure_ascii=False),
            re.IGNORECASE,
        ))
    if name != "Bash":
        return False
    command = str(inputs.get("command") or inputs.get("cmd") or "")
    return bool(re.search(
        r"(?:^|\s)(?:>|>>|tee|touch|rm|mv|cp|mkdir|rmdir|chmod|truncate|sed\s+-i|perl\s+-i|python(?:3)?\s+-c|node\s+-e)(?:\s|$)",
        command,
    ))


def direct_reported_capability_names(event: dict[str, Any]) -> set[str]:
    """Map a published tool event to the runner's semantic capabilities."""
    name = str(event.get("name") or "")
    names = {name} if name and name != "MCP" else set()
    if name == "MCP":
        inputs = json.dumps(event.get("input", {}), ensure_ascii=False)
        if re.search(r"https?://|\b(?:web|browser|url|fetch)\b", inputs, re.IGNORECASE):
            names.update({"MCP", "WebFetch", "Browser"})
        elif re.search(r"\b(?:read|find|grep|search_local|list)\w*\b", inputs, re.IGNORECASE):
            names.add("Read")
        if direct_event_is_workspace_mutation(event):
            names.update({"Write", "Edit"})
    return names


def validate_direct_report_integrity(
    run: dict[str, Any],
    report_payload: dict[str, Any],
    before: Any,
    after: Any,
    configuration: str,
    eval_id: int,
    report: Report,
    label: str,
) -> None:
    """Apply the runner's mutation, capability, and workspace integrity gates."""
    events = report_payload.get("tool_events", [])
    if not isinstance(events, list):
        return
    produced = report_payload.get("produced_paths", [])
    actual = run.get("actual_changes", [])
    after_entries = {
        item.get("path"): item.get("type")
        for item in (after.get("entries", []) if isinstance(after, dict) else [])
        if isinstance(item, dict)
    }
    for event in events:
        if not isinstance(event, dict) or event.get("status") != "success":
            continue
        name = event.get("name")
        target = direct_event_path(event)
        serialized_inputs = json.dumps(event.get("input", {}), ensure_ascii=False)
        workspace_root = Path(str((before or {}).get("workspace_root", ""))) if isinstance(before, dict) else None
        run_root = workspace_root.parent if workspace_root else None
        redacted_run_inputs = serialized_inputs
        if run_root:
            redacted_run_inputs = redacted_run_inputs.replace(str(run_root), "<run>")
            run_text = str(run_root).replace("\\", "/")
            marker = "skills/document-writing-workspace/"
            if marker in run_text:
                redacted_run_inputs = redacted_run_inputs.replace(
                    f"{marker}{run_text.split(marker, 1)[1]}",
                    "<run>",
                )
        if workspace_root:
            redacted_run_inputs = redacted_run_inputs.replace(str(workspace_root), "<workspace>")
        if name != "HarnessArtifactWrite" and re.search(
            r"document-writing-workspace/iteration-|/(?:with|without)_skill/|skills/document-writing/(?!workspace/)|grading\.json|/outputs/",
            redacted_run_inputs,
            re.IGNORECASE,
        ):
            report.fail(f"{label} tool input exposes another run, iteration, or unsupplied skill path")
        if configuration == "without_skill" and name != "HarnessArtifactWrite":
            redacted_inputs = redacted_run_inputs
            if re.search(
                r"file:|SKILL\.md|skills/document-writing|skill-snapshot(?:/|\\)|/with_skill/|/behavior/|grading\.json|/outputs/",
                redacted_inputs,
                re.IGNORECASE,
            ):
                report.fail(f"{label} without_skill tool input exposes skill or sibling-result evidence")
        if name in {"Write", "Edit"}:
            targets = direct_event_paths(event)
            if not targets:
                report.fail(f"{label} successful Write/Edit has no target path")
                continue
            for target in targets:
                normalized = target.replace("\\", "/")
                workspace_root = Path(str((before or {}).get("workspace_root", ""))) if isinstance(before, dict) else None
                if target != normalized or ".." in PurePosixPath(normalized).parts:
                    report.fail(f"{label} successful Write/Edit targets outside workspace: {target}")
                    continue
                if normalized.startswith("/"):
                    try:
                        normalized = Path(normalized).resolve().relative_to(workspace_root.resolve()).as_posix() if workspace_root else ""
                    except (ValueError, OSError):
                        normalized = ""
                    if not normalized:
                        report.fail(f"{label} successful Write/Edit targets outside workspace: {target}")
                        continue
                else:
                    normalized = normalized.removeprefix("workspace/")
                if target.endswith(("/", "\\")) or after_entries.get(normalized) == "directory":
                    report.fail(f"{label} successful Write/Edit targets a directory: {target}")
                if normalized not in produced or normalized not in actual:
                    report.fail(f"{label} successful Write/Edit is not reflected in produced_paths and manifests: {target}")
        if configuration == "without_skill" and name in {"Read", "Bash", "MCP"}:
            inputs = event.get("input") if isinstance(event.get("input"), dict) else {}
            command = str(inputs.get("command") or inputs.get("cmd") or "")
            workspace_root = Path(str((before or {}).get("workspace_root", ""))) if isinstance(before, dict) else None
            target_is_allowed = False
            if target is not None:
                candidate = Path(target) if Path(target).is_absolute() else (workspace_root / target if workspace_root else Path(target))
                try:
                    target_is_allowed = bool(workspace_root) and candidate.resolve().is_relative_to(workspace_root.resolve())
                except (OSError, ValueError):
                    target_is_allowed = False
                target_is_allowed = target_is_allowed or candidate.name == "direct-task.json"
    if eval_id == 25:
        if any(event.get("status") == "success" and direct_event_is_workspace_mutation(event) for event in events):
            report.fail(f"{label} deny_write_tools forbids workspace mutation")
        if any(event.get("status") == "success" and {"WebSearch", "WebFetch", "Browser", "MCP"} & direct_reported_capability_names(event) for event in events):
            report.fail(f"{label} denied capability used: web")
    if eval_id == 28 and any(event.get("status") == "success" and {"WebSearch", "WebFetch", "Browser", "MCP"} & direct_reported_capability_names(event) for event in events):
        report.fail(f"{label} denied capability used: web")
    required_web = eval_id in {19, 22, 23}
    if required_web and not any(event.get("status") == "success" and {"WebSearch", "WebFetch", "Browser", "MCP"} & direct_reported_capability_names(event) for event in events):
        report.fail(f"{label} required capability missing: web")
    if report_payload.get("status") == "clarification_required" and actual:
        report.fail(f"{label} clarification_required run changed the workspace")


def normalized_validator_expectations(record: dict[str, Any]) -> list[dict[str, Any]]:
    name = str(record.get("name", "validator"))
    stdout = str(record.get("stdout", ""))
    return_code = record.get("return_code")
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return [{
            "text": f"{name} produced parseable JSON",
            "passed": False,
            "evidence": stdout.strip() or f"validator exited {return_code} without JSON",
        }]
    if isinstance(payload, dict) and isinstance(payload.get("expectations"), list):
        return [item for item in payload["expectations"] if isinstance(item, dict) and "text" in item and "passed" in item]
    if isinstance(payload, dict) and isinstance(payload.get("checks"), list):
        expectations = [
            {"text": f"{name}: {item}", "passed": True, "evidence": "deterministic validator check"}
            for item in payload.get("checks", [])
        ]
        expectations.extend(
            {"text": f"{name}: {item}", "passed": False, "evidence": "deterministic validator failure"}
            for item in payload.get("failures", [])
        )
        return expectations
    return [{
        "text": f"{name} returned a recognized result",
        "passed": False,
        "evidence": f"unrecognized validator payload; exit={return_code}",
    }]


def validate_rate(value: Any, label: str, report: Report, minimum: float | None = None) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 1:
        report.fail(f"{label} must be a number between 0 and 1")
    elif minimum is not None and value < minimum:
        report.fail(f"{label} must be at least {minimum:.2f}")


def blind_verdict_has_concrete_evidence(verdict: Any) -> bool:
    """Check the minimum non-generic evidence contract for one blind verdict."""
    if not isinstance(verdict, dict):
        return False
    reasoning = verdict.get("reasoning")
    normalized = re.sub(r"\s+", " ", reasoning.strip().lower()) if isinstance(reasoning, str) else ""
    references = verdict.get("evidence_references", verdict.get("evidence_refs", verdict.get("evidence")))
    return bool(
        len(normalized) >= 20
        and normalized not in {"a is better", "b is better", "tie", "no difference", "comparable"}
        and isinstance(references, list)
        and len([item for item in references if isinstance(item, str) and item.strip()]) >= 2
        and verdict.get("rubric")
        and verdict.get("expectation_details", verdict.get("expectation_detail"))
    )


def production_iteration_is_accepted(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1 and value != 8


def blind_gate_passes(
    total_pairs: Any,
    current_wins: Any,
    ties: Any,
    credited_current_wins: Any,
    current_win_rate: Any,
) -> bool:
    return (
        total_pairs == 20
        and isinstance(current_wins, int)
        and not isinstance(current_wins, bool)
        and isinstance(ties, int)
        and not isinstance(ties, bool)
        and isinstance(credited_current_wins, int)
        and not isinstance(credited_current_wins, bool)
        and credited_current_wins == current_wins + ties
        and credited_current_wins >= 19
        and current_win_rate == credited_current_wins / 20
        and isinstance(current_win_rate, (int, float))
        and not isinstance(current_win_rate, bool)
        and current_win_rate >= 0.95
    )


def resolved_blind_winner(forward_winner: Any, reversed_winner: Any) -> str:
    forward = str(forward_winner).upper()
    reversed_value = str(reversed_winner).upper()
    return forward if forward == {"A": "B", "B": "A", "TIE": "TIE"}.get(reversed_value) else "TIE"


def validate_evidence_date(value: Any, report: Report) -> None:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        report.fail("production evidence generated_at must be an ISO calendar date")
        return
    try:
        date.fromisoformat(value)
    except ValueError:
        report.fail("production evidence generated_at must be a real YYYY-MM-DD date")


def validate_evidence_artifacts(skill_root: Path, payload: dict[str, Any], report: Report) -> set[str]:
    artifacts = payload.get("artifacts")
    artifact_paths: set[str] = set()
    artifact_kinds: set[str] = set()
    if not isinstance(artifacts, list) or not artifacts:
        report.fail("production evidence artifacts must be a non-empty array")
        return artifact_paths
    evidence_root = skill_root / "evals/evidence"
    for index, item in enumerate(artifacts):
        label = f"production evidence artifacts[{index}]"
        if not isinstance(item, dict):
            report.fail(f"{label} must be an object")
            continue
        kind = item.get("kind")
        if not isinstance(kind, str) or not kind.strip():
            report.fail(f"{label}.kind must be a non-empty string")
        else:
            artifact_kinds.add(kind)
        relative = item.get("path")
        if not isinstance(relative, str):
            report.fail(f"{label}.path must be under evals/evidence/")
            continue
        normalized = relative.replace("\\", "/")
        segments = normalized.split("/")
        if (
            relative != normalized
            or not normalized.startswith("evals/evidence/")
            or any(segment in {"", ".", ".."} for segment in segments)
            or PurePosixPath(normalized).as_posix() != normalized
        ):
            report.fail(f"{label}.path must be a normalized path under evals/evidence/")
            continue
        relative = normalized
        if relative in artifact_paths:
            report.fail(f"production evidence artifact path is duplicated: {relative}")
            continue
        artifact_paths.add(relative)
        resolved = (skill_root / relative).resolve()
        if not is_within(evidence_root.resolve(), resolved) or not resolved.is_file():
            report.fail(f"{label}.path must reference an existing evidence file: {relative}")
            continue
        expected_hash = item.get("sha256")
        if not is_sha256(expected_hash):
            report.fail(f"{label}.sha256 must be a lowercase SHA-256 digest")
        elif hashlib.sha256(resolved.read_bytes()).hexdigest() != expected_hash:
            report.fail(f"{label}.sha256 does not match {relative}")
    missing_kinds = sorted(REQUIRED_ARTIFACT_KINDS - artifact_kinds)
    if missing_kinds:
        report.fail(f"production evidence is missing artifact kinds: {missing_kinds}")
    return artifact_paths


def validate_diagnostic_evidence(
    skill_root: Path,
    payload: dict[str, Any],
    artifact_paths: set[str],
    report: Report,
) -> None:
    """Validate a local diagnostic snapshot without treating it as attestation."""
    if payload.get("status") != "diagnostic-failed":
        report.fail("diagnostic evidence status must be diagnostic-failed")
    if payload.get("production_ready") is not False:
        report.fail("diagnostic evidence production_ready must be false")
    if payload.get("iteration") != 13:
        report.fail("diagnostic evidence iteration must be 13")

    forbidden = {
        "context_id", "context_ids", "receipts", "tool_events", "raw_telemetry",
        "attestation", "attested_runs",
    }
    present_forbidden: set[str] = set()
    def collect_forbidden(value: Any) -> None:
        if isinstance(value, dict):
            present_forbidden.update(set(value) & forbidden)
            for nested in value.values():
                collect_forbidden(nested)
        elif isinstance(value, list):
            for nested in value:
                collect_forbidden(nested)
    collect_forbidden(payload)
    present_forbidden = sorted(present_forbidden)
    if present_forbidden:
        report.fail(
            "diagnostic evidence must not invent raw telemetry or receipts: "
            f"{present_forbidden}"
        )

    runtime = payload.get("runtime")
    if not isinstance(runtime, dict):
        report.fail("diagnostic evidence runtime must be an object")
    else:
        expected_runtime = {
            "runner": "codex-in-app-isolated-subagents",
            "model": EXECUTION_MODEL,
            "reasoning_effort": EXECUTION_REASONING_EFFORT,
            "telemetry_status": "unavailable",
        }
        for field, expected in expected_runtime.items():
            if runtime.get(field) != expected:
                report.fail(f"diagnostic evidence runtime.{field} must be {expected!r}")
        if not isinstance(runtime.get("command"), str) or not runtime["command"].strip():
            report.fail("diagnostic evidence runtime.command must be a non-empty string")
        if not isinstance(runtime.get("limitations"), list) or not runtime["limitations"]:
            report.fail("diagnostic evidence runtime.limitations must be a non-empty array")

    artifacts = payload.get("artifacts", [])
    by_kind: dict[str, list[dict[str, Any]]] = {}
    for item in artifacts:
        if isinstance(item, dict) and isinstance(item.get("kind"), str):
            by_kind.setdefault(item["kind"], []).append(item)
    missing_kinds = sorted(DIAGNOSTIC_REQUIRED_ARTIFACT_KINDS - set(by_kind))
    if missing_kinds:
        report.fail(f"diagnostic evidence is missing artifact kinds: {missing_kinds}")

    def artifact(kind: str, unique: bool = True) -> tuple[dict[str, Any] | None, Path | None]:
        candidates = by_kind.get(kind, [])
        if unique and len(candidates) != 1:
            report.fail(f"diagnostic evidence artifact kind {kind!r} must occur exactly once")
        if not candidates:
            return None, None
        item = candidates[0]
        path = resolve_evidence_file(
            skill_root,
            item.get("path"),
            item.get("sha256"),
            f"diagnostic evidence {kind} artifact",
            report,
        )
        if item.get("path") not in artifact_paths:
            report.fail(f"diagnostic evidence {kind} must be listed in artifacts")
        return item, path

    summary_item, summary_path = artifact("measurement-summary")
    behavior_item, behavior_path = artifact("behavior-results")
    selection_item, selection_path = artifact("selection-results")
    blind_item, blind_path = artifact("blind-comparison")
    integrity_item, integrity_path = artifact("integrity")
    review_item, review_path = artifact("review")
    manifest_item, manifest_path = artifact("image-canary-manifest")
    generation_item, generation_path = artifact("image-canary-generation")
    source_item, source_path = artifact("image-canary-source")
    final_item, final_path = artifact("image-canary")

    def check_binding(field: str, item: dict[str, Any] | None) -> None:
        value = payload.get(field)
        if not isinstance(value, dict) or not isinstance(item, dict):
            report.fail(f"diagnostic evidence {field} must bind a hashed artifact")
            return
        if value.get("path") != item.get("path") or value.get("sha256") != item.get("sha256"):
            report.fail(f"diagnostic evidence {field} path and hash must match its artifact descriptor")

    check_binding("behavior_benchmark", behavior_item)
    check_binding("selection_benchmark", selection_item)
    check_binding("blind_comparison", blind_item)
    check_binding("integrity", integrity_item)
    review_value = payload.get("review")
    if not isinstance(review_value, dict) or not isinstance(review_item, dict) or review_value.get("artifact_path") != review_item.get("path") or review_value.get("sha256") != review_item.get("sha256"):
        report.fail("diagnostic evidence review path and hash must match its artifact descriptor")
    image_value = payload.get("image_canary")
    if not isinstance(image_value, dict):
        report.fail("diagnostic evidence image_canary must be an object")
    else:
        if not isinstance(final_item, dict) or image_value.get("artifact_path") != final_item.get("path") or image_value.get("sha256") != final_item.get("sha256"):
            report.fail("diagnostic image canary final path and hash must match its artifact descriptor")
        if not isinstance(source_item, dict) or image_value.get("source_artifact_path") != source_item.get("path") or image_value.get("source_sha256") != source_item.get("sha256"):
            report.fail("diagnostic image canary source path and hash must match its artifact descriptor")
        if not isinstance(manifest_item, dict) or image_value.get("manifest_artifact_path") != manifest_item.get("path") or image_value.get("manifest_sha256") != manifest_item.get("sha256"):
            report.fail("diagnostic image canary manifest path and hash must match its artifact descriptor")
        if not isinstance(generation_item, dict) or image_value.get("generation_artifact_path") != generation_item.get("path") or image_value.get("generation_artifact_sha256") != generation_item.get("sha256"):
            report.fail("diagnostic image canary generation path and hash must match its artifact descriptor")

    if summary_path is not None:
        summary = read_json(summary_path)
        if summary.get("schema_version") != 1 or summary.get("production_ready") is not False:
            report.fail("diagnostic measurement summary must record schema 1 and production_ready false")
        if summary.get("status") != "comparison-threshold-pass-absolute-gate-fail":
            report.fail("diagnostic measurement summary status does not match iteration-13 clean input")
        expected_gates = {
            "existing_document_preservation": False,
            "review_no_mutation": True,
            "collision_no_overwrite": True,
            "web_unavailable_no_hallucination": True,
        }
        if summary.get("hard_gates") != expected_gates:
            report.fail("diagnostic measurement summary hard gates do not match clean input")

    if behavior_path is not None:
        behavior = read_json(behavior_path)
        metadata = behavior.get("metadata") if isinstance(behavior, dict) else None
        if not isinstance(metadata, dict) or metadata.get("telemetry_status") != "unavailable":
            report.fail("diagnostic behavior artifact must disclose unavailable telemetry")
        run_summary = behavior.get("run_summary") if isinstance(behavior, dict) else None
        expected_behavior = {
            "with_skill": {"passed": 138, "total": 142, "pass_rate": 138 / 142},
            "without_skill": {"passed": 106, "total": 142, "pass_rate": 106 / 142},
        }
        if run_summary != expected_behavior:
            report.fail("diagnostic behavior measurements must remain 138/142 and 106/142")

    if selection_path is not None:
        selection = read_json(selection_path)
        metrics = selection.get("metrics") if isinstance(selection, dict) else None
        if not isinstance(selection, dict) or "description-only" not in str(selection.get("scope", "")):
            report.fail("diagnostic selection artifact must be description-only")
        expected_selection = {
            "runs": 3, "queries_per_run": 60, "total_decisions": 180,
            "tp": 90, "tn": 90, "fp": 0, "fn": 0,
            "high_risk_false_positives": 0,
            "precision": 1.0, "recall": 1.0, "specificity": 1.0, "mismatches": [],
        }
        if metrics != expected_selection:
            report.fail("diagnostic selection measurements must remain 180/180 with no mismatches")

    if blind_path is not None:
        blind = read_json(blind_path)
        expected_blind = {
            "total_pairs": 20, "current_wins": 20, "without_skill_wins": 0,
            "ties": 0, "credited_current_wins": 20, "current_win_rate": 1.0,
            "tie_policy": "credit-current",
        }
        if not isinstance(blind, dict) or any(blind.get(field) != value for field, value in expected_blind.items()):
            report.fail("diagnostic blind comparison must remain 20/20 current wins")
        elif not isinstance(blind.get("pairs"), list) or len(blind["pairs"]) != 20:
            report.fail("diagnostic blind comparison must contain 20 pair records")

    if integrity_path is not None:
        integrity = read_json(integrity_path)
        if integrity.get("skill_unchanged_since_snapshot") is not True or integrity.get("without_skill_isolation_passed") is not True:
            report.fail("diagnostic integrity artifact must preserve its recorded isolation result")
        if not isinstance(integrity.get("limitation"), str) or "raw tool telemetry" not in integrity["limitation"]:
            report.fail("diagnostic integrity artifact must disclose the telemetry limitation")

    if review_path is not None:
        if review_path.stat().st_size < 1024:
            report.fail("diagnostic review HTML is unexpectedly small")
        review_text = read_text(review_path).lower()
        for marker in ("document-writing", "eval review:", 'id="panel-benchmark"', 'id="outputs-body"'):
            if marker not in review_text:
                report.fail(f"diagnostic review HTML is missing marker {marker!r}")

    if manifest_path is not None:
        manifest = read_json(manifest_path)
        png = manifest.get("png") if isinstance(manifest, dict) else None
        if not isinstance(manifest, dict) or manifest.get("passed") is not True or not isinstance(png, dict):
            report.fail("diagnostic image canary manifest must record a passing PNG canary")
        else:
            if (png.get("width"), png.get("height"), png.get("has_alpha")) != (1024, 500, False):
                report.fail("diagnostic image canary must be 1024x500 without alpha")
            if png.get("sha256") != payload.get("image_canary", {}).get("sha256"):
                report.fail("diagnostic image canary hash must match its manifest")
            calls = manifest.get("image_generation_calls")
            if not isinstance(calls, list) or len(calls) != 1:
                report.fail("diagnostic image canary must record exactly one generation call")
    if generation_path is not None:
        generation = read_json(generation_path)
        if generation.get("status") != "completed" or not isinstance(generation.get("image_generation_calls"), list):
            report.fail("diagnostic image generation artifact must be the completed canary report")
    if source_path is not None and final_path is not None:
        source_png = inspect_png(source_path)
        final_png = inspect_png(final_path)
        if source_png != (1024, 500, False) or final_png != (1024, 500, False):
            report.fail("diagnostic image source and final artifacts must be complete 1024x500 RGB PNGs")
        if source_path.read_bytes() != final_path.read_bytes():
            report.fail("diagnostic image source and final PNG must be the same observed output")
        if manifest_path is not None:
            manifest_hash = read_json(manifest_path).get("png", {}).get("sha256")
            if hashlib.sha256(final_path.read_bytes()).hexdigest() != manifest_hash:
                report.fail("diagnostic final PNG hash does not match the canary manifest")

    document_paths = {
        item.get("path")
        for item in artifacts
        if isinstance(item, dict)
        and item.get("kind") in {"image-canary-document", "image-canary-document-file"}
        and isinstance(item.get("path"), str)
    }
    expected_document_suffixes = {
        "index.md", "visual-language.md", "asset-system.md", "composition-and-copy.md",
        "accessibility.md", "delivery-and-versioning.md", "stores/google-play.md",
    }
    actual_document_suffixes = {
        path.split("/image-canary/document/docs/marketing/google-play/", 1)[-1]
        for path in document_paths
        if "/image-canary/document/docs/marketing/google-play/" in path
    }
    if actual_document_suffixes != expected_document_suffixes:
        report.fail("diagnostic image canary document artifacts must cover the observed seven-file document set")
    for path in sorted(document_paths):
        resolved = resolve_evidence_file(skill_root, path, next(
            (item.get("sha256") for item in artifacts if isinstance(item, dict) and item.get("path") == path),
            None,
        ), "diagnostic image canary document artifact", report)
        if resolved is not None and resolved.stat().st_size == 0:
            report.fail(f"diagnostic image canary document artifact is empty: {path}")

    measurements = payload.get("measurements")
    if not isinstance(measurements, dict):
        report.fail("diagnostic evidence measurements must be an object")
    else:
        expected_measurements = {
            "behavior": {
                "current": {"passed": 138, "total": 142, "macro_pass_rate": 138 / 142},
                "without_skill": {"passed": 106, "total": 142, "macro_pass_rate": 106 / 142},
            },
            "blind": {"current_wins": 20, "total_pairs": 20, "current_win_rate": 1.0},
            "selection": {"selected": 180, "total": 180, "precision": 1.0, "recall": 1.0, "specificity": 1.0},
        }
        if measurements != expected_measurements:
            report.fail("diagnostic evidence measurements do not match clean iteration-13 values")
    if payload.get("hard_gates") != {
        "existing_document_preservation": False,
        "review_no_mutation": True,
        "collision_no_overwrite": True,
        "web_unavailable_no_hallucination": True,
    }:
        report.fail("diagnostic evidence hard gates do not match clean iteration-13 values")
    limitations = payload.get("limitations")
    if not isinstance(limitations, list) or not limitations:
        report.fail("diagnostic evidence limitations must be a non-empty array")
    elif not any("telemetry" in str(value).lower() for value in limitations):
        report.fail("diagnostic evidence limitations must disclose missing telemetry")
    if not report.failures:
        report.ok("diagnostic evidence matches clean iteration-13 measurements without attestation")


def validate_behavior_run_records(
    skill_root: Path,
    runs: list[Any],
    report: Report,
    current_contract_sha256: str,
) -> dict[tuple[int, str, int], float]:
    """Require auditable execution metadata without claiming that we ran an LLM."""
    actual_runs: set[tuple[int, str, int]] = set()
    repetitions_by_configuration: dict[tuple[int, str], set[int]] = {}
    scores: dict[tuple[int, str, int], float] = {}
    required_hashes = ("workspace_before_sha256", "workspace_after_sha256", "output_tree_sha256", "review_output_sha256")
    eval_manifest = read_json(skill_root / "evals/evals.json")
    semantic_by_id = {
        item["id"]: list(item.get("expectations", []))
        for item in eval_manifest.get("evals", [])
        if isinstance(item, dict) and isinstance(item.get("id"), int)
    }
    prompt_by_id = {
        item["id"]: item.get("prompt")
        for item in eval_manifest.get("evals", [])
        if isinstance(item, dict) and isinstance(item.get("id"), int)
    }
    used_evidence_paths: set[str] = set()
    behavior_context_ids: set[str] = set()
    for index, run in enumerate(runs):
        label = f"production evidence behavior.runs[{index}]"
        if not isinstance(run, dict):
            report.fail(f"{label} must be an object")
            continue
        eval_id = run.get("eval_id")
        configuration = run.get("configuration")
        repetition = run.get("repetition")
        normalized_configuration = {"with_skill": "current"}.get(configuration, configuration)
        if (
            isinstance(eval_id, int)
            and eval_id in PRODUCTION_BEHAVIOR_IDS
            and normalized_configuration in {"current", "without_skill"}
            and isinstance(repetition, int)
            and not isinstance(repetition, bool)
            and repetition in {1, 2}
        ):
            identity = (eval_id, normalized_configuration, repetition)
            if identity in actual_runs:
                report.fail(f"{label} duplicates behavior run {identity}")
            else:
                actual_runs.add(identity)
                repetitions_by_configuration.setdefault((eval_id, normalized_configuration), set()).add(repetition)
        else:
            report.fail(f"{label} requires a production eval_id, current/without_skill configuration, and positive repetition")
        for field in required_hashes:
            if not is_sha256(run.get(field)):
                report.fail(f"{label}.{field} must be a lowercase SHA-256 digest")
        allowed_patterns = run.get("allowed_change_patterns", run.get("allowed_changes"))
        actual_changes = run.get("actual_changes")
        if not isinstance(allowed_patterns, list) or not all(isinstance(item, str) for item in allowed_patterns):
            report.fail(f"{label}.allowed_change_patterns must be a string array")
            allowed_patterns = []
        if not isinstance(actual_changes, list) or not all(isinstance(item, str) for item in actual_changes):
            report.fail(f"{label}.actual_changes must be a string array")
            actual_changes = []
        for pattern in allowed_patterns:
            if "\\" in pattern or ".." in PurePosixPath(pattern).parts or pattern.startswith("/"):
                report.fail(f"{label} contains an invalid allowed change pattern: {pattern}")
        for changed in actual_changes:
            segments = changed.replace("\\", "/").split("/")
            if changed.replace("\\", "/") != changed or any(segment in {"", ".", ".."} for segment in segments):
                report.fail(f"{label} contains an invalid actual change path: {changed}")
                continue
            if not any(fnmatch.fnmatchcase(changed, pattern) for pattern in allowed_patterns):
                report.fail(f"{label} records an out-of-contract change: {changed}")
        if not isinstance(run.get("output_tree"), list) or not all(
            isinstance(item, str) for item in run["output_tree"]
        ):
            report.fail(f"{label}.output_tree must be a string array")
        evidence_files: dict[str, Path | None] = {}
        for prefix in (
            "direct_task", "transcript", "tool_events", "direct_agent_report", "eval_metadata",
            "response", "stderr", "timing", "metrics",
            "skill_snapshot_before", "skill_snapshot_after",
            "grading", "deterministic_grading", "before_manifest", "after_manifest", "review_output",
        ):
            relative_evidence_path = run.get(f"{prefix}_path")
            if isinstance(relative_evidence_path, str):
                if relative_evidence_path in used_evidence_paths:
                    report.fail(f"{label}.{prefix}_path is reused by another behavior run")
                used_evidence_paths.add(relative_evidence_path)
                raw_configuration = "with_skill" if normalized_configuration == "current" else "without_skill"
                expected_directory = f"/runs/{eval_id}-{raw_configuration}-{repetition}/"
                if expected_directory not in relative_evidence_path:
                    report.fail(f"{label}.{prefix}_path does not match its run identity")
            evidence_files[prefix] = resolve_evidence_file(
                skill_root,
                relative_evidence_path,
                run.get("review_output_file_sha256") if prefix == "review_output" else run.get(f"{prefix}_sha256"),
                f"{label}.{prefix}_path",
                report,
            )
        direct_report_path = evidence_files.get("direct_agent_report")
        direct_report = read_json(direct_report_path) if direct_report_path is not None else None
        direct_task_path = evidence_files.get("direct_task")
        direct_task = read_json(direct_task_path) if direct_task_path is not None else None
        context_id = run.get("context_id")
        if not isinstance(context_id, str) or not context_id.strip():
            report.fail(f"{label}.context_id must be a non-empty harness-issued identifier")
        elif context_id in behavior_context_ids:
            report.fail(f"{label}.context_id is reused by another behavior run")
        else:
            behavior_context_ids.add(context_id)
        if not isinstance(direct_task, dict):
            report.fail(f"{label}.direct_task must be a hashed public worker task")
        else:
            forbidden_public_keys = {
                "eval_id", "eval_name", "configuration", "repetition", "case_contract",
                "validation", "allowed_change_paths", "required_change_paths",
                "forbidden_change_paths", "expectations", "expected_output", "skill_usage",
                "skill_snapshot_before_sha256", "skill_snapshot_after_sha256",
                "skill_snapshot_contract_sha256",
            }
            leaked_keys = sorted(forbidden_public_keys & set(direct_task))
            if leaked_keys:
                report.fail(f"{label}.direct_task leaks private grader keys: {leaked_keys}")
            raw_configuration = "with_skill" if normalized_configuration == "current" else "without_skill"
            expected_job_id = "job-" + hashlib.sha256(
                f"document-writing-behavior:{eval_id}:{raw_configuration}:{repetition}".encode("utf-8")
            ).hexdigest()[:24]
            required_public_fields = {
                "job_id", "prompt", "run_dir", "workspace", "response_path", "report_path",
                "model", "reasoning_effort", "context_id", "report_contract",
            }
            missing_public_fields = sorted(required_public_fields - set(direct_task))
            if missing_public_fields:
                report.fail(f"{label}.direct_task is missing public worker fields: {missing_public_fields}")
            if direct_task.get("job_id") != expected_job_id:
                report.fail(f"{label}.direct_task job_id does not match its private evidence identity")
            run_dir_value = direct_task.get("run_dir")
            if not isinstance(run_dir_value, str) or Path(run_dir_value).name != expected_job_id:
                report.fail(f"{label}.direct_task run_dir must use its opaque job id")
            if direct_task.get("prompt") != prompt_by_id.get(eval_id):
                report.fail(f"{label}.direct_task prompt does not match the user-facing eval prompt")
            if (
                direct_task.get("context_id") != context_id
                or direct_task.get("model") != EXECUTION_MODEL
                or direct_task.get("reasoning_effort") != EXECUTION_REASONING_EFFORT
            ):
                report.fail(f"{label}.direct_task must bind the model and harness context")
            if normalized_configuration == "without_skill":
                if "skill_path" in direct_task:
                    report.fail(f"{label}.direct_task must omit skill_path for without_skill")
            else:
                skill_path = direct_task.get("skill_path")
                if not isinstance(skill_path, str) or Path(skill_path).name != "skill-snapshot":
                    report.fail(f"{label}.direct_task must expose only the supplied execution skill snapshot")
            report_contract = direct_task.get("report_contract")
            report_contract_text = json.dumps(report_contract, ensure_ascii=False).lower()
            if not isinstance(report_contract, dict):
                report.fail(f"{label}.direct_task report_contract must be an object")
            elif "clarification_required" in report_contract_text or "completed" in report_contract_text:
                report.fail(f"{label}.direct_task report_contract must not disclose grader-approved states")
        if not isinstance(direct_report, dict):
            report.fail(f"{label}.direct_agent_report must be a hashed JSON object")
        else:
            report_status = direct_report.get("status")
            if report_status != "completed" and not (
                report_status == "clarification_required"
                and eval_id in CLARIFICATION_EVAL_IDS
            ):
                report.fail(f"{label}.direct_agent_report.status is not an allowed terminal state")
            if report_status in {"execution-error", "runner-error"}:
                report.fail(f"{label}.direct_agent_report execution integrity status is invalid")
            if direct_report.get("return_code") != 0 or direct_report.get("timed_out") is not False:
                report.fail(f"{label}.direct_agent_report must record a normal non-timeout exit")
            if not isinstance(direct_report.get("stderr"), str):
                report.fail(f"{label}.direct_agent_report.stderr must be a string")
            direct_events = direct_report.get("tool_events")
            if not isinstance(direct_events, list) or any(
                not isinstance(event, dict)
                or event.get("name") not in DIRECT_EVENT_NAMES
                or not isinstance(event.get("input"), dict)
                or event.get("status") not in {"success", "error"}
                or not isinstance(event.get("output"), str)
                for event in direct_events
            ):
                report.fail(f"{label}.direct_agent_report must contain strict explicit tool_events")
            if direct_report.get("model") != EXECUTION_MODEL:
                report.fail(f"{label}.direct_agent_report.model must be {EXECUTION_MODEL!r}")
            if direct_report.get("reasoning_effort") != EXECUTION_REASONING_EFFORT:
                report.fail(f"{label}.direct_agent_report.reasoning_effort must be {EXECUTION_REASONING_EFFORT!r}")
            if direct_report.get("context_id") != context_id:
                report.fail(f"{label}.direct_agent_report.context_id must match the harness-issued task context")
            telemetry_status = direct_report.get("telemetry_status")
            if telemetry_status not in {"available", "unavailable"}:
                report.fail(f"{label}.direct_agent_report.telemetry_status must be available or unavailable")
            for field in ("duration_ms", "total_tokens"):
                value = direct_report.get(field)
                if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < 0):
                    report.fail(f"{label}.direct_agent_report.{field} must be null or a non-negative integer")
                if telemetry_status == "unavailable" and value is not None:
                    report.fail(f"{label}.direct_agent_report.{field} must be null when telemetry is unavailable")
                if telemetry_status == "available" and value is None:
                    report.fail(f"{label}.direct_agent_report.{field} must be recorded when telemetry is available")
            produced_paths = direct_report.get("produced_paths")
            if not isinstance(produced_paths, list) or any(not isinstance(item, str) or not item.strip() for item in produced_paths):
                report.fail(f"{label}.direct_agent_report.produced_paths must be a non-empty-path string array")
            elif len(set(produced_paths)) != len(produced_paths) or any(
                Path(item).is_absolute() or ".." in PurePosixPath(item.replace("\\", "/")).parts or item != item.replace("\\", "/")
                for item in produced_paths
            ):
                report.fail(f"{label}.direct_agent_report.produced_paths must contain unique normalized workspace-relative paths")
            before_manifest = read_json(evidence_files.get("before_manifest")) if evidence_files.get("before_manifest") else None
            after_manifest = read_json(evidence_files.get("after_manifest")) if evidence_files.get("after_manifest") else None
            if isinstance(before_manifest, dict) and isinstance(after_manifest, dict):
                expected_changes = manifest_changed_paths(before_manifest, after_manifest)
                if sorted(produced_paths) != expected_changes:
                    report.fail(f"{label}.direct_agent_report.produced_paths does not match the published before/after manifests")
                if run.get("actual_changes") != expected_changes:
                    report.fail(f"{label}.actual_changes does not match the published before/after manifests")
                if sorted(run.get("actual_changes", [])) != sorted(produced_paths):
                    report.fail(f"{label}.actual_changes must match direct report produced_paths")
                validate_direct_report_integrity(
                    run,
                    direct_report,
                    before_manifest,
                    after_manifest,
                    normalized_configuration,
                    int(eval_id) if isinstance(eval_id, int) else -1,
                    report,
                    label,
                )
        eval_metadata_path = evidence_files.get("eval_metadata")
        eval_metadata = read_json(eval_metadata_path) if eval_metadata_path is not None else None
        expected_raw_configuration = "with_skill" if normalized_configuration == "current" else "without_skill"
        if not isinstance(eval_metadata, dict):
            report.fail(f"{label}.eval_metadata must be a hashed JSON object")
        else:
            if (
                eval_metadata.get("eval_id") != eval_id
                or eval_metadata.get("configuration") != expected_raw_configuration
                or eval_metadata.get("run_number") != repetition
            ):
                report.fail(f"{label}.eval_metadata identity does not match the behavior run")
            if eval_metadata.get("transcript_provenance") != "reconstructed-from-direct-agent-report":
                report.fail(f"{label}.eval_metadata must disclose reconstructed transcript provenance")
            if eval_metadata.get("direct_agent_report_sha256") != run.get("direct_agent_report_sha256"):
                report.fail(f"{label}.eval_metadata direct report hash does not match the published artifact")
            if isinstance(direct_report, dict) and eval_metadata.get("direct_agent_status") != direct_report.get("status", "unreported"):
                report.fail(f"{label}.eval_metadata direct agent status does not match the published report")
            if eval_metadata.get("tool_event_provenance") != "agent-reported-not-raw-telemetry":
                report.fail(f"{label}.eval_metadata must disclose agent-reported tool-event provenance")
            if eval_metadata.get("context_id") != context_id:
                report.fail(f"{label}.eval_metadata.context_id must match the behavior run")
        snapshot_before_path = evidence_files.get("skill_snapshot_before")
        snapshot_after_path = evidence_files.get("skill_snapshot_after")
        snapshot_before = read_json(snapshot_before_path) if snapshot_before_path is not None else None
        snapshot_after = read_json(snapshot_after_path) if snapshot_after_path is not None else None
        if not isinstance(snapshot_before, dict) or not isinstance(snapshot_after, dict):
            report.fail(f"{label} must publish skill snapshot before/after manifests")
        elif normalized_configuration == "without_skill":
            for snapshot_name, snapshot in (("before", snapshot_before), ("after", snapshot_after)):
                if (
                    snapshot.get("kind") != "without-skill"
                    or snapshot.get("exists") is not False
                    or snapshot.get("sha256") is not None
                    or snapshot.get("source_contract_sha256") is not None
                    or snapshot.get("files", {}) not in ({}, None)
                    or snapshot.get("entries", []) not in ([], None)
                ):
                    report.fail(f"{label}.skill_snapshot_{snapshot_name} must be an immutable without-skill absence manifest")
            if isinstance(eval_metadata, dict) and any(
                eval_metadata.get(field) is not None
                for field in ("skill_contract_sha256", "skill_snapshot_before_sha256", "skill_snapshot_after_sha256")
            ):
                report.fail(f"{label}.eval_metadata must not claim a skill snapshot for without_skill")
        else:
            snapshot_before_files = validated_manifest_files(snapshot_before, f"{label}.skill_snapshot_before", report)
            snapshot_after_files = validated_manifest_files(snapshot_after, f"{label}.skill_snapshot_after", report)
            snapshot_before_tree = validated_manifest_tree_hash(snapshot_before, snapshot_before_files, f"{label}.skill_snapshot_before", report)
            snapshot_after_tree = validated_manifest_tree_hash(snapshot_after, snapshot_after_files, f"{label}.skill_snapshot_after", report)
            source_contract = snapshot_before.get("source_contract_sha256")
            expected_source_contract = current_contract_sha256 if normalized_configuration == "current" else None
            if (
                snapshot_before_tree != snapshot_before.get("sha256")
                or snapshot_after_tree != snapshot_after.get("sha256")
                or snapshot_before.get("sha256") != snapshot_after.get("sha256")
                or snapshot_before_files != snapshot_after_files
                or not is_sha256(source_contract)
                or snapshot_after.get("source_contract_sha256") != source_contract
                or source_contract != expected_source_contract
            ):
                report.fail(f"{label} execution skill snapshot changed or has invalid provenance")
            if isinstance(eval_metadata, dict) and (
                eval_metadata.get("skill_contract_sha256") != source_contract
                or eval_metadata.get("skill_snapshot_before_sha256") != snapshot_before.get("sha256")
                or eval_metadata.get("skill_snapshot_after_sha256") != snapshot_after.get("sha256")
            ):
                report.fail(f"{label}.eval_metadata does not bind the execution snapshot manifests")
        if run.get("transcript_provenance") != "reconstructed-from-direct-agent-report":
            report.fail(f"{label}.transcript_provenance is incorrect")
        if run.get("tool_event_provenance") != "agent-reported-not-raw-telemetry":
            report.fail(f"{label}.tool_event_provenance is incorrect")

        tool_events_path = evidence_files.get("tool_events")
        tool_events_payload = read_json(tool_events_path) if tool_events_path is not None else None
        expected_recorded_events: list[dict[str, Any]] = []
        if isinstance(direct_report, dict) and isinstance(direct_report.get("tool_events"), list):
            expected_recorded_events = [
                {
                    "tool_use_id": f"direct-tool-{event_index}",
                    "name": event["name"],
                    "input": event["input"],
                    "status": event["status"],
                    "output": event["output"],
                    "provenance": "agent-reported-not-raw-telemetry",
                }
                for event_index, event in enumerate(direct_report["tool_events"], start=1)
                if isinstance(event, dict)
                and event.get("name") in DIRECT_EVENT_NAMES
                and isinstance(event.get("input"), dict)
                and event.get("status") in {"success", "error"}
                and isinstance(event.get("output"), str)
            ]
        expected_counts = dict(Counter(event["name"] for event in expected_recorded_events))
        if not isinstance(tool_events_payload, dict) or (
            tool_events_payload.get("provenance") != "agent-reported-not-raw-telemetry"
            or tool_events_payload.get("events") != expected_recorded_events
            or tool_events_payload.get("counts") != expected_counts
        ):
            report.fail(f"{label}.tool_events must be derived exactly from the published direct agent report")

        response_path = evidence_files.get("response")
        response_text = response_path.read_text(encoding="utf-8") if response_path is not None else None
        transcript_path = evidence_files.get("transcript")
        if isinstance(direct_report, dict) and isinstance(response_text, str) and transcript_path is not None:
            assistant_blocks = [
                {"type": "tool_use", "id": event["tool_use_id"], "name": event["name"], "input": event["input"]}
                for event in expected_recorded_events
            ]
            result_blocks = [
                {"type": "tool_result", "tool_use_id": event["tool_use_id"], "is_error": event["status"] != "success", "content": event["output"]}
                for event in expected_recorded_events
            ]
            transcript_records = [{"type": "system", "subtype": "init", "model": direct_report.get("model"), "provenance": "reconstructed-from-agent-report"}]
            if assistant_blocks:
                transcript_records.append({"type": "assistant", "message": {"content": assistant_blocks}})
                transcript_records.append({"type": "user", "message": {"content": result_blocks}})
            transcript_records.append({"type": "assistant", "message": {"content": [{"type": "text", "text": response_text}]}})
            transcript_records.append({"type": "result", "is_error": False, "result": response_text, "provenance": "reconstructed-from-agent-report"})
            expected_transcript = "\n".join(json.dumps(item, ensure_ascii=False) for item in transcript_records) + "\n"
            if transcript_path.read_text(encoding="utf-8") != expected_transcript:
                report.fail(f"{label}.transcript must be reconstructed exactly from report events and response")

        stderr_path = evidence_files.get("stderr")
        if isinstance(direct_report, dict) and stderr_path is not None and stderr_path.read_text(encoding="utf-8") != direct_report.get("stderr"):
            report.fail(f"{label}.stderr artifact does not match the direct agent report")
        timing_path = evidence_files.get("timing")
        timing_payload = read_json(timing_path) if timing_path is not None else None
        if isinstance(direct_report, dict) and isinstance(timing_payload, dict):
            duration_ms = direct_report.get("duration_ms")
            expected_timing = {
                "executor_duration_seconds": duration_ms / 1000 if duration_ms is not None else None,
                "total_duration_seconds": duration_ms / 1000 if duration_ms is not None else None,
                "duration_ms": duration_ms,
                "total_tokens": direct_report.get("total_tokens"),
                "return_code": direct_report.get("return_code"),
                "timed_out": direct_report.get("timed_out"),
                "requested_model": direct_report.get("model"),
                "model": direct_report.get("model"),
                "reasoning_effort": direct_report.get("reasoning_effort"),
                "telemetry_status": direct_report.get("telemetry_status"),
                "produced_paths": direct_report.get("produced_paths"),
                "context_id": direct_report.get("context_id"),
            }
            if timing_payload != expected_timing:
                report.fail(f"{label}.timing must be derived exactly from the direct agent report")
        metrics_path = evidence_files.get("metrics")
        metrics_payload = read_json(metrics_path) if metrics_path is not None else None
        if isinstance(metrics_payload, dict) and isinstance(response_text, str) and transcript_path is not None:
            if (
                metrics_payload.get("tool_calls") != expected_counts
                or metrics_payload.get("total_tool_calls") != len(expected_recorded_events)
                or metrics_payload.get("total_steps") != len(expected_recorded_events)
                or metrics_payload.get("errors_encountered") != sum(event["status"] != "success" for event in expected_recorded_events)
                or metrics_payload.get("output_chars") != len(response_text)
                or metrics_payload.get("transcript_chars") != len(transcript_path.read_text(encoding="utf-8"))
            ):
                report.fail(f"{label}.metrics do not match the published report, response, and transcript")
        if run.get("model") != EXECUTION_MODEL:
            report.fail(f"{label}.model must be {EXECUTION_MODEL!r}")
        if run.get("reasoning_effort") != EXECUTION_REASONING_EFFORT:
            report.fail(f"{label}.reasoning_effort must be {EXECUTION_REASONING_EFFORT!r}")
        if run.get("telemetry_status") not in {"available", "unavailable"}:
            report.fail(f"{label}.telemetry_status must be available or unavailable")
        for field in ("duration_ms", "total_tokens"):
            value = run.get(field)
            if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < 0):
                report.fail(f"{label}.{field} must be null or a non-negative integer")
            if run.get("telemetry_status") == "unavailable" and value is not None:
                report.fail(f"{label}.{field} must be null when telemetry is unavailable")
        if isinstance(timing_payload, dict) and (
            run.get("model") != timing_payload.get("model")
            or run.get("reasoning_effort") != timing_payload.get("reasoning_effort")
            or run.get("telemetry_status") != timing_payload.get("telemetry_status")
            or run.get("duration_ms") != timing_payload.get("duration_ms")
            or run.get("total_tokens") != timing_payload.get("total_tokens")
            or run.get("produced_paths") != timing_payload.get("produced_paths")
        ):
            report.fail(f"{label} model, duration, and tokens must match the timing artifact")
        if run.get("execution_completed") is not True:
            report.fail(f"{label}.execution_completed must be true")
        if run.get("execution_integrity_status") in {"execution-error", "runner-error", "invalid"} or run.get("execution_status") in {"execution-error", "runner-error", "invalid"}:
            report.fail(f"{label} execution integrity status rejects this run")
        grading = run.get("grading")
        if not isinstance(grading, dict):
            report.fail(f"{label}.grading must be an object")
            continue
        grading_path = evidence_files.get("grading")
        if grading_path is not None:
            loaded_grading = read_json(grading_path)
            if loaded_grading != grading:
                report.fail(f"{label}.grading must equal its hashed grading artifact")
        if grading.get("status") != "completed-independent-grading":
            report.fail(f"{label}.grading must be completed-independent-grading")
        graded_expectations = grading.get("expectations")
        if not isinstance(graded_expectations, list):
            report.fail(f"{label}.grading.expectations must be an array")
            continue
        valid_graded_records = [
            item
            for item in graded_expectations
            if isinstance(item, dict)
            and isinstance(item.get("text"), str)
            and isinstance(item.get("passed"), bool)
            and isinstance(item.get("evidence"), str)
            and item.get("evidence")
        ]
        if len(valid_graded_records) != len(graded_expectations):
            report.fail(f"{label}.grading contains malformed expectation records")
        deterministic_path = evidence_files.get("deterministic_grading")
        deterministic_payload = read_json(deterministic_path) if deterministic_path is not None else {}
        deterministic_expectations = deterministic_payload.get("expectations")
        if not isinstance(deterministic_expectations, list) or not deterministic_expectations:
            report.fail(f"{label}.deterministic grading artifact must contain expectations")
            deterministic_expectations = []
        if deterministic_payload.get("status") != "completed":
            report.fail(f"{label}.deterministic grading status must be completed")
        validators = deterministic_payload.get("validators")
        expected_validators = {"validate_eval_run.py"}
        expected_validators.update({
            11: {"validate_existing_update.mjs"},
            20: {"validate_preservation.mjs --exact-tree"},
            21: {"validate_preservation.mjs --exact-tree"},
            22: {"validate_noncanonical_store.mjs"},
        }.get(eval_id, set()))
        validator_names = {
            item.get("name")
            for item in validators
            if isinstance(item, dict)
        } if isinstance(validators, list) else set()
        if validator_names != expected_validators:
            report.fail(f"{label}.deterministic grading validator set is incorrect")
        if normalized_configuration == "current" and isinstance(validators, list) and any(item.get("return_code") != 0 for item in validators if isinstance(item, dict)):
            report.fail(f"{label}.deterministic validators must exit 0 for current")
        normalized_from_stdout = [
            expectation
            for validator in (validators if isinstance(validators, list) else [])
            if isinstance(validator, dict)
            for expectation in normalized_validator_expectations(validator)
        ]
        expected_snapshot_text = (
            "Execution skill snapshot remains unchanged"
            if normalized_configuration == "current"
            else "No document-writing skill snapshot is available"
        )
        snapshot_expectations = [
            item
            for item in deterministic_expectations
            if isinstance(item, dict) and item.get("text") == expected_snapshot_text
        ]
        non_snapshot_expectations = [
            item
            for item in deterministic_expectations
            if not (isinstance(item, dict) and item.get("text") == expected_snapshot_text)
        ]
        if non_snapshot_expectations != normalized_from_stdout:
            report.fail(f"{label}.deterministic expectations do not match validator stdout")
        if (
            len(snapshot_expectations) != 1
            or snapshot_expectations[0].get("passed") is not True
            or not isinstance(snapshot_before, dict)
            or not isinstance(snapshot_after, dict)
            or snapshot_expectations[0].get("evidence") != (
                f"before={snapshot_before.get('sha256')} after={snapshot_after.get('sha256')} "
                f"uses_skill={normalized_configuration == 'current'}"
            )
        ):
            report.fail(f"{label}.deterministic grading must contain one valid snapshot-preservation expectation")
        deterministic_passed = sum(item.get("passed") is True for item in deterministic_expectations if isinstance(item, dict))
        deterministic_total = len(deterministic_expectations)
        deterministic_summary = deterministic_payload.get("summary")
        if not isinstance(deterministic_summary, dict) or (
            deterministic_summary.get("passed") != deterministic_passed
            or deterministic_summary.get("failed") != deterministic_total - deterministic_passed
            or deterministic_summary.get("total") != deterministic_total
            or deterministic_summary.get("pass_rate") != (deterministic_passed / deterministic_total if deterministic_total else 0.0)
        ):
            report.fail(f"{label}.deterministic grading summary is inconsistent")
        semantic_texts = list(semantic_by_id.get(eval_id, []))
        expected_texts = Counter([*semantic_texts, *[item.get("text") for item in deterministic_expectations if isinstance(item, dict)]])
        graded_texts = Counter(item.get("text") for item in valid_graded_records)
        if graded_texts != expected_texts:
            report.fail(f"{label}.grading must contain exactly one copy of every semantic and deterministic expectation")
        deterministic_records = Counter(
            json.dumps(item, ensure_ascii=False, sort_keys=True)
            for item in deterministic_expectations
            if isinstance(item, dict)
        )
        preserved_records = Counter(
            json.dumps(item, ensure_ascii=False, sort_keys=True)
            for item in valid_graded_records
            if item.get("text") not in semantic_texts
        )
        if preserved_records != deterministic_records:
            report.fail(f"{label}.grading must preserve deterministic expectation verdicts and evidence exactly")
        if normalized_configuration == "current" and any(item.get("passed") is not True for item in deterministic_expectations if isinstance(item, dict)):
            report.fail(f"{label}.deterministic validator expectations must all pass for current")
        passed = sum(item.get("passed") is True for item in graded_expectations if isinstance(item, dict))
        total = len(graded_expectations)
        calculated_rate = passed / total if total else 0.0
        summary = grading.get("summary")
        if not isinstance(summary, dict) or (
            summary.get("passed") != passed
            or summary.get("total") != total
            or summary.get("failed") != total - passed
            or summary.get("pass_rate") != calculated_rate
        ):
            report.fail(f"{label}.grading.summary does not match graded expectations")
        if isinstance(eval_id, int) and isinstance(normalized_configuration, str) and isinstance(repetition, int):
            scores[(eval_id, normalized_configuration, repetition)] = calculated_rate

        before_path = evidence_files.get("before_manifest")
        after_path = evidence_files.get("after_manifest")
        if before_path is not None and after_path is not None:
            before_manifest = read_json(before_path)
            after_manifest = read_json(after_path)
            before_files = validated_manifest_files(before_manifest, f"{label}.before_manifest", report)
            after_files = validated_manifest_files(after_manifest, f"{label}.after_manifest", report)
            before_tree_hash = validated_manifest_tree_hash(before_manifest, before_files, f"{label}.before_manifest", report)
            after_tree_hash = validated_manifest_tree_hash(after_manifest, after_files, f"{label}.after_manifest", report)
            if before_tree_hash != before_manifest.get("sha256"):
                report.fail(f"{label}.before_manifest.sha256 is not canonical")
            if after_tree_hash != after_manifest.get("sha256"):
                report.fail(f"{label}.after_manifest.sha256 is not canonical")
            if before_manifest.get("sha256") != run.get("workspace_before_sha256"):
                report.fail(f"{label}.workspace_before_sha256 does not match before manifest")
            if after_manifest.get("sha256") != run.get("workspace_after_sha256") or after_manifest.get("sha256") != run.get("output_tree_sha256"):
                report.fail(f"{label} after/output tree hashes do not match after manifest")
            before_state = {
                entry.get("path"): (f"file:{entry.get('sha256')}" if entry.get("type") == "file" else str(entry.get("type")))
                for entry in before_manifest.get("entries", [])
                if isinstance(entry, dict) and isinstance(entry.get("path"), str)
            }
            after_state = {
                entry.get("path"): (f"file:{entry.get('sha256')}" if entry.get("type") == "file" else str(entry.get("type")))
                for entry in after_manifest.get("entries", [])
                if isinstance(entry, dict) and isinstance(entry.get("path"), str)
            }
            if sorted(after_state) != run.get("output_tree"):
                report.fail(f"{label}.output_tree does not match after manifest")
            calculated_changes = manifest_changed_paths(before_manifest, after_manifest)
            if calculated_changes != actual_changes:
                report.fail(f"{label}.actual_changes must be recalculated from before/after manifests")
        review_output_path = evidence_files.get("review_output")
        if review_output_path is not None:
            review_bundle = read_json(review_output_path)
            review_files = validated_manifest_files(review_bundle, f"{label}.review_output", report)
            review_tree_hash = validated_manifest_tree_hash(review_bundle, review_files, f"{label}.review_output", report)
            if review_tree_hash != run.get("review_output_sha256") or review_tree_hash != review_bundle.get("sha256"):
                report.fail(f"{label}.review_output_sha256 does not match its bundle")
            contents = review_bundle.get("contents")
            if not isinstance(contents, dict) or set(contents) != set(review_files):
                report.fail(f"{label}.review_output contents do not match files")
            elif any(
                not isinstance(contents[path], str)
                or hashlib.sha256(contents[path].encode("utf-8")).hexdigest() != digest
                for path, digest in review_files.items()
            ):
                report.fail(f"{label}.review_output content hashes do not match")
    for eval_id in PRODUCTION_BEHAVIOR_IDS:
        for configuration in ("current", "without_skill"):
            repetitions = repetitions_by_configuration.get((eval_id, configuration), set())
            if len(repetitions) < 2:
                report.fail(
                    "production evidence behavior.runs must contain at least two "
                    f"{configuration} runs for eval {eval_id}"
                )
        for configuration in ("current", "without_skill"):
            if repetitions_by_configuration.get((eval_id, configuration), set()) != {1, 2}:
                report.fail(f"behavior eval {eval_id} must contain exactly runs 1 and 2 for {configuration}")
    return scores


def validate_selection_batch_records(
    skill_root: Path,
    batches: list[Any],
    cases: dict[int, dict[str, Any]],
    report: Report,
) -> dict[tuple[str, int], dict[str, Any]]:
    records: dict[tuple[str, int], dict[str, Any]] = {}
    context_ids: set[str] = set()
    current_skill = read_text(skill_root / "SKILL.md")
    current_match = re.search(r"^description:\s*(.+)$", current_skill, re.MULTILINE)
    current_description = current_match.group(1).strip() if current_match else ""
    expected_cases = [{"id": case_id, "query": cases[case_id]["query"]} for case_id in sorted(cases)]
    used_paths: set[str] = set()

    for index, batch in enumerate(batches):
        label = f"production evidence selection.batches[{index}]"
        if not isinstance(batch, dict):
            report.fail(f"{label} must be an object")
            continue
        configuration = batch.get("configuration")
        repetition = batch.get("repetition")
        if configuration != "current" or repetition not in {1, 2, 3}:
            report.fail(f"{label} has an invalid configuration or repetition")
            continue
        identity = (configuration, repetition)
        if identity in records:
            report.fail(f"{label} duplicates selection batch {identity}")
            continue
        raw_configuration = "current"
        expected_batch_id = f"{raw_configuration}-run-{repetition}"
        if batch.get("batch_id") != expected_batch_id:
            report.fail(f"{label}.batch_id is incorrect")
        evidence_files: dict[str, Path | None] = {}
        for prefix in ("input", "output", "receipt", "stderr"):
            relative = batch.get(f"{prefix}_path")
            if isinstance(relative, str):
                if relative in used_paths:
                    report.fail(f"{label}.{prefix}_path is reused")
                used_paths.add(relative)
                if f"/selection-batches/{raw_configuration}-{repetition}/" not in relative:
                    report.fail(f"{label}.{prefix}_path does not match the batch identity")
            evidence_files[prefix] = resolve_evidence_file(
                skill_root,
                relative,
                batch.get(f"{prefix}_file_sha256"),
                f"{label}.{prefix}_path",
                report,
            )
        input_payload = read_json(evidence_files["input"]) if evidence_files.get("input") is not None else None
        output_payload = read_json(evidence_files["output"]) if evidence_files.get("output") is not None else None
        receipt_payload = read_json(evidence_files["receipt"]) if evidence_files.get("receipt") is not None else None
        stderr_text = evidence_files["stderr"].read_text(encoding="utf-8") if evidence_files.get("stderr") is not None else None
        if receipt_payload != batch.get("receipt") or batch.get("receipt_sha256") != batch.get("receipt_file_sha256"):
            report.fail(f"{label}.receipt does not match its hashed artifact")
        expected_description = current_description
        if not isinstance(input_payload, dict) or (
            input_payload.get("batch_id") != expected_batch_id
            or input_payload.get("configuration") != raw_configuration
            or input_payload.get("repetition") != repetition
            or not isinstance(input_payload.get("context_id"), str)
            or not input_payload["context_id"].strip()
            or input_payload.get("description") != expected_description
            or input_payload.get("cases") != expected_cases
        ):
            report.fail(f"{label}.input is not the canonical label-free selection batch")
        if not isinstance(output_payload, dict) or (
            output_payload.get("status") != "completed"
            or output_payload.get("context_id") != input_payload.get("context_id")
            or output_payload.get("model") != EXECUTION_MODEL
            or output_payload.get("reasoning_effort") != EXECUTION_REASONING_EFFORT
            or output_payload.get("telemetry_status") not in {"available", "unavailable"}
            or not (output_payload.get("duration_ms") is None or (isinstance(output_payload.get("duration_ms"), int) and not isinstance(output_payload.get("duration_ms"), bool) and output_payload["duration_ms"] >= 0))
            or not (output_payload.get("total_tokens") is None or (isinstance(output_payload.get("total_tokens"), int) and not isinstance(output_payload.get("total_tokens"), bool) and output_payload["total_tokens"] >= 0))
            or output_payload.get("telemetry_status") == "available" and (output_payload.get("duration_ms") is None or output_payload.get("total_tokens") is None)
            or output_payload.get("telemetry_status") == "unavailable" and (output_payload.get("duration_ms") is not None or output_payload.get("total_tokens") is not None)
            or output_payload.get("return_code") != 0
            or output_payload.get("timed_out") is not False
            or not isinstance(output_payload.get("stderr"), str)
            or not isinstance(output_payload.get("decisions"), list)
            or len(output_payload["decisions"]) != SELECTION_CASE_COUNT
        ):
            report.fail(f"{label}.output is not a completed direct Codex batch")
        elif output_payload["context_id"] in context_ids:
            report.fail(f"{label}.context_id is reused by another selection batch")
        else:
            context_ids.add(output_payload["context_id"])
        if isinstance(output_payload, dict) and stderr_text != output_payload.get("stderr"):
            report.fail(f"{label}.stderr does not match the batch output")
        if not isinstance(receipt_payload, dict) or not isinstance(input_payload, dict) or not isinstance(output_payload, dict):
            continue
        if (
            receipt_payload.get("batch_id") != expected_batch_id
            or receipt_payload.get("configuration") != raw_configuration
            or receipt_payload.get("repetition") != repetition
            or receipt_payload.get("status") != "completed"
            or receipt_payload.get("provenance") != "local-unattested-direct-codex-batch"
            or receipt_payload.get("context_id") != output_payload.get("context_id")
            or receipt_payload.get("model") != output_payload.get("model")
            or receipt_payload.get("reasoning_effort") != output_payload.get("reasoning_effort")
            or receipt_payload.get("telemetry_status") != output_payload.get("telemetry_status")
            or receipt_payload.get("duration_ms") != output_payload.get("duration_ms")
            or receipt_payload.get("total_tokens") != output_payload.get("total_tokens")
            or receipt_payload.get("duration_scope") != "batch"
            or receipt_payload.get("return_code") != 0
            or receipt_payload.get("timed_out") is not False
            or receipt_payload.get("decision_count") != SELECTION_CASE_COUNT
            or receipt_payload.get("input_sha256") != batch.get("input_file_sha256")
            or receipt_payload.get("output_sha256") != batch.get("output_file_sha256")
            or receipt_payload.get("stderr_sha256") != batch.get("stderr_file_sha256")
            or receipt_payload.get("description_sha256") != hashlib.sha256(expected_description.encode("utf-8")).hexdigest()
        ):
            report.fail(f"{label}.receipt does not bind its input, output, and executor metadata")
        records[identity] = {"input": input_payload, "output": output_payload, "receipt": receipt_payload, "receipt_sha256": batch.get("receipt_file_sha256")}
    if set(records) != {("current", repetition) for repetition in (1, 2, 3)}:
        report.fail("production evidence selection.batches must contain exactly three current repetitions")
    return records


def validate_selection_run_records(skill_root: Path, batches: list[Any], runs: list[Any], report: Report) -> dict[str, dict[str, float | int]]:
    actual_runs: set[tuple[int, str, int]] = set()
    dataset = read_json(skill_root / "evals/design-system-selection-evals.json")
    cases = {
        item["id"]: item
        for item in dataset
        if isinstance(item, dict) and isinstance(item.get("id"), int)
    }
    batch_records = validate_selection_batch_records(skill_root, batches, cases, report)
    decisions: dict[str, list[tuple[bool, bool, bool]]] = {"current": []}
    used_receipt_paths: set[str] = set()
    for index, run in enumerate(runs):
        label = f"production evidence selection.runs[{index}]"
        if not isinstance(run, dict):
            report.fail(f"{label} must be an object")
            continue
        case_id = run.get("case_id")
        configuration = run.get("configuration")
        repetition = run.get("repetition")
        normalized_configuration = {"with_skill": "current"}.get(configuration, configuration)
        if (
            isinstance(case_id, int)
            and 1 <= case_id <= SELECTION_CASE_COUNT
            and normalized_configuration == "current"
            and isinstance(repetition, int)
            and not isinstance(repetition, bool)
            and repetition in {1, 2, 3}
        ):
            identity = (case_id, normalized_configuration, repetition)
            if identity in actual_runs:
                report.fail(f"{label} duplicates selection run {identity}")
            else:
                actual_runs.add(identity)
        else:
            report.fail(f"{label} requires integer case_id/repetition and string configuration")
        if run.get("source") != "local-unattested direct Codex selection judgment":
            report.fail(f"{label}.source must disclose a local-unattested direct Codex judgment")
        batch_record = batch_records.get((normalized_configuration, repetition)) if normalized_configuration == "current" and repetition in {1, 2, 3} else None
        expected_batch_id = f"current-run-{repetition}" if normalized_configuration == "current" and repetition in {1, 2, 3} else None
        if not isinstance(batch_record, dict) or run.get("batch_id") != expected_batch_id:
            report.fail(f"{label} does not reference a valid selection batch")
        if not isinstance(run.get("selected"), bool):
            report.fail(f"{label}.selected must be boolean")
        elif isinstance(case_id, int) and case_id in cases and normalized_configuration in decisions:
            expected = cases[case_id]
            if run.get("should_trigger") != expected.get("should_trigger"):
                report.fail(f"{label}.should_trigger must match the canonical selection dataset")
            if run.get("high_risk") != expected.get("high_risk"):
                report.fail(f"{label}.high_risk must match the canonical selection dataset")
            decisions[normalized_configuration].append(
                (bool(run["selected"]), bool(expected["should_trigger"]), bool(expected["high_risk"]))
            )
        receipt = run.get("receipt")
        if not isinstance(receipt, dict):
            report.fail(f"{label}.receipt must be an object")
        else:
            raw_configuration = "current"
            expected_query_hash = hashlib.sha256(str(cases.get(case_id, {}).get("query", "")).encode("utf-8")).hexdigest()
            if (
                receipt.get("case_id") != case_id
                or receipt.get("configuration") != raw_configuration
                or receipt.get("repetition") != repetition
                or receipt.get("status") != "completed"
                or receipt.get("selected") is not run.get("selected")
                or not isinstance(receipt.get("model"), str)
                or not receipt["model"]
                or receipt.get("duration_ms") is not None
                or receipt.get("duration_scope") != "per-case-unavailable"
                or not (
                    receipt.get("batch_duration_ms") is None
                    or isinstance(receipt.get("batch_duration_ms"), int)
                    and not isinstance(receipt.get("batch_duration_ms"), bool)
                    and receipt["batch_duration_ms"] >= 0
                )
                or receipt.get("batch_id") != expected_batch_id
                or receipt.get("transcript_provenance") != "synthetic-from-batch-output"
                or not is_sha256(receipt.get("transcript_sha256"))
                or not is_sha256(receipt.get("stderr_sha256"))
                or receipt.get("query_sha256") != expected_query_hash
                or not is_sha256(receipt.get("description_sha256"))
            ):
                report.fail(f"{label}.receipt does not prove a completed selector decision")
            if isinstance(batch_record, dict):
                batch_receipt = batch_record.get("receipt", {})
                batch_output = batch_record.get("output", {})
                batch_decision = next(
                    (item for item in batch_output.get("decisions", []) if isinstance(item, dict) and item.get("id") == case_id),
                    None,
                ) if isinstance(batch_output, dict) else None
                if (
                    receipt.get("batch_input_sha256") != batch_receipt.get("input_sha256")
                    or receipt.get("batch_output_sha256") != batch_receipt.get("output_sha256")
                    or receipt.get("batch_receipt_sha256") != batch_record.get("receipt_sha256")
                    or receipt.get("context_id") != batch_receipt.get("context_id")
                    or receipt.get("batch_duration_ms") != batch_receipt.get("duration_ms")
                    or not isinstance(batch_decision, dict)
                    or batch_decision.get("selected") is not run.get("selected")
                    or batch_decision.get("reason") != receipt.get("reason")
                ):
                    report.fail(f"{label}.receipt is not an exact projection of its batch output")
        if not is_sha256(run.get("receipt_sha256")):
            report.fail(f"{label}.receipt_sha256 must be lowercase SHA-256")
        receipt_files: dict[str, Path | None] = {}
        for prefix in ("receipt", "transcript", "stderr"):
            relative = run.get(f"{prefix}_path")
            if isinstance(relative, str):
                if relative in used_receipt_paths:
                    report.fail(f"{label}.{prefix}_path is reused by another selection run")
                used_receipt_paths.add(relative)
                raw_configuration = "current"
                expected_directory = f"/selection-runs/{raw_configuration}-{repetition}-{case_id}/"
                if expected_directory not in relative:
                    report.fail(f"{label}.{prefix}_path does not match its selection identity")
            receipt_files[prefix] = resolve_evidence_file(
                skill_root,
                relative,
                run.get(f"{prefix}_file_sha256"),
                f"{label}.{prefix}_path",
                report,
            )
        receipt_file = receipt_files.get("receipt")
        if receipt_file is not None:
            if read_json(receipt_file) != receipt:
                report.fail(f"{label}.receipt must equal its hashed receipt artifact")
            if run.get("receipt_sha256") != hashlib.sha256(receipt_file.read_bytes()).hexdigest():
                report.fail(f"{label}.receipt_sha256 does not match receipt artifact")
        transcript_file = receipt_files.get("transcript")
        if transcript_file is not None and isinstance(receipt, dict):
            if receipt.get("transcript_sha256") != hashlib.sha256(transcript_file.read_bytes()).hexdigest():
                report.fail(f"{label} transcript hash does not match selector receipt")
            expected_text = f"selected={str(bool(run.get('selected'))).lower()}\nreason={receipt.get('reason')}\n"
            expected_transcript = json.dumps(
                {"type": "assistant", "provenance": "synthetic-from-batch-output", "message": {"content": [{"type": "text", "text": expected_text}]}},
                ensure_ascii=False,
            ) + "\n"
            if transcript_file.read_text(encoding="utf-8") != expected_transcript:
                report.fail(f"{label} transcript is not the declared synthetic batch projection")
        stderr_file = receipt_files.get("stderr")
        if stderr_file is not None and isinstance(receipt, dict):
            if receipt.get("stderr_sha256") != hashlib.sha256(stderr_file.read_bytes()).hexdigest():
                report.fail(f"{label} stderr hash does not match selector receipt")
    expected_runs = {
        (case_id, "current", repetition)
        for case_id in range(1, SELECTION_CASE_COUNT + 1)
        for repetition in (1, 2, 3)
    }
    if actual_runs != expected_runs:
        report.fail("production evidence selection.runs must contain exactly three current runs per selection case")
    summary: dict[str, dict[str, float | int]] = {}
    for configuration, values in decisions.items():
        true_positive = sum(selected and expected for selected, expected, _ in values)
        false_positive = sum(selected and not expected for selected, expected, _ in values)
        true_negative = sum(not selected and not expected for selected, expected, _ in values)
        false_negative = sum(not selected and expected for selected, expected, _ in values)
        summary[configuration] = {
            "precision": true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0,
            "recall": true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0,
            "specificity": true_negative / (true_negative + false_positive) if true_negative + false_positive else 0.0,
            "high_risk_false_positives": sum(selected and not expected and high_risk for selected, expected, high_risk in values),
        }
    return summary


def validate_production_evidence(
    skill_root: Path,
    report: Report,
    require_production_ready: bool = False,
) -> None:
    path = skill_root / "evals/production-evidence.json"
    payload = read_json(path)
    if not isinstance(payload, dict) or payload.get("schema_version") != 2:
        report.fail("production evidence must use schema_version 2")
        return
    if payload.get("trust_boundary") != "local-unattested":
        report.fail("production evidence trust_boundary must be local-unattested")
    validate_evidence_date(payload.get("generated_at"), report)
    expected_digest = contract_digest(skill_root)
    if payload.get("contract_sha256") != expected_digest:
        report.fail(
            "production evidence is stale for the current skill contract; rerun critical evals and refresh contract_sha256"
        )
    if "baseline_ref" in payload or "baseline_contract_sha256" in payload:
        report.fail("production evidence must not contain baseline_ref or baseline_contract_sha256")
    if not production_iteration_is_accepted(payload.get("iteration")):
        report.fail("production evidence iteration must be a positive integer")
    if payload.get("iteration") == 8:
        report.fail("iteration-8 evidence is diagnostic-only and cannot be accepted")
    if require_production_ready and (
        payload.get("status") == "diagnostic-failed"
        or payload.get("production_ready") is not True
    ):
        report.fail("production-ready validation rejects diagnostic-failed or production_ready=false evidence")
    if payload.get("status") == "diagnostic-failed":
        artifact_paths = validate_evidence_artifacts(skill_root, payload, report)
        validate_diagnostic_evidence(skill_root, payload, artifact_paths, report)
        return
    for field in ("behavior_benchmark", "selection_benchmark"):
        value = payload.get(field)
        if not ((isinstance(value, str) and value.strip()) or (isinstance(value, dict) and value)):
            report.fail(f"production evidence {field} must be a non-empty path or object")
    runtime = payload.get("runtime")
    if not isinstance(runtime, dict):
        report.fail("production evidence runtime must be an object")
    else:
        if runtime.get("runner") != "scripts/run_production_evals.py":
            report.fail("production evidence runtime.runner must be scripts/run_production_evals.py")
        if not isinstance(runtime.get("command"), str) or not runtime["command"].strip():
            report.fail("production evidence runtime.command must be a non-empty string")
        if runtime.get("model") != EXECUTION_MODEL:
            report.fail(f"production evidence runtime.model must be {EXECUTION_MODEL!r}")
        if runtime.get("reasoning_effort") != EXECUTION_REASONING_EFFORT:
            report.fail(f"production evidence runtime.reasoning_effort must be {EXECUTION_REASONING_EFFORT!r}")

    artifact_paths = validate_evidence_artifacts(skill_root, payload, report)
    benchmark_payloads: dict[str, Any] = {}
    for field in ("behavior_benchmark", "selection_benchmark"):
        descriptor = payload.get(field)
        if not isinstance(descriptor, dict):
            continue
        benchmark_path = resolve_evidence_file(
            skill_root,
            descriptor.get("path"),
            descriptor.get("sha256"),
            f"production evidence {field}",
            report,
        )
        if descriptor.get("path") not in artifact_paths:
            report.fail(f"production evidence {field} must reference a top-level hashed artifact")
        if benchmark_path is not None:
            benchmark_payloads[field] = read_json(benchmark_path)
    behavior_scores: dict[tuple[int, str, int], float] = {}
    behavior = payload.get("behavior")
    if not isinstance(behavior, dict):
        report.fail("production evidence behavior must be an object")
    else:
        runs = behavior.get("runs")
        if not isinstance(runs, list) or len(runs) != len(PRODUCTION_BEHAVIOR_IDS) * 4:
            report.fail("production evidence behavior.runs must record exactly 40 current/without_skill base runs")
        elif isinstance(runs, list):
            behavior_scores = validate_behavior_run_records(
                skill_root,
                runs,
                report,
                str(payload.get("contract_sha256", "")),
            )
        summary = behavior.get("summary")
        if not isinstance(summary, dict):
            report.fail("production evidence behavior.summary must be an object")
            summary = {}
        elif set(summary) != {"current", "without_skill"}:
            report.fail("production evidence behavior.summary must contain current and without_skill only")
        for configuration in ("current", "without_skill"):
            result = summary.get(configuration)
            if not isinstance(result, dict):
                report.fail(f"production evidence behavior.summary.{configuration} must be an object")
                continue
            validate_rate(result.get("macro_pass_rate"), f"behavior.summary.{configuration}.macro_pass_rate", report,
                          0.90 if configuration == "current" else None)
            calculated_values = [
                value
                for (eval_id, run_configuration, _repetition), value in behavior_scores.items()
                if eval_id in PRODUCTION_BEHAVIOR_IDS and run_configuration == configuration
            ]
            calculated_macro = round(sum(calculated_values) / len(calculated_values), 4) if calculated_values else 0.0
            if result.get("macro_pass_rate") != calculated_macro:
                report.fail(f"behavior.summary.{configuration}.macro_pass_rate must be recalculated from grading artifacts")
            if not isinstance(result.get("hard_gates_passed"), bool):
                report.fail(f"behavior.summary.{configuration}.hard_gates_passed must be boolean")
            elif configuration == "current" and not result["hard_gates_passed"]:
                report.fail("current behavior hard gates must all pass")
            hard_gate_ids = {
                "existing-document-preservation": 11,
                "review-no-mutation": 20,
                "collision-no-overwrite": 21,
                "web-unavailable-no-hallucination": 25,
            }
            calculated_hard_gates = {
                name: bool(values := [
                    value
                    for (run_eval_id, run_configuration, _repetition), value in behavior_scores.items()
                    if run_eval_id == eval_id and run_configuration == configuration
                ]) and all(value == 1.0 for value in values)
                for name, eval_id in hard_gate_ids.items()
            }
            hard_gates = result.get("hard_gates")
            if hard_gates != calculated_hard_gates:
                report.fail(f"behavior.summary.{configuration}.hard_gates must be recalculated from grading artifacts")
            if result.get("hard_gates_passed") != all(calculated_hard_gates.values()):
                report.fail(f"behavior.summary.{configuration}.hard_gates_passed does not match hard-gate records")
            if configuration == "current" and any(value is not True for value in calculated_hard_gates.values()):
                report.fail("every current behavior hard gate must pass")
        behavior_artifact = benchmark_payloads.get("behavior_benchmark")
        if not isinstance(behavior_artifact, dict) or not isinstance(behavior_artifact.get("runs"), list):
            report.fail("behavior-results artifact must contain benchmark runs")
        elif isinstance(runs, list):
            artifact_run_list = [item for item in behavior_artifact["runs"] if isinstance(item, dict)]
            artifact_identities = [
                (item.get("eval_id"), item.get("configuration"), item.get("run_number"))
                for item in artifact_run_list
            ]
            if len(artifact_identities) != len(set(artifact_identities)):
                report.fail("behavior-results artifact contains duplicate run identities")
            artifact_runs = {
                (
                    item.get("eval_id"),
                    item.get("configuration"),
                    item.get("run_number"),
                ): item
                for item in artifact_run_list
            }
            expected_valid_artifact_ids = {
                (
                    run.get("eval_id"),
                    "with_skill" if run.get("configuration") == "current" else "without_skill",
                    run.get("repetition"),
                )
                for run in runs
                if isinstance(run, dict)
            }
            actual_valid_artifact_ids = {
                identity
                for identity, item in artifact_runs.items()
                if item.get("result", {}).get("valid") is True
            }
            if actual_valid_artifact_ids != expected_valid_artifact_ids:
                report.fail("behavior-results valid run identities must exactly match production evidence runs")
            for artifact_run in artifact_run_list:
                expectations = artifact_run.get("expectations")
                result = artifact_run.get("result")
                if not isinstance(expectations, list) or not isinstance(result, dict):
                    report.fail("behavior-results run is missing expectations or result")
                    continue
                passed = sum(item.get("passed") is True for item in expectations if isinstance(item, dict))
                total = len(expectations)
                if (
                    result.get("passed") != passed
                    or result.get("failed") != total - passed
                    or result.get("total") != total
                    or result.get("pass_rate") != (passed / total if total else 0.0)
                ):
                    report.fail("behavior-results run counters do not match expectations")
            for run in runs:
                if not isinstance(run, dict):
                    continue
                raw_configuration = "with_skill" if run.get("configuration") == "current" else "without_skill"
                artifact_run = artifact_runs.get((run.get("eval_id"), raw_configuration, run.get("repetition")))
                if not isinstance(artifact_run, dict) or artifact_run.get("result", {}).get("valid") is not True:
                    report.fail("every evidence behavior run must map to a valid behavior-results run")
                    continue
                if artifact_run.get("expectations") != run.get("grading", {}).get("expectations"):
                    report.fail("behavior-results expectations must match the hashed independent grading")
                if artifact_run.get("result", {}).get("pass_rate") != run.get("grading", {}).get("summary", {}).get("pass_rate"):
                    report.fail("behavior-results pass rate must match the independent grading summary")
            artifact_summary = behavior_artifact.get("run_summary")
            if not isinstance(artifact_summary, dict):
                report.fail("behavior-results artifact must contain run_summary")
            else:
                for raw_configuration, normalized_configuration in (("with_skill", "current"), ("without_skill", "without_skill")):
                    artifact_mean = artifact_summary.get(raw_configuration, {}).get("pass_rate", {}).get("mean")
                    evidence_mean = summary.get(normalized_configuration, {}).get("macro_pass_rate") if isinstance(summary, dict) else None
                    if artifact_mean != evidence_mean:
                        report.fail("behavior-results run_summary must match production evidence behavior summary")

    selection = payload.get("selection")
    calculated_selection: dict[str, dict[str, float | int]] = {}
    if not isinstance(selection, dict):
        report.fail("production evidence selection must be an object")
    else:
        runs = selection.get("runs")
        if not isinstance(runs, list) or len(runs) != SELECTION_CASE_COUNT * 3:
            report.fail("production evidence selection.runs must record exactly 180 current runs")
        elif isinstance(runs, list):
            batches = selection.get("batches")
            if not isinstance(batches, list):
                report.fail("production evidence selection.batches must be an array")
                batches = []
            calculated_selection = validate_selection_run_records(skill_root, batches, runs, report)
            selection_artifact = benchmark_payloads.get("selection_benchmark")
            if isinstance(selection_artifact, dict):
                normalized_artifact_runs = [
                    {
                        **item,
                        "configuration": {
                            "with_skill": "current",
                            "without_skill": "without_skill",
                        }.get(item.get("configuration"), item.get("configuration")),
                    }
                    for item in selection_artifact.get("runs", [])
                    if isinstance(item, dict)
                ]
                if normalized_artifact_runs != runs:
                    report.fail("production evidence selection.runs must match selection-results artifact")
        summary = selection.get("summary")
        if not isinstance(summary, dict):
            report.fail("production evidence selection.summary must be an object")
            summary = {}
        if set(summary) != {"current"}:
            report.fail("production evidence selection.summary must contain current only")
        for configuration in ("current",):
            result = summary.get(configuration)
            if not isinstance(result, dict):
                report.fail(f"production evidence selection.summary.{configuration} must be an object")
                continue
            for metric in ("precision", "recall", "specificity"):
                validate_rate(
                    result.get(metric),
                    f"selection.summary.{configuration}.{metric}",
                    report,
                    0.95 if configuration == "current" else None,
                )
                if result.get(metric) != calculated_selection.get(configuration, {}).get(metric):
                    report.fail(f"selection.summary.{configuration}.{metric} must be recalculated from selection runs")
            high_risk_false_positives = result.get("high_risk_false_positives")
            if not isinstance(high_risk_false_positives, int) or high_risk_false_positives < 0:
                report.fail(
                    f"selection.summary.{configuration}.high_risk_false_positives must be a non-negative integer"
                )
            elif configuration == "current" and high_risk_false_positives != 0:
                report.fail("current selection high-risk false positives must be 0")
            if high_risk_false_positives != calculated_selection.get(configuration, {}).get("high_risk_false_positives"):
                report.fail(f"selection.summary.{configuration}.high_risk_false_positives must be recalculated from selection runs")
        selection_artifact = benchmark_payloads.get("selection_benchmark")
        if isinstance(selection_artifact, dict):
            artifact_summary = selection_artifact.get("summary")
            expected_artifact_summary = {"current": summary.get("current", {}) if isinstance(summary, dict) else {}}
            if artifact_summary != expected_artifact_summary:
                report.fail("selection-results summary must match production evidence selection summary")

    blind = payload.get("blind_comparison")
    behavior_output_hashes = {
        (run.get("eval_id"), run.get("configuration"), run.get("repetition")): run.get("review_output_sha256")
        for run in behavior.get("runs", [])
        if isinstance(behavior, dict) and isinstance(run, dict)
    } if isinstance(behavior, dict) else {}
    if not isinstance(blind, dict):
        report.fail("production evidence blind_comparison must be an object")
    else:
        blind_descriptor = next(
            (item for item in payload.get("artifacts", []) if isinstance(item, dict) and item.get("kind") == "blind-comparison"),
            None,
        )
        if isinstance(blind_descriptor, dict):
            blind_artifact_path = resolve_evidence_file(
                skill_root,
                blind_descriptor.get("path"),
                blind_descriptor.get("sha256"),
                "blind comparison artifact",
                report,
            )
            if blind_artifact_path is not None and read_json(blind_artifact_path) != blind:
                report.fail("blind comparison summary must equal its hashed artifact")
        pairs = blind.get("pairs")
        pair_records: set[tuple[int, int]] = set()
        current_wins = 0
        without_skill_wins = 0
        ties = 0
        if not isinstance(pairs, list) or not pairs:
            report.fail("blind_comparison.pairs must be a non-empty array")
            pairs = []
        seen_blind_reasoning: set[str] = set()
        for index, pair in enumerate(pairs):
            label = f"blind_comparison.pairs[{index}]"
            if not isinstance(pair, dict):
                report.fail(f"{label} must be an object")
                continue
            eval_id = pair.get("eval_id")
            repetition = pair.get("repetition")
            winner = pair.get("winner")
            identity = (eval_id, repetition)
            if (
                not isinstance(eval_id, int)
                or eval_id not in PRODUCTION_BEHAVIOR_IDS
                or repetition not in {1, 2}
                or winner not in {"current", "without_skill", "tie"}
                or identity in pair_records
            ):
                report.fail(f"{label} has an invalid or duplicate eval/repetition/winner")
                continue
            pair_records.add(identity)
            if winner == "current":
                current_wins += 1
            elif winner == "without_skill":
                without_skill_wins += 1
            else:
                ties += 1
            for field in ("output_a_sha256", "output_b_sha256"):
                if not is_sha256(pair.get(field)):
                    report.fail(f"{label}.{field} must be a lowercase SHA-256 digest")
            for field in (
                "forward_input_a_sha256", "forward_input_b_sha256",
                "reversed_input_a_sha256", "reversed_input_b_sha256",
            ):
                if not is_sha256(pair.get(field)):
                    report.fail(f"{label}.{field} must be a lowercase SHA-256 digest")
            if (
                pair.get("reversed_input_a_sha256") != pair.get("forward_input_b_sha256")
                or pair.get("reversed_input_b_sha256") != pair.get("forward_input_a_sha256")
            ):
                report.fail(f"{label} reversed comparator inputs must swap forward A and B")
            input_manifests = pair.get("input_manifests")
            validated_input_manifests: dict[tuple[str, str], dict[str, Any]] = {}
            if not isinstance(input_manifests, dict):
                report.fail(f"{label}.input_manifests must publish forward and reversed comparator inputs")
            else:
                for orientation in ("forward", "reversed"):
                    orientation_payload = input_manifests.get(orientation)
                    if not isinstance(orientation_payload, dict):
                        report.fail(f"{label}.input_manifests.{orientation} must be an object")
                        continue
                    for side in ("A", "B"):
                        manifest_payload = orientation_payload.get(side)
                        manifest_label = f"{label}.input_manifests.{orientation}.{side}"
                        if not isinstance(manifest_payload, dict):
                            report.fail(f"{manifest_label} must be an object")
                            continue
                        files = validated_manifest_files(manifest_payload, manifest_label, report)
                        tree_hash = validated_manifest_tree_hash(manifest_payload, files, manifest_label, report)
                        expected_hash = pair.get(f"{orientation}_input_{side.lower()}_sha256")
                        if tree_hash != expected_hash or manifest_payload.get("sha256") != expected_hash:
                            report.fail(f"{manifest_label} does not match its comparator input hash")
                        validated_input_manifests[(orientation, side)] = manifest_payload
                if (
                    validated_input_manifests.get(("reversed", "A"), {}).get("entries")
                    != validated_input_manifests.get(("forward", "B"), {}).get("entries")
                    or validated_input_manifests.get(("reversed", "B"), {}).get("entries")
                    != validated_input_manifests.get(("forward", "A"), {}).get("entries")
                ):
                    report.fail(f"{label} reversed comparator manifests must swap forward A and B")
                for side in ("A", "B"):
                    forward_manifest = validated_input_manifests.get(("forward", side))
                    if not isinstance(forward_manifest, dict):
                        continue
                    stripped_entries = [
                        entry
                        for entry in forward_manifest.get("entries", [])
                        if isinstance(entry, dict) and entry.get("path") != "grading-summary.json"
                    ]
                    stripped_hash = hashlib.sha256(
                        json.dumps(
                            sorted(stripped_entries, key=lambda item: item["path"]),
                            ensure_ascii=False,
                            separators=(",", ":"),
                        ).encode("utf-8")
                    ).hexdigest()
                    if stripped_hash != pair.get(f"output_{side.lower()}_sha256"):
                        report.fail(f"{label} comparator input {side} is not derived from its behavior output plus grading summary")
            forward_context_id = pair.get("forward_context_id")
            reversed_context_id = pair.get("reversed_context_id")
            if (
                not isinstance(forward_context_id, str)
                or not forward_context_id.strip()
                or not isinstance(reversed_context_id, str)
                or not reversed_context_id.strip()
                or forward_context_id == reversed_context_id
            ):
                report.fail(f"{label} must bind two distinct comparator context IDs")
            current_side = pair.get("current_side")
            mapping_nonce = pair.get("mapping_nonce")
            expected_commitment = hashlib.sha256(
                f"{eval_id}:{repetition}:{current_side}:{mapping_nonce}".encode("utf-8")
            ).hexdigest()
            if current_side not in {"A", "B"} or not isinstance(mapping_nonce, str) or pair.get("mapping_commitment") != expected_commitment:
                report.fail(f"{label} has an invalid blind mapping commitment")
            current_hash = behavior_output_hashes.get((eval_id, "current", repetition))
            without_skill_hash = behavior_output_hashes.get((eval_id, "without_skill", repetition))
            if current_side == "A":
                mapping_matches = pair.get("output_a_sha256") == current_hash and pair.get("output_b_sha256") == without_skill_hash
            else:
                mapping_matches = pair.get("output_b_sha256") == current_hash and pair.get("output_a_sha256") == without_skill_hash
            if not mapping_matches:
                report.fail(f"{label} A/B hashes do not match the committed current/without_skill mapping")
            if pair.get("output_a_sha256") == pair.get("output_b_sha256") and winner != "tie":
                report.fail(f"{label} must be a tie when A and B outputs are byte-identical")
            reasoning = pair.get("reasoning")
            if not isinstance(reasoning, dict) or not all(isinstance(reasoning.get(side), str) and len(reasoning[side].strip()) >= 20 for side in ("forward", "reversed")):
                report.fail(f"{label}.reasoning must contain concrete forward and reversed explanations")
            elif any(
                re.sub(r"\s+", " ", reasoning[side].strip().lower()) in {"a is better", "b is better", "tie", "no difference", "comparable"}
                or re.sub(r"\s+", " ", reasoning[side].strip().lower()) in seen_blind_reasoning
                for side in ("forward", "reversed")
            ) or re.sub(r"\s+", " ", reasoning["forward"].strip().lower()) == re.sub(r"\s+", " ", reasoning["reversed"].strip().lower()):
                report.fail(f"{label}.reasoning must be concrete and unique for both comparison directions")
            elif isinstance(reasoning, dict):
                seen_blind_reasoning.update(re.sub(r"\s+", " ", reasoning[side].strip().lower()) for side in ("forward", "reversed"))
            raw_comparison = pair.get("raw_comparison")
            raw_winner = pair.get("raw_winner")
            if not isinstance(raw_comparison, dict) or raw_winner not in {"A", "B", "TIE"}:
                report.fail(f"{label}.raw_comparison must contain forward and reversed blind verdicts")
            else:
                raw_hash = hashlib.sha256(
                    json.dumps(raw_comparison, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
                ).hexdigest()
                if pair.get("raw_comparison_sha256") != raw_hash:
                    report.fail(f"{label}.raw_comparison_sha256 does not match the embedded verdict")
                forward = raw_comparison.get("forward")
                reversed_verdict = raw_comparison.get("reversed")
                if not isinstance(forward, dict) or not isinstance(reversed_verdict, dict):
                    report.fail(f"{label}.raw_comparison must include both verdict objects")
                    continue
                verdict_winners = []
                for verdict_name, verdict in (("forward", forward), ("reversed", reversed_verdict)):
                    verdict_winner = str(verdict.get("winner", "")).upper()
                    if verdict_winner not in {"A", "B", "TIE"}:
                        report.fail(f"{label}.raw_comparison.{verdict_name}.winner is invalid")
                    verdict_winners.append(verdict_winner)
                    verdict_reasoning = verdict.get("reasoning")
                    if not isinstance(verdict_reasoning, str) or len(verdict_reasoning.strip()) < 20 or verdict_reasoning.strip().lower() in {"a is better", "b is better", "tie", "no difference", "comparable"}:
                        report.fail(f"{label}.raw_comparison.{verdict_name}.reasoning is missing or generic")
                    references = verdict.get("evidence_references", verdict.get("evidence_refs", verdict.get("evidence")))
                    if not isinstance(references, list) or len([item for item in references if isinstance(item, str) and item.strip()]) < 2:
                        report.fail(f"{label}.raw_comparison.{verdict_name} needs concrete evidence references")
                    if not verdict.get("rubric") or not verdict.get("expectation_details", verdict.get("expectation_detail")):
                        report.fail(f"{label}.raw_comparison.{verdict_name} is missing rubric or expectation detail")
                    if not blind_verdict_has_concrete_evidence(verdict):
                        report.fail(f"{label}.raw_comparison.{verdict_name} lacks concrete evidence")
                    expected_input_a = pair.get(f"{verdict_name}_input_a_sha256")
                    expected_input_b = pair.get(f"{verdict_name}_input_b_sha256")
                    expected_context_id = pair.get(f"{verdict_name}_context_id")
                    if (
                        verdict.get("orientation") != verdict_name
                        or verdict.get("context_id") != expected_context_id
                        or verdict.get("input_a_sha256") != expected_input_a
                        or verdict.get("input_b_sha256") != expected_input_b
                    ):
                        report.fail(f"{label}.raw_comparison.{verdict_name} is not bound to its comparator input")
                if len(verdict_winners) == 2:
                    expected_raw_winner = resolved_blind_winner(verdict_winners[0], verdict_winners[1])
                    if raw_winner != expected_raw_winner:
                        report.fail(f"{label}.raw_winner must become TIE when forward and reversed verdicts disagree")
                translated_winner = "tie" if raw_winner == "TIE" else ("current" if raw_winner == current_side else "without_skill")
                if winner != translated_winner:
                    report.fail(f"{label}.winner does not match the committed blind mapping and raw verdict")
        expected_pairs = {
            (eval_id, repetition)
            for eval_id in PRODUCTION_BEHAVIOR_IDS
            for repetition in {run_repetition for (run_eval_id, configuration, run_repetition) in behavior_scores if run_eval_id == eval_id and configuration == "current"}
            if (eval_id, "without_skill", repetition) in behavior_scores
        }
        if pair_records != expected_pairs:
            report.fail("blind comparison must contain one pair for every paired behavior run")
        credited_current_wins = current_wins + ties
        calculated_win_rate = credited_current_wins / 20 if pair_records else 0.0
        validate_rate(blind.get("current_win_rate"), "blind_comparison.current_win_rate", report, 0.95)
        if blind.get("tie_policy") != "credit-current":
            report.fail("blind_comparison.tie_policy must be credit-current")
        if not blind_gate_passes(
            blind.get("total_pairs"), current_wins, ties,
            blind.get("credited_current_wins"), blind.get("current_win_rate")
        ):
            report.fail("blind comparison must contain exactly 20 pairs and at least 19 credited current wins")
        for field in ("current_wins", "without_skill_wins", "ties", "credited_current_wins"):
            if not isinstance(blind.get(field), int) or isinstance(blind.get(field), bool) or blind[field] < 0:
                report.fail(f"blind_comparison.{field} must be a non-negative integer")
        if (
            blind.get("current_wins") != current_wins
            or blind.get("without_skill_wins") != without_skill_wins
            or blind.get("ties") != ties
            or blind.get("credited_current_wins") != credited_current_wins
            or blind.get("current_win_rate") != calculated_win_rate
        ):
            report.fail("blind comparison summary must be recalculated from pair records")
    review = payload.get("review")
    if not isinstance(review, dict):
        report.fail("production evidence review must be an object")
    else:
        if review.get("status") != "generated":
            report.fail("production evidence review.status must be generated")
        if not isinstance(review.get("reason"), str) or not review["reason"].strip():
            report.fail("production evidence review.reason must be a non-empty string")
        review_path = resolve_evidence_file(
            skill_root,
            review.get("artifact_path"),
            review.get("sha256"),
            "production evidence review artifact",
            report,
        )
        if review_path is not None and review_path.stat().st_size < 1024:
            report.fail("production evidence review HTML is unexpectedly small")
        elif review_path is not None:
            review_text = read_text(review_path).lower()
            if (
                "document-writing" not in review_text
                or "eval review:" not in review_text
                or 'id="panel-benchmark"' not in review_text
                or 'id="outputs-body"' not in review_text
            ):
                report.fail("production evidence review HTML does not contain the skill benchmark")
            eval_manifest = read_json(skill_root / "evals/evals.json")
            required_eval_names = {
                str(item.get("eval_name", f"eval-{item.get('id')}")).lower()
                for item in eval_manifest.get("evals", [])
                if isinstance(item, dict) and item.get("id") in PRODUCTION_BEHAVIOR_IDS
            }
            if any(name not in review_text for name in required_eval_names):
                report.fail("production evidence review HTML does not contain every production behavior eval")

    image_canary = payload.get("image_canary")
    if not isinstance(image_canary, dict):
        report.fail("production evidence image_canary must be an object")
    else:
        if image_canary.get("passed") is not True:
            report.fail("production evidence image_canary.passed must be true")
        if image_canary.get("eval_id") != 24:
            report.fail("production evidence image canary must be linked to eval 24")
        if image_canary.get("artifact_name") != "orbit-notes-feature-graphic-1024x500.png":
            report.fail("production evidence image canary artifact_name does not match the suite")
        artifact_path = image_canary.get("artifact_path")
        if artifact_path not in artifact_paths:
            report.fail("image canary artifact_path must reference a hashed evidence artifact")
        if not is_sha256(image_canary.get("sha256")):
            report.fail("image canary sha256 must be a lowercase SHA-256 digest")
        elif isinstance(artifact_path, str) and artifact_path in artifact_paths:
            actual_path = skill_root / artifact_path
            if actual_path.is_file() and hashlib.sha256(actual_path.read_bytes()).hexdigest() != image_canary["sha256"]:
                report.fail("image canary sha256 does not match its artifact")
        if image_canary.get("image_tool_calls") != 1:
            report.fail("image canary image_tool_calls must be exactly 1")
        if image_canary.get("generation_tool") != "image_gen":
            report.fail("image canary generation_tool must be image_gen")
        for field in ("generation_prompt_sha256", "generated_source_sha256"):
            if not is_sha256(image_canary.get(field)):
                report.fail(f"image canary {field} must be a lowercase SHA-256 digest")
        source_artifact_path = image_canary.get("generated_source_artifact_path")
        if source_artifact_path not in artifact_paths:
            report.fail("image canary generated source must reference a hashed evidence artifact")
        source_image_path = resolve_evidence_file(
            skill_root,
            source_artifact_path,
            image_canary.get("generated_source_artifact_sha256"),
            "image canary generated source artifact",
            report,
        )
        if source_image_path is not None:
            if image_canary.get("generated_source_sha256") != hashlib.sha256(source_image_path.read_bytes()).hexdigest():
                report.fail("image canary generated source hash does not match its source artifact")
            if inspect_png(source_image_path) is None:
                report.fail("image canary generated source must be a complete PNG")
        generation_artifact_path = image_canary.get("generation_artifact_path")
        if generation_artifact_path not in artifact_paths:
            report.fail("image canary generation_artifact_path must reference a hashed evidence artifact")
        generation_bundle_path = resolve_evidence_file(
            skill_root,
            generation_artifact_path,
            image_canary.get("generation_artifact_sha256"),
            "image canary generation artifact",
            report,
        )
        if generation_bundle_path is not None:
            generation = read_json(generation_bundle_path)
            generation_prompt = generation.get("prompt")
            if not isinstance(generation_prompt, str) or hashlib.sha256(generation_prompt.encode("utf-8")).hexdigest() != image_canary.get("generation_prompt_sha256"):
                report.fail("image canary generation prompt does not match its hash")
            expected_generation = {
                "eval_id": 24,
                "tool": "image_gen",
                "tool_calls": 1,
                "prompt": generation_prompt,
                "prompt_sha256": image_canary.get("generation_prompt_sha256"),
                "generated_source_sha256": image_canary.get("generated_source_sha256"),
                "final_artifact_sha256": image_canary.get("sha256"),
                "artifact_name": image_canary.get("artifact_name"),
            }
            if generation != expected_generation:
                report.fail("image canary generation artifact does not match the bound tool and image evidence")
        if isinstance(artifact_path, str) and artifact_path in artifact_paths:
            inspected = inspect_png(skill_root / artifact_path)
            if inspected is None:
                report.fail("image canary artifact must be a complete, decodable PNG")
            else:
                width, height, has_alpha = inspected
                if (width, height, has_alpha) != (1024, 500, False):
                    report.fail("image canary PNG must be 1024x500 without alpha")
                if image_canary.get("width") != width or image_canary.get("height") != height:
                    report.fail("image canary dimensions must match the PNG")
        document_artifact_path = image_canary.get("document_artifact_path")
        if document_artifact_path not in artifact_paths:
            report.fail("image canary document_artifact_path must reference a hashed evidence artifact")
        document_bundle_path = resolve_evidence_file(
            skill_root,
            document_artifact_path,
            image_canary.get("document_artifact_sha256"),
            "image canary document artifact",
            report,
        )
        if document_bundle_path is not None:
            document_bundle = read_json(document_bundle_path)
            if document_bundle.get("document_root") != "docs/marketing/google-play":
                report.fail("image canary document artifact must own docs/marketing/google-play")
            files = document_bundle.get("files")
            if not isinstance(files, list):
                report.fail("image canary document artifact files must be an array")
                files = []
            paths = {item.get("path") for item in files if isinstance(item, dict)}
            if not {"index.md", "stores/google-play.md"}.issubset(paths):
                report.fail("image canary document artifact must include index.md and stores/google-play.md")
            for index, item in enumerate(files):
                if not isinstance(item, dict) or not isinstance(item.get("content"), str) or not is_sha256(item.get("sha256")):
                    report.fail(f"image canary document files[{index}] is incomplete")
                    continue
                if hashlib.sha256(item["content"].encode("utf-8")).hexdigest() != item["sha256"]:
                    report.fail(f"image canary document files[{index}] hash does not match content")
            source_urls = document_bundle.get("source_urls")
            if not isinstance(source_urls, list) or not any(
                isinstance(value, str)
                and value.startswith(("https://support.google.com/googleplay/", "https://developer.android.com/"))
                for value in source_urls
            ):
                report.fail("image canary document artifact must record an opened first-party Google source")
            response = document_bundle.get("assistant_response")
            if not isinstance(response, str) or "생성하지" not in response:
                report.fail("image canary document response must state that document-writing did not generate the image")
    limitations = payload.get("limitations")
    if not isinstance(limitations, list) or not limitations:
        report.fail("production evidence must state remaining limitations")
    if not report.failures:
        report.ok("production evidence matches the current schema-v2 benchmark contract")


def normalize_link_target(raw_target: str) -> str:
    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    return unquote(target.split("#", 1)[0])


def validate_markdown_links(skill_root: Path, report: Report) -> None:
    checked = 0
    for markdown_file in sorted(skill_root.rglob("*.md")):
        if "evals" in markdown_file.parts and "fixtures" in markdown_file.parts:
            continue
        if "feature-design-doc" in markdown_file.parts:
            continue
        content = FENCE_RE.sub("", read_text(markdown_file))
        for match in LINK_RE.finditer(content):
            raw_target = match.group("target").strip()
            parsed = urlparse(raw_target)
            if parsed.scheme or raw_target.startswith("#"):
                continue
            target = normalize_link_target(raw_target)
            if not target:
                continue
            checked += 1
            resolved = (markdown_file.parent / target).resolve()
            if not is_within(skill_root, resolved):
                report.fail(
                    f"relative link escapes skill root: {markdown_file.relative_to(skill_root)} -> {raw_target}"
                )
            elif not resolved.exists():
                report.fail(
                    f"broken relative link: {markdown_file.relative_to(skill_root)} -> {raw_target}"
                )

    if not report.failures:
        report.ok(f"{checked} relative Markdown links resolve within the skill package")


def validate_repository_metadata(
    skill_root: Path, report: Report, expected_version: str | None
) -> None:
    repo_root = skill_root.parent.parent
    package_path = repo_root / "package.json"
    marketplace_path = repo_root / ".claude-plugin/marketplace.json"
    readme_path = repo_root / "README.md"
    for path in (package_path, marketplace_path, readme_path):
        if not path.is_file():
            report.fail(f"repository metadata file is missing: {path.relative_to(repo_root)}")
            return

    package = read_json(package_path)
    marketplace = read_json(marketplace_path)
    package_version = package.get("version") if isinstance(package, dict) else None
    marketplace_version = None
    if isinstance(marketplace, dict) and isinstance(marketplace.get("metadata"), dict):
        marketplace_version = marketplace["metadata"].get("version")
    if not isinstance(package_version, str) or package_version != marketplace_version:
        report.fail(
            "package.json version and marketplace metadata.version must match"
        )
    elif not SEMVER_RE.fullmatch(package_version):
        report.fail(f"repository version is not valid SemVer: {package_version!r}")
    if expected_version is not None and package_version != expected_version:
        report.fail(
            f"release version {expected_version!r} does not match package.json version {package_version!r}"
        )

    skill_entries: list[str] = []
    if isinstance(marketplace, dict) and isinstance(marketplace.get("plugins"), list):
        for plugin in marketplace["plugins"]:
            if not isinstance(plugin, dict) or not isinstance(plugin.get("skills"), list):
                continue
            skill_entries.extend(
                item for item in plugin["skills"] if isinstance(item, str)
            )
    if skill_entries.count("./skills/document-writing") != 1:
        report.fail(
            "marketplace must contain ./skills/document-writing exactly once"
        )

    readme = read_text(readme_path)
    if "[document-writing](skills/document-writing/)" not in readme:
        report.fail("README available-skills table must link document-writing")

    if not report.failures:
        report.ok(
            "repository version, marketplace membership, and README exposure are aligned"
        )


def validate_package(
    skill_root: Path,
    expected_version: str | None = None,
    require_production_ready: bool = False,
) -> Report:
    report = Report()
    validate_required_files(skill_root, report)
    if report.failures:
        return report
    validate_frontmatter(skill_root, report)
    validate_eval_manifest(skill_root, report)
    validate_trigger_manifest(skill_root, report)
    validate_selection_manifest(skill_root, report)
    validate_production_suite(skill_root, report)
    validate_node_validators(skill_root, report)
    validate_python_eval_scripts(skill_root, report)
    validate_markdown_links(skill_root, report)
    validate_repository_metadata(skill_root, report, expected_version)
    validate_production_evidence(skill_root, report, require_production_ready)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the document-writing skill package structure."
    )
    parser.add_argument(
        "skill_root",
        nargs="?",
        default=str(Path(__file__).resolve().parents[1]),
        help="Path to the document-writing skill root.",
    )
    parser.add_argument(
        "--format", choices=("text", "json"), default="text"
    )
    parser.add_argument(
        "--expected-version",
        help="Require package and marketplace versions to match this release version.",
    )
    parser.add_argument(
        "--print-contract-digest",
        action="store_true",
        help="Print the current production-evidence digest and exit.",
    )
    parser.add_argument(
        "--require-production-ready",
        action="store_true",
        help="Reject diagnostic-failed or production_ready=false evidence.",
    )
    args = parser.parse_args()

    skill_root = Path(args.skill_root).resolve()
    if not skill_root.is_dir():
        print(f"error: skill root is not a directory: {skill_root}", file=sys.stderr)
        return EXIT_USAGE

    if args.print_contract_digest:
        print(contract_digest(skill_root))
        return EXIT_OK

    try:
        report = validate_package(
            skill_root,
            args.expected_version,
            args.require_production_ready,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_USAGE

    print(report.as_json() if args.format == "json" else report.as_text())
    return EXIT_VALIDATION if report.failures else EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
