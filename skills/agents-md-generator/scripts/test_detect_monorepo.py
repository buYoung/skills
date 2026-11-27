"""Regression checks for monorepo markers through the detector's public CLI."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("detect_monorepo.py")
NOT_MONOREPO = {"is_monorepo": False, "markers": []}


def detect_files(files):
    """Write {relative_path: text} into a temporary root and run the CLI."""
    with tempfile.TemporaryDirectory() as directory:
        for relative_path, text in files.items():
            path = Path(directory) / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), directory],
            capture_output=True, text=True, check=True,
        )
    return json.loads(result.stdout)


class GradleDetectionTests(unittest.TestCase):
    def detect(self, settings, filename="settings.gradle.kts"):
        return detect_files({filename: settings})

    def test_multiple_project_declarations(self):
        cases = [
            'include(\n    ":app",\n    ":core",\n)\n',
            'include(":app", ":core")\n',
            'include(":app")\ninclude(":core")\n',
            'include(\n ":app", /* comment, include(":fake") */\n ":core" // comment\n)\n',
            "include ':app', ':core'\n",
            "include ':app',\n ':core'\n",
        ]
        for filename in ("settings.gradle.kts", "settings.gradle"):
            for settings in cases:
                with self.subTest(filename=filename, settings=settings):
                    result = self.detect(settings, filename)
                    self.assertTrue(result["is_monorepo"])
                    self.assertEqual(result["markers"], [{
                        "marker": filename, "type": "gradle-multiproject",
                    }])

    def test_single_project_duplicates_and_fake_declarations(self):
        cases = [
            'include(\n ":app",\n)\n',
            'include(":app",)\n',
            "include ':app'\n",
            'include(":app", ":app")\n',
            'include(":app")\ninclude(":app")\n',
            'include("app", ":app")\n',
            '// include(":app", ":core")\n',
            '/* include(":app", ":core") */\n',
            'val example = """\ninclude(":app", ":core")\n"""\n',
            "def example = '''\ninclude ':app', ':core'\n'''\n",
            'val example = "include(\\\":app\\\", \\\":core\\\")"\n',
        ]
        for settings in cases:
            with self.subTest(settings=settings):
                self.assertEqual(self.detect(settings), {"is_monorepo": False, "markers": []})

    def test_composite_build_is_provisional_marker(self):
        for settings in ('includeBuild("../shared")\n', "includeBuild '../shared'\n"):
            with self.subTest(settings=settings):
                self.assertTrue(self.detect(settings)["is_monorepo"])


class PythonWorkspaceDetectionTests(unittest.TestCase):
    def assert_python_workspace(self, filename, text):
        self.assertEqual(detect_files({filename: text}), {
            "is_monorepo": True,
            "markers": [{"marker": filename, "type": "python-workspaces"}],
        })

    def test_hatch_environment_without_workspace_is_not_a_marker(self):
        cases = [
            '[tool.hatch.envs.default]\ndependencies = ["pytest"]\n',
            '[tool.hatch.envs.lint.scripts]\ncheck = "ruff check ."\n',
            '[[tool.hatch.envs.test.matrix]]\npython = ["3.11", "3.12"]\n',
            '[tool.hatch.envs.default]\n# workspace.members = ["packages/*"]\n',
            '[tool.hatch.envs.default.scripts]\nworkspace.members = "echo"\n',
            '[project]\ndescription = """\n[tool.hatch.envs.default]\n'
            'workspace.members = ["packages/*"]\n"""\n',
        ]
        for text in cases:
            with self.subTest(text=text):
                self.assertEqual(detect_files({"pyproject.toml": text}), NOT_MONOREPO)
        self.assertEqual(
            detect_files({"hatch.toml": '[envs.default]\ndependencies = ["pytest"]\n'}),
            NOT_MONOREPO,
        )

    def test_hatch_workspace_members(self):
        cases = [
            '[tool.hatch.envs.default]\nworkspace.members = ["packages/*"]\n',
            '[tool.hatch.envs.unit-tests]\nworkspace.members = [\n  "packages/core",\n]\n',
            '[tool.hatch.envs.default.workspace]\nmembers = ["packages/*"]\n',
            '[tool.hatch.envs.default]\nworkspace = { members = ["packages/*"] }\n',
        ]
        for text in cases:
            with self.subTest(text=text):
                self.assert_python_workspace("pyproject.toml", text)
        self.assert_python_workspace(
            "hatch.toml", '[envs.default]\nworkspace.members = ["packages/*"]\n')

    def test_uv_and_rye_workspace_tables(self):
        for text in ('[tool.uv.workspace]\nmembers = ["packages/*"]\n',
                     '[tool.rye.workspace]\n'):
            with self.subTest(text=text):
                self.assert_python_workspace("pyproject.toml", text)
        self.assertEqual(
            detect_files({"pyproject.toml": '[tool.uv.sources]\ncore = { workspace = true }\n'}),
            NOT_MONOREPO,
        )


class MavenDetectionTests(unittest.TestCase):
    def test_modules_and_subprojects(self):
        for pom in ('<project><modules><module>core</module></modules></project>',
                    '<project><subprojects><subproject>core</subproject></subprojects></project>'):
            with self.subTest(pom=pom):
                self.assertEqual(detect_files({"pom.xml": pom})["markers"], [
                    {"marker": "pom.xml", "type": "maven-multimodule"},
                ])

    def test_commented_modules_are_ignored(self):
        pom = '<project>\n<!-- <modules><module>core</module></modules> -->\n</project>'
        self.assertEqual(detect_files({"pom.xml": pom}), NOT_MONOREPO)


class BuildSystemMarkerTests(unittest.TestCase):
    def test_marker_files(self):
        cases = [
            (".moon/workspace.yml", "moonrepo"),
            (".moon/workspace.toml", "moonrepo"),
            (".moon/workspace.pkl", "moonrepo"),
            ("REPO.bazel", "bazel"),
            ("MODULE.bazel", "bazel"),
        ]
        for marker, marker_type in cases:
            with self.subTest(marker=marker):
                self.assertEqual(detect_files({marker: ""})["markers"], [
                    {"marker": marker, "type": marker_type},
                ])


if __name__ == "__main__":
    unittest.main()
