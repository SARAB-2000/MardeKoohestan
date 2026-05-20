from __future__ import annotations

import html

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QHeaderView,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from settings import DEFAULT_ADMIN_USERNAME
from user_store import (
    get_product_scan_detail_fields_by_user,
    get_product_structure_by_user,
    get_product_structures,
    get_users,
    save_product_scan_detail_fields_by_user,
    save_product_structure_by_user,
    save_product_structures,
)
from ui.widgets.styled_combo_field import StyledComboField

_DEFAULT_FIELD_TYPES = [
    "text",
    "number",
    "boolean",
    "dictionary",
    "list",
    "datetime",
]


def _rich_paragraph_rtl_right(plain: str) -> str:
    """متن ساده را برای QLabel با RichText راست‌چین و rtl (مثل دیالوگ جزئیات اسکن) برمی‌گرداند."""
    return (
        '<p dir="rtl" align="right" style="margin: 0;">'
        f"{html.escape(plain.strip())}"
        "</p>"
    )


class ProductsTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._structures: list[dict[str, object]] = get_product_structures()
        self._structure_by_user: dict[str, str] = get_product_structure_by_user()
        self._scan_detail_fields_by_user: dict[str, list[dict[str, object]]] = (
            get_product_scan_detail_fields_by_user()
        )
        self._managed_users: list[str] = self._load_managed_users()
        self._assignment_updating = False

        layout = QVBoxLayout()
        layout.setSpacing(12)

        self.products_tabs = QTabWidget()
        self.products_tabs.setObjectName("ManagementTabs")
        layout.addWidget(self.products_tabs, 1)

        structures_page = QWidget()
        structures_layout = QVBoxLayout()
        structures_layout.setSpacing(12)

        top_row = QHBoxLayout()
        self.status_label = QLabel()
        self.status_label.setObjectName("DialogSubtitle")
        self.status_label.setWordWrap(True)
        self.status_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        top_row.addWidget(self.status_label, 1)
        top_row.addStretch()

        self.add_button = QPushButton("＋ افزودن ساختار")
        self.add_button.setObjectName("AddUserButton")
        self.add_button.clicked.connect(self._open_add_structure_dialog)
        top_row.addWidget(self.add_button)
        structures_layout.addLayout(top_row)

        self.structures_table = QTableWidget(0, 3)
        self.structures_table.setObjectName("UsersTable")
        self.structures_table.setHorizontalHeaderLabels(["نام ساختار", "فیلدها", "عملیات"])
        self.structures_table.verticalHeader().setVisible(False)
        self.structures_table.setAlternatingRowColors(True)
        self.structures_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.structures_table.setSelectionMode(QTableWidget.NoSelection)
        self.structures_table.setFocusPolicy(Qt.NoFocus)
        self.structures_table.verticalHeader().setDefaultSectionSize(48)
        self.structures_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.structures_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.structures_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        structures_layout.addWidget(self.structures_table, 1)
        structures_page.setLayout(structures_layout)
        self.products_tabs.addTab(structures_page, "ساختارها")

        assignment_page = QWidget()
        assignment_layout = QVBoxLayout()
        assignment_layout.setSpacing(12)

        assignment_hint = QLabel(
            "هر کاربر فقط می‌تواند یک ساختار داشته باشد. پس از انتخاب ساختار، می‌توانید مشخص کنید "
            "کدام فیلدها در ستون «جزئیات» جدول نتیجهٔ اسکن در صفحهٔ خانهٔ همان کاربر نمایش داده شوند."
        )
        assignment_hint.setObjectName("DialogSubtitle")
        assignment_hint.setWordWrap(True)
        assignment_layout.addWidget(assignment_hint)

        self.assignment_table = QTableWidget(0, 3)
        self.assignment_table.setObjectName("UsersTable")
        self.assignment_table.setHorizontalHeaderLabels(
            ["کاربر", "ساختار محصول", "فیلدهای جزئیات اسکن"]
        )
        self.assignment_table.verticalHeader().setVisible(False)
        self.assignment_table.setAlternatingRowColors(True)
        self.assignment_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.assignment_table.setSelectionMode(QTableWidget.NoSelection)
        self.assignment_table.setFocusPolicy(Qt.NoFocus)
        self.assignment_table.verticalHeader().setDefaultSectionSize(48)
        self.assignment_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.assignment_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.assignment_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        assignment_layout.addWidget(self.assignment_table, 1)
        assignment_page.setLayout(assignment_layout)
        self.products_tabs.addTab(assignment_page, "اختصاص به کاربران")

        self.setLayout(layout)
        self._refresh_table()
        self._refresh_assignment_table()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._managed_users = self._load_managed_users()
        self._structures = get_product_structures()
        self._structure_by_user = get_product_structure_by_user()
        self._scan_detail_fields_by_user = get_product_scan_detail_fields_by_user()
        self._refresh_table()
        self._refresh_assignment_table()

    def _create_type_selector_shell(self, field_type: str) -> StyledComboField:
        selector = StyledComboField()
        field_type_combo = selector.combo_box
        for option in _DEFAULT_FIELD_TYPES:
            field_type_combo.addItem(option)
        field_type_combo.setEditable(True)
        field_type_combo.setCurrentText(field_type)
        return selector

    def _create_unique_selector_shell(self, unique: bool) -> StyledComboField:
        selector = StyledComboField()
        selector.setMinimumWidth(0)
        selector.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        combo = selector.combo_box
        combo.setMinimumContentsLength(8)
        combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        combo.addItem("خیر", False)
        combo.addItem("بله", True)
        combo.setCurrentIndex(1 if unique else 0)
        combo.setMinimumContentsLength(6)
        combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        view = combo.view()
        view.setMinimumWidth(200)
        selector.setMinimumWidth(220)
        return selector

    def _refresh_table(self) -> None:
        self.structures_table.setRowCount(0)
        self.status_label.setText(
            f"تعداد ساختارهای محصول: {len(self._structures)} | تعداد کاربران قابل‌اختصاص: {len(self._managed_users)}"
        )

        for structure in self._structures:
            row = self.structures_table.rowCount()
            self.structures_table.insertRow(row)

            name = str(structure.get("name", "")).strip()
            fields = structure.get("fields", [])
            field_count = len(fields) if isinstance(fields, list) else 0
            unique_ct = 0
            if isinstance(fields, list):
                for f in fields:
                    if not isinstance(f, dict):
                        continue
                    ur = f.get("unique", False)
                    if ur is True or str(ur).strip().lower() in {"true", "1", "yes"}:
                        unique_ct += 1

            name_item = QTableWidgetItem(name)
            name_item.setTextAlignment(Qt.AlignCenter)
            fields_summary = f"{field_count} فیلد"
            if unique_ct:
                fields_summary += f" ({unique_ct} یکتا)"
            fields_item = QTableWidgetItem(fields_summary)
            fields_item.setTextAlignment(Qt.AlignCenter)

            self.structures_table.setItem(row, 0, name_item)
            self.structures_table.setItem(row, 1, fields_item)
            self._set_action_cell(row)

    def _load_managed_users(self) -> list[str]:
        return [
            user["username"]
            for user in get_users()
            if user["username"].strip() != DEFAULT_ADMIN_USERNAME
        ]

    def _refresh_assignment_table(self) -> None:
        self._assignment_updating = True
        self.assignment_table.setRowCount(0)

        structure_names = [
            str(item.get("name", "")).strip()
            for item in self._structures
            if str(item.get("name", "")).strip()
        ]

        valid_assignments: dict[str, str] = {}
        for username, structure_name in self._structure_by_user.items():
            if username in self._managed_users and structure_name in structure_names:
                valid_assignments[username] = structure_name
        self._structure_by_user = valid_assignments

        for username in self._managed_users:
            row = self.assignment_table.rowCount()
            self.assignment_table.insertRow(row)

            user_item = QTableWidgetItem(username)
            user_item.setTextAlignment(Qt.AlignCenter)
            self.assignment_table.setItem(row, 0, user_item)

            selector_shell = self._create_structure_selector_shell(username, structure_names)
            self.assignment_table.setCellWidget(row, 1, selector_shell)

            wrap = QWidget()
            wrap_l = QHBoxLayout(wrap)
            wrap_l.setContentsMargins(4, 0, 4, 0)
            wrap_l.setSpacing(0)
            wrap_l.addStretch(1)

            details_btn = QPushButton("انتخاب فیلدها")
            details_btn.setObjectName("ScanDetailPickButton")
            details_btn.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
            struct_for_user = self._structure_by_user.get(username, "")
            details_btn.setEnabled(bool(self._structure_field_names(struct_for_user)))
            details_btn.setToolTip(
                "مشخص کنید کدام فیلدهای ساختار در ستون «جزئیات» جدول نتیجهٔ اسکن "
                "(صفحهٔ خانهٔ این کاربر) دیده شوند."
            )
            details_btn.clicked.connect(
                lambda _checked=False, un=username: self._open_scan_detail_fields_dialog(un)
            )
            wrap_l.addWidget(details_btn, 0, Qt.AlignVCenter)
            wrap_l.addStretch(1)
            self.assignment_table.setCellWidget(row, 2, wrap)

        self._assignment_updating = False
        self._normalize_scan_detail_fields_by_user()
        self._save_scan_detail_fields_silently()
        self._save_assignments_silently()

    def _structure_field_names(self, structure_name: str) -> list[str]:
        name = str(structure_name).strip()
        if not name:
            return []
        for st in self._structures:
            if str(st.get("name", "")).strip() != name:
                continue
            fields = st.get("fields", [])
            out: list[str] = []
            if isinstance(fields, list):
                for f in fields:
                    if isinstance(f, dict):
                        fn = str(f.get("name", "")).strip()
                        if fn:
                            out.append(fn)
            return out
        return []

    def _normalize_scan_detail_fields_by_user(self) -> None:
        managed = set(self._managed_users)
        for username in list(self._scan_detail_fields_by_user.keys()):
            if username not in managed:
                self._scan_detail_fields_by_user.pop(username, None)
                continue
            struct_name = self._structure_by_user.get(username, "")
            order = self._structure_field_names(struct_name)
            if not order:
                self._scan_detail_fields_by_user.pop(username, None)
                continue
            saved_raw = self._scan_detail_fields_by_user.get(username, [])
            if not isinstance(saved_raw, list):
                self._scan_detail_fields_by_user.pop(username, None)
                continue

            parsed_map: dict[str, bool] = {}
            for item in saved_raw:
                if isinstance(item, str):
                    name = item.strip()
                    if name:
                        parsed_map[name.casefold()] = True
                    continue
                if not isinstance(item, dict):
                    continue
                name = str(item.get("name", "")).strip()
                if not name:
                    continue
                raw_show = item.get("show_name", True)
                show_name = raw_show is True or str(raw_show).strip().lower() in {"true", "1", "yes"}
                parsed_map[name.casefold()] = show_name

            normalized_entries: list[dict[str, object]] = []
            for field_name in order:
                key = field_name.casefold()
                if key not in parsed_map:
                    continue
                normalized_entries.append({"name": field_name, "show_name": bool(parsed_map[key])})

            # پیش‌فرض: اگر همهٔ فیلدها انتخاب شده باشند و نمایش نام برای همه روشن باشد، تنظیم ذخیره نمی‌شود.
            if (
                len(normalized_entries) == len(order)
                and all(bool(item.get("show_name", True)) for item in normalized_entries)
            ):
                self._scan_detail_fields_by_user.pop(username, None)
            else:
                # لیست خالیِ صریح یعنی «هیچ فیلدی نمایش داده نشود».
                self._scan_detail_fields_by_user[username] = normalized_entries

    def _save_scan_detail_fields_silently(self) -> None:
        save_product_scan_detail_fields_by_user(self._scan_detail_fields_by_user)

    def _open_scan_detail_fields_dialog(self, username: str) -> None:
        struct_name = self._structure_by_user.get(username, "")
        field_names = self._structure_field_names(struct_name)
        if not field_names:
            QMessageBox.information(
                self,
                "جزئیات اسکن",
                "برای این کاربر ابتدا ساختاری با حداقل یک فیلد انتخاب کنید.",
            )
            return

        dialog = QDialog(self)
        dialog.setObjectName("ScanDetailFieldsDialog")
        dialog.setLayoutDirection(Qt.RightToLeft)
        dialog.setWindowTitle(f"فیلدهای جزئیات اسکن — {username}")
        dialog.setModal(True)
        dialog.resize(440, 400)

        root = QVBoxLayout(dialog)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(14)

        _intro_plain = (
            "فیلدهایی که با دکمهٔ مربع کنار نام‌شان علامت ✓ می‌گیرند در ستون «جزئیات» جدول نتیجهٔ اسکن "
            "در صفحهٔ خانهٔ این کاربر نمایش داده می‌شوند. دکمهٔ کنار هر فیلد مشخص می‌کند نمایش به‌صورت "
            "«نام فیلد: مقدار» باشد یا فقط «مقدار». اگر همهٔ فیلدها را انتخاب کنید و حالت نام برای همه روشن باشد، "
            "رفتار پیش‌فرض (همهٔ فیلدها با نام) اعمال می‌شود."
        )
        intro = QLabel()
        intro.setObjectName("DialogSubtitle")
        intro.setTextFormat(Qt.TextFormat.RichText)
        intro.setText(_rich_paragraph_rtl_right(_intro_plain))
        intro.setWordWrap(True)
        intro.setOpenExternalLinks(False)
        intro.setLayoutDirection(Qt.RightToLeft)
        root.addWidget(intro)

        scroll = QScrollArea()
        scroll.setObjectName("ScanDetailFieldsScroll")
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        inner = QWidget()
        inner.setObjectName("ScanDetailFieldsInner")
        inner.setLayoutDirection(Qt.LeftToRight)
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(12, 12, 12, 12)
        inner_layout.setSpacing(8)

        saved = self._scan_detail_fields_by_user.get(username)
        saved_map: dict[str, bool] | None = None
        if isinstance(saved, list):
            saved_map = {}
            for item in saved:
                if isinstance(item, str):
                    name = item.strip()
                    if name:
                        saved_map[name.casefold()] = True
                    continue
                if not isinstance(item, dict):
                    continue
                name = str(item.get("name", "")).strip()
                if not name:
                    continue
                raw_show = item.get("show_name", True)
                show_name = raw_show is True or str(raw_show).strip().lower() in {"true", "1", "yes"}
                saved_map[name.casefold()] = show_name

        toggles: dict[str, QPushButton] = {}
        name_toggles: dict[str, QPushButton] = {}
        for fname in field_names:
            row = QFrame()
            row.setObjectName("ScanDetailFieldRow")
            row.setLayoutDirection(Qt.LeftToRight)
            hl = QHBoxLayout(row)
            hl.setContentsMargins(8, 6, 8, 6)
            hl.setSpacing(8)

            name_lbl = QLabel()
            name_lbl.setObjectName("FormFieldLabel")
            name_lbl.setTextFormat(Qt.TextFormat.RichText)
            name_lbl.setText(_rich_paragraph_rtl_right(fname))
            name_lbl.setWordWrap(True)
            name_lbl.setOpenExternalLinks(False)
            name_lbl.setLayoutDirection(Qt.RightToLeft)
            name_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

            toggle = QPushButton()
            toggle.setObjectName("ScanDetailFieldToggle")
            toggle.setLayoutDirection(Qt.LeftToRight)
            toggle.setCheckable(True)
            toggle.setCursor(Qt.PointingHandCursor)
            toggle.setAutoDefault(False)
            toggle.setDefault(False)

            mode_btn = QPushButton()
            mode_btn.setObjectName("ScanDetailModeToggle")
            mode_btn.setCheckable(True)
            mode_btn.setCursor(Qt.PointingHandCursor)
            mode_btn.setAutoDefault(False)
            mode_btn.setDefault(False)
            mode_btn.setToolTip("روشن: نام فیلد + مقدار | خاموش: فقط مقدار")

            def _sync_toggle_mark(_checked: bool, b: QPushButton = toggle) -> None:
                b.setText("✓" if b.isChecked() else "")

            initial_on = True
            initial_show_name = True
            if saved_map is not None:
                key = fname.casefold()
                initial_on = key in saved_map
                if initial_on:
                    initial_show_name = bool(saved_map[key])

            def _sync_mode_btn_text(_checked: bool, b: QPushButton = mode_btn) -> None:
                b.setText("نام+مقدار" if b.isChecked() else "فقط مقدار")

            toggle.setChecked(initial_on)
            _sync_toggle_mark(initial_on)
            toggle.toggled.connect(_sync_toggle_mark)
            mode_btn.setChecked(initial_show_name)
            _sync_mode_btn_text(initial_show_name)
            mode_btn.toggled.connect(_sync_mode_btn_text)
            mode_btn.setEnabled(initial_on)
            toggle.toggled.connect(mode_btn.setEnabled)

            hl.addWidget(name_lbl, 1)
            hl.addWidget(mode_btn, 0, Qt.AlignVCenter)
            hl.addWidget(toggle, 0, Qt.AlignVCenter)
            inner_layout.addWidget(row)
            toggles[fname] = toggle
            name_toggles[fname] = mode_btn
        inner_layout.addStretch()
        scroll.setWidget(inner)
        root.addWidget(scroll, 1)

        presets = QHBoxLayout()
        presets.setSpacing(10)
        select_all_btn = QPushButton("انتخاب همه")
        select_all_btn.setObjectName("ScanDetailPresetAll")
        select_none_btn = QPushButton("پاک‌کردن انتخاب‌ها")
        select_none_btn.setObjectName("ScanDetailPresetNone")
        presets.addWidget(select_all_btn)
        presets.addWidget(select_none_btn)
        presets.addStretch()
        root.addLayout(presets)

        def select_all() -> None:
            for t in toggles.values():
                t.setChecked(True)
            for m in name_toggles.values():
                m.setChecked(True)

        def select_none() -> None:
            for t in toggles.values():
                t.setChecked(False)

        select_all_btn.clicked.connect(select_all)
        select_none_btn.clicked.connect(select_none)

        footer_host = QWidget()
        footer_host.setLayoutDirection(Qt.RightToLeft)
        footer = QHBoxLayout(footer_host)
        footer.setSpacing(12)
        ok_btn = QPushButton("تایید")
        ok_btn.setObjectName("PrimaryButton")
        ok_btn.setAutoDefault(True)
        ok_btn.setDefault(True)
        ok_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn = QPushButton("لغو")
        cancel_btn.setObjectName("SecondaryButton")
        cancel_btn.setAutoDefault(False)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        footer.addWidget(ok_btn)
        footer.addWidget(cancel_btn)
        footer.addStretch(1)
        root.addWidget(footer_host)

        def on_ok() -> None:
            picked_entries: list[dict[str, object]] = []
            for n in field_names:
                if not toggles[n].isChecked():
                    continue
                picked_entries.append({"name": n, "show_name": bool(name_toggles[n].isChecked())})
            if (
                len(picked_entries) == len(field_names)
                and all(bool(item.get("show_name", True)) for item in picked_entries)
            ):
                self._scan_detail_fields_by_user.pop(username, None)
            else:
                self._scan_detail_fields_by_user[username] = picked_entries
            self._save_scan_detail_fields_silently()
            dialog.accept()

        ok_btn.clicked.connect(on_ok)
        cancel_btn.clicked.connect(dialog.reject)
        dialog.exec()

    def _create_structure_selector_shell(
        self, username: str, structure_names: list[str]
    ) -> StyledComboField:
        selector = StyledComboField()
        combo = selector.combo_box
        selector.setProperty("username", username)
        selector.currentIndexChanged.connect(self._on_assignment_changed)

        for structure_name in structure_names:
            combo.addItem(structure_name, structure_name)

        current = self._structure_by_user.get(username, "")
        if current in structure_names:
            combo.setCurrentText(current)
        elif structure_names:
            combo.setCurrentIndex(0)
            selected = combo.currentData()
            if isinstance(selected, str) and selected:
                self._structure_by_user[username] = selected

        combo.setEnabled(bool(structure_names))
        if not structure_names:
            combo.setEditable(True)
            combo.setCurrentText("ساختاری تعریف نشده است")
            combo.lineEdit().setReadOnly(True)
        return selector

    def _on_assignment_changed(self) -> None:
        if self._assignment_updating:
            return
        selector = self.sender()
        if not isinstance(selector, StyledComboField):
            return
        username = selector.property("username")
        if not isinstance(username, str) or not username:
            return
        prev_structure = self._structure_by_user.get(username)
        selected = selector.combo_box.currentData()
        if isinstance(selected, str) and selected.strip():
            self._structure_by_user[username] = selected.strip()
        else:
            self._structure_by_user.pop(username, None)
        new_structure = self._structure_by_user.get(username)
        if prev_structure != new_structure:
            self._scan_detail_fields_by_user.pop(username, None)
            self._save_scan_detail_fields_silently()
        self._save_assignments_silently()
        self._update_scan_details_button_for_user(username)

    def _scan_detail_pick_button_at_row(self, row: int) -> QPushButton | None:
        cell = self.assignment_table.cellWidget(row, 2)
        if isinstance(cell, QPushButton):
            return cell
        if isinstance(cell, QWidget):
            lay = cell.layout()
            if lay is not None:
                for i in range(lay.count()):
                    item = lay.itemAt(i)
                    w = item.widget() if item is not None else None
                    if isinstance(w, QPushButton):
                        return w
        return None

    def _update_scan_details_button_for_user(self, username: str) -> None:
        for row in range(self.assignment_table.rowCount()):
            item = self.assignment_table.item(row, 0)
            if item is None or item.text() != username:
                continue
            btn = self._scan_detail_pick_button_at_row(row)
            if btn is not None:
                sn = self._structure_by_user.get(username, "")
                btn.setEnabled(bool(self._structure_field_names(sn)))
            break

    def _save_assignments_silently(self) -> None:
        save_product_structure_by_user(self._structure_by_user)

    def _set_action_cell(self, row: int) -> None:
        actions_container = QWidget()
        actions_layout = QHBoxLayout()
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(6)

        edit_button = QPushButton("🖉")
        edit_button.setObjectName("RowIconButton")
        edit_button.setFlat(True)
        edit_button.setToolTip("ویرایش")
        edit_button.clicked.connect(lambda: self._open_edit_structure_dialog(row))

        delete_button = QPushButton("✖")
        delete_button.setObjectName("RowDangerIconButton")
        delete_button.setFlat(True)
        delete_button.setToolTip("حذف")
        delete_button.clicked.connect(lambda: self._confirm_delete_structure(row))

        actions_layout.addWidget(edit_button)
        actions_layout.addWidget(delete_button)
        actions_container.setLayout(actions_layout)
        self.structures_table.setCellWidget(row, 2, actions_container)

    def _open_add_structure_dialog(self) -> None:
        structure = self._show_structure_dialog(title="افزودن ساختار محصول")
        if structure is None:
            return

        name = str(structure["name"])
        if self._structure_name_exists(name):
            QMessageBox.warning(self, "خطا", "این نام ساختار قبلا ثبت شده است.")
            return

        new_structures = [*self._structures, structure]
        self._commit_structures(new_structures, "ساختار محصول با موفقیت ثبت شد.")

    def _open_edit_structure_dialog(self, row: int) -> None:
        initial = self._structures[row]
        updated = self._show_structure_dialog(title="ویرایش ساختار محصول", initial=initial)
        if updated is None:
            return

        name = str(updated["name"])
        if self._structure_name_exists(name, ignore_index=row):
            QMessageBox.warning(self, "خطا", "این نام ساختار قبلا ثبت شده است.")
            return

        new_structures = [*self._structures]
        new_structures[row] = updated
        self._commit_structures(new_structures, "تغییرات ساختار با موفقیت ذخیره شد.")

    def _confirm_delete_structure(self, row: int) -> None:
        structure_name = str(self._structures[row].get("name", "")).strip()
        modal = QMessageBox(self)
        modal.setIcon(QMessageBox.Warning)
        modal.setWindowTitle("حذف ساختار محصول")
        modal.setText(f"آیا از حذف ساختار «{structure_name}» مطمئن هستید؟")
        confirm_button = modal.addButton("تایید حذف", QMessageBox.AcceptRole)
        modal.addButton("لغو", QMessageBox.RejectRole)
        modal.exec()
        if modal.clickedButton() is not confirm_button:
            return

        new_structures = [*self._structures]
        del new_structures[row]
        self._commit_structures(new_structures, "ساختار محصول حذف شد.")

    def _show_structure_dialog(
        self,
        title: str,
        initial: dict[str, object] | None = None,
    ) -> dict[str, object] | None:
        dialog = QDialog(self)
        dialog.setObjectName("ProductDialog")
        dialog.setWindowTitle(title)
        dialog.setModal(True)
        dialog.resize(720, 480)

        dialog_layout = QVBoxLayout()
        dialog_layout.setSpacing(10)

        name_label = QLabel("نام ساختار")
        name_label.setObjectName("FormFieldLabel")
        dialog_layout.addWidget(name_label)

        name_input = QLineEdit()
        name_input.setPlaceholderText("مثلا: ساختار عمومی کالا")
        if initial:
            name_input.setText(str(initial.get("name", "")).strip())
        dialog_layout.addWidget(name_input)

        fields_label = QLabel("فیلدها")
        fields_label.setObjectName("FormFieldLabel")
        dialog_layout.addWidget(fields_label)

        fields_table = QTableWidget(0, 3)
        fields_table.setObjectName("UsersTable")
        fields_table.setHorizontalHeaderLabels(["نام فیلد", "نوع داده", "یکتا بودن"])
        fields_table.verticalHeader().setVisible(False)
        fields_table.setEditTriggers(QTableWidget.NoEditTriggers)
        fields_table.setSelectionBehavior(QTableWidget.SelectRows)
        fields_table.setSelectionMode(QTableWidget.SingleSelection)
        fields_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        fields_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        fields_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Interactive)
        fields_table.setColumnWidth(2, 230)
        fields_table.verticalHeader().setDefaultSectionSize(42)
        dialog_layout.addWidget(fields_table, 1)

        field_actions_row = QHBoxLayout()
        add_field_button = QPushButton("＋ افزودن فیلد")
        add_field_button.setObjectName("AddFieldButton")
        remove_field_button = QPushButton("حذف فیلد انتخاب‌شده")
        remove_field_button.setObjectName("DangerButton")
        field_actions_row.addWidget(add_field_button)
        field_actions_row.addWidget(remove_field_button)
        field_actions_row.addStretch()
        dialog_layout.addLayout(field_actions_row)

        def add_field_row(field_name: str = "", field_type: str = "text", unique: bool = False) -> None:
            row = fields_table.rowCount()
            fields_table.insertRow(row)

            field_name_input = QLineEdit(field_name)
            field_name_input.setPlaceholderText("نام فیلد")
            fields_table.setCellWidget(row, 0, field_name_input)

            type_selector_shell = self._create_type_selector_shell(field_type)
            fields_table.setCellWidget(row, 1, type_selector_shell)

            unique_shell = self._create_unique_selector_shell(unique)
            fields_table.setCellWidget(row, 2, unique_shell)

        add_field_button.clicked.connect(lambda: add_field_row())

        def remove_selected_row() -> None:
            row = fields_table.currentRow()
            if row >= 0:
                fields_table.removeRow(row)

        remove_field_button.clicked.connect(remove_selected_row)

        initial_fields = initial.get("fields", []) if initial else []
        if isinstance(initial_fields, list):
            for field in initial_fields:
                if not isinstance(field, dict):
                    continue
                ur = field.get("unique", False)
                unique_bool = ur is True or str(ur).strip().lower() in {"true", "1", "yes"}
                add_field_row(
                    field_name=str(field.get("name", "")).strip(),
                    field_type=str(field.get("type", "")).strip() or "text",
                    unique=unique_bool,
                )
        if fields_table.rowCount() == 0:
            add_field_row()

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("تایید")
        buttons.button(QDialogButtonBox.Cancel).setText("لغو")
        dialog_layout.addWidget(buttons)
        dialog.setLayout(dialog_layout)

        buttons.rejected.connect(dialog.reject)

        result_holder: dict[str, object] = {}

        def validate_and_accept() -> None:
            structure_name = name_input.text().strip()
            if not structure_name:
                QMessageBox.warning(dialog, "خطا", "نام ساختار الزامی است.")
                return

            fields: list[dict[str, object]] = []
            seen_names: set[str] = set()
            for row in range(fields_table.rowCount()):
                field_name_widget = fields_table.cellWidget(row, 0)
                field_type_widget = fields_table.cellWidget(row, 1)
                unique_widget = fields_table.cellWidget(row, 2)
                if not isinstance(field_name_widget, QLineEdit):
                    continue
                if not isinstance(field_type_widget, StyledComboField):
                    continue

                field_name = field_name_widget.text().strip()
                field_type = field_type_widget.combo_box.currentText().strip()
                unique_val = False
                if isinstance(unique_widget, StyledComboField):
                    unique_val = bool(unique_widget.combo_box.currentData())
                if not field_name:
                    QMessageBox.warning(dialog, "خطا", "نام فیلد نمی‌تواند خالی باشد.")
                    return
                if not field_type:
                    QMessageBox.warning(dialog, "خطا", "نوع دادهٔ فیلد نمی‌تواند خالی باشد.")
                    return
                normalized = field_name.casefold()
                if normalized in seen_names:
                    QMessageBox.warning(dialog, "خطا", "نام فیلدها باید یکتا باشد.")
                    return
                seen_names.add(normalized)
                fields.append({"name": field_name, "type": field_type, "unique": unique_val})

            result_holder["value"] = {"name": structure_name, "fields": fields}
            dialog.accept()

        buttons.accepted.connect(validate_and_accept)

        if dialog.exec() != QDialog.Accepted:
            return None
        return result_holder.get("value") if isinstance(result_holder.get("value"), dict) else None

    def _structure_name_exists(self, name: str, ignore_index: int = -1) -> bool:
        target = name.casefold().strip()
        for index, structure in enumerate(self._structures):
            if index == ignore_index:
                continue
            current = str(structure.get("name", "")).casefold().strip()
            if current and current == target:
                return True
        return False

    def _commit_structures(self, structures: list[dict[str, object]], success_message: str) -> bool:
        if not save_product_structures(structures):
            QMessageBox.critical(self, "خطا", "ذخیره ساختارهای محصول انجام نشد. دوباره تلاش کنید.")
            return False

        self._structures = structures
        self._refresh_table()
        self._refresh_assignment_table()
        QMessageBox.information(self, "ساختارهای محصول", success_message)
        return True
