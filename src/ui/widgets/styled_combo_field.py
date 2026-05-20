from PySide6.QtCore import QEvent, QObject, QPoint, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPixmap, QPolygon
from PySide6.QtWidgets import QComboBox, QFrame, QHBoxLayout, QLabel, QWidget


def _dropdown_triangle_pixmap(size: int = 12, fill: str = "#334155") -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(fill))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawPolygon(
        QPolygon(
            [
                QPoint(2, int(size * 0.32)),
                QPoint(size - 2, int(size * 0.32)),
                QPoint(size // 2, size - 3),
            ]
        )
    )
    painter.end()
    return pm


class _ComboChevronLabel(QLabel):
    def __init__(self, combo: QComboBox, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("StyledComboFieldChevron")
        self._combo = combo
        self.setPixmap(_dropdown_triangle_pixmap(14))
        self.setAlignment(Qt.AlignCenter)
        self.setFixedWidth(36)
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event) -> None:
        self._combo.showPopup()
        super().mousePressEvent(event)


class StyledComboField(QFrame):
    currentIndexChanged = Signal(int)
    currentTextChanged = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("StyledComboFieldShell")

        layout = QHBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)

        self.combo_box = QComboBox()
        self.combo_box.setObjectName("StyledComboFieldCombo")
        self.combo_box.view().setMouseTracking(True)
        self.combo_box.installEventFilter(self)
        self.combo_box.currentIndexChanged.connect(self.currentIndexChanged.emit)
        self.combo_box.currentTextChanged.connect(self.currentTextChanged.emit)

        layout.addWidget(self.combo_box, 1)
        layout.addWidget(_ComboChevronLabel(self.combo_box, self))
        self.setLayout(layout)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched is self.combo_box:
            if event.type() == QEvent.Type.FocusIn:
                self.setProperty("focusWithin", True)
                self._repolish()
            elif event.type() == QEvent.Type.FocusOut:
                if self.combo_box.view().isVisible():
                    return False
                self.setProperty("focusWithin", False)
                self._repolish()
        return super().eventFilter(watched, event)

    def _repolish(self) -> None:
        style = self.style()
        if style is not None:
            style.unpolish(self)
            style.polish(self)

