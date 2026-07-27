from PySide6.QtWidgets import (
    QWidget, QPushButton, QComboBox, QLabel, QCompleter,
    QHBoxLayout, QVBoxLayout, QSizePolicy, QFrame
)
from PySide6.QtCore import Qt, QSize, QTimer, QRect

from .._style import SUCCESS, ORANGE, COMMON_STYLE
from PySide6.QtGui import QIcon, QPixmap, QCursor

from core.variable_manager import program_variables
from modding.ui.load_json_lists import load_json_list
from modding.path_dictionary import preset_dict


class _PresetPopup(QFrame):
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


class BottomRow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Left: preset controls ─────────────────────────────
        from ._apply_panel import _SelectAllFilter

        preset_col = QVBoxLayout()
        preset_col.setSpacing(8)

        preset_row = QHBoxLayout()
        preset_row.setSpacing(8)
        preset_label = QLabel("Active Mod Preset")

        self.preset_combo = QComboBox()
        load_json_list(self.preset_combo, program_variables.presets_path, preset_dict)
        self.preset_combo.setEditable(True)
        self.preset_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.preset_combo.lineEdit().setPlaceholderText("Select Preset" if preset_dict else "No Presets")
        self.preset_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.preset_combo.setMinimumWidth(160)
        QTimer.singleShot(0, lambda: (
            self.preset_combo.setCurrentIndex(-1),
            self.preset_combo.lineEdit().clear()
        ))

        _preset_completer = QCompleter(self.preset_combo.model(), self.preset_combo)
        _preset_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        _preset_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.preset_combo.setCompleter(_preset_completer)
        self.preset_combo.lineEdit().installEventFilter(
            _SelectAllFilter(self.preset_combo, self)
        )
        self.preset_combo.lineEdit().textEdited.connect(
            lambda t: (
                self.preset_combo.completer().setCompletionPrefix(""),
                self.preset_combo.completer().complete()
            ) if not t else None
        )

        [preset_row.addWidget(item) for item in (preset_label, self.preset_combo)]
        preset_row.addStretch()

        self._apply_preset_col_widget = QWidget()
        _apply_preset_split = QHBoxLayout(self._apply_preset_col_widget)
        _apply_preset_split.setSpacing(0)
        _apply_preset_split.setContentsMargins(0, 0, 0, 0)

        self.apply_preset_btn = QPushButton("Apply Preset")
        self.apply_preset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.apply_preset_btn.setMinimumWidth(160)
        self.apply_preset_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.apply_preset_btn.setStyleSheet(
            "QPushButton { border-top-right-radius: 0; border-bottom-right-radius: 0; }"
            "QPushButton:hover { border-top-right-radius: 0; border-bottom-right-radius: 0; }"
        )

        self._apply_preset_dropdown_btn = QPushButton("▼")
        self._apply_preset_dropdown_btn.setFixedWidth(22)
        self._apply_preset_dropdown_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_preset_dropdown_btn.setStyleSheet(
            "QPushButton { border-top-left-radius: 0; border-bottom-left-radius: 0; border-left: none; padding: 8px 4px; }"
            "QPushButton:hover { border-top-left-radius: 0; border-bottom-left-radius: 0; }"
        )

        _apply_preset_split.addWidget(self.apply_preset_btn)
        _apply_preset_split.addWidget(self._apply_preset_dropdown_btn)

        self._apply_preset_popup = _PresetPopup(self._apply_preset_dropdown_btn)
        self._apply_preset_popup.setStyleSheet(COMMON_STYLE)
        _popup_layout = QVBoxLayout(self._apply_preset_popup)
        _popup_layout.setContentsMargins(0, 0, 0, 0)
        _popup_layout.setSpacing(0)
        self.force_apply_preset_btn = QPushButton("Force Apply Preset")
        self.force_apply_preset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.force_apply_preset_btn.setStyleSheet("QPushButton { font-size: 11px; padding: 8px 6px; }")
        _popup_layout.addWidget(self.force_apply_preset_btn)

        self.apply_preset_btn.clicked.connect(self._on_apply_preset)
        self._apply_preset_dropdown_btn.clicked.connect(self._toggle_force_apply_preset)
        self.force_apply_preset_btn.clicked.connect(self._on_force_apply_preset)

        self._preset_feedback_label = QLabel()
        self._preset_feedback_label.hide()
        self._preset_feedback_timer = QTimer(self)
        self._preset_feedback_timer.setSingleShot(True)
        self._preset_feedback_timer.setInterval(5000)
        self._preset_feedback_timer.timeout.connect(self._preset_feedback_label.hide)

        apply_preset_row = QHBoxLayout()
        apply_preset_row.setSpacing(8)
        apply_preset_row.addWidget(self._apply_preset_col_widget)
        apply_preset_row.addWidget(self._preset_feedback_label)
        apply_preset_row.addStretch()

        preset_col.addLayout(preset_row)
        preset_col.addLayout(apply_preset_row)

        layout.addLayout(preset_col)
        layout.addStretch()

        # ── Right: icons + manage combo ───────────────────────
        icons_row = QHBoxLayout()
        icons_row.setSpacing(8)
        icons_row.setAlignment(Qt.AlignRight | Qt.AlignBottom)

        discord_btn = QPushButton()
        discord_btn.setIcon(QIcon("assets/discord.png"))
        discord_btn.setIconSize(QSize(50, 50))
        discord_btn.setFixedSize(50, 50)
        discord_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        discord_btn.setStyleSheet(
            "QPushButton { border: none; background: transparent; padding: 0px; }"
        )

        tools_btn = QPushButton("🔧")
        tools_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        tools_btn.setObjectName("icon_btn")
        tools_btn.setFixedSize(32, 32)
        tools_btn.setToolTip("Debug Mode")
        tools_btn.clicked.connect(self.on_tools_clicked)

        self.manage_combo = QComboBox()
        self.manage_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.manage_combo.addItems(["Presets", "Mods", "Skins"])
        self.manage_combo.setPlaceholderText("Manage ▲")
        self.manage_combo.setCurrentIndex(-1)
        self.manage_combo.setMinimumWidth(120)
        self.manage_combo.currentIndexChanged.connect(self.manage_combo_dispatch)

        for item in (discord_btn, tools_btn, self.manage_combo):
            item.setCursor(Qt.CursorShape.PointingHandCursor)
            icons_row.addWidget(item)

        layout.addLayout(icons_row)

    def _set_preset_feedback(self, text: str, *, success: bool = False, error: bool = False):
        color = SUCCESS if success else ("#CC2200" if error else ORANGE)
        self._preset_feedback_label.setText(text)
        self._preset_feedback_label.setStyleSheet(f"color: {color}; font-weight: bold;")
        self._preset_feedback_label.show()
        self._preset_feedback_timer.start()

    def _on_apply_preset(self):
        self._apply_preset(force=False)

    def _on_force_apply_preset(self):
        self._apply_preset_popup.hide()
        self._apply_preset(force=True)

    def _toggle_force_apply_preset(self):
        if self._apply_preset_popup.closed_by_dropdown:
            self._apply_preset_popup.closed_by_dropdown = False
            return
        col_global = self._apply_preset_col_widget.mapToGlobal(
            self._apply_preset_col_widget.rect().bottomLeft()
        )
        self._apply_preset_popup.adjustSize()
        self._apply_preset_popup.setFixedWidth(self._apply_preset_col_widget.width())
        self._apply_preset_popup.move(col_global.x(), col_global.y() + 4)
        self._apply_preset_popup.show()

    def _apply_preset(self, *, force: bool = False):
        from modding.preset_manager import apply_preset
        preset_name = self.preset_combo.currentText().strip()
        if not preset_name:
            return
        self._set_preset_feedback("Searching for skin pathes..")
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()
        try:
            apply_preset(preset_name, force=force)
            message = "Force preset applied successfully" if force else "Preset applied successfully"
            self._set_preset_feedback(message, success=True)
        except Exception:
            self._set_preset_feedback("An error occured upon modding", error=True)
            raise

    def reset_manage_combo(self):
        self.manage_combo.setCurrentIndex(-1)
        self.manage_combo.setPlaceholderText("Manage ▲")

    def manage_combo_dispatch(self):
        def manage_presets():
            from ui import manage_presets_page
            manage_presets_page.ManagePresetsPage(self).show()

        from typing import Literal
        def manage_mod_skin(editor_mode_set=Literal["skin", "mod"]):
            from ui.manage_mod_skin_page import ManageModSkinPage
            from ui.main_page import MainPage
            manage_mod_skin_page = ManageModSkinPage(editor_mode=editor_mode_set, parent=MainPage.main_page)
            manage_mod_skin_page.show()

        def empty_selection():
            pass

        dispatcher = {
            -1: empty_selection,
            0: manage_presets,
            1: lambda: manage_mod_skin("mod"),
            2: lambda: manage_mod_skin("skin")
        }

        dispatcher[self.manage_combo.currentIndex()]()
        self.reset_manage_combo()

    def on_tools_clicked(self):        
        from ui import debug_mode_page

        debug_mode_page.DebugModePage(self).show()
