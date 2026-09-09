#!/usr/bin/env python3
"""Regression checks for compiler selection and verification evidence."""
import contextlib
import io
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import validate_version_support as validator


class CompilerSelectionTests(unittest.TestCase):
    def test_all_releases_and_inherited_fixtures(self):
        args = ["--require-all"]
        for version in validator.SUPPORTED_RELEASES:
            args += ["--compiler", f"{version}=/tmp/{version}/typst"]
        targets = validator.parse_args(args).targets
        self.assertEqual([t.expected_version for t in targets], list(validator.SUPPORTED_RELEASES))
        self.assertIn("typst-0.13.typ", targets[-1].fixtures)
        self.assertIn("typst-0.14.typ", targets[-1].fixtures)
        self.assertNotIn("typst-0.14.typ", targets[0].fixtures)

    def test_legacy_aliases_preserve_exact_patch(self):
        for minor, patch_version in validator.LATEST_PATCHES.items():
            with self.subTest(minor=minor):
                args = validator.parse_args([f"--typst-{minor}", "/tmp/typst"])
                self.assertEqual(args.targets[0].expected_version, patch_version)

    def test_reject_invalid_or_incomplete_requests(self):
        cases = [
            [], ["--compiler", "0.15.1"], ["--compiler", "0.15.1="],
            ["--compiler", "0.15.1-rc.1=/tmp/t"], ["--compiler", "0.16.0=/tmp/t"],
            ["--compiler", "0.15.1=/tmp/a", "--typst-0.15", "/tmp/b"],
            ["--compiler", "0.13.0=/tmp/t", "--require-all"],
        ]
        for args in cases:
            with self.subTest(args=args), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    validator.parse_args(args)
                self.assertEqual(error.exception.code, 2)

    def test_path_can_contain_equals_and_spaces(self):
        args = validator.parse_args(["--compiler", "0.15.1=/tmp/build = stable/typst"])
        self.assertEqual(args.targets[0].compiler, Path("/tmp/build = stable/typst").resolve())


class ProcessEvidenceTests(unittest.TestCase):
    def test_version_parser_rejects_entire_nonstable_token(self):
        for token in ("0.15.1-rc.1", "0.15.1-dev", "0.15.1+build", "0.15.1.9"):
            with self.subTest(token=token), patch.object(validator.subprocess, "run") as run:
                run.return_value = subprocess.CompletedProcess([], 0, f"typst {token}\n", "")
                self.assertIsNone(validator.read_compiler_version(Path("typst"))[0])
        with patch.object(validator.subprocess, "run") as run:
            run.return_value = subprocess.CompletedProcess([], 0, "typst 0.15.1 (9dfd3a08)\n", "")
            self.assertEqual(validator.read_compiler_version(Path("typst"))[0], "0.15.1")
            self.assertEqual(run.call_args.kwargs["timeout"], 10)

    def test_version_execution_failure_and_timeout_are_reported(self):
        errors = (PermissionError("not executable"), subprocess.TimeoutExpired("typst", 10))
        for error in errors:
            with self.subTest(error=error), patch.object(validator.subprocess, "run", side_effect=error):
                version, message = validator.read_compiler_version(Path("typst"))
                self.assertIsNone(version)
                self.assertTrue(message)

    def test_compilation_needs_new_nonempty_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "common.pdf"
            output.write_bytes(b"old PDF")
            with patch.object(validator.subprocess, "run") as run:
                run.return_value = subprocess.CompletedProcess([], 0, "", "")
                passed, diagnostics = validator.compile_fixture(Path("typst"), "common.typ", root)
                self.assertFalse(passed)
                self.assertIn("non-empty PDF", diagnostics)
                self.assertFalse(output.exists())
                self.assertEqual(run.call_args.kwargs["timeout"], 60)

    def test_compilation_failure_and_timeout_are_reported(self):
        with tempfile.TemporaryDirectory() as temp:
            for error in (OSError("exec format"), subprocess.TimeoutExpired("typst", 60)):
                with self.subTest(error=error), patch.object(validator.subprocess, "run", side_effect=error):
                    passed, diagnostics = validator.compile_fixture(Path("typst"), "common.typ", Path(temp))
                    self.assertFalse(passed)
                    self.assertTrue(diagnostics)

    def test_warning_preservation_and_version_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            compiler = Path(temp) / "typst"
            compiler.touch()
            report = validator.Report()
            for version in ("0.13.0", "0.15.1"):
                target = validator.CompilerTarget(version, compiler, ("common.typ",))
                with patch.object(validator, "read_compiler_version", return_value=(version, version)), \
                     patch.object(validator, "compile_fixture", return_value=(True, "warning: unknown font")) as compile_call:
                    validator.validate_target(target, Path(temp), report)
                    self.assertEqual(compile_call.call_args.args[2], Path(temp) / version)
            self.assertEqual(len(report.warnings), 2)
            self.assertIn("warning: unknown font", report.render())
            self.assertIn("Unchecked releases: 0.13.1, 0.14.0, 0.14.1, 0.14.2, 0.15.0", report.render())

    def test_mismatch_does_not_compile(self):
        with tempfile.TemporaryDirectory() as temp:
            compiler = Path(temp) / "typst"
            compiler.touch()
            target = validator.CompilerTarget("0.13.0", compiler, ("common.typ",))
            report = validator.Report()
            with patch.object(validator, "read_compiler_version", return_value=("0.13.1", "typst 0.13.1")), \
                 patch.object(validator, "compile_fixture") as compile_call:
                validator.validate_target(target, Path(temp), report)
                compile_call.assert_not_called()
            self.assertEqual(len(report.failed), 1)
            self.assertEqual(report.checked_versions, [])

    def test_missing_compiler_and_exit_codes(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(validator.main(["--compiler", f"0.15.1={temp}/missing"]), 1)
        with patch.object(validator, "validate_target"), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(validator.main(["--compiler", "0.15.1=/tmp/typst"]), 0)


if __name__ == "__main__":
    unittest.main()
