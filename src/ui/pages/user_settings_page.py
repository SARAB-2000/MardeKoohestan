from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QLayout,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ui.widgets.input_controls import NoWheelSpinBox
from ui.pages.user_products_page import UserProductsPage
from ui.widgets.responsive_form import ResponsiveFormSection
from ui.widgets.styled_combo_field import StyledComboField
from user_store import (
    get_device_connections_by_user,
    get_devices_by_user,
    get_product_structure_by_user,
    get_product_structures,
    save_device_connections_by_user,
)

try:
    from PySide6.QtSerialPort import QSerialPortInfo
except ImportError:  # pragma: no cover - depends on runtime package
    QSerialPortInfo = None

DEVICE_TYPE_LABELS: dict[str, str] = {
    "scanner": "اسکنر",
    "printer": "پرینتر",
    "rejector": "ریجکتور",
}


def _non_negative_int(raw: object, default: int = 0) -> int:
    try:
        return max(0, int(str(raw).strip()))
    except (TypeError, ValueError):
        return default


def _stack_control_and_hint(control: QWidget, hint: QLabel) -> QWidget:
    wrap = QWidget()
    stack = QVBoxLayout(wrap)
    stack.setContentsMargins(0, 0, 0, 0)
    stack.setSpacing(4)
    stack.addWidget(control)
    stack.addWidget(hint)
    return wrap


