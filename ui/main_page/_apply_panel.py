from PySide6.QtWidgets import QFrame, QPushButton, QComboBox, QVBoxLayout, QHBoxLayout, QCompleter, QWidget, QMessageBox
from PySide6.QtCore import Qt, QObject, QEvent, QRect, QTimer
from PySide6.QtGui import QCursor

from modding.apply_mod import apply_mod
from modding.ui.load_json_lists import load_json_list
from modding.path_dictionary import skin_dict, mod_dict
from error_handler.ensure_exception import ensure_exception

from core.variable_manager import program_variables
from .._style import MUTED, COMMON_STYLE
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


class _ForcePopup(QFrame):
    """Frameless Popup that tracks whether it was closed by a click on the
    dropdown arrow button, so the button's clicked signal can skip re-opening."""

    def __init__(self, dropdown_btn: QPushButton):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.Popup | Qt.FramelessWindowHint)
        self._dropdown_btn = dropdown_btn
        self.closed_by_dropdown = False

    def hideEvent(self, event):
        # Check cursor position while the event is still being processed —
        # this is the only reliable moment before the click is re-delivered.
        cursor_pos = QCursor.pos()
        tl = self._dropdown_btn.mapToGlobal(self._dropdown_btn.rect().topLeft())
        self.closed_by_dropdown = QRect(tl, self._dropdown_btn.size()).contains(cursor_pos)
        super().hideEvent(event)


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
        self.skin_combo.currentIndexChanged.connect(self.unmod_toggle)
        self.skin_combo.currentTextChanged.connect(self.unmod_toggle)
        self.skin_combo.currentTextChanged.connect(self._update_dropdown_btn)

        self.mod_combo = QComboBox()
        load_json_list(self.mod_combo, _MOD_LIST_PATH, mod_dict)
        self.mod_combo.setEditable(True)
        self.mod_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.mod_combo.lineEdit().setPlaceholderText("Select Mod")
        self.mod_combo.setMinimumWidth(200)
        self.mod_combo.setStyleSheet(_combo_style)
        _mod_completer = QCompleter(self.mod_combo.model(), self.mod_combo)
        _mod_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        _mod_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.mod_combo.setCompleter(_mod_completer)
        QTimer.singleShot(0, lambda: (self.mod_combo.setCurrentIndex(-1), self.mod_combo.lineEdit().clear()))
        self.mod_combo.lineEdit().installEventFilter(_SelectAllFilter(self.mod_combo, self))
        self.mod_combo.lineEdit().textEdited.connect(
            lambda t: (self.mod_combo.completer().setCompletionPrefix(""), self.mod_combo.completer().complete()) if not t else None
        )
        self.mod_combo.currentTextChanged.connect(self._update_dropdown_btn)

        action_row = QHBoxLayout()
        action_row.setSpacing(8)

        self.unmod_btn = QPushButton("Unmod")
        self.unmod_btn.setEnabled(False)
        self.unmod_btn.setStyleSheet(f"color: {MUTED}; font-size: 13px;")
        self.unmod_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.unmod_btn.setObjectName("")

        # ── Split apply button ────────────────────────────────
        self._apply_col_widget = QWidget()
        _apply_split = QHBoxLayout(self._apply_col_widget)
        _apply_split.setSpacing(0)
        _apply_split.setContentsMargins(0, 0, 0, 0)

        self.action_apply_btn = QPushButton("Apply")
        self.action_apply_btn.setEnabled(False)
        self.action_apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.action_apply_btn.setStyleSheet(
            f"QPushButton {{ border-top-right-radius: 0; border-bottom-right-radius: 0; }}"
            f"QPushButton:hover {{ border-top-right-radius: 0; border-bottom-right-radius: 0; }}"
            f"QPushButton:disabled {{ color: {MUTED}; border-top-right-radius: 0; border-bottom-right-radius: 0; }}"
        )

        self._dropdown_btn = QPushButton("▾")
        self._dropdown_btn.setFixedWidth(22)
        self._dropdown_btn.setEnabled(False)
        self._dropdown_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._dropdown_btn.setStyleSheet(
            f"QPushButton {{ border-top-left-radius: 0; border-bottom-left-radius: 0; border-left: none; padding: 8px 4px; }}"
            f"QPushButton:hover {{ border-top-left-radius: 0; border-bottom-left-radius: 0; }}"
            f"QPushButton:disabled {{ color: {MUTED}; border-top-left-radius: 0; border-bottom-left-radius: 0; }}"
        )

        _apply_split.addWidget(self.action_apply_btn)
        _apply_split.addWidget(self._dropdown_btn)

        # Popup — renders outside parent clip bounds, auto-closes on outside click
        self._force_popup = _ForcePopup(self._dropdown_btn)
        self._force_popup.setStyleSheet(COMMON_STYLE)
        _popup_layout = QVBoxLayout(self._force_popup)
        _popup_layout.setContentsMargins(0, 0, 0, 0)
        _popup_layout.setSpacing(0)
        self.force_apply_btn = QPushButton("Force Apply")
        self.force_apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.force_apply_btn.setStyleSheet("QPushButton { font-size: 11px; padding: 8px 6px; }")
        _popup_layout.addWidget(self.force_apply_btn)
        # ─────────────────────────────────────────────────────

        action_row.addWidget(self.unmod_btn)
        action_row.addStretch()
        action_row.addWidget(self._apply_col_widget)

        self.action_apply_btn.clicked.connect(self._on_apply)
        self.unmod_btn.clicked.connect(self._on_unmod)
        self._dropdown_btn.clicked.connect(self._toggle_force_apply)
        self.force_apply_btn.clicked.connect(self._on_force_apply)

        layout.addWidget(self.skin_combo)
        layout.addWidget(self.mod_combo)
        layout.addLayout(action_row)

    def _on_apply(self):
        skin_name = self.skin_combo.currentText()
        mod_name  = self.mod_combo.currentText()

        skin_record = skin_dict.get(skin_name)
        mod_record  = mod_dict.get(mod_name)

        if not skin_record or not mod_record:
            return

        original_to_mod = {
            skin_record[k]: mod_record[k]
            for k in skin_record
            if k in mod_record
        }

        if original_to_mod:
            ensure_exception(apply_mod, (original_to_mod,))

    def _on_unmod(self):
        skin_name = self.skin_combo.currentText()
        if skin_name not in skin_dict:
            return
        from modding.modder import unmod_skin
        ensure_exception(unmod_skin, (skin_name,))

    def _toggle_force_apply(self):
        if self._force_popup.closed_by_dropdown:
            # Qt already closed the popup (via Popup mechanism) when the user
            # pressed ▾ — don't reopen it on the subsequent release/clicked.
            self._force_popup.closed_by_dropdown = False
            return
        col_global = self._apply_col_widget.mapToGlobal(
            self._apply_col_widget.rect().bottomLeft()
        )
        self._force_popup.adjustSize()
        self._force_popup.setFixedWidth(self._apply_col_widget.width())
        self._force_popup.move(col_global.x(), col_global.y() + 4)
        self._force_popup.show()

    def _on_force_apply(self):
        self._force_popup.hide()

        skin_name = self.skin_combo.currentText()
        mod_name  = self.mod_combo.currentText()
        skin_record = skin_dict.get(skin_name)
        mod_record  = mod_dict.get(mod_name)
        if not skin_record or not mod_record:
            QMessageBox.warning(self, "Nothing Selected", "Please select a valid skin and mod before applying.")
            return

        original_to_mod = {
            skin_record[k]: mod_record[k]
            for k in skin_record
            if k in mod_record
        }
        if original_to_mod:
            # Wrapper keeps __name__ == "apply_mod" so ensure_exception dispatches correctly
            def apply_mod_force(m):
                return apply_mod(m, force=True)
            apply_mod_force.__name__ = "apply_mod"
            ensure_exception(apply_mod_force, (original_to_mod,))

    def toggle(self):
        self.setVisible(not self.isVisible())

    def _update_dropdown_btn(self):
        both_valid = (
            self.skin_combo.currentText() in skin_dict
            and self.mod_combo.currentText() in mod_dict
        )
        self.action_apply_btn.setEnabled(both_valid)
        self._dropdown_btn.setEnabled(both_valid)

    def unmod_toggle(self):
        skin_selection_active = self.skin_combo.currentIndex() != -1

        self.unmod_btn.setEnabled(skin_selection_active)

        if skin_selection_active and self.skin_combo.currentText() in skin_dict.keys():
            self.unmod_btn.setObjectName("danger")
            self.unmod_btn.setStyleSheet("")
        else:
            self.unmod_btn.setObjectName("")
            self.unmod_btn.setStyleSheet(f"color: {MUTED}; font-size: 13px;")
