from pathlib import Path

from recorder_proxy.config.models import DeviceConfig, DeviceType, ProtocolMode, RouteConfig
from recorder_proxy.config.route_repository import load_devices, save_devices


def test_save_and_load_routes_toml(tmp_path: Path):
    route = RouteConfig(
        route_id="BBU_01_5026",
        device_id="BBU_01",
        device_type="BBU",
        protocol_mode=ProtocolMode.BBU_AUTO,
        listen_ip="127.0.0.1",
        listen_port=5026,
        hardware_ip="192.168.10.20",
        hardware_port=5026,
    )
    save_devices(tmp_path, [DeviceConfig("BBU_01", "BBU", ProtocolMode.BBU_AUTO, "BBU_01", [route])])

    devices = load_devices(tmp_path)

    assert len(devices) == 1
    assert devices[0].device_type == "BBU"
    assert devices[0].protocol_mode == ProtocolMode.BBU_AUTO
    assert devices[0].routes[0].hardware_ip == "192.168.10.20"


def test_save_and_load_custom_device_type(tmp_path: Path):
    route = RouteConfig(
        route_id="CHAMBER_01_7001",
        device_id="CHAMBER_01",
        device_type="TEMPERATURE_CHAMBER",
        protocol_mode=ProtocolMode.TEXT_INSTRUMENT,
        listen_ip="127.0.0.1",
        listen_port=7001,
        hardware_ip="192.168.10.80",
        hardware_port=7001,
    )
    save_devices(
        tmp_path,
        [DeviceConfig("CHAMBER_01", "TEMPERATURE_CHAMBER", ProtocolMode.TEXT_INSTRUMENT, "温箱", [route])],
    )

    devices = load_devices(tmp_path)

    assert devices[0].device_type == "TEMPERATURE_CHAMBER"
    assert devices[0].routes[0].device_type == "TEMPERATURE_CHAMBER"
