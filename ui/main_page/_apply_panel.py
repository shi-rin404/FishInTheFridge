from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QCompleter,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt, QObject, QEvent, QRect, QSize, QTimer
from PySide6.QtGui import QCursor, QIcon

from modding.apply_mod import apply_mod
from modding.ui.load_json_lists import load_json_list
from modding.path_dictionary import (
    NO_CHARACTER_INFO,
    character_dict,
    skin_dict,
    mod_dict,
)

from core.variable_manager import program_variables
from .._style import BG, BORDER, MUTED, TEXT, COMMON_STYLE
_SKIN_LIST_PATH = program_variables.skin_list_path
_MOD_LIST_PATH = program_variables.mod_list_path


def _invert_hex(color: str) -> str:
    color = color.lstrip("#")
    if len(color) != 6:
        return "#000000"
    return "#" + "".join(
        f"{255 - int(color[idx:idx + 2], 16):02X}"
        for idx in range(0, 6, 2)
    )


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
        self.setFixedWidth(300)
        self._character_filter_active = False
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

        self._filter_col_widget = QWidget()
        _filter_split = QHBoxLayout(self._filter_col_widget)
        _filter_split.setSpacing(0)
        _filter_split.setContentsMargins(0, 0, 0, 0)

        self.character_filter_btn = QPushButton()
        self.character_filter_btn.setIcon(QIcon("assets/filter.png"))
        self.character_filter_btn.setIconSize(QSize(22, 22))
        self.character_filter_btn.setFixedWidth(34)
        self.character_filter_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.character_filter_dropdown_btn = QPushButton("▼")
        self.character_filter_dropdown_btn.setFixedWidth(22)
        self.character_filter_dropdown_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        _filter_split.addWidget(self.character_filter_btn)
        _filter_split.addWidget(self.character_filter_dropdown_btn)

        self._filter_popup = _ForcePopup(self.character_filter_dropdown_btn)
        self._filter_popup.setStyleSheet(COMMON_STYLE)
        _filter_popup_layout = QVBoxLayout(self._filter_popup)
        _filter_popup_layout.setContentsMargins(8, 8, 8, 8)
        _filter_popup_layout.setSpacing(6)
        _filter_popup_layout.addWidget(QLabel("Character:"))
        self.character_filter_combo = QComboBox()
        self.character_filter_combo.setMinimumWidth(180)
        self.character_filter_combo.setStyleSheet(_combo_style)
        _filter_popup_layout.addWidget(self.character_filter_combo)
        self._refresh_character_filter_options()
        self._update_character_filter_btn()

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

        self._dropdown_btn = QPushButton("▼")
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
        self.character_filter_btn.clicked.connect(self._on_character_filter_clicked)
        self.character_filter_dropdown_btn.clicked.connect(self._toggle_filter_popup)
        self.character_filter_combo.currentTextChanged.connect(self._on_character_filter_changed)

        skin_row = QHBoxLayout()
        skin_row.setSpacing(6)
        skin_row.addWidget(self.skin_combo, stretch=1)
        skin_row.addWidget(self._filter_col_widget)
        layout.addLayout(skin_row)
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
            from ui.main_page import MainPage
            _feedback = MainPage.main_page.top_row.set_apply_feedback
            _feedback("Searching for skin pathes..")
            QApplication.processEvents()
            try:
                apply_mod(original_to_mod)
                _feedback("Modded successfully", success=True)
            except Exception:
                _feedback("An error occured upon modding", error=True)
                raise

    def _on_unmod(self):
        skin_name = self.skin_combo.currentText()
        if skin_name not in skin_dict:
            return
        from modding.modder import unmod_skin
        from ui.main_page import MainPage
        _feedback = MainPage.main_page.top_row.set_apply_feedback
        try:
            unmod_skin(skin_name)
            _feedback("The mod is removed", success=True)
        except Exception:
            _feedback("An error occured upon modding", error=True)
            raise

    def _toggle_force_apply(self):
        if self._force_popup.closed_by_dropdown:
            # Qt already closed the popup (via Popup mechanism) when the user
            # pressed the dropdown arrow; skip re-opening on clicked.
            self._force_popup.closed_by_dropdown = False
            return
        col_global = self._apply_col_widget.mapToGlobal(
            self._apply_col_widget.rect().bottomLeft()
        )
        self._force_popup.adjustSize()
        self._force_popup.setFixedWidth(self._apply_col_widget.width())
        self._force_popup.move(col_global.x(), col_global.y() + 4)
        self._force_popup.show()

    def refresh_mod_filter(self):
        self._refresh_character_filter_options()
        self._apply_character_filter()

    def _refresh_character_filter_options(self):
        current_text = self.character_filter_combo.currentText() or NO_CHARACTER_INFO
        character_names = [NO_CHARACTER_INFO]
        character_names.extend(
            sorted(
                name for name in character_dict.keys()
                if name != NO_CHARACTER_INFO
            )
        )
        self.character_filter_combo.blockSignals(True)
        self.character_filter_combo.clear()
        self.character_filter_combo.addItems(character_names)
        index = self.character_filter_combo.findText(current_text)
        self.character_filter_combo.setCurrentIndex(index if index != -1 else 0)
        self.character_filter_combo.blockSignals(False)

    def _on_character_filter_clicked(self):
        self._character_filter_active = not self._character_filter_active
        self._update_character_filter_btn()
        self._apply_character_filter()
        if self._character_filter_active:
            self._show_filter_popup()

    def _on_character_filter_changed(self):
        if self._character_filter_active:
            self._apply_character_filter()

    def _toggle_filter_popup(self):
        if self._filter_popup.closed_by_dropdown:
            self._filter_popup.closed_by_dropdown = False
            return
        self._show_filter_popup()

    def _show_filter_popup(self):
        col_global = self._filter_col_widget.mapToGlobal(
            self._filter_col_widget.rect().bottomLeft()
        )
        self._filter_popup.adjustSize()
        self._filter_popup.setFixedWidth(max(self._filter_col_widget.width(), 210))
        self._filter_popup.move(col_global.x(), col_global.y() + 4)
        self._filter_popup.show()

    def _update_character_filter_btn(self):
        active_bg = _invert_hex(BG)
        active_text = _invert_hex(TEXT)
        active_border = _invert_hex(BORDER)
        filter_style = (
            "QPushButton { border-top-right-radius: 0; border-bottom-right-radius: 0;"
            " padding: 8px 4px; }"
            "QPushButton:hover { border-top-right-radius: 0; border-bottom-right-radius: 0; }"
        )
        if self._character_filter_active:
            filter_style = (
                f"QPushButton {{ background-color: {active_bg}; color: {active_text};"
                f" border-color: {active_border}; border-top-right-radius: 0;"
                " border-bottom-right-radius: 0; padding: 8px 4px; }}"
                f"QPushButton:hover {{ background-color: {active_bg}; }}"
            )
        dropdown_style = (
            "QPushButton { border-top-left-radius: 0; border-bottom-left-radius: 0;"
            " border-left: none; padding: 8px 4px; }"
            "QPushButton:hover { border-top-left-radius: 0; border-bottom-left-radius: 0; }"
        )
        self.character_filter_btn.setStyleSheet(filter_style)
        self.character_filter_dropdown_btn.setStyleSheet(dropdown_style)

    def _filtered_mod_names(self) -> list[str]:
        if not self._character_filter_active:
            return list(mod_dict.keys())
        character = self.character_filter_combo.currentText() or NO_CHARACTER_INFO
        allowed_names = set(character_dict.get(character, {}).get("mods", []))
        return [name for name in mod_dict.keys() if name in allowed_names]

    def _filtered_skin_names(self) -> list[str]:
        if not self._character_filter_active:
            return list(skin_dict.keys())
        character = self.character_filter_combo.currentText() or NO_CHARACTER_INFO
        allowed_names = set(character_dict.get(character, {}).get("skins", []))
        return [name for name in skin_dict.keys() if name in allowed_names]

    def _reload_combo_items(
        self,
        combo: QComboBox,
        records: dict,
        names: list[str],
    ) -> None:
        current_text = combo.currentText()
        combo.blockSignals(True)
        combo.clear()
        for name in names:
            combo.addItem(name, userData=records[name])
        index = combo.findText(current_text)
        if index != -1:
            combo.setCurrentIndex(index)
        else:
            combo.setCurrentIndex(-1)
            combo.lineEdit().clear()
        combo.blockSignals(False)
        combo.completer().setModel(combo.model())

    def _apply_character_filter(self):
        self._reload_combo_items(
            self.skin_combo,
            skin_dict,
            self._filtered_skin_names(),
        )
        self._reload_combo_items(
            self.mod_combo,
            mod_dict,
            self._filtered_mod_names(),
        )
        self.unmod_toggle()
        self._update_dropdown_btn()

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
            from ui.main_page import MainPage
            _feedback = MainPage.main_page.top_row.set_apply_feedback
            _feedback("Searching for skin pathes..")
            QApplication.processEvents()
            try:
                apply_mod(original_to_mod, force=True)
                _feedback("Force applied successfully", success=True)
            except Exception:
                _feedback("An error occured upon modding", error=True)
                raise

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
