from __future__ import annotations

from pathlib import Path

from recorder_proxy.utils.toml_compat import loads


class ExportValidator:
    def validate_toml(self, path: Path) -> None:
        loads(path.read_text(encoding="utf-8"))
