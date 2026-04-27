from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

from ui._style import window_style
from ui._widgets import StylePaintMixin, WindowControls


class DispatchPage(StylePaintMixin, QWidget):
    """
    The first window the user sees.  Handles Discord OAuth and mode selection.
    After a successful auth it creates the appropriate main window and closes
    itself.
    """

    dispatch_page: "DispatchPage | None" = None

    def __init__(self, debug: bool = False, parent=None):
        DispatchPage.dispatch_page = self
        super().__init__(parent, Qt.WindowType.Window)
        self.setObjectName("dispatch_page")
        self.setStyleSheet(window_style("dispatch_page"))
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.resize(340, 400)

        self._drag_pos = QPoint()
        self._worker   = None
        self._debug    = debug

        self._build_ui()

        from PySide6.QtCore import QTimer
        if debug:
            QTimer.singleShot(0, self._debug_bypass)
        else:
            QTimer.singleShot(0, self._check_existing_session)

    # ── Drag ─────────────────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and not self._drag_pos.isNull():
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Window controls row
        wc_row = QHBoxLayout()
        wc_row.setContentsMargins(0, 8, 8, 0)
        wc_row.addStretch()
        self._wc = WindowControls()
        self._wc.minimize_requested.connect(self.showMinimized)
        self._wc.close_requested.connect(self.close)
        wc_row.addWidget(self._wc)
        root.addLayout(wc_row)

        # Content
        content = QVBoxLayout()
        content.setContentsMargins(50, 16, 50, 40)
        content.setSpacing(18)
        content.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Discord logo
        logo = QLabel()
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        px = QPixmap("assets/discord.png")
        if not px.isNull():
            logo.setPixmap(px.scaledToWidth(72, Qt.TransformationMode.SmoothTransformation))
        content.addWidget(logo)

        # Status label
        self._status = QLabel("Checking session...")
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status.setWordWrap(True)
        content.addWidget(self._status)

        # Login button
        self._login_btn = QPushButton("Login with Discord")
        self._login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._login_btn.clicked.connect(self._on_login)
        self._login_btn.hide()
        content.addWidget(self._login_btn)

        # Mode buttons
        mode_row = QHBoxLayout()
        mode_row.setSpacing(10)

        self._client_btn = QPushButton("Client Mode")
        self._client_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._client_btn.clicked.connect(lambda: self._launch("client"))
        self._client_btn.hide()
        mode_row.addWidget(self._client_btn)

        self._dev_btn = QPushButton("Developer Mode")
        self._dev_btn.setObjectName("success")
        self._dev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._dev_btn.clicked.connect(lambda: self._launch("developer"))
        self._dev_btn.hide()
        mode_row.addWidget(self._dev_btn)

        content.addLayout(mode_row)

        # Retry button
        self._retry_btn = QPushButton("Try Again")
        self._retry_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._retry_btn.clicked.connect(self._show_login)
        self._retry_btn.hide()
        content.addWidget(self._retry_btn)

        root.addLayout(content)
        root.addStretch()

    # ── State helpers ─────────────────────────────────────────────────────────

    def _hide_actions(self):
        for w in (self._login_btn, self._client_btn, self._dev_btn, self._retry_btn):
            w.hide()

    def _show_login(self):
        self._hide_actions()
        self._status.setText("Login with Discord to continue.")
        self._login_btn.show()

    def _show_error(self, message: str):
        self._hide_actions()
        self._status.setText(f"Error: {message}")
        self._retry_btn.show()

    def _show_ready(self, mode: str):
        self._hide_actions()
        self._status.setText("Authorization successful.")
        if mode in ("client", "developer"):
            self._client_btn.show()
        if mode == "developer":
            self._dev_btn.show()

    # ── Debug bypass ──────────────────────────────────────────────────────────

    def _debug_bypass(self):
        self._hw_id = "debug"
        self._status.setText("[DEBUG] Auth bypassed.")
        self._show_ready("developer")

    # ── Startup session check ─────────────────────────────────────────────────

    def _check_existing_session(self):
        from security.hardware_fingerprint import get_hw_id
        from security.session import load_session

        self._hw_id = get_hw_id()
        session = load_session()

        if session:
            from ui.dispatch_page._auth_worker import SessionCheckWorker
            self._worker = SessionCheckWorker(session, self._hw_id, parent=self)
            self._worker.valid.connect(self._on_session_valid)
            self._worker.invalid.connect(self._show_login)
            self._worker.update_needed.connect(self._on_update_needed)
            self._worker.start()
        else:
            self._show_login()

    def _on_session_valid(self, mode: str, sv: int):
        from security.session import save_session, load_session
        session = load_session()
        if session:
            save_session(session["session_token"], mode, sv)
        from security.tamper_guard import start_watchdog
        start_watchdog(session["session_token"] if session else "", self._hw_id)
        self._show_ready(mode)

    def _on_update_needed(self, session_token: str, new_sv: int):
        """Security update detected — force re-auth to get a fresh build."""
        self._status.setText("Security update available. Please re-login.")
        self._show_login()

    # ── Login flow ────────────────────────────────────────────────────────────

    def _on_login(self):
        self._hide_actions()
        self._status.setText("Waiting for Discord authorization...")
        from ui.dispatch_page._auth_worker import AuthWorker
        self._worker = AuthWorker(self._hw_id, parent=self)
        self._worker.status_update.connect(self._status.setText)
        self._worker.success.connect(self._on_auth_success)
        self._worker.failure.connect(self._show_error)
        self._worker.start()

    def _on_auth_success(self, mode: str, _sv: int):
        self._show_ready(mode)

    # ── Mode launch ───────────────────────────────────────────────────────────

    def _launch(self, mode: str):
        from database.system.system_variables import system_variables
        system_variables.mode = mode

        from modding.get_mods import get_mods
        get_mods()

        from ui.main_page import MainPage
        self._main_window = MainPage()
        self._main_window.show()
        self.close()
