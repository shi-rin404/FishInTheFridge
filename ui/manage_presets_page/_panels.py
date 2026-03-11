from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QLineEdit, QCheckBox,
    QHBoxLayout, QVBoxLayout, QComboBox, QStackedWidget, QCompleter
)
from PySide6.QtCore import Qt, QObject, QEvent, QTimer

_COMBO_STYLE = "QComboBox { padding: 6px 16px; }"


def _set_btn_active(btn: QPushButton, enabled: bool, style_name: str) -> None:
    """Enable/disable a button and apply its named style only when active."""
    btn.setEnabled(enabled)
    btn.setObjectName(style_name if enabled else "")
    btn.style().unpolish(btn)
    btn.style().polish(btn)
    btn.update()


class _SelectAllFilter(QObject):
    def __init__(self, combo, parent=None):
        super().__init__(parent)
        self._combo = combo

    def _show_all_completions(self):
        c = self._combo.completer()
        c.setCompletionPrefix("")
        c.complete()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.FocusIn:
            QTimer.singleShot(0, obj.selectAll)
        elif event.type() == QEvent.Type.MouseButtonRelease:
            obj.selectAll()
            if not obj.text():
                self._show_all_completions()
        return super().eventFilter(obj, event)


def _setup_editable_combo(
    combo: QComboBox, placeholder: str, parent, no_items_text: str = ""
) -> None:
    """Apply the standard editable-combo pattern (completer, style, select-all).

    If *no_items_text* is provided the placeholder switches between that and
    *placeholder* depending on whether the model has any items.
    """
    combo.setEditable(True)
    combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
    combo.setCurrentIndex(-1)
    combo.setStyleSheet(_COMBO_STYLE)
    completer = QCompleter(combo.model(), combo)
    completer.setFilterMode(Qt.MatchFlag.MatchContains)
    completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
    combo.setCompleter(completer)
    combo.lineEdit().installEventFilter(_SelectAllFilter(combo, parent))
    combo.lineEdit().textEdited.connect(
        lambda t: (combo.completer().setCompletionPrefix(""), combo.completer().complete()) if not t else None
    )

    if no_items_text:
        def _refresh_placeholder(*_):
            combo.lineEdit().setPlaceholderText(
                placeholder if combo.count() > 0 else no_items_text
            )
        combo.model().rowsInserted.connect(_refresh_placeholder)
        combo.model().rowsRemoved.connect(_refresh_placeholder)
        _refresh_placeholder()
    else:
        combo.lineEdit().setPlaceholderText(placeholder)


