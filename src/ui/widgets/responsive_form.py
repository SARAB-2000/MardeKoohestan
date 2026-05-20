from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import (
    QGridLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class ResponsiveFormSection(QWidget):
    def __init__(self, min_column_width: int = 320, max_columns: int = 3) -> None:
        super().__init__()
        self._min_column_width = min_column_width
        self._max_columns = max_columns
        self._field_groups: list[QWidget] = []

        self._grid = QGridLayout()
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setHorizontalSpacing(12)
        self._grid.setVerticalSpacing(12)
        self.setLayout(self._grid)

    def add_field(self, title: str, field_widget: QWidget) -> None:
        field_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        label = QLabel(title)
        label.setObjectName("FormFieldLabel")

        group = QWidget()
        group.setObjectName("FormFieldGroup")
        group.setMinimumWidth(self._min_column_width)

        group_layout = QVBoxLayout()
        group_layout.setContentsMargins(0, 0, 0, 0)
        group_layout.setSpacing(6)
        group_layout.addWidget(label)
        group_layout.addWidget(field_widget)
        group.setLayout(group_layout)

        self._field_groups.append(group)
        self._reflow()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._reflow()

    def _reflow(self) -> None:
        while self._grid.count():
            self._grid.takeAt(0)

        columns = self._calculate_column_count()
        for index, group in enumerate(self._field_groups):
            row = index // columns
            column = index % columns
            self._grid.addWidget(group, row, column)

        for column in range(columns):
            self._grid.setColumnStretch(column, 1)

    def _calculate_column_count(self) -> int:
        available_width = max(1, self.width())
        slot_width = self._min_column_width + self._grid.horizontalSpacing()
        estimated_columns = max(1, available_width // slot_width)
        return min(self._max_columns, estimated_columns)
