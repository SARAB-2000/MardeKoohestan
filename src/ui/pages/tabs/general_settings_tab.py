from PySide6.QtCore import QSettings, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from settings import APP_NAME as DEFAULT_APP_NAME, DEFAULT_ADMIN_USERNAME
from user_store import get_app_name, get_scan_results_limit, get_users
from ui.widgets.input_controls import NoWheelSpinBox
from ui.widgets.responsive_form import ResponsiveFormSection


class GeneralSettingsTab(QWidget):
    app_name_changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._settings = QSettings("HenProject", "HenApp")

        layout = QVBoxLayout()
        form_section = ResponsiveFormSection(min_column_width=280, max_columns=3)

        self.app_name_edit = QLineEdit()
        self.app_name_edit.setObjectName("AppNameEdit")
        self.app_name_edit.setMaxLength(120)
        self.app_name_edit.setPlaceholderText("نام پروژه")
        self.app_name_edit.setText(get_app_name(DEFAULT_APP_NAME))
        self.app_name_edit.setMaximumWidth(280)
        form_section.add_field("نام پروژه", self.app_name_edit)

        self.allowed_users_spin = NoWheelSpinBox()
        self.allowed_users_spin.setObjectName("AllowedUsersSpin")
        self.allowed_users_spin.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.allowed_users_spin.setRange(1, 9999)
        self.allowed_users_spin.setValue(self._load_allowed_users())
        self.allowed_users_spin.setMaximumWidth(280)
        form_section.add_field("تعداد کاربران مجاز", self.allowed_users_spin)

        self.scan_results_limit_spin = NoWheelSpinBox()
        self.scan_results_limit_spin.setObjectName("AllowedUsersSpin")
        self.scan_results_limit_spin.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.scan_results_limit_spin.setRange(1, 999999)
        self.scan_results_limit_spin.setValue(get_scan_results_limit())
        self.scan_results_limit_spin.setMaximumWidth(280)
        form_section.add_field("حداکثر رکوردهای جدول اسکن", self.scan_results_limit_spin)

        layout.addWidget(form_section)

        self.save_button = QPushButton("ذخیره تنظیمات")
        self.save_button.setObjectName("SettingsSaveButton")
        self.save_button.clicked.connect(self._save_settings)
        layout.addStretch()
        layout.addWidget(self.save_button, alignment=Qt.AlignRight | Qt.AlignBottom)
        self.setLayout(layout)

    def _load_allowed_users(self) -> int:
        value = self._settings.value("general/allowed_users", 1)
        try:
            parsed_value = int(value)
        except (TypeError, ValueError):
            return 1
        return max(1, parsed_value)

    def _save_settings(self) -> None:
        new_app_name = self.app_name_edit.text().strip()
        if not new_app_name:
            QMessageBox.warning(self, "نام پروژه", "نام پروژه نمی‌تواند خالی باشد.")
            self.app_name_edit.setText(get_app_name(DEFAULT_APP_NAME))
            return

        new_limit = self.allowed_users_spin.value()
        managed_users_count = sum(
            1
            for user in get_users()
            if str(user.get("username", "")).strip() != DEFAULT_ADMIN_USERNAME
        )
        if new_limit < managed_users_count:
            QMessageBox.warning(
                self,
                "محدودیت کاربران",
                f"تعداد کاربران فعلی ({managed_users_count}) از سقف جدید بیشتر است. "
                "ابتدا کاربران را کاهش دهید یا سقف را برابر/بیشتر قرار دهید.",
            )
            self.allowed_users_spin.setValue(managed_users_count)
            return

        self._settings.setValue("general/app_name", new_app_name)
        self._settings.setValue("general/allowed_users", new_limit)
        self._settings.setValue(
            "general/scan_results_limit", self.scan_results_limit_spin.value()
        )
        self._settings.sync()

        if self._settings.status() == QSettings.NoError:
            self.app_name_changed.emit(new_app_name)
            QMessageBox.information(self, "ذخیره تنظیمات", "تنظیمات با موفقیت ذخیره شد.")
            return

        QMessageBox.critical(self, "خطا", "ذخیره تنظیمات انجام نشد. دوباره تلاش کنید.")
