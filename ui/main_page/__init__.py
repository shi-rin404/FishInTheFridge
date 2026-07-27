import random
import string
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout
from PySide6.QtCore import Qt, QPoint, QTimer
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import QStyle, QStyleOption

from .._style import COMMON_STYLE
from ._top_row import TopRow
from ._apply_panel import ApplyPanel
from ._bottom_row import BottomRow
from ._auto_load import AutoLoadModsController
from ._background_image import (
    BackgroundImageEditor,
    custom_background_opacity,
    custom_background_path,
)

_TITLE_CHARS = (string.digits + string.ascii_uppercase).encode("ascii")

def _session_title() -> str:
    return ''.join(chr(random.choice(_TITLE_CHARS)) for _ in range(16))


class MainPage(QWidget):
    main_page = None

    def __init__(self):
        MainPage.main_page = self

        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setStyleSheet(COMMON_STYLE)
        self.resize(800, 500)
        self.setWindowTitle(_session_title())
        self._drag_pos = QPoint()
        self._background_pixmap = QPixmap()
        self._background_opacity = 1.0
        self._build_ui()
        self.reload_custom_background()

    def paintEvent(self, event):
        painter = QPainter(self)
        option = QStyleOption()
        option.initFrom(self)
        self.style().drawPrimitive(QStyle.PrimitiveElement.PE_Widget, option, painter, self)
        if not self._background_pixmap.isNull():
            painter.save()
            painter.setOpacity(self._background_opacity)
            painter.drawPixmap(self.rect(), self._background_pixmap)
            painter.restore()

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
        self.top_row.background_apply_requested.connect(self.apply_custom_background)
        self.top_row.background_cancel_requested.connect(self.cancel_custom_background_edit)
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
        self.bottom_row.background_image_selected.connect(self.begin_custom_background_edit)
        self.bottom_row.background_image_removed.connect(self.remove_custom_background)
        root.addWidget(self.bottom_row)
        self.background_editor = BackgroundImageEditor(self)
        self.auto_load_mods = AutoLoadModsController(self)
        QTimer.singleShot(0, self.auto_load_mods.start_if_enabled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "background_editor"):
            self.background_editor.setGeometry(self.rect())

    def reload_custom_background(self):
        path = custom_background_path()
        self._background_pixmap = QPixmap(str(path)) if path is not None else QPixmap()
        self._background_opacity = custom_background_opacity()
        self.update()

    def begin_custom_background_edit(self, image_path: str):
        if self.background_editor.begin(image_path):
            self._background_pixmap = QPixmap()
            self._background_opacity = 1.0
            self.update()
            self.top_row.set_background_apply_visible(True)
            self.top_row.raise_()
            self.bottom_row.raise_()

    def apply_custom_background(self):
        if not self.background_editor.isVisible():
            return
        self.background_editor.render_to_file()
        self.reload_custom_background()
        self.top_row.set_background_apply_visible(False)
        self.bottom_row.sync_background_image_button()

    def cancel_custom_background_edit(self):
        if not self.background_editor.isVisible():
            return
        self.background_editor.hide()
        self.top_row.set_background_apply_visible(False)
        self.reload_custom_background()

    def remove_custom_background(self):
        from ._background_image import clear_custom_background
        clear_custom_background()
        self.background_editor.hide()
        self._background_pixmap = QPixmap()
        self._background_opacity = 1.0
        self.top_row.set_background_apply_visible(False)
        self.bottom_row.sync_background_image_button()
        self.update()
