from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel,
    QHBoxLayout, QVBoxLayout
)
from PySide6.QtCore import Qt

from .._style import COMMON_STYLE
from .._widgets import WindowControls


class HighBanRiskPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(COMMON_STYLE)
        self.resize(380, 235)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(60, 5, 15, 50)
        root.setSpacing(24)

        # ── Top row ───────────────────────────────────────────
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(12)
        top_row.addStretch()

        self.window_controls = WindowControls()
        self.window_controls.minimize_requested.connect(self.showMinimized)
        self.window_controls.close_requested.connect(self.close)
        top_row.addWidget(self.window_controls)
        root.addLayout(top_row)

        # ── Title ─────────────────────────────────────────────
        title = QLabel("High Ban Risk")
        title.setObjectName("title")
        title.setStyleSheet(
            "color: #D05050;"
            "text-decoration: underline;"
            "font-family: Georgia, 'Times New Roman', serif;"
            "font-size: 38px;"
            "border: none;"
            "background: transparent;"
        )
        root.addWidget(title)

        # ── Launch row ────────────────────────────────────────
        launch_row = QHBoxLayout()
        launch_row.setSpacing(12)

        self.launch_btn = QPushButton("Launch the Game with 3DMigoto")
        self.launch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.launch_btn.setStyleSheet("border-color: #D05050;")

        help_btn = QPushButton("?")
        help_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        help_btn.setObjectName("help_btn")
        help_btn.setToolTip(
            "Launching with 3DMigoto injects a DLL into the game process, "
            "which may be detected by anti-cheat software."
        )

        launch_row.addWidget(self.launch_btn)
        launch_row.addWidget(help_btn)
        launch_row.addStretch()

        root.addLayout(launch_row)
        root.addStretch()
