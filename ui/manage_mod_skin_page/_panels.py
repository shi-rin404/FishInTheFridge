from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QLineEdit, QCheckBox,
    QHBoxLayout, QVBoxLayout, QComboBox, QMessageBox, QCompleter, QFrame
)
from PySide6.QtCore import Qt, QObject, QEvent, QTimer, QRect
from PySide6.QtGui import QCursor

from .._style import COMMON_STYLE


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


class _GrabPopup(QFrame):
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
        self.delete_entry_btn.clicked.connect(self._delete_entry)

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
        self._preferred_data_type = None
        self._quick_grab_col_widget = QWidget()
        _quick_grab_split = QHBoxLayout(self._quick_grab_col_widget)
        _quick_grab_split.setSpacing(0)
        _quick_grab_split.setContentsMargins(0, 0, 0, 0)

        self.quick_grab_btn = QPushButton("Grab Current Skin")
        self.quick_grab_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.quick_grab_btn.setStyleSheet(
            "QPushButton { border-top-right-radius: 0; border-bottom-right-radius: 0; }"
            "QPushButton:hover { border-top-right-radius: 0; border-bottom-right-radius: 0; }"
        )

        self._quick_grab_dropdown_btn = QPushButton("▼")
        self._quick_grab_dropdown_btn.setFixedWidth(22)
        self._quick_grab_dropdown_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._quick_grab_dropdown_btn.setStyleSheet(
            "QPushButton { border-top-left-radius: 0; border-bottom-left-radius: 0; border-left: none; padding: 8px 4px; }"
            "QPushButton:hover { border-top-left-radius: 0; border-bottom-left-radius: 0; }"
        )

        _quick_grab_split.addWidget(self.quick_grab_btn)
        _quick_grab_split.addWidget(self._quick_grab_dropdown_btn)

        self._quick_grab_popup = _GrabPopup(self._quick_grab_dropdown_btn)
        self._quick_grab_popup.setStyleSheet(COMMON_STYLE)
        _popup_layout = QVBoxLayout(self._quick_grab_popup)
        _popup_layout.setContentsMargins(0, 0, 0, 0)
        _popup_layout.setSpacing(0)
        self.quick_grab_item_btn = QPushButton("Grab Current Item")
        self.quick_grab_item_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.quick_grab_item_btn.setStyleSheet("QPushButton { font-size: 11px; padding: 8px 6px; }")
        _popup_layout.addWidget(self.quick_grab_item_btn)

        self.quick_grab_layout.addWidget(self._quick_grab_col_widget)
        self.quick_grab_layout.addStretch()
        self.quick_grab_btn.clicked.connect(self._grab_current_skin)
        self._quick_grab_dropdown_btn.clicked.connect(self._toggle_quick_grab_popup)
        self.quick_grab_item_btn.clicked.connect(self._grab_current_item)

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

    def _toggle_quick_grab_popup(self):
        if self._quick_grab_popup.closed_by_dropdown:
            self._quick_grab_popup.closed_by_dropdown = False
            return
        col_global = self._quick_grab_col_widget.mapToGlobal(
            self._quick_grab_col_widget.rect().bottomLeft()
        )
        self._quick_grab_popup.adjustSize()
        self._quick_grab_popup.setFixedWidth(self._quick_grab_col_widget.width())
        self._quick_grab_popup.move(col_global.x(), col_global.y() + 4)
        self._quick_grab_popup.show()

    def _grab_current_skin(self):
        from core.automatic_processes.grab_current_skin import grab_current_skin
        self._preferred_data_type = None
        self.skin_path_input.setText(grab_current_skin())

    def _grab_current_item(self):
        from core.automatic_processes.grab_current_skin import grab_current_skin
        self._quick_grab_popup.hide()
        self._preferred_data_type = "item"
        self.skin_path_input.setText(grab_current_skin("ITEM"))
