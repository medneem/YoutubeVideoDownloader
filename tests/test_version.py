import tempfile
import unittest
from pathlib import Path

from scripts.stamp_version import make_version, stamp_version


class BuildVersionTests(unittest.TestCase):
    def test_version_uses_pipeline_number(self):
        self.assertEqual(make_version("0.1", "42"), "0.1.42")
        self.assertEqual(make_version("1.3", "99"), "1.3.99")

    def test_invalid_run_number_rejected(self):
        for value in ("", "0", "-1", "foo", "65536"):
            with self.subTest(run_number=value):
                with self.assertRaises(ValueError):
                    make_version("0.1", value)

    def test_version_files_generated(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            self.assertEqual(stamp_version("0.1", "42", folder), "0.1.42")
            self.assertIn('APP_VERSION = "0.1.42"', (
                folder / "version.py").read_text(encoding="utf-8"))
            self.assertIn("0, 1, 42, 0", (
                folder / "windows_version_info.txt").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
