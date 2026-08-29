#!/usr/bin/env python3
"""Validate the document-writing skill package and schema-v3 evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import struct
import subprocess
import sys
import zlib
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import unquote, urlparse


EXIT_OK = 0
EXIT_VALIDATION = 1
EXIT_USAGE = 2
FRONTMATTER_RE = re.compile(r"\A---\n(?P<body>.*?)\n---(?:\n|\Z)", re.DOTALL)
LINK_RE = re.compile(r"\[[^\]]*\]\((?P<target>[^)]+)\)")
FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
PRODUCTION_BEHAVIOR_IDS = tuple(range(1, 33))
SELECTION_CASE_COUNT = 60
EXECUTION_MODEL = "gpt-5.6-luna"
EXECUTION_REASONING_EFFORT = "medium"
HARD_GATE_NAMES = {
    "direction-approval-no-premature-write",
    "existing-document-preservation",
    "review-no-mutation",
    "collision-no-overwrite",
    "web-unavailable-no-hallucination",
    "qualitative-feedback-translation",
    "cross-context-consistency-not-sameness",
    "focused-update-propagation",
    "contradictory-preference-convergence",
}
REQUIRED_PACKAGE_FILES = (
    "SKILL.md",
    "evals/evals.json",
    "evals/trigger-evals.json",
    "evals/design-system-selection-evals.json",
    "evals/production-suite.json",
    "evals/production-evidence.json",
    "evals/README.md",
    "evals/validators/validate_existing_update.mjs",
    "evals/validators/validate_preservation.mjs",
    "evals/validators/validate_noncanonical_store.mjs",
    "evals/validators/validate_warning_update.mjs",
    "scripts/run_production_evals.py",
    "scripts/validate_fdd.py",
    "scripts/validate_eval_run.py",
    "scripts/validate_design_system_output.py",
    "scripts/test_eval_validators.py",
    "references/document-types/design-system/design-system-overview.md",
    "references/document-types/design-system/design-direction-workflow.md",
    "references/document-types/design-system/design-system-authoring.md",
    "references/document-types/design-system/design-system-review.md",
    "references/document-types/design-system/prebuilts/default.md",
    "references/document-types/design-system/prebuilts/app-store-page.md",
)
NODE_VALIDATORS = (
    "evals/validators/validate_existing_update.mjs",
    "evals/validators/validate_preservation.mjs",
    "evals/validators/validate_noncanonical_store.mjs",
    "evals/validators/validate_warning_update.mjs",
)
PYTHON_EVAL_SCRIPTS = (
    "scripts/run_production_evals.py",
    "scripts/validate_fdd.py",
    "scripts/validate_eval_run.py",
    "scripts/validate_design_system_output.py",
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
        return json.dumps({"passed": not self.failures, "checks": self.passes, "failures": self.failures}, ensure_ascii=False, indent=2)

    def as_text(self) -> str:
        lines = [*(f"PASS: {item}" for item in self.passes), *(f"FAIL: {item}" for item in self.failures)]
        return "\n".join(lines)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> Any:
    try:
        return json.loads(read_text(path))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read valid JSON from {path}: {exc}") from exc


def is_within(root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def is_sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def validate_required_files(skill_root: Path, report: Report) -> None:
    missing = [relative for relative in REQUIRED_PACKAGE_FILES if not (skill_root / relative).is_file()]
    if missing:
        report.fail(f"required package files are missing: {missing}")
    else:
        report.ok(f"all {len(REQUIRED_PACKAGE_FILES)} required package files exist")


def validate_frontmatter(skill_root: Path, report: Report) -> None:
    match = FRONTMATTER_RE.match(read_text(skill_root / "SKILL.md"))
    if not match:
        report.fail("SKILL.md must start with YAML frontmatter")
        return
    body = match.group("body")
    name = re.search(r"(?m)^name:\s*(.+)$", body)
    description = re.search(r"(?m)^description:\s*(.+)$", body)
    if name is None or name.group(1).strip() != "document-writing":
        report.fail("SKILL.md frontmatter name must be document-writing")
    if description is None or len(description.group(1).strip()) < 100:
        report.fail("SKILL.md frontmatter description must be a substantive scalar")
    if not report.failures:
        report.ok("SKILL.md frontmatter is valid")


def validate_eval_manifest(skill_root: Path, report: Report) -> None:
    payload = read_json(skill_root / "evals/evals.json")
    if not isinstance(payload, dict) or payload.get("skill_name") != "document-writing" or not isinstance(payload.get("evals"), list):
        report.fail("evals.json must contain the document-writing eval list")
        return
    evals = payload["evals"]
    ids = [item.get("id") for item in evals if isinstance(item, dict)]
    if ids != list(PRODUCTION_BEHAVIOR_IDS):
        report.fail("evals.json must contain eval 1 through 32 in order")
    for index, item in enumerate(evals):
        if not isinstance(item, dict):
            report.fail(f"evals[{index}] must be an object")
            continue
        if not isinstance(item.get("prompt"), str) or not item["prompt"].strip():
            report.fail(f"eval {item.get('id')} needs a prompt")
        expectations = item.get("expectations")
        if not isinstance(expectations, list) or not expectations or not all(isinstance(value, str) and value.strip() for value in expectations):
            report.fail(f"eval {item.get('id')} needs semantic expectations")
        files = item.get("files", [])
        if not isinstance(files, list) or not all(isinstance(value, str) for value in files):
            report.fail(f"eval {item.get('id')} files must be an array")
        else:
            for relative in files:
                if not (skill_root / relative).is_file():
                    report.fail(f"eval {item.get('id')} fixture is missing: {relative}")
    if not report.failures:
        report.ok("32 behavior evals have prompts, expectations, and fixtures")


def validate_trigger_manifest(skill_root: Path, report: Report) -> None:
    payload = read_json(skill_root / "evals/trigger-evals.json")
    if not isinstance(payload, list) or not payload:
        report.fail("trigger-evals.json must contain a non-empty case array")
        return
    if any(not isinstance(item, dict) or not isinstance(item.get("query"), str) or not isinstance(item.get("should_trigger"), bool) for item in payload):
        report.fail("trigger eval cases must contain query and should_trigger")
    elif len({item["query"] for item in payload}) != len(payload):
        report.fail("trigger eval queries must be unique")
    elif not any(item["should_trigger"] for item in payload) or not any(not item["should_trigger"] for item in payload):
        report.fail("trigger evals must contain positive and negative cases")
    else:
        report.ok(f"{len(payload)} trigger evals have complete balanced-direction labels")


def validate_selection_manifest(skill_root: Path, report: Report) -> None:
    payload = read_json(skill_root / "evals/design-system-selection-evals.json")
    if not isinstance(payload, list) or len(payload) != SELECTION_CASE_COUNT:
        report.fail("selection dataset must contain exactly 60 cases")
        return
    labels = [item.get("should_trigger") for item in payload if isinstance(item, dict)]
    if labels.count(True) != 30 or labels.count(False) != 30:
        report.fail("selection dataset must have 30 positive and 30 negative cases")
    elif any(not isinstance(item.get("id"), int) or not isinstance(item.get("query"), str) for item in payload):
        report.fail("selection cases must contain integer id and query")
    else:
        report.ok("selection dataset is balanced and complete")


def validate_production_suite(skill_root: Path, report: Report) -> None:
    payload = read_json(skill_root / "evals/production-suite.json")
    if not isinstance(payload, dict) or payload.get("schema_version") != 3:
        report.fail("production suite must use schema_version 3")
        return
    if payload.get("skill_name") != "document-writing" or payload.get("workspace") != "../document-writing-workspace":
        report.fail("production suite identity or workspace is invalid")
    if "cases" in payload:
        report.fail("schema-v3 suite must keep contracts under behavior.case_contracts only")
    behavior = payload.get("behavior")
    if not isinstance(behavior, dict):
        report.fail("production suite behavior must be an object")
        return
    if behavior.get("eval_ids") != list(PRODUCTION_BEHAVIOR_IDS) or behavior.get("repetitions") != 1:
        report.fail("behavior must cover eval 1 through 32 once")
    if behavior.get("configurations") != [{"name": "with_skill", "source": "working-tree", "capability_overrides": {}}]:
        report.fail("behavior must contain only the current working-tree configuration")
    contracts = behavior.get("case_contracts")
    if not isinstance(contracts, dict) or set(contracts) != {str(value) for value in PRODUCTION_BEHAVIOR_IDS}:
        report.fail("case_contracts must cover eval 1 through 32 exactly")
        contracts = {}
    no_write_ids = {1, 2, 4, 5, 6, 7, 8, 9, 10, 12, 20, 21, 25, 26, 29, 32}
    for eval_id in no_write_ids:
        contract = contracts.get(str(eval_id), {})
        if contract.get("deny_write_tools") is not True or contract.get("allowed_change_paths") != []:
            report.fail(f"eval {eval_id} must be a no-write case")
    if contracts.get("3", {}).get("validation") != "validate_fdd.py --strict":
        report.fail("eval 3 must use strict FDD validation")
    for eval_id in (14, 15, 16, 17, 18, 19, 22, 23, 24):
        source = contracts.get(str(eval_id), {}).get("source_evidence", {})
        if source.get("require_https_url") is not True or source.get("require_verification_date") is not True:
            report.fail(f"eval {eval_id} must require observable source evidence")
    expected_png = {"root": "docs/marketing/google-play", "glob": "*.png", "count": 1, "width": 1024, "height": 500, "has_alpha": False}
    if contracts.get("24", {}).get("png") != expected_png:
        report.fail("eval 24 PNG contract must be filename-independent and exact on binary properties")
    document_validation = contracts.get("24", {}).get("document_validation", {})
    if document_validation.get("root") != "docs/marketing/google-play" or document_validation.get("prebuilt") != "app-store-page" or document_validation.get("stores") != ["google-play"]:
        report.fail("eval 24 must require index.md and the Google Play store owner")
    image_canary = payload.get("image_canary")
    expected_image = {"eval_id": 24, "document_root": "docs/marketing/google-play", "artifact_glob": "*.png", "count": 1, "width": 1024, "height": 500, "has_alpha": False, "required_capabilities": ["web", "image-generation"]}
    if image_canary != expected_image:
        report.fail("image_canary must match the filename-independent eval 24 contract")
    selection = payload.get("selection")
    if not isinstance(selection, dict) or selection.get("mode") != "reuse-only" or selection.get("dataset") != "evals/design-system-selection-evals.json":
        report.fail("selection must be reuse-only")
    elif any(not is_sha256(selection.get(field)) for field in ("evidence_sha256", "description_sha256", "dataset_sha256")):
        report.fail("selection reuse hashes must be SHA-256 digests")
    runtime = payload.get("runtime")
    if not isinstance(runtime, dict) or runtime.get("model") != EXECUTION_MODEL or runtime.get("reasoning_effort") != EXECUTION_REASONING_EFFORT or runtime.get("execution_contexts") != 32 or runtime.get("grading_contexts") != 32:
        report.fail("runtime must declare the full 32+32 Luna-medium production budget")
    evidence = payload.get("evidence")
    gates = evidence.get("gates") if isinstance(evidence, dict) else None
    if not isinstance(evidence, dict) or evidence.get("schema_version") != 3 or not isinstance(gates, dict):
        report.fail("evidence schema and gates must use schema 3")
    else:
        if set(gates.get("behavior_hard_gates", [])) != HARD_GATE_NAMES:
            report.fail("every behavior hard gate must remain declared")
        expected_gates = {"macro_pass_rate_min": 0.90, "selection_precision_min": 0.95, "selection_recall_min": 0.95, "selection_specificity_min": 0.95, "high_risk_false_positives_max": 0, "all_execution_receipts_valid": True, "all_independent_gradings_complete": True}
        for field, expected in expected_gates.items():
            if gates.get(field) != expected:
                report.fail(f"evidence gate {field} must be {expected!r}")
    if not report.failures:
        report.ok("production suite matches the current-only schema-v3 contract")


def validate_node_validators(skill_root: Path, report: Report) -> None:
    node = shutil.which("node")
    if node is None:
        report.fail("Node.js is required to validate eval scripts")
        return
    for relative in NODE_VALIDATORS:
        completed = subprocess.run([node, "--check", str(skill_root / relative)], text=True, capture_output=True, check=False)
        if completed.returncode != 0:
            report.fail(f"invalid Node validator {relative}: {(completed.stderr or completed.stdout).strip()}")
    if not report.failures:
        report.ok(f"all {len(NODE_VALIDATORS)} Node validators parse")


def validate_python_eval_scripts(skill_root: Path, report: Report) -> None:
    for relative in PYTHON_EVAL_SCRIPTS:
        try:
            compile(read_text(skill_root / relative), str(skill_root / relative), "exec")
        except SyntaxError as exc:
            report.fail(f"invalid Python eval script {relative}: {exc.msg} at line {exc.lineno}")
    if not report.failures:
        report.ok(f"all {len(PYTHON_EVAL_SCRIPTS)} Python eval scripts parse")


def contract_digest(skill_root: Path) -> str:
    files = [skill_root / "SKILL.md"]
    files.extend(path for path in (skill_root / "scripts").glob("*.py") if path.name != "validate_fdd.py")
    files.extend((skill_root / "references" / "document-types" / "design-system").rglob("*.md"))
    files.extend(skill_root / "references" / "shared" / name for name in ("human-readable-writing.md", "source-grounding.md", "existing-document-edits.md"))
    files.extend((skill_root / "evals").rglob("*"))
    included = [path for path in files if path.is_file() and path.relative_to(skill_root).as_posix() != "evals/production-evidence.json" and path.relative_to(skill_root).as_posix() not in {"evals/evals.json", "evals/trigger-evals.json"} and not path.relative_to(skill_root).as_posix().startswith("evals/evidence/")]
    digest = hashlib.sha256()
    for path in sorted(set(included)):
        digest.update(path.relative_to(skill_root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    manifest = read_json(skill_root / "evals/evals.json")
    suite = read_json(skill_root / "evals/production-suite.json")
    selected = set(suite.get("behavior", {}).get("eval_ids", []))
    subset = {"skill_name": manifest.get("skill_name"), "evals": [item for item in manifest.get("evals", []) if isinstance(item, dict) and item.get("id") in selected]}
    digest.update(b"evals/evals.design-system.json\0")
    digest.update(json.dumps(subset, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    digest.update(b"\0")
    return digest.hexdigest()


def inspect_png(path: Path) -> tuple[int, int, bool] | None:
    content = path.read_bytes()
    if not content.startswith(b"\x89PNG\r\n\x1a\n"):
        return None
    position = 8
    chunks: list[tuple[bytes, bytes]] = []
    while position < len(content):
        if position + 12 > len(content):
            return None
        length = struct.unpack(">I", content[position:position + 4])[0]
        chunk_type = content[position + 4:position + 8]
        data_start = position + 8
        data_end = data_start + length
        crc_end = data_end + 4
        if crc_end > len(content):
            return None
        data = content[data_start:data_end]
        if struct.unpack(">I", content[data_end:crc_end])[0] != zlib.crc32(chunk_type + data) & 0xFFFFFFFF:
            return None
        chunks.append((chunk_type, data))
        position = crc_end
        if chunk_type == b"IEND":
            break
    if position != len(content) or not chunks or chunks[0][0] != b"IHDR" or len(chunks[0][1]) != 13 or chunks[-1] != (b"IEND", b""):
        return None
    width, height, bit_depth, color_type, compression, filter_method, interlace = struct.unpack(">IIBBBBB", chunks[0][1])
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(color_type)
    if width <= 0 or height <= 0 or channels is None or bit_depth not in {8, 16} or compression != 0 or filter_method != 0 or interlace != 0:
        return None
    try:
        decoded = zlib.decompress(b"".join(data for chunk_type, data in chunks if chunk_type == b"IDAT"))
    except zlib.error:
        return None
    expected = height * (1 + ((width * channels * bit_depth + 7) // 8))
    if len(decoded) != expected:
        return None
    return width, height, color_type in {4, 6} or any(chunk_type == b"tRNS" for chunk_type, _data in chunks)


def normalized_artifact_paths(skill_root: Path, payload: dict[str, Any], report: Report) -> set[str]:
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list):
        report.fail("production evidence artifacts must be an array")
        return set()
    paths: set[str] = set()
    for index, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict) or not isinstance(artifact.get("kind"), str) or not isinstance(artifact.get("path"), str):
            report.fail(f"artifacts[{index}] is invalid")
            continue
        relative = artifact["path"]
        normalized = relative.replace("\\", "/")
        if relative != normalized or not normalized.startswith("evals/evidence/") or any(part in {"", ".", ".."} for part in normalized.split("/")) or PurePosixPath(normalized).as_posix() != normalized:
            report.fail(f"artifacts[{index}] path is invalid")
            continue
        if normalized in paths:
            report.fail(f"duplicate evidence artifact path: {normalized}")
            continue
        paths.add(normalized)
        resolved = (skill_root / normalized).resolve()
        if not is_within(skill_root / "evals/evidence", resolved) or not resolved.is_file():
            report.fail(f"evidence artifact does not exist: {normalized}")
        elif not is_sha256(artifact.get("sha256")) or hashlib.sha256(resolved.read_bytes()).hexdigest() != artifact["sha256"]:
            report.fail(f"evidence artifact hash does not match: {normalized}")
    return paths


def resolve_descriptor(skill_root: Path, descriptor: Any, artifact_paths: set[str], label: str, report: Report) -> Path | None:
    if not isinstance(descriptor, dict) or descriptor.get("path") not in artifact_paths or not is_sha256(descriptor.get("sha256")):
        report.fail(f"{label} must reference a hashed evidence artifact")
        return None
    path = skill_root / descriptor["path"]
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != descriptor["sha256"]:
        report.fail(f"{label} artifact is missing or has the wrong hash")
        return None
    return path


def manifest_changed_paths(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
    def state(payload: dict[str, Any]) -> dict[str, str]:
        return {item["path"]: f"{item.get('type')}:{item.get('sha256', '')}" for item in payload.get("entries", []) if isinstance(item, dict) and isinstance(item.get("path"), str)}
    before_state = state(before)
    after_state = state(after)
    return [path for path in sorted(set(before_state) | set(after_state)) if before_state.get(path) != after_state.get(path) and (after_state.get(path) or before_state.get(path) or "").startswith("file:")]


def validate_manifest(payload: Any, label: str, report: Report) -> dict[str, str]:
    if not isinstance(payload, dict) or not isinstance(payload.get("files"), dict) or not isinstance(payload.get("entries"), list):
        report.fail(f"{label} manifest is incomplete")
        return {}
    files = payload["files"]
    if any(not isinstance(path, str) or not is_sha256(digest) for path, digest in files.items()):
        report.fail(f"{label} manifest files are invalid")
        return {}
    entries = payload["entries"]
    entry_files = {
        item.get("path"): item.get("sha256")
        for item in entries
        if isinstance(item, dict) and item.get("type") == "file" and isinstance(item.get("path"), str)
    }
    if entry_files != files:
        report.fail(f"{label} manifest entries do not match files")
    encoded = json.dumps(sorted(entries, key=lambda item: item.get("path", "")), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if hashlib.sha256(encoded).hexdigest() != payload.get("sha256"):
        report.fail(f"{label} manifest tree hash is not canonical")
    return files


def description_hash(skill_root: Path) -> str:
    match = FRONTMATTER_RE.match(read_text(skill_root / "SKILL.md"))
    body = match.group("body") if match else ""
    description = re.search(r"(?m)^description:\s*(.+)$", body)
    return hashlib.sha256((description.group(1).strip() if description else "").encode("utf-8")).hexdigest()


def validate_selection_reuse(skill_root: Path, selection: Any, report: Report) -> None:
    suite = read_json(skill_root / "evals/production-suite.json")
    contract = suite["selection"]
    if not isinstance(selection, dict):
        report.fail("selection reuse evidence must be an object")
        return
    current_dataset_hash = hashlib.sha256((skill_root / contract["dataset"]).read_bytes()).hexdigest()
    metrics = selection.get("metrics") if isinstance(selection.get("metrics"), dict) else {}
    if selection.get("status") != "reused" or selection.get("passed") is not True or selection.get("new_selection_executed") is not False or selection.get("description_sha256") != description_hash(skill_root) or selection.get("description_sha256") != contract["description_sha256"] or selection.get("dataset_sha256") != current_dataset_hash or selection.get("dataset_sha256") != contract["dataset_sha256"] or selection.get("source_sha256") != contract["evidence_sha256"]:
        report.fail("selection evidence does not satisfy exact-hash reuse")
    if metrics.get("precision", 0) < 0.95 or metrics.get("recall", 0) < 0.95 or metrics.get("specificity", 0) < 0.95 or metrics.get("high_risk_false_positives") != 0:
        report.fail("reused selection metrics do not pass release thresholds")


def validate_behavior_evidence(skill_root: Path, payload: dict[str, Any], artifact_paths: set[str], report: Report) -> None:
    scope = payload.get("evaluation_scope")
    behavior = payload.get("behavior")
    if not isinstance(scope, dict) or scope.get("kind") not in {"production", "targeted"} or not isinstance(scope.get("eval_ids"), list):
        report.fail("evaluation_scope is invalid")
        return
    eval_ids = scope["eval_ids"]
    if not isinstance(behavior, dict) or not isinstance(behavior.get("runs"), list) or not isinstance(behavior.get("summary"), dict):
        report.fail("behavior evidence is incomplete")
        return
    runs = behavior["runs"]
    summary = behavior["summary"]
    if [run.get("eval_id") for run in runs if isinstance(run, dict)] != eval_ids:
        report.fail("behavior runs must match evaluation_scope order")
    calculated = {"responses_present": 0, "valid_execution_receipts": 0, "deterministic_passed": 0, "deterministic_failed": 0, "completed_independent_gradings": 0, "semantic_passed": 0}
    pass_rates: list[float] = []
    task_ids: set[str] = set()
    grader_ids: set[str] = set()
    for index, run in enumerate(runs):
        label = f"behavior.runs[{index}]"
        if not isinstance(run, dict):
            report.fail(f"{label} must be an object")
            continue
        calculated["responses_present"] += run.get("response_present") is True
        execution = run.get("execution") if isinstance(run.get("execution"), dict) else {}
        calculated["valid_execution_receipts"] += execution.get("valid") is True
        calculated["deterministic_passed"] += run.get("deterministic_status") == "pass"
        calculated["deterministic_failed"] += run.get("deterministic_status") == "fail"
        calculated["completed_independent_gradings"] += run.get("grading_status") in {"completed", "quality-failed"}
        calculated["semantic_passed"] += run.get("grading_status") == "completed"
        if isinstance(run.get("pass_rate"), (int, float)):
            pass_rates.append(float(run["pass_rate"]))
        task_id = run.get("task_context_id")
        grader_id = run.get("grader_task_context_id")
        if execution.get("valid") is True and isinstance(task_id, str):
            task_ids.add(task_id)
        if run.get("grading_status") in {"completed", "quality-failed"} and isinstance(grader_id, str):
            grader_ids.add(grader_id)
        receipt_path = resolve_descriptor(skill_root, run.get("execution_receipt"), artifact_paths, f"{label}.execution_receipt", report) if run.get("execution_receipt") else None
        before_path = resolve_descriptor(skill_root, run.get("workspace_before_manifest"), artifact_paths, f"{label}.workspace_before_manifest", report) if run.get("workspace_before_manifest") else None
        after_path = resolve_descriptor(skill_root, run.get("workspace_after_manifest"), artifact_paths, f"{label}.workspace_after_manifest", report) if run.get("workspace_after_manifest") else None
        response_path = resolve_descriptor(skill_root, run.get("response"), artifact_paths, f"{label}.response", report) if run.get("response") else None
        if all(path is not None for path in (receipt_path, before_path, after_path, response_path)):
            receipt = read_json(receipt_path)
            before = read_json(before_path)
            after = read_json(after_path)
            before_files = validate_manifest(before, f"{label}.before", report)
            after_files = validate_manifest(after, f"{label}.after", report)
            if receipt.get("schema_version") != 3 or receipt.get("provenance") != "harness-derived-from-task-response-and-manifests" or receipt.get("task_context_id") != task_id or receipt.get("telemetry") != {"status": "unavailable", "duration_ms": None, "total_tokens": None} or receipt.get("capability_evidence") != {"status": "unverified", "events": []}:
                report.fail(f"{label} execution receipt contract is invalid")
            if receipt.get("produced_paths") != manifest_changed_paths(before, after):
                report.fail(f"{label} produced_paths do not match manifest diff")
            if receipt.get("workspace_before_sha256") != before.get("sha256") or receipt.get("workspace_after_sha256") != after.get("sha256"):
                report.fail(f"{label} receipt hashes do not match manifests")
            if receipt.get("response_sha256") != hashlib.sha256(response_path.read_bytes()).hexdigest():
                report.fail(f"{label} response hash does not match receipt")
            workspace_relative = run.get("workspace_path")
            workspace_root = (skill_root / workspace_relative).resolve() if isinstance(workspace_relative, str) else None
            if workspace_root is None or not is_within(skill_root / "evals/evidence", workspace_root) or not workspace_root.is_dir():
                report.fail(f"{label} preserved workspace is missing")
            else:
                actual_files = {path.relative_to(workspace_root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in workspace_root.rglob("*") if path.is_file() and not path.is_symlink()}
                if actual_files != after_files or any(path.is_symlink() for path in workspace_root.rglob("*")):
                    report.fail(f"{label} preserved workspace does not match after manifest")
            if not isinstance(before_files, dict):
                report.fail(f"{label} before files are invalid")
        if run.get("grading"):
            grading_path = resolve_descriptor(skill_root, run.get("grading"), artifact_paths, f"{label}.grading", report)
            if grading_path is not None:
                grading = read_json(grading_path)
                if grading.get("schema_version") != 3 or grading.get("status") != "completed-independent-grading" or grading.get("provenance") != "independent-luna-grader-output" or grading.get("grader_task_context_id") != grader_id:
                    report.fail(f"{label} grading contract is invalid")
                records = grading.get("expectations")
                grading_summary = grading.get("summary")
                if not isinstance(records, list) or not isinstance(grading_summary, dict):
                    report.fail(f"{label} grading records are incomplete")
                else:
                    passed = sum(isinstance(item, dict) and item.get("passed") is True for item in records)
                    expected_summary = {"passed": passed, "failed": len(records) - passed, "total": len(records), "pass_rate": passed / len(records) if records else 0.0}
                    if grading_summary != expected_summary:
                        report.fail(f"{label} grading summary is not recalculated")
                    if run.get("pass_rate") != grading_summary.get("pass_rate"):
                        report.fail(f"{label} published pass_rate does not match grading")
                    expected_status = "completed" if grading_summary.get("failed") == 0 else "quality-failed"
                    if run.get("grading_status") != expected_status:
                        report.fail(f"{label} grading status does not match semantic result")
        if run.get("deterministic_grading"):
            deterministic_path = resolve_descriptor(skill_root, run.get("deterministic_grading"), artifact_paths, f"{label}.deterministic_grading", report)
            if deterministic_path is not None:
                deterministic = read_json(deterministic_path)
                failed = deterministic.get("summary", {}).get("failed")
                expected_status = "pass" if failed == 0 else "fail"
                if deterministic.get("status") != "completed" or run.get("deterministic_status") != expected_status:
                    report.fail(f"{label} deterministic status does not match its artifact")
    if summary.get("planned_execution_tasks") != len(eval_ids):
        report.fail("behavior summary planned_execution_tasks is inaccurate")
    for field, value in calculated.items():
        if summary.get(field) != value:
            report.fail(f"behavior summary {field} is inaccurate")
    calculated_macro = round(sum(pass_rates) / len(pass_rates), 4) if pass_rates else None
    if summary.get("macro_pass_rate") != calculated_macro:
        report.fail("behavior macro_pass_rate must be null without grades or recalculated from completed grades")
    if len(task_ids) != calculated["valid_execution_receipts"]:
        report.fail("valid execution receipts must have unique harness task IDs")
    if len(grader_ids) != calculated["completed_independent_gradings"]:
        report.fail("completed gradings must have unique harness grader task IDs")
    runtime = payload.get("runtime") if isinstance(payload.get("runtime"), dict) else {}
    for field in ("planned_execution_tasks", "responses_present", "valid_execution_receipts", "deterministic_passed", "deterministic_failed", "completed_independent_gradings"):
        if runtime.get(field) != summary.get(field):
            report.fail(f"runtime {field} must match behavior summary")
    if "execution_contexts" in runtime or "grading_contexts" in runtime:
        report.fail("runtime must not present planned task IDs as raw host context counts")


def validate_production_evidence(skill_root: Path, report: Report, require_production_ready: bool = False) -> None:
    payload = read_json(skill_root / "evals/production-evidence.json")
    if not isinstance(payload, dict):
        report.fail("production evidence must be an object")
        return
    if payload.get("schema_version") == 2:
        if require_production_ready:
            report.fail("schema-v2 evidence is diagnostic-only")
        elif payload.get("production_ready") is not False or payload.get("status") != "diagnostic-failed":
            report.fail("schema-v2 evidence must remain diagnostic-failed")
        else:
            report.ok("schema-v2 evidence is retained as diagnostic-only audit material")
        return
    if payload.get("schema_version") != 3:
        report.fail("production evidence must use schema_version 3")
        return
    if payload.get("trust_boundary") != "local-unattested":
        report.fail("production evidence trust_boundary must be local-unattested")
    try:
        date.fromisoformat(str(payload.get("generated_at")))
    except ValueError:
        report.fail("production evidence generated_at must be a real ISO date")
    if payload.get("contract_sha256") != contract_digest(skill_root):
        report.fail("production evidence is stale for the current contract")
    production_ready = payload.get("production_ready") is True and payload.get("status") == "production-ready"
    diagnostic = payload.get("production_ready") is False and payload.get("status") == "diagnostic-failed"
    if not production_ready and not diagnostic:
        report.fail("production evidence status and production_ready are inconsistent")
    if require_production_ready and not production_ready:
        report.fail("production-ready validation rejects diagnostic evidence")
    if any(field in payload for field in ("baseline_ref", "baseline_contract_sha256", "blind_comparison")):
        report.fail("schema-v3 evidence must not contain baseline or blind comparison")
    artifact_paths = normalized_artifact_paths(skill_root, payload, report)
    validate_behavior_evidence(skill_root, payload, artifact_paths, report)
    validate_selection_reuse(skill_root, payload.get("selection"), report)
    scope = payload.get("evaluation_scope") if isinstance(payload.get("evaluation_scope"), dict) else {}
    summary = payload.get("behavior", {}).get("summary", {}) if isinstance(payload.get("behavior"), dict) else {}
    verification_status = payload.get("verification_status")
    if scope.get("kind") == "targeted":
        expected = "targeted-pass" if summary.get("all_scope_passed") is True else "targeted-failed"
        if verification_status != expected or production_ready:
            report.fail("targeted evidence must report targeted pass/fail and remain non-production")
    if production_ready:
        if scope.get("kind") != "production" or scope.get("eval_ids") != list(PRODUCTION_BEHAVIOR_IDS):
            report.fail("production-ready evidence must cover eval 1 through 32")
        if summary.get("valid_execution_receipts") != 32 or summary.get("deterministic_passed") != 32 or summary.get("completed_independent_gradings") != 32 or summary.get("semantic_passed") != 32 or not isinstance(summary.get("macro_pass_rate"), (int, float)) or summary["macro_pass_rate"] < 0.90:
            report.fail("production-ready behavior gates are incomplete")
        hard_gates = summary.get("hard_gates")
        if not isinstance(hard_gates, dict) or set(hard_gates) != HARD_GATE_NAMES or any(value != "pass" for value in hard_gates.values()):
            report.fail("production-ready hard gates must all pass")
    review = payload.get("review")
    if summary.get("all_scope_passed") is True:
        if not isinstance(review, dict) or review.get("status") != "generated":
            report.fail("successful scope requires a generated static review")
        else:
            review_path = skill_root / str(review.get("artifact_path"))
            if review.get("artifact_path") not in artifact_paths or not review_path.is_file() or hashlib.sha256(review_path.read_bytes()).hexdigest() != review.get("sha256") or review_path.stat().st_size < 1024:
                report.fail("static review artifact is invalid")
    if 24 in scope.get("eval_ids", []) and summary.get("all_scope_passed") is True:
        image = payload.get("image_canary")
        if not isinstance(image, dict) or image.get("passed") is not True or image.get("eval_id") != 24:
            report.fail("successful eval 24 requires a passing image canary")
        else:
            image_path = skill_root / str(image.get("artifact_path"))
            if image.get("artifact_path") not in artifact_paths or not image_path.is_file() or hashlib.sha256(image_path.read_bytes()).hexdigest() != image.get("sha256") or inspect_png(image_path) != (1024, 500, False):
                report.fail("eval 24 PNG evidence is invalid")
    if not isinstance(payload.get("limitations"), list) or not payload["limitations"]:
        report.fail("production evidence must state limitations")
    if not report.failures:
        report.ok("production evidence matches the schema-v3 scope and receipt contract")


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
        if "evals" in markdown_file.parts and "evidence" in markdown_file.parts:
            continue
        content = FENCE_RE.sub("", read_text(markdown_file))
        for match in LINK_RE.finditer(content):
            raw = match.group("target").strip()
            if urlparse(raw).scheme or raw.startswith("#"):
                continue
            target = normalize_link_target(raw)
            if not target:
                continue
            checked += 1
            resolved = (markdown_file.parent / target).resolve()
            if not is_within(skill_root, resolved):
                report.fail(f"relative link escapes skill root: {markdown_file.relative_to(skill_root)} -> {raw}")
            elif not resolved.exists():
                report.fail(f"broken relative link: {markdown_file.relative_to(skill_root)} -> {raw}")
    if not report.failures:
        report.ok(f"{checked} relative Markdown links resolve")


def validate_repository_metadata(skill_root: Path, report: Report, expected_version: str | None) -> None:
    repo_root = skill_root.parent.parent
    package = read_json(repo_root / "package.json")
    marketplace = read_json(repo_root / ".claude-plugin/marketplace.json")
    package_version = package.get("version") if isinstance(package, dict) else None
    marketplace_version = marketplace.get("metadata", {}).get("version") if isinstance(marketplace, dict) and isinstance(marketplace.get("metadata"), dict) else None
    if not isinstance(package_version, str) or package_version != marketplace_version or not SEMVER_RE.fullmatch(package_version):
        report.fail("repository and marketplace versions must match valid SemVer")
    if expected_version is not None and package_version != expected_version:
        report.fail("repository version does not match the requested release version")
    skill_entries = [item for plugin in marketplace.get("plugins", []) if isinstance(plugin, dict) for item in plugin.get("skills", []) if isinstance(item, str)] if isinstance(marketplace, dict) else []
    if skill_entries.count("./skills/document-writing") != 1:
        report.fail("marketplace must contain document-writing exactly once")
    if "[document-writing](skills/document-writing/)" not in read_text(repo_root / "README.md"):
        report.fail("README must expose document-writing")
    if not report.failures:
        report.ok("repository metadata is aligned")


def validate_package(skill_root: Path, expected_version: str | None = None, require_production_ready: bool = False) -> Report:
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_root", nargs="?", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--expected-version")
    parser.add_argument("--print-contract-digest", action="store_true")
    parser.add_argument("--require-production-ready", action="store_true")
    args = parser.parse_args()
    skill_root = Path(args.skill_root).resolve()
    if not skill_root.is_dir():
        print(f"error: skill root is not a directory: {skill_root}", file=sys.stderr)
        return EXIT_USAGE
    if args.print_contract_digest:
        print(contract_digest(skill_root))
        return EXIT_OK
    try:
        report = validate_package(skill_root, args.expected_version, args.require_production_ready)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_USAGE
    print(report.as_json() if args.format == "json" else report.as_text())
    return EXIT_VALIDATION if report.failures else EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
