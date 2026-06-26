from __future__ import annotations

from pathlib import Path
import sys


def resource_path(relative_path: str) -> Path:
    bundled_root = getattr(sys, "_MEIPASS", None)
    if bundled_root:
        root = Path(bundled_root)
        packaged = root / "recorder_proxy" / "gui" / relative_path
        if packaged.exists():
            return packaged
        return root / relative_path
    return Path(__file__).resolve().parent / relative_path


def app_icon_path() -> Path:
    return resource_path("assets/app_icon.svg")
