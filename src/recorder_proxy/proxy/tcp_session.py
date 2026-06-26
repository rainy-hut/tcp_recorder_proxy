from __future__ import annotations

import asyncio
from contextlib import suppress

from recorder_proxy.config.models import RouteConfig
from recorder_proxy.proxy.connection_registry import ConnectionRegistry
from recorder_proxy.proxy.forwarder import Forwarder
from recorder_proxy.recording.models import ConnectionInfo


class TcpSessionHandler:
    def __init__(self, route: RouteConfig, session_id: str, registry: ConnectionRegistry, forwarder: Forwarder) -> None:
        self.route = route
        self.session_id = session_id
        self.registry = registry
        self.forwarder = forwarder

    async def handle(self, client_reader: asyncio.StreamReader, client_writer: asyncio.StreamWriter) -> None:
        hardware_reader: asyncio.StreamReader | None = None
        hardware_writer: asyncio.StreamWriter | None = None
        try:
            hardware_reader, hardware_writer = await asyncio.open_connection(self.route.hardware_ip, self.route.hardware_port)
            client_host, client_port = client_writer.get_extra_info("peername")[:2]
            connection = ConnectionInfo(
                session_id=self.session_id,
                connection_id=self.registry.next_id(),
                device_id=self.route.device_id,
                device_type=self.route.device_type,
                route_id=self.route.route_id,
                listen_ip=self.route.listen_ip,
                listen_port=self.route.listen_port,
                client_ip=str(client_host),
                client_port=int(client_port),
                hardware_ip=self.route.hardware_ip,
                hardware_port=self.route.hardware_port,
            )
            tasks = [
                asyncio.create_task(self.forwarder.pipe(client_reader, hardware_writer, connection, "client_to_hardware")),
                asyncio.create_task(self.forwarder.pipe(hardware_reader, client_writer, connection, "hardware_to_client")),
            ]
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in pending:
                task.cancel()
            for task in done:
                with suppress(asyncio.CancelledError):
                    await task
            for task in pending:
                with suppress(asyncio.CancelledError):
                    await task
        finally:
            client_writer.close()
            with suppress(OSError):
                await client_writer.wait_closed()
            if hardware_writer is not None:
                hardware_writer.close()
                with suppress(OSError):
                    await hardware_writer.wait_closed()
