from PySide6.QtWidgets import QWidget, QPushButton, QLabel, QHBoxLayout, QVBoxLayout, QComboBox, QStackedWidget
from PySide6.QtCore import Qt, QPoint

from .._style import COMMON_STYLE
from .._widgets import WindowControls
from ._panels import _PanelsMixin
from ._tab_logic import _TabLogicMixin
from ._type_combo import _TypeComboMixin
from ._save import _SaveMixin

from typing import Literal


class ManageModSkinPage(_SaveMixin, _TypeComboMixin, _TabLogicMixin, _PanelsMixin, QWidget):
    """
    Two modes switched by Manage | Add tabs:
      - Manage mode : lists saved M/S entries (dropdown + Edit + Delete)
      - Add mode    : form to add or save a new/edited entry
    Clicking "Edit" in the Manage panel forwards to the Add form in edit-mode.
    """

    manage_mod_skin_page = None

    def __init__(self, editor_mode=Literal["skin", "mod"], parent=None):
        ManageModSkinPage.manage_mod_skin_page = self
        super().__init__(parent, Qt.Window)
        self.setStyleSheet(COMMON_STYLE)
        self.resize(500, 300)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self._drag_pos = QPoint()
        self.editor_mode = editor_mode
        self._is_edit_mode = False
        self._edit_paths = {}
        self._current_type = None
        self._build_ui()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and not self._drag_pos.isNull():
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)

        # ── Window controls ───────────────────────────────────
        wc_row = QHBoxLayout()
        wc_row.setContentsMargins(0, 10, 10, 0)
        wc_row.setSpacing(12)
        self.window_controls = WindowControls()
        self.window_controls.minimize_requested.connect(self.showMinimized)
        self.window_controls.close_requested.connect(self.close)
        wc_row.addStretch()
        wc_row.addWidget(self.window_controls)
        root.addLayout(wc_row)

        # ── Title ─────────────────────────────────────────────
        title_row = QHBoxLayout()
        title_row.setContentsMargins(60, 0, 60, 0)
        title = QLabel(f"Manage {self.editor_mode.capitalize()}")
        title.setObjectName("title")
        title_row.addWidget(title)
        root.addLayout(title_row)

        # ── Tab row ───────────────────────────────────────────
        tab_row = QHBoxLayout()
        tab_row.setContentsMargins(60, 0, 60, 0)
        tab_row.setSpacing(0)

        self.manage_tab = QPushButton("Manage")
        self.add_tab = QPushButton("Edit" if self.editor_mode == "mod" else "Add")
        tab_row.addWidget(self.manage_tab)
        tab_row.addWidget(self.add_tab)
        tab_row.addStretch()

        self.type_combo = QComboBox()
        self.type_combo.setMinimumWidth(140)
        self.type_combo.currentTextChanged.connect(self._on_type_combo_changed)
        tab_row.addWidget(self.type_combo)

        root.addLayout(tab_row)

        # ── Stacked panels ────────────────────────────────────
        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_edit_panel())
        self.stack.addWidget(self._build_add_panel())
        root.addWidget(self.stack)
        root.addStretch()

        # ── Tab connections ───────────────────────────────────
        self.manage_tab.clicked.connect(self._show_manage)
        if self.editor_mode == "mod":
            self.add_tab.clicked.connect(self._forward_to_edit_form)
            self._show_manage()
        elif self.editor_mode == "skin":
            self.add_tab.clicked.connect(self._show_add)
            self._show_add()
        else:
            raise ValueError(f"Invalid editor mode: {self.editor_mode}")