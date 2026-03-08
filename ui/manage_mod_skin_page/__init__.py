from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QLineEdit, QCheckBox,
    QHBoxLayout, QVBoxLayout, QComboBox, QStackedWidget
)
from PySide6.QtCore import Qt, QPoint

from typing import Literal

from .._style import COMMON_STYLE, set_tab
from .._widgets import WindowControls

class ManageModSkinPage(QWidget):
    """
    Two modes switched by Edit | Add tabs:
      - Edit mode  : lists saved M/S entries (dropdown + Edit + Delete)
      - Add mode   : form to add or save a new/edited entry
    Clicking "Edit" in the list forwards to the Add form in save-mode.
    """

    def __init__(self, editor_mode=Literal["skin", "mod"], parent=None):
        super().__init__(parent, Qt.Window)
        self.setStyleSheet(COMMON_STYLE)
        self.resize(500, 300)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self._drag_pos = QPoint()
        self.editor_mode = editor_mode
        self._build_ui()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and not self._drag_pos.isNull():
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0,0,0,0)
        root.setSpacing(16)

        # -- Window Controls -----------------------------------
        window_controls_layout = QHBoxLayout()
        window_controls_layout.setContentsMargins(0, 10, 10, 0)
        window_controls_layout.setSpacing(12)
        self.window_controls = WindowControls()
        self.window_controls.minimize_requested.connect(self.showMinimized)
        self.window_controls.close_requested.connect(self.close)
        window_controls_layout.addStretch()
        window_controls_layout.addWidget(self.window_controls)
        root.addLayout(window_controls_layout)

        # ── Title ─────────────────────────────────────────────
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(60, 0, 60, 0)
        title_layout.setSpacing(12)
        root.addLayout(title_layout)
        title = QLabel(f"Manage {self.editor_mode.capitalize()}")
        title.setObjectName("title")
        title_layout.addWidget(title)        

        # ── Tab row ───────────────────────────────────────────
        tab_row = QHBoxLayout()
        tab_row.setContentsMargins(60, 0, 60, 0)
        tab_row.setSpacing(0)

        self.edit_tab = QPushButton("Edit")
        self.add_tab = QPushButton("Add")

        tab_row.addWidget(self.edit_tab)
        tab_row.addWidget(self.add_tab)
        tab_row.addStretch()
        root.addLayout(tab_row)

        # ── Stacked content ───────────────────────────────────
        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_edit_panel())
        self.stack.addWidget(self._build_add_panel())
        root.addWidget(self.stack)
        root.addStretch()

        # ── Tab connections ───────────────────────────────────
        self.edit_tab.clicked.connect(self._show_edit)
        self.add_tab.clicked.connect(self._show_add)

        # Default: Add tab active
        self._show_add()

    # ── Panels ────────────────────────────────────────────────

    def _build_edit_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(60, 0, 60, 50)
        layout.setSpacing(10)

        ms_row = QHBoxLayout()
        ms_row.setSpacing(10)
        ms_label = QLabel(self.editor_mode.capitalize())
        self.ms_combo = QComboBox()
        self.ms_combo.setMinimumWidth(220)
        ms_row.addWidget(ms_label)
        ms_row.addWidget(self.ms_combo)
        ms_row.addStretch()

        edit_delete_row = QVBoxLayout()
        edit_delete_row.setSpacing(10)
        self.edit_entry_btn = QPushButton("Edit")
        self.delete_entry_btn = QPushButton("Delete")
        self.delete_entry_btn.setObjectName("danger")
        edit_delete_row.addStretch()
        edit_delete_row.addWidget(self.edit_entry_btn)
        edit_delete_row.addWidget(self.delete_entry_btn)


        # Clicking Edit in the list forwards to the Add form in save-mode
        self.edit_entry_btn.clicked.connect(self._forward_to_edit_form)

        layout.addStretch()      
        layout.addLayout(ms_row)
        ms_row.addLayout(edit_delete_row)
        layout.addStretch()
        return panel

    def _build_add_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(60, 0, 60, 50)
        layout.setSpacing(10)

        self.skin_name_input = QLineEdit()
        self.skin_name_input.setPlaceholderText("Skin Name")

        self.skin_path_input = QLineEdit()
        self.skin_path_input.setPlaceholderText("Skin Path")

        # Backslash checkbox + help icon + Save button on same row
        options_row = QHBoxLayout()
        options_row.setSpacing(8)

        self.backslash_check = QCheckBox("Backslash")

        help_btn = QPushButton("?")
        help_btn.setObjectName("help_btn")

        self.save_btn = QPushButton("Save")
        self.save_btn.setObjectName("success")

        options_row.addWidget(self.backslash_check)
        options_row.addWidget(help_btn)
        options_row.addStretch()
        options_row.addWidget(self.save_btn)

        self.quick_grab_layout = QHBoxLayout()
        self.quick_grab_layout.setSpacing(8)            
        self.quick_grab_btn = QPushButton("Quick Grab Current Skin")                
        self.quick_grab_layout.addWidget(self.quick_grab_btn)
        self.quick_grab_layout.addStretch()

        layout.addWidget(self.skin_name_input)
        layout.addWidget(self.skin_path_input)
        layout.addLayout(options_row)
        layout.addLayout(self.quick_grab_layout)
        layout.addStretch()
        return panel

    # ── Tab switching ─────────────────────────────────────────

    def _show_edit(self):
        set_tab(self.edit_tab, self.add_tab)
        self.stack.setCurrentIndex(0)

    def _show_add(self):
        set_tab(self.add_tab, self.edit_tab)
        self.stack.setCurrentIndex(1)
        self.save_btn.setText("Save")

    def _forward_to_edit_form(self):
        """Edit button in the list forwards to the Add form in save-mode."""
        set_tab(self.add_tab, self.edit_tab)
        self.stack.setCurrentIndex(1)
        self.save_btn.setText("Save")
        # TODO: pre-fill form with selected M/S entry data
