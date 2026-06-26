from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class _StringEnum(str, Enum):
    pass


class DeviceType(_StringEnum):
    BBU = "BBU"
    SIGNAL_GENERATOR = "SIGNAL_GENERATOR"
    SPECTRUM_ANALYZER = "SPECTRUM_ANALYZER"
    POWER_METER = "POWER_METER"
    CUSTOM_TCP = "CUSTOM_TCP"


class ProtocolMode(_StringEnum):
    BBU_AUTO = "BBU_AUTO"
    TEXT_INSTRUMENT = "TEXT_INSTRUMENT"


@dataclass(frozen=True)
class RouteConfig:
    route_id: str
    device_id: str
    device_type: str
    protocol_mode: ProtocolMode
    listen_ip: str
    listen_port: int
    hardware_ip: str
    hardware_port: int


@dataclass(frozen=True)
class DeviceConfig:
    device_id: str
    device_type: str
    protocol_mode: ProtocolMode
    label: str
    routes: list[RouteConfig] = field(default_factory=list)


@dataclass(frozen=True)
class AppSettings:
    project_root: Path
    recordings_dir: Path
    raw_queue_size: int = 100000
    parse_queue_size: int = 100000
    chunk_size: int = 65536
    max_frame_bytes: int = 10 * 1024 * 1024
    flush_every_events: int = 20
    flush_interval_seconds: float = 1.0


@dataclass
class AppConfig:
    settings: AppSettings
    devices: list[DeviceConfig]

    @property
    def routes(self) -> list[RouteConfig]:
        return [route for device in self.devices for route in device.routes]
