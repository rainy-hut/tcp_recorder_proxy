from __future__ import annotations

from pathlib import Path

from recorder_proxy.config.models import AppConfig
from recorder_proxy.config.route_repository import load_devices
from recorder_proxy.config.settings_repository import load_settings


def load_app_config(project_root: Path) -> AppConfig:
    return AppConfig(settings=load_settings(project_root), devices=load_devices(project_root))
