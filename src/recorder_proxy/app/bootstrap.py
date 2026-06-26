from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from qasync import QEventLoop

from recorder_proxy.app.app_context import AppContext
from recorder_proxy.config.device_repository import load_app_config
from recorder_proxy.gui.main_window import MainWindow
from recorder_proxy.gui.resources import app_icon_path
from recorder_proxy.proxy.proxy_service import ProxyService


def main() -> int:
    project_root = Path(__file__).resolve().parents[3]
    app_config = load_app_config(project_root)
    qt_app = QApplication(sys.argv)
    icon = QIcon(str(app_icon_path()))
    qt_app.setWindowIcon(icon)
    loop = QEventLoop(qt_app)
    asyncio.set_event_loop(loop)
    context = AppContext(config=app_config, proxy_service=ProxyService(app_config))
    window = MainWindow(context)
    window.setWindowIcon(icon)
    window.show()
    with loop:
        return loop.run_forever() or 0
