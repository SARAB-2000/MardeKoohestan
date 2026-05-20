from PySide6.QtCore import Qt
from PySide6.QtWidgets import QScrollArea, QTabWidget, QWidget

from ui.pages.tabs.copy_user_settings_tab import CopyUserSettingsTab
from ui.pages.tabs.devices_tab import DevicesTab
from ui.pages.tabs.general_settings_tab import GeneralSettingsTab
from ui.pages.tabs.products_tab import ProductsTab
from ui.pages.tabs.users_tab import UsersTab


class ManagementTabs(QTabWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("ManagementTabs")
        self.general_settings_tab = GeneralSettingsTab()
        self.addTab(self._with_scroll(self.general_settings_tab), "تنظیمات کلی")
        self.addTab(self._with_scroll(UsersTab()), "کاربران")
        self.addTab(self._with_scroll(DevicesTab()), "دستگاه‌ها")
        self.addTab(self._with_scroll(ProductsTab()), "محصولات")
        self.addTab(self._with_scroll(CopyUserSettingsTab()), "کپی تنظیمات کاربر")
        self.setCurrentIndex(0)
        self.setVisible(False)

    def _with_scroll(self, widget: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setObjectName("AppContentScrollArea")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setWidget(widget)
        return scroll
