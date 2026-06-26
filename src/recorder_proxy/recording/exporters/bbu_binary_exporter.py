from __future__ import annotations

from pathlib import Path
import json
import sqlite3

from recorder_proxy.recording.exporters.toml_writer import quote
from recorder_proxy.recording.session_manager import RecordingSession
from recorder_proxy.utils.time_utils import session_stamp


class BbuBinaryExporter:
    def export(self, session: RecordingSession, device_id: str) -> Path | None:
        out_dir = session.paths.exports / device_id / "binary"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"bbu_bts5900_binary_recording_{session_stamp()}.toml"
        conn = sqlite3.connect(session.paths.sqlite_path)
        rows = conn.execute(
            """
            SELECT message_id, connection_id, source_event_ids, message_start_offset, message_length,
                   message_sha256, decoded_summary, raw_message_hex
            FROM parsed_messages
            WHERE device_id=? AND classification='BBU_BINARY'
            ORDER BY rowid
            """,
            (device_id,),
        ).fetchall()
        conn.close()
        if not rows:
            return None
        lines = [
            "[device]",
            'type = "bbu_binary_recording"',
            'protocol = "bbu-tcp"',
            f"source_session_id = {quote(session.session_id)}",
            "",
        ]
        for index, row in enumerate(rows, start=1):
            _, connection_id, event_ids, offset, length, sha256, summary_json, raw_hex = row
            summary = json.loads(summary_json)
            lines.extend(
                [
                    "[[device.binary_messages]]",
                    f"id = {quote(f'rec_bbu_bin_{index:06d}')}",
                    f"classification = {quote('BBU_BINARY')}",
                    f"transparent_cmd = {quote(str(summary.get('transparent_cmd')))}",
                    f"entity_cmd = {quote(str(summary.get('entity_cmd')))}",
                    f"entity_operation_code = {quote(str(summary.get('entity_operation_code')))}",
                    f"transaction_id1 = {int(summary.get('transaction_id1') or 0)}",
                    'match_strategy = "transaction_and_operation"',
                    'dynamic_fields = ["transaction_id1","length_fields"]',
                    f"normalized_match_key = {quote(str(summary.get('entity_operation_code')))}",
                    f"raw_request_hex = {quote(raw_hex)}",
                    'raw_response_hex = ""',
                    f"source_device_id = {quote(device_id)}",
                    f"source_session_id = {quote(session.session_id)}",
                    f"source_connection_id = {quote(connection_id)}",
                    f"source_raw_stream_file = {quote(f'../../raw/{device_id}/connections/{connection_id}_client_to_hardware.bin')}",
                    f"source_byte_offset = {int(offset)}",
                    f"source_byte_length = {int(length)}",
                    f"source_event_ids = {event_ids}",
                    f"source_raw_sha256 = {quote(sha256)}",
                    "",
                ]
            )
        out_path.write_text("\n".join(lines), encoding="utf-8")
        return out_path
