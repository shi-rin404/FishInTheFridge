from PySide6.QtWidgets import (
    QWidget, QPushButton, QComboBox, QLabel,
    QHBoxLayout, QVBoxLayout, QSizePolicy
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap



class BottomRow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Left: preset controls ─────────────────────────────
        preset_col = QVBoxLayout()
        preset_col.setSpacing(8)

        preset_row = QHBoxLayout()
        preset_row.setSpacing(8)
        preset_label = QLabel("Active Mod Preset")
        self.preset_combo = QComboBox()
        self.preset_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.preset_combo.setMinimumWidth(160)
        self.preset_combo.setPlaceholderText("No Presets")
        self.preset_combo.setCurrentIndex(-1) # TODO: Set it -1 when the user has no active preset saved
        [preset_row.addWidget(item) for item in (preset_label, self.preset_combo)]
        preset_row.addStretch()

        self.apply_preset_btn = QPushButton("Apply Preset")
        self.apply_preset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.apply_preset_btn.setMinimumWidth(160)
        self.apply_preset_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        preset_col.addLayout(preset_row)
        preset_col.addWidget(self.apply_preset_btn)

        layout.addLayout(preset_col)
        layout.addStretch()

        # ── Right: icons + manage combo ───────────────────────
        icons_row = QHBoxLayout()
        icons_row.setSpacing(8)
        icons_row.setAlignment(Qt.AlignRight | Qt.AlignBottom)

        discord_btn = QPushButton()
        discord_btn.setIcon(QIcon("assets/discord.png"))
        discord_btn.setIconSize(QSize(50,50))
        discord_btn.setFixedSize(50,50)
        discord_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        discord_btn.setStyleSheet(
            "QPushButton { border: none; background: transparent; padding: 0px; }"
        )

        tools_btn = QPushButton("🔧")
        tools_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        tools_btn.setObjectName("icon_btn")
        tools_btn.setFixedSize(32, 32)
        tools_btn.setToolTip("Get Mods (test)")        

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

    def reset_manage_combo(self):
        self.manage_combo.setCurrentIndex(-1)
        self.manage_combo.setPlaceholderText("Manage ▲")

    def manage_combo_dispatch(self):
        def manage_presets():
            ... 
        
        from typing import Literal
        def manage_mod_skin(editor_mode_set=Literal["skin", "mod"]):
            from ui.manage_mod_skin_page import ManageModSkinPage
            from ui.main_page import MainPage
            manage_mod_skin_page = ManageModSkinPage(editor_mode=editor_mode_set, parent = MainPage.main_page)
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