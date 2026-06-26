from __future__ import annotations

import asyncio
from dataclasses import replace
import hashlib
import json
from pathlib import Path
from typing import BinaryIO
import uuid

from recorder_proxy.config.models import AppConfig, ProtocolMode
from recorder_proxy.protocol.bbu.bbu_auto_framer import BbuAutoFramer
from recorder_proxy.protocol.text.text_framer import TextFramer
from recorder_proxy.recording.event_queue import RecordingQueues
from recorder_proxy.recording.jsonl_audit_writer import JsonlAuditWriter
from recorder_proxy.recording.models import ParsedMessage, RawCaptureEvent
from recorder_proxy.recording.session_manager import RecordingSession
from recorder_proxy.recording.sqlite_repository import SQLiteRepository
from recorder_proxy.utils.hex_utils import raw_hex, sha256_hex


class _DeviceRawWriters:
    def __init__(self, session: RecordingSession, device_id: str, device_type: str, started_at: str, parse_enabled: bool) -> None:
        self.session = session
        self.device_id = device_id
        self.device_type = device_type
        self.root = session.paths.raw / device_id
        self.connections_dir = self.root / "connections"
        self.connections_dir.mkdir(parents=True, exist_ok=True)
        self.events = JsonlAuditWriter(self.root / "events.jsonl")
        self.parsed = JsonlAuditWriter(self.root / "parsed_messages.jsonl")
        self.warnings = JsonlAuditWriter(self.root / "parse_warnings.jsonl")
        self.files: dict[tuple[str, str], BinaryIO] = {}
        self.hashers: dict[tuple[str, str], "hashlib._Hash"] = {}
        self.offsets: dict[tuple[str, str], int] = {}
        self.connections: dict[str, dict[str, object]] = {}
        self.event_count = 0
        self.started_at = started_at
        self.parse_enabled = parse_enabled

    def write_raw(self, event: RawCaptureEvent) -> RawCaptureEvent:
        key = (event.connection.connection_id, event.direction)
        rel = f"connections/{event.connection.connection_id}_{event.direction}.bin"
        if key not in self.files:
            self.files[key] = (self.root / rel).open("ab")
            self.hashers[key] = hashlib.sha256()
            self.offsets[key] = 0
        offset = self.offsets[key]
        self.files[key].write(event.data)
        self.hashers[key].update(event.data)
        self.offsets[key] += len(event.data)
        digest = sha256_hex(event.data)
        self.event_count += 1
        c = event.connection
        written = replace(event, raw_stream_file=rel, byte_offset=offset)
        self.events.write(
            {
                "event_id": event.event_id,
                "session_id": c.session_id,
                "device_id": c.device_id,
                "device_type": c.device_type,
                "route_id": c.route_id,
                "connection_id": c.connection_id,
                "timestamp_utc": event.timestamp_utc,
                "timestamp_ns": event.timestamp_ns,
                "monotonic_ns": event.monotonic_ns,
                "direction": event.direction,
                "listen_ip": c.listen_ip,
                "listen_port": c.listen_port,
                "client_ip": c.client_ip,
                "client_port": c.client_port,
                "hardware_ip": c.hardware_ip,
                "hardware_port": c.hardware_port,
                "chunk_sequence": event.chunk_sequence,
                "raw_stream_file": rel,
                "byte_offset": offset,
                "byte_length": len(event.data),
                "sha256": digest,
                "raw_hex": raw_hex(event.data),
                "forward_status": event.forward_status,
                "forward_latency_us": event.forward_latency_us,
                "classification_at_capture": "UNCLASSIFIED",
                "parser_status_at_capture": "PENDING" if self.parse_enabled else "DISABLED",
            }
        )
        conn = self.connections.setdefault(
            c.connection_id,
            {
                "connection_id": c.connection_id,
                "client_to_hardware_file": f"connections/{c.connection_id}_client_to_hardware.bin",
                "hardware_to_client_file": f"connections/{c.connection_id}_hardware_to_client.bin",
                "client_to_hardware_bytes": 0,
                "hardware_to_client_bytes": 0,
            },
        )
        conn[f"{event.direction}_bytes"] = int(conn.get(f"{event.direction}_bytes", 0)) + len(event.data)
        return written

    def write_parsed(self, message: ParsedMessage) -> None:
        self.parsed.write(message.__dict__)

    def write_warning(self, payload: dict[str, object]) -> None:
        self.warnings.write(payload)

    def close(self, generated_toml_files: list[str], dropped_count: int, parse_error_count: int, unknown_count: int, routes: list[dict[str, object]]) -> None:
        for key, file in self.files.items():
            file.flush()
            file.close()
            conn_id, direction = key
            if conn_id in self.connections:
                self.connections[conn_id][f"{direction}_sha256"] = self.hashers[key].hexdigest()
        self.events.close()
        self.parsed.close()
        self.warnings.close()
        manifest = {
            "format_version": "1.0",
            "session_id": self.session.session_id,
            "device_id": self.device_id,
            "device_type": self.device_type,
            "recording_started_at": self.started_at,
            "recording_ended_at": self.session.ended_at,
            "recording_mode": self.session.recording_mode,
            "routes": routes,
            "connections": list(self.connections.values()),
            "event_count": self.event_count,
            "raw_capture_dropped_count": dropped_count,
            "parse_error_count": parse_error_count,
            "unknown_message_count": unknown_count,
            "generated_toml_files": generated_toml_files,
        }
        (self.root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


class ProtocolParser:
    def __init__(self, app_config: AppConfig) -> None:
        self.app_config = app_config
        self.framers: dict[tuple[str, str], object] = {}

    def parse(self, event: RawCaptureEvent) -> list[ParsedMessage]:
        key = (event.connection.connection_id, event.direction)
        if key not in self.framers:
            if event.connection.device_type == "BBU":
                self.framers[key] = BbuAutoFramer(self.app_config.settings.max_frame_bytes)
            else:
                self.framers[key] = TextFramer()
        framer = self.framers[key]
        frames = framer.feed(event.data)  # type: ignore[attr-defined]
        messages: list[ParsedMessage] = []
        offset = event.byte_offset
        for frame in frames:
            data = frame.data
            messages.append(
                ParsedMessage(
                    message_id=f"msg_{uuid.uuid4().hex}",
                    session_id=event.connection.session_id,
                    device_id=event.connection.device_id,
                    route_id=event.connection.route_id,
                    connection_id=event.connection.connection_id,
                    source_event_ids=[event.event_id],
                    direction=event.direction,
                    message_start_offset=offset,
                    message_length=len(data),
                    message_sha256=sha256_hex(data),
                    classification=frame.classification,
                    parse_status=frame.parse_status,
                    parser_name=framer.__class__.__name__,
                    parser_version="1.0.0",
                    decoded_summary=frame.decoded_summary,
                    raw_message_hex=raw_hex(data),
                    parse_error=frame.parse_error,
                )
            )
            offset += len(data)
        return messages


class EventProcessor:
    def __init__(self, app_config: AppConfig, session: RecordingSession, queues: RecordingQueues, parse_enabled: bool = True) -> None:
        self.app_config = app_config
        self.session = session
        self.queues = queues
        self.parse_enabled = parse_enabled
        self.sqlite = SQLiteRepository(session.paths.sqlite_path)
        self.parser = ProtocolParser(app_config)
        self.device_writers: dict[str, _DeviceRawWriters] = {}
        self.tasks: list[asyncio.Task[None]] = []
        self.parse_error_count = 0
        self.unknown_count = 0

    def start(self) -> None:
        self.tasks = [asyncio.create_task(self._raw_loop(), name="raw-capture-writer")]
        if self.parse_enabled:
            self.tasks.append(asyncio.create_task(self._parse_loop(), name="protocol-parser"))

    async def stop(self) -> None:
        await self.queues.raw.put(None)
        await self.queues.raw.join()
        if self.parse_enabled:
            await self.queues.parse.put(None)
            await self.queues.parse.join()
        for task in self.tasks:
            await task
        self.session.raw_capture_dropped_count = self.queues.stats.raw_dropped
        self.session.parse_dropped_count = self.queues.stats.parse_dropped
        self.session.parse_error_count = self.parse_error_count
        self.session.unknown_message_count = self.unknown_count
        self.sqlite.close()

    def close_manifests(self) -> None:
        route_by_device: dict[str, list[dict[str, object]]] = {}
        for route in self.app_config.routes:
            route_by_device.setdefault(route.device_id, []).append(
                {
                    "route_id": route.route_id,
                    "listen_ip": route.listen_ip,
                    "listen_port": route.listen_port,
                    "hardware_ip": route.hardware_ip,
                    "hardware_port": route.hardware_port,
                }
            )
        for device_id, writer in self.device_writers.items():
            writer.close(
                self.session.generated_toml_files,
                self.queues.stats.raw_dropped,
                self.parse_error_count,
                self.unknown_count,
                route_by_device.get(device_id, []),
            )

    def _writer_for(self, event: RawCaptureEvent) -> _DeviceRawWriters:
        return self.device_writers.setdefault(
            event.connection.device_id,
            _DeviceRawWriters(
                self.session,
                event.connection.device_id,
                event.connection.device_type,
                self.session.started_at,
                self.parse_enabled,
            ),
        )

    async def _raw_loop(self) -> None:
        while True:
            event = await self.queues.raw.get()
            try:
                if event is None:
                    return
                writer = self._writer_for(event)
                written = writer.write_raw(event)
                self.sqlite.insert_raw_event(written, sha256_hex(written.data))
                if self.parse_enabled:
                    self.queues.offer_parse(written)
            finally:
                self.queues.raw.task_done()

    async def _parse_loop(self) -> None:
        while True:
            event = await self.queues.parse.get()
            try:
                if event is None:
                    return
                writer = self._writer_for(event)
                try:
                    for message in self.parser.parse(event):
                        if "UNKNOWN" in message.classification:
                            self.unknown_count += 1
                        if message.parse_status == "FAILED":
                            self.parse_error_count += 1
                            writer.write_warning(
                                {
                                    "message_id": message.message_id,
                                    "event_id": event.event_id,
                                    "classification": message.classification,
                                    "parse_error": message.parse_error,
                                }
                            )
                        writer.write_parsed(message)
                        self.sqlite.insert_parsed_message(message)
                    self.sqlite.commit()
                except Exception as exc:
                    self.parse_error_count += 1
                    writer.write_warning({"event_id": event.event_id, "parse_error": repr(exc)})
            finally:
                self.queues.parse.task_done()
