#!/usr/bin/env python3
"""Validate one recorded production evaluation run from a suite contract.

The validator is intentionally independent of an LLM runner.  It verifies the
runner's manifests and transcripts so CI can reject stale, incomplete, or
fabricated evidence without needing model credentials.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import struct
import sys
import zlib
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


@dataclass
class Report:
    failures: list[str] = field(default_factory=list)
    checks: list[str] = field(default_factory=list)

    def check(self, condition: bool, text: str) -> None:
        if condition:
            self.checks.append(text)
        else:
            self.failures.append(text)

    def emit(self) -> None:
        print(json.dumps({"checks": self.checks, "failures": self.failures}, ensure_ascii=False, indent=2))


class UsageError(Exception):
    pass


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise UsageError(f"missing required JSON file: {path}") from error
    except json.JSONDecodeError as error:
        raise UsageError(f"invalid JSON in {path}: {error}") from error


def require_object(value: Any, description: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise UsageError(f"{description} must be an object")
    return value


def require_string(value: Any, description: str) -> str:
    if not isinstance(value, str) or not value:
        raise UsageError(f"{description} must be a non-empty string")
    return value


def resolve_run_file(run_root: Path, metadata: dict[str, Any], field: str, default_name: str) -> Path:
    raw = metadata.get(field, default_name)
    relative = require_string(raw, f"run metadata {field}")
    candidate = (run_root / relative).resolve()
    if run_root not in candidate.parents and candidate != run_root:
        raise UsageError(f"run metadata {field} escapes run root: {relative}")
    return candidate


def normalize_manifest(payload: Any, label: str) -> tuple[str | None, dict[str, str]]:
    object_payload = require_object(payload, f"{label} manifest")
    files = object_payload.get("files", object_payload)
    if not isinstance(files, dict):
        raise UsageError(f"{label} manifest files must be an object")
    normalized: dict[str, str] = {}
    for raw_path, raw_entry in files.items():
        path = require_string(raw_path, f"{label} manifest path").replace("\\", "/")
        segments = path.split("/")
        if (
            path.startswith("/")
            or re.match(r"^[A-Za-z]:", path)
            or any(segment in {"", ".", ".."} for segment in segments)
            or PurePosixPath(path).as_posix() != path
            or path in normalized
        ):
            raise UsageError(f"invalid or duplicate {label} manifest path: {path}")
        if isinstance(raw_entry, str):
            digest = raw_entry
        elif isinstance(raw_entry, dict):
            digest = raw_entry.get("sha256") or raw_entry.get("hash")
        else:
            raise UsageError(f"invalid manifest entry for {path}")
        digest = require_string(digest, f"manifest digest for {path}")
        if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise UsageError(f"manifest digest for {path} must be lowercase SHA-256")
        normalized[path] = digest
    manifest_hash = object_payload.get("sha256")
    if manifest_hash is not None and (
        not isinstance(manifest_hash, str)
        or re.fullmatch(r"[0-9a-f]{64}", manifest_hash) is None
    ):
        raise UsageError(f"{label} manifest sha256 must be lowercase SHA-256")
    workspace = object_payload.get("workspace_root") or object_payload.get("workspace")
    if workspace is not None and not isinstance(workspace, str):
        raise UsageError(f"{label} manifest workspace root must be a string")
    return workspace, normalized


def declared_tree_hash(payload: dict[str, Any], files: dict[str, str], label: str) -> str:
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise UsageError(f"{label} manifest entries must be an array")
    normalized_entries: list[dict[str, str]] = []
    entry_files: dict[str, str] = {}
    seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise UsageError(f"{label} manifest contains an invalid entry")
        path = entry["path"].replace("\\", "/")
        segments = path.split("/")
        if (
            entry["path"] != path
            or any(segment in {"", ".", ".."} for segment in segments)
            or PurePosixPath(path).as_posix() != path
            or path in seen
        ):
            raise UsageError(f"{label} manifest contains an invalid or duplicate entry path: {path}")
        seen.add(path)
        entry_type = entry.get("type")
        if entry_type == "directory":
            normalized_entries.append({"path": path, "type": "directory"})
        elif entry_type == "file" and re.fullmatch(r"[0-9a-f]{64}", str(entry.get("sha256", ""))):
            digest = str(entry["sha256"])
            normalized_entries.append({"path": path, "type": "file", "sha256": digest})
            entry_files[path] = digest
        else:
            raise UsageError(f"{label} manifest entry has an unsupported type or digest: {path}")
    if entry_files != files:
        raise UsageError(f"{label} manifest entries do not match files")
    encoded = json.dumps(sorted(normalized_entries, key=lambda item: item["path"]), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def manifest_entry_state(payload: dict[str, Any]) -> dict[str, str]:
    state: dict[str, str] = {}
    for entry in payload.get("entries", []):
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            continue
        if entry.get("type") == "file":
            state[entry["path"]] = f"file:{entry.get('sha256')}"
        else:
            state[entry["path"]] = str(entry.get("type"))
    return state


def load_events(path: Path) -> list[dict[str, Any]]:
    payload = load_json(path)
    if isinstance(payload, dict):
        payload = payload.get("events")
    if not isinstance(payload, list) or not all(isinstance(item, dict) for item in payload):
        raise UsageError("tool events must be an array of objects")
    return payload


def event_text(event: dict[str, Any]) -> str:
    return " ".join(str(event.get(key, "")) for key in ("tool", "name", "kind", "action", "url", "input", "output", "status")).lower()


def event_tool_name(event: dict[str, Any]) -> str:
    return str(event.get("name") or event.get("tool") or "")


def event_request_text(event: dict[str, Any]) -> str:
    return " ".join(
        (
            event_tool_name(event),
            str(event.get("url", "")),
            json.dumps(event.get("input", {}), ensure_ascii=False, sort_keys=True),
        )
    ).lower()


def actual_tree_manifest(root: Path) -> tuple[dict[str, str], str]:
    if not root.is_dir():
        raise UsageError(f"recorded workspace is not a directory: {root}")
    entries: list[dict[str, str]] = []
    files: dict[str, str] = {}
    for path in sorted(root.rglob("*"), key=lambda value: value.as_posix()):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            raise UsageError(f"workspace contains a symbolic link: {relative}")
        if path.is_file():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            entries.append({"path": relative, "type": "file", "sha256": digest})
            files[relative] = digest
        elif path.is_dir():
            entries.append({"path": relative, "type": "directory"})
        else:
            raise UsageError(f"workspace contains a special file: {relative}")
    encoded = json.dumps(entries, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return files, hashlib.sha256(encoded).hexdigest()


def expected_before_files(suite_path: Path, suite: dict[str, Any], metadata: dict[str, Any]) -> dict[str, str]:
    eval_id = metadata.get("eval_id")
    if not isinstance(eval_id, int):
        raise UsageError("run metadata eval_id must be an integer")
    skill_root = suite_path.parent.parent
    behavior = require_object(suite.get("behavior"), "production suite behavior")
    eval_manifest_path = skill_root / require_string(behavior.get("eval_manifest"), "behavior eval_manifest")
    eval_manifest = require_object(load_json(eval_manifest_path), "behavior eval manifest")
    eval_item = next(
        (item for item in eval_manifest.get("evals", []) if isinstance(item, dict) and item.get("id") == eval_id),
        None,
    )
    eval_item = require_object(eval_item, f"behavior eval {eval_id}")
    fixture_files = eval_item.get("files", [])
    if not isinstance(fixture_files, list) or not all(isinstance(item, str) for item in fixture_files):
        raise UsageError(f"behavior eval {eval_id} files must be a string array")
    if not fixture_files:
        return {}
    fixture_roots: set[PurePosixPath] = set()
    for relative in fixture_files:
        parts = PurePosixPath(relative.replace("\\", "/")).parts
        try:
            fixture_index = parts.index("fixtures")
            fixture_roots.add(PurePosixPath(*parts[: fixture_index + 2]))
        except (ValueError, IndexError) as error:
            raise UsageError(f"invalid fixture path for eval {eval_id}: {relative}") from error
    if len(fixture_roots) != 1:
        raise UsageError(f"eval {eval_id} must use exactly one fixture root")
    fixture_root = next(iter(fixture_roots))
    destination_value = behavior.get("fixture_destinations", {}).get(str(eval_id), "input")
    destination = PurePosixPath(require_string(destination_value, f"fixture destination for eval {eval_id}"))
    expected: dict[str, str] = {}
    for relative in fixture_files:
        source_relative = PurePosixPath(relative.replace("\\", "/"))
        source = skill_root / source_relative
        if not source.is_file():
            raise UsageError(f"fixture file is missing: {source_relative}")
        child = source_relative.relative_to(fixture_root)
        output_relative = (destination / child).as_posix()
        expected[output_relative] = hashlib.sha256(source.read_bytes()).hexdigest()
    return expected


def expected_entry_shapes(files: dict[str, str]) -> set[tuple[str, str]]:
    shapes: set[tuple[str, str]] = {(path, "file") for path in files}
    for relative in files:
        parent = PurePosixPath(relative).parent
        while parent != PurePosixPath("."):
            shapes.add((parent.as_posix(), "directory"))
            parent = parent.parent
    return shapes


def transcript_evidence(path: Path) -> tuple[list[dict[str, Any]], str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError as error:
        raise UsageError(f"missing transcript: {path}") from error
    if not lines:
        raise UsageError(f"transcript is empty: {path}")
    events: list[dict[str, Any]] = []
    by_id: dict[str, dict[str, Any]] = {}
    assistant_text: list[str] = []
    for line_number, line in enumerate(lines, start=1):
        try:
            event = json.loads(line)
        except json.JSONDecodeError as error:
            raise UsageError(f"invalid transcript JSON at line {line_number}: {error}") from error
        if event.get("type") == "assistant":
            for block in event.get("message", {}).get("content", []):
                if block.get("type") == "text" and isinstance(block.get("text"), str):
                    assistant_text.append(block["text"])
                elif block.get("type") == "tool_use":
                    record = {
                        "line": line_number,
                        "tool_use_id": block.get("id"),
                        "name": block.get("name"),
                        "input": block.get("input", {}),
                        "status": "pending",
                    }
                    events.append(record)
                    if isinstance(block.get("id"), str):
                        by_id[block["id"]] = record
        elif event.get("type") == "user":
            for block in event.get("message", {}).get("content", []):
                tool_use_id = block.get("tool_use_id")
                if block.get("type") != "tool_result" or not isinstance(tool_use_id, str):
                    continue
                record = by_id.get(tool_use_id)
                if record is None:
                    raise UsageError(f"transcript tool_result has no matching tool_use: {tool_use_id}")
                record["status"] = "error" if block.get("is_error") is True else "success"
                record["output"] = block.get("content", "")
    return events, "\n\n".join(assistant_text).strip()


def matches_path(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def validate_png(path: Path, specification: dict[str, Any], report: Report) -> None:
    try:
        content = path.read_bytes()
    except FileNotFoundError:
        report.check(False, f"required PNG exists: {path.name}")
        return
    valid_signature = content.startswith(PNG_SIGNATURE)
    report.check(valid_signature, f"PNG signature is valid: {path.name}")
    if not valid_signature:
        return
    position = len(PNG_SIGNATURE)
    chunks: list[tuple[bytes, bytes]] = []
    chunks_valid = True
    while position < len(content):
        if position + 12 > len(content):
            chunks_valid = False
            break
        length = struct.unpack(">I", content[position : position + 4])[0]
        chunk_type = content[position + 4 : position + 8]
        data_start = position + 8
        data_end = data_start + length
        crc_end = data_end + 4
        if crc_end > len(content):
            chunks_valid = False
            break
        data = content[data_start:data_end]
        expected_crc = struct.unpack(">I", content[data_end:crc_end])[0]
        actual_crc = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            chunks_valid = False
            break
        chunks.append((chunk_type, data))
        position = crc_end
        if chunk_type == b"IEND":
            break
    report.check(chunks_valid and position == len(content), f"PNG chunks and CRCs are valid: {path.name}")
    if not chunks_valid or position != len(content) or not chunks:
        return
    ihdr_type, ihdr = chunks[0]
    has_valid_ihdr = ihdr_type == b"IHDR" and len(ihdr) == 13
    report.check(has_valid_ihdr, f"PNG IHDR is valid and first: {path.name}")
    if not has_valid_ihdr:
        return
    idat = b"".join(data for chunk_type, data in chunks if chunk_type == b"IDAT")
    has_iend = chunks[-1][0] == b"IEND" and chunks[-1][1] == b""
    report.check(bool(idat), f"PNG contains image data: {path.name}")
    report.check(has_iend, f"PNG terminates with IEND: {path.name}")
    if not idat or not has_iend:
        return
    try:
        decoded = zlib.decompress(idat)
    except zlib.error:
        decoded = b""
    report.check(bool(decoded), f"PNG image data decompresses: {path.name}")
    width, height, bit_depth, color_type, compression, filter_method, interlace = struct.unpack(">IIBBBBB", ihdr)
    report.check(width > 0 and height > 0, f"PNG dimensions are positive: {path.name}")
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
    valid_layout = (
        channels is not None
        and bit_depth in allowed_depths.get(color_type, set())
        and compression == 0
        and filter_method == 0
        and interlace == 0
        and (color_type != 3 or palette_valid)
    )
    report.check(valid_layout, f"PNG uses a supported non-interlaced layout: {path.name}")
    if valid_layout:
        expected_bytes = height * (1 + ((width * channels * bit_depth + 7) // 8))
        report.check(len(decoded) == expected_bytes, f"PNG contains complete scanlines: {path.name}")
        row_bytes = (width * channels * bit_depth + 7) // 8
        filters_valid = len(decoded) == expected_bytes and all(decoded[row * (row_bytes + 1)] <= 4 for row in range(height))
        report.check(filters_valid, f"PNG scanline filters are valid: {path.name}")
    if "width" in specification:
        report.check(width == specification["width"], f"PNG width matches contract: {path.name}")
    if "height" in specification:
        report.check(height == specification["height"], f"PNG height matches contract: {path.name}")


def as_string_list(value: Any, description: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise UsageError(f"{description} must be an array of non-empty strings")
    return value


def select_case(suite: dict[str, Any], case_name: str) -> dict[str, Any]:
    cases = suite.get("cases")
    if isinstance(cases, dict):
        case = cases.get(case_name)
    elif isinstance(cases, list):
        case = next((item for item in cases if isinstance(item, dict) and item.get("name") == case_name), None)
    else:
        raise UsageError("production suite cases must be an object or array")
    return require_object(case, f"production suite case {case_name}")


def validate(suite_path: Path, run_root: Path, case_override: str | None) -> int:
    suite = require_object(load_json(suite_path), "production suite")
    metadata = require_object(load_json(run_root / "run.json"), "run metadata")
    case_name = case_override or metadata.get("case_name")
    case = select_case(suite, require_string(case_name, "case name"))
    report = Report()

    before_path = resolve_run_file(run_root, metadata, "before_manifest", "before-manifest.json")
    after_path = resolve_run_file(run_root, metadata, "after_manifest", "after-manifest.json")
    before_payload = require_object(load_json(before_path), "before manifest")
    after_payload = require_object(load_json(after_path), "after manifest")
    before_workspace, before = normalize_manifest(before_payload, "before")
    after_workspace, after = normalize_manifest(after_payload, "after")
    report.check(before_workspace == after_workspace, "before/after manifests describe the same workspace")
    report.check(before_payload.get("sha256") == declared_tree_hash(before_payload, before, "before"), "before manifest tree hash is canonical")
    report.check(after_payload.get("sha256") == declared_tree_hash(after_payload, after, "after"), "after manifest tree hash is canonical")
    expected_before = expected_before_files(suite_path, suite, metadata)
    report.check(before == expected_before, "before manifest matches canonical package fixtures")
    before_shapes = {
        (entry.get("path"), entry.get("type"))
        for entry in before_payload.get("entries", [])
        if isinstance(entry, dict)
    }
    report.check(before_shapes == expected_entry_shapes(expected_before), "before manifest directories match canonical package fixtures")
    actual_workspace = run_root / "workspace"
    actual_files, actual_tree_hash = actual_tree_manifest(actual_workspace)
    report.check(actual_files == after, "after manifest matches the preserved workspace files")
    report.check(after_payload.get("sha256") == actual_tree_hash, "after manifest tree hash matches the preserved workspace")
    before_state = manifest_entry_state(before_payload)
    after_state = manifest_entry_state(after_payload)
    changes = {path for path in set(before_state) | set(after_state) if before_state.get(path) != after_state.get(path)}
    allowed = as_string_list(case.get("allowed_change_paths"), "allowed_change_paths")
    forbidden = as_string_list(case.get("forbidden_change_paths"), "forbidden_change_paths")
    required = as_string_list(case.get("required_change_paths"), "required_change_paths")
    report.check(bool(changes) or not required, "workspace change set is available")
    for changed in sorted(changes):
        report.check(matches_path(changed, allowed), f"changed path is allowed: {changed}")
        report.check(not matches_path(changed, forbidden), f"changed path is not forbidden: {changed}")
    for expected in required:
        report.check(any(fnmatch.fnmatchcase(path, expected) for path in changes), f"required change occurred: {expected}")

    response_path = resolve_run_file(run_root, metadata, "response", "response.txt")
    try:
        response = response_path.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise UsageError(f"missing response file: {response_path}") from error
    transcript_path = resolve_run_file(run_root, metadata, "transcript", "transcript.stream.jsonl")
    events, transcript_response = transcript_evidence(transcript_path)
    report.check(response.strip() == transcript_response.strip(), "response is derived from the recorded transcript")
    response_rules = require_object(case.get("response", {}), "response rules")
    question_count = len(re.findall(r"(?:^|\n)\s*(?:[-*]\s*)?[^\n?]{1,240}\?\s*$", response))
    max_questions = response_rules.get("max_questions")
    if max_questions is not None:
        if not isinstance(max_questions, int) or max_questions < 0:
            raise UsageError("response max_questions must be a non-negative integer")
        report.check(question_count <= max_questions, f"response question count <= {max_questions}")
    for pattern in as_string_list(response_rules.get("required_patterns"), "response required_patterns"):
        report.check(re.search(pattern, response, re.IGNORECASE | re.MULTILINE) is not None, f"response contains required pattern: {pattern}")
    for pattern in as_string_list(response_rules.get("forbidden_patterns"), "response forbidden_patterns"):
        report.check(re.search(pattern, response, re.IGNORECASE | re.MULTILINE) is None, f"response excludes forbidden pattern: {pattern}")

    events_path = resolve_run_file(run_root, metadata, "tool_events", "tool-events.json")
    events_payload = load_json(events_path)
    report.check(
        isinstance(events_payload, dict)
        and events_payload.get("provenance") == "agent-reported-not-raw-telemetry",
        "tool events disclose agent-reported provenance",
    )
    recorded_events = load_events(events_path)
    recorded_by_id = {
        event.get("tool_use_id"): event
        for event in recorded_events
        if isinstance(event.get("tool_use_id"), str)
    }
    for event in events:
        tool_use_id = event.get("tool_use_id")
        recorded = recorded_by_id.get(tool_use_id) if isinstance(tool_use_id, str) else None
        report.check(
            recorded is not None
            and event_tool_name(recorded) == event_tool_name(event)
            and recorded.get("input") == event.get("input")
            and str(recorded.get("status")) == str(event.get("status"))
            and recorded.get("output") == event.get("output"),
            f"reported tool claim matches reconstructed transcript: {tool_use_id or event_tool_name(event)}",
        )
    forbidden_tools = as_string_list(case.get("forbidden_tool_calls"), "forbidden_tool_calls")
    for pattern in forbidden_tools:
        report.check(not any(re.search(pattern, event_tool_name(event), re.IGNORECASE) for event in events), f"forbidden reported capability claim is absent: {pattern}")
    for pattern in as_string_list(case.get("required_tool_calls"), "required_tool_calls"):
        report.check(any(re.search(pattern, event_tool_name(event), re.IGNORECASE) for event in events), f"required reported capability claim is present: {pattern}")
    for pattern in as_string_list(case.get("required_web_events"), "required_web_events"):
        found = any(
            re.search(r"^(?:WebFetch|web[_ -]?(?:open|fetch)|browser.*(?:open|fetch))$", event_tool_name(event), re.IGNORECASE)
            and re.search(pattern, event_request_text(event), re.IGNORECASE)
            and str(event.get("status", "unknown")).lower() in {"success", "ok", "completed"}
            for event in events
        )
        report.check(found, f"successful reported web open/fetch claim matches: {pattern}")
    for pattern in as_string_list(case.get("forbidden_web_events"), "forbidden_web_events"):
        found = any(
            re.search(r"^(?:WebSearch|WebFetch|web[_ -]?(?:search|open|fetch)|browser.*(?:search|open|fetch))$", event_tool_name(event), re.IGNORECASE)
            and re.search(pattern, event_request_text(event), re.IGNORECASE)
            for event in events
        )
        report.check(not found, f"no reported web research claim matches excluded scope: {pattern}")

    png_rules = case.get("png")
    if png_rules is not None:
        if not isinstance(png_rules, list) or not all(isinstance(item, dict) for item in png_rules):
            raise UsageError("png must be an array of objects")
        for item in png_rules:
            relative = require_string(item.get("path"), "PNG path")
            candidate = (run_root / relative).resolve()
            if run_root not in candidate.parents:
                raise UsageError(f"PNG path escapes run root: {relative}")
            validate_png(candidate, item, report)

    report.emit()
    return 0 if not report.failures else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", type=Path, required=True)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--case")
    args = parser.parse_args()
    try:
        return validate(args.suite.resolve(), args.run.resolve(), args.case)
    except UsageError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
