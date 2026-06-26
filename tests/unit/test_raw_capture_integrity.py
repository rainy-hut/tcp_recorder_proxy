import asyncio
import json
from pathlib import Path
import sqlite3

from recorder_proxy.config.models import AppConfig, AppSettings, DeviceConfig, DeviceType, ProtocolMode, RouteConfig
from recorder_proxy.recording.event_processor import EventProcessor
from recorder_proxy.recording.event_queue import RecordingQueues
from recorder_proxy.recording.models import ConnectionInfo, RawCaptureEvent
from recorder_proxy.recording.raw_reparser import RawLogReparser
from recorder_proxy.recording.session_manager import SessionManager
from recorder_proxy.utils.hex_utils import sha256_hex
from recorder_proxy.utils.time_utils import monotonic_ns, timestamp_ns, utc_now_iso


def test_raw_capture_writes_exact_bytes_and_index(tmp_path: Path):
    async def run() -> None:
        route = RouteConfig(
            route_id="BBU_5026",
            device_id="BBU_01",
            device_type="BBU",
            protocol_mode=ProtocolMode.BBU_AUTO,
            listen_ip="127.0.0.1",
            listen_port=5026,
            hardware_ip="192.0.2.1",
            hardware_port=5026,
        )
        config = AppConfig(
            settings=AppSettings(project_root=tmp_path, recordings_dir=tmp_path / "recordings"),
            devices=[DeviceConfig("BBU_01", "BBU", ProtocolMode.BBU_AUTO, "BBU", [route])],
        )
        session = SessionManager(config.settings).start()
        queues = RecordingQueues(10, 10)
        processor = EventProcessor(config, session, queues)
        processor.start()
        conn = ConnectionInfo(
            session_id=session.session_id,
            connection_id="conn_000001",
            device_id="BBU_01",
            device_type="BBU",
            route_id="BBU_5026",
            listen_ip="127.0.0.1",
            listen_port=5026,
            client_ip="127.0.0.1",
            client_port=60000,
            hardware_ip="192.0.2.1",
            hardware_port=5026,
        )
        payload = b"LST SOFTWARE:;\r\n"
        queues.offer_raw(
            RawCaptureEvent(
                event_id="evt_1",
                connection=conn,
                timestamp_utc=utc_now_iso(),
                timestamp_ns=timestamp_ns(),
                monotonic_ns=monotonic_ns(),
                direction="client_to_hardware",
                chunk_sequence=1,
                data=payload,
            )
        )
        await processor.stop()
        session.ended_at = utc_now_iso()
        processor.close_manifests()

        raw_file = session.paths.raw / "BBU_01" / "connections" / "conn_000001_client_to_hardware.bin"
        assert raw_file.read_bytes() == payload
        event = json.loads((session.paths.raw / "BBU_01" / "events.jsonl").read_text(encoding="utf-8").splitlines()[0])
        assert event["byte_offset"] == 0
        assert event["byte_length"] == len(payload)
        assert event["sha256"] == sha256_hex(payload)
        assert raw_file.read_bytes()[event["byte_offset"] : event["byte_offset"] + event["byte_length"]] == payload

    asyncio.run(run())


def test_parse_enabled_writes_parsed_messages_on_stop(tmp_path: Path):
    async def run() -> None:
        route = RouteConfig(
            route_id="BBU_5026",
            device_id="BBU_01",
            device_type="BBU",
            protocol_mode=ProtocolMode.BBU_AUTO,
            listen_ip="127.0.0.1",
            listen_port=5026,
            hardware_ip="192.0.2.1",
            hardware_port=5026,
        )
        config = AppConfig(
            settings=AppSettings(project_root=tmp_path, recordings_dir=tmp_path / "recordings"),
            devices=[DeviceConfig("BBU_01", "BBU", ProtocolMode.BBU_AUTO, "BBU", [route])],
        )
        session = SessionManager(config.settings).start()
        session.recording_mode = "RAW_AND_PARSE"
        queues = RecordingQueues(10, 10)
        processor = EventProcessor(config, session, queues, parse_enabled=True)
        processor.start()
        conn = ConnectionInfo(
            session_id=session.session_id,
            connection_id="conn_000001",
            device_id="BBU_01",
            device_type="BBU",
            route_id="BBU_5026",
            listen_ip="127.0.0.1",
            listen_port=5026,
            client_ip="127.0.0.1",
            client_port=60000,
            hardware_ip="192.0.2.1",
            hardware_port=5026,
        )
        queues.offer_raw(
            RawCaptureEvent(
                event_id="evt_1",
                connection=conn,
                timestamp_utc=utc_now_iso(),
                timestamp_ns=timestamp_ns(),
                monotonic_ns=monotonic_ns(),
                direction="client_to_hardware",
                chunk_sequence=1,
                data=b"LST SOFTWARE:;\r\n",
            )
        )
        await processor.stop()

        parsed_path = session.paths.raw / "BBU_01" / "parsed_messages.jsonl"
        parsed_lines = parsed_path.read_text(encoding="utf-8").splitlines()
        assert len(parsed_lines) == 1
        assert json.loads(parsed_lines[0])["classification"] == "BBU_MML_PLAIN"
        assert session.parsed_message_count == 1

    asyncio.run(run())


