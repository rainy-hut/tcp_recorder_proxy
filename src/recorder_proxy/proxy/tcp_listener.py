from __future__ import annotations

import asyncio

from recorder_proxy.config.models import RouteConfig
from recorder_proxy.proxy.connection_registry import ConnectionRegistry
from recorder_proxy.proxy.forwarder import Forwarder
from recorder_proxy.proxy.tcp_session import TcpSessionHandler


class TcpListener:
    def __init__(self, route: RouteConfig, session_id: str, registry: ConnectionRegistry, forwarder: Forwarder) -> None:
        self.route = route
        self.handler = TcpSessionHandler(route, session_id, registry, forwarder)
        self.server: asyncio.AbstractServer | None = None

    async def start(self) -> None:
        self.server = await asyncio.start_server(self.handler.handle, self.route.listen_ip, self.route.listen_port)

    async def stop(self) -> None:
        if self.server is None:
            return
        self.server.close()
        await self.server.wait_closed()
