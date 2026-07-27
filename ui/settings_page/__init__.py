from PySide6.QtWidgets import (
    QApplication, QLabel, QMessageBox, QPushButton, QWidget,
    QHBoxLayout, QVBoxLayout,
)
from PySide6.QtCore import QObject, QPoint, Qt, QThread, Signal

from .._style import MUTED, window_style
from .._widgets import StylePaintMixin, WindowControls


class UpdateWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, action: str, asset=None):
        super().__init__()
        self.action = action
        self.asset = asset

    def run(self):
        try:
            if self.action == "check":
                from core.auto_updater import check_for_updates
                self.finished.emit(check_for_updates())
            elif self.action == "install":
                from core.auto_updater import install_update
                self.finished.emit(install_update(self.asset))
        except Exception as exc:
            self.failed.emit(str(exc))


class SettingsPage(StylePaintMixin, QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window)
        self.setObjectName("settings_page")
        self.setStyleSheet(window_style("settings_page"))
        self.resize(520, 250)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self._drag_pos = QPoint()
        self._update_thread = None
        self._update_worker = None
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

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 5, 8, 0)
        top_row.setSpacing(12)
        top_row.addStretch()

        self.window_controls = WindowControls()
        self.window_controls.minimize_requested.connect(self.showMinimized)
        self.window_controls.close_requested.connect(self.close)
        top_row.addWidget(self.window_controls)
        root.addLayout(top_row)

        content = QVBoxLayout()
        content.setContentsMargins(60, 16, 60, 50)
        content.setSpacing(24)

        title = QLabel("Settings")
        title.setObjectName("title")
        content.addWidget(title)

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

        update_row = QHBoxLayout()
        update_row.setSpacing(16)

        self.manage_options_btn = QPushButton("Manage Options")
        self.manage_options_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.manage_options_btn.clicked.connect(self._show_options)

        self.check_updates_btn = QPushButton("Check for Updates")
        self.check_updates_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.check_updates_btn.clicked.connect(self.check_for_updates)

        from database.system.system_variables import system_variables
        self.version_label = QLabel(system_variables.version)
        self.version_label.setStyleSheet(f"color: {MUTED}; font-size: 13px;")

        update_row.addWidget(self.manage_options_btn)
        update_row.addWidget(self.check_updates_btn)
        update_row.addWidget(self.version_label)
        update_row.addStretch()

        content.addLayout(update_row)
        content.addStretch()

        root.addLayout(content)

    def _show_options(self):
        from ui.options_page import OptionsPage
        self._options_page = OptionsPage(parent=self)
        self._options_page.show()

    def _start_update_worker(self, action: str, asset=None):
        self.check_updates_btn.setEnabled(False)
        self._update_thread = QThread(self)
        self._update_worker = UpdateWorker(action, asset)
        self._update_worker.moveToThread(self._update_thread)
        self._update_thread.started.connect(self._update_worker.run)
        self._update_worker.finished.connect(self._on_update_worker_finished)
        self._update_worker.failed.connect(self._on_update_worker_failed)
        self._update_worker.finished.connect(self._update_thread.quit)
        self._update_worker.failed.connect(self._update_thread.quit)
        self._update_thread.finished.connect(self._update_worker.deleteLater)
        self._update_thread.finished.connect(self._update_thread.deleteLater)
        self._update_thread.start()

    def check_for_updates(self) -> None:
        self.check_updates_btn.setText("Checking...")
        self._start_update_worker("check")

    def _on_update_worker_finished(self, result):
        self.check_updates_btn.setText("Check for Updates")
        self.check_updates_btn.setEnabled(True)

        if isinstance(result, bool):
            QMessageBox.information(
                self,
                "Update Installing",
                "The update will be installed now. The application will restart automatically.",
            )
            QApplication.quit()
            return

        if not result.update_available:
            QMessageBox.information(
                self,
                "No Updates Found",
                f"You are already on the latest version ({result.current_version}).",
            )
            return

        reply = QMessageBox.question(
            self,
            "Update Available",
            (
                f"Version {result.latest_version} is available.\n"
                f"Current version: {result.current_version}\n\n"
                "Install it now?"
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.check_updates_btn.setText("Installing...")
            self._start_update_worker("install", result.asset)

    def _on_update_worker_failed(self, message: str):
        self.check_updates_btn.setText("Check for Updates")
        self.check_updates_btn.setEnabled(True)
        QMessageBox.critical(self, "Update Failed", message)

    def manual_set_game_exec(self) -> None:
        from file_io.input.select_game_exec import select_game_exec

        exec_path = select_game_exec()

        if exec_path is None:
            return

        from file_io.output.edit_json import edit_json
        from core.variable_manager import program_variables
        edit_json(program_variables.__memory_json__, "game_executable", exec_path)

    def on_auto_detect_game_folder(self) -> None:
        from core.automatic_processes.find_game_executable import find_game_executable

        result = find_game_executable()

        if result is not None:
            QMessageBox.information(self, "Successful", f"The game has found in {result}")
            return

        QMessageBox.critical(
            self,
            "Unsuccessful",
            "The game has not been found in its default directory. You might moved or renamed it. Try to manual choose.",
        )
