import ctypes
import hashlib
import threading
import time

# ── Expected hashes ───────────────────────────────────────────────────────────
# SHA-256 of the security/*.py files as they existed when the dispatch layer
# was built.  Fill these in at build time by running:
#
#   python -c "
#   import hashlib
#   for f in ['security/discord_oauth.py','security/session.py',
#             'security/memory_loader.py','security/tamper_guard.py']:
#       print(f, hashlib.sha256(open(f,'rb').read()).hexdigest())
#   "
#
# Leave a value as "" to skip checking that file (useful during development).
EXPECTED_HASHES: dict[str, str] = {
    "security/discord_oauth.py": "",
    "security/session.py":       "",
    "security/memory_loader.py": "",
    "security/tamper_guard.py":  "",
}

_POLL_INTERVAL = 30  # seconds


# ── Detection helpers ─────────────────────────────────────────────────────────

def _is_debugger_present() -> bool:
    try:
        return bool(ctypes.windll.kernel32.IsDebuggerPresent())
    except Exception:
        return False


def _check_file_hashes() -> list[str]:
    """Returns paths of files whose hash no longer matches the expected value."""
    tampered = []
    for path, expected in EXPECTED_HASHES.items():
        if not expected:
            continue  # not set yet — skip
        try:
            actual = hashlib.sha256(open(path, "rb").read()).hexdigest()
            if actual != expected:
                tampered.append(path)
        except FileNotFoundError:
            tampered.append(path)
    return tampered


# ── Silent reporting ──────────────────────────────────────────────────────────

def _report_tamper(session_token: str, hw_id: str, evidence: dict) -> None:
    """Fire-and-forget POST to server.  Never raises.  Never shows UI."""
    try:
        import requests
        from security.session import AUTH_SERVER
        requests.post(f"{AUTH_SERVER}/tamper-report", json={
            "session_token": session_token,
            "hw_id":         hw_id,
            "evidence":      evidence,
        }, timeout=5)
    except Exception:
        pass


# ── Watchdog ──────────────────────────────────────────────────────────────────

def start_watchdog(session_token: str, hw_id: str) -> None:
    """
    Starts a daemon thread that silently polls for tamper signals every 30 s.
    The attacker sees completely normal operation — we never alert or terminate.
    """
    def _loop():
        while True:
            evidence: dict = {}

            if _is_debugger_present():
                evidence["debugger"] = True

            modified = _check_file_hashes()
            if modified:
                evidence["modified_files"] = modified

            if evidence:
                _report_tamper(session_token, hw_id, evidence)

            time.sleep(_POLL_INTERVAL)

    threading.Thread(target=_loop, daemon=True, name="tamper-watchdog").start()
