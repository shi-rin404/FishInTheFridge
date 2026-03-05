from PySide6.QtWidgets import QWidget, QPushButton, QHBoxLayout
from PySide6.QtCore import Signal, Qt

from .._widgets import WindowControls


class TopRow(QWidget):
    apply_mod_toggled  = Signal()
    minimize_requested = Signal()
    close_requested    = Signal()
    install_mod_clicked = Signal()
    settings_clicked   = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.install_btn = QPushButton("Install Mod  ↑")
        self.install_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.install_btn.setMinimumWidth(160)
        self.install_btn.clicked.connect(self.install_mod_clicked)

        self.apply_mod_btn = QPushButton("Apply Mod  ▼")
        self.apply_mod_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.apply_mod_btn.setMinimumWidth(160)
        self.apply_mod_btn.clicked.connect(self.apply_mod_toggled)

        layout.addWidget(self.install_btn)
        layout.addWidget(self.apply_mod_btn)
        layout.addStretch()

        warn_btn = QPushButton("⚠")
        warn_btn.setObjectName("icon_btn")
        warn_btn.setFixedSize(32, 32)
        warn_btn.setStyleSheet("color: #cc3333; font-size: 18px;")
        warn_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(warn_btn)

        logs_btn = QPushButton("📄")
        logs_btn.setObjectName("icon_btn")
        logs_btn.setFixedSize(32, 32)
        logs_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(logs_btn)

        settings_btn = QPushButton("⚙")
        settings_btn.setObjectName("icon_btn")
        settings_btn.setFixedSize(32, 32)
        settings_btn.setStyleSheet("font-size: 18px;")
        settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_btn.clicked.connect(self.settings_clicked)
        layout.addWidget(settings_btn)

        self.window_controls = WindowControls()
        self.window_controls.minimize_requested.connect(self.minimize_requested)
        self.window_controls.close_requested.connect(self.close_requested)
        layout.addWidget(self.window_controls)
