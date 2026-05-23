"""
صفحهٔ خانهٔ کاربر عادی: اتصال دستگاه‌ها، ورودی اولویت‌های دستی، اسکن و چاپ.
"""

from __future__ import annotations

import json
from typing import Any

from PySide6.QtCore import QByteArray, Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtNetwork import QAbstractSocket, QTcpSocket
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from printers.A520i import send_to_printer
from user_store import (
    PRINTER_TYPE_A520I,
    _normalize_printer_type,
    get_device_connections_by_user,
    get_devices_by_user,
    get_product_scan_detail_fields_by_user,
    get_product_structure_by_user,
    get_product_structures,
    get_products_by_user,
    get_scan_results_limit,
    resolve_print_priorities,
)

try:
    from PySide6.QtSerialPort import QSerialPort
except ImportError:  # pragma: no cover
    QSerialPort = None


def _nz_int(raw: object) -> int:
    try:
        return max(0, int(str(raw).strip()))
    except (TypeError, ValueError):
        return 0


_START_BUTTON_LABEL = "▶  شروع"
_STOP_BUTTON_LABEL = "■  توقف"
_CONNECTING_BUTTON_LABEL = "⏳  در حال اتصال…"


class _SendAllAdapter:
    """Shim so A520i.send_to_printer can write via QTcpSocket / QSerialPort."""

    def __init__(self, link: QTcpSocket | Any) -> None:
        self._link = link

    def sendall(self, data: bytes) -> None:
        if not data:
            return

        offset = 0
        while offset < len(data):
            chunk = data[offset:]
            if isinstance(self._link, QTcpSocket):
                if self._link.state() != QAbstractSocket.SocketState.ConnectedState:
                    raise OSError(self._link.errorString() or "QTcpSocket is not connected")
                written = self._link.write(chunk)
            elif QSerialPort is not None and isinstance(self._link, QSerialPort):
                if not self._link.isOpen():
                    raise OSError("QSerialPort is not open")
                written = self._link.write(chunk)
            else:
                raise OSError("Unsupported printer link type")

            if written < 0:
                if isinstance(self._link, QTcpSocket):
                    raise OSError(self._link.errorString() or "QTcpSocket write failed")
                raise OSError("QSerialPort write failed")
            if written == 0:
                # Buffer full: wait briefly, then retry (do not abort on slow printers).
                self._link.waitForBytesWritten(10000)
                continue
            offset += written

        self._link.flush()
        # Best-effort drain; many printers never ACK quickly over TCP.
        pending = int(self._link.bytesToWrite()) if hasattr(self._link, "bytesToWrite") else 0
        attempts = 0
        while pending > 0 and attempts < 10:
            if isinstance(self._link, QTcpSocket):
                if self._link.state() != QAbstractSocket.SocketState.ConnectedState:
                    raise OSError(self._link.errorString() or "QTcpSocket disconnected during send")
            elif QSerialPort is not None and isinstance(self._link, QSerialPort):
                if not self._link.isOpen():
                    raise OSError("QSerialPort closed during send")
            self._link.waitForBytesWritten(3000)
            pending = int(self._link.bytesToWrite()) if hasattr(self._link, "bytesToWrite") else 0
            attempts += 1


