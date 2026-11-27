"""Regression checks for the LOC measurement CLI."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("loc_to_limit.py")


class LocToLimitTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("tokei"), "tokei is not installed")
    def test_forced_color_output_is_parsed(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "main.py").write_text("a = 1\nb = 2\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), directory],
                capture_output=True, text=True, check=False,
                env={**os.environ, "CLICOLOR_FORCE": "1"},
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout),
                         {"loc": 2, "scale": "Small", "character_limit": 10000})


if __name__ == "__main__":
    unittest.main()
