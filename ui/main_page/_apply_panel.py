from PySide6.QtWidgets import QFrame, QPushButton, QComboBox, QVBoxLayout, QHBoxLayout, QCompleter
from PySide6.QtCore import Qt, QObject, QEvent, QTimer

from modding.apply_mod import apply_mod
from modding.ui.load_json_lists import load_json_list
from modding.path_dictionary import skin_dict, mod_dict
from error_handler.ensure_exception import ensure_exception

from core.variable_manager import program_variables
_SKIN_LIST_PATH = program_variables.skin_list_path
_MOD_LIST_PATH = program_variables.mod_list_path


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


class ApplyPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sub_panel")
        self.setStyleSheet(
            "QFrame#sub_panel { border: 1.5px solid #5a5549; border-radius: 8px; }"
        )
        self.setFixedWidth(260)
        self._build()
        self.hide()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        _combo_style = "QComboBox { padding: 6px 16px; }"

        self.skin_combo = QComboBox()
        load_json_list(self.skin_combo, _SKIN_LIST_PATH, skin_dict)
        self.skin_combo.setEditable(True)
        self.skin_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.skin_combo.lineEdit().setPlaceholderText("Select Skin")
        self.skin_combo.setCurrentIndex(-1)
        self.skin_combo.setMinimumWidth(200)
        self.skin_combo.setStyleSheet(_combo_style)
        _skin_completer = QCompleter(self.skin_combo.model(), self.skin_combo)
        _skin_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        _skin_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.skin_combo.setCompleter(_skin_completer)
        self.skin_combo.lineEdit().installEventFilter(_SelectAllFilter(self.skin_combo, self))
        self.skin_combo.lineEdit().textEdited.connect(
            lambda t: (self.skin_combo.completer().setCompletionPrefix(""), self.skin_combo.completer().complete()) if not t else None
        )

        self.mod_combo = QComboBox()
        load_json_list(self.mod_combo, _MOD_LIST_PATH, mod_dict)
        self.mod_combo.setEditable(True)
        self.mod_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.mod_combo.lineEdit().setPlaceholderText("Select Mod")
        self.mod_combo.setCurrentIndex(-1)
        self.mod_combo.setMinimumWidth(200)
        self.mod_combo.setStyleSheet(_combo_style)
        _mod_completer = QCompleter(self.mod_combo.model(), self.mod_combo)
        _mod_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        _mod_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.mod_combo.setCompleter(_mod_completer)
        self.mod_combo.lineEdit().installEventFilter(_SelectAllFilter(self.mod_combo, self))
        self.mod_combo.lineEdit().textEdited.connect(
            lambda t: (self.mod_combo.completer().setCompletionPrefix(""), self.mod_combo.completer().complete()) if not t else None
        )

        action_row = QHBoxLayout()
        action_row.setSpacing(8)
        self.unmod_btn = QPushButton("Unmod")
        self.unmod_btn.setObjectName("danger")
        self.action_apply_btn = QPushButton("Apply")
        action_row.addWidget(self.unmod_btn)
        action_row.addStretch()
        action_row.addWidget(self.action_apply_btn)

        self.action_apply_btn.clicked.connect(self._on_apply)

        layout.addWidget(self.skin_combo)
        layout.addWidget(self.mod_combo)
        layout.addLayout(action_row)

    def _on_apply(self):
        skin, mod = None, None
        def get_items_to_mod():
            nonlocal skin, mod
            skin = skin_dict[self.skin_combo.currentData()]
            mod = mod_dict[self.mod_combo.currentData()]

        ensure_exception(get_items_to_mod, ())

        if skin and mod:
            ensure_exception(apply_mod, ({skin: mod}))

    def toggle(self):
        self.setVisible(not self.isVisible())