def test_raw_only_mode_does_not_parse(tmp_path: Path):
    async def run() -> None:
        route = RouteConfig(
            route_id="BBU_5026",
            device_id="BBU_01",
            device_type="BBU",
            protocol_mode=ProtocolMode.BBU_AUTO,
            listen_ip="127.0.0.1",
            listen_port=5026,
            hardware_ip="192.0.2.1",
            hardware_port=5026,
        )
        config = AppConfig(
            settings=AppSettings(project_root=tmp_path, recordings_dir=tmp_path / "recordings"),
            devices=[DeviceConfig("BBU_01", "BBU", ProtocolMode.BBU_AUTO, "BBU", [route])],
        )
        session = SessionManager(config.settings).start()
        session.recording_mode = "RAW_ONLY"
        queues = RecordingQueues(10, 10)
        processor = EventProcessor(config, session, queues, parse_enabled=False)
        processor.start()
        conn = ConnectionInfo(
            session_id=session.session_id,
            connection_id="conn_000001",
            device_id="BBU_01",
            device_type="BBU",
            route_id="BBU_5026",
            listen_ip="127.0.0.1",
            listen_port=5026,
            client_ip="127.0.0.1",
            client_port=60000,
            hardware_ip="192.0.2.1",
            hardware_port=5026,
        )
        queues.offer_raw(
            RawCaptureEvent(
                event_id="evt_1",
                connection=conn,
                timestamp_utc=utc_now_iso(),
                timestamp_ns=timestamp_ns(),
                monotonic_ns=monotonic_ns(),
                direction="client_to_hardware",
                chunk_sequence=1,
                data=b"LST SOFTWARE:;\r\n",
            )
        )
        await processor.stop()
        session.ended_at = utc_now_iso()
        processor.close_manifests()

        raw_dir = session.paths.raw / "BBU_01"
        event = json.loads((raw_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()[0])
        assert event["parser_status_at_capture"] == "DISABLED"
        assert (raw_dir / "parsed_messages.jsonl").read_text(encoding="utf-8") == ""
        manifest = json.loads((raw_dir / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["recording_mode"] == "RAW_ONLY"

    asyncio.run(run())


def test_raw_only_session_can_be_reparsed(tmp_path: Path):
    async def run() -> None:
        route = RouteConfig(
            route_id="BBU_5026",
            device_id="BBU_01",
            device_type="BBU",
            protocol_mode=ProtocolMode.BBU_AUTO,
            listen_ip="127.0.0.1",
            listen_port=5026,
            hardware_ip="192.0.2.1",
            hardware_port=5026,
        )
        config = AppConfig(
            settings=AppSettings(project_root=tmp_path, recordings_dir=tmp_path / "recordings"),
            devices=[DeviceConfig("BBU_01", "BBU", ProtocolMode.BBU_AUTO, "BBU", [route])],
        )
        session = SessionManager(config.settings).start()
        session.recording_mode = "RAW_ONLY"
        queues = RecordingQueues(10, 10)
        processor = EventProcessor(config, session, queues, parse_enabled=False)
        processor.start()
        conn = ConnectionInfo(
            session_id=session.session_id,
            connection_id="conn_000001",
            device_id="BBU_01",
            device_type="BBU",
            route_id="BBU_5026",
            listen_ip="127.0.0.1",
            listen_port=5026,
            client_ip="127.0.0.1",
            client_port=60000,
            hardware_ip="192.0.2.1",
            hardware_port=5026,
        )
        queues.offer_raw(
            RawCaptureEvent(
                event_id="evt_1",
                connection=conn,
                timestamp_utc=utc_now_iso(),
                timestamp_ns=timestamp_ns(),
                monotonic_ns=monotonic_ns(),
                direction="client_to_hardware",
                chunk_sequence=1,
                data=b"LST SOFTWARE:;\r\n",
            )
        )
        await processor.stop()
        session.ended_at = utc_now_iso()
        processor.close_manifests()

        result = RawLogReparser(config, session).reparse()

        assert result.event_count == 1
        assert result.message_count == 1
        parsed_lines = (session.paths.raw / "BBU_01" / "parsed_messages.jsonl").read_text(encoding="utf-8").splitlines()
        assert json.loads(parsed_lines[0])["classification"] == "BBU_MML_PLAIN"
        conn_sql = sqlite3.connect(session.paths.sqlite_path)
        count = conn_sql.execute("SELECT COUNT(*) FROM parsed_messages").fetchone()[0]
        conn_sql.close()
        assert count == 1

    asyncio.run(run())
