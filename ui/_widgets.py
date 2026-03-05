from PySide6.QtWidgets import QWidget, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, Signal


class WindowControls(QWidget):
    """Reusable window control bar: settings · minimize · close."""

    minimize_requested = Signal()
    close_requested    = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        minimize_btn = QPushButton("—")
        minimize_btn.setObjectName("icon_btn")
        minimize_btn.setFixedSize(32, 32)
        minimize_btn.clicked.connect(self.minimize_requested)

        close_btn = QPushButton("✕")
        close_btn.setObjectName("close_btn")
        close_btn.setFixedSize(32, 32)
        close_btn.clicked.connect(self.close_requested)

        for btn in (minimize_btn, close_btn):
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            layout.addWidget(btn)
