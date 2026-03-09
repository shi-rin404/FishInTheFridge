from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel,
    QHBoxLayout, QVBoxLayout
)
from PySide6.QtCore import Qt, QPoint

from .._style import COMMON_STYLE, MUTED
from .._widgets import WindowControls


class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window)
        self.setStyleSheet(COMMON_STYLE)
        self.resize(250, 250)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self._drag_pos = QPoint()
        self._build_ui()

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

        # ── Top row ───────────────────────────────────────────
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 5, 8, 0)
        top_row.setSpacing(12)
        top_row.addStretch()

        self.window_controls = WindowControls()
        self.window_controls.minimize_requested.connect(self.showMinimized)
        self.window_controls.close_requested.connect(self.close)
        top_row.addWidget(self.window_controls)
        root.addLayout(top_row)

        # ── Content ───────────────────────────────────────────
        content = QVBoxLayout()
        content.setContentsMargins(60, 16, 60, 50)
        content.setSpacing(24)

        # ── Title ─────────────────────────────────────────────
        title = QLabel("Settings")
        title.setObjectName("title")
        content.addWidget(title)

        # ── Folder buttons ────────────────────────────────────
        folder_row = QHBoxLayout()
        folder_row.setSpacing(12)
          
        self.auto_detect_btn = QPushButton("Auto-Detect Game Folder")
        self.auto_detect_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.auto_detect_btn.clicked.connect(self.on_auto_detect_game_folder)

        
        self.choose_folder_btn = QPushButton("Choose Game Folder")
        self.choose_folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.choose_folder_btn.clicked.connect(self.manual_set_game_exec)        

        folder_row.addWidget(self.auto_detect_btn)
        folder_row.addWidget(self.choose_folder_btn)
        folder_row.addStretch()

        content.addLayout(folder_row)

        # ── Update row ────────────────────────────────────────
        update_row = QHBoxLayout()
        update_row.setSpacing(16)

        self.check_updates_btn = QPushButton("↻   Check for Updates")
        self.check_updates_btn.setEnabled(False)
        self.check_updates_btn.setStyleSheet(f"color: {MUTED}; font-size: 13px;")

        from database.system.system_variables import system_variables
        self.version_label = QLabel(system_variables.version)
        self.version_label.setStyleSheet(f"color: {MUTED}; font-size: 13px;")

        update_row.addWidget(self.check_updates_btn)
        update_row.addWidget(self.version_label)
        update_row.addStretch()

        content.addLayout(update_row)
        content.addStretch()

        root.addLayout(content)

    def manual_set_game_exec(self) -> None:
        from file_io.input.select_game_exec import select_game_exec

        exec_path = select_game_exec()

        if exec_path is None: return

        from file_io.output.edit_json import edit_json
        from core.variable_manager import program_variables
        from error_handler.ensure_exception import ensure_exception

        ensure_exception(edit_json, (program_variables.__memory_json__, "game_executable", exec_path))

    def on_auto_detect_game_folder(self) -> None:
        from core.automatic_processes.find_game_executable import find_game_executable   
        from PySide6.QtWidgets import QMessageBox
        
        result = find_game_executable()

        if result is not None:
            QMessageBox.information(self, "Successful", f"The game has found in {result}")
            return
        
        QMessageBox.critical(self, "Unsuccessful", "The game has not been found in its default directory. You might moved or renamed it. Try to manual choose.")