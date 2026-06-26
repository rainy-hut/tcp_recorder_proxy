from __future__ import annotations

from pathlib import Path
import json
import sqlite3

from recorder_proxy.recording.exporters.toml_writer import quote
from recorder_proxy.recording.session_manager import RecordingSession
from recorder_proxy.utils.time_utils import session_stamp


class TextInstrumentExporter:
    def export(self, session: RecordingSession, device_id: str) -> Path | None:
        out_dir = session.paths.exports / device_id / "text"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{device_id.lower()}_text_{session_stamp()}.toml"
        conn = sqlite3.connect(session.paths.sqlite_path)
        rows = conn.execute(
            """
            SELECT connection_id, source_event_ids, decoded_summary, raw_message_hex, message_sha256
            FROM parsed_messages
            WHERE device_id=? AND classification IN ('TEXT_COMMAND','TEXT_RESPONSE','UNKNOWN_TEXT')
            ORDER BY rowid
            """,
            (device_id,),
        ).fetchall()
        conn.close()
        if not rows:
            return None
        lines = ["[device]", 'type = "text_instrument_recording"', f"source_session_id = {quote(session.session_id)}", ""]
        for index, (connection_id, event_ids, summary_json, raw_hex, sha256) in enumerate(rows, start=1):
            summary = json.loads(summary_json)
            text = str(summary.get("text_preview", ""))
            lines.extend(
                [
                    "[[device.commands]]",
                    f"id = {quote(f'rec_text_{index:06d}')}",
                    f"request = {quote(text)}",
                    'response = ""',
                    'match_strategy = "exact_or_regex"',
                    'dynamic_fields = []',
                    f"source_device_id = {quote(device_id)}",
                    f"source_session_id = {quote(session.session_id)}",
                    f"source_connection_id = {quote(connection_id)}",
                    f"source_event_ids = {event_ids}",
                    f"raw_request_hex = {quote(raw_hex)}",
                    'raw_response_hex = ""',
                    f"source_raw_sha256 = {quote(sha256)}",
                    "",
                ]
            )
        out_path.write_text("\n".join(lines), encoding="utf-8")
        return out_path
