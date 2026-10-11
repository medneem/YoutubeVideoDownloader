import json
import tempfile
import unittest
from pathlib import Path

from settings import (
    default_settings,
    load_settings,
    normalize_settings,
    save_settings,
    validate_http_proxy,
)


class SettingsTest(unittest.TestCase):
    def test_config_is_created_beside_app(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            settings = load_settings(folder)
            self.assertEqual(settings["mode"], "video")
            self.assertFalse(settings["proxy_enabled"])
            self.assertEqual(settings["proxy_url"], "")
            self.assertTrue((folder / "config.json").is_file())

    def test_settings_roundtrip_with_proxy(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            values = default_settings()
            values["proxy_enabled"] = True
            values["proxy_url"] = "http://127.0.0.1:8118"
            values["quality"] = "1080"
            save_settings(values, folder)
            self.assertEqual(load_settings(folder), values)
            raw = json.loads((folder / "config.json").read_text(encoding="utf-8"))
            self.assertTrue(raw["proxy_enabled"])

    def test_proxy_validation(self):
        self.assertEqual(
            validate_http_proxy(" http://127.0.0.1:8118 "),
            "http://127.0.0.1:8118",
        )
        for invalid in ("", "socks5://127.0.0.1:1080", "127.0.0.1:8118", "http://localhost"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    validate_http_proxy(invalid)

    def test_invalid_config_does_not_get_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text("{broken", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_settings(Path(directory))
            self.assertEqual(path.read_text(encoding="utf-8"), "{broken")

    def test_defaults_are_merged(self):
        value = normalize_settings({"quality": "720"})
        self.assertEqual(value["quality"], "720")
        self.assertIn("proxy_enabled", value)


if __name__ == "__main__":
    unittest.main()
