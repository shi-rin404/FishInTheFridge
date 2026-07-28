from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QCheckBox, QComboBox,
    QHBoxLayout, QVBoxLayout
)
from PySide6.QtCore import Qt, QPoint

from core.options_memory import read_memory, set_memory_value
from core.variable_manager import program_variables
from modding.path_dictionary import preset_dict
from modding.ui.load_json_lists import load_json_list
from .._style import window_style
from .._widgets import WindowControls, StylePaintMixin


class OptionsPage(StylePaintMixin, QWidget):
    options_page = None

    def __init__(self, parent=None):
        OptionsPage.options_page = self
        super().__init__(parent, Qt.Window)
        self.setObjectName("options_page")
        self.setStyleSheet(window_style("options_page"))
        self.resize(460, 230)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self._drag_pos = QPoint()
        self._build_ui()
        self._load_settings()

    def closeEvent(self, event):
        if OptionsPage.options_page is self:
            OptionsPage.options_page = None
        super().closeEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and not self._drag_pos.isNull():
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 5, 8, 0)
        top_row.addStretch()
        self.window_controls = WindowControls()
        self.window_controls.minimize_requested.connect(self.showMinimized)
        self.window_controls.close_requested.connect(self.close)
        top_row.addWidget(self.window_controls)
        root.addLayout(top_row)

        content = QVBoxLayout()
        content.setContentsMargins(40, 16, 40, 40)
        content.setSpacing(20)

        title = QLabel("Options")
        title.setObjectName("title")
        content.addWidget(title)

        self.check_updates_on_start_check = QCheckBox("Check for updates on start")
        self.check_updates_on_start_check.setCursor(Qt.CursorShape.PointingHandCursor)
        self.check_updates_on_start_check.toggled.connect(
            self._on_check_updates_on_start_toggled
        )
        content.addWidget(self.check_updates_on_start_check)

        launch_row = QHBoxLayout()
        launch_row.setSpacing(12)
        self.load_mods_check = QCheckBox("Load mods on launch")
        self.load_mods_check.setCursor(Qt.CursorShape.PointingHandCursor)
        self.load_mods_check.toggled.connect(self._on_load_mods_toggled)

        self.launch_preset_combo = QComboBox()
        self.launch_preset_combo.setMinimumWidth(160)
        self.launch_preset_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        load_json_list(self.launch_preset_combo, program_variables.presets_path, preset_dict)
        self.launch_preset_combo.setCurrentIndex(-1)
        self.launch_preset_combo.currentTextChanged.connect(self._on_preset_changed)

        launch_row.addWidget(self.load_mods_check)
        launch_row.addWidget(self.launch_preset_combo)
        launch_row.addStretch()
        content.addLayout(launch_row)
        content.addStretch()

        root.addLayout(content)

    def _load_settings(self):
        memory = read_memory()
        check_updates = bool(memory.get("check_updates_on_start", True))
        enabled = bool(memory.get("load_mods_on_launch", False))
        preset_name = str(memory.get("load_mods_on_launch_preset", "") or "")

        self.check_updates_on_start_check.blockSignals(True)
        self.check_updates_on_start_check.setChecked(check_updates)
        self.check_updates_on_start_check.blockSignals(False)

        self.load_mods_check.blockSignals(True)
        self.load_mods_check.setChecked(enabled)
        self.load_mods_check.blockSignals(False)

        self.launch_preset_combo.blockSignals(True)
        index = self.launch_preset_combo.findText(preset_name)
        self.launch_preset_combo.setCurrentIndex(index if index != -1 else -1)
        self.launch_preset_combo.setVisible(enabled)
        self.launch_preset_combo.blockSignals(False)

    def _on_load_mods_toggled(self, checked: bool):
        self.launch_preset_combo.setVisible(checked)
        set_memory_value("load_mods_on_launch", checked)
        if not checked:
            set_memory_value("load_mods_on_launch_preset", "")
            self.launch_preset_combo.blockSignals(True)
            self.launch_preset_combo.setCurrentIndex(-1)
            self.launch_preset_combo.blockSignals(False)

    def _on_preset_changed(self, preset_name: str):
        if self.load_mods_check.isChecked():
            set_memory_value("load_mods_on_launch_preset", preset_name.strip())

    def _on_check_updates_on_start_toggled(self, checked: bool):
        set_memory_value("check_updates_on_start", checked)
