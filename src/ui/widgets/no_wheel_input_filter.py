from PySide6.QtCore import QEvent, QObject
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QAbstractSlider, QAbstractSpinBox, QComboBox, QWidget
from PySide6.QtWidgets import QAbstractScrollArea


class NoWheelInputFilter(QObject):
    """Blocks wheel-based value changes for input widgets globally."""

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() != QEvent.Type.Wheel:
            return False
        if not isinstance(watched, QWidget):
            return False
        if watched.property("allowWheelInput") is True:
            return False
        if isinstance(watched, (QAbstractSpinBox, QComboBox, QAbstractSlider)):
            if isinstance(event, QWheelEvent):
                self._forward_wheel_to_parent_scroll(watched, event)
            return True
        return False

    def _forward_wheel_to_parent_scroll(self, widget: QWidget, event: QWheelEvent) -> None:
        scroll_area = self._find_parent_scroll_area(widget)
        if scroll_area is None:
            return
        scroll_bar = scroll_area.verticalScrollBar()
        if scroll_bar is None:
            return

        angle_y = event.angleDelta().y()
        if angle_y:
            steps = angle_y / 120.0
            delta = int(scroll_bar.singleStep() * steps)
            scroll_bar.setValue(scroll_bar.value() - delta)
            return

        pixel_y = event.pixelDelta().y()
        if pixel_y:
            scroll_bar.setValue(scroll_bar.value() - pixel_y)

    def _find_parent_scroll_area(self, widget: QWidget) -> QAbstractScrollArea | None:
        parent = widget.parentWidget()
        while parent is not None:
            if isinstance(parent, QAbstractScrollArea):
                return parent
            parent = parent.parentWidget()
        return None
