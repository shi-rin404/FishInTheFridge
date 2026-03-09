from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QLineEdit, QCheckBox,
    QHBoxLayout, QVBoxLayout, QComboBox, QStackedWidget, QCompleter, QMessageBox,
    QInputDialog
)
from PySide6.QtCore import Qt, QPoint, QObject, QEvent, QTimer


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

from typing import Literal

from .._style import COMMON_STYLE, set_tab
from .._widgets import WindowControls

class ManageModSkinPage(QWidget):
    """
    Two modes switched by Manage | Add tabs:
      - Manage mode  : lists saved M/S entries (dropdown + Edit + Delete)
      - Add mode   : form to add or save a new/edited entry
    Clicking "Manage" in the list forwards to the Add form in save-mode.
    """

    manage_mod_skin_page = None
    def __init__(self, editor_mode=Literal["skin", "mod"], parent=None):
        manage_mod_skin_page = self
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

        self.manage_tab = QPushButton("Manage")
        self.add_tab = QPushButton("Add")

        tab_row.addWidget(self.manage_tab)
        tab_row.addWidget(self.add_tab)
        tab_row.addStretch()

        self.type_combo = QComboBox()
        self.type_combo.setMinimumWidth(140)
        self.type_combo.currentTextChanged.connect(self._on_type_combo_changed)
        tab_row.addWidget(self.type_combo)

        root.addLayout(tab_row)

        # ── Stacked content ───────────────────────────────────
        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_edit_panel())
        self.stack.addWidget(self._build_add_panel())
        root.addWidget(self.stack)
        root.addStretch()

        # ── Tab connections ───────────────────────────────────
        self.manage_tab.clicked.connect(self._show_manage)
        self.add_tab.clicked.connect(self._show_add)

        # Default: Add tab active
        self._show_add()

    # ── Panels ────────────────────────────────────────────────
    def _build_edit_panel(self) -> QWidget:
        from core.variable_manager import program_variables
        from modding.ui.load_json_lists import load_json_list

        if self.editor_mode == "skin":
            from modding.path_dictionary import skin_dict as ms_dict
            _MS_LIST_PATH = program_variables.skin_list_path
        else:
            from modding.path_dictionary import mod_dict as ms_dict
            _MS_LIST_PATH = program_variables.mod_list_path

        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(60, 0, 60, 50)
        layout.setSpacing(10)

        ms_row = QHBoxLayout()
        ms_row.setSpacing(10)
        ms_label = QLabel(self.editor_mode.capitalize())
        self.ms_combo = QComboBox()
        load_json_list(self.ms_combo, _MS_LIST_PATH, ms_dict)
        self.ms_combo.setEditable(True)
        self.ms_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.ms_combo.lineEdit().setPlaceholderText(f"Select {self.editor_mode.capitalize()}")
        self.ms_combo.setCurrentIndex(-1)
        self.ms_combo.setMinimumWidth(220)
        _ms_completer = QCompleter(self.ms_combo.model(), self.ms_combo)
        _ms_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        _ms_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.ms_combo.setCompleter(_ms_completer)
        self.ms_combo.lineEdit().installEventFilter(_SelectAllFilter(self.ms_combo, self))
        self.ms_combo.lineEdit().textEdited.connect(
            lambda t: (self.ms_combo.completer().setCompletionPrefix(""), self.ms_combo.completer().complete()) if not t else None
        )
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

        checkbox_row = QVBoxLayout()
        checkbox_row.setSpacing(8)

        backslash_row = QHBoxLayout()
        backslash_row.setSpacing(8)

        self.backslash_check = QCheckBox("Backslash")
        self.backslash_check.setToolTip("It is needed for some of item mods, don't use it for skin mods")

        self.help_btn = QPushButton("?")
        self.help_btn.setObjectName("help_btn")
        self.help_btn.setToolTip("It is needed for some of item mods, don't use it for skin mods")
        self.help_btn.clicked.connect(lambda: QMessageBox.information(self, "Backslash Info", "It is needed for some of item mods, don't use it for skin mods"))

        self.auto_detect_check = QCheckBox("Auto Detect Type")
        self.auto_detect_check.setToolTip("It tries to detect the path you type is skin, item or accessory")

        self.save_btn = QPushButton("Save")
        self.save_btn.setObjectName("success")
        self.save_btn.clicked.connect(self.save_btn_dispatcher)

        backslash_row.addWidget(self.backslash_check)
        backslash_row.addWidget(self.help_btn)
        checkbox_row.addLayout(backslash_row)
        checkbox_row.addWidget(self.auto_detect_check)
        options_row.addLayout(checkbox_row)
        options_row.addStretch()
        options_row.addWidget(self.save_btn)

        self.quick_grab_layout = QHBoxLayout()
        self.quick_grab_layout.setSpacing(8)
        self.quick_grab_btn = QPushButton("Grab Current Skin")
        self.quick_grab_layout.addWidget(self.quick_grab_btn)
        self.quick_grab_layout.addStretch()
        from core.automatic_processes.grab_current_skin import grab_current_skin
        self.quick_grab_btn.clicked.connect(lambda: self.skin_path_input.setText(grab_current_skin()))

        from .._toggle_pin import TogglePin
        self.pin_toggle = TogglePin(parent=self, _checked=True)
        name_row = QHBoxLayout()
        name_row.setSpacing(8)
        name_row.addWidget(self.skin_name_input)
        name_row.addWidget(self.pin_toggle)

        layout.addLayout(name_row)
        layout.addWidget(self.skin_path_input)
        layout.addLayout(options_row)
        layout.addLayout(self.quick_grab_layout)
        layout.addStretch()
        return panel

    # ── Tab switching ─────────────────────────────────────────

    def _show_manage(self):
        set_tab(self.manage_tab, self.add_tab)
        self.stack.setCurrentIndex(0)
        self.type_combo.setVisible(False)
        self._is_edit_mode = False
        self.add_tab.setText("Add")

    def _show_add(self):
        set_tab(self.add_tab, self.manage_tab)
        self.stack.setCurrentIndex(1)
        self.save_btn.setText("Save")
        self._set_add_mode(False)
        self._populate_type_combo_for_add()
        self.type_combo.setVisible(True)

    def _forward_to_edit_form(self):
        """Edit button in the list loads the selected entry into the Add form."""
        if self.editor_mode == "skin":
            from modding.path_dictionary import skin_dict as ms_dict
        else:
            from modding.path_dictionary import mod_dict as ms_dict

        selected_key = self.ms_combo.currentText()
        if not selected_key or selected_key not in ms_dict:
            return

        entry_dict = ms_dict[selected_key]
        self._edit_paths = dict(entry_dict)

        self.skin_name_input.setText(selected_key)

        self.type_combo.blockSignals(True)
        self.type_combo.clear()
        for key in entry_dict:
            self.type_combo.addItem(key)
        self.type_combo.addItem("Add New Data")
        self.type_combo.blockSignals(False)

        if entry_dict:
            first_type, first_path = next(iter(entry_dict.items()))
            self._current_type = first_type
            self.type_combo.setCurrentIndex(0)
            self.skin_path_input.setText(first_path)

        set_tab(self.add_tab, self.manage_tab)
        self.stack.setCurrentIndex(1)
        self.save_btn.setText("Save")
        self.type_combo.setVisible(True)
        self.quick_grab_btn.setVisible(False)
        self._set_add_mode(True)        

    def _set_add_mode(self, is_edit: bool):
        self._is_edit_mode = is_edit
        add_only = not is_edit
        self.backslash_check.setVisible(add_only)
        self.help_btn.setVisible(add_only)
        self.auto_detect_check.setVisible(add_only)
        self.pin_toggle.setVisible(add_only)
        self.skin_name_input.setReadOnly(is_edit)
        self.add_tab.setText("Edit" if is_edit else "Add")        

    def _populate_type_combo_for_add(self):
        self.type_combo.blockSignals(True)
        self.type_combo.clear()
        for t in ["skin", "item", "accessory"]:
            self.type_combo.addItem(t)
        self.type_combo.addItem("Add New Data")
        self.type_combo.blockSignals(False)
        self.type_combo.setCurrentIndex(0)
        self._current_type = "skin"
        self._edit_paths = {}

    def _on_type_combo_changed(self, text: str):
        if text == "Add New Data":
            self._handle_add_new_data_type()
            return

        if self._is_edit_mode:
            if self._current_type is not None:
                self._edit_paths[self._current_type] = self.skin_path_input.text()
            self.skin_path_input.setText(self._edit_paths.get(text, ""))

        self._current_type = text

    def _handle_add_new_data_type(self):
        name, ok = QInputDialog.getText(self, "New Data Type", "Enter data type name:")
        if not ok or not name.strip():
            # Revert to previous selection
            if self._current_type:
                self.type_combo.blockSignals(True)
                idx = self.type_combo.findText(self._current_type)
                if idx >= 0:
                    self.type_combo.setCurrentIndex(idx)
                self.type_combo.blockSignals(False)
            return

        new_type = name.strip().lower()
        insert_idx = self.type_combo.count() - 1  # insert before "Add New Data"

        self.type_combo.blockSignals(True)
        self.type_combo.insertItem(insert_idx, new_type)
        self.type_combo.setCurrentIndex(insert_idx)
        self.type_combo.blockSignals(False)

        if self._is_edit_mode:
            if self._current_type is not None:
                self._edit_paths[self._current_type] = self.skin_path_input.text()
            self._edit_paths[new_type] = ""
            self.skin_path_input.setText("")

        self._current_type = new_type

    # ── Save ──────────────────────────────────────────────────

    def save_for_skin(self):
        from file_io.output.edit_json import merge_dict_json
        from core.variable_manager import program_variables

        data_type = self.type_combo.currentText()
        if data_type == "Add New Data":
            self._handle_add_new_data_type()
            data_type = self.type_combo.currentText()
            if data_type == "Add New Data":
                return
        if not data_type:
            QMessageBox.warning(self, "Missing Data Type", "Please select a data type.")
            return

        if self._is_edit_mode:
            skin_path = self.skin_path_input.text()
        else:
            skin_path = self.skin_path_input.text().replace("/", "\\") if self.backslash_check.isChecked() else self.skin_path_input.text().replace("\\", "/")
            if self.auto_detect_check.isChecked():
                data_type = self.path_type_detector(skin_path)
                if data_type == "other":
                    QMessageBox.warning(
                        self, "Auto Detect Failed",
                        "Could not determine the data type from the path.\nPlease select the type manually using the type selector."
                    )
                    self.auto_detect_check.setChecked(False)
                    return

        skin_info_dict = {
            data_type: skin_path
        }

        merge_dict_json(
            program_variables.skin_list_path,
            self.skin_name_input.text(),
            skin_info_dict
        )

        from modding.update_ms_lists import update_ms_list
        update_ms_list("skin")

        if self._is_edit_mode:
            self._edit_paths[data_type] = skin_path
        else:
            if not self.pin_toggle.isChecked():
                self.skin_name_input.setText("")
            self.skin_path_input.setText("")
            self.backslash_check.setChecked(False)

    def save_for_mod(self):
        pass

    def save_btn_dispatcher(self):
        if self.editor_mode == "skin":
            self.save_for_skin()

        elif self.editor_mode == "mod":
            self.save_for_mod()

    def path_type_detector(self, path: str) -> Literal["skin", "item", "accessory", "other"]:
        import re

        if (("player" in path) or ("boss" in path)) and re.search(r"\w+_[cde]_[^_]+\.gim$", path):
            return "skin"
        elif "prop" in path:
            return "item"
        elif "guajian" in path:
            return "accessory"
        else:
            return "other"
