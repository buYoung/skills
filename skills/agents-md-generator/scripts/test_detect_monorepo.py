"""Regression checks for Gradle markers through the detector's public CLI."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("detect_monorepo.py")


class GradleDetectionTests(unittest.TestCase):
    def detect(self, settings, filename="settings.gradle.kts"):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / filename).write_text(settings, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), directory],
                capture_output=True, text=True, check=True,
            )
        return json.loads(result.stdout)

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


if __name__ == "__main__":
    unittest.main()
