from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
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

from user_store import get_allowed_users_limit, get_users, save_users
from settings import DEFAULT_ADMIN_USERNAME
from ui.widgets.styled_combo_field import StyledComboField

ROLE_LABELS: dict[str, str] = {"normal": "عادی", "admin": "ادمین"}


class UsersTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._users: list[dict[str, str]] = get_users()
        self._editing_row: int | None = None

        layout = QVBoxLayout()
        layout.setSpacing(12)

        top_row = QHBoxLayout()
        top_row.setSpacing(10)
        self.limit_label = QLabel()
        self.limit_label.setObjectName("DialogSubtitle")
        self.limit_label.setWordWrap(True)
        self.limit_label.setMinimumWidth(0)
        limit_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        limit_policy.setHeightForWidth(True)
        self.limit_label.setSizePolicy(limit_policy)
        top_row.addWidget(self.limit_label, 1)
        self.add_button = QPushButton("＋ افزودن کاربر")
        self.add_button.setObjectName("AddUserButton")
        self.add_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.add_button.clicked.connect(self._open_add_user_dialog)
        top_row.addWidget(self.add_button, 0, Qt.AlignTop)
        layout.addLayout(top_row)

        self.users_table = QTableWidget(0, 4)
        self.users_table.setObjectName("UsersTable")
        self.users_table.setHorizontalHeaderLabels(["نام کاربری", "رمز عبور", "دسترسی", "عملیات"])
        self.users_table.verticalHeader().setVisible(False)
        self.users_table.setAlternatingRowColors(True)
        self.users_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.users_table.setSelectionMode(QTableWidget.NoSelection)
        self.users_table.setFocusPolicy(Qt.NoFocus)
        self.users_table.verticalHeader().setDefaultSectionSize(48)
        self.users_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        header = self.users_table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setMinimumSectionSize(70)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        layout.addWidget(self.users_table, 1)

        self.setLayout(layout)
        self._refresh_table()
        self._update_limit_label()

    def _update_limit_label(self) -> None:
        limit = get_allowed_users_limit()
        managed_users_count = self._managed_users_count()
        self.limit_label.setText(
            f"حداکثر کاربران مجاز: {limit} | تعداد فعلی کاربران: {managed_users_count} (ادمین محاسبه نمی‌شود)"
        )

    def _refresh_table(self) -> None:
        self.users_table.setRowCount(0)
        for user in self._users:
            row = self.users_table.rowCount()
            self.users_table.insertRow(row)
            username_item = QTableWidgetItem(user["username"])
            username_item.setTextAlignment(Qt.AlignCenter)
            password_item = QTableWidgetItem("●●●●●●")
            password_item.setTextAlignment(Qt.AlignCenter)
            role_code = self._normalize_role(user.get("role"))
            role_item = QTableWidgetItem(ROLE_LABELS[role_code])
            role_item.setTextAlignment(Qt.AlignCenter)
            self.users_table.setItem(row, 0, username_item)
            self.users_table.setItem(row, 1, password_item)
            self.users_table.setItem(row, 2, role_item)
            self._set_action_cell(row)
        self._update_limit_label()

    def _normalize_role(self, role: str | None, username: str | None = None) -> str:
        clean_role = str(role or "").strip().lower()
        if clean_role in ROLE_LABELS:
            return clean_role
        if str(username or "").strip() == DEFAULT_ADMIN_USERNAME:
            return "admin"
        return "normal"

    def _username_exists(self, username: str, ignore_index: int = -1) -> bool:
        for index, user in enumerate(self._users):
            if index == ignore_index:
                continue
            if user["username"] == username:
                return True
        return False

    def _password_exists(self, password: str, ignore_index: int = -1) -> bool:
        for index, user in enumerate(self._users):
            if index == ignore_index:
                continue
            if user["password"] == password:
                return True
        return False

    def _is_admin_user(self, user: dict[str, str]) -> bool:
        return user.get("username", "").strip() == DEFAULT_ADMIN_USERNAME

    def _managed_users_count(self) -> int:
        return sum(1 for user in self._users if not self._is_admin_user(user))

    def _open_add_user_dialog(self) -> None:
        if self._managed_users_count() >= get_allowed_users_limit():
            QMessageBox.warning(
                self,
                "محدودیت کاربران",
                "تعداد کاربران به سقف مجاز رسیده است. ابتدا سقف را افزایش دهید.",
            )
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("افزودن کاربر جدید")
        dialog.setModal(True)
        dialog.resize(420, 180)

        dialog_layout = QVBoxLayout()
        username_input = QLineEdit()
        username_input.setPlaceholderText("نام کاربری")
        password_input = QLineEdit()
        password_input.setPlaceholderText("رمز عبور")
        password_input.setEchoMode(QLineEdit.Password)
        password_input.setLayoutDirection(Qt.LeftToRight)
        role_selector = StyledComboField()
        role_selector.setMinimumWidth(180)
        role_selector.combo_box.addItem(ROLE_LABELS["normal"], "normal")
        role_selector.combo_box.addItem(ROLE_LABELS["admin"], "admin")
        role_selector.combo_box.setCurrentIndex(0)
        dialog_layout.addWidget(username_input)
        dialog_layout.addWidget(password_input)
        dialog_layout.addWidget(role_selector)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("تایید")
        buttons.button(QDialogButtonBox.Cancel).setText("لغو")
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        dialog_layout.addWidget(buttons)
        dialog.setLayout(dialog_layout)

        if dialog.exec() != QDialog.Accepted:
            return

        username = username_input.text().strip()
        password = password_input.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "خطا", "نام کاربری و رمز عبور الزامی است.")
            return
        if self._username_exists(username):
            QMessageBox.warning(self, "خطا", "این نام کاربری قبلا ثبت شده است.")
            return
        if self._password_exists(password):
            QMessageBox.warning(self, "خطا", "این رمز عبور قبلا برای کاربر دیگری ثبت شده است.")
            return
        role_code = role_selector.combo_box.currentData()
        if not isinstance(role_code, str):
            role_code = "normal"

        new_users = [*self._users, {"username": username, "password": password, "role": role_code}]
        self._commit_users(new_users, success_message="کاربر جدید با موفقیت ثبت شد.")

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
        self.users_table.setCellWidget(row, 3, actions_container)

    def _start_row_edit(self, row: int) -> None:
        if self._editing_row is not None and self._editing_row != row:
            QMessageBox.information(
                self,
                "ویرایش فعال",
                "ابتدا ویرایش ردیف فعلی را تایید کنید، سپس ردیف بعدی را ویرایش کنید.",
            )
            return

        self._editing_row = row
        username_editor = QLineEdit(self._users[row]["username"])
        password_editor = QLineEdit(self._users[row]["password"])
        password_editor.setLayoutDirection(Qt.LeftToRight)
        role_selector = StyledComboField()
        role_selector.setMinimumWidth(0)
        role_selector.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        role_selector.combo_box.addItem(ROLE_LABELS["normal"], "normal")
        role_selector.combo_box.addItem(ROLE_LABELS["admin"], "admin")
        role_selector.combo_box.setCurrentText(
            ROLE_LABELS[self._normalize_role(self._users[row].get("role"), self._users[row].get("username"))]
        )
        self.users_table.setCellWidget(row, 0, username_editor)
        self.users_table.setCellWidget(row, 1, password_editor)
        self.users_table.setCellWidget(row, 2, role_selector)
        self._toggle_row_actions(row, editing=True)

    def _confirm_row_edit(self, row: int) -> None:
        username_editor = self.users_table.cellWidget(row, 0)
        password_editor = self.users_table.cellWidget(row, 1)
        role_selector = self.users_table.cellWidget(row, 2)
        if (
            not isinstance(username_editor, QLineEdit)
            or not isinstance(password_editor, QLineEdit)
            or not isinstance(role_selector, StyledComboField)
        ):
            return

        username = username_editor.text().strip()
        password = password_editor.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "خطا", "نام کاربری و رمز عبور الزامی است.")
            return
        if self._username_exists(username, ignore_index=row):
            QMessageBox.warning(self, "خطا", "این نام کاربری قبلا ثبت شده است.")
            return
        if self._password_exists(password, ignore_index=row):
            QMessageBox.warning(self, "خطا", "این رمز عبور قبلا برای کاربر دیگری ثبت شده است.")
            return
        role_code = role_selector.combo_box.currentData()
        if not isinstance(role_code, str):
            role_code = "normal"
        if username == DEFAULT_ADMIN_USERNAME:
            role_code = "admin"

        new_users = [*self._users]
        new_users[row] = {"username": username, "password": password, "role": role_code}
        if not self._commit_users(new_users, success_message="تغییرات کاربر با موفقیت ثبت شد."):
            return

        self._editing_row = None

    def _toggle_row_actions(self, row: int, editing: bool) -> None:
        actions_container = self.users_table.cellWidget(row, 3)
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
        if self._is_admin_user(self._users[row]):
            QMessageBox.information(
                self,
                "حذف کاربر",
                "حذف کاربر ادمین مجاز نیست.",
            )
            return

        username = self._users[row]["username"]
        modal = QMessageBox(self)
        modal.setIcon(QMessageBox.Warning)
        modal.setWindowTitle("حذف کاربر")
        modal.setText(f"آیا از حذف کاربر «{username}» مطمئن هستید؟")
        confirm_button = modal.addButton("تایید حذف", QMessageBox.AcceptRole)
        modal.addButton("لغو", QMessageBox.RejectRole)
        modal.exec()
        if modal.clickedButton() is not confirm_button:
            return

        new_users = [*self._users]
        del new_users[row]
        if not self._commit_users(new_users, success_message="کاربر با موفقیت حذف شد."):
            return
        self._editing_row = None

    def _commit_users(self, users: list[dict[str, str]], success_message: str | None = None) -> bool:
        managed_users_count = sum(
            1
            for user in users
            if user.get("username", "").strip() != DEFAULT_ADMIN_USERNAME
        )
        if managed_users_count > get_allowed_users_limit():
            QMessageBox.warning(
                self,
                "خطا",
                "تعداد کاربران بیشتر از سقف مجاز است. ابتدا سقف را افزایش دهید یا کاربران را کم کنید.",
            )
            return False

        if not save_users(users):
            QMessageBox.critical(self, "خطا", "ذخیره کاربران انجام نشد. دوباره تلاش کنید.")
            return False

        normalized_users: list[dict[str, str]] = []
        for user in users:
            username = str(user.get("username", "")).strip()
            role = self._normalize_role(user.get("role"), username)
            if username == DEFAULT_ADMIN_USERNAME:
                role = "admin"
            normalized_users.append(
                {"username": username, "password": str(user.get("password", "")), "role": role}
            )

        self._users = normalized_users
        self._editing_row = None
        self._refresh_table()
        if success_message:
            QMessageBox.information(self, "کاربران", success_message)
        return True
