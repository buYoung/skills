#!/usr/bin/env python3
"""Self-tests for document-writing eval validators (no external dependencies)."""

from __future__ import annotations

import json
import hashlib
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

from validate_eval_run import UsageError, normalize_manifest
from validate_package import inspect_png
from validate_package import blind_gate_passes, blind_verdict_has_concrete_evidence, production_iteration_is_accepted, resolved_blind_winner
from run_production_evals import (
    ProductionEvalError,
    behavior_job_id,
    direct_report_status_is_usable,
    direct_agent_report_contract,
    normalize_direct_report_events,
    public_direct_task,
    expected_run_dir,
    validate_direct_run_integrity,
)


ROOT = Path(__file__).resolve().parents[1]
VALIDATORS = ROOT / "evals" / "validators"
RUN_VALIDATOR = ROOT / "scripts" / "validate_eval_run.py"


def write(root: Path, relative: str, content: str) -> None:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def copy_tree(source: Path, destination: Path) -> None:
    shutil.copytree(source, destination)


def run_node(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["node", str(VALIDATORS / script), *args], text=True, capture_output=True, check=False)


def tree_manifest(root: Path) -> dict[str, object]:
    entries: list[dict[str, str]] = []
    files: dict[str, str] = {}
    for path in sorted(root.rglob("*"), key=lambda value: value.as_posix()):
        relative = path.relative_to(root).as_posix()
        if path.is_file():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            entries.append({"path": relative, "type": "file", "sha256": digest})
            files[relative] = digest
        elif path.is_dir():
            entries.append({"path": relative, "type": "directory"})
    encoded = json.dumps(entries, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return {"workspace_root": "isolated", "entries": entries, "files": files, "sha256": hashlib.sha256(encoded).hexdigest()}


def png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)


def valid_png() -> bytes:
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    image_data = zlib.compress(b"\x00\x00\x00\x00")
    return b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", ihdr) + png_chunk(b"IDAT", image_data) + png_chunk(b"IEND", b"")


