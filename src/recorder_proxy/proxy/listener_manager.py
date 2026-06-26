from __future__ import annotations

import asyncio

from recorder_proxy.config.models import RouteConfig
from recorder_proxy.proxy.connection_registry import ConnectionRegistry
from recorder_proxy.proxy.forwarder import Forwarder
from recorder_proxy.proxy.tcp_listener import TcpListener


class ListenerManager:
    def __init__(self, routes: list[RouteConfig], session_id: str, registry: ConnectionRegistry, forwarder: Forwarder) -> None:
        self.listeners = [TcpListener(route, session_id, registry, forwarder) for route in routes]

    async def start(self) -> None:
        await asyncio.gather(*(listener.start() for listener in self.listeners))

    async def stop(self) -> None:
        await asyncio.gather(*(listener.stop() for listener in self.listeners), return_exceptions=True)
