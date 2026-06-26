from __future__ import annotations

from pathlib import Path
import sys


def resource_path(relative_path: str) -> Path:
    bundled_root = getattr(sys, "_MEIPASS", None)
    if bundled_root:
        return Path(bundled_root) / relative_path
    return Path(__file__).resolve().parent / relative_path


def app_icon_path() -> Path:
    return resource_path("assets/app_icon.svg")
