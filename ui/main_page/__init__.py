from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout
from PySide6.QtCore import Qt, QPoint

from .._style import COMMON_STYLE
from ._top_row import TopRow
from ._apply_panel import ApplyPanel
from ._bottom_row import BottomRow

class MainPage(QWidget):    
    main_page = None

    def __init__(self):
        from security.generator.session_title import generate_session_title
        
        MainPage.main_page = self

        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setStyleSheet(COMMON_STYLE)
        self.resize(800, 500)
        self.setWindowTitle(generate_session_title())
        self._drag_pos = QPoint()        
        self._build_ui()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and not self._drag_pos.isNull():
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(0)

        # ── Top row ───────────────────────────────────────────
        from modding.install_mod import install_mod
        from ui.settings_page import SettingsPage

        self.top_row = TopRow()
        self.top_row.minimize_requested.connect(self.showMinimized)
        self.top_row.close_requested.connect(self.close)
        self.top_row.install_mod_clicked.connect(install_mod)
        self.top_row.settings_clicked.connect(lambda: SettingsPage(parent=self).show())
        root.addWidget(self.top_row)
        root.addSpacing(8)

        # ── Apply panel ───────────────────────────────────────
        self.apply_panel = ApplyPanel()
        self.top_row.apply_mod_toggled.connect(self.apply_panel.toggle)

        panel_wrapper = QHBoxLayout()
        panel_wrapper.setContentsMargins(176, 0, 0, 0)
        panel_wrapper.addWidget(self.apply_panel)
        panel_wrapper.addStretch()
        root.addLayout(panel_wrapper)
        self.apply_panel.hide()

        root.addStretch()

        # ── Bottom row ────────────────────────────────────────
        self.bottom_row = BottomRow()
        root.addWidget(self.bottom_row)


