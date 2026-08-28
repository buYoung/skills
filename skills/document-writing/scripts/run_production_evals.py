#!/usr/bin/env python3
"""Coordinate direct Codex production evaluations for document-writing.

The runner compares the current skill with the same tasks performed without
the skill. Independent graders and blind comparators write their own records
between stages; evidence generation fails closed until those records,
the static review, and the image canary are complete.

Usage examples:
  python scripts/run_production_evals.py --stage prepare
  python scripts/run_production_evals.py --stage direct-behavior-prepare --iteration 1
  python scripts/run_production_evals.py --stage direct-behavior-finalize --iteration 1
  python scripts/run_production_evals.py --stage direct-selection-prepare --iteration 1
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import io
import json
import math
import os
import re
import secrets
import shutil
import subprocess
import sys
import tarfile
import tempfile
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


EXIT_OK = 0
EXIT_FAILURE = 1
EXIT_USAGE = 2
SCRIPT_PATH = Path(__file__).resolve()
SKILL_ROOT = SCRIPT_PATH.parent.parent
REPOSITORY_ROOT = SKILL_ROOT.parent.parent
SUITE_PATH = SKILL_ROOT / "evals" / "production-suite.json"
CURRENT_SNAPSHOT = "with-skill"
EXECUTION_MODEL = "gpt-5.6-luna"
EXECUTION_REASONING_EFFORT = "medium"
DIRECT_EVENT_NAMES = {
    "Read", "Write", "Edit", "Bash", "WebSearch", "WebFetch",
    "BrowserOpen", "MCP", "image_gen", "HarnessArtifactWrite",
}
CLARIFICATION_EVAL_IDS = {21, 26, 27}


class ProductionEvalError(RuntimeError):
    """Raised when the suite cannot be executed safely."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ProductionEvalError(f"cannot read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ProductionEvalError(f"invalid JSON in {path}: {exc}") from exc


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_manifest(root: Path) -> dict[str, Any]:
    """Return a deterministic full tree manifest without following symlinks."""
    entries: list[dict[str, str]] = []
    files: dict[str, str] = {}
    if not root.exists():
        return {"workspace_root": str(root), "root": str(root), "exists": False, "entries": [], "files": {}, "sha256": hashlib.sha256(b"").hexdigest()}
    for path in sorted(root.rglob("*"), key=lambda value: value.as_posix()):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            item = {"path": relative, "type": "symlink", "target": os.readlink(path)}
        elif path.is_file():
            digest = sha256_file(path)
            item = {"path": relative, "type": "file", "sha256": digest}
            files[relative] = digest
        elif path.is_dir():
            item = {"path": relative, "type": "directory"}
        else:
            item = {"path": relative, "type": "special"}
        entries.append(item)
    encoded = json.dumps(entries, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return {"workspace_root": str(root), "root": str(root), "exists": True, "entries": entries, "files": files, "sha256": hashlib.sha256(encoded).hexdigest()}


def manifest_state(manifest: dict[str, Any]) -> dict[str, str]:
    return {
        entry["path"]: (f"file:{entry.get('sha256')}" if entry.get("type") == "file" else str(entry.get("type")))
        for entry in manifest.get("entries", [])
        if isinstance(entry, dict) and isinstance(entry.get("path"), str)
    }


def write_review_bundle(run_dir: Path, workspace: Path, response: str, manifest: dict[str, Any]) -> None:
    """Create the flat files expected by the skill-creator review viewer."""
    outputs = run_dir / "outputs"
    outputs.mkdir(parents=True, exist_ok=True)
    (outputs / "assistant-response.md").write_text(response, encoding="utf-8")
    tree_lines = [f"{entry['type']}: {entry['path']}" for entry in manifest.get("entries", [])]
    (outputs / "tree.txt").write_text("\n".join(tree_lines) + ("\n" if tree_lines else ""), encoding="utf-8")
    sections: list[str] = []
    for relative in sorted(manifest.get("files", {})):
        if not relative.lower().endswith(".md") or relative == ".eval-context.md":
            continue
        source = workspace / relative
        sections.append(f"# `{relative}`\n\n{source.read_text(encoding='utf-8')}".rstrip())
    (outputs / "artifact-review.md").write_text("\n\n---\n\n".join(sections) + ("\n" if sections else ""), encoding="utf-8")


def sanitize_name(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not slug:
        raise ProductionEvalError(f"cannot derive a safe directory name from {value!r}")
    return slug


def require_relative(path_value: str, label: str) -> Path:
    candidate = Path(path_value)
    if not path_value.strip() or candidate == Path(".") or candidate.is_absolute() or ".." in candidate.parts:
        raise ProductionEvalError(f"{label} must be a repository-relative path: {path_value!r}")
    return candidate


def suite_workspace(suite: dict[str, Any]) -> Path:
    relative = Path(str(suite["workspace"]))
    if relative.is_absolute() or relative.parts != ("..", "document-writing-workspace"):
        raise ProductionEvalError("workspace must be the exact ignored sibling ../document-writing-workspace")
    workspace = (SKILL_ROOT / relative).resolve()
    expected_parent = SKILL_ROOT.parent.resolve()
    if workspace.parent != expected_parent:
        raise ProductionEvalError("workspace must be the ignored sibling of skills/document-writing")
    return workspace


def next_iteration(workspace: Path) -> int:
    numbers = []
    for candidate in workspace.glob("iteration-*"):
        if candidate.is_dir() and candidate.name.removeprefix("iteration-").isdigit():
            numbers.append(int(candidate.name.removeprefix("iteration-")))
    return max(numbers, default=0) + 1


def iteration_root(workspace: Path, iteration: int) -> Path:
    if iteration < 1:
        raise ProductionEvalError("iteration must be a positive integer")
    return workspace / f"iteration-{iteration}"


def git_archive(ref: str, destination: Path) -> None:
    """Extract the document-writing skill from a ref without checking it out."""
    destination.mkdir(parents=True, exist_ok=True)
    command = ["git", "archive", "--format=tar", ref, "skills/document-writing"]
    try:
        completed = subprocess.run(command, cwd=REPOSITORY_ROOT, capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc, subprocess.CalledProcessError) else str(exc)
        raise ProductionEvalError(f"git archive failed for {ref}: {detail.strip()}") from exc
    with tarfile.open(fileobj=io.BytesIO(completed.stdout), mode="r:") as archive:
        members = archive.getmembers()
        if any(member.name.startswith("/") or ".." in Path(member.name).parts for member in members):
            raise ProductionEvalError(f"git archive for {ref} contains an unsafe path")
        archive.extractall(destination, members=members)
    extracted = destination / "skills" / "document-writing"
    if not extracted.is_dir():
        raise ProductionEvalError(f"git archive for {ref} did not contain skills/document-writing")
    shutil.move(str(extracted), str(destination / "document-writing"))
    shutil.rmtree(destination / "skills")


def overlay_working_tree(snapshot_root: Path) -> None:
    """Overlay tracked and untracked current files after the Git archive snapshot."""
    target = snapshot_root / "document-writing"
    shutil.copytree(SKILL_ROOT, target, dirs_exist_ok=True, symlinks=True,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))


def copy_execution_skill(source: Path, destination: Path) -> None:
    """Copy only the instructions needed by Design System evals, never eval answers."""
    destination.mkdir(parents=True, exist_ok=False)
    shutil.copy2(source / "SKILL.md", destination / "SKILL.md")
    design_system_source = source / "references" / "document-types" / "design-system"
    if not design_system_source.is_dir():
        raise ProductionEvalError(f"design-system references are missing: {design_system_source}")
    shutil.copytree(
        design_system_source,
        destination / "references" / "document-types" / "design-system",
        symlinks=True,
    )
    shared_destination = destination / "references" / "shared"
    shared_destination.mkdir(parents=True)
    for name in ("human-readable-writing.md", "source-grounding.md", "existing-document-edits.md"):
        source_file = source / "references" / "shared" / name
        if not source_file.is_file():
            raise ProductionEvalError(f"shared reference is missing: {source_file}")
        shutil.copy2(source_file, shared_destination / name)


def contract_hash(skill_path: Path) -> str:
    """Match validate_package.py's cycle-free production contract digest."""
    files = [skill_path / "SKILL.md"]
    files.extend(
        path
        for path in (skill_path / "scripts").glob("*.py")
        if path.name != "validate_fdd.py"
    )
    files.extend(
        (skill_path / "references" / "document-types" / "design-system").rglob("*.md")
    )
    files.extend(
        skill_path / "references" / "shared" / name
        for name in ("human-readable-writing.md", "source-grounding.md", "existing-document-edits.md")
    )
    files.extend((skill_path / "evals").rglob("*"))
    included = [
        path for path in files if path.is_file()
        and path.relative_to(skill_path).as_posix() != "evals/production-evidence.json"
        and path.relative_to(skill_path).as_posix() not in {
            "evals/evals.json",
            "evals/trigger-evals.json",
        }
        and not path.relative_to(skill_path).as_posix().startswith("evals/evidence/")
    ]
    digest = hashlib.sha256()
    for path in sorted(set(included)):
        digest.update(path.relative_to(skill_path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    eval_manifest = load_json(skill_path / "evals/evals.json")
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


def skill_snapshot_manifest(skill_path: Path, source_contract_sha256: str) -> dict[str, Any]:
    manifest = tree_manifest(skill_path)
    manifest["source_contract_sha256"] = source_contract_sha256
    return manifest


def without_skill_manifest() -> dict[str, Any]:
    """Record the intentional absence of a document-writing skill snapshot."""
    return {
        "kind": "without-skill",
        "exists": False,
        "sha256": None,
        "source_contract_sha256": None,
    }


def prepare_iteration(suite: dict[str, Any], iteration: int, dry_run: bool) -> Path:
    workspace = suite_workspace(suite)
    root = iteration_root(workspace, iteration)
    if root.exists():
        raise ProductionEvalError(f"iteration already exists; choose another iteration: {root}")
    planned = [["git", "archive", "--format=tar", "HEAD", "skills/document-writing"]]
    if dry_run:
        print(json.dumps({"stage": "prepare", "iteration": iteration, "commands": planned}, ensure_ascii=False, indent=2))
        return root
    root.mkdir(parents=True)
    snapshots = root / "snapshots"
    git_archive("HEAD", snapshots / CURRENT_SNAPSHOT)
    overlay_working_tree(snapshots / CURRENT_SNAPSHOT)
    metadata = {
        "schema_version": 2,
        "iteration": iteration,
        "prepared_at": utc_now(),
        "suite_path": str(SUITE_PATH.relative_to(REPOSITORY_ROOT)),
        "snapshots": {
            "with_skill": {"path": "snapshots/with-skill/document-writing", "contract_sha256": contract_hash(snapshots / CURRENT_SNAPSHOT / "document-writing")},
        },
    }
    write_json(root / "iteration.json", metadata)
    return root


def load_selected_evals(suite: dict[str, Any]) -> tuple[dict[int, dict[str, Any]], list[dict[str, Any]]]:
    behavior = suite["behavior"]
    manifest_path = SKILL_ROOT / require_relative(str(behavior["eval_manifest"]), "behavior.eval_manifest")
    manifest = load_json(manifest_path)
    by_id = {item.get("id"): item for item in manifest.get("evals", []) if isinstance(item, dict) and isinstance(item.get("id"), int)}
    missing = [{"eval_id": item, "status": "pending", "reason": "eval-id-missing-from-manifest"}
               for item in behavior["eval_ids"] if item not in by_id]
    return by_id, missing


def destination_for_fixture(eval_id: int, suite: dict[str, Any]) -> Path:
    configured = suite["behavior"].get("fixture_destinations", {}).get(str(eval_id), "input")
    return require_relative(str(configured), f"fixture destination for eval {eval_id}")


def copy_fixtures(eval_item: dict[str, Any], workspace: Path, suite: dict[str, Any]) -> list[str]:
    files = eval_item.get("files", [])
    if not files:
        return []
    destination = workspace / destination_for_fixture(int(eval_item["id"]), suite)
    copied: list[str] = []
    roots: set[Path] = set()
    for value in files:
        relative = require_relative(str(value), "fixture file")
        source = SKILL_ROOT / relative
        if not source.is_file():
            raise ProductionEvalError(f"fixture is missing: {source}")
        try:
            fixture_index = relative.parts.index("fixtures")
            roots.add(Path(*relative.parts[:fixture_index + 2]))
        except (ValueError, IndexError) as exc:
            raise ProductionEvalError(f"fixture does not have a fixture-root segment: {relative}") from exc
    if len(roots) != 1:
        raise ProductionEvalError(f"eval {eval_item['id']} must use exactly one fixture root")
    fixture_root = next(iter(roots))
    source_root = SKILL_ROOT / fixture_root
    shutil.copytree(source_root, destination, dirs_exist_ok=False, symlinks=True)
    copied.append(destination.relative_to(workspace).as_posix())
    return copied


def case_contract(eval_id: int, suite: dict[str, Any]) -> dict[str, Any]:
    contract = suite["behavior"].get("case_contracts", {}).get(str(eval_id), {})
    if not isinstance(contract, dict):
        raise ProductionEvalError(f"case contract for eval {eval_id} must be an object")
    return contract


def validator_expectations(label: str, stdout: str, return_code: int) -> list[dict[str, Any]]:
    """Normalize deterministic validator output without treating failures as success."""
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return [{"text": f"{label} produced parseable JSON", "passed": False,
                 "evidence": stdout.strip() or f"validator exited {return_code} without JSON"}]
    if isinstance(payload, dict) and isinstance(payload.get("expectations"), list):
        return [item for item in payload["expectations"] if isinstance(item, dict) and "text" in item and "passed" in item]
    if isinstance(payload, dict) and isinstance(payload.get("checks"), list):
        expectations = [{"text": f"{label}: {item}", "passed": True, "evidence": "deterministic validator check"}
                        for item in payload.get("checks", [])]
        expectations.extend({"text": f"{label}: {item}", "passed": False, "evidence": "deterministic validator failure"}
                            for item in payload.get("failures", []))
        return expectations
    return [{"text": f"{label} returned a recognized result", "passed": False,
             "evidence": f"unrecognized validator payload; exit={return_code}"}]


def fixture_root_for_eval(eval_item: dict[str, Any]) -> Path | None:
    roots: set[Path] = set()
    for value in eval_item.get("files", []):
        relative = require_relative(str(value), "fixture file")
        if "fixtures" in relative.parts:
            index = relative.parts.index("fixtures")
            roots.add(Path(*relative.parts[:index + 2]))
    return SKILL_ROOT / next(iter(roots)) if len(roots) == 1 else None


def run_deterministic_validators(run_dir: Path, workspace: Path, suite: dict[str, Any], eval_item: dict[str, Any]) -> dict[str, Any]:
    """Run fixture and run-record validators after the direct executor has ended."""
    records: list[dict[str, Any]] = []
    contract = case_contract(int(eval_item["id"]), suite)
    mjs_name = contract.get("validation")
    if isinstance(mjs_name, str) and mjs_name:
        fixture_root = fixture_root_for_eval(eval_item)
        result_root = workspace / destination_for_fixture(int(eval_item["id"]), suite)
        if fixture_root is None:
            records.append({"name": mjs_name, "return_code": 2, "stdout": "", "stderr": "fixture root is unavailable"})
        else:
            parts = mjs_name.split()
            command = ["node", str(SKILL_ROOT / "evals" / "validators" / parts[0]), str(fixture_root), str(result_root), *parts[1:]]
            completed = subprocess.run(command, cwd=SKILL_ROOT, text=True, capture_output=True, check=False)
            records.append({"name": mjs_name, "command": command, "return_code": completed.returncode,
                            "stdout": completed.stdout, "stderr": completed.stderr})
    run_validator = [sys.executable, str(SKILL_ROOT / "scripts" / "validate_eval_run.py"),
                     "--suite", str(SUITE_PATH), "--run", str(run_dir)]
    completed = subprocess.run(run_validator, cwd=SKILL_ROOT, text=True, capture_output=True, check=False)
    records.append({"name": "validate_eval_run.py", "command": run_validator, "return_code": completed.returncode,
                    "stdout": completed.stdout, "stderr": completed.stderr})
    expectations: list[dict[str, Any]] = []
    for record in records:
        expectations.extend(validator_expectations(str(record["name"]), str(record["stdout"]), int(record["return_code"])))
    passed = sum(item.get("passed") is True for item in expectations)
    return {"status": "completed", "validators": records, "expectations": expectations,
            "summary": {"passed": passed, "failed": len(expectations) - passed, "total": len(expectations),
                        "pass_rate": passed / len(expectations) if expectations else 0.0}}


def behavior_job_id(eval_id: int, configuration: str, repetition: int) -> str:
    """Return a stable, opaque identifier for one behavior execution."""
    identity = f"document-writing-behavior:{eval_id}:{configuration}:{repetition}"
    return f"job-{hashlib.sha256(identity.encode('utf-8')).hexdigest()[:24]}"


def expected_run_dir(root: Path, eval_item: dict[str, Any], configuration: str, repetition: int) -> Path:
    return root / "behavior" / behavior_job_id(int(eval_item["id"]), configuration, repetition)


def behavior_jobs(suite: dict[str, Any], evals: dict[int, dict[str, Any]]) -> list[tuple[dict[str, Any], dict[str, Any], int]]:
    configurations = suite["behavior"]["configurations"]
    names = [str(item.get("name")) for item in configurations if isinstance(item, dict)]
    if names != ["with_skill", "without_skill"]:
        raise ProductionEvalError("behavior configurations must be exactly with_skill and without_skill")
    jobs: list[tuple[dict[str, Any], dict[str, Any], int]] = []
    for eval_id in suite["behavior"]["eval_ids"]:
        eval_item = evals.get(eval_id)
        if eval_item is None:
            continue
        for configuration in suite["behavior"]["configurations"]:
            for repetition in range(1, int(suite["behavior"]["repetitions"]) + 1):
                jobs.append((eval_item, configuration, repetition))
    return jobs


def direct_report_status_is_usable(
    agent_report: dict[str, Any], eval_id: int, configuration: str = "with_skill"
) -> bool:
    """Fail closed unless the report has an allowed terminal state and exit record."""
    status = agent_report.get("status")
    status_is_allowed = status == "completed" or (
        status == "clarification_required"
        and eval_id in CLARIFICATION_EVAL_IDS
    )
    duration_ms = agent_report.get("duration_ms")
    total_tokens = agent_report.get("total_tokens")
    telemetry_status = agent_report.get("telemetry_status")
    nullable_metric_is_valid = lambda value: value is None or (
        isinstance(value, int) and not isinstance(value, bool) and value >= 0
    )
    return (
        status_is_allowed
        and agent_report.get("return_code") == 0
        and agent_report.get("timed_out") is False
        and isinstance(agent_report.get("stderr"), str)
        and agent_report.get("model") == EXECUTION_MODEL
        and agent_report.get("reasoning_effort") == EXECUTION_REASONING_EFFORT
        and telemetry_status in {"available", "unavailable"}
        and nullable_metric_is_valid(duration_ms)
        and nullable_metric_is_valid(total_tokens)
        and (
            (telemetry_status == "available" and duration_ms is not None and total_tokens is not None)
            or (telemetry_status == "unavailable" and duration_ms is None and total_tokens is None)
        )
        and isinstance(agent_report.get("produced_paths"), list)
        and all(isinstance(path, str) and path.strip() for path in agent_report["produced_paths"])
        and len(set(agent_report["produced_paths"])) == len(agent_report["produced_paths"])
        and isinstance(agent_report.get("context_id"), str)
        and bool(agent_report["context_id"].strip())
    )


def normalize_direct_report_events(
    agent_report: dict[str, Any], _before: dict[str, Any], _after: dict[str, Any]
) -> list[dict[str, Any]]:
    """Preserve strict agent-reported events without aliases or inferred calls."""
    normalized: list[dict[str, Any]] = []

    raw_events = agent_report.get("tool_events")
    if not isinstance(raw_events, list):
        raise ProductionEvalError("direct agent report tool_events must be an array")
    for event in raw_events:
        if (
            not isinstance(event, dict)
            or event.get("name") not in DIRECT_EVENT_NAMES
            or not isinstance(event.get("input"), dict)
            or event.get("status") not in {"success", "error"}
            or not isinstance(event.get("output"), str)
        ):
            raise ProductionEvalError("direct agent report contains a non-canonical tool event")
        normalized.append({
            "name": event["name"],
            "input": event["input"],
            "status": event["status"],
            "output": event["output"],
            "provenance": "agent-reported-not-raw-telemetry",
        })
    return normalized


def direct_agent_report_contract(context_id: str) -> dict[str, Any]:
    """Describe the report shape without disclosing grader-approved outcomes."""
    return {
        "status": "String describing the executor's terminal state.",
        "model": "String identifying the model used by the executor.",
        "reasoning_effort": "String identifying the reasoning setting used by the executor.",
        "telemetry_status": "String describing whether execution telemetry was available.",
        "duration_ms": "Non-negative integer duration in milliseconds, or null when unavailable.",
        "total_tokens": "Non-negative integer token count, or null when unavailable.",
        "produced_paths": "Array of unique workspace-relative paths changed by the executor.",
        "context_id": context_id,
        "return_code": "Integer executor exit status.",
        "timed_out": "Boolean indicating whether the executor timed out.",
        "stderr": "String containing executor stderr, possibly empty.",
        "tool_events": {
            "type": "array",
            "event_shape": {"name": "string", "input": "object", "status": "success|error", "output": "string"},
            "rules": [
                "Record observed capability use as separate events in execution order; this is agent-reported evidence, not raw platform telemetry.",
                "Keep each event's name, input, status, and output in the declared shape.",
            ],
        },
    }


def actual_changed_file_paths(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
    before_state = manifest_state(before)
    after_state = manifest_state(after)
    changed = []
    for path in sorted(set(before_state) | set(after_state)):
        if before_state.get(path) == after_state.get(path):
            continue
        state = after_state.get(path) or before_state.get(path) or ""
        if state.startswith("file:"):
            changed.append(path)
    return changed


def event_paths(event: dict[str, Any]) -> list[str]:
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


def event_path(event: dict[str, Any]) -> str | None:
    paths = event_paths(event)
    return paths[0] if paths else None


def path_is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def event_is_mutating(event: dict[str, Any]) -> bool:
    name = event.get("name")
    if name in {"Write", "Edit"}:
        return True
    if name == "MCP":
        inputs = event.get("input") if isinstance(event.get("input"), dict) else {}
        return bool(re.search(r"\b(?:write|edit|create|update|delete|remove|mutat)\w*\b", json.dumps(inputs, ensure_ascii=False), re.IGNORECASE))
    if name != "Bash":
        return False
    inputs = event.get("input") if isinstance(event.get("input"), dict) else {}
    command = str(inputs.get("command") or inputs.get("cmd") or "")
    return bool(re.search(r"(?:^|\s)(?:>|>>|tee|touch|rm|mv|cp|mkdir|rmdir|chmod|truncate|sed\s+-i|perl\s+-i|python(?:3)?\s+-c|node\s+-e)(?:\s|$)", command))


def capability_used(event: dict[str, Any], capability: str) -> bool:
    name = event.get("name")
    if capability == "web":
        if name in {"WebSearch", "WebFetch", "BrowserOpen"}:
            return True
        if name == "MCP":
            return bool(re.search(
                r"https?://|\b(?:web|browser|url|fetch)\b",
                json.dumps(event.get("input", {}), ensure_ascii=False),
                re.IGNORECASE,
            ))
        return False
    if capability == "image-generation":
        return name == "image_gen"
    return name == capability


def reported_capability_names(event: dict[str, Any]) -> set[str]:
    """Map a recorded tool event to semantic capability names for case contracts."""
    name = str(event.get("name") or "")
    names = {name} if name and name != "MCP" else set()
    if name == "MCP":
        inputs = json.dumps(event.get("input", {}), ensure_ascii=False)
        if capability_used(event, "web"):
            names.update({"MCP", "WebFetch", "Browser"})
        elif re.search(r"\b(?:read|find|grep|search_local|list)\w*\b", inputs, re.IGNORECASE):
            names.add("Read")
        if event_is_mutating(event):
            names.update({"Write", "Edit"})
    return names


def validate_direct_run_integrity(
    run_dir: Path,
    workspace: Path,
    before: dict[str, Any],
    after: dict[str, Any],
    agent_report: dict[str, Any],
    contract: dict[str, Any],
    configuration: str,
    response: str,
) -> list[str]:
    failures: list[str] = []
    events = normalize_direct_report_events(agent_report, before, after)
    changed_paths = actual_changed_file_paths(before, after)
    produced_paths = agent_report.get("produced_paths")
    if not isinstance(produced_paths, list):
        return ["produced_paths must be an array of workspace-relative changed file paths"]
    if any(Path(path).is_absolute() or ".." in Path(path).parts for path in produced_paths):
        failures.append("produced_paths must contain workspace-relative paths")
    if sorted(produced_paths) != changed_paths:
        failures.append(f"produced_paths does not match actual changed file paths: produced={produced_paths!r} actual={changed_paths!r}")
    allowed_change_paths = contract.get("allowed_change_paths", [])
    if not isinstance(allowed_change_paths, list):
        failures.append("allowed_change_paths must be an array")
        allowed_change_paths = []
    for changed_path in changed_paths:
        if not any(fnmatch.fnmatchcase(changed_path, str(pattern)) for pattern in allowed_change_paths):
            failures.append(f"workspace change is outside allowed paths: {changed_path}")
    final_files = set(after.get("files", {}))
    claimed_paths = re.findall(r"`((?:docs|input)/[^`]+)`", response)
    claims_file_completion = bool(re.search(
        r"(?:작성|생성|갱신|업데이트)(?:했|해|을|를| 완료)|\b(?:created|wrote|updated)\b",
        response,
        re.IGNORECASE,
    ))
    if claims_file_completion:
        for claimed_path in claimed_paths:
            normalized_claim = claimed_path.rstrip("/")
            if normalized_claim not in final_files and not any(
                path.startswith(f"{normalized_claim}/") for path in produced_paths
            ):
                failures.append(f"completion response claims a path not present in final outputs: {claimed_path}")
    for event in events:
        if event.get("status") != "success":
            continue
        serialized_inputs = json.dumps(event.get("input", {}), ensure_ascii=False)
        try:
            current_run_relative = run_dir.relative_to(REPOSITORY_ROOT).as_posix()
        except ValueError:
            current_run_relative = run_dir.as_posix()
        redacted_run_inputs = (
            serialized_inputs
            .replace(str(run_dir), "<run>")
            .replace(current_run_relative, "<run>")
            .replace(str(workspace), "<workspace>")
            .replace(str(run_dir / "direct-task.json"), "<direct-task>")
            .replace(str(run_dir / "skill-snapshot"), "<skill-snapshot>")
        )
        if event.get("name") != "HarnessArtifactWrite" and re.search(
            r"document-writing-workspace/iteration-|/(?:with|without)_skill/|skills/document-writing/(?!workspace/)|grading\.json|/outputs/",
            redacted_run_inputs,
            re.IGNORECASE,
        ):
            failures.append("tool input exposes another run, iteration, or unsupplied skill path")
        if configuration == "without_skill" and event.get("name") != "HarnessArtifactWrite":
            redacted_inputs = redacted_run_inputs
            if re.search(
                r"file:|SKILL\.md|skills/document-writing|skill-snapshot(?:/|\\)|/with_skill/|/behavior/|grading\.json|/outputs/",
                redacted_inputs,
                re.IGNORECASE,
            ):
                failures.append("without_skill tool input exposes skill or sibling-result evidence")
        if event.get("name") in {"Write", "Edit"}:
            raw_paths = event_paths(event)
            if not raw_paths:
                failures.append("successful Write/Edit has no target path")
                continue
            for raw_path in raw_paths:
                target = Path(raw_path)
                if target.is_absolute():
                    if not path_is_within(target, workspace):
                        failures.append(f"successful Write/Edit targets outside workspace: {raw_path}")
                        continue
                    relative_target = target.resolve().relative_to(workspace.resolve()).as_posix()
                elif ".." in target.parts:
                    failures.append(f"successful Write/Edit targets outside workspace: {raw_path}")
                    continue
                else:
                    relative_target = target.as_posix()
                    if relative_target.startswith("workspace/"):
                        relative_target = relative_target.removeprefix("workspace/")
                    target = Path(relative_target)
                resolved = workspace / target
                if not path_is_within(resolved, workspace):
                    failures.append(f"successful Write/Edit targets outside workspace: {raw_path}")
                if resolved.is_dir() or raw_path.endswith(("/", "\\")):
                    failures.append(f"successful Write/Edit targets a directory: {raw_path}")
                if relative_target not in changed_paths or relative_target not in produced_paths:
                    failures.append(f"successful Write/Edit is not reflected in manifest/produced_paths: {raw_path}")
        if configuration == "without_skill" and event.get("name") in {"Read", "Bash", "MCP"}:
            raw_path = event_path(event)
            is_allowed_read = False
            if raw_path is not None:
                candidate = Path(raw_path) if Path(raw_path).is_absolute() else workspace / raw_path
                is_allowed_read = path_is_within(candidate, workspace) or candidate.resolve() == (run_dir / "direct-task.json").resolve()
                if not is_allowed_read:
                    failures.append(f"without_skill read is outside workspace: {raw_path}")
    if configuration == "without_skill" and (run_dir / "skill-snapshot").exists():
        failures.append("without_skill contains a skill snapshot")
    denied = set(str(value) for value in contract.get("denied_capabilities", []))
    if contract.get("deny_write_tools") and any(
        event.get("status") == "success" and event_is_mutating(event) for event in events
    ):
        failures.append("deny_write_tools forbids write or mutation capability use")
    for capability in denied:
        if any(capability_used(event, capability) for event in events):
            failures.append(f"denied capability used: {capability}")
    for capability in contract.get("required_capabilities", []):
        if not any(event.get("status") == "success" and capability_used(event, str(capability)) for event in events):
            failures.append(f"required capability missing: {capability}")
    for pattern in contract.get("forbidden_tool_calls", []):
        try:
            forbidden = re.compile(str(pattern))
        except re.error:
            failures.append(f"invalid forbidden tool pattern: {pattern}")
            continue
        if any(
            forbidden.search(capability)
            for event in events
            for capability in reported_capability_names(event)
        ):
            failures.append(f"forbidden capability use: {pattern}")
    for pattern in contract.get("required_tool_calls", []):
        try:
            required = re.compile(str(pattern))
        except re.error:
            failures.append(f"invalid required tool pattern: {pattern}")
            continue
        if not any(
            event.get("status") == "success" and required.search(capability)
            for event in events
            for capability in reported_capability_names(event)
        ):
            failures.append(f"required capability missing: {pattern}")
    if agent_report.get("status") == "clarification_required" and changed_paths:
        failures.append("clarification_required run changed the workspace")
    return failures


def write_execution_failure(run_dir: Path, reasons: list[str]) -> None:
    payload = {"status": "execution-error", "valid": False, "reasons": reasons}
    write_json(run_dir / "execution-failure.json", payload)
    write_json(run_dir / "grading.json", payload)


def public_direct_task(
    job_id: str,
    prompt: str,
    run_dir: Path,
    workspace: Path,
    response_path: Path,
    report_path: Path,
    context_id: str,
    report_contract: dict[str, Any],
    skill_path: Path | None = None,
) -> dict[str, Any]:
    """Build the worker-facing contract without private evaluation metadata."""
    task = {
        "job_id": job_id,
        "prompt": prompt,
        "run_dir": str(run_dir),
        "workspace": str(workspace),
        "response_path": str(response_path),
        "report_path": str(report_path),
        "model": EXECUTION_MODEL,
        "reasoning_effort": EXECUTION_REASONING_EFFORT,
        "context_id": context_id,
        "report_contract": report_contract,
    }
    if skill_path is not None:
        task["skill_path"] = str(skill_path)
    return task


def direct_behavior_prepare_stage(root: Path, suite: dict[str, Any], dry_run: bool) -> dict[str, Any]:
    evals, missing = load_selected_evals(suite)
    tasks: list[dict[str, Any]] = []
    for eval_item, configuration, repetition in behavior_jobs(suite, evals):
        run_dir = expected_run_dir(root, eval_item, str(configuration["name"]), repetition)
        uses_skill = configuration["source"] == "working-tree"
        job_id = behavior_job_id(int(eval_item["id"]), str(configuration["name"]), repetition)
        context_id = uuid.uuid4().hex
        source_skill = root / "snapshots" / CURRENT_SNAPSHOT / "document-writing" if uses_skill else None
        task = public_direct_task(
            job_id,
            str(eval_item["prompt"]),
            run_dir,
            run_dir / "workspace",
            run_dir / "direct-response.md",
            run_dir / "direct-agent-report.json",
            context_id,
            direct_agent_report_contract(context_id),
            run_dir / "skill-snapshot" if uses_skill else None,
        )
        tasks.append(task)
        if dry_run:
            continue
        if run_dir.exists():
            raise ProductionEvalError(f"direct behavior run already exists: {run_dir}")
        run_dir.mkdir(parents=True)
        if uses_skill:
            assert source_skill is not None
            copy_execution_skill(source_skill, run_dir / "skill-snapshot")
            skill_before = skill_snapshot_manifest(run_dir / "skill-snapshot", contract_hash(source_skill))
        else:
            skill_before = without_skill_manifest()
        write_json(run_dir / "skill-snapshot-before.json", skill_before)
        workspace = run_dir / "workspace"
        workspace.mkdir()
        copy_fixtures(eval_item, workspace, suite)
        before = tree_manifest(workspace)
        write_json(run_dir / "workspace-before.json", before)
        write_json(run_dir / "before-manifest.json", before)
        write_json(run_dir / "direct-task.json", task)
    task_refs = [
        {
            "job_id": task["job_id"],
            "task_path": str(Path(task["run_dir"]) / "direct-task.json"),
        }
        for task in tasks
    ]
    report = {"stage": "direct-behavior-prepare", "tasks": task_refs, "pending": missing}
    if not dry_run:
        write_json(root / "direct-behavior-tasks.json", report)
    return report


def direct_behavior_finalize_stage(root: Path, suite: dict[str, Any], dry_run: bool) -> dict[str, Any]:
    evals, missing = load_selected_evals(suite)
    finalized: list[dict[str, Any]] = []
    jobs = behavior_jobs(suite, evals)
    for eval_item, configuration, repetition in jobs:
        run_dir = expected_run_dir(root, eval_item, str(configuration["name"]), repetition)
        if dry_run:
            finalized.append({"run_dir": str(run_dir), "status": "planned"})
            continue
        existing_grading = load_json(run_dir / "grading.json") if (run_dir / "grading.json").is_file() else None
        if isinstance(existing_grading, dict) and existing_grading.get("status") == "completed-independent-grading":
            finalized.append({"run_dir": str(run_dir), "status": "already-finalized"})
            continue
        response_path = run_dir / "direct-response.md"
        report_path = run_dir / "direct-agent-report.json"
        if not response_path.is_file() or not report_path.is_file():
            reason = f"direct agent result is missing: {run_dir}"
            write_execution_failure(run_dir, [reason])
            finalized.append({"run_dir": str(run_dir), "status": "execution-error", "reasons": [reason]})
            continue
        response = response_path.read_text(encoding="utf-8")
        agent_report = load_json(report_path)
        if not isinstance(agent_report, dict) or not direct_report_status_is_usable(
            agent_report, int(eval_item["id"]), str(configuration["name"])
        ):
            reason = f"direct agent report is incomplete: {report_path}"
            write_execution_failure(run_dir, [reason])
            finalized.append({"run_dir": str(run_dir), "status": "execution-error", "reasons": [reason]})
            continue
        before = load_json(run_dir / "workspace-before.json")
        after = tree_manifest(run_dir / "workspace")
        write_json(run_dir / "workspace-after.json", after)
        write_json(run_dir / "after-manifest.json", after)
        try:
            integrity_failures = validate_direct_run_integrity(
                run_dir,
                run_dir / "workspace",
                before,
                after,
                agent_report,
                {
                    **case_contract(int(eval_item["id"]), suite),
                    **suite.get("cases", {}).get(f"eval-{eval_item['id']}", {}),
                },
                str(configuration["name"]),
                response,
            )
        except ProductionEvalError as exc:
            integrity_failures = [str(exc)]
        if integrity_failures:
            write_execution_failure(run_dir, integrity_failures)
            finalized.append({"run_dir": str(run_dir), "status": "execution-error", "reasons": integrity_failures})
            continue
        normalized_events = normalize_direct_report_events(agent_report, before, after)
        tool_events = []
        assistant_tool_blocks = []
        tool_result_blocks = []
        for index, event in enumerate(normalized_events, start=1):
            tool_use_id = f"direct-tool-{index}"
            status = str(event.get("status", "success"))
            tool_event = {
                "tool_use_id": tool_use_id,
                "name": event["name"],
                "input": event.get("input", {}),
                "status": status,
                "output": event["output"],
                "provenance": event.get("provenance"),
            }
            tool_events.append(tool_event)
            assistant_tool_blocks.append({"type": "tool_use", "id": tool_use_id, "name": event["name"], "input": event.get("input", {})})
            tool_result_blocks.append({"type": "tool_result", "tool_use_id": tool_use_id, "is_error": status != "success", "content": event.get("output", "recorded by direct Codex executor")})
        transcript_records = [{"type": "system", "subtype": "init", "model": agent_report.get("model", "codex-direct"), "provenance": "reconstructed-from-agent-report"}]
        if assistant_tool_blocks:
            transcript_records.append({"type": "assistant", "message": {"content": assistant_tool_blocks}})
            transcript_records.append({"type": "user", "message": {"content": tool_result_blocks}})
        transcript_records.append({"type": "assistant", "message": {"content": [{"type": "text", "text": response}]}})
        transcript_records.append({"type": "result", "is_error": False, "result": response, "provenance": "reconstructed-from-agent-report"})
        transcript = "\n".join(json.dumps(item, ensure_ascii=False) for item in transcript_records) + "\n"
        (run_dir / "transcript.stream.jsonl").write_text(transcript, encoding="utf-8")
        (run_dir / "response.txt").write_text(response, encoding="utf-8")
        (run_dir / "assistant-response.md").write_text(response, encoding="utf-8")
        (run_dir / "stderr.log").write_text(agent_report["stderr"], encoding="utf-8")
        counts = dict(Counter(event["name"] for event in tool_events))
        write_json(run_dir / "tool-events.json", {"provenance": "agent-reported-not-raw-telemetry", "events": tool_events, "counts": counts})
        write_review_bundle(run_dir, run_dir / "workspace", response, after)
        skill_before = load_json(run_dir / "skill-snapshot-before.json")
        uses_skill = configuration["source"] == "working-tree"
        if uses_skill:
            skill_after = skill_snapshot_manifest(run_dir / "skill-snapshot", skill_before["source_contract_sha256"])
        else:
            skill_after = without_skill_manifest()
        write_json(run_dir / "skill-snapshot-after.json", skill_after)
        snapshot_is_preserved = (
            skill_before.get("sha256") == skill_after.get("sha256")
            and skill_before.get("source_contract_sha256") == skill_after.get("source_contract_sha256")
            and (uses_skill or not (run_dir / "skill-snapshot").exists())
        )
        metadata = {
            "eval_id": eval_item["id"],
            "eval_name": eval_item.get("eval_name", f"eval-{eval_item['id']}"),
            "configuration": configuration["name"],
            "run_number": repetition,
            "prompt": eval_item["prompt"],
            "expectations": eval_item.get("expectations", []),
            "expected_output": eval_item.get("expected_output"),
            "case_contract": case_contract(int(eval_item["id"]), suite),
            "allowed_workspace_change_paths": case_contract(int(eval_item["id"]), suite).get("allowed_change_paths", []),
            "skill_contract_sha256": skill_before["source_contract_sha256"],
            "skill_snapshot_before_sha256": skill_before["sha256"],
            "skill_snapshot_after_sha256": skill_after["sha256"],
            "skill_usage": "required" if uses_skill else "prohibited",
            "executor": "codex-direct-subagent",
            "transcript_provenance": "reconstructed-from-direct-agent-report",
            "tool_event_provenance": "agent-reported-not-raw-telemetry",
            "direct_agent_report_sha256": sha256_file(report_path),
            "direct_agent_status": agent_report.get("status", "unreported"),
            "context_id": agent_report.get("context_id"),
        }
        write_json(run_dir / "eval_metadata.json", metadata)
        write_json(run_dir / "run.json", {
            "case_name": f"eval-{eval_item['id']}",
            "eval_id": eval_item["id"],
            "configuration": configuration["name"],
            "run_number": repetition,
            "before_manifest": "before-manifest.json",
            "after_manifest": "after-manifest.json",
            "response": "response.txt",
            "tool_events": "tool-events.json",
            "transcript": "transcript.stream.jsonl",
        })
        duration_ms = agent_report.get("duration_ms")
        write_json(run_dir / "timing.json", {
            "executor_duration_seconds": duration_ms / 1000 if duration_ms is not None else None,
            "total_duration_seconds": duration_ms / 1000 if duration_ms is not None else None,
            "duration_ms": duration_ms,
            "total_tokens": agent_report.get("total_tokens"),
            "return_code": agent_report["return_code"],
            "timed_out": agent_report["timed_out"],
            "requested_model": agent_report.get("model", "codex-direct"),
            "model": agent_report.get("model", "codex-direct"),
            "reasoning_effort": agent_report.get("reasoning_effort"),
            "telemetry_status": agent_report.get("telemetry_status"),
            "produced_paths": agent_report.get("produced_paths"),
            "context_id": agent_report.get("context_id"),
        })
        write_json(run_dir / "metrics.json", {
            "tool_calls": counts,
            "total_tool_calls": sum(counts.values()),
            "total_steps": len(tool_events),
            "files_created": sorted(set(after["files"]) - set(before["files"])),
            "produced_paths": agent_report["produced_paths"],
            "actual_changed_file_paths": actual_changed_file_paths(before, after),
            "errors_encountered": sum(event["status"] != "success" for event in tool_events),
            "output_chars": len(response),
            "transcript_chars": len(transcript),
            "workspace_before_sha256": before["sha256"],
            "workspace_after_sha256": after["sha256"],
        })
        deterministic = run_deterministic_validators(run_dir, run_dir / "workspace", suite, eval_item)
        deterministic["expectations"].append({
            "text": "Execution skill snapshot remains unchanged" if uses_skill else "No document-writing skill snapshot is available",
            "passed": snapshot_is_preserved,
            "evidence": f"before={skill_before['sha256']} after={skill_after['sha256']} uses_skill={uses_skill}",
        })
        deterministic["summary"] = {"passed": sum(item.get("passed") is True for item in deterministic["expectations"]), "failed": sum(item.get("passed") is not True for item in deterministic["expectations"]), "total": len(deterministic["expectations"]), "pass_rate": sum(item.get("passed") is True for item in deterministic["expectations"]) / len(deterministic["expectations"])}
        write_json(run_dir / "deterministic-grading.json", deterministic)
        write_json(run_dir / "grading.json", {"status": "deterministic-only", "expectations": deterministic["expectations"], "summary": deterministic["summary"], "pending_semantic_expectations": eval_item.get("expectations", [])})
        finalized.append({"run_dir": str(run_dir), "status": "completed"})
    report = {"stage": "direct-behavior-finalize", "runs": finalized, "pending": missing}
    write_json(root / "behavior-status.json", report)
    return report


def direct_selection_prepare_stage(root: Path, suite: dict[str, Any], dry_run: bool) -> dict[str, Any]:
    dataset = load_json(SKILL_ROOT / require_relative(str(suite["selection"]["dataset"]), "selection.dataset"))
    cases = [{"id": item["id"], "query": item["query"]} for item in dataset]
    if len(cases) != 60:
        raise ProductionEvalError(f"selection dataset must contain exactly 60 cases, found {len(cases)}")
    tasks: list[dict[str, Any]] = []
    for configuration, snapshot in (("current", CURRENT_SNAPSHOT),):
        description = description_from_skill(root / "snapshots" / snapshot / "document-writing")
        for repetition in range(1, int(suite["selection"]["repetitions"]) + 1):
            context_id = uuid.uuid4().hex
            task_path = root / "direct-selection" / f"{configuration}-run-{repetition}-input.json"
            output_path = root / "direct-selection" / f"{configuration}-run-{repetition}-output.json"
            task = {
                "batch_id": f"{configuration}-run-{repetition}",
                "configuration": configuration,
                "repetition": repetition,
                "context_id": context_id,
                "description": description,
                "cases": cases,
                "input_path": str(task_path),
                "output_path": str(output_path),
                "output_contract": {
                    "status": "completed",
                    "context_id": context_id,
                    "model": EXECUTION_MODEL,
                    "reasoning_effort": EXECUTION_REASONING_EFFORT,
                    "telemetry_status": "available|unavailable",
                    "duration_ms": "nullable non-negative batch duration; use null when unavailable",
                    "total_tokens": "nullable non-negative total token count; use null when unavailable",
                    "return_code": 0,
                    "timed_out": False,
                    "stderr": "string",
                    "decisions": "exactly 60 unique {id, selected, reason} objects",
                },
            }
            tasks.append(task)
            if not dry_run:
                write_json(task_path, task)
    report = {"stage": "direct-selection-prepare", "tasks": tasks}
    if not dry_run:
        write_json(root / "direct-selection-tasks.json", report)
    return report


def direct_selection_finalize_stage(root: Path, suite: dict[str, Any], dry_run: bool) -> dict[str, Any]:
    dataset = load_json(SKILL_ROOT / require_relative(str(suite["selection"]["dataset"]), "selection.dataset"))
    if len(dataset) != 60:
        raise ProductionEvalError(f"selection dataset must contain exactly 60 cases, found {len(dataset)}")
    by_id = {item["id"]: item for item in dataset}
    results = []
    seen_context_ids: set[str] = set()
    for configuration, snapshot in (("current", CURRENT_SNAPSHOT),):
        snapshot_description = description_from_skill(root / "snapshots" / snapshot / "document-writing")
        for repetition in range(1, int(suite["selection"]["repetitions"]) + 1):
            input_path = root / "direct-selection" / f"{configuration}-run-{repetition}-input.json"
            output_path = root / "direct-selection" / f"{configuration}-run-{repetition}-output.json"
            if dry_run:
                results.append({"configuration": configuration, "run_number": repetition, "output_path": str(output_path)})
                continue
            input_payload = load_json(input_path)
            expected_batch_id = f"{configuration}-run-{repetition}"
            if (
                input_payload.get("batch_id") != expected_batch_id
                or input_payload.get("configuration") != configuration
                or input_payload.get("repetition") != repetition
                or not isinstance(input_payload.get("context_id"), str)
                or not input_payload["context_id"].strip()
                or input_payload.get("description") != snapshot_description
                or input_payload.get("cases") != [{"id": item["id"], "query": item["query"]} for item in dataset]
                or input_payload.get("input_path") != str(input_path)
                or input_payload.get("output_path") != str(output_path)
            ):
                raise ProductionEvalError(f"direct selection input changed after prepare: {input_path}")
            description = input_payload["description"]
            payload = load_json(output_path)
            decisions = payload.get("decisions")
            if (
                payload.get("status") != "completed"
                or payload.get("context_id") != input_payload.get("context_id")
                or payload.get("model") != EXECUTION_MODEL
                or payload.get("reasoning_effort") != EXECUTION_REASONING_EFFORT
                or payload.get("telemetry_status") not in {"available", "unavailable"}
                or not (payload.get("duration_ms") is None or (isinstance(payload.get("duration_ms"), int) and not isinstance(payload.get("duration_ms"), bool) and payload["duration_ms"] >= 0))
                or not (payload.get("total_tokens") is None or (isinstance(payload.get("total_tokens"), int) and not isinstance(payload.get("total_tokens"), bool) and payload["total_tokens"] >= 0))
                or (
                    payload.get("telemetry_status") == "available"
                    and (payload.get("duration_ms") is None or payload.get("total_tokens") is None)
                )
                or (
                    payload.get("telemetry_status") == "unavailable"
                    and (payload.get("duration_ms") is not None or payload.get("total_tokens") is not None)
                )
                or payload.get("return_code") != 0
                or payload.get("timed_out") is not False
                or not isinstance(payload.get("stderr"), str)
                or not isinstance(decisions, list)
                or len(decisions) != 60
            ):
                raise ProductionEvalError(f"direct selection output is incomplete: {output_path}")
            if payload["context_id"] in seen_context_ids:
                raise ProductionEvalError(f"direct selection context_id is reused: {payload['context_id']}")
            seen_context_ids.add(payload["context_id"])
            decisions_by_id = {item.get("id"): item for item in decisions if isinstance(item, dict)}
            if set(decisions_by_id) != set(by_id) or any(
                not isinstance(item.get("selected"), bool)
                or not isinstance(item.get("reason"), str)
                or not item["reason"].strip()
                for item in decisions_by_id.values()
            ):
                raise ProductionEvalError(f"direct selection decisions are invalid: {output_path}")
            run_dir = root / "selection" / configuration / f"run-{repetition}"
            if run_dir.exists():
                shutil.rmtree(run_dir)
            run_dir.mkdir(parents=True, exist_ok=False)
            batch_input = run_dir / "batch-input.json"
            batch_output = run_dir / "batch-output.json"
            shutil.copy2(input_path, batch_input)
            shutil.copy2(output_path, batch_output)
            batch_stderr = run_dir / "batch-stderr.log"
            batch_stderr.write_text(payload["stderr"], encoding="utf-8")
            batch_receipt = {
                "batch_id": expected_batch_id,
                "configuration": configuration,
                "repetition": repetition,
                "status": "completed",
                "provenance": "local-unattested-direct-codex-batch",
                "context_id": payload["context_id"],
                "model": payload["model"],
                "reasoning_effort": payload["reasoning_effort"],
                "telemetry_status": payload["telemetry_status"],
                "duration_ms": payload["duration_ms"],
                "total_tokens": payload.get("total_tokens"),
                "duration_scope": "batch",
                "return_code": payload["return_code"],
                "timed_out": payload["timed_out"],
                "decision_count": len(decisions),
                "input_sha256": sha256_file(batch_input),
                "output_sha256": sha256_file(batch_output),
                "stderr_sha256": sha256_file(batch_stderr),
                "description_sha256": hashlib.sha256(description.encode("utf-8")).hexdigest(),
            }
            write_json(run_dir / "batch-receipt.json", batch_receipt)
            result_items = []
            receipts = []
            for case_id in sorted(by_id):
                case = by_id[case_id]
                decision = decisions_by_id[case_id]
                selected = decision["selected"]
                query_dir = run_dir / "queries" / f"case-{case_id}"
                query_dir.mkdir(parents=True)
                decision_text = f"selected={str(selected).lower()}\nreason={decision['reason']}\n"
                transcript = json.dumps({"type": "assistant", "provenance": "synthetic-from-batch-output", "message": {"content": [{"type": "text", "text": decision_text}]}}, ensure_ascii=False) + "\n"
                (query_dir / "transcript.stream.jsonl").write_text(transcript, encoding="utf-8")
                (query_dir / "stderr.log").write_text("", encoding="utf-8")
                receipt = {
                    "case_id": case_id,
                    "configuration": configuration,
                    "repetition": repetition,
                    "status": "completed",
                    "selected": selected,
                    "should_trigger": case["should_trigger"],
                    "reason": decision["reason"],
                    "duration_ms": None,
                    "duration_scope": "per-case-unavailable",
                    "batch_duration_ms": payload["duration_ms"],
                    "batch_id": expected_batch_id,
                    "batch_input_sha256": batch_receipt["input_sha256"],
                    "batch_output_sha256": batch_receipt["output_sha256"],
                    "batch_receipt_sha256": sha256_file(run_dir / "batch-receipt.json"),
                    "context_id": payload["context_id"],
                    "transcript_provenance": "synthetic-from-batch-output",
                    "requested_model": payload["model"],
                    "model": payload["model"],
                    "reasoning_effort": payload["reasoning_effort"],
                    "telemetry_status": payload["telemetry_status"],
                    "query_sha256": hashlib.sha256(case["query"].encode("utf-8")).hexdigest(),
                    "description_sha256": hashlib.sha256(description.encode("utf-8")).hexdigest(),
                    "transcript_sha256": hashlib.sha256(transcript.encode("utf-8")).hexdigest(),
                    "stderr_sha256": hashlib.sha256(b"").hexdigest(),
                }
                write_json(query_dir / "receipt.json", receipt)
                receipts.append(receipt)
                result_items.append({
                    "query": case["query"],
                    "should_trigger": case["should_trigger"],
                    "trigger_rate": 1.0 if selected else 0.0,
                    "triggers": int(selected),
                    "runs": 1,
                    "pass": selected is case["should_trigger"],
                })
            write_json(run_dir / "result.json", {
                "skill_name": suite["skill_name"],
                "description": description,
                "results": result_items,
                "summary": {"total": 60, "passed": sum(item["pass"] for item in result_items), "failed": sum(not item["pass"] for item in result_items)},
            })
            write_json(run_dir / "receipts.json", {"status": "completed", "batch_receipt": batch_receipt, "receipts": receipts})
            results.append({"configuration": configuration, "run_number": repetition, "status": "completed", "errors": 0})
    report = {"stage": "direct-selection-finalize", "completed_at": utc_now(), "runs": results}
    if not dry_run:
        write_json(root / "selection-status.json", report)
    return report


def completed_pass_rate(run_dir: Path) -> float | None:
    grading_path = run_dir / "grading.json"
    timing_path = run_dir / "timing.json"
    metrics_path = run_dir / "metrics.json"
    if not grading_path.is_file() or not timing_path.is_file() or not metrics_path.is_file():
        return None
    grading = load_json(grading_path)
    timing = load_json(timing_path)
    if (
        timing.get("return_code") != 0
        or timing.get("timed_out") is True
        or grading.get("status") != "completed-independent-grading"
    ):
        return None
    summary = grading.get("summary")
    value = summary.get("pass_rate") if isinstance(summary, dict) else None
    return float(value) if isinstance(value, (int, float)) else None


def description_from_skill(skill_path: Path) -> str:
    content = (skill_path / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---", content, flags=re.DOTALL)
    if not match:
        raise ProductionEvalError(f"snapshot has no YAML frontmatter: {skill_path / 'SKILL.md'}")
    for line in match.group(1).splitlines():
        if line.startswith("description:"):
            return line.split(":", 1)[1].strip()
    raise ProductionEvalError(f"snapshot has no scalar description: {skill_path / 'SKILL.md'}")


def stats(values: Iterable[float | int | None]) -> dict[str, float | None]:
    data = [float(value) for value in values if value is not None]
    if not data:
        return {"mean": None, "stddev": None, "min": None, "max": None}
    mean = sum(data) / len(data)
    variance = sum((value - mean) ** 2 for value in data) / (len(data) - 1) if len(data) > 1 else 0.0
    return {"mean": round(mean, 4), "stddev": round(math.sqrt(variance), 4), "min": round(min(data), 4), "max": round(max(data), 4)}


def grade_status(run_dir: Path, expectations: list[str]) -> tuple[list[dict[str, Any]], str]:
    grading_path = run_dir / "grading.json"
    if grading_path.is_file():
        payload = load_json(grading_path)
        if payload.get("status") != "completed-independent-grading":
            deterministic = payload.get("expectations", []) if isinstance(payload.get("expectations"), list) else []
            pending = payload.get("pending_semantic_expectations", expectations)
            pending_records = [
                {"text": text, "passed": False, "evidence": "pending independent semantic grading"}
                for text in pending
                if isinstance(text, str)
            ]
            return [*deterministic, *pending_records], "pending-independent-grading"
        return payload.get("expectations", []), "grader-provided"
    return ([{"text": text, "passed": False, "evidence": "pending independent grading"} for text in expectations], "pending-independent-grading")


def aggregate_stage(root: Path, suite: dict[str, Any], dry_run: bool) -> dict[str, Any]:
    evals, missing = load_selected_evals(suite)
    behavior_configurations = [str(item["name"]) for item in suite["behavior"]["configurations"]]
    runs: list[dict[str, Any]] = []
    for eval_id in suite["behavior"]["eval_ids"]:
        eval_item = evals.get(eval_id)
        if eval_item is None:
            continue
        for configuration in behavior_configurations:
            for repetition in range(1, int(suite["behavior"]["repetitions"]) + 1):
                run_dir = expected_run_dir(root, eval_item, configuration, repetition)
                if not run_dir.is_dir():
                    continue
                timing = load_json(run_dir / "timing.json") if (run_dir / "timing.json").is_file() else {}
                metrics = load_json(run_dir / "metrics.json") if (run_dir / "metrics.json").is_file() else {}
                grading_payload = load_json(run_dir / "grading.json") if (run_dir / "grading.json").is_file() else {}
                if grading_payload.get("status") in {"execution-error", "runner-error"}:
                    expectations, grading_status = [], "execution-error"
                else:
                    expectations, grading_status = grade_status(run_dir, list(eval_item.get("expectations", [])))
                passed = sum(1 for item in expectations if item.get("passed") is True)
                total = len(expectations)
                execution_valid = (
                    timing.get("return_code") == 0
                    and timing.get("timed_out") is not True
                    and grading_status == "grader-provided"
                )
                runs.append({
                    "eval_id": eval_id,
                    "eval_name": eval_item.get("eval_name", f"eval-{eval_id}"),
                    "configuration": configuration,
                    "run_number": repetition,
                    "result": {"valid": execution_valid, "pass_rate": passed / total if total else None, "passed": passed, "failed": total - passed,
                               "total": total, "time_seconds": timing.get("total_duration_seconds"),
                               "tokens": timing.get("total_tokens"), "tool_calls": metrics.get("total_tool_calls", 0),
                               "errors": metrics.get("errors_encountered", 1)},
                    "expectations": expectations,
                    "notes": [grading_status],
                })
    summary: dict[str, Any] = {}
    for configuration in behavior_configurations:
        subset = [run["result"] for run in runs if run["configuration"] == configuration and run["result"].get("valid") is True]
        summary[configuration] = {"pass_rate": stats(item["pass_rate"] for item in subset),
                                  "time_seconds": stats(item["time_seconds"] for item in subset),
                                  "tokens": stats(item["tokens"] for item in subset)}
    def delta(name: str, digits: int) -> str | None:
        current = summary["with_skill"][name]["mean"]
        without = summary["without_skill"][name]["mean"]
        if current is None or without is None:
            return None
        return f"{current - without:+.{digits}f}"

    summary["delta"] = {"pass_rate": delta("pass_rate", 2), "time_seconds": delta("time_seconds", 1), "tokens": delta("tokens", 0)}
    benchmark = {"metadata": {"skill_name": suite["skill_name"], "skill_path": str(SKILL_ROOT), "executor_model": EXECUTION_MODEL,
                               "reasoning_effort": EXECUTION_REASONING_EFFORT,
                               "timestamp": utc_now(), "evals_run": suite["behavior"]["eval_ids"], "runs_per_configuration": suite["behavior"]["repetitions"],
                               "configurations": behavior_configurations}, "runs": runs, "run_summary": summary,
                 "notes": ["Assertions are pending independent grading unless a run contains grading.json.", *[f"eval {item['eval_id']}: {item['reason']}" for item in missing]]}
    if not dry_run:
        write_json(root / "benchmark.json", benchmark)
    selection_benchmark = aggregate_selection(root, suite)
    if not dry_run:
        write_json(root / "selection-benchmark.json", selection_benchmark)
    return {"stage": "aggregate", "behavior_runs": len(runs), "pending": missing, "selection_status": selection_benchmark["status"]}


def aggregate_selection(root: Path, suite: dict[str, Any]) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    batches: list[dict[str, Any]] = []
    dataset = load_json(SKILL_ROOT / require_relative(str(suite["selection"]["dataset"]), "selection.dataset"))
    risk_by_id = {item["id"]: bool(item.get("high_risk")) for item in dataset if isinstance(item, dict) and isinstance(item.get("id"), int)}
    for config in ("current",):
        for result_path in sorted((root / "selection" / config).glob("run-*/result.json")):
            result = load_json(result_path)
            batch_receipt_path = result_path.parent / "batch-receipt.json"
            if not batch_receipt_path.is_file():
                raise ProductionEvalError(f"selection batch receipt is missing: {batch_receipt_path}")
            batch_receipt = load_json(batch_receipt_path)
            batches.append({
                "configuration": config,
                "repetition": int(result_path.parent.name.removeprefix("run-")),
                "batch_id": batch_receipt.get("batch_id"),
                "receipt": batch_receipt,
                "receipt_sha256": sha256_file(batch_receipt_path),
            })
            values = result.get("results", [])
            for item in values:
                case_id = next((case["id"] for case in dataset if case.get("query") == item.get("query")), None)
                if not isinstance(case_id, int):
                    continue
                selected = bool(item.get("triggers", 0))
                receipt_path = result_path.parent / "queries" / f"case-{case_id}" / "receipt.json"
                if not receipt_path.is_file():
                    raise ProductionEvalError(f"selection receipt is missing: {receipt_path}")
                receipt = load_json(receipt_path)
                if receipt.get("status") != "completed" or receipt.get("selected") is not selected:
                    raise ProductionEvalError(f"selection receipt does not match result: {receipt_path}")
                entries.append({"case_id": case_id, "configuration": config, "repetition": int(result_path.parent.name.removeprefix("run-")), "selected": selected,
                                "should_trigger": bool(item.get("should_trigger")), "high_risk": risk_by_id.get(case_id, False),
                                "source": "local-unattested direct Codex selection judgment", "trigger_count": int(item.get("triggers", 0)), "runs": int(item.get("runs", 1)),
                                "batch_id": receipt.get("batch_id"),
                                "batch_input_sha256": receipt.get("batch_input_sha256"),
                                "batch_output_sha256": receipt.get("batch_output_sha256"),
                                "batch_receipt_sha256": receipt.get("batch_receipt_sha256"),
                                "receipt": receipt, "receipt_sha256": sha256_file(receipt_path)})
    if not entries:
        return {"status": "pending", "reason": "selection-runs-not-available", "dataset": suite["selection"]["dataset"], "runs": []}
    summary: dict[str, Any] = {}
    for config in ("current",):
        values = [item for item in entries if item["configuration"] == config]
        positive = [item for item in values if item["should_trigger"]]
        negative = [item for item in values if not item["should_trigger"]]
        true_positive = sum(item["selected"] for item in positive)
        false_positive = sum(item["selected"] for item in negative)
        true_negative = sum(not item["selected"] for item in negative)
        summary[config] = {"precision": true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0,
                           "recall": true_positive / len(positive) if positive else 0.0,
                           "specificity": true_negative / len(negative) if negative else 0.0,
                           "high_risk_false_positives": sum(item["selected"] for item in negative if item["high_risk"])}
    return {"status": "completed", "dataset": suite["selection"]["dataset"], "runs_per_configuration": suite["selection"]["repetitions"], "batches": batches, "runs": entries, "summary": summary}


def comparison_prepare_stage(root: Path, suite: dict[str, Any], dry_run: bool) -> dict[str, Any]:
    evals, missing = load_selected_evals(suite)
    comparisons_root = root / "comparisons"
    mapping_path = root / ".blind-mapping.json"
    if comparisons_root.exists() or mapping_path.exists():
        raise ProductionEvalError("blind comparison workspace already exists")
    planned: list[dict[str, Any]] = []
    mapping: list[dict[str, Any]] = []
    for eval_id in suite["behavior"]["eval_ids"]:
        eval_item = evals.get(eval_id)
        if eval_item is None:
            continue
        current_runs = {
            f"run-{repetition}": expected_run_dir(root, eval_item, "with_skill", repetition)
            for repetition in range(1, int(suite["behavior"]["repetitions"]) + 1)
            if expected_run_dir(root, eval_item, "with_skill", repetition).is_dir()
        }
        without_skill_runs = {
            f"run-{repetition}": expected_run_dir(root, eval_item, "without_skill", repetition)
            for repetition in range(1, int(suite["behavior"]["repetitions"]) + 1)
            if expected_run_dir(root, eval_item, "without_skill", repetition).is_dir()
        }
        for run_name in sorted(set(current_runs) & set(without_skill_runs)):
            repetition = int(run_name.removeprefix("run-"))
            current_grade = load_json(current_runs[run_name] / "grading.json")
            without_skill_grade = load_json(without_skill_runs[run_name] / "grading.json")
            current_deterministic = load_json(current_runs[run_name] / "deterministic-grading.json")
            without_skill_deterministic = load_json(without_skill_runs[run_name] / "deterministic-grading.json")
            current_timing = load_json(current_runs[run_name] / "timing.json")
            without_skill_timing = load_json(without_skill_runs[run_name] / "timing.json")
            pair_is_valid = all((
                current_grade.get("status") == "completed-independent-grading",
                without_skill_grade.get("status") == "completed-independent-grading",
                current_timing.get("return_code") == 0,
                without_skill_timing.get("return_code") == 0,
                current_timing.get("timed_out") is not True,
                without_skill_timing.get("timed_out") is not True,
            ))
            if not pair_is_valid:
                continue
            current_is_a = secrets.choice((True, False))
            mapping_nonce = secrets.token_hex(16)
            current_side = "A" if current_is_a else "B"
            mapping_commitment = hashlib.sha256(
                f"{eval_id}:{repetition}:{current_side}:{mapping_nonce}".encode("utf-8")
            ).hexdigest()
            pair_dir = comparisons_root / f"eval-{eval_id}-run-{repetition}"
            output_a = current_runs[run_name] / "outputs" if current_is_a else without_skill_runs[run_name] / "outputs"
            output_b = without_skill_runs[run_name] / "outputs" if current_is_a else current_runs[run_name] / "outputs"
            output_a_sha256 = tree_manifest(output_a)["sha256"]
            output_b_sha256 = tree_manifest(output_b)["sha256"]
            forward_context_id = uuid.uuid4().hex
            reversed_context_id = uuid.uuid4().hex
            planned.append({"eval_id": eval_id, "repetition": repetition, "pair_dir": str(pair_dir), "verdict_files": ["comparison-forward.json", "comparison-reversed.json"]})
            mapping.append({"eval_id": eval_id, "repetition": repetition, "current_side": current_side, "nonce": mapping_nonce})
            if dry_run:
                continue
            pair_dir.mkdir(parents=True)
            shutil.copytree(output_a, pair_dir / "A")
            shutil.copytree(output_b, pair_dir / "B")
            def anonymized_grading_summary(
                grading: dict[str, Any], deterministic: dict[str, Any]
            ) -> dict[str, Any]:
                return {
                    "status": grading.get("status"),
                    "deterministic_expectations": deterministic.get("expectations", []),
                    "deterministic_summary": deterministic.get("summary", {}),
                    "semantic_expectations": [
                        item
                        for item in grading.get("expectations", [])
                        if item not in deterministic.get("expectations", [])
                    ],
                    "overall_summary": grading.get("summary", {}),
                }

            write_json(
                pair_dir / "A" / "grading-summary.json",
                anonymized_grading_summary(
                    current_grade if current_is_a else without_skill_grade,
                    current_deterministic if current_is_a else without_skill_deterministic,
                ),
            )
            write_json(
                pair_dir / "B" / "grading-summary.json",
                anonymized_grading_summary(
                    without_skill_grade if current_is_a else current_grade,
                    without_skill_deterministic if current_is_a else current_deterministic,
                ),
            )
            forward_a_manifest = tree_manifest(pair_dir / "A")
            forward_b_manifest = tree_manifest(pair_dir / "B")
            forward_a_sha256 = forward_a_manifest["sha256"]
            forward_b_sha256 = forward_b_manifest["sha256"]
            shutil.copytree(pair_dir / "B", pair_dir / "reversed" / "A")
            shutil.copytree(pair_dir / "A", pair_dir / "reversed" / "B")
            reversed_a_manifest = tree_manifest(pair_dir / "reversed" / "A")
            reversed_b_manifest = tree_manifest(pair_dir / "reversed" / "B")
            reversed_a_sha256 = reversed_a_manifest["sha256"]
            reversed_b_sha256 = reversed_b_manifest["sha256"]
            def portable_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
                return {
                    "exists": manifest.get("exists"),
                    "entries": manifest.get("entries", []),
                    "files": manifest.get("files", {}),
                    "sha256": manifest.get("sha256"),
                }
            write_json(pair_dir / "pair.json", {
                "eval_id": eval_id,
                "repetition": repetition,
                "prompt": eval_item["prompt"],
                "expectations": eval_item.get("expectations", []),
                "output_a_sha256": output_a_sha256,
                "output_b_sha256": output_b_sha256,
                "orientations": {
                    "forward": {
                        "context_id": forward_context_id,
                        "input_a_sha256": forward_a_sha256,
                        "input_b_sha256": forward_b_sha256,
                    },
                    "reversed": {
                        "context_id": reversed_context_id,
                        "input_a_sha256": reversed_a_sha256,
                        "input_b_sha256": reversed_b_sha256,
                    },
                },
                "input_manifests": {
                    "forward": {"A": portable_manifest(forward_a_manifest), "B": portable_manifest(forward_b_manifest)},
                    "reversed": {"A": portable_manifest(reversed_a_manifest), "B": portable_manifest(reversed_b_manifest)},
                },
                "mapping_commitment": mapping_commitment,
                "rubric": {"expectations": eval_item.get("expectations", []), "deterministic_checks_are_authoritative": True},
                "accuracy_policy": "Unsupported numeric, brand, token, or storefront requirements are accuracy failures, not helpful specificity.",
                "verdict_files": ["comparison-forward.json", "comparison-reversed.json"],
            })
    if not dry_run:
        write_json(mapping_path, {"pairs": mapping})
    return {"stage": "compare-prepare", "pairs": planned, "pending": missing}


def comparison_finalize_stage(root: Path, dry_run: bool) -> dict[str, Any]:
    mapping_payload = load_json(root / ".blind-mapping.json")
    mapping = {
        (item["eval_id"], item["repetition"]): item
        for item in mapping_payload.get("pairs", [])
        if isinstance(item, dict)
    }
    pairs: list[dict[str, Any]] = []
    seen_reasoning: set[str] = set()
    for pair_dir in sorted((root / "comparisons").glob("eval-*-run-*")):
        pair = load_json(pair_dir / "pair.json")
        verdicts = []
        for verdict_name in ("comparison-forward.json", "comparison-reversed.json"):
            verdict_path = pair_dir / verdict_name
            if not verdict_path.is_file():
                raise ProductionEvalError(f"blind comparison verdict is missing: {verdict_path}")
            verdict = load_json(verdict_path)
            winner = str(verdict.get("winner", "")).upper()
            if winner not in {"A", "B", "TIE"}:
                raise ProductionEvalError(f"invalid blind comparison winner: {verdict_path}")
            verdicts.append((verdict_name, verdict, winner))
        mapping_record = mapping.get((pair["eval_id"], pair["repetition"]))
        current_side = mapping_record.get("current_side") if isinstance(mapping_record, dict) else None
        if current_side not in {"A", "B"}:
            raise ProductionEvalError(f"blind mapping is missing: {pair_dir}")
        nonce = mapping_record.get("nonce")
        calculated_commitment = hashlib.sha256(
            f"{pair['eval_id']}:{pair['repetition']}:{current_side}:{nonce}".encode("utf-8")
        ).hexdigest()
        if calculated_commitment != pair.get("mapping_commitment"):
            raise ProductionEvalError(f"blind mapping commitment changed: {pair_dir}")
        orientations = pair.get("orientations", {})
        forward_orientation = orientations.get("forward", {}) if isinstance(orientations, dict) else {}
        reversed_orientation = orientations.get("reversed", {}) if isinstance(orientations, dict) else {}
        actual_a_hash = tree_manifest(pair_dir / "A")["sha256"]
        actual_b_hash = tree_manifest(pair_dir / "B")["sha256"]
        actual_reversed_a_hash = tree_manifest(pair_dir / "reversed" / "A")["sha256"]
        actual_reversed_b_hash = tree_manifest(pair_dir / "reversed" / "B")["sha256"]
        if (
            actual_a_hash != forward_orientation.get("input_a_sha256")
            or actual_b_hash != forward_orientation.get("input_b_sha256")
            or actual_reversed_a_hash != reversed_orientation.get("input_a_sha256")
            or actual_reversed_b_hash != reversed_orientation.get("input_b_sha256")
        ):
            raise ProductionEvalError(f"blind comparator input changed after preparation: {pair_dir}")
        side_summaries = {side: load_json(pair_dir / side / "grading-summary.json") for side in ("A", "B")}
        deterministic_scores = {}
        for side, summary in side_summaries.items():
            score = summary.get("deterministic_summary", {}).get("pass_rate")
            deterministic_scores[side] = float(score) if isinstance(score, (int, float)) else None

        def validate_verdict(
            verdict_name: str, verdict: dict[str, Any], winner: str, is_reversed: bool
        ) -> None:
            orientation_name = "reversed" if is_reversed else "forward"
            expected_orientation = orientations.get(orientation_name, {}) if isinstance(orientations, dict) else {}
            if (
                verdict.get("orientation") != orientation_name
                or verdict.get("context_id") != expected_orientation.get("context_id")
                or verdict.get("input_a_sha256") != expected_orientation.get("input_a_sha256")
                or verdict.get("input_b_sha256") != expected_orientation.get("input_b_sha256")
            ):
                raise ProductionEvalError(f"blind comparator verdict is not bound to its {orientation_name} input: {pair_dir / verdict_name}")
            reasoning = verdict.get("reasoning")
            if not isinstance(reasoning, str) or len(reasoning.strip()) < 20:
                raise ProductionEvalError(f"blind comparator reasoning is missing or generic: {pair_dir / verdict_name}")
            normalized_reasoning = re.sub(r"\s+", " ", reasoning.strip().lower())
            if normalized_reasoning in {"a is better", "b is better", "tie", "no difference", "comparable"}:
                raise ProductionEvalError(f"blind comparator reasoning is generic: {pair_dir / verdict_name}")
            references = verdict.get("evidence_references", verdict.get("evidence_refs", verdict.get("evidence")))
            if not isinstance(references, list) or len([item for item in references if isinstance(item, str) and item.strip()]) < 2:
                raise ProductionEvalError(f"blind comparator needs at least two concrete evidence references: {pair_dir / verdict_name}")
            rubric_detail = verdict.get("rubric")
            expectation_detail = verdict.get("expectation_details", verdict.get("expectation_detail"))
            if not rubric_detail or not expectation_detail:
                raise ProductionEvalError(f"blind comparator rubric/expectation detail is missing: {pair_dir / verdict_name}")
            if winner in {"A", "B"}:
                forward_winner = {"A": "B", "B": "A"}[winner] if is_reversed else winner
                selected_score = deterministic_scores.get(forward_winner)
                other_score = deterministic_scores.get("B" if forward_winner == "A" else "A")
                if selected_score is not None and other_score is not None and selected_score + 1e-9 < other_score:
                    raise ProductionEvalError(f"blind comparator verdict contradicts deterministic checks: {pair_dir / verdict_name}")

        for verdict_name, verdict, winner in verdicts:
            validate_verdict(
                verdict_name,
                verdict,
                winner,
                verdict_name == "comparison-reversed.json",
            )
        forward_reasoning = re.sub(r"\s+", " ", str(next(item for name, item, _ in verdicts if name == "comparison-forward.json").get("reasoning", "")).strip().lower())
        reversed_reasoning = re.sub(r"\s+", " ", str(next(item for name, item, _ in verdicts if name == "comparison-reversed.json").get("reasoning", "")).strip().lower())
        if forward_reasoning == reversed_reasoning:
            raise ProductionEvalError(f"blind comparator reused reasoning for forward and reversed views: {pair_dir}")
        if forward_reasoning in seen_reasoning or reversed_reasoning in seen_reasoning:
            raise ProductionEvalError(f"blind comparator reused reasoning across pairs: {pair_dir}")
        seen_reasoning.update({forward_reasoning, reversed_reasoning})
        forward = next(item for name, item, _ in verdicts if name == "comparison-forward.json")
        reversed_verdict = next(item for name, item, _ in verdicts if name == "comparison-reversed.json")
        forward_winner = str(forward["winner"]).upper()
        reversed_winner = str(reversed_verdict["winner"]).upper()
        reversed_as_forward = {"A": "B", "B": "A", "TIE": "TIE"}[reversed_winner]
        winner = forward_winner if forward_winner == reversed_as_forward else "TIE"
        translated = "tie" if winner == "TIE" else ("current" if winner == current_side else "without_skill")
        raw_comparison_sha256 = hashlib.sha256(
            json.dumps({"forward": forward, "reversed": reversed_verdict}, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        pairs.append({
            "eval_id": pair["eval_id"],
            "repetition": pair["repetition"],
            "winner": translated,
            "current_side": current_side,
            "mapping_nonce": nonce,
            "mapping_commitment": pair["mapping_commitment"],
            "raw_winner": winner,
            "raw_comparison": {"forward": forward, "reversed": reversed_verdict},
            "raw_comparison_sha256": raw_comparison_sha256,
            "output_a_sha256": pair["output_a_sha256"],
            "output_b_sha256": pair["output_b_sha256"],
            "forward_input_a_sha256": forward_orientation.get("input_a_sha256"),
            "forward_input_b_sha256": forward_orientation.get("input_b_sha256"),
            "reversed_input_a_sha256": reversed_orientation.get("input_a_sha256"),
            "reversed_input_b_sha256": reversed_orientation.get("input_b_sha256"),
            "forward_context_id": forward_orientation.get("context_id"),
            "reversed_context_id": reversed_orientation.get("context_id"),
            "input_manifests": pair.get("input_manifests"),
            "reasoning": {"forward": forward.get("reasoning"), "reversed": reversed_verdict.get("reasoning")},
        })
    current_wins = sum(item["winner"] == "current" for item in pairs)
    without_skill_wins = sum(item["winner"] == "without_skill" for item in pairs)
    ties = sum(item["winner"] == "tie" for item in pairs)
    total_pairs = len(pairs)
    credited_current_wins = current_wins + ties
    result = {"pairs": pairs, "total_pairs": total_pairs, "current_wins": current_wins,
              "without_skill_wins": without_skill_wins, "ties": ties,
              "credited_current_wins": credited_current_wins, "tie_policy": "credit-current",
              "current_win_rate": credited_current_wins / total_pairs if total_pairs else 0.0}
    if not dry_run:
        write_json(root / "blind-comparison.json", result)
    return {"stage": "compare-finalize", **result}


def review_generator_path() -> Path:
    """Resolve the skill-creator viewer without committing a host-specific path."""
    candidates: list[Path] = []
    configured = os.environ.get("CC_SKILL_CREATOR_PATH")
    if configured:
        configured_path = Path(configured).expanduser()
        candidates.append(
            configured_path
            if configured_path.name == "generate_review.py"
            else configured_path / "eval-viewer" / "generate_review.py"
        )
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        candidates.append(Path(codex_home) / "skills" / "skill-creator" / "eval-viewer" / "generate_review.py")
    candidates.append(Path.home() / ".codex" / "skills" / "skill-creator" / "eval-viewer" / "generate_review.py")
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise ProductionEvalError(
        "skill-creator review generator is unavailable; set CC_SKILL_CREATOR_PATH "
        "to the skill-creator root or generate_review.py"
    )


def review_stage(root: Path, suite: dict[str, Any], dry_run: bool) -> dict[str, Any]:
    benchmark = root / "benchmark.json"
    if not benchmark.is_file():
        raise ProductionEvalError("aggregate stage must produce benchmark.json before review")
    viewer = review_generator_path()
    command = [sys.executable, str(viewer), str(root), "--skill-name", suite["skill_name"], "--benchmark", str(benchmark), "--static", str(root / "review.html")]
    if dry_run:
        return {"stage": "review", "command": command}
    completed = subprocess.run(command, cwd=REPOSITORY_ROOT, text=True, capture_output=True)
    if completed.returncode != 0 or not (root / "review.html").is_file():
        raise ProductionEvalError(f"review generation failed: {(completed.stderr or completed.stdout).strip()}")
    return {"stage": "review", "path": str(root / "review.html"), "sha256": sha256_file(root / "review.html")}


def validate_evidence_candidate(evidence_root: Path, published_root: Path, candidate_path: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="document-writing-evidence-check-") as temporary:
        temporary_root = Path(temporary)
        temporary_skill = temporary_root / "document-writing"

        def ignore(source: str, names: list[str]) -> set[str]:
            ignored = {name for name in names if name in {"__pycache__", ".DS_Store"} or name.endswith(".pyc")}
            if Path(source).resolve() == (SKILL_ROOT / "evals").resolve() and "evidence" in names:
                ignored.add("evidence")
            return ignored

        shutil.copytree(SKILL_ROOT, temporary_skill, ignore=ignore)
        temporary_evidence = temporary_skill / "evals" / "evidence" / published_root.name
        shutil.copytree(evidence_root, temporary_evidence)
        shutil.copy2(candidate_path, temporary_skill / "evals" / "production-evidence.json")
        validation_code = (
            "import pathlib,sys; "
            f"sys.path.insert(0,{str((temporary_skill / 'scripts')).__repr__()}); "
            "import validate_package as v; "
            "r=v.Report(); v.validate_production_evidence(pathlib.Path(sys.argv[1]),r); "
            "print(r.as_json()); raise SystemExit(1 if r.failures else 0)"
        )
        completed = subprocess.run(
            [sys.executable, "-c", validation_code, str(temporary_skill)],
            text=True,
            capture_output=True,
        )
        if completed.returncode != 0:
            raise ProductionEvalError(f"schema-v2 evidence candidate failed validation: {completed.stdout or completed.stderr}")


def evidence_stage(root: Path, suite: dict[str, Any], dry_run: bool) -> dict[str, Any]:
    if root.name == "iteration-8":
        raise ProductionEvalError("iteration-8 is diagnostic-only and cannot be accepted as production evidence")
    benchmark_path = root / "benchmark.json"
    selection_path = root / "selection-benchmark.json"
    if not benchmark_path.is_file() and not dry_run:
        raise ProductionEvalError("aggregate stage must produce benchmark.json before evidence")
    benchmark = load_json(benchmark_path) if benchmark_path.is_file() else {"runs": [], "run_summary": {}}
    selection = load_json(selection_path) if selection_path.is_file() else {"status": "pending", "reason": "selection-benchmark-missing", "runs": [], "summary": {}}
    iteration_metadata = load_json(root / "iteration.json") if (root / "iteration.json").is_file() else {"snapshots": {}}
    current_hash = iteration_metadata.get("snapshots", {}).get("with_skill", {}).get("contract_sha256")
    evidence_dir = SKILL_ROOT / require_relative(str(suite["evidence"]["directory"]), "evidence.directory")
    production_path = SKILL_ROOT / require_relative(str(suite["evidence"]["production_evidence"]), "evidence.production_evidence")
    if dry_run:
        print(json.dumps({"stage": "evidence", "artifact_directory": str(evidence_dir / root.name), "production_evidence": str(production_path)}, ensure_ascii=False, indent=2))
    else:
        if current_hash != contract_hash(SKILL_ROOT):
            raise ProductionEvalError("working-tree contract changed after prepare; start a new iteration")
        valid_behavior_runs = [run for run in benchmark.get("runs", []) if run.get("result", {}).get("valid") is True]
        for eval_id in suite["behavior"]["eval_ids"]:
            for configuration in ("with_skill", "without_skill"):
                count = sum(run.get("eval_id") == eval_id and run.get("configuration") == configuration for run in valid_behavior_runs)
                if count < 2:
                    raise ProductionEvalError(f"evidence requires two valid graded {configuration} runs for eval {eval_id}")
        current_macro = benchmark.get("run_summary", {}).get("with_skill", {}).get("pass_rate", {}).get("mean", 0.0)
        if current_macro < suite["evidence"]["gates"]["macro_pass_rate_min"]:
            raise ProductionEvalError(f"current behavior macro pass rate is below the production gate: {current_macro}")
        for eval_id in (11, 20, 21, 25):
            hard_gate_runs = [
                run
                for run in valid_behavior_runs
                if run.get("configuration") == "with_skill" and run.get("eval_id") == eval_id
            ]
            if not hard_gate_runs or any(run.get("result", {}).get("pass_rate") != 1.0 for run in hard_gate_runs):
                raise ProductionEvalError(f"current hard gate failed for eval {eval_id}")
        if selection.get("status") != "completed" or len(selection.get("runs", [])) != 180:
            raise ProductionEvalError("selection evidence must contain 180 completed case runs")
        current_selection = selection.get("summary", {}).get("current", {})
        for metric in ("precision", "recall", "specificity"):
            if current_selection.get(metric, 0.0) < suite["evidence"]["gates"][f"selection_{metric}_min"]:
                raise ProductionEvalError(f"current selection {metric} is below the production gate")
        if current_selection.get("high_risk_false_positives") != 0:
            raise ProductionEvalError("current selection has a high-risk false positive")
        blind_source = root / "blind-comparison.json"
        if not blind_source.is_file():
            raise ProductionEvalError("blind-comparison.json is missing")
        blind_result = load_json(blind_source)
        if blind_result.get("total_pairs", 0) != 20 or blind_result.get("credited_current_wins", 0) < 19 or blind_result.get("current_win_rate", 0.0) < suite["evidence"]["gates"]["blind_current_win_rate_min"]:
            raise ProductionEvalError("blind comparison does not meet the production gate: requires 20 pairs and at least 19 current wins after ties are credited")
        if not (root / "review.html").is_file() or (root / "review.html").stat().st_size == 0:
            raise ProductionEvalError("static review.html is missing")
        image_manifest_path = root / "image-canary.json"
        if not image_manifest_path.is_file() or load_json(image_manifest_path).get("passed") is not True:
            raise ProductionEvalError("completed image-canary.json is missing")
        published_evidence_root = evidence_dir / root.name
        for stale in evidence_dir.glob(f".{root.name}.staging-*"):
            if stale.is_dir():
                shutil.rmtree(stale)
        evidence_root = evidence_dir / f".{root.name}.staging-{uuid.uuid4().hex[:12]}"
        evidence_root.mkdir(parents=True, exist_ok=True)

        def published_relative(path: Path) -> str:
            published = published_evidence_root / path.relative_to(evidence_root)
            return str(published.relative_to(SKILL_ROOT))
        selection_evidence = json.loads(json.dumps(selection))
        for batch in selection_evidence.get("batches", []):
            raw_configuration = batch.get("configuration")
            repetition = batch.get("repetition")
            source_dir = root / "selection" / str(raw_configuration) / f"run-{repetition}"
            destination_dir = evidence_root / "selection-batches" / f"{raw_configuration}-{repetition}"
            destination_dir.mkdir(parents=True, exist_ok=False)
            for filename, field in (
                ("batch-input.json", "input"),
                ("batch-output.json", "output"),
                ("batch-receipt.json", "receipt"),
                ("batch-stderr.log", "stderr"),
            ):
                source_file = source_dir / filename
                if not source_file.is_file():
                    raise ProductionEvalError(f"selection batch evidence source is missing: {source_file}")
                destination_file = destination_dir / filename
                shutil.copy2(source_file, destination_file)
                batch[f"{field}_path"] = published_relative(destination_file)
                batch[f"{field}_file_sha256"] = sha256_file(destination_file)
        for entry in selection_evidence.get("runs", []):
            raw_configuration = entry.get("configuration")
            repetition = entry.get("repetition")
            case_id = entry.get("case_id")
            source_dir = root / "selection" / str(raw_configuration) / f"run-{repetition}" / "queries" / f"case-{case_id}"
            destination_dir = evidence_root / "selection-runs" / f"{raw_configuration}-{repetition}-{case_id}"
            destination_dir.mkdir(parents=True, exist_ok=False)
            for filename in ("receipt.json", "transcript.stream.jsonl", "stderr.log"):
                source_file = source_dir / filename
                if not source_file.is_file():
                    raise ProductionEvalError(f"selection evidence source is missing: {source_file}")
                destination_file = destination_dir / filename
                shutil.copy2(source_file, destination_file)
                field = filename.split(".", 1)[0].replace("-", "_")
                entry[f"{field}_path"] = published_relative(destination_file)
                entry[f"{field}_file_sha256"] = sha256_file(destination_file)
        behavior_destination = evidence_root / "behavior-results.json"
        selection_destination = evidence_root / "selection-results.json"
        blind_destination = evidence_root / "blind-comparison.json"
        shutil.copy2(benchmark_path, behavior_destination)
        write_json(selection_destination, selection_evidence)
        shutil.copy2(root / "blind-comparison.json", blind_destination)
        artifacts = [
            {"kind": "behavior-results", "path": published_relative(behavior_destination), "sha256": sha256_file(behavior_destination)},
            {"kind": "selection-results", "path": published_relative(selection_destination), "sha256": sha256_file(selection_destination)},
            {"kind": "blind-comparison", "path": published_relative(blind_destination), "sha256": sha256_file(blind_destination)},
        ]
        selection = selection_evidence
        image_manifest_path = root / "image-canary.json"
        if image_manifest_path.is_file():
            image_manifest = load_json(image_manifest_path)
            if image_manifest.get("eval_id") != suite["image_canary"]["eval_id"]:
                raise ProductionEvalError("image canary manifest does not identify eval 24")
            source_relative = require_relative(str(image_manifest.get("source_path", "")), "image canary source_path")
            image_source = root / source_relative
            if not image_source.is_file():
                raise ProductionEvalError(f"image canary source is missing: {image_source}")
            if image_source.name != suite["image_canary"]["artifact_name"]:
                raise ProductionEvalError("image canary artifact name does not match the suite contract")
            image_destination = evidence_root / image_source.name
            shutil.copy2(image_source, image_destination)
            image_artifact = {
                "kind": "image-canary",
                "path": published_relative(image_destination),
                "sha256": sha256_file(image_destination),
            }
            artifacts.append(image_artifact)
            generated_source_relative = require_relative(
                str(image_manifest.get("generated_source_path", "")),
                "image canary generated_source_path",
            )
            generated_source = root / generated_source_relative
            if not generated_source.is_file():
                raise ProductionEvalError(f"image canary generated source is missing: {generated_source}")
            generated_source_destination = evidence_root / "image-canary-generated-source.png"
            shutil.copy2(generated_source, generated_source_destination)
            generated_source_artifact = {
                "kind": "image-canary-source",
                "path": published_relative(generated_source_destination),
                "sha256": sha256_file(generated_source_destination),
            }
            if generated_source_artifact["sha256"] != image_manifest.get("generated_source_sha256"):
                raise ProductionEvalError("image canary generated source hash does not match its manifest")
            artifacts.append(generated_source_artifact)
            document_source_relative = require_relative(
                str(image_manifest.get("document_source_path", "")),
                "image canary document_source_path",
            )
            document_source = root / document_source_relative
            if not document_source.is_dir():
                raise ProductionEvalError(f"image canary document source is missing: {document_source}")
            response_source_relative = require_relative(
                str(image_manifest.get("document_response_path", "")),
                "image canary document_response_path",
            )
            response_source = root / response_source_relative
            if not response_source.is_file():
                raise ProductionEvalError(f"image canary document response is missing: {response_source}")
            document_files = [
                {
                    "path": path.relative_to(document_source).as_posix(),
                    "sha256": sha256_file(path),
                    "content": path.read_text(encoding="utf-8"),
                }
                for path in sorted(document_source.rglob("*.md"))
                if path.is_file()
            ]
            document_bundle_path = evidence_root / "image-canary-document.json"
            write_json(
                document_bundle_path,
                {
                    "document_root": suite["image_canary"]["document_root"],
                    "files": document_files,
                    "tree_sha256": tree_manifest(document_source)["sha256"],
                    "assistant_response": response_source.read_text(encoding="utf-8"),
                    "source_urls": image_manifest.get("source_urls", []),
                },
            )
            document_artifact = {
                "kind": "image-canary-document",
                "path": published_relative(document_bundle_path),
                "sha256": sha256_file(document_bundle_path),
            }
            artifacts.append(document_artifact)
            generation_bundle_path = evidence_root / "image-canary-generation.json"
            write_json(
                generation_bundle_path,
                {
                    "eval_id": image_manifest["eval_id"],
                    "tool": image_manifest.get("generation_tool"),
                    "tool_calls": image_manifest.get("image_tool_calls"),
                    "prompt": image_manifest.get("generation_prompt"),
                    "prompt_sha256": image_manifest.get("generation_prompt_sha256"),
                    "generated_source_sha256": image_manifest.get("generated_source_sha256"),
                    "final_artifact_sha256": image_artifact["sha256"],
                    "artifact_name": image_source.name,
                },
            )
            generation_artifact = {
                "kind": "image-canary-generation",
                "path": published_relative(generation_bundle_path),
                "sha256": sha256_file(generation_bundle_path),
            }
            artifacts.append(generation_artifact)
            image_canary = {
                "passed": image_manifest.get("passed") is True,
                "eval_id": image_manifest.get("eval_id"),
                "artifact_name": image_source.name,
                "artifact_path": image_artifact["path"],
                "sha256": image_artifact["sha256"],
                "width": image_manifest.get("width"),
                "height": image_manifest.get("height"),
                "image_tool_calls": image_manifest.get("image_tool_calls"),
                "generation_tool": image_manifest.get("generation_tool"),
                "generation_prompt_sha256": image_manifest.get("generation_prompt_sha256"),
                "generated_source_sha256": image_manifest.get("generated_source_sha256"),
                "generated_source_artifact_path": generated_source_artifact["path"],
                "generated_source_artifact_sha256": generated_source_artifact["sha256"],
                "document_artifact_path": document_artifact["path"],
                "document_artifact_sha256": document_artifact["sha256"],
                "generation_artifact_path": generation_artifact["path"],
                "generation_artifact_sha256": generation_artifact["sha256"],
            }
        else:
            pending_image = evidence_root / "image-canary-pending.json"
            write_json(pending_image, {"status": "pending", "reason": "image-canary.json is missing"})
            image_artifact = {
                "kind": "image-canary",
                "path": published_relative(pending_image),
                "sha256": sha256_file(pending_image),
            }
            artifacts.append(image_artifact)
            image_canary = {
                "passed": False,
                "eval_id": None,
                "artifact_name": None,
                "artifact_path": image_artifact["path"],
                "sha256": image_artifact["sha256"],
                "width": 0,
                "height": 0,
                "image_tool_calls": 0,
                "generation_tool": None,
                "generation_prompt_sha256": None,
                "generated_source_sha256": None,
                "generated_source_artifact_path": None,
                "generated_source_artifact_sha256": None,
                "document_artifact_path": None,
                "document_artifact_sha256": None,
                "generation_artifact_path": None,
                "generation_artifact_sha256": None,
            }
        review_source = root / "review.html"
        review_destination = evidence_root / "review.html"
        if review_source.is_file() and review_source.stat().st_size > 0:
            shutil.copy2(review_source, review_destination)
            review_artifact = {
                "kind": "review",
                "path": published_relative(review_destination),
                "sha256": sha256_file(review_destination),
            }
            artifacts.append(review_artifact)
            review = {
                "status": "generated",
                "reason": "Static skill-creator review generated from the graded benchmark.",
                "artifact_path": review_artifact["path"],
                "sha256": review_artifact["sha256"],
            }
        else:
            review = {"status": "pending", "reason": "review.html is missing"}
        behavior_runs = []
        evals, _ = load_selected_evals(suite)
        for item in benchmark.get("runs", []):
            if item.get("result", {}).get("valid") is not True:
                continue
            eval_item = evals.get(item.get("eval_id"))
            if eval_item is None:
                continue
            run_dir = expected_run_dir(root, eval_item, item["configuration"], int(item["run_number"]))
            before = load_json(run_dir / "workspace-before.json")
            after = load_json(run_dir / "workspace-after.json")
            timing = load_json(run_dir / "timing.json")
            grading = load_json(run_dir / "grading.json")
            run_copy = evidence_root / "runs" / f"{item['eval_id']}-{item['configuration']}-{item['run_number']}"
            run_copy.mkdir(parents=True, exist_ok=True)
            copied_run_files = {}
            for filename in (
                "direct-task.json",
                "transcript.stream.jsonl",
                "tool-events.json",
                "direct-agent-report.json",
                "eval_metadata.json",
                "assistant-response.md",
                "stderr.log",
                "timing.json",
                "metrics.json",
                "skill-snapshot-before.json",
                "skill-snapshot-after.json",
                "grading.json",
                "deterministic-grading.json",
                "workspace-before.json",
                "workspace-after.json",
            ):
                destination = run_copy / filename
                shutil.copy2(run_dir / filename, destination)
                copied_run_files[filename] = destination
            outputs_root = run_dir / "outputs"
            outputs_manifest = tree_manifest(outputs_root)
            review_bundle = run_copy / "review-output.json"
            write_json(review_bundle, {
                **outputs_manifest,
                "contents": {
                    relative: (outputs_root / relative).read_text(encoding="utf-8")
                    for relative in outputs_manifest["files"]
                },
            })
            copied_run_files["review-output.json"] = review_bundle
            before_state = manifest_state(before)
            after_state = manifest_state(after)
            changed = actual_changed_file_paths(before, after)
            configured_allowed = list(case_contract(int(item["eval_id"]), suite).get("allowed_change_paths", []))
            execution_completed = (
                timing.get("return_code") == 0
                and timing.get("timed_out") is not True
            )
            behavior_runs.append({"eval_id": item["eval_id"], "configuration": "current" if item["configuration"] == "with_skill" else "without_skill",
                                  "repetition": item["run_number"], "workspace_before_sha256": before["sha256"], "workspace_after_sha256": after["sha256"],
                                  "context_id": timing.get("context_id"),
                                  "output_tree_sha256": after["sha256"], "allowed_changes": configured_allowed,
                                  "allowed_change_patterns": configured_allowed, "actual_changes": changed,
                                  "output_tree": sorted(after_state), "execution_completed": execution_completed,
                                  "review_output_sha256": outputs_manifest["sha256"],
                                  "review_output_path": published_relative(review_bundle),
                                  "review_output_file_sha256": sha256_file(review_bundle),
                                  "transcript_path": published_relative(copied_run_files["transcript.stream.jsonl"]),
                                  "transcript_sha256": sha256_file(copied_run_files["transcript.stream.jsonl"]),
                                  "transcript_provenance": "reconstructed-from-direct-agent-report",
                                  "tool_events_path": published_relative(copied_run_files["tool-events.json"]),
                                  "tool_events_sha256": sha256_file(copied_run_files["tool-events.json"]),
                                  "tool_event_provenance": "agent-reported-not-raw-telemetry",
                                  "direct_agent_report_path": published_relative(copied_run_files["direct-agent-report.json"]),
                                  "direct_agent_report_sha256": sha256_file(copied_run_files["direct-agent-report.json"]),
                                  "direct_task_path": published_relative(copied_run_files["direct-task.json"]),
                                  "direct_task_sha256": sha256_file(copied_run_files["direct-task.json"]),
                                  "eval_metadata_path": published_relative(copied_run_files["eval_metadata.json"]),
                                  "eval_metadata_sha256": sha256_file(copied_run_files["eval_metadata.json"]),
                                  "response_path": published_relative(copied_run_files["assistant-response.md"]),
                                  "response_sha256": sha256_file(copied_run_files["assistant-response.md"]),
                                  "stderr_path": published_relative(copied_run_files["stderr.log"]),
                                  "stderr_sha256": sha256_file(copied_run_files["stderr.log"]),
                                  "timing_path": published_relative(copied_run_files["timing.json"]),
                                  "timing_sha256": sha256_file(copied_run_files["timing.json"]),
                                  "metrics_path": published_relative(copied_run_files["metrics.json"]),
                                  "metrics_sha256": sha256_file(copied_run_files["metrics.json"]),
                                  "skill_snapshot_before_path": published_relative(copied_run_files["skill-snapshot-before.json"]),
                                  "skill_snapshot_before_sha256": sha256_file(copied_run_files["skill-snapshot-before.json"]),
                                  "skill_snapshot_after_path": published_relative(copied_run_files["skill-snapshot-after.json"]),
                                  "skill_snapshot_after_sha256": sha256_file(copied_run_files["skill-snapshot-after.json"]),
                                  "grading_path": published_relative(copied_run_files["grading.json"]),
                                  "grading_sha256": sha256_file(copied_run_files["grading.json"]),
                                  "deterministic_grading_path": published_relative(copied_run_files["deterministic-grading.json"]),
                                  "deterministic_grading_sha256": sha256_file(copied_run_files["deterministic-grading.json"]),
                                  "before_manifest_path": published_relative(copied_run_files["workspace-before.json"]),
                                  "before_manifest_sha256": sha256_file(copied_run_files["workspace-before.json"]),
                                  "after_manifest_path": published_relative(copied_run_files["workspace-after.json"]),
                                  "after_manifest_sha256": sha256_file(copied_run_files["workspace-after.json"]),
                                  "model": str(timing.get("model") or EXECUTION_MODEL), "reasoning_effort": timing.get("reasoning_effort", EXECUTION_REASONING_EFFORT),
                                  "telemetry_status": timing.get("telemetry_status"),
                                  "duration_ms": int(float(timing["total_duration_seconds"]) * 1000) if timing.get("total_duration_seconds") is not None else None,
                                  "total_tokens": timing.get("total_tokens"), "grading": grading})
        behavior_context_ids = [run.get("context_id") for run in behavior_runs]
        if (
            len(behavior_runs) != 40
            or any(not isinstance(value, str) or not value.strip() for value in behavior_context_ids)
            or len(set(behavior_context_ids)) != 40
        ):
            raise ProductionEvalError("production evidence requires 40 unique one-run behavior context IDs")
        summary = benchmark.get("run_summary", {})
        hard_gate_ids = {"existing-document-preservation": 11, "review-no-mutation": 20, "collision-no-overwrite": 21, "web-unavailable-no-hallucination": 25}
        hard_gates = {
            configuration: {
                name: all(
                    run["result"]["pass_rate"] == 1.0
                    for run in benchmark.get("runs", [])
                    if run["configuration"] == configuration
                    and run["eval_id"] == eval_id
                    and run.get("result", {}).get("valid") is True
                )
                for name, eval_id in hard_gate_ids.items()
            }
            for configuration in ("with_skill", "without_skill")
        }
        selection_summary = selection.get("summary", {})
        evidence = {"schema_version": int(suite["evidence"]["schema_version"]), "trust_boundary": "local-unattested", "generated_at": datetime.now(timezone.utc).date().isoformat(), "iteration": int(root.name.removeprefix("iteration-")),
                    "contract_sha256": current_hash,
                    "runtime": {"runner": "scripts/run_production_evals.py", "command": suite["runtime"]["command"], "model": EXECUTION_MODEL, "reasoning_effort": EXECUTION_REASONING_EFFORT},
                    "artifacts": artifacts, "behavior_benchmark": {"path": artifacts[0]["path"], "sha256": artifacts[0]["sha256"]},
                    "selection_benchmark": {"path": artifacts[1]["path"], "sha256": artifacts[1]["sha256"]},
                    "behavior": {"runs": behavior_runs, "summary": {"current": {"macro_pass_rate": summary.get("with_skill", {}).get("pass_rate", {}).get("mean"), "hard_gates_passed": all(hard_gates["with_skill"].values()), "hard_gates": hard_gates["with_skill"]},
                                                                            "without_skill": {"macro_pass_rate": summary.get("without_skill", {}).get("pass_rate", {}).get("mean"), "hard_gates_passed": all(hard_gates["without_skill"].values()), "hard_gates": hard_gates["without_skill"]}}},
                    "selection": {"runs": [{**item, "configuration": "current"}
                                           for item in selection.get("runs", [])],
                                  "batches": [{**item, "configuration": "current"}
                                              for item in selection.get("batches", [])],
                                  "summary": {"current": selection_summary.get("current", {})}},
                    "blind_comparison": load_json(root / "blind-comparison.json") if (root / "blind-comparison.json").is_file() else {"total_pairs": 0, "current_wins": 0, "without_skill_wins": 0, "ties": 0, "credited_current_wins": 0, "tie_policy": "credit-current", "current_win_rate": 0.0},
                    "review": review,
                    "image_canary": image_canary,
                    "limitations": [
                        "Execution receipts are locally recorded and internally cross-checked, not cryptographically attested by a remote evaluator.",
                        "Behavior tool events are explicit agent-reported capability claims, not raw Codex platform telemetry; reconstructed transcripts preserve that provenance.",
                        "This host does not attest physical per-subagent tool removal; denied-capability evidence is policy-bound and checked against recorded events.",
                        "Selection case transcripts are synthetic projections of three locally recorded batch judgments; original batch inputs, outputs, context identifiers, durations, and hashes are published separately.",
                        "Live storefront requirements are time-sensitive and must be reopened when a document is generated or refreshed.",
                        "CI validates committed artifacts and negative controls but does not rerun external models, live web research, or image generation.",
                    ]}
        write_json(evidence_root / "summary.json", evidence)
        descriptor, candidate_name = tempfile.mkstemp(prefix="document-writing-production-evidence-", suffix=".json")
        os.close(descriptor)
        candidate_path = Path(candidate_name)
        write_json(candidate_path, evidence)
        replace_path = production_path.parent / ".production-evidence.replace.tmp"
        backup_evidence_root = evidence_dir / f".{root.name}.backup-{uuid.uuid4().hex[:12]}"
        evidence_swapped = False
        try:
            validate_evidence_candidate(evidence_root, published_evidence_root, candidate_path)
            if published_evidence_root.exists():
                os.replace(published_evidence_root, backup_evidence_root)
            os.replace(evidence_root, published_evidence_root)
            evidence_swapped = True
            write_json(replace_path, evidence)
            os.replace(replace_path, production_path)
            if backup_evidence_root.exists():
                shutil.rmtree(backup_evidence_root)
        except Exception:
            if evidence_swapped and published_evidence_root.exists():
                shutil.rmtree(published_evidence_root)
            if backup_evidence_root.exists():
                os.replace(backup_evidence_root, published_evidence_root)
            raise
        finally:
            if candidate_path.exists():
                candidate_path.unlink()
            if replace_path.exists():
                replace_path.unlink()
            if evidence_root.exists():
                shutil.rmtree(evidence_root)
    return {"stage": "evidence", "status": "completed", "evidence": str(evidence_dir / root.name / "summary.json")}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("prepare", "direct-behavior-prepare", "direct-behavior-finalize", "direct-selection-prepare", "direct-selection-finalize", "aggregate", "compare-prepare", "compare-finalize", "review", "evidence"), default="prepare")
    parser.add_argument("--iteration", type=int, help="Existing iteration for non-prepare stages; defaults to the latest or next iteration.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned external commands without invoking them or writing artifacts.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        suite = load_json(SUITE_PATH)
        workspace = suite_workspace(suite)
        iteration = args.iteration or (next_iteration(workspace) if args.stage == "prepare" else next_iteration(workspace) - 1)
        if args.stage == "prepare":
            root = prepare_iteration(suite, iteration, args.dry_run)
        else:
            root = iteration_root(workspace, iteration)
            if not root.is_dir():
                raise ProductionEvalError(f"iteration does not exist; run --stage prepare first: {root}")
        reports = []
        if args.stage == "direct-behavior-prepare":
            reports.append(direct_behavior_prepare_stage(root, suite, args.dry_run))
        if args.stage == "direct-behavior-finalize":
            reports.append(direct_behavior_finalize_stage(root, suite, args.dry_run))
        if args.stage == "direct-selection-prepare":
            reports.append(direct_selection_prepare_stage(root, suite, args.dry_run))
        if args.stage == "direct-selection-finalize":
            reports.append(direct_selection_finalize_stage(root, suite, args.dry_run))
        if args.stage == "aggregate":
            reports.append(aggregate_stage(root, suite, args.dry_run))
        if args.stage == "compare-prepare":
            reports.append(comparison_prepare_stage(root, suite, args.dry_run))
        if args.stage == "compare-finalize":
            reports.append(comparison_finalize_stage(root, args.dry_run))
        if args.stage == "review":
            reports.append(review_stage(root, suite, args.dry_run))
        if args.stage == "evidence":
            reports.append(evidence_stage(root, suite, args.dry_run))
        print(json.dumps({"status": "ok", "iteration": str(root), "reports": reports}, ensure_ascii=False, indent=2))
        failed_runs = [
            run
            for report in reports
            for run in report.get("runs", [])
            if isinstance(run, dict) and run.get("status") in {"execution-error", "runner-error"}
        ]
        return EXIT_FAILURE if failed_runs else EXIT_OK
    except ProductionEvalError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except OSError as exc:
        print(f"error: unexpected filesystem or process error: {exc}", file=sys.stderr)
        return EXIT_FAILURE


if __name__ == "__main__":
    raise SystemExit(main())