class UserHomePage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._username = ""
        self._running = False
        self._connecting = False
        self._links: dict[str, QTcpSocket | Any] = {}
        self._device_order: list[str] = []
        self._device_ui: dict[str, tuple[QLabel, QLabel]] = {}
        self._manual_edits: dict[str, QLineEdit] = {}
        self._scanner_device_name: str | None = None
        self._scanner_conn: dict[str, Any] = {}
        self._connections_flat: dict[str, dict[str, Any]] = {}
        self._devices_payload: list[dict[str, str]] = []
        self._scan_buffer = bytearray()
        self._scheduled_timers: list[QTimer] = []
        self._connect_queue: list[tuple[str, dict[str, Any]]] = []
        self._connect_results: dict[str, bool] = {}
        self._stopping_session = False

        root = QVBoxLayout(self)
        root.setSpacing(14)

        top_card = QFrame()
        top_card.setObjectName("HomeTopCard")
        top_layout = QHBoxLayout(top_card)
        top_layout.setSpacing(12)

        self.devices_wrap = QWidget()
        self.devices_row_layout = QHBoxLayout(self.devices_wrap)
        self.devices_row_layout.setSpacing(10)
        top_layout.addWidget(self.devices_wrap, 1)

        self.start_stop_button = QPushButton(_START_BUTTON_LABEL)
        self.start_stop_button.setObjectName("PrimaryButton")
        self.start_stop_button.setMinimumWidth(120)
        self.start_stop_button.clicked.connect(self._on_start_stop_clicked)
        top_layout.addWidget(self.start_stop_button, alignment=Qt.AlignVCenter)

        root.addWidget(top_card)

        self.manual_section_title = QLabel("مقادیر دستی اولویت چاپ (پر کردن قبل از شروع)")
        self.manual_section_title.setObjectName("FormFieldLabel")
        root.addWidget(self.manual_section_title)

        self.manual_fields_host = QWidget()
        self.manual_grid = QGridLayout(self.manual_fields_host)
        self.manual_grid.setContentsMargins(0, 0, 0, 0)
        self.manual_grid.setHorizontalSpacing(12)
        self.manual_grid.setVerticalSpacing(10)
        root.addWidget(self.manual_fields_host)

        results_title = QLabel("نتیجهٔ اسکن‌ها")
        results_title.setObjectName("FormFieldLabel")
        root.addWidget(results_title)

        self.results_table = QTableWidget(0, 3)
        self.results_table.setObjectName("UsersTable")
        self.results_table.setHorizontalHeaderLabels(["بارکد / مقدار اسکن", "وضعیت", "جزئیات"])
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.results_table.setSelectionMode(QTableWidget.NoSelection)
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.results_table.setMinimumHeight(180)
        self.results_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.results_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        root.addWidget(self.results_table, 1)

        self._hint = QLabel()
        self._hint.setObjectName("DialogSubtitle")
        self._hint.setWordWrap(True)
        root.addWidget(self._hint)

    def set_username(self, username: str | None) -> None:
        self.stop_session_if_running()
        self._username = (username or "").strip()
        self.reload_devices_ui()

    def reload_devices_ui(self) -> None:
        if self._running or self._connecting:
            return
        self._clear_layout(self.devices_row_layout)
        self._device_ui.clear()
        self._manual_edits.clear()
        self._clear_manual_grid()

        if not self._username:
            self._hint.setText("وارد حساب نشده‌اید.")
            self.start_stop_button.setEnabled(False)
            return

        devices_by_user = get_devices_by_user()
        connections_by_user = get_device_connections_by_user()
        self._devices_payload = list(devices_by_user.get(self._username, []))
        self._connections_flat = dict(connections_by_user.get(self._username, {}))

        self._device_order = [
            str(d.get("name", "")).strip()
            for d in self._devices_payload
            if str(d.get("name", "")).strip()
        ]

        if not self._device_order:
            self._hint.setText("دستگاهی به این کاربر اختصاص داده نشده است.")
            self.start_stop_button.setEnabled(False)
            return

        self._hint.setText(
            "پس از پر کردن فیلدهای دستی (در صورت وجود)، شروع را بزنید؛ پس از اتصال موفق همهٔ دستگاه‌ها، اسکن بارکد فعال می‌شود."
        )
        self.start_stop_button.setEnabled(True)

        for device_name in self._device_order:
            chip = QFrame()
            chip.setObjectName("HomeDeviceChip")
            hl = QHBoxLayout(chip)
            hl.setContentsMargins(10, 8, 10, 8)
            hl.setSpacing(8)
            name_lbl = QLabel(device_name)
            name_lbl.setObjectName("HomeDeviceName")
            status_lbl = QLabel("○")
            status_lbl.setObjectName("HomeDeviceStatusIdle")
            hl.addWidget(name_lbl)
            hl.addWidget(status_lbl)
            self.devices_row_layout.addWidget(chip)
            self._device_ui[device_name] = (name_lbl, status_lbl)

        self.devices_row_layout.addStretch()

        manual_names = self._collect_manual_priority_names()
        self.manual_section_title.setVisible(bool(manual_names))
        self.manual_fields_host.setVisible(bool(manual_names))

        if manual_names:
            cols = min(4, max(1, len(manual_names)))
            for i, label_text in enumerate(manual_names):
                row, col = divmod(i, cols)
                field_label = QLabel(label_text)
                field_label.setObjectName("FormFieldLabel")
                edit = QLineEdit()
                edit.setPlaceholderText(label_text)
                cell = QWidget()
                cv = QVBoxLayout(cell)
                cv.setContentsMargins(0, 0, 0, 0)
                cv.setSpacing(4)
                cv.addWidget(field_label)
                cv.addWidget(edit)
                self.manual_grid.addWidget(cell, row, col)
                self._manual_edits[label_text] = edit

        self._scanner_device_name = self._pick_scanner_name()

    def stop_session_if_running(self) -> None:
        if self._running or self._connecting:
            self._shutdown_session()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not self._running and not self._connecting:
            if self.results_table.rowCount() > 0:
                self.results_table.setRowCount(0)
            self._scan_buffer.clear()
            self.reload_devices_ui()

    def _clear_layout(self, layout: QHBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

    def _clear_manual_grid(self) -> None:
        while self.manual_grid.count():
            item = self.manual_grid.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

    def _collect_manual_priority_names(self) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []
        for device in self._devices_payload:
            if str(device.get("type", "")).strip().lower() != "printer":
                continue
            dname = str(device.get("name", "")).strip()
            cfg = self._connections_flat.get(dname, {})
            raw_pri = cfg.get("print_priorities", [])
            if not isinstance(raw_pri, list):
                continue
            for item in raw_pri:
                if not isinstance(item, dict):
                    continue
                if str(item.get("source_type", "")).strip() != "manual":
                    continue
                pname = str(item.get("name", "")).strip()
                if pname and pname not in seen:
                    seen.add(pname)
                    ordered.append(pname)
        return ordered

    def _pick_scanner_name(self) -> str | None:
        for device in self._devices_payload:
            if str(device.get("type", "")).strip().lower() == "scanner":
                n = str(device.get("name", "")).strip()
                if n:
                    return n
        return None

    def _set_device_status(self, device_name: str, state: str) -> None:
        ui = self._device_ui.get(device_name)
        if not ui:
            return
        _, status_lbl = ui
        if state == "idle":
            status_lbl.setText("○")
            status_lbl.setObjectName("HomeDeviceStatusIdle")
        elif state == "ok":
            status_lbl.setText("✓")
            status_lbl.setObjectName("HomeDeviceStatusOk")
        elif state == "fail":
            status_lbl.setText("✗")
            status_lbl.setObjectName("HomeDeviceStatusFail")
        status_lbl.style().unpolish(status_lbl)
        status_lbl.style().polish(status_lbl)

    def _reset_all_device_status_ui(self) -> None:
        for name in self._device_order:
            self._set_device_status(name, "idle")

    def _on_start_stop_clicked(self) -> None:
        if self._running:
            self._shutdown_session()
            return
        self._begin_start_sequence()

    def _begin_start_sequence(self) -> None:
        if not self._username or not self._device_order:
            return
        if self._scanner_device_name is None:
            QMessageBox.warning(self, "شروع", "هیچ دستگاه اسکنری به این کاربر اختصاص داده نشده است.")
            return
        for title, edit in self._manual_edits.items():
            if not edit.text().strip():
                QMessageBox.warning(self, "شروع", f"فیلد دستی «{title}» را پر کنید.")
                return

        self.results_table.setRowCount(0)
        self._scan_buffer.clear()
        self._running = False
        self._connecting = True
        self._links.clear()
        self._connect_results = {}
        self._reset_all_device_status_ui()
        self.start_stop_button.setText(_CONNECTING_BUTTON_LABEL)
        self.start_stop_button.setEnabled(False)

        self._connect_queue = []
        for device in self._devices_payload:
            name = str(device.get("name", "")).strip()
            if not name:
                continue
            cfg = dict(self._connections_flat.get(name, {}))
            self._connect_queue.append((name, cfg))

        self._connect_next_device()

    def _connect_next_device(self) -> None:
        if not self._connect_queue:
            self._on_all_devices_processed()
            return

        device_name, cfg = self._connect_queue.pop(0)
        mode = str(cfg.get("mode", "ip")).strip().lower()
        if mode not in {"ip", "com"}:
            mode = "ip"

        if mode == "ip":
            ip = str(cfg.get("ip", "")).strip()
            port_s = str(cfg.get("port", "")).strip()
            if not ip or not port_s:
                self._connect_results[device_name] = False
                self._set_device_status(device_name, "fail")
                self._connect_next_device()
                return
            try:
                port = int(port_s, 10)
            except ValueError:
                self._connect_results[device_name] = False
                self._set_device_status(device_name, "fail")
                self._connect_next_device()
                return

            sock = QTcpSocket(self)
            self._links[device_name] = sock

            def cleanup_signals() -> None:
                try:
                    sock.connected.disconnect()
                except TypeError:
                    pass
                try:
                    sock.errorOccurred.disconnect()
                except TypeError:
                    pass

            def on_ok() -> None:
                cleanup_signals()
                self._connect_results[device_name] = True
                self._set_device_status(device_name, "ok")
                self._connect_next_device()

            def on_err(_: QAbstractSocket.SocketError = QAbstractSocket.SocketError.UnknownSocketError) -> None:
                cleanup_signals()
                self._connect_results[device_name] = False
                self._set_device_status(device_name, "fail")
                sock.abort()
                sock.deleteLater()
                self._links.pop(device_name, None)
                self._connect_next_device()

            sock.connected.connect(on_ok)
            sock.errorOccurred.connect(on_err)
            sock.connectToHost(ip, port)
            return

        if QSerialPort is None:
            self._connect_results[device_name] = False
            self._set_device_status(device_name, "fail")
            self._connect_next_device()
            return

        com_port = str(cfg.get("com", "")).strip()
        if not com_port:
            self._connect_results[device_name] = False
            self._set_device_status(device_name, "fail")
            self._connect_next_device()
            return

        serial = QSerialPort(self)
        serial.setPortName(com_port)
        ok_open = serial.open(QSerialPort.OpenModeFlag.ReadWrite)
        self._connect_results[device_name] = ok_open
        if ok_open:
            self._links[device_name] = serial
            self._set_device_status(device_name, "ok")
        else:
            serial.deleteLater()
            self._set_device_status(device_name, "fail")
        self._connect_next_device()

    def _on_all_devices_processed(self) -> None:
        self._connecting = False
        all_ok = bool(self._device_order) and all(
            self._connect_results.get(name, False) for name in self._device_order
        )
        if not all_ok:
            QMessageBox.warning(
                self,
                "اتصال",
                "اتصال به همهٔ دستگاه‌ها برقرار نشد. اتصال‌های جزئی قطع می‌شود.",
            )
            self._cleanup_links()
            self._reset_all_device_status_ui()
            self.start_stop_button.setText(_START_BUTTON_LABEL)
            self.start_stop_button.setEnabled(True)
            self.start_stop_button.setObjectName("PrimaryButton")
            self.start_stop_button.style().unpolish(self.start_stop_button)
            self.start_stop_button.style().polish(self.start_stop_button)
            return

        scanner_name = self._scanner_device_name
        if not scanner_name or scanner_name not in self._links:
            QMessageBox.warning(self, "اسکنر", "اتصال اسکنر برقرار نیست.")
            self._cleanup_links()
            self._reset_all_device_status_ui()
            self.start_stop_button.setText(_START_BUTTON_LABEL)
            self.start_stop_button.setEnabled(True)
            return

        self._scanner_conn = dict(self._connections_flat.get(scanner_name, {}))
        self._running = True
        self._attach_runtime_disconnect_watchers()
        self._attach_scanner_reader(scanner_name)
        self.start_stop_button.setText(_STOP_BUTTON_LABEL)
        self.start_stop_button.setEnabled(True)
        self.start_stop_button.setObjectName("DangerButton")
        self.start_stop_button.style().unpolish(self.start_stop_button)
        self.start_stop_button.style().polish(self.start_stop_button)

        for edit in self._manual_edits.values():
            edit.setReadOnly(True)

    def _attach_runtime_disconnect_watchers(self) -> None:
        for device_name, link in self._links.items():
            if isinstance(link, QTcpSocket):
                link.disconnected.connect(
                    lambda checked=False, name=device_name: self._on_runtime_device_disconnected(name)
                )
                link.errorOccurred.connect(
                    lambda _error, name=device_name: self._on_runtime_device_disconnected(name)
                )
            elif QSerialPort is not None and isinstance(link, QSerialPort):
                link.errorOccurred.connect(
                    lambda error, name=device_name: self._on_runtime_serial_error(name, error)
                )

    def _on_runtime_serial_error(self, device_name: str, error: Any) -> None:
        if QSerialPort is not None and error == QSerialPort.SerialPortError.NoError:
            return
        self._on_runtime_device_disconnected(device_name)

    def _on_runtime_device_disconnected(self, device_name: str) -> None:
        if not self._running or self._stopping_session:
            return
        self._stopping_session = True
        self._running = False
        self._connecting = False
        self._cancel_timers()
        self._cleanup_links()
        self._scan_buffer.clear()
        self._connect_queue.clear()
        self._reset_all_device_status_ui()
        self._set_device_status(device_name, "fail")
        self.start_stop_button.setText(_START_BUTTON_LABEL)
        self.start_stop_button.setObjectName("PrimaryButton")
        self.start_stop_button.style().unpolish(self.start_stop_button)
        self.start_stop_button.style().polish(self.start_stop_button)
        self.start_stop_button.setEnabled(bool(self._username) and bool(self._device_order))
        self._hint.setText(f"اتصال دستگاه «{device_name}» قطع شد. عملیات متوقف شد.")
        for edit in self._manual_edits.values():
            edit.setReadOnly(False)
        self._stopping_session = False
        QTimer.singleShot(0, lambda name=device_name: self._show_disconnect_dialog(name))

    def _show_disconnect_dialog(self, device_name: str) -> None:
        QMessageBox.critical(
            self,
            "قطع اتصال دستگاه",
            f"اتصال دستگاه «{device_name}» قطع شد.\nعملیات متوقف شد. لطفاً پس از بررسی، دوباره شروع کنید.",
        )

    def _attach_scanner_reader(self, scanner_name: str) -> None:
        link = self._links.get(scanner_name)
        if isinstance(link, QTcpSocket):
            link.readyRead.connect(self._on_scanner_ready_read)
        elif QSerialPort is not None and isinstance(link, QSerialPort):
            link.readyRead.connect(self._on_scanner_ready_read)

    def _detach_scanner_reader(self) -> None:
        scanner_name = self._scanner_device_name
        if not scanner_name:
            return
        link = self._links.get(scanner_name)
        if isinstance(link, QTcpSocket):
            try:
                link.readyRead.disconnect(self._on_scanner_ready_read)
            except TypeError:
                pass
        elif QSerialPort is not None and isinstance(link, QSerialPort):
            try:
                link.readyRead.disconnect(self._on_scanner_ready_read)
            except TypeError:
                pass

    def _on_scanner_ready_read(self) -> None:
        scanner_name = self._scanner_device_name
        if not scanner_name:
            return
        link = self._links.get(scanner_name)
        chunk = QByteArray()
        if isinstance(link, QTcpSocket):
            chunk = link.readAll()
        elif QSerialPort is not None and isinstance(link, QSerialPort):
            chunk = link.readAll()
        if chunk.isEmpty():
            return
        self._scan_buffer.extend(chunk.data())

        while True:
            buf = self._scan_buffer
            pos_nl = buf.find(b"\n")
            pos_cr = buf.find(b"\r")
            candidates = [p for p in (pos_nl, pos_cr) if p >= 0]
            if not candidates:
                break
            pos = min(candidates)
            raw_line = buf[:pos]
            del buf[: pos + 1]
            try:
                line = raw_line.decode("utf-8").strip()
            except UnicodeDecodeError:
                line = raw_line.decode("utf-8", errors="ignore").strip()
            if line:
                self._handle_scanned_value(line)

    def _handle_scanned_value(self, barcode: str) -> None:
        lookup_field = str(self._scanner_conn.get("lookup_field", "")).strip()
        products = get_products_by_user().get(self._username, [])
        if not isinstance(products, list):
            products = []

        found: dict[str, Any] | None = None
        if lookup_field:
            for item in products:
                if not isinstance(item, dict):
                    continue
                values = item.get("values", {})
                if not isinstance(values, dict):
                    continue
                v = values.get(lookup_field)
                if v is not None and str(v).strip() == barcode:
                    found = dict(values)
                    break

        if not barcode.strip():
            self._append_result_row(barcode, invalid=True, details="مقدار اسکن خالی است.")
            self._trigger_rejector_sequence()
            return

        if found is None:
            self._append_result_row(barcode, invalid=True, details="محصولی با این مقدار یافت نشد.")
            self._trigger_rejector_sequence()
            return

        details_text = self._format_product_details(found)
        self._append_result_row(barcode, invalid=False, details=details_text)
        self._send_print_job(found)

    def _structure_field_labels(self) -> list[tuple[str, str, bool]]:
        struct_name = str(get_product_structure_by_user().get(self._username, "")).strip()
        detail_map = get_product_scan_detail_fields_by_user()
        display_cfg: dict[str, bool] | None
        if self._username not in detail_map:
            display_cfg = None
        else:
            raw_entries = detail_map.get(self._username, [])
            if not isinstance(raw_entries, list):
                display_cfg = None
            else:
                display_cfg = {}
                for item in raw_entries:
                    if isinstance(item, dict):
                        name = str(item.get("name", "")).strip()
                        if not name:
                            continue
                        raw_show = item.get("show_name", True)
                        show_name = raw_show is True or str(raw_show).strip().lower() in {
                            "true",
                            "1",
                            "yes",
                        }
                        display_cfg[name.casefold()] = show_name

        for st in get_product_structures():
            if str(st.get("name", "")).strip() == struct_name:
                fields = st.get("fields", [])
                out: list[tuple[str, str, bool]] = []
                if isinstance(fields, list):
                    for f in fields:
                        if isinstance(f, dict):
                            fn = str(f.get("name", "")).strip()
                            ft = str(f.get("type", "")).strip()
                            if fn:
                                out.append((fn, ft, True))
                if display_cfg is None:
                    return out
                if not display_cfg:
                    return []
                filtered: list[tuple[str, str, bool]] = []
                for fn, ft, _default_show in out:
                    key = fn.casefold()
                    if key in display_cfg:
                        filtered.append((fn, ft, bool(display_cfg[key])))
                return filtered
        return []

    def _format_product_details(self, values: dict[str, Any]) -> str:
        lines: list[str] = []
        for fname, _ftype, show_name in self._structure_field_labels():
            raw = values.get(fname)
            scalar = _format_cell_scalar(raw)
            lines.append(f"{fname}: {scalar}" if show_name else scalar)
        if not lines:
            return json.dumps(values, ensure_ascii=False)
        return " | ".join(lines)

    def _append_result_row(self, barcode: str, *, invalid: bool, details: str) -> None:
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        bc_item = QTableWidgetItem(barcode)
        bc_item.setTextAlignment(Qt.AlignCenter)
        status_item = QTableWidgetItem("نامعتبر" if invalid else "موفق")
        status_item.setTextAlignment(Qt.AlignCenter)
        if invalid:
            status_item.setForeground(QColor("#b91c1c"))
        else:
            status_item.setForeground(QColor("#15803d"))
        det_item = QTableWidgetItem(details)
        det_item.setTextAlignment(Qt.AlignCenter)
        self.results_table.setItem(row, 0, bc_item)
        self.results_table.setItem(row, 1, status_item)
        self.results_table.setItem(row, 2, det_item)
        self._trim_result_rows()
        self.results_table.scrollToBottom()

    def _trim_result_rows(self) -> None:
        overflow_count = self.results_table.rowCount() - get_scan_results_limit()
        if overflow_count <= 0:
            return
        for _ in range(overflow_count):
            self.results_table.removeRow(0)

    def _manual_text(self, title: str) -> str:
        edit = self._manual_edits.get(title)
        return edit.text().strip() if edit else ""

    def _annotate_last_result(self, suffix: str) -> None:
        row = self.results_table.rowCount() - 1
        if row < 0:
            return
        item = self.results_table.item(row, 2)
        if item is None:
            return
        base = item.text().strip()
        item.setText(f"{base} | {suffix}" if base else suffix)

    def _build_print_items(
        self, product_values: dict[str, Any], priorities: list[dict[str, str]]
    ) -> list[str]:
        """Build non-empty print values in priority order (sent as one list to the printer)."""
        items: list[str] = []
        for item in priorities:
            name = str(item.get("name", "")).strip()
            source_type = str(item.get("source_type", "")).strip()
            source_value = str(item.get("source_value", "")).strip()
            if source_type == "manual":
                text = self._manual_text(name)
            elif source_type == "product_field" and source_value:
                text = _format_cell_scalar(product_values.get(source_value))
            else:
                continue
            text = text.strip()
            if text:
                items.append(text)
        return items

    def _send_print_job(self, product_values: dict[str, Any]) -> None:
        printer_name = str(self._scanner_conn.get("target_printer", "")).strip()
        if not printer_name:
            self._annotate_last_result("چاپ: پرینتر هدف برای اسکنر تنظیم نشده است")
            return

        cfg = dict(self._connections_flat.get(printer_name, {}))
        priorities = resolve_print_priorities(cfg)
        if not priorities:
            self._annotate_last_result(
                f"چاپ: برای دستگاه «{printer_name}» اولویت چاپ تعریف نشده است"
            )
            return

        print_items = self._build_print_items(product_values, priorities)
        if not print_items:
            self._annotate_last_result("چاپ: متن خالی است (فیلدها مقدار ندارند)")
            return

        printer_type = _normalize_printer_type(cfg.get("printer_type", PRINTER_TYPE_A520I))
        link = self._links.get(printer_name)
        if link is None:
            self._annotate_last_result(f"چاپ: اتصال به «{printer_name}» برقرار نیست")
            return

        connected = isinstance(link, QTcpSocket) and link.state() == QAbstractSocket.SocketState.ConnectedState
        serial_open = QSerialPort is not None and isinstance(link, QSerialPort) and link.isOpen()
        if not connected and not serial_open:
            self._annotate_last_result(f"چاپ: اتصال به «{printer_name}» قطع شده است")
            return

        if printer_type == PRINTER_TYPE_A520I:
            adapter = _SendAllAdapter(link)
            if send_to_printer(print_items, adapter):
                count_label = f"{len(print_items)} مورد"
                self._annotate_last_result(f"چاپ: ارسال {count_label} به «{printer_name}» انجام شد")
            else:
                self._annotate_last_result(f"چاپ: خطا در ارسال به «{printer_name}»")
            return

        payload = "\n".join(print_items) + "\n"
        self._write_device_text(printer_name, payload)
        self._annotate_last_result(f"چاپ: ارسال {len(print_items)} مورد به «{printer_name}» انجام شد")

    def _trigger_rejector_sequence(self) -> None:
        rname = str(self._scanner_conn.get("target_rejector", "")).strip()
        if not rname:
            return
        cfg = dict(self._connections_flat.get(rname, {}))
        delay_o = _nz_int(cfg.get("rejector_delay_before_ms", "0"))
        duration = _nz_int(cfg.get("rejector_open_duration_ms", "0"))
        delay_c = delay_o + duration

        self._schedule_timer(delay_o, lambda: self._write_device_raw(rname, b"O"))
        self._schedule_timer(delay_c, lambda: self._write_device_raw(rname, b"C"))

    def _schedule_timer(self, delay_ms: int, callback) -> None:
        if delay_ms < 0:
            delay_ms = 0
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(callback)
        timer.start(delay_ms)
        self._scheduled_timers.append(timer)

    def _cancel_timers(self) -> None:
        for t in self._scheduled_timers:
            t.stop()
            t.deleteLater()
        self._scheduled_timers.clear()

    def _write_device_raw(self, device_name: str, data: bytes) -> None:
        link = self._links.get(device_name)
        if isinstance(link, QTcpSocket) and link.state() == QAbstractSocket.SocketState.ConnectedState:
            link.write(data)
            link.flush()
        elif QSerialPort is not None and isinstance(link, QSerialPort) and link.isOpen():
            link.write(data)
            link.flush()

    def _write_device_text(self, device_name: str, text: str) -> None:
        self._write_device_raw(device_name, text.encode("utf-8"))

    def _disconnect_link_signals(self, link: QTcpSocket | Any) -> None:
        if isinstance(link, QTcpSocket):
            for signal in (link.readyRead, link.disconnected, link.errorOccurred):
                try:
                    signal.disconnect()
                except (TypeError, RuntimeError):
                    pass
        elif QSerialPort is not None and isinstance(link, QSerialPort):
            for signal in (link.readyRead, link.errorOccurred):
                try:
                    signal.disconnect()
                except (TypeError, RuntimeError):
                    pass

    def _cleanup_links(self) -> None:
        self._detach_scanner_reader()
        for name, link in list(self._links.items()):
            self._disconnect_link_signals(link)
            if isinstance(link, QTcpSocket):
                link.disconnectFromHost()
                link.abort()
                link.deleteLater()
            elif QSerialPort is not None and isinstance(link, QSerialPort):
                link.close()
                link.deleteLater()
        self._links.clear()

    def _shutdown_session(self) -> None:
        self._cancel_timers()
        self._cleanup_links()
        self._scan_buffer.clear()
        self._connect_queue.clear()
        self._running = False
        self._connecting = False
        self._reset_all_device_status_ui()
        self.start_stop_button.setText(_START_BUTTON_LABEL)
        self.start_stop_button.setObjectName("PrimaryButton")
        self.start_stop_button.style().unpolish(self.start_stop_button)
        self.start_stop_button.style().polish(self.start_stop_button)
        self.start_stop_button.setEnabled(bool(self._username) and bool(self._device_order))

        for edit in self._manual_edits.values():
            edit.setReadOnly(False)


def _format_cell_scalar(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "بله" if value else "خیر"
    if isinstance(value, float):
        return str(value)
    if isinstance(value, (dict, list)):
        try:
            return json.dumps(value, ensure_ascii=False)
        except TypeError:
            return str(value)
    return str(value)
