import os

from PySide6.QtWidgets import QWidget, QPushButton, QLabel, QHBoxLayout, QFrame, QVBoxLayout
from PySide6.QtCore import Signal, Qt, QTimer, QRect
from PySide6.QtGui import QCursor

from .._style import DANGER, SUCCESS, ORANGE, COMMON_STYLE
from .._widgets import WindowControls


class _InstallPopup(QFrame):
    def __init__(self, dropdown_btn: QPushButton):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.Popup | Qt.FramelessWindowHint)
        self._dropdown_btn = dropdown_btn
        self.closed_by_dropdown = False

    def hideEvent(self, event):
        cursor_pos = QCursor.pos()
        tl = self._dropdown_btn.mapToGlobal(self._dropdown_btn.rect().topLeft())
        self.closed_by_dropdown = QRect(tl, self._dropdown_btn.size()).contains(cursor_pos)
        super().hideEvent(event)


class TopRow(QWidget):
    apply_mod_toggled          = Signal()
    minimize_requested         = Signal()
    close_requested            = Signal()
    install_mod_clicked        = Signal()
    background_apply_requested = Signal()
    background_cancel_requested = Signal()

    settings_clicked           = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # ── Split install button ──────────────────────────────
        self._install_col_widget = QWidget()
        _install_split = QHBoxLayout(self._install_col_widget)
        _install_split.setSpacing(0)
        _install_split.setContentsMargins(0, 0, 0, 0)

        self.install_btn = QPushButton("Install Mod  ↑")
        self.install_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.install_btn.setMinimumWidth(160)
        self.install_btn.setStyleSheet(
            "QPushButton { border-top-right-radius: 0; border-bottom-right-radius: 0; }"
            "QPushButton:hover { border-top-right-radius: 0; border-bottom-right-radius: 0; }"
        )
        self.install_btn.clicked.connect(self.install_mod_clicked)

        self._install_dropdown_btn = QPushButton("▾")
        self._install_dropdown_btn.setFixedWidth(22)
        self._install_dropdown_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._install_dropdown_btn.setStyleSheet(
            "QPushButton { border-top-left-radius: 0; border-bottom-left-radius: 0; border-left: none; padding: 8px 4px; }"
            "QPushButton:hover { border-top-left-radius: 0; border-bottom-left-radius: 0; }"
        )

        _install_split.addWidget(self.install_btn)
        _install_split.addWidget(self._install_dropdown_btn)

        self._install_popup = _InstallPopup(self._install_dropdown_btn)
        self._install_popup.setStyleSheet(COMMON_STYLE)
        _popup_layout = QVBoxLayout(self._install_popup)
        _popup_layout.setContentsMargins(0, 0, 0, 0)
        _popup_layout.setSpacing(0)
        self.install_folder_btn = QPushButton("Scan for Mods")
        self.install_folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.install_folder_btn.setStyleSheet("QPushButton { font-size: 11px; padding: 8px 6px; }")
        _popup_layout.addWidget(self.install_folder_btn)

        self._install_dropdown_btn.clicked.connect(self._toggle_install_popup)
        self.install_folder_btn.clicked.connect(self._on_scan_mods)
        # ─────────────────────────────────────────────────────

        self.apply_mod_btn = QPushButton("Apply Mod  ▼")
        self.apply_mod_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.apply_mod_btn.setMinimumWidth(160)
        self.apply_mod_btn.clicked.connect(self.apply_mod_toggled)

        self._apply_feedback_timer = QTimer(self)
        self._apply_feedback_timer.setSingleShot(True)
        self._apply_feedback_timer.setInterval(5000)

        self.apply_feedback_label = QLabel()
        self.apply_feedback_label.hide()

        self._apply_feedback_timer.timeout.connect(self.apply_feedback_label.hide)

        layout.addWidget(self._install_col_widget)
        layout.addWidget(self.apply_mod_btn)
        layout.addWidget(self.apply_feedback_label)
        layout.addStretch()

        from ui.high_ban_risk_page import HighBanRiskPage
        warn_btn = QPushButton("⚠")
        warn_btn.setToolTip("3D Migoto Loaders")
        warn_btn.setObjectName("icon_btn")
        warn_btn.setFixedSize(32, 32)
        warn_btn.setStyleSheet("color: #cc3333; font-size: 18px;")
        warn_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        warn_btn.clicked.connect(lambda: HighBanRiskPage(parent=self).show())

        self._background_apply_col_widget = QWidget()
        _background_apply_split = QHBoxLayout(self._background_apply_col_widget)
        _background_apply_split.setSpacing(0)
        _background_apply_split.setContentsMargins(0, 0, 0, 0)

        self.background_apply_btn = QPushButton("Apply")
        self.background_apply_btn.setToolTip("Apply Background Image")
        self.background_apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.background_apply_btn.setStyleSheet(
            f"QPushButton {{ background-color: {SUCCESS}; color: white; border-color: {SUCCESS};"
            " border-top-right-radius: 0; border-bottom-right-radius: 0; }}"
            f"QPushButton:hover {{ background-color: {SUCCESS}; color: white; }}"
        )
        self.background_apply_btn.clicked.connect(self.background_apply_requested)
        self._background_apply_dropdown_btn = QPushButton("▼")
        self._background_apply_dropdown_btn.setFixedWidth(22)
        self._background_apply_dropdown_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._background_apply_dropdown_btn.setStyleSheet(
            f"QPushButton {{ background-color: {SUCCESS}; color: white; border-color: {SUCCESS};"
            " border-left: none; padding: 8px 4px;"
            " border-top-left-radius: 0; border-bottom-left-radius: 0; }}"
            f"QPushButton:hover {{ background-color: {SUCCESS}; color: white; }}"
        )
        _background_apply_split.addWidget(self.background_apply_btn)
        _background_apply_split.addWidget(self._background_apply_dropdown_btn)

        self._background_apply_popup = _InstallPopup(self._background_apply_dropdown_btn)
        self._background_apply_popup.setStyleSheet(COMMON_STYLE)
        _background_apply_popup_layout = QVBoxLayout(self._background_apply_popup)
        _background_apply_popup_layout.setContentsMargins(0, 0, 0, 0)
        _background_apply_popup_layout.setSpacing(0)
        self.background_cancel_btn = QPushButton("Cancel")
        self.background_cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.background_cancel_btn.setStyleSheet(
            f"QPushButton {{ background-color: {DANGER}; color: white; border-color: {DANGER};"
            " font-size: 11px; padding: 8px 6px; }}"
            f"QPushButton:hover {{ background-color: {DANGER}; color: white; }}"
        )
        _background_apply_popup_layout.addWidget(self.background_cancel_btn)
        self._background_apply_dropdown_btn.clicked.connect(self._toggle_background_apply_popup)
        self.background_cancel_btn.clicked.connect(self._on_background_cancel)

        self._background_apply_col_widget.hide()
        layout.addWidget(self._background_apply_col_widget)
        layout.addWidget(warn_btn)

        logs_btn = QPushButton("📄")
        logs_btn.setToolTip("Game Logs")
        logs_btn.setObjectName("icon_btn")
        logs_btn.setFixedSize(32, 32)
        logs_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        from database.user.user_variables import user_variables
        logs_btn.clicked.connect(lambda: os.startfile(user_variables.game_logs))
        layout.addWidget(logs_btn)

        settings_btn = QPushButton("⚙")
        settings_btn.setToolTip("Loader Settings")
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

    def _toggle_install_popup(self):
        if self._install_popup.closed_by_dropdown:
            self._install_popup.closed_by_dropdown = False
            return
        col_global = self._install_col_widget.mapToGlobal(
            self._install_col_widget.rect().bottomLeft()
        )
        self._install_popup.adjustSize()
        self._install_popup.setFixedWidth(self._install_col_widget.width())
        self._install_popup.move(col_global.x(), col_global.y() + 4)
        self._install_popup.show()

    def _on_scan_mods(self):
        from modding.get_mods import get_mods
        self._install_popup.hide()
        get_mods()

    def set_apply_feedback(self, text: str, *, success: bool = False, error: bool = False):
        color = SUCCESS if success else ("#CC2200" if error else ORANGE)
        self.apply_feedback_label.setText(text)
        self.apply_feedback_label.setStyleSheet(f"color: {color}; font-weight: bold;")
        self.apply_feedback_label.show()
        self._apply_feedback_timer.start()

    def set_background_apply_visible(self, visible: bool):
        self._background_apply_col_widget.setVisible(visible)
        if not visible:
            self._background_apply_popup.hide()

    def _toggle_background_apply_popup(self):
        if self._background_apply_popup.closed_by_dropdown:
            self._background_apply_popup.closed_by_dropdown = False
            return
        col_global = self._background_apply_col_widget.mapToGlobal(
            self._background_apply_col_widget.rect().bottomLeft()
        )
        self._background_apply_popup.adjustSize()
        self._background_apply_popup.setFixedWidth(self._background_apply_col_widget.width())
        self._background_apply_popup.move(col_global.x(), col_global.y() + 4)
        self._background_apply_popup.show()

    def _on_background_cancel(self):
        self._background_apply_popup.hide()
        self.background_cancel_requested.emit()
