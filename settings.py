"""Portable JSON settings stored beside the executable."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

VALID_MODES = {"video", "audio"}
VALID_QUALITIES = {"best", "2160", "1440", "1080", "720", "480", "360"}


def application_directory() -> Path:
    """In PyInstaller onedir, sys.executable is beside config.json."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def default_settings() -> dict[str, Any]:
    return {
        "download_dir": str(Path.home() / "Downloads"),
        "mode": "video",
        "quality": "best",
        "proxy_enabled": False,
        "proxy_url": "",
    }


def validate_http_proxy(value: str) -> str:
    value = value.strip()
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as exc:
        raise ValueError("Некорректный адрес или порт прокси.") from exc
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or port is None
        or not (1 <= port <= 65535)
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(
            "Укажите HTTP-прокси в виде http://127.0.0.1:8118"
        )
    return value


def normalize_settings(raw: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError("Содержимое config.json должно быть JSON-объектом.")

    values = default_settings()
    for name in values:
        if name in raw:
            values[name] = raw[name]

    if not isinstance(values["download_dir"], str) or not values["download_dir"].strip():
        raise ValueError("download_dir должен быть непустой строкой.")
    if values["mode"] not in VALID_MODES:
        raise ValueError("Недопустимый режим загрузки.")
    if values["quality"] not in VALID_QUALITIES:
        raise ValueError("Недопустимое качество видео.")
    if not isinstance(values["proxy_enabled"], bool):
        raise ValueError("proxy_enabled должен быть true или false.")
    if not isinstance(values["proxy_url"], str):
        raise ValueError("proxy_url должен быть строкой.")
    values["download_dir"] = values["download_dir"].strip()
    values["proxy_url"] = values["proxy_url"].strip()
    if values["proxy_enabled"]:
        values["proxy_url"] = validate_http_proxy(values["proxy_url"])
    return values


def settings_file(base_dir: Path | None = None) -> Path:
    return (base_dir if base_dir is not None else application_directory()) / "config.json"


def save_settings(settings: dict[str, Any], base_dir: Path | None = None) -> None:
    path = settings_file(base_dir)
    normalized = normalize_settings(settings)
    temporary = path.with_name(path.name + ".tmp")
    try:
        temporary.write_text(
            json.dumps(normalized, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def load_settings(base_dir: Path | None = None) -> dict[str, Any]:
    path = settings_file(base_dir)
    if not path.exists():
        defaults = default_settings()
        save_settings(defaults, base_dir)
        return defaults
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Некорректный JSON в {path}: {exc}") from exc
    return normalize_settings(raw)
