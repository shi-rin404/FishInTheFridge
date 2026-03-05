from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel,
    QHBoxLayout, QVBoxLayout
)
from PySide6.QtCore import Qt

from .._style import COMMON_STYLE, MUTED
from .._widgets import WindowControls


class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(COMMON_STYLE)
        self.resize(800, 600)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Top row ───────────────────────────────────────────
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 5, 8, 0)
        top_row.setSpacing(12)
        top_row.addStretch()

        self.window_controls = WindowControls()
        self.window_controls.minimize_requested.connect(self.showMinimized)
        self.window_controls.close_requested.connect(self.close)
        top_row.addWidget(self.window_controls)
        root.addLayout(top_row)

        # ── Content ───────────────────────────────────────────
        content = QVBoxLayout()
        content.setContentsMargins(60, 16, 60, 50)
        content.setSpacing(24)

        # ── Title ─────────────────────────────────────────────
        title = QLabel("Settings")
        title.setObjectName("title")
        content.addWidget(title)

        # ── Folder buttons ────────────────────────────────────
        folder_row = QHBoxLayout()
        folder_row.setSpacing(12)

        self.auto_detect_btn = QPushButton("Auto-Detect Game Folder")
        self.choose_folder_btn = QPushButton("Choose Game Folder")

        folder_row.addWidget(self.auto_detect_btn)
        folder_row.addWidget(self.choose_folder_btn)
        folder_row.addStretch()

        content.addLayout(folder_row)

        # ── Update row ────────────────────────────────────────
        update_row = QHBoxLayout()
        update_row.setSpacing(16)

        self.check_updates_btn = QPushButton("↻   Check for Updates")

        self.version_label = QLabel("VERSION_INFO")
        self.version_label.setStyleSheet(f"color: {MUTED}; font-size: 13px;")

        update_row.addWidget(self.check_updates_btn)
        update_row.addWidget(self.version_label)
        update_row.addStretch()

        content.addLayout(update_row)
        content.addStretch()

        root.addLayout(content)
