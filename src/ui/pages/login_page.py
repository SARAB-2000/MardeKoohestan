from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from user_store import get_users


class LoginDialog(QDialog):
    def __init__(self) -> None:
        super().__init__()
        self.user_role: str | None = None
        self.authenticated_username: str | None = None
        self.setWindowTitle("ورود به سیستم")
        self.setModal(True)
        self.resize(460, 240)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("رمز عبور را وارد کنید")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.returnPressed.connect(self.submit_login)
        self.password_input.setLayoutDirection(Qt.LeftToRight)

        self.toggle_password_button = QPushButton("👁")
        self.toggle_password_button.setObjectName("IconButton")
        self.toggle_password_button.setCheckable(True)
        self.toggle_password_button.setToolTip("نمایش یا مخفی کردن رمز عبور")
        self.toggle_password_button.clicked.connect(self.toggle_password_visibility)

        submit_button = QPushButton("ورود")
        submit_button.setObjectName("PrimaryButton")
        submit_button.clicked.connect(self.submit_login)

        title_label = QLabel("خوش آمدید")
        title_label.setObjectName("DialogTitle")
        subtitle_label = QLabel("برای ادامه، رمز عبور را وارد کنید")
        subtitle_label.setObjectName("DialogSubtitle")

        form = QFormLayout()
        password_row = QHBoxLayout()
        password_row.setSpacing(8)
        password_row.addWidget(self.password_input)
        password_row.addWidget(self.toggle_password_button)
        form.addRow("رمز عبور:", password_row)

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout()
        card_layout.setSpacing(12)
        card_layout.addWidget(title_label)
        card_layout.addWidget(subtitle_label)
        card_layout.addLayout(form)
        card_layout.addWidget(submit_button)
        card.setLayout(card_layout)

        container = QVBoxLayout()
        container.setContentsMargins(20, 20, 20, 20)
        container.addWidget(card)
        self.setLayout(container)

    def submit_login(self) -> None:
        entered_password = self.password_input.text().strip()
        users = get_users()
        for user in users:
            if user["password"] != entered_password:
                continue
            role = str(user.get("role", "normal")).strip().lower()
            self.user_role = "admin" if role == "admin" else "normal"
            self.authenticated_username = str(user.get("username", "")).strip() or None
            self.accept()
            return

        QMessageBox.warning(self, "خطا", "رمز عبور نادرست است.")
        self.password_input.clear()
        self.password_input.setFocus()

    def toggle_password_visibility(self) -> None:
        is_visible = self.toggle_password_button.isChecked()
        self.password_input.setEchoMode(
            QLineEdit.Normal if is_visible else QLineEdit.Password
        )
        self.toggle_password_button.setText("🙈" if is_visible else "👁")
