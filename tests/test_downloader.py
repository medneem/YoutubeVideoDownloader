import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import downloader

from downloader import build_download_options


class DownloaderOptionsTest(unittest.TestCase):
    def options(
        self, mode="video", quality="best", proxy=False,
        cookies_mode="none", cookies_browser="chrome", cookies_file="",
    ):
        settings = {
            "download_dir": "C:/Downloads",
            "mode": mode,
            "quality": quality,
            "proxy_enabled": proxy,
            "proxy_url": "http://127.0.0.1:8118",
            "cookies_mode": cookies_mode,
            "cookies_browser": cookies_browser,
            "cookies_file": cookies_file,
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
        self.assertEqual(
            options["outtmpl"],
            "%(title)s [%(id)s] [%(height)sp].%(ext)s",
        )

    def test_mp3(self):
        options = self.options(mode="audio")
        self.assertEqual(options["postprocessors"][0]["preferredcodec"], "mp3")
        self.assertEqual(
            options["outtmpl"],
            "%(title)s [%(id)s] [MP3 192kbps].%(ext)s",
        )

    def test_best_quality_uses_actual_resolution_in_name(self):
        options = self.options(quality="best")
        self.assertEqual(
            options["outtmpl"],
            "%(title)s [%(id)s] [%(height)sp].%(ext)s",
        )

    def test_repeated_download_overwrites_instead_of_resuming(self):
        for mode in ("video", "audio"):
            with self.subTest(mode=mode):
                options = self.options(mode=mode)
                self.assertTrue(options["overwrites"])
                self.assertFalse(options["continuedl"])

    def test_http_proxy_and_deno(self):
        options = self.options(proxy=True)
        self.assertEqual(options["proxy"], "http://127.0.0.1:8118")
        self.assertEqual(
            options["js_runtimes"]["deno"]["path"], "C:/tools/deno.exe"
        )

    def test_cookies_are_off_by_default(self):
        options = self.options()
        self.assertNotIn("cookiesfrombrowser", options)
        self.assertNotIn("cookiefile", options)

    def test_cookies_from_browser(self):
        for browser in ("chrome", "firefox", "edge"):
            with self.subTest(browser=browser):
                options = self.options(cookies_mode="browser", cookies_browser=browser)
                self.assertEqual(options["cookiesfrombrowser"], (browser,))
                self.assertNotIn("cookiefile", options)

    def test_cookies_from_netscape_file(self):
        with tempfile.TemporaryDirectory() as directory:
            cookie_file = Path(directory) / "cookies.txt"
            cookie_file.write_text("# Netscape HTTP Cookie File\n", encoding="utf-8")
            options = self.options(cookies_mode="file", cookies_file=str(cookie_file))
            self.assertEqual(options["cookiefile"], str(cookie_file))
            self.assertNotIn("cookiesfrombrowser", options)

    def test_missing_cookies_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "missing-cookies.txt")
            with self.assertRaisesRegex(FileNotFoundError, "Файл cookies не найден"):
                self.options(cookies_mode="file", cookies_file=path)


class FinalFileNameTest(unittest.TestCase):
    def test_reports_existing_video_after_merge(self):
        with tempfile.TemporaryDirectory() as temp:
            filename = Path(temp) / "Тест [abc] [1080p].mp4"
            filename.write_bytes(b"merged MP4")
            self.assertEqual(downloader.final_download_path({"filepath": str(filename)}), filename)

    def test_reports_final_mp3_not_source_extension(self):
        with tempfile.TemporaryDirectory() as temp:
            mp3 = Path(temp) / "Музыка [abc] [MP3 192kbps].mp3"
            mp3.write_bytes(b"converted MP3")
            info = {"filepath": str(mp3), "ext": "webm", "_filename": "source.webm"}
            self.assertEqual(downloader.final_download_path(info), mp3)

    def test_does_not_report_missing_or_temporary_file(self):
        with tempfile.TemporaryDirectory() as temp:
            missing = Path(temp) / "not-saved.mp4"
            self.assertIsNone(downloader.final_download_path({"filepath": str(missing)}))
            self.assertIsNone(downloader.final_download_path({"ext": "mp4"}))
            self.assertIsNone(downloader.final_download_path(None))


class DownloadWorkerFinalNameTest(unittest.TestCase):
    def test_emits_actual_filename_after_successful_download(self):
        with tempfile.TemporaryDirectory() as temp:
            name = Path(temp) / "Результат [id] [MP3 192kbps].mp3"
            name.write_bytes(b"mp3")
            settings = {
                "download_dir": temp,
                "mode": "audio",
                "quality": "best",
                "proxy_enabled": False,
                "proxy_url": "",
                "cookies_mode": "none",
            }
            worker = downloader.DownloadWorker("https://www.youtube.com/watch?v=test", settings)
            actual_files, completions = [], []
            worker.file_saved.connect(actual_files.append)
            worker.finished.connect(lambda success, message: completions.append((success, message)))

            class FakeDownloader:
                def __init__(self, options):
                    self.options = options
                def __enter__(self):
                    return self
                def __exit__(self, *args):
                    return False
                def extract_info(self, url, download=False):
                    assert download is True
                    return {"filepath": str(name), "ext": "webm"}

            with (
                patch("downloader.find_program", side_effect=lambda p: f"C:/tools/{p}.exe"),
                patch("downloader.yt_dlp.YoutubeDL", FakeDownloader),
            ):
                worker.run()

            self.assertEqual(actual_files, [str(name)])
            self.assertEqual(len(completions), 1)
            self.assertTrue(completions[0][0])


if __name__ == "__main__":
    unittest.main()
