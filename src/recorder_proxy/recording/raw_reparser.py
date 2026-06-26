from __future__ import annotations

from dataclasses import dataclass
import json

from recorder_proxy.config.models import AppConfig
from recorder_proxy.recording.event_processor import ProtocolParser
from recorder_proxy.recording.models import ConnectionInfo, ParsedMessage, RawCaptureEvent
from recorder_proxy.recording.session_manager import RecordingSession
from recorder_proxy.recording.sqlite_repository import SQLiteRepository
from recorder_proxy.utils.hex_utils import sha256_hex


@dataclass(frozen=True)
class ReparseResult:
    event_count: int
    message_count: int
    parse_error_count: int
    unknown_message_count: int


class RawLogReparser:
    def __init__(self, app_config: AppConfig, session: RecordingSession) -> None:
        self.app_config = app_config
        self.session = session
        self.parser = ProtocolParser(app_config)

    def reparse(self) -> ReparseResult:
        sqlite = SQLiteRepository(self.session.paths.sqlite_path)
        sqlite.clear_parsed_messages(self.session.session_id)
        event_count = 0
        message_count = 0
        parse_error_count = 0
        unknown_message_count = 0

        for device_dir in sorted(self.session.paths.raw.iterdir() if self.session.paths.raw.exists() else []):
            if not device_dir.is_dir():
                continue
            parsed_path = device_dir / "parsed_messages.jsonl"
            warnings_path = device_dir / "parse_warnings.jsonl"
            events_path = device_dir / "events.jsonl"
            if not events_path.exists():
                continue
            with parsed_path.open("w", encoding="utf-8", newline="\n") as parsed_file, warnings_path.open(
                "w", encoding="utf-8", newline="\n"
            ) as warnings_file:
                for line in events_path.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    raw_event = json.loads(line)
                    event = self._event_from_index(raw_event, device_dir)
                    event_count += 1
                    for message in self.parser.parse(event):
                        message_count += 1
                        if "UNKNOWN" in message.classification:
                            unknown_message_count += 1
                        if message.parse_status == "FAILED":
                            parse_error_count += 1
                            warnings_file.write(
                                json.dumps(
                                    {
                                        "message_id": message.message_id,
                                        "event_id": event.event_id,
                                        "classification": message.classification,
                                        "parse_error": message.parse_error,
                                    },
                                    ensure_ascii=False,
                                    separators=(",", ":"),
                                )
                                + "\n"
                            )
                        parsed_file.write(json.dumps(message.__dict__, ensure_ascii=False, separators=(",", ":")) + "\n")
                        sqlite.insert_parsed_message(message)
            self._update_manifest(device_dir, parse_error_count, unknown_message_count)

        sqlite.commit()
        sqlite.close()
        self.session.parse_error_count = parse_error_count
        self.session.unknown_message_count = unknown_message_count
        self.session.parsed_message_count = message_count
        return ReparseResult(event_count, message_count, parse_error_count, unknown_message_count)

    def _event_from_index(self, raw_event: dict[str, object], device_dir) -> RawCaptureEvent:  # type: ignore[no-untyped-def]
        raw_stream_file = str(raw_event["raw_stream_file"])
        byte_offset = int(raw_event["byte_offset"])
        byte_length = int(raw_event["byte_length"])
        stream_path = device_dir / raw_stream_file
        with stream_path.open("rb") as stream:
            stream.seek(byte_offset)
            data = stream.read(byte_length)
        expected_sha = str(raw_event.get("sha256", ""))
        actual_sha = sha256_hex(data)
        if expected_sha and actual_sha != expected_sha:
            raise ValueError(f"{raw_event['event_id']} sha256 mismatch: {actual_sha} != {expected_sha}")
        connection = ConnectionInfo(
            session_id=str(raw_event["session_id"]),
            connection_id=str(raw_event["connection_id"]),
            device_id=str(raw_event["device_id"]),
            device_type=str(raw_event["device_type"]),
            route_id=str(raw_event["route_id"]),
            listen_ip=str(raw_event["listen_ip"]),
            listen_port=int(raw_event["listen_port"]),
            client_ip=str(raw_event["client_ip"]),
            client_port=int(raw_event["client_port"]),
            hardware_ip=str(raw_event["hardware_ip"]),
            hardware_port=int(raw_event["hardware_port"]),
        )
        return RawCaptureEvent(
            event_id=str(raw_event["event_id"]),
            connection=connection,
            timestamp_utc=str(raw_event["timestamp_utc"]),
            timestamp_ns=int(raw_event["timestamp_ns"]),
            monotonic_ns=int(raw_event["monotonic_ns"]),
            direction=str(raw_event["direction"]),  # type: ignore[arg-type]
            chunk_sequence=int(raw_event["chunk_sequence"]),
            data=data,
            forward_status=str(raw_event.get("forward_status", "forwarded")),
            forward_latency_us=int(raw_event.get("forward_latency_us", 0)),
            raw_stream_file=raw_stream_file,
            byte_offset=byte_offset,
        )

    def _update_manifest(self, device_dir, parse_error_count: int, unknown_message_count: int) -> None:  # type: ignore[no-untyped-def]
        manifest_path = device_dir / "manifest.json"
        if not manifest_path.exists():
            return
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["parse_error_count"] = parse_error_count
        manifest["unknown_message_count"] = unknown_message_count
        manifest["last_reparse_mode"] = "RAW_LOG_REPARSE"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
