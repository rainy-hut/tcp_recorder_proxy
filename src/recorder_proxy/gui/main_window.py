from __future__ import annotations

import asyncio
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QBrush, QDesktopServices, QIcon
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from qasync import asyncSlot

from recorder_proxy.app.app_context import AppContext
from recorder_proxy.config.models import DeviceConfig, ProtocolMode, RouteConfig
from recorder_proxy.config.route_repository import save_devices
from recorder_proxy.gui.resources import app_icon_path
from recorder_proxy.gui.theme import APP_STYLE
from recorder_proxy.proxy.proxy_service import ProxyService


class MainWindow(QMainWindow):
    ROUTE_HEADERS = ["序号", "设备ID", "设备类型", "协议模式", "路由ID", "监听地址", "真实硬件地址", "状态", "操作"]
    DEVICE_TYPE_SUGGESTIONS = [
        "BBU",
        "SIGNAL_GENERATOR",
        "SPECTRUM_ANALYZER",
        "POWER_METER",
        "CUSTOM_TCP",
        "OSCILLOSCOPE",
        "TEMPERATURE_CHAMBER",
    ]

    def __init__(self, context: AppContext) -> None:
        super().__init__()
        self.context = context
        self.setWindowTitle("TCP 命令码流录制代理器")
        self.setWindowIcon(QIcon(str(app_icon_path())))
        self.resize(1280, 800)
        self.setMinimumSize(960, 560)
        self.setStyleSheet(APP_STYLE)
        self.start_button = QPushButton("开始监听")
        self.start_button.setObjectName("PrimaryButton")
        self.stop_button = QPushButton("停止并导出")
        self.stop_button.setObjectName("SecondaryButton")
        self.stop_button.setEnabled(False)
        self.raw_only_button = QPushButton("仅原始码流")
        self.raw_only_button.setObjectName("SecondaryButton")
        self.raw_only_button.setCheckable(True)
        self.raw_parse_button = QPushButton("原始码流 + 解析")
        self.raw_parse_button.setObjectName("PrimaryButton")
        self.raw_parse_button.setCheckable(True)
        self.raw_parse_button.setChecked(True)
        self.recording_mode_group = QButtonGroup(self)
        self.recording_mode_group.setExclusive(True)
        self.recording_mode_group.addButton(self.raw_parse_button, 1)
        self.recording_mode_group.addButton(self.raw_only_button, 0)
        self.status_label = QLabel("未启动")
        self.warning_label = QLabel("")
        self.warning_label.setObjectName("Warning")
        self.queue_label = QLabel("")
        self.queue_label.setObjectName("SubtleText")
        self.session_label = QLabel("")
        self.session_label.setObjectName("SubtleText")
        self.route_save_status = QLabel("已保存")
        self.route_save_status.setObjectName("SavedBadge")
        self.routes_dirty = False
        self.routes_table = QTableWidget(0, len(self.ROUTE_HEADERS))
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self._build_ui()
        self.start_button.clicked.connect(self._start_clicked)
        self.stop_button.clicked.connect(self._stop_clicked)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._refresh_status)
        self.timer.start(500)

    def _build_ui(self) -> None:
        workspace = QWidget()
        root_layout = QHBoxLayout(workspace)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(16, 18, 16, 16)
        sidebar_layout.setSpacing(14)
        title = QLabel("码流录制代理")
        title.setObjectName("SidebarTitle")
        sidebar_layout.addWidget(title)
        self.nav = QListWidget()
        self.stack = QStackedWidget()
        pages = [
            ("运行控制", self._dashboard_page()),
            ("路由配置", self._routes_page()),
            ("原始日志", self._raw_page()),
            ("日志", self._log_page()),
        ]
        for page_title, page in pages:
            self.nav.addItem(page_title)
            self.stack.addWidget(page)
        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.nav.setCurrentRow(0)
        sidebar_layout.addWidget(self.nav, 1)
        root_layout.addWidget(sidebar)
        root_layout.addWidget(self.stack, 1)
        self.setCentralWidget(workspace)

    def _dashboard_page(self) -> QWidget:
        page = QFrame()
        page.setObjectName("Page")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)
        title = QLabel("运行控制")
        title.setObjectName("HeroTitle")
        hint = QLabel("启动透明 TCP 代理后，所有收发 bytes 会先原样转发，再进入异步原始录制和协议解析。")
        hint.setObjectName("SubtleText")
        layout.addWidget(title)
        layout.addWidget(hint)

        panel = QFrame()
        panel.setObjectName("Panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(20, 16, 20, 16)
        panel_layout.setSpacing(12)
        mode_row = QHBoxLayout()
        mode_label = QLabel("录制模式")
        mode_label.setObjectName("FieldName")
        mode_row.addWidget(mode_label)
        mode_row.addWidget(self.raw_parse_button)
        mode_row.addWidget(self.raw_only_button)
        mode_row.addStretch(1)
        panel_layout.addLayout(mode_row)
        controls = QHBoxLayout()
        controls.addWidget(self.start_button)
        controls.addWidget(self.stop_button)
        open_session = QPushButton("打开会话目录")
        open_session.setObjectName("SecondaryButton")
        open_session.clicked.connect(self._open_session_dir)
        controls.addWidget(open_session)
        controls.addStretch(1)
        controls.addWidget(self.status_label)
        panel_layout.addLayout(controls)
        panel_layout.addWidget(self.warning_label)
        panel_layout.addWidget(self.queue_label)
        panel_layout.addWidget(self.session_label)
        layout.addWidget(panel)
        layout.addStretch(1)
        return page

    def _routes_page(self) -> QWidget:
        page = QFrame()
        page.setObjectName("Page")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)
        title = QLabel("路由配置")
        title.setObjectName("HeroTitle")
        hint = QLabel("维护组件访问地址与真实硬件地址。BBU 设备可配置多个监听端口，每个端口独立监听。")
        hint.setObjectName("SubtleText")
        layout.addWidget(title)
        layout.addWidget(hint)

        card = QFrame()
        card.setObjectName("ConfigCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(12)
        header = QHBoxLayout()
        card_title = QLabel("TCP 路由映射")
        card_title.setObjectName("ConfigCardTitle")
        header.addWidget(card_title)
        header.addWidget(self.route_save_status)
        header.addStretch(1)
        add = QPushButton("新增路由")
        add.setObjectName("SecondaryButton")
        add.clicked.connect(self._add_route_row)
        delete = QPushButton("删除选中")
        delete.setObjectName("DangerButton")
        delete.clicked.connect(self._delete_selected_route)
        save = QPushButton("保存配置")
        save.setObjectName("PrimaryButton")
        save.clicked.connect(self._save_routes)
        header.addWidget(add)
        header.addWidget(delete)
        header.addWidget(save)
        card_layout.addLayout(header)
        note = QLabel("监听运行中不可修改路由；停止后编辑并保存，会回写 config/routes.toml。")
        note.setObjectName("MutedText")
        card_layout.addWidget(note)

        self.routes_table.setHorizontalHeaderLabels(self.ROUTE_HEADERS)
        self.routes_table.setAlternatingRowColors(True)
        self.routes_table.itemChanged.connect(self._mark_routes_dirty)
        card_layout.addWidget(self.routes_table, 1)
        layout.addWidget(card, 1)
        self._load_route_rows()
        return page

    def _raw_page(self) -> QWidget:
        page = QFrame()
        page.setObjectName("Page")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)
        title = QLabel("原始日志")
        title.setObjectName("HeroTitle")
        layout.addWidget(title)
        hint = QLabel("原始 .bin、events.jsonl、parsed_messages.jsonl 与 manifest.json 将按设备独立保存。")
        hint.setObjectName("SubtleText")
        layout.addWidget(hint)
        panel = QFrame()
        panel.setObjectName("Panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(20, 16, 20, 16)
        open_raw = QPushButton("打开 raw 目录")
        open_raw.setObjectName("SecondaryButton")
        open_raw.clicked.connect(self._open_raw_dir)
        panel_layout.addWidget(open_raw)
        layout.addWidget(panel)
        layout.addStretch(1)
        return page

    def _log_page(self) -> QWidget:
        page = QFrame()
        page.setObjectName("Page")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)
        title = QLabel("日志")
        title.setObjectName("HeroTitle")
        layout.addWidget(title)
        layout.addWidget(self.log, 1)
        return page

    def _load_route_rows(self) -> None:
        self.routes_table.blockSignals(True)
        self.routes_table.setRowCount(0)
        for route in self.context.config.routes:
            self._add_route_row(route, mark_dirty=False)
        self.routes_table.blockSignals(False)
        self._set_routes_dirty(False)

    def _add_route_row(self, route: RouteConfig | None = None, mark_dirty: bool = True) -> None:
        if self.context.proxy_service.running:
            QMessageBox.information(self, "路由运行中", "请先停止监听，再修改路由配置。")
            return
        row = self.routes_table.rowCount()
        route = route or RouteConfig(
            route_id=f"Route_{row + 1:02d}",
            device_id=f"Device_{row + 1:02d}",
            device_type="CUSTOM_TCP",
            protocol_mode=ProtocolMode.TEXT_INSTRUMENT,
            listen_ip="127.0.0.1",
            listen_port=15026 + row,
            hardware_ip="192.168.1.20",
            hardware_port=5025,
        )
        self.routes_table.insertRow(row)
        index = QTableWidgetItem(str(row + 1))
        index.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        self.routes_table.setItem(row, 0, index)
        self.routes_table.setItem(row, 1, QTableWidgetItem(route.device_id))
        self._set_combo(row, 2, self.DEVICE_TYPE_SUGGESTIONS, str(route.device_type), editable=True)
        self._set_combo(row, 3, [item.value for item in ProtocolMode], route.protocol_mode.value)
        self.routes_table.setItem(row, 4, QTableWidgetItem(route.route_id))
        self.routes_table.setItem(row, 5, QTableWidgetItem(f"{route.listen_ip}:{route.listen_port}"))
        self.routes_table.setItem(row, 6, QTableWidgetItem(f"{route.hardware_ip}:{route.hardware_port}"))
        status = QTableWidgetItem("待启动")
        status.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        self.routes_table.setItem(row, 7, status)
        self.routes_table.setCellWidget(row, 8, self._route_actions(row))
        self._apply_route_column_widths()
        if mark_dirty:
            self._set_routes_dirty(True)

    def _set_combo(self, row: int, col: int, values: list[str], current: str, editable: bool = False) -> None:
        combo = QComboBox()
        combo.setEditable(editable)
        combo.addItems(values)
        combo.setCurrentText(current)
        combo.currentTextChanged.connect(lambda _text: self._mark_routes_dirty())
        self.routes_table.setCellWidget(row, col, combo)

    def _route_actions(self, row: int) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        delete = QPushButton("删除")
        delete.setObjectName("DangerButton")
        delete.clicked.connect(lambda _checked=False, r=row: self._delete_route_row(r))
        layout.addWidget(delete)
        return widget

    def _delete_selected_route(self) -> None:
        self._delete_route_row(self.routes_table.currentRow())

    def _delete_route_row(self, row: int) -> None:
        if self.context.proxy_service.running:
            QMessageBox.information(self, "路由运行中", "请先停止监听，再修改路由配置。")
            return
        if row < 0 or row >= self.routes_table.rowCount():
            QMessageBox.information(self, "删除路由", "请先选择一条路由。")
            return
        route_name = self._route_text(row, 4) or f"第 {row + 1} 行"
        if QMessageBox.question(self, "确认删除", f"确认删除路由 {route_name}？") != QMessageBox.Yes:
            return
        self.routes_table.removeRow(row)
        self._renumber_route_rows()
        self._set_routes_dirty(True)

    def _save_routes(self) -> None:
        if self.context.proxy_service.running:
            QMessageBox.information(self, "路由运行中", "请先停止监听，再保存路由配置。")
            return
        try:
            devices = self._collect_route_devices()
            save_devices(self.context.config.settings.project_root, devices)
            self.context.config.devices = devices
            self.context.proxy_service = ProxyService(self.context.config)
            self._set_routes_dirty(False)
            QMessageBox.information(self, "保存成功", "路由配置已保存。")
            self._append_log("路由配置已保存，并刷新代理服务配置。")
        except Exception as exc:
            QMessageBox.warning(self, "配置错误", str(exc))

    def _collect_route_devices(self) -> list[DeviceConfig]:
        by_device: dict[str, dict[str, object]] = {}
        seen_routes: set[str] = set()
        seen_listeners: set[tuple[str, int]] = set()
        for row in range(self.routes_table.rowCount()):
            device_id = self._route_text(row, 1) or f"Device_{row + 1:02d}"
            device_type = self._combo_text(row, 2).strip()
            protocol_mode = ProtocolMode(self._combo_text(row, 3))
            route_id = self._route_text(row, 4) or f"{device_id}_{row + 1:02d}"
            listen_ip, listen_port = self._parse_address(self._route_text(row, 5), "127.0.0.1", 15026 + row)
            hardware_ip, hardware_port = self._parse_address(self._route_text(row, 6), "", 5025)
            if not device_type:
                raise ValueError(f"第 {row + 1} 行缺少设备类型")
            if not hardware_ip:
                raise ValueError(f"{route_id} 缺少真实硬件地址")
            if route_id in seen_routes:
                raise ValueError(f"路由 ID 重复: {route_id}")
            if (listen_ip, listen_port) in seen_listeners:
                raise ValueError(f"监听地址重复: {listen_ip}:{listen_port}")
            seen_routes.add(route_id)
            seen_listeners.add((listen_ip, listen_port))
            entry = by_device.setdefault(
                device_id,
                {"device_type": device_type, "protocol_mode": protocol_mode, "routes": []},
            )
            if entry["device_type"] != device_type or entry["protocol_mode"] != protocol_mode:
                raise ValueError(f"同一设备 {device_id} 的设备类型和协议模式必须一致")
            entry["routes"].append(
                RouteConfig(
                    route_id=route_id,
                    device_id=device_id,
                    device_type=device_type,
                    protocol_mode=protocol_mode,
                    listen_ip=listen_ip,
                    listen_port=listen_port,
                    hardware_ip=hardware_ip,
                    hardware_port=hardware_port,
                )
            )
        if not by_device:
            raise ValueError("至少需要保留一条路由")
        return [
            DeviceConfig(
                device_id=device_id,
                device_type=entry["device_type"],  # type: ignore[arg-type]
                protocol_mode=entry["protocol_mode"],  # type: ignore[arg-type]
                label=device_id,
                routes=entry["routes"],  # type: ignore[arg-type]
            )
            for device_id, entry in by_device.items()
        ]

    def _mark_routes_dirty(self) -> None:
        self._set_routes_dirty(True)

    def _set_routes_dirty(self, dirty: bool) -> None:
        self.routes_dirty = dirty
        self.route_save_status.setText("有未保存修改" if dirty else "已保存")
        self.route_save_status.setObjectName("DirtyBadge" if dirty else "SavedBadge")
        self.route_save_status.style().unpolish(self.route_save_status)
        self.route_save_status.style().polish(self.route_save_status)
        if dirty:
            for row in range(self.routes_table.rowCount()):
                item = self.routes_table.item(row, 0)
                if item and not item.text().startswith("● "):
                    item.setText(f"● {row + 1}")
                    item.setBackground(Qt.GlobalColor.yellow)
        else:
            self._renumber_route_rows()

    def _renumber_route_rows(self) -> None:
        self.routes_table.blockSignals(True)
        for row in range(self.routes_table.rowCount()):
            item = self.routes_table.item(row, 0)
            if item:
                item.setText(str(row + 1))
                item.setBackground(QBrush())
            self.routes_table.setCellWidget(row, 8, self._route_actions(row))
        self.routes_table.blockSignals(False)

    def _apply_route_column_widths(self) -> None:
        widths = [56, 180, 150, 170, 210, 190, 210, 90, 90]
        for col, width in enumerate(widths):
            self.routes_table.setColumnWidth(col, width)

    def _route_text(self, row: int, col: int) -> str:
        item = self.routes_table.item(row, col)
        return item.text().replace("●", "").strip() if item else ""

    def _combo_text(self, row: int, col: int) -> str:
        widget = self.routes_table.cellWidget(row, col)
        if isinstance(widget, QComboBox):
            return widget.currentText()
        return ""

    def _parse_address(self, value: str, default_host: str, default_port: int) -> tuple[str, int]:
        if not value:
            return default_host, default_port
        if ":" not in value:
            return value.strip(), default_port
        host, port = value.rsplit(":", 1)
        return host.strip(), int(port.strip())

    @asyncSlot()
    async def _start_clicked(self) -> None:
        try:
            parse_enabled = self.recording_mode_group.checkedId() == 1
            self.context.proxy_service.set_parse_enabled(parse_enabled)
            await self.context.proxy_service.start()
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self._set_recording_mode_controls_enabled(False)
            self.status_label.setText("监听中")
            mode_text = "原始码流 + 解析" if parse_enabled else "仅原始码流"
            self._append_log(f"代理已启动，录制模式：{mode_text}。")
            self._mark_routes("监听中")
        except Exception as exc:
            QMessageBox.critical(self, "启动失败", repr(exc))
            self._append_log(f"启动失败: {exc!r}")

    @asyncSlot()
    async def _stop_clicked(self) -> None:
        self.stop_button.setEnabled(False)
        self._append_log("正在停止监听并等待队列落盘...")
        try:
            await self.context.proxy_service.stop()
            self.start_button.setEnabled(True)
            self._set_recording_mode_controls_enabled(True)
            self.status_label.setText("已停止")
            self._mark_routes("已停止")
            self._append_log("停止完成，TOML 已按设备导出。")
        except Exception as exc:
            QMessageBox.critical(self, "停止失败", repr(exc))
            self._append_log(f"停止失败: {exc!r}")

    def _refresh_status(self) -> None:
        service = self.context.proxy_service
        raw_size = service.queues.raw.qsize()
        parse_size = service.queues.parse.qsize()
        stats = service.queues.stats
        self.queue_label.setText(
            f"Raw 队列: {raw_size}  Parse 队列: {parse_size}  "
            f"Raw 丢失: {stats.raw_dropped}  Parse 丢失: {stats.parse_dropped}"
        )
        if stats.raw_dropped:
            self.warning_label.setText("严重告警：原始录制队列发生丢失，透明转发仍继续。")
        elif stats.parse_dropped:
            self.warning_label.setText("告警：解析队列发生丢失，原始日志仍优先保存。")
        else:
            self.warning_label.setText("")
        if service.session_manager.session is not None:
            self.session_label.setText(f"当前会话: {service.session.paths.root}")

    def _mark_routes(self, text: str) -> None:
        for row in range(self.routes_table.rowCount()):
            item = self.routes_table.item(row, 7)
            if item is None:
                item = QTableWidgetItem(text)
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                self.routes_table.setItem(row, 7, item)
            item.setText(text)

    def _set_recording_mode_controls_enabled(self, enabled: bool) -> None:
        self.raw_only_button.setEnabled(enabled)
        self.raw_parse_button.setEnabled(enabled)

    def _append_log(self, text: str) -> None:
        self.log.append(text)

    def _open_session_dir(self) -> None:
        session = self.context.proxy_service.session_manager.session
        path = session.paths.root if session else self.context.config.settings.recordings_dir
        self._open_path(path)

    def _open_raw_dir(self) -> None:
        session = self.context.proxy_service.session_manager.session
        path = session.paths.raw if session else self.context.config.settings.recordings_dir
        self._open_path(path)

    def _open_path(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def closeEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        if self.context.proxy_service.running:
            QMessageBox.warning(self, "仍在运行", "请先点击“停止并导出”。")
            event.ignore()
            return
        if self.routes_dirty:
            result = QMessageBox.question(self, "未保存路由", "路由配置有未保存修改，确认退出？")
            if result != QMessageBox.Yes:
                event.ignore()
                return
        event.accept()
