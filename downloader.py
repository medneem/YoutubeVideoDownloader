"""yt-dlp wrapper and Qt background worker."""

from __future__ import annotations

import shutil
import threading
import time
from pathlib import Path

import yt_dlp
from PySide6.QtCore import QObject, Signal, Slot

from settings import application_directory


class DownloadCancelled(Exception):
    """Raised by yt-dlp progress hooks when the user cancels a download."""


def find_program(name: str) -> str:
    """Prefer the executable bundled alongside the portable EXE."""
    local = application_directory() / (name + ".exe")
    if local.is_file():
        return str(local)
    system = shutil.which(name)
    if system:
        return system
    raise FileNotFoundError(
        f"Не найден {name}. Для портативной версии нужны {name}.exe "
        "рядом с YoutubeVideoDownloader.exe."
    )


def build_download_options(
    settings: dict,
    *,
    ffmpeg_exe: str,
    deno_exe: str,
    progress_hook,
    postprocessor_hook,
) -> dict:
    output = Path(settings["download_dir"]).expanduser()
    options = {
        "paths": {"home": str(output)},
        "outtmpl": "%(title)s [%(id)s].%(ext)s",
        "noplaylist": True,
        "ignoreerrors": False,
        "quiet": True,
        "no_warnings": False,
        "overwrites": False,
        "continuedl": True,
        "ffmpeg_location": str(Path(ffmpeg_exe).parent),
        "js_runtimes": {"deno": {"path": deno_exe}},
        "proxy": settings["proxy_url"] if settings["proxy_enabled"] else "",
        "progress_hooks": [progress_hook],
        "postprocessor_hooks": [postprocessor_hook],
    }
    if settings["mode"] == "audio":
        options["format"] = "bestaudio/best"
        options["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
    else:
        quality = settings["quality"]
        if quality == "best":
            options["format"] = "bv*+ba/b"
        else:
            options["format"] = (
                f"bv*[height<={quality}]+ba/b[height<={quality}]"
            )
        options["merge_output_format"] = "mp4"
    return options


class DownloadWorker(QObject):
    progress = Signal(int, str)
    finished = Signal(bool, str)

    def __init__(self, url: str, settings: dict) -> None:
        super().__init__()
        self.url = url
        self.settings = settings.copy()
        self._cancel_requested = threading.Event()
        self._last_update = 0.0

    def cancel(self) -> None:
        self._cancel_requested.set()

    def _check_cancel(self) -> None:
        if self._cancel_requested.is_set():
            raise DownloadCancelled("Загрузка отменена.")

    def _progress_hook(self, info: dict) -> None:
        self._check_cancel()
        if info.get("status") == "finished":
            self.progress.emit(100, "Загружено. Обработка файла…")
            return
        if info.get("status") != "downloading":
            return
        current_time = time.monotonic()
        if current_time - self._last_update < 0.2:
            return
        self._last_update = current_time

        downloaded = info.get("downloaded_bytes") or 0
        total = info.get("total_bytes") or info.get("total_bytes_estimate") or 0
        percentage = min(100, round(100 * downloaded / total)) if total else 0
        speed = info.get("speed")
        eta = info.get("eta")
        details = f"Загружено: {downloaded / 1048576:.1f} МБ"
        if total:
            details += f" / {total / 1048576:.1f} МБ"
        if isinstance(speed, (int, float)) and speed > 0:
            details += f" • {speed / 1048576:.1f} МБ/с"
        if isinstance(eta, (int, float)) and eta >= 0:
            details += f" • осталось {int(eta)} с"
        self.progress.emit(percentage, details)

    def _postprocessor_hook(self, info: dict) -> None:
        self._check_cancel()
        if info.get("status") == "started":
            self.progress.emit(100, "Обработка файла через FFmpeg…")

    @Slot()
    def run(self) -> None:
        try:
            self._check_cancel()
            ffmpeg_exe = find_program("ffmpeg")
            deno_exe = find_program("deno")
            Path(self.settings["download_dir"]).expanduser().mkdir(
                parents=True, exist_ok=True
            )
            options = build_download_options(
                self.settings,
                ffmpeg_exe=ffmpeg_exe,
                deno_exe=deno_exe,
                progress_hook=self._progress_hook,
                postprocessor_hook=self._postprocessor_hook,
            )
            with yt_dlp.YoutubeDL(options) as downloader:
                downloader.download([self.url])
            self._check_cancel()
        except Exception as exc:
            if self._cancel_requested.is_set() or isinstance(exc, DownloadCancelled):
                self.finished.emit(False, "Загрузка отменена.")
            else:
                self.finished.emit(False, f"Ошибка загрузки: {exc}")
        else:
            self.finished.emit(True, "Готово! Файл сохранён в выбранной папке.")
