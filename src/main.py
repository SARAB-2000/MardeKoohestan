import sys

from PySide6.QtCore import QLocale, Qt
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication, QDialog

from settings import APP_LAYOUT_DIRECTION, APP_LOCALE
from ui.main_window import MainWindow
from ui.pages.login_page import LoginDialog
from ui.styles import get_app_stylesheet
from ui.widgets.no_wheel_input_filter import NoWheelInputFilter




def main() -> None:
    # Keep UI texts as-is but force Latin digits globally.
    QLocale.setDefault(QLocale("en_US"))
    app = QApplication(sys.argv)
    no_wheel_filter = NoWheelInputFilter(app)
    app.installEventFilter(no_wheel_filter)
    app.setProperty("_noWheelInputFilter", no_wheel_filter)
    available_families = set(QFontDatabase.families())
    chosen_family: str | None = None
    for family_name in (
        "Vazirmatn",
        "Vazir",
        "Shabnam",
        "Sahel",
        "IRANSans",
        "IRANSansX",
        "Segoe UI",
        "Tahoma",
        "Arial",
    ):
        if family_name in available_families:
            chosen_family = family_name
            break

    if chosen_family is not None:
        app_font = QFont(chosen_family, 10)
        try:
            app_font.setFeature(QFont.Tag("lnum"), 1)
            app_font.setFeature(QFont.Tag("tnum"), 1)
        except (AttributeError, TypeError):
            pass
        app.setFont(app_font)

    app.setLayoutDirection(
        Qt.RightToLeft if APP_LAYOUT_DIRECTION.lower() == "rtl" else Qt.LeftToRight
    )
    app.setStyleSheet(get_app_stylesheet())

    login_dialog = LoginDialog()
    if login_dialog.exec() != QDialog.Accepted or not login_dialog.user_role:
        sys.exit(0)

    window = MainWindow()
    window.apply_role(login_dialog.user_role, login_dialog.authenticated_username)
    window.show()
    app.processEvents()
    print(f"Window size after login: {window.width()}x{window.height()}")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
