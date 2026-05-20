from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QHeaderView,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from settings import DEFAULT_ADMIN_USERNAME
from user_store import get_devices_by_user, get_users, save_devices_by_user
from ui.widgets.styled_combo_field import StyledComboField

DEVICE_TYPE_LABELS: dict[str, str] = {
    "scanner": "اسکنر",
    "printer": "پرینتر",
    "rejector": "ریجکتور",
}


class DevicesTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._editing_row: int | None = None
        self._devices_by_user = get_devices_by_user()
        self._managed_users = self._load_managed_users()

        layout = QVBoxLayout()
        layout.setSpacing(12)

        top_row = QHBoxLayout()
        self.status_label = QLabel()
        self.status_label.setObjectName("DialogSubtitle")
        self.status_label.setWordWrap(True)
        self.status_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        top_row.addWidget(self.status_label, 1)
        top_row.addStretch()

        self.user_selector_shell = StyledComboField()
        self.user_selector = self.user_selector_shell.combo_box
        self.user_selector.currentTextChanged.connect(self._on_user_changed)
        self.user_selector_shell.setMinimumWidth(0)
        self.user_selector_shell.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        top_row.addWidget(self.user_selector_shell)

        self.add_button = QPushButton("＋ افزودن دستگاه")
        self.add_button.setObjectName("AddUserButton")
        self.add_button.clicked.connect(self._open_add_device_dialog)
        top_row.addWidget(self.add_button)
        layout.addLayout(top_row)

        self.empty_state_card = QFrame()
        self.empty_state_card.setObjectName("EmptyStateCard")
        empty_state_layout = QVBoxLayout()
        empty_state_layout.setContentsMargins(18, 16, 18, 16)
        self.empty_hint = QLabel("هیچ کاربری تعریف نشده است. ابتدا یک کاربر جدید ایجاد کنید.")
        self.empty_hint.setObjectName("EmptyStateText")
        self.empty_hint.setAlignment(Qt.AlignCenter)
        empty_state_layout.addWidget(self.empty_hint)
        self.empty_state_card.setLayout(empty_state_layout)
        layout.addWidget(self.empty_state_card, alignment=Qt.AlignCenter)

        self.devices_table = QTableWidget(0, 3)
        self.devices_table.setObjectName("UsersTable")
        self.devices_table.setHorizontalHeaderLabels(["نام دستگاه", "نوع دستگاه", "عملیات"])
        self.devices_table.verticalHeader().setVisible(False)
        self.devices_table.setAlternatingRowColors(True)
        self.devices_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.devices_table.setSelectionMode(QTableWidget.NoSelection)
        self.devices_table.setFocusPolicy(Qt.NoFocus)
        self.devices_table.verticalHeader().setDefaultSectionSize(48)
        self.devices_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        header = self.devices_table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setMinimumSectionSize(70)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        layout.addWidget(self.devices_table, 1)

        self.setLayout(layout)
        self._refresh_user_selector()
        self._refresh_page_state()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._devices_by_user = get_devices_by_user()
        self._refresh_user_selector()
        self._refresh_page_state()

    def _load_managed_users(self) -> list[str]:
        return [
            user["username"]
            for user in get_users()
            if user["username"].strip() != DEFAULT_ADMIN_USERNAME
        ]

    def _refresh_user_selector(self) -> None:
        current = self.user_selector.currentText()
        self._managed_users = self._load_managed_users()
        self.user_selector.blockSignals(True)
        self.user_selector.clear()
        self.user_selector.addItems(self._managed_users)
        if current and current in self._managed_users:
            self.user_selector.setCurrentText(current)
        self.user_selector.blockSignals(False)

    def _refresh_page_state(self) -> None:
        has_users = bool(self._managed_users)
        self.empty_state_card.setVisible(not has_users)
        self.user_selector_shell.setVisible(has_users)
        self.add_button.setVisible(has_users)
        self.devices_table.setVisible(has_users)
        if not has_users:
            self.status_label.clear()
            return
        self._refresh_table()

    def _current_username(self) -> str:
        return self.user_selector.currentText().strip()

    def _devices_for_current_user(self) -> list[dict[str, str]]:
        username = self._current_username()
        return self._devices_by_user.setdefault(username, [])

    def _on_user_changed(self) -> None:
        self._editing_row = None
        self._refresh_table()

    def _refresh_table(self) -> None:
        username = self._current_username()
        devices = self._devices_by_user.get(username, [])
        self.status_label.setText(f"لیست دستگاه‌های کاربر: {username} | تعداد: {len(devices)}")
        self.devices_table.setRowCount(0)
        for device in devices:
            row = self.devices_table.rowCount()
            self.devices_table.insertRow(row)
            device_item = QTableWidgetItem(device["name"])
            device_item.setTextAlignment(Qt.AlignCenter)
            type_item = QTableWidgetItem(self._display_type(device.get("type")))
            type_item.setTextAlignment(Qt.AlignCenter)
            self.devices_table.setItem(row, 0, device_item)
            self.devices_table.setItem(row, 1, type_item)
            self._set_action_cell(row)

    def _set_action_cell(self, row: int) -> None:
        actions_container = QWidget()
        actions_layout = QHBoxLayout()
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(6)

        edit_button = QPushButton("🖉")
        edit_button.setObjectName("RowIconButton")
        edit_button.setFlat(True)
        edit_button.setToolTip("ویرایش")
        edit_button.clicked.connect(lambda: self._start_row_edit(row))

        delete_button = QPushButton("✖")
        delete_button.setObjectName("RowDangerIconButton")
        delete_button.setFlat(True)
        delete_button.setToolTip("حذف")
        delete_button.clicked.connect(lambda: self._confirm_delete_row(row))

        confirm_button = QPushButton("✓")
        confirm_button.setObjectName("RowConfirmIconButton")
        confirm_button.setFlat(True)
        confirm_button.setToolTip("تایید و ذخیره این سطر")
        confirm_button.clicked.connect(lambda: self._confirm_row_edit(row))
        confirm_button.hide()

        actions_layout.addWidget(edit_button)
        actions_layout.addWidget(delete_button)
        actions_layout.addWidget(confirm_button)
        actions_container.setLayout(actions_layout)
        actions_container.setProperty("edit_button", edit_button)
        actions_container.setProperty("delete_button", delete_button)
        actions_container.setProperty("confirm_button", confirm_button)
        self.devices_table.setCellWidget(row, 2, actions_container)

    def _open_add_device_dialog(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("افزودن دستگاه")
        dialog.setModal(True)
        dialog.resize(420, 150)

        dialog_layout = QVBoxLayout()
        name_input = QLineEdit()
        name_input.setPlaceholderText("نام دستگاه")
        dialog_layout.addWidget(name_input)
        type_selector_shell = StyledComboField()
        type_selector = type_selector_shell.combo_box
        for code, fa_label in DEVICE_TYPE_LABELS.items():
            type_selector.addItem(fa_label, code)
        dialog_layout.addWidget(type_selector_shell)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("تایید")
        buttons.button(QDialogButtonBox.Cancel).setText("لغو")
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        dialog_layout.addWidget(buttons)
        dialog.setLayout(dialog_layout)

        if dialog.exec() != QDialog.Accepted:
            return

        name = name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "خطا", "نام دستگاه الزامی است.")
            return
        if self._device_name_exists(name):
            QMessageBox.warning(self, "خطا", "این نام دستگاه قبلا ثبت شده است.")
            return

        selected_type = type_selector.currentData()
        if not isinstance(selected_type, str):
            QMessageBox.warning(self, "خطا", "نوع دستگاه نامعتبر است.")
            return

        self._devices_for_current_user().append({"name": name, "type": selected_type})
        if not self._persist_devices():
            self._devices_for_current_user().pop()
            return
        self._refresh_table()

    def _display_type(self, type_code: str | None) -> str:
        normalized = type_code if type_code in DEVICE_TYPE_LABELS else "scanner"
        return DEVICE_TYPE_LABELS[normalized]

    def _device_name_exists(self, name: str, ignore_index: int = -1) -> bool:
        for index, device in enumerate(self._devices_for_current_user()):
            if index == ignore_index:
                continue
            if device["name"] == name:
                return True
        return False

    def _start_row_edit(self, row: int) -> None:
        if self._editing_row is not None and self._editing_row != row:
            QMessageBox.information(
                self,
                "ویرایش فعال",
                "ابتدا ویرایش ردیف فعلی را تایید کنید، سپس ردیف بعدی را ویرایش کنید.",
            )
            return
        self._editing_row = row
        editor = QLineEdit(self._devices_for_current_user()[row]["name"])
        self.devices_table.setCellWidget(row, 0, editor)
        self._toggle_row_actions(row, editing=True)

    def _confirm_row_edit(self, row: int) -> None:
        editor = self.devices_table.cellWidget(row, 0)
        if not isinstance(editor, QLineEdit):
            return

        new_name = editor.text().strip()
        if not new_name:
            QMessageBox.warning(self, "خطا", "نام دستگاه الزامی است.")
            return
        if self._device_name_exists(new_name, ignore_index=row):
            QMessageBox.warning(self, "خطا", "این نام دستگاه قبلا ثبت شده است.")
            return

        previous = dict(self._devices_for_current_user()[row])
        self._devices_for_current_user()[row] = {
            "name": new_name,
            "type": previous.get("type", "scanner"),
        }
        if not self._persist_devices():
            self._devices_for_current_user()[row] = previous
            self._editing_row = None
            self._refresh_table()
            return

        self.devices_table.removeCellWidget(row, 0)
        item = QTableWidgetItem(new_name)
        item.setTextAlignment(Qt.AlignCenter)
        self.devices_table.setItem(row, 0, item)
        self._toggle_row_actions(row, editing=False)
        self._editing_row = None

    def _toggle_row_actions(self, row: int, editing: bool) -> None:
        actions_container = self.devices_table.cellWidget(row, 2)
        if actions_container is None:
            return

        edit_button = actions_container.property("edit_button")
        delete_button = actions_container.property("delete_button")
        confirm_button = actions_container.property("confirm_button")
        if isinstance(edit_button, QPushButton):
            edit_button.setVisible(not editing)
        if isinstance(delete_button, QPushButton):
            delete_button.setVisible(not editing)
        if isinstance(confirm_button, QPushButton):
            confirm_button.setVisible(editing)

    def _confirm_delete_row(self, row: int) -> None:
        device_name = self._devices_for_current_user()[row]["name"]
        modal = QMessageBox(self)
        modal.setIcon(QMessageBox.Warning)
        modal.setWindowTitle("حذف دستگاه")
        modal.setText(f"آیا از حذف دستگاه «{device_name}» مطمئن هستید؟")
        modal.setInformativeText("پس از تایید، دستگاه از لیست حذف و ذخیره می‌شود.")
        confirm_button = modal.addButton("تایید حذف", QMessageBox.AcceptRole)
        modal.addButton("لغو", QMessageBox.RejectRole)
        modal.exec()
        if modal.clickedButton() is not confirm_button:
            return

        removed = self._devices_for_current_user()[row]
        del self._devices_for_current_user()[row]
        if not self._persist_devices():
            self._devices_for_current_user().insert(row, removed)
            self._refresh_table()
            return

        self._editing_row = None
        self._refresh_table()

    def _persist_devices(self) -> bool:
        existing_users = set(self._load_managed_users())
        cleaned_data: dict[str, list[dict[str, str]]] = {}
        for username, devices in self._devices_by_user.items():
            if username in existing_users:
                cleaned_data[username] = devices

        if save_devices_by_user(cleaned_data):
            self._devices_by_user = cleaned_data
            return True

        QMessageBox.critical(self, "خطا", "ذخیره دستگاه‌ها انجام نشد. دوباره تلاش کنید.")
        return False
