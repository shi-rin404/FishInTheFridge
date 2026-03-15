from PySide6.QtWidgets import (
    QWidget, QFrame, QPushButton, QLabel, QComboBox,
    QHBoxLayout, QVBoxLayout
)
from PySide6.QtCore import Qt, QPoint

from core.variable_manager import program_variables
from database.user.user_variables import user_variables
from pathlib import Path
from typing import Literal
import os, shutil, subprocess, threading

from .._style import window_style, MUTED
from .._widgets import WindowControls, StylePaintMixin


class HighBanRiskPage(StylePaintMixin, QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("high_ban_risk_page")
        self.setStyleSheet(window_style("high_ban_risk_page"))
        self.resize(380, 235)
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
        root.setContentsMargins(60, 5, 15, 50)
        root.setSpacing(24)

        # ── Top row ───────────────────────────────────────────
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(12)
        top_row.addStretch()

        self.window_controls = WindowControls()
        self.window_controls.minimize_requested.connect(self.showMinimized)
        self.window_controls.close_requested.connect(self.close)
        top_row.addWidget(self.window_controls)
        root.addLayout(top_row)

        # ── Title ─────────────────────────────────────────────
        title = QLabel("High Ban Risk")
        title.setObjectName("title")
        title.setStyleSheet(
            "color: #D05050;"
            "text-decoration: underline;"
            "font-family: Georgia, 'Times New Roman', serif;"
            "font-size: 38px;"
            "border: none;"
            "background: transparent;"
        )
        root.addWidget(title)

        # ── Launch row ────────────────────────────────────────
        launch_row = QHBoxLayout()
        launch_row.setSpacing(12)

        self.launch_combo = QComboBox()
        self.launch_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.launch_combo.setStyleSheet(f"QComboBox {{border-color: #D05050; color: {MUTED};}}"
                                        f"QComboBox QAbstractItemView {{ color: black; }}")
        self.launch_combo.setPlaceholderText("Select a Method for 3DM")
        self.launch_combo.setCurrentIndex(-1)
        self.launch_combo.addItems([
            "Install 3D Migoto into Game Folder" if self.internal_3dm_dispatcher("verify") == "install" else "Uninstall 3D Migoto",
            "Inject 3D Migoto Real Time",
        ])
        self.launch_combo.currentIndexChanged.connect(self._on_launch_selected)

        help_btn = QPushButton("?")
        help_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        help_btn.setObjectName("help_btn")
        help_btn.setToolTip(
            "Launching with 3DMigoto injects a DLL into the game process, "
            "which may be detected by anti-cheat software."
        )

        launch_row.addWidget(self.launch_combo)
        launch_row.addWidget(help_btn)
        launch_row.addStretch()

        root.addLayout(launch_row)
        root.addStretch()

    def _on_launch_selected(self, index: int):
        [lambda: self.internal_3dm_dispatcher("action"), self._inject_3dm][index]() if index != -1 else None
        self.launch_combo.setCurrentIndex(-1)
        self.launch_combo.setItemText(0, "Install 3D Migoto into Game Folder" if self.internal_3dm_dispatcher("verify") == "install" else "Uninstall 3D Migoto")

    
    def install_3dm(self):      
        # Case Handlers
        def on_file_not_found(file_name: str):
            shutil.copy(
                Path(program_variables._3dm_folder_path) / file_name,
                Path(user_variables.game_dir) / file_name
            )

        def on_folder_not_found(folder_name: str):
            shutil.copytree(
                Path(program_variables._3dm_folder_path) / folder_name,
                Path(user_variables.game_dir) / folder_name
            )

        # File Verification
        for file_name in user_variables._3dm:
            if not os.path.exists(Path(user_variables.game_dir) / file_name):
                if "." in file_name:
                    on_file_not_found(file_name)
                else:
                    on_folder_not_found(file_name)


    def uninstall_3dm(self):        
        # File Verification
        for file_name in user_variables._3dm:
            if os.path.exists(Path(user_variables.game_dir) / file_name):
                dst = Path(program_variables._3dm_folder_path) / file_name
                if dst.is_dir():
                    shutil.rmtree(dst)
                elif dst.exists():
                    dst.unlink()
                shutil.move(Path(user_variables.game_dir) / file_name, dst)
    
    def internal_3dm_dispatcher(self, mode:Literal["action", "verify"]):
        if mode not in ("action", "verify"):
            raise ValueError("mode must be either 'action' or 'verify'")        
        # ============================ #        
        if any(os.path.exists(Path(user_variables.game_dir) / file_name) for file_name in user_variables._3dm):
            return self.uninstall_3dm() if mode == "action" else "uninstall"
        else:
            return self.install_3dm() if mode == "action" else "install"
    
    def _inject_3dm(self):
        proc = subprocess.Popen(
            Path(program_variables._3dm_folder_path) / "3DMigoto Loader.exe",
            stdout=subprocess.PIPE,
            text=True
        )
        threading.Thread(target=self._watch_loader, args=(proc,), daemon=True).start()

    def _watch_loader(self, proc):
        for line in proc.stdout:
            if "3DMigoto ready - Now run the game." in line:
                os.startfile(user_variables.game_executable)
                break