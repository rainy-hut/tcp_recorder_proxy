from __future__ import annotations

from pathlib import Path

from recorder_proxy.config.models import AppConfig
from recorder_proxy.proxy.connection_registry import ConnectionRegistry
from recorder_proxy.proxy.forwarder import Forwarder
from recorder_proxy.proxy.listener_manager import ListenerManager
from recorder_proxy.recording.event_processor import EventProcessor
from recorder_proxy.recording.event_queue import RecordingQueues
from recorder_proxy.recording.exporters.bbu_binary_exporter import BbuBinaryExporter
from recorder_proxy.recording.exporters.bbu_mml_exporter import BbuMmlExporter
from recorder_proxy.recording.exporters.export_validator import ExportValidator
from recorder_proxy.recording.exporters.text_instrument_exporter import TextInstrumentExporter
from recorder_proxy.recording.session_manager import RecordingSession, SessionManager


class ProxyService:
    def __init__(self, app_config: AppConfig) -> None:
        self.app_config = app_config
        self.session_manager = SessionManager(app_config.settings)
        self.queues = RecordingQueues(app_config.settings.raw_queue_size, app_config.settings.parse_queue_size)
        self.registry = ConnectionRegistry()
        self.forwarder = Forwarder(self.queues, app_config.settings.chunk_size)
        self.processor: EventProcessor | None = None
        self.listener_manager: ListenerManager | None = None
        self.parse_enabled = True
        self.running = False

    @property
    def session(self) -> RecordingSession:
        return self.session_manager.require()

    async def start(self) -> None:
        if self.running:
            return
        session = self.session_manager.start()
        session.recording_mode = "RAW_AND_PARSE" if self.parse_enabled else "RAW_ONLY"
        self.processor = EventProcessor(self.app_config, session, self.queues, parse_enabled=self.parse_enabled)
        self.processor.start()
        self.listener_manager = ListenerManager(self.app_config.routes, session.session_id, self.registry, self.forwarder)
        await self.listener_manager.start()
        self.running = True

    def set_parse_enabled(self, enabled: bool) -> None:
        if self.running:
            raise RuntimeError("录制运行中不能切换解析模式")
        self.parse_enabled = enabled

    async def stop(self) -> None:
        if not self.running:
            return
        if self.listener_manager is not None:
            await self.listener_manager.stop()
        if self.processor is not None:
            await self.processor.stop()
        self.export_all()
        self.session_manager.finish(self.app_config.routes)
        if self.processor is not None:
            self.processor.close_manifests()
        self.running = False

    def export_all(self) -> list[Path]:
        session = self.session
        paths: list[Path] = []
        for device in self.app_config.devices:
            exporters = (
                [BbuMmlExporter(), BbuBinaryExporter()]
                if device.device_type == "BBU"
                else [TextInstrumentExporter()]
            )
            for exporter in exporters:
                path = exporter.export(session, device.device_id)
                if path is not None:
                    ExportValidator().validate_toml(path)
                    paths.append(path)
                    session.generated_toml_files.append(str(path.relative_to(session.paths.root)))
        return paths
