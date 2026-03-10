from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QLineEdit, QCheckBox,
    QHBoxLayout, QVBoxLayout, QComboBox, QMessageBox, QCompleter
)
from PySide6.QtCore import Qt, QObject, QEvent, QTimer


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


class _PanelsMixin:
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
