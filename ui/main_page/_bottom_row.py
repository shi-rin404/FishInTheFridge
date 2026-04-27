from PySide6.QtWidgets import (
    QWidget, QPushButton, QComboBox, QLabel, QCompleter,
    QHBoxLayout, QVBoxLayout, QSizePolicy
)
from PySide6.QtCore import Qt, QSize, QTimer

from .._style import SUCCESS, ORANGE
from PySide6.QtGui import QIcon, QPixmap

from core.variable_manager import program_variables
from modding.ui.load_json_lists import load_json_list
from modding.path_dictionary import preset_dict


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

        self.apply_preset_btn = QPushButton("Apply Preset")
        self.apply_preset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.apply_preset_btn.setMinimumWidth(160)
        self.apply_preset_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.apply_preset_btn.clicked.connect(self._on_apply_preset)

        self._preset_feedback_label = QLabel()
        self._preset_feedback_label.hide()
        self._preset_feedback_timer = QTimer(self)
        self._preset_feedback_timer.setSingleShot(True)
        self._preset_feedback_timer.setInterval(5000)
        self._preset_feedback_timer.timeout.connect(self._preset_feedback_label.hide)

        apply_preset_row = QHBoxLayout()
        apply_preset_row.setSpacing(8)
        apply_preset_row.addWidget(self.apply_preset_btn)
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
        from modding.preset_manager import apply_preset
        preset_name = self.preset_combo.currentText().strip()
        if not preset_name:
            return
        self._set_preset_feedback("Searching for skin pathes..")
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()
        try:
            apply_preset(preset_name)
            self._set_preset_feedback("Preset applied successfully", success=True)
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