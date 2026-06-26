from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Direction = Literal["client_to_hardware", "hardware_to_client"]


@dataclass(frozen=True)
class ConnectionInfo:
    session_id: str
    connection_id: str
    device_id: str
    device_type: str
    route_id: str
    listen_ip: str
    listen_port: int
    client_ip: str
    client_port: int
    hardware_ip: str
    hardware_port: int


@dataclass(frozen=True)
class RawCaptureEvent:
    event_id: str
    connection: ConnectionInfo
    timestamp_utc: str
    timestamp_ns: int
    monotonic_ns: int
    direction: Direction
    chunk_sequence: int
    data: bytes
    forward_status: str = "forwarded"
    forward_latency_us: int = 0
    raw_stream_file: str = ""
    byte_offset: int = 0


@dataclass(frozen=True)
class ParsedMessage:
    message_id: str
    session_id: str
    device_id: str
    route_id: str
    connection_id: str
    source_event_ids: list[str]
    direction: Direction
    message_start_offset: int
    message_length: int
    message_sha256: str
    classification: str
    parse_status: str
    parser_name: str
    parser_version: str
    decoded_summary: dict[str, Any] = field(default_factory=dict)
    raw_message_hex: str = ""
    parse_error: str | None = None
