from __future__ import annotations

from pathlib import Path
import json
import sqlite3

from recorder_proxy.recording.exporters.toml_writer import multiline, quote
from recorder_proxy.recording.session_manager import RecordingSession
from recorder_proxy.utils.time_utils import session_stamp


class BbuMmlExporter:
    def export(self, session: RecordingSession, device_id: str) -> Path | None:
        out_dir = session.paths.exports / device_id / "mml"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"bbu_bts5900_mml_text_{session_stamp()}.toml"
        conn = sqlite3.connect(session.paths.sqlite_path)
        rows = conn.execute(
            """
            SELECT message_id, connection_id, source_event_ids, decoded_summary, raw_message_hex, message_sha256
            FROM parsed_messages
            WHERE device_id=? AND classification IN ('BBU_MML_FRAMED','BBU_MML_PLAIN')
            ORDER BY rowid
            """,
            (device_id,),
        ).fetchall()
        conn.close()
        if not rows:
            return None
        lines = [
            "[device]",
            'type = "bbu_bts5900_mml_text_recording"',
            f"source_session_id = {quote(session.session_id)}",
            "",
        ]
        for index, (message_id, connection_id, event_ids, summary_json, raw_hex, sha256) in enumerate(rows, start=1):
            summary = json.loads(summary_json)
            request = str(summary.get("mml_text") or summary.get("text_preview") or "")
            lines.extend(
                [
                    "[[device.commands]]",
                    f"id = {quote(f'rec_bbu_mml_{index:06d}')}",
                    f"request = {quote(request)}",
                    'response = ""',
                    'match_strategy = "recorded_or_regex"',
                    'dynamic_fields = []',
                    f"normalized_match_key = {quote(request.upper())}",
                    f"raw_request_hex = {quote(raw_hex)}",
                    'raw_response_hex = ""',
                    f"source_device_id = {quote(device_id)}",
                    f"source_session_id = {quote(session.session_id)}",
                    f"source_connection_id = {quote(connection_id)}",
                    f"source_event_ids = {event_ids}",
                    'source_raw_log = "../../raw/{}/events.jsonl"'.format(device_id),
                    f"source_raw_sha256 = {quote(sha256)}",
                    "",
                ]
            )
        out_path.write_text("\n".join(lines), encoding="utf-8")
        return out_path
