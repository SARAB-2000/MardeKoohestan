from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

from settings import APP_NAME, APP_WINDOW_HEIGHT, APP_WINDOW_WIDTH
from user_store import get_app_name
from ui.pages.login_page import LoginDialog
from ui.pages.management_tabs import ManagementTabs
from ui.pages.user_home_page import UserHomePage
from ui.pages.user_settings_page import UserSettingsPage
from ui.widgets.nav_item import NavItem
from ui.widgets.user_badge import UserBadge


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.current_role: str | None = None
        self.setWindowTitle(get_app_name(APP_NAME))
        self.resize(APP_WINDOW_WIDTH, APP_WINDOW_HEIGHT)
        self.setMinimumSize(800, 600)

        central_widget = QWidget()
        self.root_layout = QHBoxLayout()
        self.root_layout.setContentsMargins(24, 20, 24, 20)
        self.root_layout.setSpacing(16)

        self.sidebar = QFrame()
        self.sidebar.setObjectName("SidebarNav")
        self.sidebar.setMinimumWidth(150)
        self.sidebar.setMaximumWidth(220)
        self.sidebar.setFixedWidth(180)
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(12, 12, 12, 12)
        sidebar_layout.setSpacing(10)

        self.user_badge = UserBadge()
        sidebar_layout.addWidget(self.user_badge)

        self.home_button = NavItem("خانه", "⌂")
        self.home_button.clicked.connect(self.show_home_page)

        self.settings_button = NavItem("تنظیمات", "⚙")
        self.settings_button.clicked.connect(self.show_settings_page)

        self.management_button = NavItem("مدیریت", "⚙")
        self.management_button.clicked.connect(self.show_management_page)

        self.logout_button = NavItem("خروج", "⏻")
        self.logout_button.clicked.connect(self.logout)

        sidebar_layout.addWidget(self.home_button)
        sidebar_layout.addWidget(self.settings_button)
        sidebar_layout.addWidget(self.management_button)
        sidebar_layout.addWidget(self.logout_button)
        sidebar_layout.addStretch()
        self.sidebar.setLayout(sidebar_layout)

        self.content_card = QFrame()
        self.content_card.setObjectName("Card")
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 16, 20, 16)
        content_layout.setSpacing(6)

        self.page_title_label = QLabel("صفحه اصلی")
        self.page_title_label.setObjectName("PageTitle")

        self.management_tabs = ManagementTabs()
        self.management_tabs.general_settings_tab.app_name_changed.connect(
            self.setWindowTitle
        )
        self.settings_page = UserSettingsPage()
        self.settings_page.setVisible(False)

        content_layout.addWidget(self.page_title_label)
        self.user_home_page = UserHomePage()
        self.user_home_page.setVisible(False)
        content_layout.addWidget(self.user_home_page)
        content_layout.addWidget(self.management_tabs)
        content_layout.addWidget(self.settings_page)
        # content_layout.addStretch()
        self.content_card.setLayout(content_layout)

        self.root_layout.addWidget(self.sidebar)
        self.root_layout.addWidget(self.content_card, 1)
        central_widget.setLayout(self.root_layout)
        self.setCentralWidget(central_widget)
        self._apply_responsive_layout()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._apply_responsive_layout()

    def _apply_responsive_layout(self) -> None:
        compact = self.width() <= 980
        if compact:
            self.root_layout.setContentsMargins(12, 10, 12, 10)
            self.root_layout.setSpacing(10)
            self.sidebar.setFixedWidth(160)
            return

        self.root_layout.setContentsMargins(24, 20, 24, 20)
        self.root_layout.setSpacing(16)
        self.sidebar.setFixedWidth(180)

    def apply_role(self, role: str, username: str | None = None) -> None:
        self.current_role = role
        self.sidebar.setVisible(True)
        self.user_badge.set_username(username)
        if role == "admin":
            self.user_home_page.setVisible(False)
            self.home_button.setVisible(False)
            self.settings_button.setVisible(False)
            self.management_button.setVisible(True)
            self.show_management_page()
            return
        self.user_home_page.set_username(username)
        self.settings_page.set_username(username)
        self.home_button.setVisible(True)
        self.settings_button.setVisible(True)
        self.management_button.setVisible(False)
        self.show_home_page()

    def show_home_page(self) -> None:
        self.page_title_label.setText("صفحه اصلی")
        self.management_tabs.setVisible(False)
        self.settings_page.setVisible(False)
        self.user_home_page.setVisible(True)
        self.user_home_page.reload_devices_ui()
        self.home_button.set_active(True)
        self.settings_button.set_active(False)
        self.management_button.set_active(False)
        self.logout_button.set_active(False)

    def show_management_page(self) -> None:
        self.page_title_label.setText("صفحه مدیریت")
        self.user_home_page.setVisible(False)
        self.management_tabs.setCurrentIndex(0)
        self.management_tabs.setVisible(True)
        self.settings_page.setVisible(False)
        self.home_button.set_active(False)
        self.settings_button.set_active(False)
        self.management_button.set_active(True)
        self.logout_button.set_active(False)

    def show_settings_page(self) -> None:
        self.page_title_label.setText("تنظیمات")
        self.user_home_page.stop_session_if_running()
        self.user_home_page.setVisible(False)
        self.management_tabs.setVisible(False)
        self.settings_page.setVisible(True)
        self.home_button.set_active(False)
        self.settings_button.set_active(True)
        self.management_button.set_active(False)
        self.logout_button.set_active(False)

    def logout(self) -> None:
        self.user_home_page.stop_session_if_running()
        self.hide()
        login_dialog = LoginDialog()
        if login_dialog.exec() != QDialog.Accepted or not login_dialog.user_role:
            QApplication.quit()
            return

        self.apply_role(login_dialog.user_role, login_dialog.authenticated_username)
        self.show()
