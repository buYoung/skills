"""Regression checks for the update parser's public CLI contract."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("parse_sections.py")
MARKER = "<!-- agents-md-generator: v1; doc-type: single_repo -->"


class ParseSectionsTests(unittest.TestCase):
    def parse(self, text, doc_type="single_repo"):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "AGENTS.md"
            path.write_bytes(text.encode("utf-8"))
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(path), "--doc-type", doc_type],
                capture_output=True, text=True, check=True,
            )
        return json.loads(result.stdout)

    def test_matching_heading_does_not_establish_management(self):
        result = self.parse("# AGENTS.md\n\n## 1. Overview\nHandwritten policy.\n")
        self.assertEqual(result["management_status"], "unmarked")
        self.assertIsNone(result["generated_doc_type"])
        self.assertTrue(result["sections"][0]["is_standard"])
        self.assertEqual(result["missing_required_standard"], [
            "## 3. Core Behaviors & Patterns", "## 4. Conventions",
            "## 5. Working Agreements",
        ])

    def test_valid_marker_and_existing_json_contract(self):
        result = self.parse(f"# AGENTS.md\n{MARKER}\n\n## 1. Overview\nBody\n")
        self.assertEqual(result["management_status"], "managed")
        self.assertEqual(result["generated_doc_type"], "single_repo")
        self.assertEqual(result["doc_type"], "single_repo")
        self.assertEqual(result["preamble_end_line"], 3)
        self.assertEqual(result["sections"][0]["start_line"], 3)
        self.assertEqual(result["sections"][0]["end_line"], 4)
        self.assertEqual(result["optional_standard"], ["## 2. Ownership Map"])
        self.assertEqual(result["missing_standard"],
                         result["missing_required_standard"] + result["missing_optional_standard"])

    def test_document_type_mismatch_is_visible_without_changing_requested_map(self):
        result = self.parse(f"{MARKER}\n## 5. Working Agreements\nPolicy\n", "monorepo_root")
        self.assertEqual(result["management_status"], "managed")
        self.assertEqual(result["generated_doc_type"], "single_repo")
        self.assertEqual(result["doc_type"], "monorepo_root")
        self.assertFalse(result["sections"][0]["is_standard"])
        original = self.parse(f"{MARKER}\n## 5. Working Agreements\nPolicy\n")
        self.assertTrue(original["sections"][0]["is_standard"])

    def test_monorepo_root_marker(self):
        marker = MARKER.replace("single_repo", "monorepo_root")
        result = self.parse(f"{marker}\n## 3. Working Agreements\nPolicy\n", "monorepo_root")
        self.assertEqual(result["generated_doc_type"], "monorepo_root")
        self.assertEqual(result["management_status"], "managed")
        self.assertTrue(result["sections"][0]["is_standard"])

    def test_invalid_duplicate_and_misplaced_markers(self):
        cases = [
            MARKER.replace("v1", "v2"),
            MARKER.replace("single_repo", "package"),
            MARKER.removesuffix(" -->"),
            MARKER + "\n" + MARKER,
            "## Custom Instructions\n" + MARKER,
            MARKER + "\n## Custom Instructions\n" + MARKER,
        ]
        for text in cases:
            with self.subTest(text=text):
                result = self.parse(text + "\n")
                self.assertEqual(result["management_status"], "invalid")
                self.assertIsNone(result["generated_doc_type"])

    def test_fenced_markers_and_headings_are_ignored(self):
        for fence in ("```", "~~~~"):
            with self.subTest(fence=fence):
                result = self.parse(f"{fence}\n{MARKER}\n## 1. Overview\n{fence}\n## Custom\nKeep\n")
                self.assertEqual(result["management_status"], "unmarked")
                self.assertEqual([s["title"] for s in result["sections"]], ["## Custom"])
        result = self.parse(f"{MARKER}\n```\n{MARKER}\n```\n## 1. Overview\n")
        self.assertEqual(result["management_status"], "managed")

    def test_preservation_ranges_recover_original_crlf_bytes(self):
        preamble = ("# AGENTS.md\r\n" + MARKER + "\r\n\r\n").encode("utf-8")
        custom = "## Custom Instructions\r\n사용자 규칙  \r\n```md\r\n## 4. Conventions\r\n```\r\n\r\n".encode("utf-8")
        original = preamble + b"## 1. Overview\r\nManaged\r\n" + custom + b"## 1. Overview\r\nDuplicate\r\n"
        result = self.parse(original.decode("utf-8"))
        lines = original.splitlines(keepends=True)
        self.assertEqual(b"".join(lines[:result["preamble_end_line"]]), preamble)
        section = result["sections"][1]
        self.assertFalse(section["is_standard"])
        self.assertEqual(b"".join(lines[section["start_line"]:section["end_line"] + 1]), custom)
        self.assertTrue(result["sections"][2]["is_duplicate_standard"])

    def test_legacy_alias_and_custom_final_newline_preservation(self):
        for newline in ("\n", "\r\n"):
            for has_final_newline in (False, True):
                with self.subTest(newline=newline, has_final_newline=has_final_newline):
                    custom = "## Custom Instructions" + newline + "Keep this  "
                    if has_final_newline:
                        custom += newline
                    original = newline.join([
                        MARKER, "## 2. Folder Structure", "Old managed section",
                        "## 2. Ownership Map", "Duplicate managed section", custom,
                    ]).encode("utf-8")
                    result = self.parse(original.decode("utf-8"))
                    legacy, duplicate, preserved = result["sections"]
                    self.assertTrue(legacy["is_legacy_standard"])
                    self.assertEqual(legacy["canonical_title"], "## 2. Ownership Map")
                    self.assertTrue(duplicate["is_duplicate_standard"])
                    self.assertEqual(result["missing_optional_standard"], [])
                    lines = original.splitlines(keepends=True)
                    self.assertEqual(
                        b"".join(lines[preserved["start_line"]:preserved["end_line"] + 1]),
                        custom.encode("utf-8"),
                    )


if __name__ == "__main__":
    unittest.main()
