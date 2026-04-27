import base64
import json

import requests
from cryptography.fernet import Fernet, InvalidToken

from core.variable_manager import program_variables

AUTH_SERVER = "https://your-auth-server.com"  # replace with your server URL


# ── Local session file ────────────────────────────────────────────────────────

def _fernet() -> Fernet:
    """Fernet key derived from the machine's hardware fingerprint."""
    from security.hardware_fingerprint import get_hw_id
    return Fernet(base64.urlsafe_b64encode(bytes.fromhex(get_hw_id())))


def load_session() -> dict | None:
    """Returns {session_token, mode, security_version} or None."""
    try:
        ciphertext = program_variables.auth_file.read_bytes()
        plaintext  = _fernet().decrypt(ciphertext)
        return json.loads(plaintext)
    except (FileNotFoundError, InvalidToken, json.JSONDecodeError):
        return None


def save_session(session_token: str, mode: str, security_version: int = 0) -> None:
    plaintext  = json.dumps({
        "session_token":    session_token,
        "mode":             mode,
        "security_version": security_version,
    }).encode()
    ciphertext = _fernet().encrypt(plaintext)
    program_variables.auth_file.write_bytes(ciphertext)


# ── Server calls ──────────────────────────────────────────────────────────────

def validate_session(session_token: str, hw_id: str) -> tuple[bool, str, int]:
    """
    Returns (valid, mode, security_version).
    Returns (False, "", 0) on network error so the caller falls back to login.
    """
    try:
        resp = requests.post(f"{AUTH_SERVER}/validate", json={
            "session_token": session_token,
            "hw_id":         hw_id,
        }, timeout=10)
        if resp.ok:
            data = resp.json()
            return data.get("valid", False), data.get("mode", ""), data.get("security_version", 0)
    except Exception:
        pass
    return False, "", 0


def authenticate(discord_token: str, hw_id: str) -> dict:
    """
    POST /auth to the auth server.
    Returns {session_token, delivery_key (hex), mode, security_version}.
    Raises RuntimeError on failure.
    """
    resp = requests.post(f"{AUTH_SERVER}/auth", json={
        "discord_token": discord_token,
        "hw_id":         hw_id,
    }, timeout=15)
    if not resp.ok:
        raise RuntimeError(resp.json().get("detail", "Authentication failed"))
    return resp.json()


def download_and_decrypt(session_token: str, hw_id: str, delivery_key_hex: str) -> bytes:
    """
    Download the encrypted tool ZIP from the server and decrypt it entirely
    in memory.  The delivery_key is ephemeral — it is never stored on disk.
    Returns the raw decrypted ZIP bytes.
    """
    resp = requests.post(f"{AUTH_SERVER}/download",
                         headers={"Authorization": f"Bearer {session_token}"},
                         json={"hw_id": hw_id},
                         timeout=120)
    if not resp.ok:
        raise RuntimeError(f"Download failed ({resp.status_code})")

    delivery_key = bytes.fromhex(delivery_key_hex)
    fernet_key   = base64.urlsafe_b64encode(delivery_key)
    return Fernet(fernet_key).decrypt(resp.content)
