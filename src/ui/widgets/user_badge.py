from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout


class UserBadge(QFrame):
    """نشان کاربر در ساید‌بار: آواتار دایره‌ای با حرف اول نام، و نام کاربر زیر آن."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("UserBadge")
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        layout = QVBoxLayout()
        layout.setContentsMargins(8, 12, 8, 12)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

        self.avatar = QLabel()
        self.avatar.setObjectName("UserAvatar")
        self.avatar.setFixedSize(64, 64)
        self.avatar.setAlignment(Qt.AlignCenter)

        self.name_label = QLabel("")
        self.name_label.setObjectName("UserBadgeName")
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setMinimumWidth(0)

        layout.addWidget(self.avatar, 0, Qt.AlignHCenter)
        layout.addWidget(self.name_label)
        self.setLayout(layout)

    def set_username(self, username: str | None) -> None:
        text = (username or "").strip()
        self.name_label.setText(text or "—")
        initial = text[:1] if text else "?"
        try:
            initial = initial.upper()
        except Exception:
            pass
        self.avatar.setText(initial)
