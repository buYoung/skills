#!/usr/bin/env python3
"""Run current-only schema-v3 document-writing evaluations.

Workers receive one embedded task contract and write only the user response plus
allowlisted workspace outputs. The harness derives receipts from files. Separate
fresh graders score semantic expectations. Baselines, repetitions, worker
self-reports, selection execution, and blind comparison are intentionally absent.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tarfile
import tempfile
import uuid
import zlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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
EXECUTION_RECEIPT_SCHEMA_VERSION = 3
GRADING_SCHEMA_VERSION = 3
HARD_GATE_EVAL_IDS = {
    "direction-approval-no-premature-write": (10, 12),
    "existing-document-preservation": (11,),
    "review-no-mutation": (20,),
    "collision-no-overwrite": (21,),
    "web-unavailable-no-hallucination": (25,),
    "qualitative-feedback-translation": (29,),
    "cross-context-consistency-not-sameness": (30,),
    "focused-update-propagation": (31,),
    "contradictory-preference-convergence": (32,),
}


class ProductionEvalError(RuntimeError):
    """Raised when the evaluation contract cannot be executed safely."""


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


def require_relative(value: str, label: str) -> Path:
    path = Path(value)
    if not value.strip() or path.is_absolute() or path == Path(".") or ".." in path.parts:
        raise ProductionEvalError(f"{label} must be a normalized repository-relative path: {value!r}")
    return path


def tree_manifest(root: Path) -> dict[str, Any]:
    entries: list[dict[str, str]] = []
    files: dict[str, str] = {}
    if not root.exists():
        return {
            "workspace_root": str(root),
            "root": str(root),
            "exists": False,
            "entries": [],
            "files": {},
            "sha256": hashlib.sha256(b"").hexdigest(),
        }
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            entry = {"path": relative, "type": "symlink", "target": os.readlink(path)}
        elif path.is_file():
            digest = sha256_file(path)
            entry = {"path": relative, "type": "file", "sha256": digest}
            files[relative] = digest
        elif path.is_dir():
            entry = {"path": relative, "type": "directory"}
        else:
            entry = {"path": relative, "type": "special"}
        entries.append(entry)
    encoded = json.dumps(entries, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return {
        "workspace_root": str(root),
        "root": str(root),
        "exists": True,
        "entries": entries,
        "files": files,
        "sha256": hashlib.sha256(encoded).hexdigest(),
    }


def manifest_state(manifest: dict[str, Any]) -> dict[str, str]:
    return {
        entry["path"]: (f"file:{entry.get('sha256')}" if entry.get("type") == "file" else str(entry.get("type")))
        for entry in manifest.get("entries", [])
        if isinstance(entry, dict) and isinstance(entry.get("path"), str)
    }


def actual_changed_file_paths(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
    before_state = manifest_state(before)
    after_state = manifest_state(after)
    changed: list[str] = []
    for path in sorted(set(before_state) | set(after_state)):
        if before_state.get(path) == after_state.get(path):
            continue
        state = after_state.get(path) or before_state.get(path) or ""
        if state.startswith("file:"):
            changed.append(path)
    return changed


def suite_workspace(suite: dict[str, Any]) -> Path:
    if suite.get("workspace") != "../document-writing-workspace":
        raise ProductionEvalError("workspace must be ../document-writing-workspace")
    workspace = (SKILL_ROOT / ".." / "document-writing-workspace").resolve()
    if workspace.parent != SKILL_ROOT.parent.resolve():
        raise ProductionEvalError("workspace must be the ignored sibling of document-writing")
    return workspace


def next_iteration(workspace: Path) -> int:
    values = [
        int(path.name.removeprefix("iteration-"))
        for path in workspace.glob("iteration-*")
        if path.is_dir() and path.name.removeprefix("iteration-").isdigit()
    ]
    return max(values, default=0) + 1


def iteration_root(workspace: Path, iteration: int) -> Path:
    return workspace / f"iteration-{iteration}"


def git_archive(ref: str, destination: Path) -> None:
    completed = subprocess.run(
        ["git", "archive", "--format=tar", ref, "skills/document-writing"],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise ProductionEvalError(completed.stderr.decode("utf-8", errors="replace").strip())
    destination.mkdir(parents=True)
    with tempfile.NamedTemporaryFile(suffix=".tar") as archive_file:
        archive_file.write(completed.stdout)
        archive_file.flush()
        with tarfile.open(archive_file.name) as archive:
            members = archive.getmembers()
            if any(member.name.startswith("/") or ".." in Path(member.name).parts for member in members):
                raise ProductionEvalError("git archive contains an unsafe path")
            archive.extractall(destination, members=members)
    extracted = destination / "skills" / "document-writing"
    if not extracted.is_dir():
        raise ProductionEvalError("git archive did not contain document-writing")
    shutil.move(str(extracted), str(destination / "document-writing"))
    shutil.rmtree(destination / "skills")


def overlay_working_tree(snapshot_root: Path) -> None:
    shutil.copytree(
        SKILL_ROOT,
        snapshot_root / "document-writing",
        dirs_exist_ok=True,
        symlinks=True,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"),
    )


def contract_hash(skill_path: Path) -> str:
    files = [skill_path / "SKILL.md"]
    files.extend(path for path in (skill_path / "scripts").glob("*.py") if path.name != "validate_fdd.py")
    files.extend((skill_path / "references" / "document-types" / "design-system").rglob("*.md"))
    files.extend(
        skill_path / "references" / "shared" / name
        for name in ("human-readable-writing.md", "source-grounding.md", "existing-document-edits.md")
    )
    files.extend((skill_path / "evals").rglob("*"))
    included = [
        path
        for path in files
        if path.is_file()
        and path.relative_to(skill_path).as_posix() != "evals/production-evidence.json"
        and path.relative_to(skill_path).as_posix() not in {"evals/evals.json", "evals/trigger-evals.json"}
        and not path.relative_to(skill_path).as_posix().startswith("evals/evidence/")
    ]
    digest = hashlib.sha256()
    for path in sorted(set(included)):
        digest.update(path.relative_to(skill_path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    manifest = load_json(skill_path / "evals" / "evals.json")
    suite = load_json(skill_path / "evals" / "production-suite.json")
    selected = set(suite.get("behavior", {}).get("eval_ids", []))
    subset = {
        "skill_name": manifest.get("skill_name"),
        "evals": [item for item in manifest.get("evals", []) if isinstance(item, dict) and item.get("id") in selected],
    }
    digest.update(b"evals/evals.design-system.json\0")
    digest.update(json.dumps(subset, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    digest.update(b"\0")
    return digest.hexdigest()


def prepare_iteration(suite: dict[str, Any], iteration: int, eval_ids: list[int] | None, dry_run: bool) -> Path:
    workspace = suite_workspace(suite)
    root = iteration_root(workspace, iteration)
    if root.exists():
        raise ProductionEvalError(f"iteration already exists: {root}")
    all_eval_ids = list(suite["behavior"]["eval_ids"])
    selected = all_eval_ids if eval_ids is None else eval_ids
    if not selected or len(set(selected)) != len(selected) or any(value not in all_eval_ids for value in selected):
        raise ProductionEvalError("--eval-ids must be a unique non-empty subset of the production suite")
    scope_kind = "production" if selected == all_eval_ids else "targeted"
    if dry_run:
        return root
    root.mkdir(parents=True)
    snapshots = root / "snapshots"
    git_archive("HEAD", snapshots / CURRENT_SNAPSHOT)
    overlay_working_tree(snapshots / CURRENT_SNAPSHOT)
    write_json(
        root / "iteration.json",
        {
            "schema_version": 3,
            "iteration": iteration,
            "prepared_at": utc_now(),
            "suite_path": str(SUITE_PATH.relative_to(REPOSITORY_ROOT)),
            "evaluation_scope": {"kind": scope_kind, "eval_ids": selected},
            "snapshot": {
                "path": "snapshots/with-skill/document-writing",
                "contract_sha256": contract_hash(snapshots / CURRENT_SNAPSHOT / "document-writing"),
            },
        },
    )
    return root


def iteration_scope(root: Path, suite: dict[str, Any]) -> tuple[str, list[int]]:
    metadata = load_json(root / "iteration.json")
    scope = metadata.get("evaluation_scope")
    if not isinstance(scope, dict) or scope.get("kind") not in {"production", "targeted"}:
        raise ProductionEvalError("iteration evaluation scope is invalid")
    eval_ids = scope.get("eval_ids")
    if not isinstance(eval_ids, list) or not eval_ids or any(not isinstance(value, int) for value in eval_ids):
        raise ProductionEvalError("iteration eval_ids are invalid")
    if any(value not in suite["behavior"]["eval_ids"] for value in eval_ids):
        raise ProductionEvalError("iteration contains an eval outside the suite")
    return str(scope["kind"]), eval_ids


def selected_evals(root: Path, suite: dict[str, Any], eval_id: int | None = None) -> list[dict[str, Any]]:
    _kind, scope_ids = iteration_scope(root, suite)
    if eval_id is not None:
        if eval_id not in scope_ids:
            raise ProductionEvalError(f"eval {eval_id} is outside this iteration scope")
        scope_ids = [eval_id]
    manifest = load_json(SKILL_ROOT / suite["behavior"]["eval_manifest"])
    by_id = {item.get("id"): item for item in manifest.get("evals", []) if isinstance(item, dict)}
    missing = [value for value in scope_ids if value not in by_id]
    if missing:
        raise ProductionEvalError(f"eval IDs are missing from evals.json: {missing}")
    return [by_id[value] for value in scope_ids]


def behavior_job_id(eval_id: int) -> str:
    identity = f"document-writing-behavior:{eval_id}:with_skill:1"
    return f"job-{hashlib.sha256(identity.encode('utf-8')).hexdigest()[:24]}"


def expected_run_dir(root: Path, eval_id: int) -> Path:
    return root / "behavior" / behavior_job_id(eval_id)


def copy_execution_skill(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    shutil.copy2(source / "SKILL.md", destination / "SKILL.md")
    shutil.copytree(source / "references", destination / "references", symlinks=True)
    (destination / "scripts").mkdir()
    for name in ("validate_fdd.py", "validate_design_system_output.py"):
        source_file = source / "scripts" / name
        if source_file.is_file():
            shutil.copy2(source_file, destination / "scripts" / name)


def skill_snapshot_manifest(skill_path: Path, source_contract_sha256: str) -> dict[str, Any]:
    manifest = tree_manifest(skill_path)
    return {"kind": "with-skill", "exists": True, "sha256": manifest["sha256"], "source_contract_sha256": source_contract_sha256}


def destination_for_fixture(eval_id: int, suite: dict[str, Any]) -> Path:
    value = suite["behavior"].get("fixture_destinations", {}).get(str(eval_id), "input")
    return require_relative(str(value), f"fixture destination for eval {eval_id}")


def fixture_root_for_eval(eval_item: dict[str, Any]) -> Path | None:
    roots: set[Path] = set()
    for value in eval_item.get("files", []):
        relative = require_relative(str(value), "fixture file")
        if "fixtures" in relative.parts:
            index = relative.parts.index("fixtures")
            roots.add(Path(*relative.parts[: index + 2]))
    return SKILL_ROOT / next(iter(roots)) if len(roots) == 1 else None


def copy_fixtures(eval_item: dict[str, Any], workspace: Path, suite: dict[str, Any]) -> None:
    if not eval_item.get("files"):
        return
    fixture_root = fixture_root_for_eval(eval_item)
    if fixture_root is None or not fixture_root.is_dir():
        raise ProductionEvalError(f"eval {eval_item['id']} fixture root is invalid")
    destination = workspace / destination_for_fixture(int(eval_item["id"]), suite)
    shutil.copytree(fixture_root, destination, dirs_exist_ok=False, symlinks=True)


def case_contract(eval_id: int, suite: dict[str, Any]) -> dict[str, Any]:
    contract = suite["behavior"].get("case_contracts", {}).get(str(eval_id))
    if not isinstance(contract, dict):
        raise ProductionEvalError(f"case contract is missing for eval {eval_id}")
    return contract


def public_direct_task(
    job_id: str,
    prompt: str,
    run_dir: Path,
    workspace: Path,
    response_path: Path,
    task_context_id: str,
    skill_path: Path,
    execution_policy: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": 3,
        "job_id": job_id,
        "prompt": prompt,
        "run_dir": str(run_dir),
        "workspace": str(workspace),
        "response_path": str(response_path),
        "skill_path": str(skill_path),
        "model": EXECUTION_MODEL,
        "reasoning_effort": EXECUTION_REASONING_EFFORT,
        "task_context_id": task_context_id,
        "execution_policy": execution_policy,
    }


def worker_dispatch_message(task: dict[str, Any]) -> str:
    task_json = json.dumps(task, ensure_ascii=False, indent=2)
    return (
        "Execute exactly the authoritative task JSON embedded below. Do not retype or infer a task-file path, "
        "inspect sibling runs, package evals, manifests, grading, prior evidence, or unrelated global skills. Do not spawn "
        "subagents. Read skill_path/SKILL.md completely and only the relevant references it routes to. A capability "
        "skill may be used only when execution_policy.required_capabilities explicitly names that capability. "
        "workspace_read_policy applies to reads; allowed_workspace_paths and allowed_workspace_write_paths restrict writes only. "
        "Meet any response_contract exactly. Write only response_path and workspace files permitted by execution_policy. Do not create an audit report, receipt, "
        "telemetry, tool-event log, or changed-path list.\n\nAUTHORITATIVE_TASK_JSON\n```json\n"
        f"{task_json}\n```"
    )


def execution_policy_for_case(contract: dict[str, Any]) -> dict[str, Any]:
    allowed = list(contract.get("allowed_change_paths", []))
    response_rules = contract.get("response") if isinstance(contract.get("response"), dict) else {}
    response_contract = {
        key: response_rules[key]
        for key in ("min_questions", "max_questions")
        if isinstance(response_rules.get(key), int) and not isinstance(response_rules.get(key), bool)
    }
    policy = {
        "skill_access": "supplied_snapshot_only",
        "workspace_read_policy": "entire_workspace",
        "workspace_write_policy": "disabled" if contract.get("deny_write_tools") is True or not allowed else "allowlisted",
        "allowed_workspace_paths": allowed,
        "allowed_workspace_write_paths": allowed,
        "required_capabilities": list(contract.get("required_capabilities", [])),
        "denied_capabilities": list(contract.get("denied_capabilities", [])),
        "rules": [
            "Use only the embedded task contract, its workspace, and its supplied skill snapshot, except for a capability skill explicitly named by required_capabilities.",
            "Read the entire workspace when needed; allowed_workspace_paths limits writes only and never limits reads.",
            "For an existing-set revision, inventory every workspace file and follow index, approval, change, decision, and governance owners before claiming evidence is unavailable.",
            "Write workspace files only when the policy is allowlisted and only under allowed_workspace_write_paths.",
            "Write the final user-facing answer to response_path and satisfy response_contract exactly when present.",
            "Do not create execution evidence or self-report capability use.",
        ],
    }
    if response_contract:
        policy["response_contract"] = response_contract
    return policy


def direct_behavior_prepare_stage(root: Path, suite: dict[str, Any], eval_id: int | None, dry_run: bool) -> dict[str, Any]:
    tasks: list[dict[str, Any]] = []
    source_skill = root / "snapshots" / CURRENT_SNAPSHOT / "document-writing"
    source_contract_sha256 = contract_hash(source_skill)
    for eval_item in selected_evals(root, suite, eval_id):
        current_eval_id = int(eval_item["id"])
        run_dir = expected_run_dir(root, current_eval_id)
        contract = case_contract(current_eval_id, suite)
        policy = execution_policy_for_case(contract)
        task = public_direct_task(
            behavior_job_id(current_eval_id),
            str(eval_item["prompt"]),
            run_dir,
            run_dir / "workspace",
            run_dir / "direct-response.md",
            uuid.uuid4().hex,
            run_dir / "skill-snapshot",
            policy,
        )
        dispatch = worker_dispatch_message(task)
        tasks.append({"eval_id": current_eval_id, "job_id": task["job_id"], "task": task, "dispatch_message": dispatch})
        if dry_run:
            continue
        if run_dir.exists():
            raise ProductionEvalError(f"behavior run already exists: {run_dir}")
        run_dir.mkdir(parents=True)
        copy_execution_skill(source_skill, run_dir / "skill-snapshot")
        write_json(run_dir / "skill-snapshot-before.json", skill_snapshot_manifest(run_dir / "skill-snapshot", source_contract_sha256))
        (run_dir / "workspace").mkdir()
        copy_fixtures(eval_item, run_dir / "workspace", suite)
        before = tree_manifest(run_dir / "workspace")
        write_json(run_dir / "workspace-before.json", before)
        write_json(run_dir / "before-manifest.json", before)
        write_json(run_dir / "direct-task.json", task)
        write_json(
            run_dir / "worker-dispatch.json",
            {
                "schema_version": 3,
                "provenance": "harness-generated-embedded-task",
                "eval_id": current_eval_id,
                "task_sha256": sha256_file(run_dir / "direct-task.json"),
                "dispatch_message": dispatch,
            },
        )
    return {"stage": "direct-behavior-prepare", "tasks": tasks}


def build_harness_execution_receipt(
    task: dict[str, Any], response_path: Path, before: dict[str, Any], after: dict[str, Any]
) -> dict[str, Any]:
    if not response_path.is_file() or not response_path.read_text(encoding="utf-8").strip():
        raise ProductionEvalError(f"response is missing or empty: {response_path}")
    return {
        "schema_version": EXECUTION_RECEIPT_SCHEMA_VERSION,
        "provenance": "harness-derived-from-task-response-and-manifests",
        "status": "completed",
        "task_context_id": task.get("task_context_id"),
        "model": task.get("model"),
        "reasoning_effort": task.get("reasoning_effort"),
        "response_sha256": sha256_file(response_path),
        "workspace_before_sha256": before.get("sha256"),
        "workspace_after_sha256": after.get("sha256"),
        "produced_paths": actual_changed_file_paths(before, after),
        "telemetry": {"status": "unavailable", "duration_ms": None, "total_tokens": None},
        "capability_evidence": {"status": "unverified", "events": []},
    }


def validate_harness_execution_receipt(
    receipt: dict[str, Any], task: dict[str, Any], before: dict[str, Any], after: dict[str, Any]
) -> list[str]:
    failures: list[str] = []
    changed = actual_changed_file_paths(before, after)
    policy = task.get("execution_policy") if isinstance(task.get("execution_policy"), dict) else {}
    allowed = policy.get("allowed_workspace_paths")
    if receipt.get("schema_version") != 3 or receipt.get("provenance") != "harness-derived-from-task-response-and-manifests":
        failures.append("execution receipt schema or provenance is invalid")
    for field in ("task_context_id", "model", "reasoning_effort"):
        if receipt.get(field) != task.get(field):
            failures.append(f"execution receipt {field} does not match task")
    if receipt.get("status") != "completed":
        failures.append("execution receipt status is not completed")
    if receipt.get("workspace_before_sha256") != before.get("sha256") or receipt.get("workspace_after_sha256") != after.get("sha256"):
        failures.append("execution receipt workspace hashes do not match manifests")
    if receipt.get("produced_paths") != changed:
        failures.append("execution receipt produced_paths do not match manifest diff")
    if receipt.get("telemetry") != {"status": "unavailable", "duration_ms": None, "total_tokens": None}:
        failures.append("unavailable telemetry must remain null")
    if receipt.get("capability_evidence") != {"status": "unverified", "events": []}:
        failures.append("missing raw capability evidence must remain unverified")
    if policy.get("workspace_write_policy") == "disabled" and changed:
        failures.append("workspace changed while write policy is disabled")
    if not isinstance(allowed, list):
        failures.append("allowed_workspace_paths must be an array")
        allowed = []
    for path in changed:
        if not any(fnmatch.fnmatchcase(path, str(pattern)) for pattern in allowed):
            failures.append(f"workspace change is outside allowed paths: {path}")
    return failures


def count_user_questions(response: str) -> int:
    without_fences = re.sub(r"```[\s\S]*?```", "", response)
    without_inline_code = re.sub(r"`[^`\n]*`", "", without_fences)
    without_urls = re.sub(r"https?://\S+", "", without_inline_code)
    return without_urls.count("?") + without_urls.count("？")


def validator_expectations(label: str, stdout: str, return_code: int) -> list[dict[str, Any]]:
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return [{"text": f"{label} produced parseable JSON", "passed": False, "evidence": stdout.strip() or f"exit={return_code}"}]
    if isinstance(payload, dict) and isinstance(payload.get("expectations"), list):
        return [item for item in payload["expectations"] if isinstance(item, dict)]
    if isinstance(payload, dict) and isinstance(payload.get("checks"), list):
        values = [{"text": f"{label}: {item}", "passed": True, "evidence": "deterministic check"} for item in payload.get("checks", [])]
        values.extend({"text": f"{label}: {item}", "passed": False, "evidence": "deterministic failure"} for item in payload.get("failures", []))
        return values
    if isinstance(payload, dict) and isinstance(payload.get("passed"), bool) and isinstance(payload.get("findings"), list):
        passed = payload["passed"] is True and int(payload.get("major_count", 0)) == 0 and return_code == 0
        return [{"text": f"{label} passes strict FDD structure validation", "passed": passed, "evidence": f"major_count={payload.get('major_count')} findings={len(payload['findings'])}"}]
    return [{"text": f"{label} returned a recognized result", "passed": False, "evidence": f"exit={return_code}"}]


def select_primary_fdd(workspace: Path) -> tuple[Path | None, str | None]:
    fdd_root = workspace / "docs" / "FDD"
    candidates = sorted(path for path in fdd_root.glob("*.md") if path.name.lower() != "index.md")
    marked = [
        path
        for path in candidates
        if re.search(r"(?m)^doc-type:\s*(?:feature-design-doc|fdd)\s*$", path.read_text(encoding="utf-8"), re.IGNORECASE)
    ]
    if len(marked) == 1:
        return marked[0], None
    if len(marked) > 1:
        return None, f"multiple frontmatter-marked FDD files found: {[path.name for path in marked]}"
    if len(candidates) == 1:
        return candidates[0], None
    return None, f"expected one primary FDD excluding index.md, found {[path.name for path in candidates]}"


def run_deterministic_validators(
    run_dir: Path, workspace: Path, suite: dict[str, Any], eval_item: dict[str, Any]
) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    contract = case_contract(int(eval_item["id"]), suite)
    validation = contract.get("validation")
    if isinstance(validation, str) and validation:
        parts = validation.split()
        if parts[0] == "validate_fdd.py":
            candidate, selection_error = select_primary_fdd(workspace)
            if candidate is None:
                records.append({"name": validation, "return_code": 2, "stdout": "", "stderr": selection_error or "primary FDD unavailable"})
            else:
                command = [sys.executable, str(run_dir / "skill-snapshot" / "scripts" / "validate_fdd.py"), str(candidate), "--format", "json", *parts[1:]]
                completed = subprocess.run(command, cwd=workspace, text=True, capture_output=True, check=False)
                records.append({"name": validation, "return_code": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr})
        else:
            fixture_root = fixture_root_for_eval(eval_item)
            result_root = workspace / destination_for_fixture(int(eval_item["id"]), suite)
            if fixture_root is None:
                records.append({"name": validation, "return_code": 2, "stdout": "", "stderr": "fixture root unavailable"})
            else:
                command = ["node", str(SKILL_ROOT / "evals" / "validators" / parts[0]), str(fixture_root), str(result_root), *parts[1:]]
                completed = subprocess.run(command, cwd=SKILL_ROOT, text=True, capture_output=True, check=False)
                records.append({"name": validation, "return_code": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr})
    document_validation = contract.get("document_validation")
    if isinstance(document_validation, dict):
        command = [
            sys.executable,
            str(run_dir / "skill-snapshot" / "scripts" / "validate_design_system_output.py"),
            str(workspace / require_relative(str(document_validation["root"]), "document validation root")),
            "--prebuilt",
            str(document_validation["prebuilt"]),
            "--format",
            "json",
        ]
        for store in document_validation.get("stores", []):
            command.extend(("--store", str(store)))
        png = document_validation.get("png")
        if isinstance(png, dict):
            command.extend(("--png-count", str(png.get("count", 1)), "--png-width", str(png["width"]), "--png-height", str(png["height"]), "--png-alpha", "true" if png.get("has_alpha") else "false"))
        completed = subprocess.run(command, cwd=workspace, text=True, capture_output=True, check=False)
        records.append({"name": "validate_design_system_output.py", "return_code": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr})
    command = [sys.executable, str(SKILL_ROOT / "scripts" / "validate_eval_run.py"), "--suite", str(SUITE_PATH), "--run", str(run_dir)]
    completed = subprocess.run(command, cwd=SKILL_ROOT, text=True, capture_output=True, check=False)
    records.append({"name": "validate_eval_run.py", "return_code": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr})
    expectations: list[dict[str, Any]] = []
    for record in records:
        expectations.extend(validator_expectations(record["name"], record["stdout"], int(record["return_code"])))
    passed = sum(item.get("passed") is True for item in expectations)
    return {
        "status": "completed",
        "validators": records,
        "expectations": expectations,
        "summary": {"passed": passed, "failed": len(expectations) - passed, "total": len(expectations), "pass_rate": passed / len(expectations) if expectations else 0.0},
    }


def write_review_bundle(run_dir: Path, workspace: Path, response: str, manifest: dict[str, Any]) -> None:
    outputs = run_dir / "outputs"
    outputs.mkdir(parents=True, exist_ok=True)
    (outputs / "assistant-response.md").write_text(response, encoding="utf-8")
    (outputs / "tree.txt").write_text("\n".join(f"{entry['type']}: {entry['path']}" for entry in manifest.get("entries", [])) + "\n", encoding="utf-8")
    sections: list[str] = []
    for relative in sorted(manifest.get("files", {})):
        source = workspace / relative
        if source.suffix.lower() == ".md":
            sections.append(f"# `{relative}`\n\n{source.read_text(encoding='utf-8')}")
        elif source.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".svg"}:
            shutil.copy2(source, outputs / source.name)
    (outputs / "artifact-review.md").write_text("\n\n---\n\n".join(sections) + ("\n" if sections else ""), encoding="utf-8")


def canonicalize_worker_response(run_dir: Path, response_path: Path) -> Path | None:
    if response_path.is_file() and response_path.read_text(encoding="utf-8").strip():
        return response_path
    excluded_roots = {"workspace", "skill-snapshot", "outputs", "revalidation", "transport-recovery", "grader"}
    candidates = [
        path
        for path in run_dir.rglob("direct-response.md")
        if path != response_path
        and not any(part in excluded_roots for part in path.relative_to(run_dir).parts)
        and path.is_file()
        and path.read_text(encoding="utf-8").strip()
    ]
    if len(candidates) != 1:
        return None
    response_path.write_bytes(candidates[0].read_bytes())
    write_json(run_dir / "response-canonicalization.json", {"schema_version": 1, "provenance": "harness-canonicalized-worker-transport", "source": candidates[0].relative_to(run_dir).as_posix(), "destination": response_path.name, "sha256": sha256_file(response_path)})
    return response_path


def direct_behavior_finalize_stage(root: Path, suite: dict[str, Any], eval_id: int | None, dry_run: bool) -> dict[str, Any]:
    runs: list[dict[str, Any]] = []
    for eval_item in selected_evals(root, suite, eval_id):
        current_eval_id = int(eval_item["id"])
        run_dir = expected_run_dir(root, current_eval_id)
        if dry_run:
            runs.append({"eval_id": current_eval_id, "status": "planned"})
            continue
        if not run_dir.is_dir():
            runs.append({"eval_id": current_eval_id, "status": "not-prepared", "reasons": ["run directory missing"]})
            continue
        if (run_dir / "execution-validation.json").is_file():
            raise ProductionEvalError(f"eval {current_eval_id} has already been finalized")
        task = load_json(run_dir / "direct-task.json")
        before = load_json(run_dir / "workspace-before.json")
        after = tree_manifest(run_dir / "workspace")
        write_json(run_dir / "workspace-after.json", after)
        write_json(run_dir / "after-manifest.json", after)
        response_path = run_dir / "direct-response.md"
        canonicalize_worker_response(run_dir, response_path)
        if not response_path.is_file() or not response_path.read_text(encoding="utf-8").strip():
            receipt = {
                "schema_version": 3,
                "provenance": "harness-derived-from-task-response-and-manifests",
                "status": "missing-response",
                "task_context_id": task.get("task_context_id"),
                "model": task.get("model"),
                "reasoning_effort": task.get("reasoning_effort"),
                "response_sha256": None,
                "workspace_before_sha256": before.get("sha256"),
                "workspace_after_sha256": after.get("sha256"),
                "produced_paths": actual_changed_file_paths(before, after),
                "telemetry": {"status": "unavailable", "duration_ms": None, "total_tokens": None},
                "capability_evidence": {"status": "unverified", "events": []},
            }
            write_json(run_dir / "execution-receipt.json", receipt)
            validation = {"schema_version": 3, "provenance": "harness-execution-validation", "eval_id": current_eval_id, "status": "missing-response", "valid": False, "reasons": ["response is missing or empty"]}
            write_json(run_dir / "execution-validation.json", validation)
            runs.append({"eval_id": current_eval_id, "status": "execution-error", "reasons": validation["reasons"]})
            continue
        receipt = build_harness_execution_receipt(task, response_path, before, after)
        reasons = validate_harness_execution_receipt(receipt, task, before, after)
        write_json(run_dir / "execution-receipt.json", receipt)
        skill_before = load_json(run_dir / "skill-snapshot-before.json")
        skill_after = skill_snapshot_manifest(run_dir / "skill-snapshot", skill_before["source_contract_sha256"])
        write_json(run_dir / "skill-snapshot-after.json", skill_after)
        snapshot_preserved = skill_before == skill_after
        metadata = {
            "schema_version": 3,
            "eval_id": current_eval_id,
            "eval_name": eval_item.get("eval_name", f"eval-{current_eval_id}"),
            "configuration": "current",
            "run_number": 1,
            "prompt": eval_item["prompt"],
            "expectations": eval_item.get("expectations", []),
            "case_contract": case_contract(current_eval_id, suite),
            "task_context_id": receipt.get("task_context_id"),
        }
        write_json(run_dir / "eval_metadata.json", metadata)
        response = response_path.read_text(encoding="utf-8")
        (run_dir / "assistant-response.md").write_text(response, encoding="utf-8")
        write_review_bundle(run_dir, run_dir / "workspace", response, after)
        if not reasons:
            deterministic = run_deterministic_validators(run_dir, run_dir / "workspace", suite, eval_item)
            deterministic["expectations"].append({"text": "Execution skill snapshot remains unchanged", "passed": snapshot_preserved, "evidence": f"before={skill_before['sha256']} after={skill_after['sha256']}"})
            passed = sum(item.get("passed") is True for item in deterministic["expectations"])
            deterministic["summary"] = {"passed": passed, "failed": len(deterministic["expectations"]) - passed, "total": len(deterministic["expectations"]), "pass_rate": passed / len(deterministic["expectations"])}
            write_json(run_dir / "deterministic-grading.json", deterministic)
            if deterministic["summary"]["failed"]:
                reasons.extend(str(item.get("text")) for item in deterministic["expectations"] if item.get("passed") is not True)
        status = "completed" if not reasons else "hard-gate-failed"
        validation = {"schema_version": 3, "provenance": "harness-execution-validation", "eval_id": current_eval_id, "status": status, "valid": not reasons, "reasons": reasons}
        write_json(run_dir / "execution-validation.json", validation)
        runs.append({"eval_id": current_eval_id, "status": status, "reasons": reasons})
    status_path = root / "behavior-status.json"
    prior = load_json(status_path).get("runs", []) if status_path.is_file() else []
    merged = {item["eval_id"]: item for item in prior if isinstance(item, dict) and isinstance(item.get("eval_id"), int)}
    merged.update({item["eval_id"]: item for item in runs})
    write_json(status_path, {"schema_version": 3, "runs": [merged[key] for key in sorted(merged)], "updated_at": utc_now()})
    return {"stage": "direct-behavior-finalize", "runs": runs}


def direct_behavior_revalidate_stage(root: Path, suite: dict[str, Any], eval_id: int | None, dry_run: bool) -> dict[str, Any]:
    if eval_id is None:
        raise ProductionEvalError("direct-behavior-revalidate requires --eval-id")
    eval_item = selected_evals(root, suite, eval_id)[0]
    run_dir = expected_run_dir(root, eval_id)
    required = ("direct-task.json", "direct-response.md", "workspace-before.json", "workspace-after.json", "execution-receipt.json", "eval_metadata.json", "deterministic-grading.json", "execution-validation.json")
    if any(not (run_dir / name).is_file() for name in required):
        raise ProductionEvalError(f"eval {eval_id} cannot be revalidated because required artifacts are missing")
    if dry_run:
        return {"stage": "direct-behavior-revalidate", "runs": [{"eval_id": eval_id, "status": "planned"}]}
    task = load_json(run_dir / "direct-task.json")
    before = load_json(run_dir / "workspace-before.json")
    after = load_json(run_dir / "workspace-after.json")
    receipt = load_json(run_dir / "execution-receipt.json")
    receipt_failures = validate_harness_execution_receipt(receipt, task, before, after)
    if receipt_failures:
        raise ProductionEvalError(f"eval {eval_id} receipt is invalid and cannot be revalidated: {receipt_failures}")
    history_root = run_dir / "revalidation" / "attempt-1"
    if history_root.exists():
        raise ProductionEvalError(f"eval {eval_id} has already been revalidated")
    history_root.mkdir(parents=True)
    shutil.copy2(run_dir / "deterministic-grading.json", history_root / "deterministic-grading.json")
    shutil.copy2(run_dir / "execution-validation.json", history_root / "execution-validation.json")
    deterministic = run_deterministic_validators(run_dir, run_dir / "workspace", suite, eval_item)
    skill_before = load_json(run_dir / "skill-snapshot-before.json")
    skill_after = load_json(run_dir / "skill-snapshot-after.json")
    deterministic["expectations"].append({"text": "Execution skill snapshot remains unchanged", "passed": skill_before == skill_after, "evidence": f"before={skill_before['sha256']} after={skill_after['sha256']}"})
    passed = sum(item.get("passed") is True for item in deterministic["expectations"])
    deterministic["summary"] = {"passed": passed, "failed": len(deterministic["expectations"]) - passed, "total": len(deterministic["expectations"]), "pass_rate": passed / len(deterministic["expectations"])}
    write_json(run_dir / "deterministic-grading.json", deterministic)
    reasons = [str(item.get("text")) for item in deterministic["expectations"] if item.get("passed") is not True]
    status = "completed" if not reasons else "hard-gate-failed"
    validation = {"schema_version": 3, "provenance": "harness-execution-revalidation", "eval_id": eval_id, "status": status, "valid": not reasons, "reasons": reasons}
    write_json(run_dir / "execution-validation.json", validation)
    write_json(run_dir / "revalidation-history.json", {"schema_version": 1, "eval_id": eval_id, "reason": "Primary FDD selection now excludes docs/FDD/index.md and chooses the actual feature document.", "model_rerun": False, "prior_artifacts": "revalidation/attempt-1", "result": status, "recorded_at": utc_now()})
    return {"stage": "direct-behavior-revalidate", "runs": [{"eval_id": eval_id, "status": status, "reasons": reasons}]}


def direct_behavior_recover_stage(root: Path, suite: dict[str, Any], eval_id: int | None, dry_run: bool) -> dict[str, Any]:
    if eval_id is None:
        raise ProductionEvalError("direct-behavior-recover requires --eval-id")
    eval_item = selected_evals(root, suite, eval_id)[0]
    run_dir = expected_run_dir(root, eval_id)
    task_path = run_dir / "direct-task.json"
    before_path = run_dir / "workspace-before.json"
    if not task_path.is_file() or not before_path.is_file():
        raise ProductionEvalError(f"eval {eval_id} has no prepared transport to recover")
    recovery_root = run_dir / "transport-recovery" / "attempt-1"
    if recovery_root.exists():
        raise ProductionEvalError(f"eval {eval_id} transport was already recovered")
    if dry_run:
        return {"stage": "direct-behavior-recover", "runs": [{"eval_id": eval_id, "status": "planned"}]}
    recovery_root.mkdir(parents=True)
    for name in ("direct-response.md", "execution-receipt.json", "execution-validation.json", "deterministic-grading.json"):
        source = run_dir / name
        if source.is_file():
            shutil.copy2(source, recovery_root / name)
    expected_response = run_dir / "direct-response.md"
    receipt = load_json(run_dir / "execution-receipt.json") if (run_dir / "execution-receipt.json").is_file() else {}
    preserved_response = run_dir / "assistant-response.md"
    source: Path | None = None
    if preserved_response.is_file() and receipt.get("response_sha256") == sha256_file(preserved_response):
        source = preserved_response
    if source is None:
        canonicalize_worker_response(run_dir, expected_response)
        if expected_response.is_file() and expected_response.read_text(encoding="utf-8").strip():
            source = expected_response
    if source is None:
        raise ProductionEvalError(f"eval {eval_id} has no unique recoverable response")
    if source != expected_response:
        expected_response.write_bytes(source.read_bytes())
    task = load_json(task_path)
    before = load_json(before_path)
    after = tree_manifest(run_dir / "workspace")
    write_json(run_dir / "workspace-after.json", after)
    write_json(run_dir / "after-manifest.json", after)
    new_receipt = build_harness_execution_receipt(task, expected_response, before, after)
    reasons = validate_harness_execution_receipt(new_receipt, task, before, after)
    write_json(run_dir / "execution-receipt.json", new_receipt)
    skill_before = load_json(run_dir / "skill-snapshot-before.json")
    skill_after = skill_snapshot_manifest(run_dir / "skill-snapshot", skill_before["source_contract_sha256"])
    write_json(run_dir / "skill-snapshot-after.json", skill_after)
    metadata = {"schema_version": 3, "eval_id": eval_id, "eval_name": eval_item.get("eval_name", f"eval-{eval_id}"), "configuration": "current", "run_number": 1, "prompt": eval_item["prompt"], "expectations": eval_item.get("expectations", []), "case_contract": case_contract(eval_id, suite), "task_context_id": new_receipt.get("task_context_id")}
    write_json(run_dir / "eval_metadata.json", metadata)
    response = expected_response.read_text(encoding="utf-8")
    (run_dir / "assistant-response.md").write_text(response, encoding="utf-8")
    write_review_bundle(run_dir, run_dir / "workspace", response, after)
    if not reasons:
        deterministic = run_deterministic_validators(run_dir, run_dir / "workspace", suite, eval_item)
        deterministic["expectations"].append({"text": "Execution skill snapshot remains unchanged", "passed": skill_before == skill_after, "evidence": f"before={skill_before['sha256']} after={skill_after['sha256']}"})
        passed = sum(item.get("passed") is True for item in deterministic["expectations"])
        deterministic["summary"] = {"passed": passed, "failed": len(deterministic["expectations"]) - passed, "total": len(deterministic["expectations"]), "pass_rate": passed / len(deterministic["expectations"])}
        write_json(run_dir / "deterministic-grading.json", deterministic)
        reasons.extend(str(item.get("text")) for item in deterministic["expectations"] if item.get("passed") is not True)
    status = "completed" if not reasons else "hard-gate-failed"
    write_json(run_dir / "execution-validation.json", {"schema_version": 3, "provenance": "harness-transport-recovery-validation", "eval_id": eval_id, "status": status, "valid": not reasons, "reasons": reasons})
    write_json(run_dir / "transport-recovery-history.json", {"schema_version": 1, "eval_id": eval_id, "model_rerun": False, "source": source.relative_to(run_dir).as_posix(), "response_sha256": sha256_file(expected_response), "result": status, "recorded_at": utc_now()})
    return {"stage": "direct-behavior-recover", "runs": [{"eval_id": eval_id, "status": status, "reasons": reasons}]}


def grading_job_id(eval_id: int) -> str:
    identity = f"document-writing-grading:{eval_id}:current:1"
    return f"grader-{hashlib.sha256(identity.encode('utf-8')).hexdigest()[:24]}"


def validate_independent_grading(grading: dict[str, Any], task: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if grading.get("schema_version") != 3 or grading.get("status") != "completed-independent-grading" or grading.get("provenance") != "independent-luna-grader-output":
        failures.append("grading schema, status, or provenance is invalid")
    for field in ("eval_id", "grader_task_context_id", "model", "reasoning_effort"):
        if grading.get(field) != task.get(field):
            failures.append(f"grading {field} does not match grader task")
    for field in ("telemetry", "tool_events", "produced_paths", "execution_status"):
        if field in grading:
            failures.append(f"grading must not self-report {field}")
    expected = task.get("expectations") if isinstance(task.get("expectations"), list) else []
    records = grading.get("expectations")
    if not isinstance(records, list) or len(records) != len(expected):
        failures.append("grading must contain exactly one record per semantic expectation")
        records = []
    else:
        for index, (record, text) in enumerate(zip(records, expected, strict=True)):
            if not isinstance(record, dict) or record.get("text") != text or not isinstance(record.get("passed"), bool) or not isinstance(record.get("evidence"), str) or not record["evidence"].strip():
                failures.append(f"grading expectation {index} is invalid")
    passed = sum(isinstance(item, dict) and item.get("passed") is True for item in records)
    summary = {"passed": passed, "failed": len(expected) - passed, "total": len(expected), "pass_rate": passed / len(expected) if expected else 0.0}
    if grading.get("summary") != summary:
        failures.append("grading summary must be recalculated")
    return failures


def grader_dispatch_message(task: dict[str, Any]) -> str:
    task_json = json.dumps(task, ensure_ascii=False, indent=2)
    return (
        "Grade exactly the authoritative grading task JSON embedded below. Do not inspect the skill snapshot, sibling "
        "runs, package evidence, or prior grades. Do not spawn subagents. Read only the supplied response, workspace, "
        "receipt, and deterministic grading. A chat-only answer is a failed run. Before sending any final response: "
        "(1) use apply_patch to create output_path with the complete JSON object, (2) run `python3 -m json.tool output_path`, "
        "and (3) read output_path back and confirm every required field and expectation is present. Only after all three "
        "actions succeed may you return a short confirmation. Write no other file.\n\nAUTHORITATIVE_GRADING_TASK_JSON\n```json\n"
        f"{task_json}\n```"
    )


def direct_grading_prepare_stage(root: Path, suite: dict[str, Any], eval_id: int | None, dry_run: bool) -> dict[str, Any]:
    tasks: list[dict[str, Any]] = []
    for eval_item in selected_evals(root, suite, eval_id):
        current_eval_id = int(eval_item["id"])
        run_dir = expected_run_dir(root, current_eval_id)
        validation_path = run_dir / "execution-validation.json"
        if not validation_path.is_file() or load_json(validation_path).get("valid") is not True:
            raise ProductionEvalError(f"eval {current_eval_id} execution is not valid; grader must not run")
        grader_root = run_dir / "grader" / "attempt-1"
        input_root = grader_root / "input"
        if not dry_run:
            if grader_root.exists():
                raise ProductionEvalError(f"eval {current_eval_id} grader attempt already exists")
            input_root.mkdir(parents=True)
            shutil.copy2(run_dir / "direct-response.md", input_root / "response.md")
            shutil.copytree(run_dir / "workspace", input_root / "workspace")
            shutil.copy2(run_dir / "execution-receipt.json", input_root / "execution-receipt.json")
            shutil.copy2(run_dir / "deterministic-grading.json", input_root / "deterministic-grading.json")
        task = {
            "schema_version": 3,
            "job_id": grading_job_id(current_eval_id),
            "eval_id": current_eval_id,
            "grader_task_context_id": uuid.uuid4().hex,
            "model": EXECUTION_MODEL,
            "reasoning_effort": EXECUTION_REASONING_EFFORT,
            "prompt": eval_item["prompt"],
            "expectations": list(eval_item.get("expectations", [])),
            "response_path": str(input_root / "response.md"),
            "workspace_path": str(input_root / "workspace"),
            "execution_receipt_path": str(input_root / "execution-receipt.json"),
            "deterministic_grading_path": str(input_root / "deterministic-grading.json"),
            "output_path": str(grader_root / "grading-candidate.json"),
            "source_bindings": {"response_sha256": sha256_file(run_dir / "direct-response.md"), "workspace_sha256": tree_manifest(run_dir / "workspace")["sha256"]},
            "required_completion_actions": [
                "Create output_path with apply_patch; a chat-only answer is failure.",
                "Validate output_path with python3 -m json.tool.",
                "Read output_path back and verify the complete output_contract before finishing.",
            ],
            "output_contract": {
                "schema_version": 3,
                "status": "completed-independent-grading",
                "provenance": "independent-luna-grader-output",
                "eval_id": current_eval_id,
                "grader_task_context_id": "copy from task",
                "model": EXECUTION_MODEL,
                "reasoning_effort": EXECUTION_REASONING_EFFORT,
                "expectations": [{"text": "exact supplied expectation", "passed": True, "evidence": "specific artifact evidence"}],
                "summary": {"passed": 0, "failed": 0, "total": 0, "pass_rate": 0.0},
            },
        }
        dispatch = grader_dispatch_message(task)
        tasks.append({"eval_id": current_eval_id, "job_id": task["job_id"], "task": task, "dispatch_message": dispatch})
        if not dry_run:
            write_json(run_dir / "grading-task.json", task)
            write_json(run_dir / "grader-dispatch.json", {"schema_version": 3, "provenance": "harness-generated-embedded-task", "eval_id": current_eval_id, "task_sha256": sha256_file(run_dir / "grading-task.json"), "dispatch_message": dispatch})
    return {"stage": "direct-grading-prepare", "tasks": tasks}


def direct_grading_finalize_stage(root: Path, suite: dict[str, Any], eval_id: int | None, dry_run: bool) -> dict[str, Any]:
    runs: list[dict[str, Any]] = []
    for eval_item in selected_evals(root, suite, eval_id):
        current_eval_id = int(eval_item["id"])
        run_dir = expected_run_dir(root, current_eval_id)
        if dry_run:
            runs.append({"eval_id": current_eval_id, "status": "planned"})
            continue
        if (run_dir / "grading-validation.json").is_file():
            raise ProductionEvalError(f"eval {current_eval_id} grading has already been finalized")
        reasons: list[str] = []
        task_path = run_dir / "grading-task.json"
        task = load_json(task_path) if task_path.is_file() else {}
        candidate_path = Path(str(task.get("output_path", run_dir / "grading.json")))
        bindings = task.get("source_bindings") if isinstance(task.get("source_bindings"), dict) else {}
        if bindings and (sha256_file(run_dir / "direct-response.md") != bindings.get("response_sha256") or tree_manifest(run_dir / "workspace")["sha256"] != bindings.get("workspace_sha256")):
            reasons.append("grader source isolation failed: original response or workspace changed")
        if not task_path.is_file() or not candidate_path.is_file():
            reasons.append("grading task or output is missing")
            grading: dict[str, Any] = {}
        else:
            grading = load_json(candidate_path)
            reasons.extend(validate_independent_grading(grading, task))
            if not reasons:
                write_json(run_dir / "grading.json", grading)
        format_valid = not reasons
        semantic_passed = format_valid and grading.get("summary", {}).get("failed") == 0
        status = "completed" if semantic_passed else ("quality-failed" if format_valid else "grading-error")
        validation = {"schema_version": 3, "provenance": "harness-validation-of-independent-grading", "eval_id": current_eval_id, "status": status, "format_valid": format_valid, "semantic_passed": semantic_passed, "reasons": reasons, "grading_sha256": sha256_file(run_dir / "grading.json") if (run_dir / "grading.json").is_file() else None}
        write_json(run_dir / "grading-validation.json", validation)
        runs.append({"eval_id": current_eval_id, "status": status, "reasons": reasons})
    status_path = root / "grading-status.json"
    prior = load_json(status_path).get("runs", []) if status_path.is_file() else []
    merged = {item["eval_id"]: item for item in prior if isinstance(item, dict) and isinstance(item.get("eval_id"), int)}
    merged.update({item["eval_id"]: item for item in runs})
    write_json(status_path, {"schema_version": 3, "runs": [merged[key] for key in sorted(merged)], "updated_at": utc_now()})
    return {"stage": "direct-grading-finalize", "runs": runs}


def aggregate_stage(root: Path, suite: dict[str, Any], dry_run: bool) -> dict[str, Any]:
    scope_kind, scope_ids = iteration_scope(root, suite)
    evals = {item["id"]: item for item in selected_evals(root, suite)}
    runs: list[dict[str, Any]] = []
    for current_eval_id in scope_ids:
        eval_item = evals[current_eval_id]
        run_dir = expected_run_dir(root, current_eval_id)
        response_present = (run_dir / "direct-response.md").is_file() and bool((run_dir / "direct-response.md").read_text(encoding="utf-8").strip())
        receipt_valid = False
        receipt_status = "not-prepared" if not run_dir.is_dir() else "not-finalized"
        task_context_id = None
        if all((run_dir / name).is_file() for name in ("direct-task.json", "workspace-before.json", "workspace-after.json", "execution-receipt.json")):
            task = load_json(run_dir / "direct-task.json")
            receipt = load_json(run_dir / "execution-receipt.json")
            task_context_id = task.get("task_context_id")
            receipt_status = str(receipt.get("status"))
            receipt_valid = not validate_harness_execution_receipt(receipt, task, load_json(run_dir / "workspace-before.json"), load_json(run_dir / "workspace-after.json"))
            if response_present and receipt.get("response_sha256") != sha256_file(run_dir / "direct-response.md"):
                receipt_valid = False
        deterministic_status = "not-run"
        if (run_dir / "deterministic-grading.json").is_file():
            deterministic_status = "pass" if load_json(run_dir / "deterministic-grading.json").get("summary", {}).get("failed") == 0 else "fail"
        grading_status = "not-run"
        grading_format_valid = False
        semantic_passed = False
        pass_rate = None
        grader_task_context_id = None
        if (run_dir / "grading-validation.json").is_file():
            grading_validation = load_json(run_dir / "grading-validation.json")
            grading_status = str(grading_validation.get("status"))
            grading_format_valid = grading_validation.get("format_valid") is True
            semantic_passed = grading_validation.get("semantic_passed") is True
            if (run_dir / "grading.json").is_file():
                grading = load_json(run_dir / "grading.json")
                grader_task_context_id = grading.get("grader_task_context_id")
                if grading_format_valid:
                    pass_rate = grading.get("summary", {}).get("pass_rate")
        execution_valid = receipt_valid and receipt_status == "completed"
        scoreable = execution_valid and deterministic_status == "pass" and grading_format_valid
        runs.append({
            "eval_id": current_eval_id,
            "eval_name": eval_item.get("eval_name", f"eval-{current_eval_id}"),
            "configuration": "current",
            "run_number": 1,
            "job_id": behavior_job_id(current_eval_id),
            "task_context_id": task_context_id,
            "grader_task_context_id": grader_task_context_id,
            "response_present": response_present,
            "execution": {"receipt_status": receipt_status, "receipt_valid": receipt_valid, "valid": execution_valid},
            "deterministic_status": deterministic_status,
            "grading": {"status": grading_status, "format_valid": grading_format_valid, "semantic_passed": semantic_passed, "pass_rate": pass_rate},
            "scoreable": scoreable,
        })
    completed_rates = [float(run["grading"]["pass_rate"]) for run in runs if run["scoreable"] and isinstance(run["grading"]["pass_rate"], (int, float))]
    hard_gates: dict[str, str] = {}
    for name, eval_ids in HARD_GATE_EVAL_IDS.items():
        relevant = [run for run in runs if run["eval_id"] in eval_ids]
        if not relevant:
            hard_gates[name] = "not-in-scope"
        elif any(
            run["deterministic_status"] == "fail"
            or run["execution"]["receipt_status"] == "missing-response"
            or (run["execution"]["receipt_status"] == "completed" and not run["execution"]["valid"])
            for run in relevant
        ):
            hard_gates[name] = "fail"
        elif any(
            run["execution"]["receipt_status"] in {"not-prepared", "not-finalized"}
            or run["deterministic_status"] == "not-run"
            for run in relevant
        ):
            hard_gates[name] = "not-run"
        elif any(run["grading"]["status"] == "grading-error" for run in relevant):
            hard_gates[name] = "fail"
        elif any(run["grading"]["status"] == "not-run" for run in relevant):
            hard_gates[name] = "not-graded"
        elif all(run["grading"]["semantic_passed"] for run in relevant):
            hard_gates[name] = "pass"
        else:
            hard_gates[name] = "fail"
    expected = len(scope_ids)
    summary = {
        "scope_kind": scope_kind,
        "planned_execution_tasks": expected,
        "responses_present": sum(run["response_present"] for run in runs),
        "valid_execution_receipts": sum(run["execution"]["valid"] for run in runs),
        "deterministic_passed": sum(run["deterministic_status"] == "pass" for run in runs),
        "deterministic_failed": sum(run["deterministic_status"] == "fail" for run in runs),
        "completed_independent_gradings": sum(run["grading"]["format_valid"] for run in runs),
        "semantic_passed": sum(run["grading"]["semantic_passed"] for run in runs),
        "macro_pass_rate": round(sum(completed_rates) / len(completed_rates), 4) if completed_rates else None,
        "hard_gates": hard_gates,
    }
    all_scope_passed = (
        summary["valid_execution_receipts"] == expected
        and summary["deterministic_passed"] == expected
        and summary["completed_independent_gradings"] == expected
        and summary["semantic_passed"] == expected
    )
    summary["all_scope_passed"] = all_scope_passed
    summary["production_eligible"] = scope_kind == "production" and scope_ids == list(suite["behavior"]["eval_ids"])
    benchmark = {"schema_version": 3, "status": "completed" if all_scope_passed else "diagnostic-failed", "metadata": {"skill_name": suite["skill_name"], "timestamp": utc_now(), "evals_run": scope_ids, "configuration": "current", "runs_per_eval": 1}, "runs": runs, "summary": summary}
    if not dry_run:
        write_json(root / "benchmark.json", benchmark)
    return {"stage": "aggregate", "status": benchmark["status"], "summary": summary}


def description_from_skill(skill_path: Path) -> str:
    content = (skill_path / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---", content, flags=re.DOTALL)
    if not match:
        raise ProductionEvalError("SKILL.md has no frontmatter")
    for line in match.group(1).splitlines():
        if line.startswith("description:"):
            return line.split(":", 1)[1].strip()
    raise ProductionEvalError("SKILL.md has no scalar description")


def selection_reuse_result(root: Path, suite: dict[str, Any]) -> dict[str, Any]:
    contract = suite["selection"]
    snapshot = root / "snapshots" / CURRENT_SNAPSHOT / "document-writing"
    description_hash = hashlib.sha256(description_from_skill(snapshot).encode("utf-8")).hexdigest()
    dataset_path = snapshot / require_relative(str(contract["dataset"]), "selection dataset")
    evidence_path = SKILL_ROOT / require_relative(str(contract["evidence"]), "selection evidence")
    dataset_hash = sha256_file(dataset_path) if dataset_path.is_file() else None
    evidence_hash = sha256_file(evidence_path) if evidence_path.is_file() else None
    evidence = load_json(evidence_path) if evidence_path.is_file() else {}
    metrics = evidence.get("metrics") if isinstance(evidence.get("metrics"), dict) else {}
    hashes_match = description_hash == contract.get("description_sha256") and dataset_hash == contract.get("dataset_sha256") and evidence_hash == contract.get("evidence_sha256")
    gates = suite["evidence"]["gates"]
    metrics_pass = metrics.get("precision", 0) >= gates["selection_precision_min"] and metrics.get("recall", 0) >= gates["selection_recall_min"] and metrics.get("specificity", 0) >= gates["selection_specificity_min"] and metrics.get("high_risk_false_positives") <= gates["high_risk_false_positives_max"]
    return {"status": "reused" if hashes_match and metrics_pass else "mismatch", "passed": hashes_match and metrics_pass, "source_path": contract["evidence"], "source_sha256": evidence_hash, "description_sha256": description_hash, "expected_description_sha256": contract.get("description_sha256"), "dataset_sha256": dataset_hash, "expected_dataset_sha256": contract.get("dataset_sha256"), "metrics": metrics, "new_selection_executed": False}


def inspect_png_artifact(path: Path) -> dict[str, Any] | None:
    try:
        content = path.read_bytes()
    except OSError:
        return None
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
    compressed = b"".join(data for chunk_type, data in chunks if chunk_type == b"IDAT")
    try:
        decoded = zlib.decompress(compressed)
    except zlib.error:
        return None
    expected_bytes = height * (1 + ((width * channels * bit_depth + 7) // 8))
    if len(decoded) != expected_bytes:
        return None
    has_alpha = color_type in {4, 6} or any(chunk_type == b"tRNS" for chunk_type, _data in chunks)
    return {"width": width, "height": height, "has_alpha": has_alpha, "sha256": hashlib.sha256(content).hexdigest()}


def review_generator_path() -> Path:
    candidates: list[Path] = []
    configured = os.environ.get("CC_SKILL_CREATOR_PATH")
    if configured:
        value = Path(configured).expanduser()
        candidates.append(value if value.name == "generate_review.py" else value / "eval-viewer" / "generate_review.py")
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        candidates.append(Path(codex_home) / "skills" / "skill-creator" / "eval-viewer" / "generate_review.py")
    candidates.append(Path.home() / ".codex" / "skills" / "skill-creator" / "eval-viewer" / "generate_review.py")
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise ProductionEvalError("skill-creator review generator is unavailable")


def review_stage(root: Path, suite: dict[str, Any], dry_run: bool) -> dict[str, Any]:
    benchmark = root / "benchmark.json"
    if not benchmark.is_file():
        raise ProductionEvalError("aggregate must produce benchmark.json before review")
    command = [sys.executable, str(review_generator_path()), str(root), "--skill-name", suite["skill_name"], "--benchmark", str(benchmark), "--static", str(root / "review.html")]
    if dry_run:
        return {"stage": "review", "command": command}
    completed = subprocess.run(command, cwd=REPOSITORY_ROOT, text=True, capture_output=True, check=False)
    if completed.returncode != 0 or not (root / "review.html").is_file():
        raise ProductionEvalError(f"review generation failed: {(completed.stderr or completed.stdout).strip()}")
    return {"stage": "review", "status": "completed", "path": str(root / "review.html"), "sha256": sha256_file(root / "review.html")}


def validate_evidence_candidate(staging: Path, published_root: Path, candidate_path: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="document-writing-evidence-check-") as temporary:
        temporary_skill = Path(temporary) / "document-writing"
        def ignore(source: str, names: list[str]) -> set[str]:
            ignored = {name for name in names if name in {"__pycache__", ".DS_Store"} or name.endswith(".pyc")}
            if Path(source).resolve() == (SKILL_ROOT / "evals").resolve() and "evidence" in names:
                ignored.add("evidence")
            return ignored
        shutil.copytree(SKILL_ROOT, temporary_skill, ignore=ignore)
        destination = temporary_skill / "evals" / "evidence" / published_root.name
        shutil.copytree(staging, destination)
        shutil.copy2(candidate_path, temporary_skill / "evals" / "production-evidence.json")
        code = "import pathlib,sys; sys.path.insert(0,str(pathlib.Path(sys.argv[1])/'scripts')); import validate_package as v; r=v.Report(); v.validate_production_evidence(pathlib.Path(sys.argv[1]),r); print(r.as_json()); raise SystemExit(1 if r.failures else 0)"
        completed = subprocess.run([sys.executable, "-c", code, str(temporary_skill)], text=True, capture_output=True, check=False)
        if completed.returncode != 0:
            raise ProductionEvalError(f"schema-v3 evidence candidate failed validation: {completed.stdout or completed.stderr}")


def evidence_stage(root: Path, suite: dict[str, Any], dry_run: bool) -> dict[str, Any]:
    benchmark_path = root / "benchmark.json"
    if not benchmark_path.is_file():
        raise ProductionEvalError("aggregate must produce benchmark.json before evidence")
    benchmark = load_json(benchmark_path)
    scope_kind, scope_ids = iteration_scope(root, suite)
    summary = benchmark.get("summary", {})
    selection = selection_reuse_result(root, suite)
    review_source = root / "review.html"
    review_present = review_source.is_file() and review_source.stat().st_size > 0
    image_contract = suite["image_canary"]
    eval24_root = expected_run_dir(root, 24) / "workspace" / image_contract["document_root"]
    image_candidates = sorted(eval24_root.glob(str(image_contract.get("artifact_glob", "*.png")))) if eval24_root.is_dir() else []
    image_source = image_candidates[0] if len(image_candidates) == int(image_contract.get("count", 1)) == 1 else None
    image_info = inspect_png_artifact(image_source) if image_source is not None else None
    image_passed = bool(image_info and image_info["width"] == image_contract["width"] and image_info["height"] == image_contract["height"] and image_info["has_alpha"] is image_contract["has_alpha"] and (eval24_root / "index.md").is_file() and (eval24_root / "stores" / "google-play.md").is_file())
    all_scope_passed = summary.get("all_scope_passed") is True
    production_eligible = summary.get("production_eligible") is True
    gates = suite["evidence"]["gates"]
    production_ready = bool(production_eligible and all_scope_passed and summary.get("macro_pass_rate") is not None and summary["macro_pass_rate"] >= gates["macro_pass_rate_min"] and selection["passed"] and image_passed and review_present)
    verification_status = "production-pass" if production_ready else ("targeted-pass" if scope_kind == "targeted" and all_scope_passed else "targeted-failed" if scope_kind == "targeted" else "production-failed")
    if dry_run:
        return {"stage": "evidence", "status": "completed" if verification_status.endswith("pass") else "diagnostic-failed", "verification_status": verification_status}
    iteration = int(root.name.removeprefix("iteration-"))
    has_revalidation = any((expected_run_dir(root, eval_id) / "revalidation-history.json").is_file() for eval_id in scope_ids)
    evidence_directory = SKILL_ROOT / suite["evidence"]["directory"]
    base_name = f"iteration-{iteration}-v3" + ("-targeted" if scope_kind == "targeted" else "") + ("-resumed" if has_revalidation else "")
    published_name = base_name
    revision = 1
    while (evidence_directory / published_name).exists():
        published_name = f"{base_name}-revision-{revision}"
        revision += 1
    published_root = evidence_directory / published_name
    staging = root / "evidence-v3-staging"
    if staging.exists():
        raise ProductionEvalError("evidence staging already exists")
    staging.mkdir(parents=True)
    def published_path(relative: Path) -> str:
        return (Path("evals") / "evidence" / published_name / relative).as_posix()
    def artifact(kind: str, relative: Path) -> dict[str, Any]:
        return {"kind": kind, "path": published_path(relative), "sha256": sha256_file(staging / relative)}
    shutil.copy2(benchmark_path, staging / "benchmark.json")
    artifacts = [artifact("behavior-results", Path("benchmark.json"))]
    selection_source = SKILL_ROOT / suite["selection"]["evidence"]
    (staging / "selection").mkdir()
    shutil.copy2(selection_source, staging / "selection" / "source.json")
    write_json(staging / "selection" / "reuse.json", selection)
    artifacts.extend((artifact("selection-results", Path("selection/source.json")), artifact("selection-reuse", Path("selection/reuse.json"))))
    if review_present:
        shutil.copy2(review_source, staging / "review.html")
        artifacts.append(artifact("review", Path("review.html")))
    revalidation_records: list[dict[str, Any]] = []
    evidence_runs: list[dict[str, Any]] = []
    for run in benchmark.get("runs", []):
        eval_id = int(run["eval_id"])
        source_run = expected_run_dir(root, eval_id)
        relative_root = Path("runs") / f"eval-{eval_id:02d}"
        destination = staging / relative_root
        destination.mkdir(parents=True)
        copied: dict[str, dict[str, Any]] = {}
        for filename, kind in (("execution-receipt.json", "execution-receipt"), ("execution-validation.json", "execution-validation"), ("deterministic-grading.json", "deterministic-grading"), ("grading.json", "independent-grading"), ("grading-validation.json", "grading-validation"), ("direct-response.md", "response"), ("workspace-before.json", "workspace-before"), ("workspace-after.json", "workspace-after"), ("eval_metadata.json", "eval-metadata")):
            source = source_run / filename
            if source.is_file():
                shutil.copy2(source, destination / filename)
                descriptor = artifact(kind, relative_root / filename)
                artifacts.append(descriptor)
                copied[filename] = descriptor
        if (source_run / "workspace").is_dir():
            shutil.copytree(source_run / "workspace", destination / "workspace")
        if (source_run / "revalidation-history.json").is_file():
            shutil.copy2(source_run / "revalidation-history.json", destination / "revalidation-history.json")
            descriptor = artifact("revalidation-history", relative_root / "revalidation-history.json")
            artifacts.append(descriptor)
            revalidation_records.append({"eval_id": eval_id, "artifact": descriptor})
        evidence_runs.append({"eval_id": eval_id, "task_context_id": run.get("task_context_id"), "grader_task_context_id": run.get("grader_task_context_id"), "response_present": run.get("response_present"), "execution": run.get("execution"), "deterministic_status": run.get("deterministic_status"), "grading_status": run.get("grading", {}).get("status"), "pass_rate": run.get("grading", {}).get("pass_rate"), "execution_receipt": copied.get("execution-receipt.json"), "grading": copied.get("grading.json"), "deterministic_grading": copied.get("deterministic-grading.json"), "response": copied.get("direct-response.md"), "workspace_before_manifest": copied.get("workspace-before.json"), "workspace_after_manifest": copied.get("workspace-after.json"), "workspace_path": published_path(relative_root / "workspace")})
    image_evidence = {"passed": image_passed, "eval_id": 24, "source_name": image_source.name if image_source else None, "width": image_info.get("width") if image_info else None, "height": image_info.get("height") if image_info else None, "has_alpha": image_info.get("has_alpha") if image_info else None, "sha256": image_info.get("sha256") if image_info else None, "artifact_path": None, "document_root": image_contract["document_root"]}
    if image_source is not None and image_source.is_file():
        (staging / "image").mkdir()
        shutil.copy2(image_source, staging / "image" / image_source.name)
        image_artifact = artifact("image-canary", Path("image") / image_source.name)
        artifacts.append(image_artifact)
        image_evidence["artifact_path"] = image_artifact["path"]
    payload = {
        "schema_version": 3,
        "status": "production-ready" if production_ready else "diagnostic-failed",
        "verification_status": verification_status,
        "production_ready": production_ready,
        "trust_boundary": "local-unattested",
        "generated_at": datetime.now(timezone.utc).date().isoformat(),
        "iteration": iteration,
        "contract_sha256": contract_hash(SKILL_ROOT),
        "evaluation_scope": {"kind": scope_kind, "eval_ids": scope_ids},
        "runtime": {"runner": "scripts/run_production_evals.py", "model": EXECUTION_MODEL, "reasoning_effort": EXECUTION_REASONING_EFFORT, "planned_execution_tasks": summary.get("planned_execution_tasks"), "responses_present": summary.get("responses_present"), "valid_execution_receipts": summary.get("valid_execution_receipts"), "deterministic_passed": summary.get("deterministic_passed"), "deterministic_failed": summary.get("deterministic_failed"), "completed_independent_gradings": summary.get("completed_independent_gradings"), "telemetry_status": "unavailable", "capability_evidence_status": "unverified"},
        "artifacts": artifacts,
        "behavior": {"runs": evidence_runs, "summary": summary},
        "selection": selection,
        "review": {"status": "generated" if review_present else "missing", "artifact_path": published_path(Path("review.html")) if review_present else None, "sha256": sha256_file(staging / "review.html") if review_present else None},
        "image_canary": image_evidence,
        "revalidations": revalidation_records,
        "limitations": ["Task context IDs are harness-assigned identifiers, not raw host model context IDs.", "Raw model telemetry and tool events were unavailable and were not inferred.", "Selection evidence was reused by exact hashes; no new selection run was executed.", "Harness-only deterministic revalidation does not rerun or alter model output.", "Targeted verification is not production-ready evidence and contains no baseline, repetition, or blind comparison."],
    }
    write_json(staging / "summary.json", payload)
    descriptor, candidate_name = tempfile.mkstemp(prefix="document-writing-schema-v3-evidence-", suffix=".json")
    os.close(descriptor)
    candidate = Path(candidate_name)
    write_json(candidate, payload)
    try:
        validate_evidence_candidate(staging, published_root, candidate)
        os.replace(staging, published_root)
        production_path = SKILL_ROOT / suite["evidence"]["production_evidence"]
        replacement = production_path.parent / ".production-evidence.schema-v3.tmp"
        write_json(replacement, payload)
        os.replace(replacement, production_path)
    finally:
        if candidate.exists():
            candidate.unlink()
        if staging.exists():
            shutil.rmtree(staging)
    return {"stage": "evidence", "status": "completed" if verification_status.endswith("pass") else "diagnostic-failed", "verification_status": verification_status, "production_ready": production_ready, "evidence": str(published_root / "summary.json")}


def parse_eval_ids(raw: str | None) -> list[int] | None:
    if raw is None:
        return None
    values: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part.isdigit():
            raise ProductionEvalError("--eval-ids must be a comma-separated list of integers")
        values.append(int(part))
    return values


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("prepare", "direct-behavior-prepare", "direct-behavior-finalize", "direct-behavior-revalidate", "direct-behavior-recover", "direct-grading-prepare", "direct-grading-finalize", "aggregate", "review", "evidence"), default="prepare")
    parser.add_argument("--iteration", type=int)
    parser.add_argument("--eval-ids", help="Comma-separated iteration scope; valid only for prepare.")
    parser.add_argument("--eval-id", type=int, help="Process one eval from the prepared iteration scope.")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        suite = load_json(SUITE_PATH)
        workspace = suite_workspace(suite)
        if args.stage == "prepare":
            if args.eval_id is not None:
                raise ProductionEvalError("--eval-id is not valid for prepare; use --eval-ids")
            iteration = args.iteration or next_iteration(workspace)
            root = prepare_iteration(suite, iteration, parse_eval_ids(args.eval_ids), args.dry_run)
            reports: list[dict[str, Any]] = []
        else:
            if args.eval_ids is not None:
                raise ProductionEvalError("--eval-ids is valid only for prepare")
            iteration = args.iteration or next_iteration(workspace) - 1
            root = iteration_root(workspace, iteration)
            if not root.is_dir():
                raise ProductionEvalError(f"iteration does not exist: {root}")
            reports = []
            if args.stage == "direct-behavior-prepare":
                reports.append(direct_behavior_prepare_stage(root, suite, args.eval_id, args.dry_run))
            elif args.stage == "direct-behavior-finalize":
                reports.append(direct_behavior_finalize_stage(root, suite, args.eval_id, args.dry_run))
            elif args.stage == "direct-behavior-revalidate":
                reports.append(direct_behavior_revalidate_stage(root, suite, args.eval_id, args.dry_run))
            elif args.stage == "direct-behavior-recover":
                reports.append(direct_behavior_recover_stage(root, suite, args.eval_id, args.dry_run))
            elif args.stage == "direct-grading-prepare":
                reports.append(direct_grading_prepare_stage(root, suite, args.eval_id, args.dry_run))
            elif args.stage == "direct-grading-finalize":
                reports.append(direct_grading_finalize_stage(root, suite, args.eval_id, args.dry_run))
            elif args.stage == "aggregate":
                reports.append(aggregate_stage(root, suite, args.dry_run))
            elif args.stage == "review":
                reports.append(review_stage(root, suite, args.dry_run))
            elif args.stage == "evidence":
                reports.append(evidence_stage(root, suite, args.dry_run))
        print(json.dumps({"status": "ok", "iteration": str(root), "reports": reports}, ensure_ascii=False, indent=2))
        failed_statuses = {"not-prepared", "execution-error", "hard-gate-failed", "grading-error", "quality-failed", "diagnostic-failed"}
        failed = any(report.get("status") in failed_statuses for report in reports) or any(run.get("status") in failed_statuses for report in reports for run in report.get("runs", []))
        return EXIT_FAILURE if failed else EXIT_OK
    except ProductionEvalError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except OSError as exc:
        print(f"error: unexpected filesystem error: {exc}", file=sys.stderr)
        return EXIT_FAILURE


if __name__ == "__main__":
    raise SystemExit(main())
