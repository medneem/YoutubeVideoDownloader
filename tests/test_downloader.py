import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import downloader

from downloader import build_download_options


class DownloaderOptionsTest(unittest.TestCase):
    def options(self, mode="video", quality="best", proxy=False):
        settings = {
            "download_dir": "C:/Downloads",
            "mode": mode,
            "quality": quality,
            "proxy_enabled": proxy,
            "proxy_url": "http://127.0.0.1:8118",
        }
        return build_download_options(
            settings,
            ffmpeg_exe="C:/tools/ffmpeg.exe",
            deno_exe="C:/tools/deno.exe",
            progress_hook=lambda info: None,
            postprocessor_hook=lambda info: None,
        )

    def test_onefile_deno_is_embedded_but_ffmpeg_external(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            app_dir = root / "app"
            bundle_dir = root / "extracted"
            app_dir.mkdir()
            bundle_dir.mkdir()
            embedded = bundle_dir / "deno.exe"
            external = app_dir / "ffmpeg.exe"
            embedded.write_bytes(b"fake-deno-for-path-test")
            external.write_bytes(b"fake-ffmpeg-for-path-test")
            with (
                patch("downloader.application_directory", return_value=app_dir),
                patch.object(downloader.sys, "frozen", True, create=True),
                patch.object(downloader.sys, "_MEIPASS", str(bundle_dir), create=True),
            ):
                self.assertEqual(downloader.find_program("deno"), str(embedded))
                self.assertEqual(downloader.find_program("ffmpeg"), str(external))
                self.assertFalse((app_dir / "deno.exe").exists())
                external.unlink()
                with self.assertRaises(FileNotFoundError):
                    downloader.find_program("ffmpeg")

    def test_missing_embedded_deno_fails_in_frozen_application(self):
        with tempfile.TemporaryDirectory() as temporary:
            with (
                patch.object(downloader.sys, "frozen", True, create=True),
                patch.object(downloader.sys, "_MEIPASS", temporary, create=True),
            ):
                with self.assertRaises(FileNotFoundError):
                    downloader.find_program("deno")

    def test_video_quality(self):
        options = self.options(quality="1080")
        self.assertIn("height<=1080", options["format"])
        self.assertEqual(options["merge_output_format"], "mp4")
        self.assertEqual(options["proxy"], "")

    def test_mp3(self):
        options = self.options(mode="audio")
        self.assertEqual(options["postprocessors"][0]["preferredcodec"], "mp3")

    def test_http_proxy_and_deno(self):
        options = self.options(proxy=True)
        self.assertEqual(options["proxy"], "http://127.0.0.1:8118")
        self.assertEqual(
            options["js_runtimes"]["deno"]["path"], "C:/tools/deno.exe"
        )


if __name__ == "__main__":
    unittest.main()
