import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from main import open_download_folder

class FolderTests(unittest.TestCase):
    def test_opens_folder_as_local_file_url(self):
        with tempfile.TemporaryDirectory() as name:
            with patch("main.QDesktopServices.openUrl", return_value=True) as mocked:
                self.assertTrue(open_download_folder(name))
                self.assertEqual(Path(mocked.call_args.args[0].toLocalFile()), Path(name).resolve())

    def test_missing_folder_does_not_launch_explorer(self):
        with tempfile.TemporaryDirectory() as name:
            with patch("main.QDesktopServices.openUrl") as mocked:
                self.assertFalse(open_download_folder(str(Path(name) / "missing")))
                mocked.assert_not_called()

if __name__ == "__main__":
    unittest.main()
