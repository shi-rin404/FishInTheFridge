from PySide6.QtWidgets import (
    QWidget, QApplication, QPushButton, QLabel, QLineEdit,
    QHBoxLayout, QVBoxLayout, QComboBox, QFrame, QStackedWidget
)
import sys

from ._style import COMMON_STYLE, set_tab


class ManagePresetsPage(QWidget):
    """
    Left section — two sub-panels:
      Top:    manage entries inside a preset (skin + mod + preset combo → Add)
      Bottom: create or edit a preset by name
    Right section (separated by vertical divider):
      manage preset/combo associations (Add | Delete)
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
        title = QLabel("Manage Presets")
        title.setObjectName("title")
        root.addWidget(title)

        # ── Two-column layout ─────────────────────────────────
        columns = QHBoxLayout()
        columns.setSpacing(0)

        columns.addLayout(self._build_left_section(), stretch=1)
        columns.addSpacing(24)

        divider = QFrame()
        divider.setObjectName("v_divider")
        columns.addWidget(divider)

        columns.addSpacing(24)
        columns.addLayout(self._build_right_section(), stretch=1)

        root.addLayout(columns)
        root.addStretch()

    # ── Left section ──────────────────────────────────────────

    def _build_left_section(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setSpacing(12)

        # ── Top sub-panel: manage entries inside a preset ─────
        layout.addLayout(self._build_entry_manager())

        # ── Horizontal divider ────────────────────────────────
        h_div = QFrame()
        h_div.setObjectName("h_divider")
        layout.addWidget(h_div)
        layout.addSpacing(4)

        # ── Bottom sub-panel: create / edit a preset ──────────
        layout.addLayout(self._build_preset_creator())

        return layout

    def _build_entry_manager(self) -> QVBoxLayout:
        """Top-left: add skin+mod+preset entries to a combo."""
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Edit | Create tabs
        tab_row = QHBoxLayout()
        tab_row.setSpacing(0)
        self.entry_edit_tab = QPushButton("Edit")
        self.entry_create_tab = QPushButton("Create")
        tab_row.addWidget(self.entry_edit_tab)
        tab_row.addWidget(self.entry_create_tab)
        tab_row.addStretch()
        layout.addLayout(tab_row)

        # Add + Delete buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self.entry_add_btn = QPushButton("Add")
        self.entry_delete_btn = QPushButton("Delete")
        self.entry_delete_btn.setObjectName("danger")
        btn_row.addStretch()
        btn_row.addWidget(self.entry_add_btn)
        btn_row.addWidget(self.entry_delete_btn)
        layout.addLayout(btn_row)

        # Skin + Mod dropdowns (side by side)
        combo_row = QHBoxLayout()
        combo_row.setSpacing(12)
        skin_label = QLabel("Skin")
        self.skin_combo = QComboBox()
        self.skin_combo.setMinimumWidth(140)
        mod_label = QLabel("Mod")
        self.mod_combo = QComboBox()
        self.mod_combo.setMinimumWidth(140)
        combo_row.addWidget(skin_label)
        combo_row.addWidget(self.skin_combo)
        combo_row.addWidget(mod_label)
        combo_row.addWidget(self.mod_combo)
        combo_row.addStretch()
        layout.addLayout(combo_row)

        # Preset dropdown
        preset_row = QHBoxLayout()
        preset_row.setSpacing(12)
        preset_label = QLabel("Preset")
        self.entry_preset_combo = QComboBox()
        self.entry_preset_combo.setMinimumWidth(200)
        preset_row.addWidget(preset_label)
        preset_row.addWidget(self.entry_preset_combo)
        preset_row.addStretch()
        layout.addLayout(preset_row)

        # Add button (right-aligned)
        add_row = QHBoxLayout()
        add_row.addStretch()
        self.add_entry_btn = QPushButton("Add")
        add_row.addWidget(self.add_entry_btn)
        layout.addLayout(add_row)

        # Tab connections
        self.entry_create_tab.clicked.connect(
            lambda: set_tab(self.entry_create_tab, self.entry_edit_tab)
        )
        self.entry_edit_tab.clicked.connect(
            lambda: set_tab(self.entry_edit_tab, self.entry_create_tab)
        )
        set_tab(self.entry_create_tab, self.entry_edit_tab)

        return layout

    def _build_preset_creator(self) -> QVBoxLayout:
        """Bottom-left: create or edit a preset by name."""
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Edit | Create tabs
        tab_row = QHBoxLayout()
        tab_row.setSpacing(0)
        self.preset_edit_tab = QPushButton("Edit")
        self.preset_create_tab = QPushButton("Create")
        tab_row.addWidget(self.preset_edit_tab)
        tab_row.addWidget(self.preset_create_tab)
        tab_row.addStretch()
        layout.addLayout(tab_row)

        self.preset_name_input = QLineEdit()
        self.preset_name_input.setPlaceholderText("Preset Name")
        layout.addWidget(self.preset_name_input)

        create_row = QHBoxLayout()
        create_row.addStretch()
        self.create_preset_btn = QPushButton("Create")
        create_row.addWidget(self.create_preset_btn)
        layout.addLayout(create_row)

        # Tab connections
        self.preset_create_tab.clicked.connect(
            lambda: set_tab(self.preset_create_tab, self.preset_edit_tab)
        )
        self.preset_edit_tab.clicked.connect(
            lambda: set_tab(self.preset_edit_tab, self.preset_create_tab)
        )
        set_tab(self.preset_create_tab, self.preset_edit_tab)

        return layout

    # ── Right section ─────────────────────────────────────────

    def _build_right_section(self) -> QVBoxLayout:
        """Right panel: manage preset/combo associations."""
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Add | Delete tab buttons
        tab_row = QHBoxLayout()
        tab_row.setSpacing(0)
        self.assoc_add_tab = QPushButton("Add")
        self.assoc_delete_tab = QPushButton("Delete")
        tab_row.addWidget(self.assoc_add_tab)
        tab_row.addWidget(self.assoc_delete_tab)
        tab_row.addStretch()
        layout.addLayout(tab_row)

        # Preset dropdown
        preset_row = QHBoxLayout()
        preset_row.setSpacing(12)
        preset_label = QLabel("Preset")
        self.assoc_preset_combo = QComboBox()
        self.assoc_preset_combo.setMinimumWidth(200)
        preset_row.addWidget(preset_label)
        preset_row.addWidget(self.assoc_preset_combo)
        preset_row.addStretch()
        layout.addLayout(preset_row)

        # Combo dropdown
        combo_row = QHBoxLayout()
        combo_row.setSpacing(12)
        combo_label = QLabel("Combo")
        self.assoc_combo_combo = QComboBox()
        self.assoc_combo_combo.setMinimumWidth(200)
        combo_row.addWidget(combo_label)
        combo_row.addWidget(self.assoc_combo_combo)
        combo_row.addStretch()
        layout.addLayout(combo_row)

        delete_row = QHBoxLayout()
        delete_row.addStretch()
        self.assoc_delete_btn = QPushButton("Delete")
        self.assoc_delete_btn.setObjectName("danger")
        delete_row.addWidget(self.assoc_delete_btn)
        layout.addLayout(delete_row)

        layout.addStretch()

        # Tab connections
        self.assoc_add_tab.clicked.connect(
            lambda: set_tab(self.assoc_add_tab, self.assoc_delete_tab)
        )
        self.assoc_delete_tab.clicked.connect(
            lambda: set_tab(self.assoc_delete_tab, self.assoc_add_tab)
        )
        set_tab(self.assoc_add_tab, self.assoc_delete_tab)

        return layout
