from PySide6.QtCore import QThread, Signal


class AuthWorker(QThread):
    """
    Runs the full Discord OAuth → server auth → download → decrypt pipeline
    off the UI thread so the DispatchPage stays responsive.

    Signals
    -------
    status_update(str)   – human-readable progress message
    success(str, int)    – (mode, security_version) on completion
    failure(str)         – error message
    """

    status_update = Signal(str)
    success       = Signal(str, int)
    failure       = Signal(str)

    def __init__(self, hw_id: str, parent=None):
        super().__init__(parent)
        self._hw_id = hw_id

    def run(self):
        try:
            hw_id = self._hw_id

            # 1 — Discord OAuth (opens browser, blocks until callback)
            self.status_update.emit("Waiting for Discord authorization...")
            from security.discord_oauth import get_discord_token
            discord_token = get_discord_token()

            # 2 — Authenticate with auth server
            self.status_update.emit("Verifying access...")
            from security.session import authenticate
            auth_data      = authenticate(discord_token, hw_id)
            session_token  = auth_data["session_token"]
            delivery_key   = auth_data["delivery_key"]   # ephemeral hex string
            mode           = auth_data["mode"]
            security_version = auth_data.get("security_version", 0)

            # 3 — Download + decrypt tool ZIP into RAM
            self.status_update.emit("Downloading...")
            from security.session import download_and_decrypt
            zip_bytes = download_and_decrypt(session_token, hw_id, delivery_key)
            # delivery_key is no longer referenced after this point

            # 4 — Install in-memory importer
            self.status_update.emit("Loading...")
            from security.memory_loader import MemoryImporter
            MemoryImporter(zip_bytes).install()

            # 5 — Persist session (delivery_key intentionally excluded)
            from security.session import save_session
            save_session(session_token, mode, security_version)

            # 6 — Start tamper watchdog
            from security.tamper_guard import start_watchdog
            start_watchdog(session_token, hw_id)

            self.success.emit(mode, security_version)

        except Exception as exc:
            self.failure.emit(str(exc))


class SessionCheckWorker(QThread):
    """
    Validates a cached session token against the server on app startup.

    Signals
    -------
    valid(str, int)   – (mode, security_version) if session is still good
    invalid()         – session missing, expired, or hw mismatch
    update_needed()   – session valid but security_version is higher
    """

    valid         = Signal(str, int)
    invalid       = Signal()
    update_needed = Signal(str, int)   # (session_token, new_security_version)

    def __init__(self, session: dict, hw_id: str, parent=None):
        super().__init__(parent)
        self._session = session
        self._hw_id   = hw_id

    def run(self):
        token = self._session.get("session_token", "")
        stored_sv = self._session.get("security_version", 0)

        from security.session import validate_session
        ok, mode, sv = validate_session(token, self._hw_id)

        if not ok:
            self.invalid.emit()
        elif sv > stored_sv:
            self.update_needed.emit(token, sv)
        else:
            self.valid.emit(mode, sv)
