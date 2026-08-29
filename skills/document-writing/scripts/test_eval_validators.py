#!/usr/bin/env python3
"""Deterministic regression tests for the schema-v3 evaluation harness."""

from __future__ import annotations

import json
import os
import shutil
import struct
import subprocess
import tempfile
import unittest
import zlib
from pathlib import Path

from run_production_evals import (
    ProductionEvalError,
    aggregate_stage,
    behavior_job_id,
    build_harness_execution_receipt,
    canonicalize_worker_response,
    count_user_questions,
    direct_grading_prepare_stage,
    execution_policy_for_case,
    expected_run_dir,
    grader_dispatch_message,
    public_direct_task,
    select_primary_fdd,
    tree_manifest,
    validate_harness_execution_receipt,
    validate_independent_grading,
    worker_dispatch_message,
)
from validate_design_system_output import validate as validate_design_output
from validate_eval_run import iso_dates
from validate_package import (
    Report as PackageReport,
    inspect_png,
    validate_markdown_links,
    validate_production_suite,
    validate_python_eval_scripts,
)


ROOT = Path(__file__).resolve().parents[1]
VALIDATORS = ROOT / "evals" / "validators"
RUN_VALIDATOR = ROOT / "scripts" / "validate_eval_run.py"
SUITE_PATH = ROOT / "evals" / "production-suite.json"


def write(root: Path, relative: str, content: str) -> None:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def run_node(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["node", str(VALIDATORS / script), *args], text=True, capture_output=True, check=False)


def png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)


def valid_png(width: int = 1, height: int = 1, has_alpha: bool = False) -> bytes:
    color_type = 6 if has_alpha else 2
    channels = 4 if has_alpha else 3
    ihdr = struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0)
    raw = b"".join(b"\x00" + (b"\x00" * width * channels) for _ in range(height))
    return b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", ihdr) + png_chunk(b"IDAT", zlib.compress(raw)) + png_chunk(b"IEND", b"")


class ValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="document-writing-schema-v3-tests-")
        self.root = Path(self.temp.name)
        self.suite = json.loads(SUITE_PATH.read_text(encoding="utf-8"))

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_existing_update_positive_and_negative_controls(self) -> None:
        fixture = self.root / "existing-fixture"
        write(fixture, "index.md", "# Existing system\n\n- [Tokens](tokens.md)\n")
        write(fixture, "tokens.md", "# Tokens\n\nDo not change `blue-500`.\n")
        write(fixture, "notes.md", "# Team notes\n\nKeep this exact custom note.\n")
        result = self.root / "existing-result"
        shutil.copytree(fixture, result)
        write(result, "index.md", (result / "index.md").read_text() + "- [Content](content.md)\n- [Accessibility](accessibility.md)\n")
        write(result, "content.md", "# Content guidance\n\nUse concise labels and explain outcomes before actions. Keep durable names understandable outside their visual context. Avoid ambiguous instructions, describe the result of each action, and ensure recovery text tells the reader what changed and what they can do next.\n")
        write(result, "accessibility.md", "# Accessibility guidance\n\nProvide keyboard access, visible focus, programmatic names, reduced motion, and non-color error cues. Ensure every control exposes a stable accessible name, every error explains recovery, and every meaningful state remains understandable without relying on color, sound, or motion alone.\n")
        self.assertEqual(run_node("validate_existing_update.mjs", str(fixture), str(result)).returncode, 0)
        no_op = self.root / "existing-no-op"
        shutil.copytree(fixture, no_op)
        self.assertEqual(run_node("validate_existing_update.mjs", str(fixture), str(no_op)).returncode, 1)

    def test_preservation_and_noncanonical_guards(self) -> None:
        fixture = ROOT / "evals" / "fixtures" / "storefront-existing-noncanonical"
        result = self.root / "preserve-result"
        shutil.copytree(fixture, result)
        self.assertEqual(run_node("validate_preservation.mjs", str(fixture), str(result), "--exact-tree").returncode, 0)
        write(result, "stores/play-store-assets.md", "# Google Play listing artwork\n\n## Store research\n\nVerified from current first-party guidance on 2026-08-29.\n\nhttps://support.google.com/googleplay/android-developer/answer/9866151\n\n## Storefront-specific relationships and ordering\n\nScreenshots must show the actual in-app experience. Keep claims in the artwork consistent with the listing review package and the current product.\n")
        self.assertEqual(run_node("validate_noncanonical_store.mjs", str(fixture), str(result)).returncode, 0)
        write(result, "stores/google-play.md", "# Duplicate\n")
        self.assertEqual(run_node("validate_noncanonical_store.mjs", str(fixture), str(result)).returncode, 1)
        destructive = self.root / "destructive-result"
        shutil.copytree(fixture, destructive)
        write(destructive, "stores/play-store-assets.md", "# Google Play listing artwork\n\nVerified: 2026-08-29\n\nhttps://support.google.com/googleplay/android-developer/answer/9866151\n\n## New requirements\n\nOnly current dimensions remain.\n")
        self.assertEqual(run_node("validate_noncanonical_store.mjs", str(fixture), str(destructive)).returncode, 1)

    def test_warning_update_propagation_and_scope_guards(self) -> None:
        fixture = ROOT / "evals" / "fixtures" / "design-system-warning-update"
        result = self.root / "warning-result"
        shutil.copytree(fixture, result)
        for relative in ("tokens.md", "components/alert.md"):
            target = result / relative
            target.write_text(target.read_text(encoding="utf-8").replace("#E5A000", "#D97706"), encoding="utf-8")
        self.assertEqual(run_node("validate_warning_update.mjs", str(fixture), str(result)).returncode, 0)
        write(result, "components/button.md", "# unrelated change\n")
        self.assertEqual(run_node("validate_warning_update.mjs", str(fixture), str(result)).returncode, 1)

    def task(self, workspace: Path, response: Path, allowed: list[str], write_policy: str = "allowlisted") -> dict[str, object]:
        return {
            "schema_version": 3,
            "job_id": "job-test",
            "prompt": "test",
            "run_dir": str(response.parent),
            "workspace": str(workspace),
            "response_path": str(response),
            "skill_path": str(response.parent / "skill-snapshot"),
            "model": "gpt-5.6-luna",
            "reasoning_effort": "medium",
            "task_context_id": "task-context",
            "execution_policy": {"workspace_write_policy": write_policy, "allowed_workspace_paths": allowed},
        }

    def test_harness_receipt_derives_no_change_and_exact_two_file_change(self) -> None:
        run = self.root / "receipt"
        workspace = run / "workspace"
        workspace.mkdir(parents=True)
        response = run / "direct-response.md"
        response.write_text("완료", encoding="utf-8")
        before = tree_manifest(workspace)
        disabled_task = self.task(workspace, response, [], "disabled")
        receipt = build_harness_execution_receipt(disabled_task, response, before, tree_manifest(workspace))
        self.assertEqual(receipt["produced_paths"], [])
        self.assertEqual(receipt["telemetry"], {"status": "unavailable", "duration_ms": None, "total_tokens": None})
        self.assertEqual(receipt["capability_evidence"], {"status": "unverified", "events": []})
        write(workspace, "docs/design-system/tokens.md", "#D97706\n")
        write(workspace, "docs/design-system/components/alert.md", "#D97706\n")
        after = tree_manifest(workspace)
        allowed = ["docs/design-system/components/alert.md", "docs/design-system/tokens.md"]
        task = self.task(workspace, response, allowed)
        receipt = build_harness_execution_receipt(task, response, before, after)
        self.assertEqual(receipt["produced_paths"], allowed)
        self.assertEqual(validate_harness_execution_receipt(receipt, task, before, after), [])

    def test_write_disabled_outside_allowlist_and_missing_response_fail(self) -> None:
        run = self.root / "receipt-errors"
        workspace = run / "workspace"
        workspace.mkdir(parents=True)
        response = run / "direct-response.md"
        response.write_text("완료", encoding="utf-8")
        before = tree_manifest(workspace)
        write(workspace, "docs/unexpected.md", "unexpected\n")
        after = tree_manifest(workspace)
        disabled = self.task(workspace, response, [], "disabled")
        failures = validate_harness_execution_receipt(build_harness_execution_receipt(disabled, response, before, after), disabled, before, after)
        self.assertTrue(any("disabled" in item for item in failures))
        allowlisted = self.task(workspace, response, ["docs/allowed.md"])
        failures = validate_harness_execution_receipt(build_harness_execution_receipt(allowlisted, response, before, after), allowlisted, before, after)
        self.assertTrue(any("outside allowed paths" in item for item in failures))
        missing = run / "missing.md"
        with self.assertRaises(ProductionEvalError):
            build_harness_execution_receipt(self.task(workspace, missing, []), missing, before, before)

    def test_question_counter_requires_visible_questions_and_ignores_code_urls(self) -> None:
        self.assertEqual(count_user_questions("A, B, C 중 하나를 승인해 주세요."), 0)
        self.assertEqual(count_user_questions("A, B, C 중 어느 방향을 승인하시겠습니까?"), 1)
        response = "진행할까요? 차갑게 느껴지나요？\nhttps://example.com/?q=x\n`ignored?`\n```\nignored?\n```"
        self.assertEqual(count_user_questions(response), 2)

    def test_iso_date_accepts_korean_particle_and_rejects_invalid_calendar_date(self) -> None:
        self.assertEqual(iso_dates("공식 문서를 2026-08-29에 확인했다."), ["2026-08-29"])
        self.assertEqual(iso_dates("검증일: 2026-08-29."), ["2026-08-29"])
        self.assertEqual(iso_dates("2026-13-99에 확인했다."), [])
        self.assertEqual(iso_dates("12026-08-290"), [])

    def test_worker_dispatch_embeds_task_and_exposes_no_private_contract(self) -> None:
        run = self.root / "dispatch"
        task = public_direct_task("job-public", "문서를 작성해줘.", run, run / "workspace", run / "direct-response.md", "task-public", run / "skill-snapshot", {"workspace_write_policy": "disabled", "allowed_workspace_paths": []})
        message = worker_dispatch_message(task)
        self.assertIn(json.dumps(task, ensure_ascii=False, indent=2), message)
        self.assertNotIn("report_path", message)
        self.assertNotIn("report_contract", message)
        self.assertNotIn("expectations", message)
        self.assertNotIn("direct-agent-report", message)
        self.assertNotIn("read direct-task", message.lower())

    def test_worker_response_is_canonicalized_from_one_nested_transport_path(self) -> None:
        run = self.root / "nested-response"
        nested = run / "job-duplicate" / "direct-response.md"
        nested.parent.mkdir(parents=True)
        nested.write_text("완료된 사용자 응답", encoding="utf-8")
        expected = run / "direct-response.md"
        selected = canonicalize_worker_response(run, expected)
        self.assertEqual(selected, expected)
        self.assertEqual(expected.read_text(encoding="utf-8"), "완료된 사용자 응답")
        self.assertTrue((run / "response-canonicalization.json").is_file())

    def test_grader_reads_isolated_copies_and_writes_candidate_path(self) -> None:
        iteration = self.root / "iteration-grader-isolation"
        write_json(iteration / "iteration.json", {"schema_version": 3, "evaluation_scope": {"kind": "targeted", "eval_ids": [1]}})
        run = expected_run_dir(iteration, 1)
        workspace = run / "workspace"
        workspace.mkdir(parents=True)
        response = run / "direct-response.md"
        response.write_text("원본 응답", encoding="utf-8")
        manifest = tree_manifest(workspace)
        task = self.task(workspace, response, [], "disabled")
        receipt = build_harness_execution_receipt(task, response, manifest, manifest)
        write_json(run / "execution-validation.json", {"valid": True})
        write_json(run / "execution-receipt.json", receipt)
        write_json(run / "deterministic-grading.json", {"status": "completed", "summary": {"failed": 0}})
        prepared = direct_grading_prepare_stage(iteration, self.suite, 1, dry_run=False)
        grader_task = prepared["tasks"][0]["task"]
        self.assertIn("grader/attempt-1/input/response.md", grader_task["response_path"])
        self.assertIn("grader/attempt-1/grading-candidate.json", grader_task["output_path"])
        self.assertEqual(response.read_text(encoding="utf-8"), "원본 응답")

    def test_independent_grading_recalculates_and_forbids_self_report(self) -> None:
        task = {"schema_version": 3, "eval_id": 1, "grader_task_context_id": "grader-task", "model": "gpt-5.6-luna", "reasoning_effort": "medium", "expectations": ["one", "two"]}
        grading = {"schema_version": 3, "status": "completed-independent-grading", "provenance": "independent-luna-grader-output", "eval_id": 1, "grader_task_context_id": "grader-task", "model": "gpt-5.6-luna", "reasoning_effort": "medium", "expectations": [{"text": "one", "passed": True, "evidence": "opening"}, {"text": "two", "passed": False, "evidence": "missing"}], "summary": {"passed": 1, "failed": 1, "total": 2, "pass_rate": 0.5}}
        self.assertEqual(validate_independent_grading(grading, task), [])
        grading["summary"]["pass_rate"] = 1.0
        self.assertTrue(validate_independent_grading(grading, task))
        grading["summary"]["pass_rate"] = 0.5
        grading["telemetry"] = {"total_tokens": 1}
        self.assertTrue(any("telemetry" in item for item in validate_independent_grading(grading, task)))

    def test_grader_dispatch_requires_file_write_parse_and_readback(self) -> None:
        task = {
            "schema_version": 3,
            "eval_id": 15,
            "grader_task_context_id": "grader-task",
            "model": "gpt-5.6-luna",
            "reasoning_effort": "medium",
            "output_path": "/tmp/grading.json",
            "expectations": ["one"],
            "required_completion_actions": [
                "Create output_path with apply_patch; a chat-only answer is failure.",
                "Validate output_path with python3 -m json.tool.",
                "Read output_path back and verify the complete output_contract before finishing.",
            ],
            "output_contract": {},
        }
        message = grader_dispatch_message(task)
        self.assertIn("chat-only answer is a failed run", message)
        self.assertIn("use apply_patch to create output_path", message)
        self.assertIn("python3 -m json.tool output_path", message)
        self.assertIn("read output_path back", message)

    def test_filename_independent_png_and_design_owner_validation(self) -> None:
        root = self.root / "design-output"
        write(root, "index.md", "# Index\n")
        write(root, "stores/google-play.md", "# Google Play\n")
        (root / "custom-feature-name.png").write_bytes(valid_png(1024, 500))
        result = validate_design_output(root, "app-store-page", ["google-play"], [], 1, 1024, 500, False)
        self.assertEqual(result["failures"], [])
        self.assertEqual(inspect_png(root / "custom-feature-name.png"), (1024, 500, False))
        (root / "second.png").write_bytes(valid_png(1024, 500))
        self.assertTrue(validate_design_output(root, "app-store-page", ["google-play"], [], 1, 1024, 500, False)["failures"])
        (root / "second.png").unlink()
        (root / "custom-feature-name.png").write_bytes(valid_png(1024, 500, has_alpha=True))
        self.assertTrue(validate_design_output(root, "app-store-page", ["google-play"], [], 1, 1024, 500, False)["failures"])
        (root / "custom-feature-name.png").write_bytes(valid_png(800, 500))
        self.assertTrue(validate_design_output(root, "app-store-page", ["google-play"], [], 1, 1024, 500, False)["failures"])

    def test_canonical_web_platform_rejects_product_subtype_filename(self) -> None:
        root = self.root / "platform-output"
        write(root, "index.md", "# Index\n")
        write(root, "platforms/web-admin.md", "# Web admin\n")
        failed = validate_design_output(root, "default", [], ["web"], None, None, None, None)
        self.assertTrue(failed["failures"])
        write(root, "platforms/web.md", "# Web\n")
        passed = validate_design_output(root, "default", [], ["web"], None, None, None, None)
        self.assertEqual(passed["failures"], [])

    def test_design_system_contract_records_all_failed_behavior_fixes(self) -> None:
        workflow = (ROOT / "references/document-types/design-system/design-direction-workflow.md").read_text(encoding="utf-8")
        authoring = (ROOT / "references/document-types/design-system/design-system-authoring.md").read_text(encoding="utf-8")
        adaptation = (ROOT / "references/document-types/design-system/platform-adaptation.md").read_text(encoding="utf-8")
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("option label", workflow)
        self.assertIn("recognizable outcome", workflow)
        self.assertIn("partial-authoring rule", workflow)
        self.assertIn("official URL, size, count, device condition, safe area, placement, or sequence", authoring)
        self.assertIn("approval, change, decision, or governance", authoring)
        self.assertIn("web-admin.md", adaptation)
        self.assertIn("approval/change/decision owners", skill)

    def test_execution_policy_separates_full_read_scope_from_write_allowlist(self) -> None:
        eval_27 = execution_policy_for_case(self.suite["behavior"]["case_contracts"]["27"])
        self.assertEqual(eval_27["workspace_read_policy"], "entire_workspace")
        self.assertEqual(eval_27["response_contract"], {"min_questions": 1, "max_questions": 1})
        self.assertEqual(eval_27["allowed_workspace_write_paths"], ["docs/design-system/**"])
        eval_31 = execution_policy_for_case(self.suite["behavior"]["case_contracts"]["31"])
        self.assertEqual(eval_31["workspace_read_policy"], "entire_workspace")
        self.assertEqual(eval_31["allowed_workspace_write_paths"], ["docs/design-system/tokens.md", "docs/design-system/components/alert.md"])
        self.assertTrue(any("never limits reads" in rule for rule in eval_31["rules"]))

    def synthetic_run(self, eval_id: int, response: str, files: dict[str, str]) -> subprocess.CompletedProcess[str]:
        run = self.root / f"synthetic-eval-{eval_id}"
        workspace = run / "workspace"
        workspace.mkdir(parents=True)
        response_path = run / "direct-response.md"
        response_path.write_text(response, encoding="utf-8")
        before = tree_manifest(workspace)
        for relative, content in files.items():
            write(workspace, relative, content)
        after = tree_manifest(workspace)
        contract = self.suite["behavior"]["case_contracts"][str(eval_id)]
        allowed = contract.get("allowed_change_paths", [])
        task = self.task(workspace, response_path, allowed, "disabled" if contract.get("deny_write_tools") or not allowed else "allowlisted")
        receipt = build_harness_execution_receipt(task, response_path, before, after)
        for name, payload in (("direct-task.json", task), ("before-manifest.json", before), ("after-manifest.json", after), ("execution-receipt.json", receipt), ("eval_metadata.json", {"eval_id": eval_id})):
            write_json(run / name, payload)
        return subprocess.run(["python3", str(RUN_VALIDATOR), "--suite", str(SUITE_PATH), "--run", str(run)], text=True, capture_output=True, check=False)

    def test_path_question_only_and_confirmed_platform_partial_write(self) -> None:
        path_result = self.synthetic_run(26, "이 문서는 여러 파일로 구성됩니다. `docs/design-system/`을 문서 세트 루트로 사용해도 될까요?", {})
        self.assertEqual(path_result.returncode, 0, path_result.stdout + path_result.stderr)
        platform_result = self.synthetic_run(
            27,
            "공통 계약과 웹 적응은 작성했습니다. 여기서 모바일은 iOS·Android 전체를 뜻하나요, 아니면 팀 내부 플랫폼 이름인가요?",
            {
                "docs/design-system/index.md": "# System\n\nWeb is confirmed. Mobile is unresolved.\n",
                "docs/design-system/platforms/web.md": "# Web\n\nKeyboard and pointer adaptation.\n",
            },
        )
        self.assertEqual(platform_result.returncode, 0, platform_result.stdout + platform_result.stderr)

    def test_primary_fdd_selection_excludes_index_and_prefers_frontmatter(self) -> None:
        workspace = self.root / "fdd-selection"
        write(workspace, "docs/FDD/index.md", "# FDD index\n")
        write(workspace, "docs/FDD/saved-search-filters.md", "---\ndoc-type: feature-design-doc\n---\n# Saved Search Filters\n")
        candidate, error = select_primary_fdd(workspace)
        self.assertIsNone(error)
        self.assertEqual(candidate.name if candidate else None, "saved-search-filters.md")
        write(workspace, "docs/FDD/second.md", "---\ndoc-type: feature-design-doc\n---\n# Second\n")
        candidate, error = select_primary_fdd(workspace)
        self.assertIsNone(candidate)
        self.assertIn("multiple frontmatter-marked", error or "")

    def test_aggregate_separates_execution_from_missing_grading(self) -> None:
        iteration = self.root / "iteration-1"
        write_json(iteration / "iteration.json", {"schema_version": 3, "evaluation_scope": {"kind": "targeted", "eval_ids": [1]}})
        run = expected_run_dir(iteration, 1)
        workspace = run / "workspace"
        workspace.mkdir(parents=True)
        response = run / "direct-response.md"
        response.write_text("설명 문서", encoding="utf-8")
        manifest = tree_manifest(workspace)
        task = self.task(workspace, response, [], "disabled")
        receipt = build_harness_execution_receipt(task, response, manifest, manifest)
        for name, payload in (("direct-task.json", task), ("workspace-before.json", manifest), ("workspace-after.json", manifest), ("execution-receipt.json", receipt), ("execution-validation.json", {"valid": True}), ("deterministic-grading.json", {"status": "completed", "summary": {"failed": 0}})):
            write_json(run / name, payload)
        result = aggregate_stage(iteration, self.suite, dry_run=True)
        summary = result["summary"]
        self.assertEqual(summary["valid_execution_receipts"], 1)
        self.assertEqual(summary["deterministic_passed"], 1)
        self.assertEqual(summary["completed_independent_gradings"], 0)
        self.assertIsNone(summary["macro_pass_rate"])

    def test_aggregate_distinguishes_missing_response_from_unprepared(self) -> None:
        iteration = self.root / "iteration-2"
        write_json(iteration / "iteration.json", {"schema_version": 3, "evaluation_scope": {"kind": "targeted", "eval_ids": [1, 2]}})
        run = expected_run_dir(iteration, 1)
        workspace = run / "workspace"
        workspace.mkdir(parents=True)
        manifest = tree_manifest(workspace)
        task = self.task(workspace, run / "direct-response.md", [], "disabled")
        missing_receipt = {"schema_version": 3, "provenance": "harness-derived-from-task-response-and-manifests", "status": "missing-response", "task_context_id": "task-context", "model": "gpt-5.6-luna", "reasoning_effort": "medium", "response_sha256": None, "workspace_before_sha256": manifest["sha256"], "workspace_after_sha256": manifest["sha256"], "produced_paths": [], "telemetry": {"status": "unavailable", "duration_ms": None, "total_tokens": None}, "capability_evidence": {"status": "unverified", "events": []}}
        for name, payload in (("direct-task.json", task), ("workspace-before.json", manifest), ("workspace-after.json", manifest), ("execution-receipt.json", missing_receipt)):
            write_json(run / name, payload)
        result = aggregate_stage(iteration, self.suite, dry_run=True)
        benchmark = json.loads((iteration / "benchmark.json").read_text()) if (iteration / "benchmark.json").exists() else None
        self.assertEqual(result["summary"]["planned_execution_tasks"], 2)
        self.assertEqual(result["summary"]["responses_present"], 0)
        self.assertEqual(result["summary"]["valid_execution_receipts"], 0)
        self.assertIsNone(benchmark)

    def test_aggregate_marks_unstarted_hard_gate_not_run_and_missing_grade_error(self) -> None:
        unstarted = self.root / "iteration-unstarted"
        write_json(unstarted / "iteration.json", {"schema_version": 3, "evaluation_scope": {"kind": "targeted", "eval_ids": [10]}})
        unstarted_result = aggregate_stage(unstarted, self.suite, dry_run=True)
        self.assertEqual(unstarted_result["summary"]["hard_gates"]["direction-approval-no-premature-write"], "not-run")

        grading_error = self.root / "iteration-grading-error"
        write_json(grading_error / "iteration.json", {"schema_version": 3, "evaluation_scope": {"kind": "targeted", "eval_ids": [15]}})
        run = expected_run_dir(grading_error, 15)
        workspace = run / "workspace"
        workspace.mkdir(parents=True)
        response = run / "direct-response.md"
        response.write_text("완료", encoding="utf-8")
        manifest = tree_manifest(workspace)
        task = self.task(workspace, response, [], "disabled")
        receipt = build_harness_execution_receipt(task, response, manifest, manifest)
        for name, payload in (
            ("direct-task.json", task),
            ("workspace-before.json", manifest),
            ("workspace-after.json", manifest),
            ("execution-receipt.json", receipt),
            ("deterministic-grading.json", {"status": "completed", "summary": {"failed": 0}}),
            ("grading-validation.json", {"status": "grading-error", "format_valid": False, "semantic_passed": False}),
        ):
            write_json(run / name, payload)
        error_result = aggregate_stage(grading_error, self.suite, dry_run=True)
        self.assertEqual(error_result["summary"]["completed_independent_gradings"], 0)

    def test_runner_contains_no_legacy_execution_paths(self) -> None:
        runner = (ROOT / "scripts" / "run_production_evals.py").read_text(encoding="utf-8")
        for forbidden in ("direct_agent_report_contract", "comparison_prepare_stage", "direct_selection_prepare_stage", "_legacy_evidence_stage_schema2", "without_skill_manifest"):
            self.assertNotIn(forbidden, runner)

    def test_production_suite_and_package_sources_are_structurally_valid(self) -> None:
        self.assertEqual(self.suite["schema_version"], 3)
        self.assertEqual(self.suite["behavior"]["eval_ids"], list(range(1, 33)))
        report = PackageReport()
        validate_production_suite(ROOT, report)
        validate_python_eval_scripts(ROOT, report)
        validate_markdown_links(ROOT, report)
        self.assertEqual(report.failures, [])


if __name__ == "__main__":
    unittest.main()
