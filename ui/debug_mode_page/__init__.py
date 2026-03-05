from PySide6.QtWidgets import (
    QWidget, QApplication, QPushButton, QLabel, QLineEdit, QListWidget,
    QProgressBar, QHBoxLayout, QVBoxLayout, QStackedWidget
)
from PySide6.QtCore import Qt
import sys

from .._style import COMMON_STYLE, set_tab
from .._widgets import WindowControls


class DebugModePage(QWidget):
    """
    Two modes switched by Change Values | Manage Values tabs:
      - Change Values : two text inputs (Current Value, Change as) + Apply button
      - Manage Values : large text area + Retrieve (green) + Edit buttons
    """

    def __init__(self):
        super().__init__()
        self.setStyleSheet(COMMON_STYLE)
        self.resize(800, 420)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # __ Top Row ___________________________________________
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 5, 8, 0)
        top_row.setSpacing(12)
        top_row.addStretch()

        self.window_controls = WindowControls()
        self.window_controls.minimize_requested.connect(self.showMinimized)
        self.window_controls.close_requested.connect(self.close)
        top_row.addWidget(self.window_controls)
        root.addLayout(top_row)

        # ── Content — margins apply only here ────────────────
        content = QVBoxLayout()
        content.setContentsMargins(60, 16, 60, 50)
        content.setSpacing(16)

        # ── Title ─────────────────────────────────────────────
        title = QLabel("Debug Mode")
        title.setObjectName("title")
        content.addWidget(title)

        # ── Tab row ───────────────────────────────────────────
        tab_row = QHBoxLayout()
        tab_row.setSpacing(0)

        self.change_tab = QPushButton("Change Values")
        self.manage_tab = QPushButton("Manage Values")

        tab_row.addWidget(self.change_tab)
        tab_row.addWidget(self.manage_tab)
        tab_row.addStretch()
        content.addLayout(tab_row)

        # ── Stacked content ───────────────────────────────────
        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_change_panel())
        self.stack.addWidget(self._build_manage_panel())
        content.addWidget(self.stack)
        content.addStretch()

        # ── Tab connections ───────────────────────────────────
        self.change_tab.clicked.connect(self._show_change)
        self.manage_tab.clicked.connect(self._show_manage)

        # Default: Manage Values active (matches design reference)
        self._show_change()

        # __ Add the Content to Root ___________________________
        root.addLayout(content)

    # ── Panels ────────────────────────────────────────────────

    def _build_change_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.current_value_input = QLineEdit()
        self.current_value_input.setPlaceholderText("Current Value")

        self.change_as_input = QLineEdit()
        self.change_as_input.setPlaceholderText("Change as")

        apply_row = QHBoxLayout()
        apply_row.addStretch()
        self.apply_btn = QPushButton("Apply")
        apply_row.addWidget(self.apply_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setContentsMargins(0, 15, 0, 0)

        layout.addWidget(self.current_value_input)
        layout.addWidget(self.change_as_input)        
        layout.addLayout(apply_row)
        layout.addWidget(self.progress_bar)
        layout.addStretch()
        return panel

    def _build_manage_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.values_list = QListWidget()
        layout.addWidget(self.values_list)

        action_row = QHBoxLayout()
        action_row.setSpacing(8)
        self.retrieve_btn = QPushButton("Retrieve")
        self.retrieve_btn.setObjectName("success")
        self.edit_values_btn = QPushButton("Edit")
        action_row.addWidget(self.retrieve_btn)
        action_row.addStretch()
        action_row.addWidget(self.edit_values_btn)
        layout.addLayout(action_row)

        return panel

    # ── Tab switching ─────────────────────────────────────────

    def _show_change(self):
        set_tab(self.change_tab, self.manage_tab)
        self.stack.setCurrentIndex(0)

    def _show_manage(self):
        set_tab(self.manage_tab, self.change_tab)
        self.stack.setCurrentIndex(1)
