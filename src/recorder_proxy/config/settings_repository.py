from __future__ import annotations

from pathlib import Path

from recorder_proxy.config.models import AppSettings
from recorder_proxy.utils.toml_compat import loads


def load_settings(project_root: Path) -> AppSettings:
    path = project_root / "config" / "app_settings.toml"
    data = loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    app = data.get("app", {})
    recordings_dir = Path(app.get("recordings_dir", "recordings"))
    if not recordings_dir.is_absolute():
        recordings_dir = project_root / recordings_dir
    return AppSettings(
        project_root=project_root,
        recordings_dir=recordings_dir,
        raw_queue_size=int(app.get("raw_queue_size", 100000)),
        parse_queue_size=int(app.get("parse_queue_size", 100000)),
        chunk_size=int(app.get("chunk_size", 65536)),
        max_frame_bytes=int(app.get("max_frame_bytes", 10 * 1024 * 1024)),
        flush_every_events=int(app.get("flush_every_events", 20)),
        flush_interval_seconds=float(app.get("flush_interval_seconds", 1.0)),
    )
