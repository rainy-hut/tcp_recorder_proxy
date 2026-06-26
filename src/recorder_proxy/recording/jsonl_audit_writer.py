from __future__ import annotations

from pathlib import Path
import json


class JsonlAuditWriter:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self._file = path.open("a", encoding="utf-8", newline="\n")

    def write(self, payload: dict[str, object]) -> None:
        self._file.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")

    def flush(self) -> None:
        self._file.flush()

    def close(self) -> None:
        self._file.flush()
        self._file.close()
