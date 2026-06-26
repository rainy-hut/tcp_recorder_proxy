from __future__ import annotations

from pathlib import Path

from recorder_proxy.config.models import DeviceConfig, ProtocolMode, RouteConfig
from recorder_proxy.utils.toml_compat import loads


def load_devices(project_root: Path) -> list[DeviceConfig]:
    path = project_root / "config" / "routes.toml"
    data = loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    devices: list[DeviceConfig] = []
    for device_data in data.get("devices", []):
        device_id = str(device_data["device_id"])
        device_type = str(device_data["device_type"])
        protocol_mode = ProtocolMode(str(device_data["protocol_mode"]))
        routes = [
            RouteConfig(
                route_id=str(route["route_id"]),
                device_id=device_id,
                device_type=device_type,
                protocol_mode=protocol_mode,
                listen_ip=str(route.get("listen_ip", "127.0.0.1")),
                listen_port=int(route["listen_port"]),
                hardware_ip=str(route["hardware_ip"]),
                hardware_port=int(route["hardware_port"]),
            )
            for route in device_data.get("routes", [])
        ]
        devices.append(
            DeviceConfig(
                device_id=device_id,
                device_type=device_type,
                protocol_mode=protocol_mode,
                label=str(device_data.get("label", device_id)),
                routes=routes,
            )
        )
    return devices


def save_devices(project_root: Path, devices: list[DeviceConfig]) -> None:
    path = project_root / "config" / "routes.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    for device in devices:
        lines.extend(
            [
                "[[devices]]",
                f"device_id = {_quote(device.device_id)}",
                f"device_type = {_quote(_enum_or_text(device.device_type))}",
                f"protocol_mode = {_quote(device.protocol_mode.value)}",
                f"label = {_quote(device.label)}",
                "",
            ]
        )
        for route in device.routes:
            lines.extend(
                [
                    "[[devices.routes]]",
                    f"route_id = {_quote(route.route_id)}",
                    f"listen_ip = {_quote(route.listen_ip)}",
                    f"listen_port = {route.listen_port}",
                    f"hardware_ip = {_quote(route.hardware_ip)}",
                    f"hardware_port = {route.hardware_port}",
                    "",
                ]
            )
    path.write_text("\n".join(lines), encoding="utf-8")


def _quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _enum_or_text(value: object) -> str:
    return str(getattr(value, "value", value))