class UserDeviceConfigPage(QWidget):
    def __init__(
        self,
        username: str,
        device_name: str,
        device_type: str,
        available_printers: list[str],
        available_rejectors: list[str],
        search_fields: list[str],
        structure_field_names: list[str],
        connections_by_user: dict[str, dict[str, dict[str, str]]],
        on_save,
    ) -> None:
        super().__init__()
        self._initializing = True
        self._username = username
        self._device_name = device_name
        self._connections_by_user = connections_by_user
        self._on_save = on_save
        self._device_type = device_type
        self._product_field_names = structure_field_names

        config = (
            self._connections_by_user.get(username, {}).get(device_name, {})
            if isinstance(self._connections_by_user.get(username, {}), dict)
            else {}
        )
        mode = str(config.get("mode", "ip")).strip().lower()
        if mode not in {"ip", "com"}:
            mode = "ip"
        reject_delay_ms = _non_negative_int(config.get("rejector_delay_before_ms", "0"))
        reject_duration_ms = _non_negative_int(config.get("rejector_open_duration_ms", "0"))

        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setObjectName("DeviceSettingsScrollArea")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scroll = scroll

        content = QWidget()
        content.setObjectName("DeviceSettingsScrollContent")
        content.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self._scroll_content = content
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setSizeConstraint(QLayout.SetMinimumSize)
        layout.setAlignment(Qt.AlignTop)
        self._scroll_content_layout = layout

        type_text = DEVICE_TYPE_LABELS.get(device_type, device_type or "نامشخص")
        self.type_label = QLabel(f"نوع دستگاه: {type_text}")
        self.type_label.setObjectName("DialogSubtitle")
        layout.addWidget(self.type_label)

        self.mode_selector = StyledComboField()
        self.mode_selector.combo_box.addItem("TCP", "ip")
        self.mode_selector.combo_box.addItem("Serial", "com")
        self.mode_selector.combo_box.setCurrentIndex(0 if mode == "ip" else 1)
        self.mode_selector.currentTextChanged.connect(self._on_mode_changed)
        layout.addWidget(self.mode_selector)

        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("مثال 192.168.1.10")
        self.ip_input.setText(str(config.get("ip", "")).strip())
        self.ip_input.editingFinished.connect(self._save)

        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("مثال 9100")
        self.port_input.setText(str(config.get("port", "")).strip())
        self.port_input.editingFinished.connect(self._save)

        self._tcp_fields = ResponsiveFormSection(min_column_width=240, max_columns=4)
        self._tcp_fields.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._tcp_fields.add_field("آدرس IP", self.ip_input)
        self._tcp_fields.add_field("پورت", self.port_input)
        layout.addWidget(self._tcp_fields)

        self.com_selector = StyledComboField()
        self.com_selector.currentIndexChanged.connect(self._save)

        self._serial_fields = ResponsiveFormSection(min_column_width=260, max_columns=3)
        self._serial_fields.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._serial_fields.add_field("درگاه سریال (COM)", self.com_selector)
        layout.addWidget(self._serial_fields)
        self._load_com_ports(selected=str(config.get("com", "")).strip())

        self.rejector_settings_title = QLabel("تنظیمات مخصوص ریجکتور")
        self.rejector_settings_title.setObjectName("FormFieldLabel")
        self.rejector_delay_spin = NoWheelSpinBox()
        self.rejector_delay_spin.setObjectName("RejectorMsSpin")
        self.rejector_delay_spin.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.rejector_delay_spin.setRange(0, 999_999_999)
        self.rejector_delay_spin.setValue(reject_delay_ms)
        self.rejector_delay_spin.valueChanged.connect(self._save)
        self.rejector_duration_spin = NoWheelSpinBox()
        self.rejector_duration_spin.setObjectName("RejectorMsSpin")
        self.rejector_duration_spin.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.rejector_duration_spin.setRange(0, 999_999_999)
        self.rejector_duration_spin.setValue(reject_duration_ms)
        self.rejector_duration_spin.valueChanged.connect(self._save)

        self._rejector_fields = ResponsiveFormSection(min_column_width=260, max_columns=4)
        self._rejector_fields.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._rejector_fields.add_field("تاخیر باز شدن (میلی‌ثانیه)", self.rejector_delay_spin)
        self._rejector_fields.add_field("مدت زمان باز ماندن (میلی‌ثانیه)", self.rejector_duration_spin)

        self.rejector_section = QWidget()
        rejector_section_layout = QVBoxLayout(self.rejector_section)
        rejector_section_layout.setContentsMargins(0, 18, 0, 0)
        rejector_section_layout.setSpacing(10)
        rejector_section_layout.addWidget(self.rejector_settings_title)
        rejector_section_layout.addWidget(self._rejector_fields)

        self.printer_hint = QLabel()
        self.printer_hint.setObjectName("DialogSubtitle")
        self.rejector_hint = QLabel()
        self.rejector_hint.setObjectName("DialogSubtitle")
        self.field_hint = QLabel()
        self.field_hint.setObjectName("DialogSubtitle")

        self.target_printer_selector = StyledComboField()
        self.target_printer_selector.currentIndexChanged.connect(self._save)
        self._populate_named_selector(
            self.target_printer_selector,
            options=available_printers,
            selected=str(config.get("target_printer", "")).strip(),
            empty_hint="پرینتر تعریف نشده است.",
            hint_label=self.printer_hint,
        )

        self.target_rejector_selector = StyledComboField()
        self.target_rejector_selector.currentIndexChanged.connect(self._save)
        self._populate_named_selector(
            self.target_rejector_selector,
            options=available_rejectors,
            selected=str(config.get("target_rejector", "")).strip(),
            empty_hint="ریجکتور تعریف نشده است.",
            hint_label=self.rejector_hint,
        )

        self.lookup_field_selector = StyledComboField()
        self.lookup_field_selector.currentIndexChanged.connect(self._save)
        self._populate_named_selector(
            self.lookup_field_selector,
            options=search_fields,
            selected=str(config.get("lookup_field", "")).strip(),
            empty_hint="فیلد text/number برای ساختار محصول کاربر تعریف نشده است.",
            hint_label=self.field_hint,
        )

        self.scanner_settings_title = QLabel("تنظیمات مخصوص اسکنر")
        self.scanner_settings_title.setObjectName("FormFieldLabel")

        self.printer_settings_title = QLabel("تنظیمات مخصوص پرینتر")
        self.printer_settings_title.setObjectName("FormFieldLabel")
        self.printer_type_selector = StyledComboField()
        self.printer_type_selector.combo_box.addItem("A", "A")
        self.printer_type_selector.combo_box.addItem("B", "B")
        current_printer_type = str(config.get("printer_type", "A")).strip().upper()
        self.printer_type_selector.combo_box.setCurrentText(
            current_printer_type if current_printer_type in {"A", "B"} else "A"
        )
        self.printer_type_selector.currentIndexChanged.connect(self._save)

        self.print_priority_title = QLabel("موارد چاپ به ترتیب اولویت")
        self.print_priority_title.setObjectName("FormFieldLabel")
        self.add_priority_button = QPushButton("＋ افزودن اولویت")
        self.add_priority_button.setObjectName("AddFieldButton")
        self.add_priority_button.clicked.connect(self._open_add_priority_dialog)

        self.priority_table = QTableWidget(0, 5)
        self.priority_table.setObjectName("UsersTable")
        self.priority_table.setHorizontalHeaderLabels(["اولویت", "نام", "جنس", "مقدار", "عملیات"])
        self.priority_table.verticalHeader().setVisible(False)
        self.priority_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.priority_table.setSelectionMode(QTableWidget.NoSelection)
        self.priority_table.setFocusPolicy(Qt.NoFocus)
        self.priority_table.verticalHeader().setDefaultSectionSize(42)
        self.priority_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.priority_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.priority_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.priority_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.priority_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.priority_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.priority_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.priority_hint = QLabel("هنوز اولویتی تعریف نشده است.")
        self.priority_hint.setObjectName("DialogSubtitle")

        self._scanner_section = ResponsiveFormSection(min_column_width=280, max_columns=4)
        self._scanner_section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._scanner_section.add_field(
            "پرینتر هدف",
            _stack_control_and_hint(self.target_printer_selector, self.printer_hint),
        )
        self._scanner_section.add_field(
            "ریجکتور هدف",
            _stack_control_and_hint(self.target_rejector_selector, self.rejector_hint),
        )
        self._scanner_section.add_field(
            "فیلد جستجوی محصول",
            _stack_control_and_hint(self.lookup_field_selector, self.field_hint),
        )

        self._printer_type_section = ResponsiveFormSection(min_column_width=240, max_columns=4)
        self._printer_type_section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._printer_type_section.add_field("نوع پرینتر", self.printer_type_selector)

        self.printer_priority_block = QWidget()
        printer_priority_layout = QVBoxLayout(self.printer_priority_block)
        printer_priority_layout.setContentsMargins(0, 0, 0, 0)
        printer_priority_layout.setSpacing(10)
        priority_toolbar = QHBoxLayout()
        priority_toolbar.setSpacing(10)
        priority_toolbar.addWidget(self.print_priority_title)
        priority_toolbar.addWidget(self.add_priority_button)
        priority_toolbar.addStretch()
        printer_priority_layout.addLayout(priority_toolbar)
        printer_priority_layout.addWidget(self.priority_table)
        printer_priority_layout.addWidget(self.priority_hint)

        loaded_priorities = config.get("print_priorities", [])
        self._print_priorities: list[dict[str, str]] = []
        if isinstance(loaded_priorities, list):
            for item in loaded_priorities:
                if not isinstance(item, dict):
                    continue
                name = str(item.get("name", "")).strip()
                source_type = str(item.get("source_type", "")).strip()
                source_value = str(item.get("source_value", "")).strip()
                is_valid = source_type in {"manual", "product_field"} and name
                if source_type == "product_field":
                    is_valid = is_valid and bool(source_value)
                if is_valid:
                    self._print_priorities.append(
                        {
                            "name": name,
                            "source_type": source_type,
                            "source_value": source_value,
                        }
                    )
        if not self._print_priorities:
            # Backward compatibility with older fixed 3-priority storage.
            for legacy_key in ("print_priority_1", "print_priority_2", "print_priority_3"):
                value = str(config.get(legacy_key, "")).strip()
                if not value:
                    continue
                source_type = "product_field" if value.startswith("فیلد: ") else "manual"
                source_value = value.removeprefix("فیلد: ").strip() if source_type == "product_field" else value
                self._print_priorities.append(
                    {"name": legacy_key.replace("print_priority_", "اولویت "), "source_type": source_type, "source_value": source_value}
                )

        layout.addWidget(self.rejector_section)
        layout.addSpacing(20)
        layout.addWidget(self.scanner_settings_title)
        layout.addWidget(self._scanner_section)
        layout.addWidget(self.printer_settings_title)
        layout.addWidget(self._printer_type_section)
        layout.addWidget(self.printer_priority_block)

        content.setLayout(layout)
        scroll.setWidget(content)
        outer_layout.addWidget(scroll)
        self.setLayout(outer_layout)
        self._apply_mode(mode)
        self._apply_scanner_visibility()
        self._refresh_priority_table()
        self._initializing = False

    def _load_com_ports(self, selected: str) -> None:
        self.com_selector.combo_box.clear()
        ports: list[str] = []
        if QSerialPortInfo is not None:
            ports = [port.portName() for port in QSerialPortInfo.availablePorts()]
        if not ports:
            self.com_selector.combo_box.addItem("COM فعال یافت نشد", "")
            self.com_selector.combo_box.setEnabled(False)
            return

        self.com_selector.combo_box.setEnabled(True)
        for port_name in ports:
            self.com_selector.combo_box.addItem(port_name, port_name)
        if selected and selected in ports:
            self.com_selector.combo_box.setCurrentText(selected)

    def _current_mode(self) -> str:
        mode = self.mode_selector.combo_box.currentData()
        return mode if isinstance(mode, str) and mode in {"ip", "com"} else "ip"

    def _populate_named_selector(
        self,
        selector: StyledComboField,
        options: list[str],
        selected: str,
        empty_hint: str,
        hint_label: QLabel,
    ) -> None:
        combo = selector.combo_box
        combo.clear()
        combo.addItem("انتخاب نشده", "")
        for option in options:
            combo.addItem(option, option)
        if selected and selected in options:
            combo.setCurrentText(selected)
        else:
            combo.setCurrentIndex(0)

        if options:
            combo.setEnabled(True)
            hint_label.clear()
            hint_label.setVisible(False)
        else:
            combo.setEnabled(False)
            hint_label.setText(empty_hint)
            hint_label.setVisible(True)

    def _on_mode_changed(self, _: str) -> None:
        self._apply_mode(self._current_mode())
        self._save()

    def _apply_mode(self, mode: str) -> None:
        is_ip = mode == "ip"
        self._tcp_fields.setVisible(is_ip)
        self._serial_fields.setVisible(not is_ip)

    def _apply_scanner_visibility(self) -> None:
        is_scanner = self._device_type == "scanner"
        is_printer = self._device_type == "printer"
        is_rejector = self._device_type == "rejector"
        self.rejector_section.setVisible(is_rejector)
        self.scanner_settings_title.setVisible(is_scanner)
        self._scanner_section.setVisible(is_scanner)
        self.printer_hint.setVisible(is_scanner and bool(self.printer_hint.text()))
        self.rejector_hint.setVisible(is_scanner and bool(self.rejector_hint.text()))
        self.field_hint.setVisible(is_scanner and bool(self.field_hint.text()))
        self.printer_settings_title.setVisible(is_printer)
        self._printer_type_section.setVisible(is_printer)
        self.printer_priority_block.setVisible(is_printer)
        self.priority_hint.setVisible(is_printer and self.priority_table.rowCount() == 0)

    def _refresh_priority_table(self) -> None:
        self.priority_table.setRowCount(0)
        for index, item in enumerate(self._print_priorities, start=1):
            row = self.priority_table.rowCount()
            self.priority_table.insertRow(row)

            priority_item = QTableWidgetItem(str(index))
            priority_item.setTextAlignment(Qt.AlignCenter)
            name_item = QTableWidgetItem(item["name"])
            name_item.setTextAlignment(Qt.AlignCenter)
            source_type = "دستی" if item["source_type"] == "manual" else "فیلد محصول"
            type_item = QTableWidgetItem(source_type)
            type_item.setTextAlignment(Qt.AlignCenter)
            value_text = (
                "—"
                if item["source_type"] == "manual"
                else f"فیلد: {item['source_value']}"
            )
            value_item = QTableWidgetItem(value_text)
            value_item.setTextAlignment(Qt.AlignCenter)

            self.priority_table.setItem(row, 0, priority_item)
            self.priority_table.setItem(row, 1, name_item)
            self.priority_table.setItem(row, 2, type_item)
            self.priority_table.setItem(row, 3, value_item)
            self._set_priority_action_cell(row)

        self.priority_hint.setVisible(
            self._device_type == "printer" and self.priority_table.rowCount() == 0
        )
        self._sync_priority_table_height()

    def _sync_priority_table_height(self) -> None:
        header_height = self.priority_table.horizontalHeader().height()
        row_count = self.priority_table.rowCount()
        rows_height = 0
        for row in range(row_count):
            rows_height += self.priority_table.rowHeight(row)

        frame = self.priority_table.frameWidth() * 2
        target_height = header_height + rows_height + frame + 4
        min_height = 140
        max_height = 520
        self.priority_table.setFixedHeight(max(min_height, min(target_height, max_height)))

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)

    def _set_priority_action_cell(self, row: int) -> None:
        actions_container = QWidget()
        actions_layout = QHBoxLayout()
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(6)

        edit_button = QPushButton("🖉")
        edit_button.setObjectName("RowIconButton")
        edit_button.setFlat(True)
        edit_button.setToolTip("ویرایش")
        edit_button.clicked.connect(lambda: self._open_edit_priority_dialog(row))

        delete_button = QPushButton("✖")
        delete_button.setObjectName("RowDangerIconButton")
        delete_button.setFlat(True)
        delete_button.setToolTip("حذف")
        delete_button.clicked.connect(lambda: self._delete_priority(row))

        actions_layout.addWidget(edit_button)
        actions_layout.addWidget(delete_button)
        actions_container.setLayout(actions_layout)
        self.priority_table.setCellWidget(row, 4, actions_container)

    def _open_add_priority_dialog(self) -> None:
        result = self._open_priority_dialog()
        if result is None:
            return
        self._print_priorities.append(result)
        self._refresh_priority_table()
        self._save()

    def _open_edit_priority_dialog(self, row: int) -> None:
        if row < 0 or row >= len(self._print_priorities):
            return
        result = self._open_priority_dialog(self._print_priorities[row])
        if result is None:
            return
        self._print_priorities[row] = result
        self._refresh_priority_table()
        self._save()

    def _delete_priority(self, row: int) -> None:
        if row < 0 or row >= len(self._print_priorities):
            return
        del self._print_priorities[row]
        self._refresh_priority_table()
        self._save()

    def _open_priority_dialog(self, initial: dict[str, str] | None = None) -> dict[str, str] | None:
        dialog = QDialog(self)
        dialog.setWindowTitle("افزودن اولویت چاپ" if initial is None else "ویرایش اولویت چاپ")
        dialog.setModal(True)
        dialog.setMinimumWidth(420)

        layout = QVBoxLayout()
        name_input = QLineEdit()
        name_input.setPlaceholderText("نام اولویت")
        if initial:
            name_input.setText(initial.get("name", ""))
        layout.addWidget(name_input)

        source_selector = StyledComboField()
        source_selector.combo_box.addItem("دستی", "manual")
        source_selector.combo_box.addItem("فیلد محصول", "product_field")
        layout.addWidget(source_selector)

        field_selector = StyledComboField()
        field_selector.combo_box.addItem("انتخاب نشده", "")
        for field_name in self._product_field_names:
            field_selector.combo_box.addItem(field_name, field_name)
        layout.addWidget(field_selector)

        current_source = initial.get("source_type", "manual") if initial else "manual"
        source_selector.combo_box.setCurrentIndex(0 if current_source == "manual" else 1)
        if initial:
            if current_source != "manual":
                field_selector.combo_box.setCurrentText(initial.get("source_value", ""))

        def refresh_source_visibility() -> None:
            is_manual = source_selector.combo_box.currentData() == "manual"
            field_selector.setVisible(not is_manual)
            dialog.adjustSize()

        source_selector.currentIndexChanged.connect(lambda _index: refresh_source_visibility())
        refresh_source_visibility()

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("تایید")
        buttons.button(QDialogButtonBox.Cancel).setText("لغو")
        layout.addWidget(buttons)
        dialog.setLayout(layout)
        buttons.rejected.connect(dialog.reject)

        result: dict[str, str] = {}

        def accept_dialog() -> None:
            name = name_input.text().strip()
            if not name:
                QMessageBox.warning(dialog, "خطا", "نام اولویت الزامی است.")
                return
            source_type = source_selector.combo_box.currentData()
            if source_type == "manual":
                source_value = ""
            else:
                source_value = str(field_selector.combo_box.currentData() or "").strip()
            if not source_value:
                if source_type == "product_field":
                    QMessageBox.warning(dialog, "خطا", "فیلد محصول باید انتخاب شود.")
                    return
            if source_type == "product_field" and source_value not in self._product_field_names:
                QMessageBox.warning(dialog, "خطا", "فیلد انتخاب‌شده معتبر نیست.")
                return
            result["name"] = name
            result["source_type"] = "manual" if source_type == "manual" else "product_field"
            result["source_value"] = source_value
            dialog.accept()

        buttons.accepted.connect(accept_dialog)
        if dialog.exec() != QDialog.Accepted:
            return None
        return result

    def _save(self, *_args) -> None:
        if self._initializing:
            return
        user_devices = self._connections_by_user.setdefault(self._username, {})
        payload = {
            "mode": self._current_mode(),
            "ip": self.ip_input.text().strip(),
            "port": self.port_input.text().strip(),
            "com": str(self.com_selector.combo_box.currentData() or "").strip(),
        }
        if self._device_type == "scanner":
            payload["target_printer"] = str(self.target_printer_selector.combo_box.currentData() or "").strip()
            payload["target_rejector"] = str(self.target_rejector_selector.combo_box.currentData() or "").strip()
            payload["lookup_field"] = str(self.lookup_field_selector.combo_box.currentData() or "").strip()
        if self._device_type == "printer":
            payload["printer_type"] = str(self.printer_type_selector.combo_box.currentData() or "A").strip()
            payload["print_priorities"] = [dict(item) for item in self._print_priorities]
        if self._device_type == "rejector":
            payload["rejector_delay_before_ms"] = str(self.rejector_delay_spin.value())
            payload["rejector_open_duration_ms"] = str(self.rejector_duration_spin.value())
        user_devices[self._device_name] = payload
        self._on_save(self._connections_by_user)


class UserDevicesPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._username: str = ""
        self._devices_by_user = get_devices_by_user()
        self._connections_by_user = get_device_connections_by_user()
        self._structure_by_user = get_product_structure_by_user()
        self._structures = get_product_structures()

        layout = QVBoxLayout()
        layout.setSpacing(10)

        self.devices_tabs = QTabWidget()
        self.devices_tabs.setObjectName("ManagementTabs")
        layout.addWidget(self.devices_tabs, 1)
        self.setLayout(layout)

    def set_username(self, username: str | None) -> None:
        self._username = (username or "").strip()
        self._devices_by_user = get_devices_by_user()
        self._connections_by_user = get_device_connections_by_user()
        self._structure_by_user = get_product_structure_by_user()
        self._structures = get_product_structures()
        self._refresh_devices()

    def _refresh_devices(self) -> None:
        self.devices_tabs.clear()
        if not self._username:
            return

        devices = self._devices_by_user.get(self._username, [])
        if not devices:
            return

        printer_devices = [
            str(device.get("name", "")).strip()
            for device in devices
            if str(device.get("type", "")).strip().lower() == "printer" and str(device.get("name", "")).strip()
        ]
        rejector_devices = [
            str(device.get("name", "")).strip()
            for device in devices
            if str(device.get("type", "")).strip().lower() == "rejector" and str(device.get("name", "")).strip()
        ]

        assigned_structure_name = str(self._structure_by_user.get(self._username, "")).strip()
        structure_map = {
            str(structure.get("name", "")).strip(): structure
            for structure in self._structures
            if str(structure.get("name", "")).strip()
        }
        assigned_structure = structure_map.get(assigned_structure_name, {})
        raw_fields = assigned_structure.get("fields", []) if isinstance(assigned_structure, dict) else []
        search_fields: list[str] = []
        structure_field_names: list[str] = []
        if isinstance(raw_fields, list):
            for field in raw_fields:
                if not isinstance(field, dict):
                    continue
                field_name = str(field.get("name", "")).strip()
                field_type = str(field.get("type", "")).strip().lower()
                if field_name:
                    structure_field_names.append(field_name)
                if field_name and field_type in {"text", "number"}:
                    search_fields.append(field_name)

        for device in devices:
            name = str(device.get("name", "")).strip()
            if not name:
                continue
            device_type = str(device.get("type", "")).strip().lower()
            tab_page = UserDeviceConfigPage(
                username=self._username,
                device_name=name,
                device_type=device_type,
                available_printers=printer_devices,
                available_rejectors=rejector_devices,
                search_fields=search_fields,
                structure_field_names=structure_field_names,
                connections_by_user=self._connections_by_user,
                on_save=self._save_connections,
            )
            self.devices_tabs.addTab(tab_page, name)

        if self.devices_tabs.count() == 0:
            return

    def _save_connections(self, data: dict[str, dict[str, dict[str, str]]]) -> None:
        self._connections_by_user = data
        save_device_connections_by_user(self._connections_by_user)

class UserSettingsPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout()
        layout.setSpacing(12)

        self.user_tabs = QTabWidget()
        self.user_tabs.setObjectName("ManagementTabs")
        self.devices_page = UserDevicesPage()
        self.products_page = UserProductsPage()
        self.user_tabs.addTab(self._with_scroll(self.devices_page), "دستگاه‌ها")
        self.user_tabs.addTab(self._with_scroll(self.products_page), "محصولات")

        layout.addWidget(self.user_tabs, 1)
        self.setLayout(layout)

    def set_username(self, username: str | None) -> None:
        self.devices_page.set_username(username)
        self.products_page.set_username(username)

    def _with_scroll(self, widget: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setObjectName("AppContentScrollArea")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setWidget(widget)
        return scroll
