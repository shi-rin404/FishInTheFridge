from PySide6.QtWidgets import (
    QWidget, QApplication, QPushButton, QLabel, QLineEdit, QCheckBox,
    QHBoxLayout, QVBoxLayout, QComboBox, QStackedWidget
)
import sys

from ._style import COMMON_STYLE, set_tab


class ManageModSkinPage(QWidget):
    """
    Two modes switched by Edit | Add tabs:
      - Edit mode  : lists saved M/S entries (dropdown + Edit + Delete)
      - Add mode   : form to add or save a new/edited entry
    Clicking "Edit" in the list forwards to the Add form in save-mode.
    """

    def __init__(self):
        super().__init__()
        self.setStyleSheet(COMMON_STYLE)
        self.resize(800, 600)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(60, 50, 60, 50)
        root.setSpacing(16)

        # ── Title ─────────────────────────────────────────────
        title = QLabel("Manage Mod/Skin")
        title.setObjectName("title")
        root.addWidget(title)

        # ── Tab row ───────────────────────────────────────────
        tab_row = QHBoxLayout()
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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        ms_row = QHBoxLayout()
        ms_row.setSpacing(10)
        ms_label = QLabel("M/S")
        self.ms_combo = QComboBox()
        self.ms_combo.setMinimumWidth(220)
        ms_row.addWidget(ms_label)
        ms_row.addWidget(self.ms_combo)
        ms_row.addStretch()

        self.edit_entry_btn = QPushButton("Edit")
        self.delete_entry_btn = QPushButton("Delete")
        self.delete_entry_btn.setObjectName("danger")

        # Clicking Edit in the list forwards to the Add form in save-mode
        self.edit_entry_btn.clicked.connect(self._forward_to_edit_form)

        layout.addLayout(ms_row)
        layout.addWidget(self.edit_entry_btn)
        layout.addWidget(self.delete_entry_btn)
        layout.addStretch()
        return panel

    def _build_add_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
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

        self.quick_grab_btn = QPushButton("Quick Grab Current Skin")

        layout.addWidget(self.skin_name_input)
        layout.addWidget(self.skin_path_input)
        layout.addLayout(options_row)
        layout.addWidget(self.quick_grab_btn)
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
