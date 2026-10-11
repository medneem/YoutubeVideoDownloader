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

    def test_deno_ffmpeg_and_ffprobe_are_external(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ext = root / "app"
            internal = root / "_MEIPASS"
            ext.mkdir()
            internal.mkdir()
            (internal / "deno.exe").write_bytes(b"obsolete")
            for name in ("deno", "ffmpeg", "ffprobe"):
                (ext / (name + ".exe")).write_bytes(b"external")
            with (
                patch("downloader.application_directory", return_value=ext),
                patch.object(downloader.sys, "frozen", True, create=True),
                patch.object(downloader.sys, "_MEIPASS", str(internal), create=True),
            ):
                for name in ("deno", "ffmpeg", "ffprobe"):
                    self.assertEqual(downloader.find_program(name), str(ext / (name + ".exe")))
                (ext / "deno.exe").unlink()
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