class _PanelsMixin:

    # ── Create panel ──────────────────────────────────────────

    def _build_create_panel(self) -> QWidget:
        """Create tab: Preset Name input + Create button."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)

        self.preset_name_input = QLineEdit()
        self.preset_name_input.setPlaceholderText("Preset Name")
        layout.addWidget(self.preset_name_input)

        create_row = QHBoxLayout()
        create_row.addStretch()
        self.create_preset_btn = QPushButton("Create")
        _set_btn_active(self.create_preset_btn, False, "success")
        create_row.addWidget(self.create_preset_btn)
        layout.addLayout(create_row)

        self.preset_name_input.textChanged.connect(
            lambda t: _set_btn_active(self.create_preset_btn, bool(t.strip()), "success")
        )

        layout.addStretch()
        return panel

    # ── Edit panel (contains Add | Delete sub-tabs) ───────────

    def _build_edit_panel(self) -> QWidget:
        """Edit tab: Add | Delete sub-tabs with stacked content."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)

        # Sub-tab row: Add | Delete  +  Preset combo (visible on Add only)
        sub_tab_row = QHBoxLayout()
        sub_tab_row.setSpacing(0)
        self.add_tab = QPushButton("Add")
        self.delete_tab = QPushButton("Delete")
        sub_tab_row.addWidget(self.add_tab)
        sub_tab_row.addWidget(self.delete_tab)
        sub_tab_row.addStretch()
        self.entry_preset_combo = QComboBox()
        self.entry_preset_combo.setMinimumWidth(140)
        _setup_editable_combo(self.entry_preset_combo, "Select Preset", self, "No Presets")
        sub_tab_row.addWidget(self.entry_preset_combo)
        layout.addLayout(sub_tab_row)

        # Sub-stack: index 0 = Add, index 1 = Delete
        self.edit_stack = QStackedWidget()
        self.edit_stack.addWidget(self._build_add_panel())
        self.edit_stack.addWidget(self._build_delete_panel())
        layout.addWidget(self.edit_stack)

        layout.addStretch()

        # Sub-tab connections — start from Add
        self.add_tab.clicked.connect(self._show_add)
        self.delete_tab.clicked.connect(self._show_delete)
        self._show_add()

        # Guard: Add enabled only when Skin, Mod, and Preset all have a selection
        def _check_add(*_):
            _set_btn_active(
                self.add_entry_btn,
                self.skin_combo.currentIndex() != -1
                and self.mod_combo.currentIndex() != -1
                and self.entry_preset_combo.currentIndex() != -1,
                "success",
            )
        self.skin_combo.currentIndexChanged.connect(_check_add)
        self.mod_combo.currentIndexChanged.connect(_check_add)
        self.entry_preset_combo.currentIndexChanged.connect(_check_add)

        return panel

    # ── Add sub-panel ─────────────────────────────────────────

    def _build_add_panel(self) -> QWidget:
        """Add sub-tab: Skin + Mod combos + Add button."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)

        # Skin + Mod side by side
        from modding.ui.load_json_lists import load_json_list
        from modding.path_dictionary import skin_dict, mod_dict
        from core.variable_manager import program_variables

        combo_row = QHBoxLayout()
        combo_row.setSpacing(12)
        skin_label = QLabel("Skin")                
        self.skin_combo = QComboBox()
        load_json_list(self.skin_combo, program_variables.skin_list_path, skin_dict)
        self.skin_combo.setMinimumWidth(140)
        _setup_editable_combo(self.skin_combo, "Select Skin", self, "No Skins")
        mod_label = QLabel("Mod")
        self.mod_combo = QComboBox()
        load_json_list(self.mod_combo, program_variables.mod_list_path, mod_dict)
        self.mod_combo.setMinimumWidth(140)
        _setup_editable_combo(self.mod_combo, "Select Mod", self, "No Mods")
        combo_row.addWidget(skin_label)
        combo_row.addWidget(self.skin_combo)
        combo_row.addWidget(mod_label)
        combo_row.addWidget(self.mod_combo)
        combo_row.addStretch()
        layout.addLayout(combo_row)

        # Add button
        add_row = QHBoxLayout()
        add_row.addStretch()
        self.add_entry_btn = QPushButton("Add")
        _set_btn_active(self.add_entry_btn, False, "success")
        add_row.addWidget(self.add_entry_btn)
        layout.addLayout(add_row)

        return panel

    # ── Delete sub-panel ──────────────────────────────────────

    def _build_delete_panel(self) -> QWidget:
        """Delete sub-tab: Preset combo + Combo combo + Delete button."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)

        # Preset combo + "Delete Preset" checkbox
        preset_row = QHBoxLayout()
        preset_row.setSpacing(12)
        preset_label = QLabel("Preset")
        self.assoc_preset_combo = QComboBox()
        self.assoc_preset_combo.setMinimumWidth(200)
        _setup_editable_combo(self.assoc_preset_combo, "Select Preset", self, "No Presets")
        self.delete_preset_check = QCheckBox("Delete Preset")
        preset_row.addWidget(preset_label)
        preset_row.addWidget(self.assoc_preset_combo)
        preset_row.addStretch()
        preset_row.addWidget(self.delete_preset_check)
        layout.addLayout(preset_row)

        # Combo combo
        self.combo_row_widget = QWidget()
        combo_row = QHBoxLayout(self.combo_row_widget)
        combo_row.setContentsMargins(0, 0, 0, 0)
        combo_row.setSpacing(12)
        combo_label = QLabel("Combo")
        self.assoc_combo_combo = QComboBox()
        self.assoc_combo_combo.setMinimumWidth(200)
        _setup_editable_combo(self.assoc_combo_combo, "Select Combo", self, "No Combos")
        combo_row.addWidget(combo_label)
        combo_row.addWidget(self.assoc_combo_combo)
        combo_row.addStretch()
        layout.addWidget(self.combo_row_widget)

        self.delete_preset_check.toggled.connect(
            lambda checked: self.combo_row_widget.setVisible(not checked)
        )

        # Delete button
        delete_row = QHBoxLayout()
        delete_row.addStretch()
        self.delete_entry_btn = QPushButton("Delete")
        _set_btn_active(self.delete_entry_btn, False, "danger")
        delete_row.addWidget(self.delete_entry_btn)
        layout.addLayout(delete_row)

        # Guard: requires Preset; also Combo when "Delete Preset" is unchecked
        def _check_delete(*_):
            preset_ok = self.assoc_preset_combo.currentIndex() != -1
            if self.delete_preset_check.isChecked():
                enabled = preset_ok
            else:
                enabled = preset_ok and self.assoc_combo_combo.currentIndex() != -1
            _set_btn_active(self.delete_entry_btn, enabled, "danger")
        self.assoc_preset_combo.currentIndexChanged.connect(_check_delete)
        self.assoc_combo_combo.currentIndexChanged.connect(_check_delete)
        self.delete_preset_check.toggled.connect(_check_delete)

        layout.addStretch()
        return panel