def undersized_declared_png() -> bytes:
    ihdr = struct.pack(">IIBBBBB", 1024, 500, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", ihdr) + png_chunk(b"IDAT", zlib.compress(b"x")) + png_chunk(b"IEND", b"")


def invalid_depth_png() -> bytes:
    ihdr = struct.pack(">IIBBBBB", 1024, 500, 0, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", ihdr) + png_chunk(b"IDAT", zlib.compress(b"\x00" * 500)) + png_chunk(b"IEND", b"")


def empty_palette_png() -> bytes:
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 3, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", ihdr) + png_chunk(b"PLTE", b"") + png_chunk(b"IDAT", zlib.compress(b"\x00\x00")) + png_chunk(b"IEND", b"")


class ValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="document-writing-eval-validators-")
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def existing_fixture(self) -> Path:
        fixture = self.root / "existing-fixture"
        write(fixture, "index.md", "# Existing system\n\n- [Tokens](tokens.md)\n")
        write(fixture, "tokens.md", "# Tokens\n\nDo not change `blue-500`.\n")
        write(fixture, "notes.md", "# Team notes\n\nKeep this exact custom note.\n")
        return fixture

    def add_owner_documents(self, result: Path, filler: bool = False) -> None:
        index = (result / "index.md").read_text(encoding="utf-8")
        write(result, "index.md", index + "- [Content](content.md)\n- [Accessibility](accessibility.md)\n")
        content = "# Content guidance\n\nUse concise labels, explain outcomes before actions, and avoid ambiguous terms. Ensure every control has a durable name that remains understandable when read outside its visual context.\n"
        accessibility = "# Accessibility guidance\n\nProvide keyboard access, visible focus, programmatic names, and reduced-motion behavior. Do not rely on color alone, and ensure error messages explain both the problem and the available recovery action.\n"
        write(result, "content.md", "# Placeholder\n" if filler else content)
        write(result, "accessibility.md", accessibility)

    def test_existing_update_positive_and_negative_controls(self) -> None:
        fixture = self.existing_fixture()
        result = self.root / "existing-result"
        copy_tree(fixture, result)
        self.add_owner_documents(result)
        self.assertEqual(run_node("validate_existing_update.mjs", str(fixture), str(result)).returncode, 0)

        no_op = self.root / "existing-no-op"
        copy_tree(fixture, no_op)
        self.assertEqual(run_node("validate_existing_update.mjs", str(fixture), str(no_op)).returncode, 1)

        filler = self.root / "existing-filler"
        copy_tree(fixture, filler)
        self.add_owner_documents(filler, filler=True)
        self.assertEqual(run_node("validate_existing_update.mjs", str(fixture), str(filler)).returncode, 1)

        outside = self.root / "existing-outside"
        copy_tree(fixture, outside)
        self.add_owner_documents(outside)
        write(outside, "unrelated.md", "# Unexpected\n")
        self.assertEqual(run_node("validate_existing_update.mjs", str(fixture), str(outside)).returncode, 1)

    def test_preservation_root_and_tree_guards(self) -> None:
        fixture = self.root / "preserve-fixture"
        write(fixture, "stores/owner.md", "# Owner\n")
        result = self.root / "preserve-result"
        copy_tree(fixture, result)
        self.assertEqual(run_node("validate_preservation.mjs", str(fixture), str(result), "--exact-tree").returncode, 0)
        write(result, "outside.md", "# Outside\n")
        self.assertEqual(run_node("validate_preservation.mjs", str(fixture), str(result), "--exact-tree").returncode, 1)
        self.assertEqual(run_node("validate_preservation.mjs", str(fixture), str(fixture)).returncode, 2)
        self.assertEqual(run_node("validate_preservation.mjs", str(fixture), str(fixture / "stores")).returncode, 2)
        self.assertEqual(run_node("validate_preservation.mjs", str(self.root / "missing"), str(result)).returncode, 2)
        empty = self.root / "empty"
        empty.mkdir()
        self.assertEqual(run_node("validate_preservation.mjs", str(empty), str(result)).returncode, 2)
        linked = self.root / "linked-fixture"
        os.symlink(fixture, linked)
        self.assertEqual(run_node("validate_preservation.mjs", str(linked), str(result)).returncode, 2)
        os.mkfifo(result / "special")
        self.assertEqual(run_node("validate_preservation.mjs", str(fixture), str(result)).returncode, 2)

    def noncanonical_fixture(self) -> Path:
        fixture = self.root / "store-fixture"
        write(fixture, "index.md", "# Asset system\n\n- [Store](stores/play-store-assets.md)\n")
        write(fixture, "notes.md", "# Preserve me\n\nUnrelated team note.\n")
        write(fixture, "stores/play-store-assets.md", "# Google Play assets\n\nOld source statement.\n\n## Asset roles\n\nScreenshots show the signed-in product experience.\n")
        return fixture

    def test_noncanonical_meaningful_update_and_duplicate_guards(self) -> None:
        fixture = self.noncanonical_fixture()
        result = self.root / "store-result"
        copy_tree(fixture, result)
        write(result, "stores/play-store-assets.md", "# Google Play assets\n\nVerified: 2026-08-27\n\nOfficial source: https://support.google.com/googleplay/android-developer/answer/9866151\n\nUse current operator documentation and record a verification date before publishing.\n\n## Asset roles\n\nScreenshots show the signed-in product experience.\n")
        self.assertEqual(run_node("validate_noncanonical_store.mjs", str(fixture), str(result)).returncode, 0)

        whitespace = self.root / "store-whitespace"
        copy_tree(fixture, whitespace)
        write(whitespace, "stores/play-store-assets.md", "\n# Google Play assets\n\nOld source statement.\n\n## Asset roles\n\nScreenshots show the signed-in product experience.\n<!-- new note -->\n")
        self.assertEqual(run_node("validate_noncanonical_store.mjs", str(fixture), str(whitespace)).returncode, 1)

        duplicate = self.root / "store-duplicate"
        copy_tree(result, duplicate)
        write(duplicate, "stores/google-play.mdx", "---\nstorefront: Google Play\n---\n# Alternate asset owner\n")
        self.assertEqual(run_node("validate_noncanonical_store.mjs", str(fixture), str(duplicate)).returncode, 1)

        destructive = self.root / "store-destructive"
        copy_tree(fixture, destructive)
        write(destructive, "stores/play-store-assets.md", "# Google Play assets\n\nVerified: 2026-08-27\n\nhttps://support.google.com/googleplay/android-developer/answer/9866151\n")
        self.assertEqual(run_node("validate_noncanonical_store.mjs", str(fixture), str(destructive)).returncode, 1)

    def run_contract(self, case: str, response: str, before: dict[str, str], after: dict[str, str], events: list[dict[str, str]], png: bool = False, truncated_png: bool = False, extra_empty_dir: bool = False) -> subprocess.CompletedProcess[str]:
        run_root = Path(tempfile.mkdtemp(prefix=f"run-{case}-", dir=self.root))
        skill_root = self.root / "contract-skill"
        suite_path = skill_root / "evals" / "suite.json"
        suite = {
            "schema_version": 1,
            "behavior": {"eval_manifest": "evals/evals.json", "fixture_destinations": {}},
            "cases": {
                "positive": {
                    "allowed_change_paths": ["docs", "docs/**"],
                    "required_change_paths": ["docs/**"],
                    "forbidden_change_paths": ["outside/**"],
                    "response": {"max_questions": 0, "required_patterns": ["completed"]},
                    "required_tool_calls": ["imagegen"],
                    "required_web_events": ["official.example"],
                    "png": [{"path": "output/feature.png", "width": 1, "height": 1}],
                },
                "web-disabled": {
                    "allowed_change_paths": [],
                    "forbidden_tool_calls": ["websearch|webfetch|browser"],
                    "response": {"max_questions": 0, "forbidden_patterns": ["https?://"]},
                },
            },
        }
        suite_path.parent.mkdir(parents=True, exist_ok=True)
        suite_path.write_text(json.dumps(suite), encoding="utf-8")
        (skill_root / "evals" / "evals.json").write_text(json.dumps({"skill_name": "test", "evals": [{"id": 1, "files": []}]}), encoding="utf-8")
        metadata = {"case_name": case, "eval_id": 1, "before_manifest": "before.json", "after_manifest": "after.json", "response": "response.txt", "tool_events": "tools.json", "transcript": "transcript.jsonl"}
        (run_root / "run.json").write_text(json.dumps(metadata), encoding="utf-8")
        before_root = run_root / "before-workspace"
        workspace = run_root / "workspace"
        before_root.mkdir()
        workspace.mkdir()
        for relative, content in before.items():
            write(before_root, relative, content)
        for relative, content in after.items():
            write(workspace, relative, content)
        if extra_empty_dir:
            (workspace / "unexpected-empty-directory").mkdir()
        (run_root / "before.json").write_text(json.dumps(tree_manifest(before_root)), encoding="utf-8")
        (run_root / "after.json").write_text(json.dumps(tree_manifest(workspace)), encoding="utf-8")
        (run_root / "response.txt").write_text(response, encoding="utf-8")
        recorded_events = []
        transcript = []
        tool_blocks = []
        for index, event in enumerate(events, start=1):
            tool_use_id = f"tool-{index}"
            name = event.get("name") or event.get("tool") or "unknown"
            tool_input = {"url": event.get("url", ""), "input": event.get("input", "")}
            tool_blocks.append({"type": "tool_use", "id": tool_use_id, "name": name, "input": tool_input})
            recorded_events.append({"tool_use_id": tool_use_id, "name": name, "input": tool_input, "status": event.get("status", "success"), "output": "result"})
        transcript.append({"type": "assistant", "message": {"content": [{"type": "text", "text": response}, *tool_blocks]}})
        if recorded_events:
            transcript.append({"type": "user", "message": {"content": [
                {"type": "tool_result", "tool_use_id": event["tool_use_id"], "is_error": event["status"] == "error", "content": "result"}
                for event in recorded_events
            ]}})
        (run_root / "transcript.jsonl").write_text("\n".join(json.dumps(item) for item in transcript) + "\n", encoding="utf-8")
        (run_root / "tools.json").write_text(json.dumps({"provenance": "agent-reported-not-raw-telemetry", "events": recorded_events}), encoding="utf-8")
        if png or truncated_png:
            target = run_root / "output" / "feature.png"
            target.parent.mkdir()
            target.write_bytes(
                b"\x89PNG\r\n\x1a\n" + (13).to_bytes(4, "big") + b"IHDR" + (1).to_bytes(4, "big") + (1).to_bytes(4, "big") + b"\x08\x02\x00\x00\x00"
                if truncated_png
                else valid_png()
            )
        return subprocess.run([sys.executable, str(RUN_VALIDATOR), "--suite", str(suite_path), "--run", str(run_root)], text=True, capture_output=True, check=False)

    def test_run_validator_positive_and_negative_controls(self) -> None:
        before = {}
        after = {"docs/index.md": "after"}
        events = [{"tool": "imagegen", "status": "success"}, {"tool": "web_open", "url": "https://official.example/rules", "status": "success"}]
        self.assertEqual(self.run_contract("positive", "completed", before, after, events, png=True).returncode, 0)
        failed_web = [{"tool": "imagegen", "status": "success"}, {"tool": "web_fetch", "url": "https://official.example/rules", "status": "error"}]
        self.assertEqual(self.run_contract("positive", "completed", before, after, failed_web, png=True).returncode, 1)
        self.assertEqual(self.run_contract("positive", "completed", before, after, events, truncated_png=True).returncode, 1)
        self.assertEqual(self.run_contract("positive", "completed", before, {"outside/leak.md": "after"}, events, png=True).returncode, 1)
        self.assertEqual(self.run_contract("web-disabled", "Found https://fabricated.invalid", before, before, [], png=False).returncode, 1)
        self.assertEqual(self.run_contract("web-disabled", "No source is available.", before, before, [], extra_empty_dir=True).returncode, 1)

    def test_package_png_inspection_rejects_truncated_data(self) -> None:
        complete = self.root / "complete.png"
        complete.write_bytes(valid_png())
        self.assertEqual(inspect_png(complete), (1, 1, False))
        truncated = self.root / "truncated.png"
        truncated.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + b"\x00" * 13)
        self.assertIsNone(inspect_png(truncated))
        undersized = self.root / "undersized.png"
        undersized.write_bytes(undersized_declared_png())
        self.assertIsNone(inspect_png(undersized))
        invalid_depth = self.root / "invalid-depth.png"
        invalid_depth.write_bytes(invalid_depth_png())
        self.assertIsNone(inspect_png(invalid_depth))
        empty_palette = self.root / "empty-palette.png"
        empty_palette.write_bytes(empty_palette_png())
        self.assertIsNone(inspect_png(empty_palette))

    def test_manifest_normalization_rejects_escape_and_collisions(self) -> None:
        digest = "0" * 64
        with self.assertRaises(UsageError):
            normalize_manifest({"files": {"..\\outside.md": digest}}, "test")
        with self.assertRaises(UsageError):
            normalize_manifest({"files": {"a/b.md": digest, "a\\b.md": digest}}, "test")
        with self.assertRaises(UsageError):
            normalize_manifest({"files": {"safe.md": "not-a-hash"}}, "test")

    def test_direct_report_normalization_preserves_provenance(self) -> None:
        before_root = self.root / "direct-before"
        after_root = self.root / "direct-after"
        before_root.mkdir()
        write(after_root, "docs/index.md", "# Result\n")
        report = {
            "status": "completed",
            "model": "gpt-5.6-luna",
            "reasoning_effort": "medium",
            "telemetry_status": "available",
            "duration_ms": 1,
            "total_tokens": 1,
            "return_code": 0,
            "timed_out": False,
            "stderr": "",
            "tool_events": [
                {
                    "name": "WebFetch",
                    "input": {"url": "https://official.example/rules"},
                    "status": "success",
                    "output": "opened successfully",
                }
            ],
            "produced_paths": ["docs/index.md"],
            "context_id": "test-direct-context",
        }
        events = normalize_direct_report_events(report, tree_manifest(before_root), tree_manifest(after_root))
        self.assertTrue(direct_report_status_is_usable(report, 19))
        self.assertIn("WebFetch", [event["name"] for event in events])
        self.assertNotIn("Edit", [event["name"] for event in events])
        self.assertTrue(all(event["provenance"] == "agent-reported-not-raw-telemetry" for event in events))

    def test_direct_report_observed_mutation_is_not_reported_as_write(self) -> None:
        before_root = self.root / "observed-before"
        after_root = self.root / "observed-after"
        before_root.mkdir()
        write(after_root, "docs/index.md", "# Result\n")
        events = normalize_direct_report_events({"tool_events": []}, tree_manifest(before_root), tree_manifest(after_root))
        self.assertEqual(events, [])
        with self.assertRaises(ProductionEvalError):
            normalize_direct_report_events({}, tree_manifest(before_root), tree_manifest(after_root))
        self.assertFalse(direct_report_status_is_usable({"status": "blocked"}, 19))
        self.assertFalse(direct_report_status_is_usable({"status": "execution-error"}, 19))

    def test_direct_report_failed_web_access_stays_failed(self) -> None:
        manifest = tree_manifest(self.root)
        report = {
            "tool_events": [
                {"name": "WebFetch", "input": {"url": "https://official.example/blocked"}, "status": "error", "output": "unavailable: 429 Too Many Requests"},
                {"name": "WebFetch", "input": {"url": "https://official.example/open"}, "status": "success", "output": "opened and used"},
            ],
            "web_fetch_urls": ["https://unattested.example/not-a-tool-event"],
        }
        events = normalize_direct_report_events(report, manifest, manifest)
        statuses = {event["input"]["url"]: event["status"] for event in events}
        self.assertEqual(statuses["https://official.example/blocked"], "error")
        self.assertEqual(statuses["https://official.example/open"], "success")
        self.assertNotIn("https://unattested.example/not-a-tool-event", statuses)

    def integrity_case(
        self,
        report: dict[str, object],
        before_root: Path,
        after_root: Path,
        contract: dict[str, object] | None = None,
        configuration: str = "with_skill",
        eval_id: int = 19,
        response: str = "completed",
    ) -> list[str]:
        run_dir = self.root / "integrity-run"
        run_dir.mkdir(exist_ok=True)
        return validate_direct_run_integrity(
            run_dir,
            after_root,
            tree_manifest(before_root),
            tree_manifest(after_root),
            report,
            contract or {},
            configuration,
            response,
        )

    def test_direct_integrity_negative_controls(self) -> None:
        before = self.root / "integrity-before"
        after = self.root / "integrity-after"
        before.mkdir()
        after.mkdir()

        base = {
            "status": "completed",
            "model": "gpt-5.6-luna",
            "reasoning_effort": "medium",
            "telemetry_status": "available",
            "duration_ms": 1,
            "total_tokens": 1,
            "return_code": 0,
            "timed_out": False,
            "stderr": "",
            "produced_paths": [],
            "tool_events": [],
        }
        fake_write = {**base, "tool_events": [{"name": "Write", "input": {"path": "docs/index.md"}, "status": "success", "output": "ok"}]}
        self.assertTrue(self.integrity_case(fake_write, before, after))

        mutating = {**base, "tool_events": [{"name": "MCP", "input": {"operation": "update"}, "status": "success", "output": "ok"}]}
        self.assertTrue(self.integrity_case(mutating, before, after, {"deny_write_tools": True}, eval_id=25))

        write(after, "docs/index.md", "changed")
        clarification = {**base, "status": "clarification_required", "produced_paths": ["docs/index.md"]}
        self.assertTrue(self.integrity_case(clarification, before, after, configuration="with_skill", eval_id=21))
        (after / "docs/index.md").unlink()

        self.assertTrue(self.integrity_case(base, before, after, {"required_capabilities": ["web"]}, eval_id=19))
        without_read = {**base, "tool_events": [{"name": "Read", "input": {"path": "../with_skill/SKILL.md"}, "status": "success", "output": "leak"}]}
        self.assertTrue(self.integrity_case(without_read, before, after, configuration="without_skill"))
        without_bash_read = {**base, "tool_events": [{"name": "Bash", "input": {"command": "sed -n 1,20p /repo/skills/document-writing/SKILL.md"}, "status": "success", "output": "leak"}]}
        self.assertTrue(self.integrity_case(without_bash_read, before, after, configuration="without_skill"))

        harness_write = {**base, "tool_events": [{"name": "HarnessArtifactWrite", "input": {"path": "direct-response.md"}, "status": "success", "output": "ok"}]}
        self.assertFalse(self.integrity_case(harness_write, before, after, {"deny_write_tools": True}, eval_id=25))
        local_mcp = {**base, "tool_events": [{"name": "MCP", "input": {"operation": "read_local_index"}, "status": "success", "output": "ok"}]}
        self.assertFalse(self.integrity_case(
            local_mcp,
            before,
            after,
            {"denied_capabilities": ["web"], "required_tool_calls": ["(?:Read|Bash)"]},
            eval_id=25,
        ))
        own_task_read = {**base, "tool_events": [{"name": "Read", "input": {"path": str(self.root / "integrity-run" / "direct-task.json")}, "status": "success", "output": "ok"}]}
        self.assertFalse(self.integrity_case(own_task_read, before, after, configuration="without_skill"))
        sibling_read = {**base, "tool_events": [{"name": "Read", "input": {"path": "/tmp/iteration-10/behavior/eval/with_skill/run-1/direct-response.md"}, "status": "success", "output": "leak"}]}
        self.assertTrue(self.integrity_case(sibling_read, before, after, configuration="without_skill"))

        array_before = self.root / "array-before"
        array_after = self.root / "array-after"
        array_before.mkdir()
        write(array_after, "docs/a.md", "a")
        write(array_after, "docs/b.md", "b")
        array_write = {
            **base,
            "produced_paths": ["docs/a.md", "docs/b.md"],
            "tool_events": [{"name": "Write", "input": {"paths": ["docs/a.md", "docs/b.md"]}, "status": "success", "output": "ok"}],
        }
        self.assertFalse(self.integrity_case(
            array_write,
            array_before,
            array_after,
            {"allowed_change_paths": ["docs/**"]},
        ))

        missing_completion = {**base}
        self.assertTrue(self.integrity_case(
            missing_completion,
            before,
            after,
            response="`docs/missing`에 문서를 작성했습니다.",
        ))

        directory_write = {**base, "tool_events": [{"name": "Write", "input": {"path": "docs/"}, "status": "success", "output": "ok"}]}
        self.assertTrue(self.integrity_case(directory_write, before, after))
        outside_write = {**base, "tool_events": [{"name": "Write", "input": {"path": "../outside.md"}, "status": "success", "output": "ok"}]}
        self.assertTrue(self.integrity_case(outside_write, before, after))

    def test_direct_report_telemetry_and_selection_integrity_controls(self) -> None:
        report = {
            "status": "completed",
            "model": "gpt-5.6-luna",
            "reasoning_effort": "medium",
            "telemetry_status": "unavailable",
            "duration_ms": 0,
            "total_tokens": 0,
            "return_code": 0,
            "timed_out": False,
            "stderr": "",
            "produced_paths": [],
            "tool_events": [],
        }
        self.assertFalse(direct_report_status_is_usable(report, 19))

    def test_public_direct_task_has_no_grader_contract_or_sibling_identity(self) -> None:
        root = self.root / "iteration-3" / "behavior"
        opaque_id = behavior_job_id(19, "without_skill", 1)
        run_dir = root / opaque_id
        report_contract = direct_agent_report_contract("context-token")
        task = public_direct_task(
            opaque_id,
            "Write the requested document.",
            run_dir,
            run_dir / "workspace",
            run_dir / "direct-response.md",
            run_dir / "direct-agent-report.json",
            "context-token",
            report_contract,
        )
        forbidden_keys = {
            "eval_id", "eval_name", "configuration", "repetition", "case_contract",
            "validation", "allowed_change_paths", "required_change_paths", "forbidden_change_paths",
            "expectations", "expected_output", "skill_usage", "skill_snapshot_before_sha256",
            "skill_snapshot_after_sha256", "skill_snapshot_contract_sha256",
        }
        self.assertTrue(forbidden_keys.isdisjoint(task))
        self.assertNotIn("skill_path", task)
        self.assertRegex(task["run_dir"], r"/behavior/job-[0-9a-f]{24}$")
        self.assertNotIn("without_skill", task["run_dir"])
        self.assertNotIn("eval-19", task["run_dir"])
        self.assertEqual(
            expected_run_dir(root.parent, {"id": 19, "eval_name": "first-name"}, "without_skill", 1),
            expected_run_dir(root.parent, {"id": 19, "eval_name": "second-name"}, "without_skill", 1),
        )
        contract_text = json.dumps(report_contract, ensure_ascii=False).lower()
        self.assertNotIn("completed", contract_text)
        self.assertNotIn("clarification_required", contract_text)

        with_skill_task = public_direct_task(
            opaque_id,
            "Write the requested document.",
            run_dir,
            run_dir / "workspace",
            run_dir / "direct-response.md",
            run_dir / "direct-agent-report.json",
            "context-token",
            report_contract,
            run_dir / "skill-snapshot",
        )
        self.assertIn("skill_path", with_skill_task)

    def test_blind_comparison_integrity_negative_controls(self) -> None:
        self.assertEqual(resolved_blind_winner("A", "A"), "TIE")
        self.assertEqual(resolved_blind_winner("A", "B"), "A")
        generic = {"winner": "A", "reasoning": "A is better", "evidence_references": [], "rubric": {}, "expectation_details": {}}
        self.assertFalse(blind_verdict_has_concrete_evidence(generic))
        concrete = {"winner": "A", "reasoning": "A preserves the required owner file while B omits it.", "evidence_references": ["A/index.md", "B/index.md"], "rubric": {"owner": True}, "expectation_details": {"owner": "preserved"}}
        self.assertTrue(blind_verdict_has_concrete_evidence(concrete))

    def test_blind_gate_and_iteration_negative_controls(self) -> None:
        self.assertTrue(blind_gate_passes(20, 15, 4, 19, 0.95))
        self.assertFalse(blind_gate_passes(20, 13, 4, 17, 0.85))
        self.assertFalse(production_iteration_is_accepted(8))
        self.assertTrue(production_iteration_is_accepted(9))

    def test_diagnostic_evidence_passes_structure_but_blocks_release(self) -> None:
        validator = ROOT / "scripts" / "validate_package.py"
        structural = subprocess.run(
            [sys.executable, str(validator), str(ROOT)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(structural.returncode, 0, structural.stdout + structural.stderr)
        self.assertIn("diagnostic evidence matches clean iteration-13", structural.stdout)

        release = subprocess.run(
            [sys.executable, str(validator), str(ROOT), "--require-production-ready"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(release.returncode, 1, release.stdout + release.stderr)
        self.assertIn("production-ready validation rejects", release.stdout)

if __name__ == "__main__":
    unittest.main(verbosity=2)
