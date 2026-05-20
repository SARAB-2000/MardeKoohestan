from __future__ import annotations

import json
import math
import uuid
from typing import Any

from PySide6.QtCore import Qt, QDateTime
from PySide6.QtWidgets import (
    QDateTimeEdit,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from user_store import (
    get_product_structure_by_user,
    get_product_structures,
    get_products_by_user,
    save_products_by_user,
)
from ui.widgets.styled_combo_field import StyledComboField


def _normalize_field_type(raw: object) -> str:
    return str(raw).strip().lower()


def _field_unique_flag(raw: object) -> bool:
    return raw is True or str(raw).strip().lower() in {"true", "1", "yes"}


def _value_present_for_unique(ft: str, value: object) -> bool:
    if value is None:
        return False
    if ft == "text":
        return str(value).strip() != ""
    if ft == "number":
        if isinstance(value, bool):
            return False
        return True
    if ft == "boolean":
        return True
    if ft == "datetime":
        return str(value).strip() != ""
    if ft == "dictionary":
        return isinstance(value, dict) and len(value) > 0
    if ft == "list":
        return isinstance(value, list) and len(value) > 0
    return str(value).strip() != ""


def _normalize_number_for_unique(value: object) -> int | float:
    x = float(value)
    if math.isfinite(x) and math.isclose(x, round(x), rel_tol=0.0, abs_tol=1e-9):
        return int(round(x))
    return x


def _canonical_unique_token(ft: str, value: object) -> object | None:
    if not _value_present_for_unique(ft, value):
        return None
    if ft == "text":
        return ("t", str(value).strip())
    if ft == "number":
        if isinstance(value, bool):
            return None
        return ("n", _normalize_number_for_unique(value))
    if ft == "boolean":
        return ("b", bool(value))
    if ft == "datetime":
        return ("d", str(value).strip())
    if ft == "dictionary":
        if not isinstance(value, dict):
            return None
        try:
            return ("j", json.dumps(value, sort_keys=True, ensure_ascii=False))
        except TypeError:
            return ("j", str(value))
    if ft == "list":
        if not isinstance(value, list):
            return None
        try:
            return ("j", json.dumps(value, sort_keys=True, ensure_ascii=False))
        except TypeError:
            return ("j", str(value))
    return ("t", str(value).strip())


def _format_value_for_cell(field_type: str, value: object) -> str:
    ft = _normalize_field_type(field_type)
    if ft == "boolean":
        if value is True or value == "true" or value == "1":
            return "بله"
        if value is False or value == "false" or value == "0":
            return "خیر"
        return ""
    if ft == "dictionary":
        if isinstance(value, dict):
            try:
                s = json.dumps(value, ensure_ascii=False)
            except TypeError:
                s = str(value)
            return s if len(s) <= 120 else s[:117] + "…"
        return str(value) if value is not None else ""
    if ft == "list":
        if isinstance(value, list):
            try:
                s = json.dumps(value, ensure_ascii=False)
            except TypeError:
                s = str(value)
            return s if len(s) <= 120 else s[:117] + "…"
        return str(value) if value is not None else ""
    if ft == "number":
        if value is None:
            return ""
        if isinstance(value, bool):
            return ""
        if isinstance(value, (int, float)):
            return str(value)
        return str(value).strip() if value is not None else ""
    if ft == "datetime":
        return str(value).strip() if value is not None else ""
    return str(value) if value is not None else ""


class UserProductsPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._username = ""
        self._products_by_user: dict[str, list[dict[str, object]]] = get_products_by_user()
        self._structures = get_product_structures()
        self._structure_by_user = get_product_structure_by_user()
        self._field_defs: list[dict[str, str]] = []

        layout = QVBoxLayout()
        layout.setSpacing(12)

        top_row = QHBoxLayout()
        info_wrap = QWidget()
        info_layout = QVBoxLayout(info_wrap)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(4)
        self.structure_info_label = QLabel()
        self.structure_info_label.setObjectName("DialogSubtitle")
        self.total_count_label = QLabel()
        self.total_count_label.setObjectName("FormFieldLabel")
        info_layout.addWidget(self.structure_info_label)
        info_layout.addWidget(self.total_count_label)
        top_row.addWidget(info_wrap)
        top_row.addStretch()

        self.add_button = QPushButton("＋ افزودن محصول")
        self.add_button.setObjectName("AddUserButton")
        self.add_button.clicked.connect(self._open_add_product_dialog)
        top_row.addWidget(self.add_button)
        layout.addLayout(top_row)

        self.empty_structure_card = QFrame()
        self.empty_structure_card.setObjectName("EmptyStateCard")
        empty_structure_layout = QVBoxLayout()
        empty_structure_layout.setContentsMargins(18, 16, 18, 16)
        self.empty_structure_hint = QLabel(
            "برای حساب شما ساختار محصولی تعیین نشده است. مدیر باید از بخش مدیریت، ساختار را به شما اختصاص دهد."
        )
        self.empty_structure_hint.setObjectName("EmptyStateText")
        self.empty_structure_hint.setWordWrap(True)
        self.empty_structure_hint.setAlignment(Qt.AlignCenter)
        empty_structure_layout.addWidget(self.empty_structure_hint)
        self.empty_structure_card.setLayout(empty_structure_layout)
        layout.addWidget(self.empty_structure_card, alignment=Qt.AlignCenter)

        self.products_table = QTableWidget(0, 1)
        self.products_table.setObjectName("UsersTable")
        self.products_table.verticalHeader().setVisible(False)
        self.products_table.setAlternatingRowColors(True)
        self.products_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.products_table.setSelectionMode(QTableWidget.NoSelection)
        self.products_table.setFocusPolicy(Qt.NoFocus)
        self.products_table.verticalHeader().setDefaultSectionSize(48)
        layout.addWidget(self.products_table, 1)

        self.setLayout(layout)
        self._refresh_layout_visibility()

    def set_username(self, username: str | None) -> None:
        self._username = (username or "").strip()
        self._products_by_user = get_products_by_user()
        self._structures = get_product_structures()
        self._structure_by_user = get_product_structure_by_user()
        self._refresh_layout_visibility()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._products_by_user = get_products_by_user()
        self._structures = get_product_structures()
        self._structure_by_user = get_product_structure_by_user()
        self._refresh_layout_visibility()

    def _assigned_structure(self) -> dict[str, Any] | None:
        if not self._username:
            return None
        name = str(self._structure_by_user.get(self._username, "")).strip()
        if not name:
            return None
        for structure in self._structures:
            if str(structure.get("name", "")).strip() == name:
                return structure
        return None

    def _structure_field_defs(self) -> list[dict[str, Any]]:
        structure = self._assigned_structure()
        if not structure:
            return []
        raw_fields = structure.get("fields", [])
        defs: list[dict[str, Any]] = []
        if not isinstance(raw_fields, list):
            return defs
        seen: set[str] = set()
        for field in raw_fields:
            if not isinstance(field, dict):
                continue
            fname = str(field.get("name", "")).strip()
            ftype = _normalize_field_type(field.get("type", "text"))
            unique = _field_unique_flag(field.get("unique", False))
            if not fname:
                continue
            key = fname.casefold()
            if key in seen:
                continue
            seen.add(key)
            defs.append({"name": fname, "type": ftype, "unique": unique})
        return defs

    def _find_unique_field_conflict(
        self,
        values: dict[str, object],
        exclude_product_id: str | None,
    ) -> str | None:
        products = self._user_products()
        exclude_product_id = (exclude_product_id or "").strip()
        for fd in self._field_defs:
            if not fd.get("unique"):
                continue
            fname = str(fd.get("name", "")).strip()
            ft = _normalize_field_type(fd.get("type", "text"))
            new_tok = _canonical_unique_token(ft, values.get(fname))
            if new_tok is None:
                continue
            for product in products:
                pid = str(product.get("id", "")).strip()
                if exclude_product_id and pid == exclude_product_id:
                    continue
                pv = product.get("values", {})
                if not isinstance(pv, dict):
                    pv = {}
                old_tok = _canonical_unique_token(ft, pv.get(fname))
                if old_tok is None:
                    continue
                if old_tok == new_tok:
                    return fname
        return None

    def _user_products(self) -> list[dict[str, object]]:
        if not self._username:
            return []
        return self._products_by_user.setdefault(self._username, [])

    def _refresh_layout_visibility(self) -> None:
        self._field_defs = self._structure_field_defs()
        has_structure = bool(self._field_defs)
        self.empty_structure_card.setVisible(not has_structure)
        self.products_table.setVisible(has_structure)
        self.add_button.setVisible(has_structure)
        if not self._username:
            self.structure_info_label.setText("ابتدا وارد حساب کاربری شوید.")
            self.total_count_label.clear()
            self.total_count_label.setVisible(False)
            self.products_table.setRowCount(0)
            self.empty_structure_card.setVisible(False)
            self.products_table.setVisible(False)
            self.add_button.setVisible(False)
            return
        if not has_structure:
            self.structure_info_label.clear()
            self.total_count_label.clear()
            self.total_count_label.setVisible(False)
            self.products_table.setRowCount(0)
            return
        structure_name = str(self._assigned_structure().get("name", "") if self._assigned_structure() else "")
        products = self._user_products()
        self.structure_info_label.setText(f"ساختار محصول: {structure_name}")
        self.total_count_label.setVisible(True)
        self.total_count_label.setText(f"تعداد کل محصولات: {len(products)}")
        self._refresh_table()

    def _refresh_table(self) -> None:
        defs = self._field_defs
        col_count = len(defs) + 2
        self.products_table.setColumnCount(col_count)
        headers = ["ردیف"] + [d["name"] for d in defs] + ["عملیات"]
        self.products_table.setHorizontalHeaderLabels(headers)
        self.products_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for col in range(1, len(defs) + 1):
            self.products_table.horizontalHeader().setSectionResizeMode(col, QHeaderView.Stretch)
        self.products_table.horizontalHeader().setSectionResizeMode(
            col_count - 1, QHeaderView.ResizeToContents
        )

        products = self._user_products()
        self.products_table.setRowCount(0)
        for row_idx, product in enumerate(products):
            self.products_table.insertRow(row_idx)
            num_item = QTableWidgetItem(str(row_idx + 1))
            num_item.setTextAlignment(Qt.AlignCenter)
            self.products_table.setItem(row_idx, 0, num_item)
            values = product.get("values", {})
            if not isinstance(values, dict):
                values = {}
            for col, fd in enumerate(defs):
                fname = fd["name"]
                ftype = fd["type"]
                cell_text = _format_value_for_cell(ftype, values.get(fname))
                item = QTableWidgetItem(cell_text)
                item.setTextAlignment(Qt.AlignCenter)
                self.products_table.setItem(row_idx, col + 1, item)
            self._set_action_cell(row_idx)

    def _set_action_cell(self, row: int) -> None:
        actions_container = QWidget()
        actions_layout = QHBoxLayout()
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(6)

        edit_button = QPushButton("🖉")
        edit_button.setObjectName("RowIconButton")
        edit_button.setFlat(True)
        edit_button.setToolTip("ویرایش")
        edit_button.clicked.connect(lambda r=row: self._open_edit_product_dialog(r))

        delete_button = QPushButton("✖")
        delete_button.setObjectName("RowDangerIconButton")
        delete_button.setFlat(True)
        delete_button.setToolTip("حذف")
        delete_button.clicked.connect(lambda r=row: self._confirm_delete_product(r))

        actions_layout.addWidget(edit_button)
        actions_layout.addWidget(delete_button)
        actions_container.setLayout(actions_layout)
        actions_col = len(self._field_defs) + 1
        self.products_table.setCellWidget(row, actions_col, actions_container)

    def _persist(self) -> bool:
        if save_products_by_user(self._products_by_user):
            return True
        QMessageBox.critical(self, "خطا", "ذخیرهٔ محصولات انجام نشد. دوباره تلاش کنید.")
        return False

    def _open_add_product_dialog(self) -> None:
        result = self._show_product_dialog(title="افزودن محصول")
        if result is None:
            return
        self._user_products().append(result)
        if not self._persist():
            self._user_products().pop()
            return
        self._refresh_layout_visibility()

    def _open_edit_product_dialog(self, row: int) -> None:
        products = self._user_products()
        if row < 0 or row >= len(products):
            return
        initial = products[row]
        updated = self._show_product_dialog(title="ویرایش محصول", initial=initial)
        if updated is None:
            return
        previous = dict(initial)
        products[row] = updated
        if not self._persist():
            products[row] = previous
            return
        self._refresh_layout_visibility()

    def _confirm_delete_product(self, row: int) -> None:
        products = self._user_products()
        if row < 0 or row >= len(products):
            return
        modal = QMessageBox(self)
        modal.setIcon(QMessageBox.Warning)
        modal.setWindowTitle("حذف محصول")
        modal.setText("آیا از حذف این محصول مطمئن هستید؟")
        modal.setInformativeText("پس از تایید، ردیف از جدول حذف و ذخیره می‌شود.")
        confirm_button = modal.addButton("تایید حذف", QMessageBox.AcceptRole)
        modal.addButton("لغو", QMessageBox.RejectRole)
        modal.exec()
        if modal.clickedButton() is not confirm_button:
            return

        removed = products[row]
        del products[row]
        if not self._persist():
            products.insert(row, removed)
            self._refresh_layout_visibility()
            return
        self._refresh_layout_visibility()

    def _show_product_dialog(
        self,
        title: str,
        initial: dict[str, object] | None = None,
    ) -> dict[str, object] | None:
        dialog = QDialog(self)
        dialog.setObjectName("ProductDialog")
        dialog.setWindowTitle(title)
        dialog.setModal(True)
        dialog.setMinimumWidth(480)

        outer = QVBoxLayout(dialog)
        outer.setSpacing(10)

        scroll = QScrollArea()
        scroll.setObjectName("ProductFormScrollArea")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        form_host = QWidget()
        form_host.setObjectName("ProductFormScrollContent")
        form_layout = QVBoxLayout()
        form_layout.setSpacing(10)
        form_host.setLayout(form_layout)

        initial_values: dict[str, Any] = {}
        if initial and isinstance(initial.get("values"), dict):
            initial_values = dict(initial["values"])  # type: ignore[arg-type]

        editors: dict[str, tuple[str, QWidget]] = {}

        for fd in self._field_defs:
            fname = fd["name"]
            ftype = _normalize_field_type(fd["type"])
            label = QLabel(fname)
            label.setObjectName("FormFieldLabel")
            form_layout.addWidget(label)

            raw_val = initial_values.get(fname)

            if ftype == "text":
                w = QLineEdit()
                w.setPlaceholderText("متن")
                if raw_val is not None:
                    w.setText(str(raw_val))
                editors[fname] = (ftype, w)
                form_layout.addWidget(w)

            elif ftype == "number":
                w = QLineEdit()
                w.setPlaceholderText("عدد")
                if raw_val is not None and not isinstance(raw_val, bool):
                    w.setText(str(raw_val))
                editors[fname] = (ftype, w)
                form_layout.addWidget(w)

            elif ftype == "boolean":
                w_shell = StyledComboField()
                combo = w_shell.combo_box
                combo.addItem("خیر", False)
                combo.addItem("بله", True)
                if raw_val is True or raw_val == "true" or raw_val == "1" or raw_val == 1:
                    combo.setCurrentIndex(1)
                else:
                    combo.setCurrentIndex(0)
                editors[fname] = (ftype, w_shell)
                form_layout.addWidget(w_shell)

            elif ftype == "dictionary":
                w = QPlainTextEdit()
                w.setPlaceholderText('مثال: {"کلید": "مقدار"}')
                w.setFixedHeight(120)
                if isinstance(raw_val, dict):
                    try:
                        w.setPlainText(json.dumps(raw_val, ensure_ascii=False, indent=2))
                    except TypeError:
                        w.setPlainText(str(raw_val))
                elif raw_val is not None:
                    w.setPlainText(str(raw_val))
                editors[fname] = (ftype, w)
                form_layout.addWidget(w)

            elif ftype == "list":
                w = QPlainTextEdit()
                w.setPlaceholderText('مثال: ["آیتم۱", "آیتم۲"]')
                w.setFixedHeight(120)
                if isinstance(raw_val, list):
                    try:
                        w.setPlainText(json.dumps(raw_val, ensure_ascii=False, indent=2))
                    except TypeError:
                        w.setPlainText(str(raw_val))
                elif raw_val is not None:
                    w.setPlainText(str(raw_val))
                editors[fname] = (ftype, w)
                form_layout.addWidget(w)

            elif ftype == "datetime":
                w = QDateTimeEdit()
                w.setCalendarPopup(True)
                w.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
                parsed = False
                if raw_val is not None:
                    s = str(raw_val).strip()
                    if s:
                        for fmt in (
                            Qt.DateFormat.ISODateWithMs,
                            Qt.DateFormat.ISODate,
                        ):
                            qdt = QDateTime.fromString(s, fmt)
                            if qdt.isValid():
                                w.setDateTime(qdt)
                                parsed = True
                                break
                if not parsed:
                    w.setDateTime(QDateTime.currentDateTime())
                editors[fname] = (ftype, w)
                form_layout.addWidget(w)

            else:
                w = QLineEdit()
                w.setPlaceholderText("مقدار")
                if raw_val is not None:
                    w.setText(str(raw_val))
                editors[fname] = ("text", w)
                form_layout.addWidget(w)

        form_host.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)
        scroll.setWidget(form_host)
        outer.addWidget(scroll, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("تایید")
        buttons.button(QDialogButtonBox.Cancel).setText("لغو")
        outer.addWidget(buttons)
        buttons.rejected.connect(dialog.reject)

        result_holder: dict[str, object] = {}

        def accept_dialog() -> None:
            values: dict[str, object] = {}
            for fname, (ftype, widget) in editors.items():
                if ftype == "text":
                    assert isinstance(widget, QLineEdit)
                    values[fname] = widget.text().strip()
                elif ftype == "number":
                    assert isinstance(widget, QLineEdit)
                    text = widget.text().strip()
                    if not text:
                        values[fname] = None
                    else:
                        try:
                            if "." in text or "e" in text.lower():
                                values[fname] = float(text)
                            else:
                                values[fname] = int(text, 10)
                        except ValueError:
                            QMessageBox.warning(dialog, "خطا", f"فیلد «{fname}» باید عدد معتبر باشد.")
                            return
                elif ftype == "boolean":
                    assert isinstance(widget, StyledComboField)
                    data = widget.combo_box.currentData()
                    values[fname] = bool(data)
                elif ftype == "dictionary":
                    assert isinstance(widget, QPlainTextEdit)
                    raw_text = widget.toPlainText().strip()
                    if not raw_text:
                        values[fname] = {}
                    else:
                        try:
                            loaded = json.loads(raw_text)
                        except json.JSONDecodeError:
                            QMessageBox.warning(dialog, "خطا", f"فیلد «{fname}» باید JSON معتبر باشد.")
                            return
                        if not isinstance(loaded, dict):
                            QMessageBox.warning(dialog, "خطا", f"فیلد «{fname}» باید یک شیء JSON باشد.")
                            return
                        values[fname] = loaded
                elif ftype == "list":
                    assert isinstance(widget, QPlainTextEdit)
                    raw_text = widget.toPlainText().strip()
                    if not raw_text:
                        values[fname] = []
                    else:
                        try:
                            loaded = json.loads(raw_text)
                        except json.JSONDecodeError:
                            QMessageBox.warning(dialog, "خطا", f"فیلد «{fname}» باید JSON معتبر باشد.")
                            return
                        if not isinstance(loaded, list):
                            QMessageBox.warning(dialog, "خطا", f"فیلد «{fname}» باید آرایهٔ JSON باشد.")
                            return
                        values[fname] = loaded
                elif ftype == "datetime":
                    assert isinstance(widget, QDateTimeEdit)
                    values[fname] = widget.dateTime().toString(Qt.DateFormat.ISODateWithMs)
                else:
                    assert isinstance(widget, QLineEdit)
                    values[fname] = widget.text().strip()

            exclude_id = str(initial.get("id", "")).strip() if initial else ""
            conflict = self._find_unique_field_conflict(values, exclude_id or None)
            if conflict:
                QMessageBox.warning(
                    dialog,
                    "خطا",
                    f"مقدار فیلد یکتای «{conflict}» با محصول دیگری تکراری است.",
                )
                return

            pid = exclude_id or uuid.uuid4().hex
            result_holder["product"] = {"id": pid, "values": values}
            dialog.accept()

        buttons.accepted.connect(accept_dialog)

        if dialog.exec() != QDialog.Accepted:
            return None
        prod = result_holder.get("product")
        return prod if isinstance(prod, dict) else None
