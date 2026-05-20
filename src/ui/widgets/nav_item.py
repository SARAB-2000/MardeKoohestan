from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QBoxLayout, QFrame, QHBoxLayout, QLabel


class NavItem(QFrame):
    clicked = Signal()

    def __init__(self, title: str, icon_text: str) -> None:
        super().__init__()
        self.setObjectName("NavItem")
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(46)
        self.setLayoutDirection(Qt.LeftToRight)

        layout = QHBoxLayout()
        layout.setDirection(QBoxLayout.LeftToRight)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)

        self.text_label = QLabel(title)
        self.text_label.setObjectName("NavItemText")
        nav_font = self.text_label.font()
        nav_font.setPointSize(11)
        nav_font.setBold(True)
        self.text_label.setFont(nav_font)
        self.text_label.setStyleSheet("color: #eef3ff;")

        self.icon_label = QLabel(icon_text)
        self.icon_label.setObjectName("NavItemIcon")

        layout.addStretch()
        layout.addWidget(self.text_label)
        layout.addWidget(self.icon_label)
        self.setLayout(layout)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def set_active(self, active: bool) -> None:
        self.setProperty("active", active)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
