from __future__ import annotations

from dataclasses import dataclass

from recorder_proxy.config.models import AppConfig
from recorder_proxy.proxy.proxy_service import ProxyService


@dataclass
class AppContext:
    config: AppConfig
    proxy_service: ProxyService
