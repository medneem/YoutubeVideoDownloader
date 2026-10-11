"""Set the release number from a successful GitHub Actions build.

Usage: python scripts/stamp_version.py 0.1 42
Writes version.py and PyInstaller's Windows VERSIONINFO resource file.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def make_version(base_version: str, run_number: str) -> str:
    if not re.fullmatch(r"\d+\.\d+", base_version):
        raise ValueError("BASE_VERSION must look like 0.1")
    if not re.fullmatch(r"[1-9]\d*", run_number):
        raise ValueError("GitHub run number must be a positive integer")
    major, minor = (int(part) for part in base_version.split("."))
    build = int(run_number)
    if any(number > 65535 for number in (major, minor, build)):
        raise ValueError("Windows executable version components must be <= 65535")
    return f"{major}.{minor}.{build}"


def windows_version_info(version: str) -> str:
    major, minor, build = map(int, version.split("."))
    win_version = (major, minor, build, 0)
    return f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={win_version!r},
    prodvers={win_version!r},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable('040904B0', [
        StringStruct('CompanyName', 'medneem'),
        StringStruct('FileDescription', 'YoutubeVideoDownloader'),
        StringStruct('FileVersion', '{version}.0'),
        StringStruct('InternalName', 'YoutubeVideoDownloader'),
        StringStruct('OriginalFilename', 'YoutubeVideoDownloader.exe'),
        StringStruct('ProductName', 'YoutubeVideoDownloader'),
        StringStruct('ProductVersion', '{version}.0')
      ])
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""


def stamp_version(
    base_version: str, run_number: str, project_root: Path
) -> str:
    version = make_version(base_version, run_number)
    (project_root / "version.py").write_text(
        f'"""Build version, generated in CI from github.run_number."""\n'
        f'APP_VERSION = "{version}"\n',
        encoding="utf-8",
    )
    (project_root / "windows_version_info.txt").write_text(
        windows_version_info(version), encoding="utf-8"
    )
    return version


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: stamp_version.py BASE_VERSION RUN_NUMBER", file=sys.stderr)
        raise SystemExit(2)
    root = Path(__file__).resolve().parent.parent
    try:
        created = stamp_version(sys.argv[1], sys.argv[2], root)
    except ValueError as exc:
        print(f"Build version error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    print(f"Generated application version {created}")
