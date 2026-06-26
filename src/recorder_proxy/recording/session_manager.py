from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json

from recorder_proxy.config.models import AppSettings, RouteConfig
from recorder_proxy.utils.time_utils import session_stamp, utc_now_iso


@dataclass
class SessionPaths:
    root: Path
    exports: Path
    raw: Path
    sqlite_path: Path
    summary_path: Path


@dataclass
class RecordingSession:
    session_id: str
    paths: SessionPaths
    started_at: str
    recording_mode: str = "RAW_AND_PARSE"
    ended_at: str | None = None
    raw_capture_dropped_count: int = 0
    parse_dropped_count: int = 0
    parse_error_count: int = 0
    unknown_message_count: int = 0
    parsed_message_count: int = 0
    generated_toml_files: list[str] = field(default_factory=list)


class SessionManager:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.session: RecordingSession | None = None

    def start(self) -> RecordingSession:
        stamp = session_stamp()
        session_id = f"session_{stamp}"
        root = self.settings.recordings_dir / f"{stamp}_{session_id}"
        paths = SessionPaths(
            root=root,
            exports=root / "exports",
            raw=root / "raw",
            sqlite_path=root / "session.sqlite",
            summary_path=root / "session_summary.json",
        )
        for path in (paths.root, paths.exports, paths.raw):
            path.mkdir(parents=True, exist_ok=True)
        self.session = RecordingSession(session_id=session_id, paths=paths, started_at=utc_now_iso())
        return self.session

    def require(self) -> RecordingSession:
        if self.session is None:
            return self.start()
        return self.session

    def finish(self, routes: list[RouteConfig]) -> None:
        session = self.require()
        session.ended_at = utc_now_iso()
        payload = {
            "format_version": "1.0",
            "session_id": session.session_id,
            "recording_started_at": session.started_at,
            "recording_ended_at": session.ended_at,
            "recording_mode": session.recording_mode,
            "routes": [
                route.__dict__
                | {
                    "device_type": str(route.device_type),
                    "protocol_mode": route.protocol_mode.value,
                }
                for route in routes
            ],
            "raw_capture_dropped_count": session.raw_capture_dropped_count,
            "parse_dropped_count": session.parse_dropped_count,
            "parse_error_count": session.parse_error_count,
            "unknown_message_count": session.unknown_message_count,
            "parsed_message_count": session.parsed_message_count,
            "generated_toml_files": session.generated_toml_files,
        }
        session.paths.summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
