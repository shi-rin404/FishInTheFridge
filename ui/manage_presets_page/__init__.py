from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel,
    QHBoxLayout, QVBoxLayout, QStackedWidget
)
from PySide6.QtCore import Qt, QPoint

from .._style import window_style
from core.automatic_processes.update_comboboxes import update_comboboxes
from .._widgets import WindowControls, StylePaintMixin
from ._panels import _PanelsMixin
from ._save import _SaveMixin
from ._tab_logic import _TabLogicMixin


class ManagePresetsPage(StylePaintMixin, _TabLogicMixin, _SaveMixin, _PanelsMixin, QWidget):
    """
    Main tab switch: Edit | Create  (starts on Create)

    Create tab:
        Preset Name input + Create button

    Edit tab — sub-tabs: Add | Delete  (starts on Add)
        Add:    Skin + Mod + Preset combos + Add button
        Delete: Preset combo + Combo combo
    """

    manage_presets_page = None

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self.setWindowFlags(Qt.WindowType.Window | Qt.FramelessWindowHint)
        self.setObjectName("manage_presets_page")
        self.setStyleSheet(window_style("manage_presets_page"))
        self.resize(500, 380)
        self._drag_pos = QPoint()
        ManagePresetsPage.manage_presets_page = self
        self._build_ui()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and not self._drag_pos.isNull():
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(60, 50, 60, 50)
        root.setSpacing(16)

        # Title row: label left, window controls right
        title_row = QHBoxLayout()
        title = QLabel("Manage Presets")
        title.setObjectName("title")
        self.window_controls = WindowControls()
        self.window_controls.minimize_requested.connect(self.showMinimized)
        self.window_controls.close_requested.connect(self.close)
        title_row.addWidget(title)
        title_row.addStretch()
        title_row.addWidget(self.window_controls)
        root.addLayout(title_row)

        # Main tab row: Edit | Create
        tab_row = QHBoxLayout()
        tab_row.setSpacing(0)
        self.edit_tab = QPushButton("Edit")
        self.create_tab = QPushButton("Create")
        tab_row.addWidget(self.edit_tab)
        tab_row.addWidget(self.create_tab)
        tab_row.addStretch()
        root.addLayout(tab_row)

        # Main stack: index 0 = Edit panel, index 1 = Create panel
        self.main_stack = QStackedWidget()
        self.main_stack.addWidget(self._build_edit_panel())
        self.main_stack.addWidget(self._build_create_panel())
        root.addWidget(self.main_stack)

        root.addStretch()

        # Main tab connections — start on Create
        self.edit_tab.clicked.connect(self._show_edit)
        self.create_tab.clicked.connect(self._show_create)
        self._show_create()

        # Action buttons
        self.create_preset_btn.clicked.connect(self._on_create_preset)
        self.add_entry_btn.clicked.connect(self._on_add_entry)
        self.delete_entry_btn.clicked.connect(self._on_delete)

        # Populate assoc_combo_combo when a preset is selected in Delete tab
        self.assoc_preset_combo.currentIndexChanged.connect(
            lambda _: self._reload_assoc_combos(self.assoc_preset_combo.currentText())
        )

        # Initial load of preset combos
        update_comboboxes("preset")
