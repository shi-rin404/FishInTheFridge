"""
FishInTheFridge Auth Server
Run with:  uvicorn main:app --host 0.0.0.0 --port 8000
"""

import base64
import hashlib
import hmac
import json
import secrets
import time
from pathlib import Path
from typing import Optional

import requests as http_requests
from cryptography.fernet import Fernet
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from config import ADMIN_KEY, DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET, MASTER_SECRET

app = FastAPI()

# ── Storage paths ─────────────────────────────────────────────────────────────
# sessions.json and state.json are gitignored — never commit them.
_WHITELIST = Path("whitelist.json")
_SESSIONS  = Path("sessions.json")
_STATE     = Path("state.json")
_BINARIES  = Path("binaries")   # binaries/client_mode.bin, binaries/dev_mode.bin

SESSION_TTL = 30 * 24 * 3600  # 30 days in seconds


# ── JSON helpers ──────────────────────────────────────────────────────────────

def _read(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading {path}: {e}")
        return {}


def _write(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2))


# ── Security version ──────────────────────────────────────────────────────────

def _get_sv() -> int:
    return _read(_STATE).get("security_version", 1)


def _increment_sv() -> int:
    state = _read(_STATE)
    state["security_version"] = state.get("security_version", 1) + 1
    _write(_STATE, state)
    return state["security_version"]


# ── Key derivation ────────────────────────────────────────────────────────────

def _derive_delivery_key(hw_id: str, session_token: str) -> bytes:
    """32-byte key unique to this (hw_id, session_token) pair."""
    msg = (hw_id + session_token).encode()
    return hmac.new(MASTER_SECRET, msg, hashlib.sha256).digest()


# ── Discord identity ──────────────────────────────────────────────────────────

def _discord_user_id(discord_token: str) -> str:
    resp = http_requests.get(
        "https://discord.com/api/users/@me",
        headers={"Authorization": f"Bearer {discord_token}"},
        timeout=10,
    )
    if not resp.ok:
        raise HTTPException(status_code=401, detail="Invalid Discord token")
    return resp.json()["id"]


# ── Models ────────────────────────────────────────────────────────────────────

class AuthRequest(BaseModel):
    discord_token: str
    hw_id: str

class ValidateRequest(BaseModel):
    session_token: str
    hw_id: str

class DownloadRequest(BaseModel):
    hw_id: str

class RevokeRequest(BaseModel):
    admin_key: str
    discord_id: str

class TamperReport(BaseModel):
    session_token: str
    hw_id: str
    evidence: dict


# ── Session helper ────────────────────────────────────────────────────────────

def _get_session(token: str) -> dict:
    """Returns the session dict or raises 401."""
    session = _read(_SESSIONS).get(token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    if time.time() > session["expires"]:
        raise HTTPException(status_code=401, detail="Session expired")
    return session


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.post("/auth")
def auth(req: AuthRequest):
    """Verify Discord identity, check whitelist, issue session + delivery key."""
    discord_id = _discord_user_id(req.discord_token)

    whitelist = _read(_WHITELIST)
    if discord_id not in whitelist:
        raise HTTPException(status_code=403, detail="Not authorized")

    mode          = whitelist[discord_id]
    session_token = secrets.token_urlsafe(32)
    delivery_key  = _derive_delivery_key(req.hw_id, session_token)
    sv            = _get_sv()

    sessions = _read(_SESSIONS)
    sessions[session_token] = {
        "discord_id": discord_id,
        "hw_id":      req.hw_id,
        "mode":       mode,
        "expires":    time.time() + SESSION_TTL,
        "sv":         sv,
    }
    _write(_SESSIONS, sessions)

    return {
        "session_token":    session_token,
        "delivery_key":     delivery_key.hex(),
        "mode":             mode,
        "security_version": sv,
    }


@app.post("/validate")
def validate(req: ValidateRequest):
    """Check whether a cached session is still valid."""
    session = _get_session(req.session_token)          # raises if invalid/expired

    if session["hw_id"] != req.hw_id:
        raise HTTPException(status_code=403, detail="Hardware mismatch")

    return {
        "valid":            True,
        "mode":             session["mode"],
        "security_version": _get_sv(),
    }


@app.post("/download")
def download(req: DownloadRequest, authorization: Optional[str] = Header(None)):
    """
    Encrypt the mode-specific binary on the fly with a per-delivery key and
    stream the ciphertext to the client.  The plaintext binary never leaves
    the server unencrypted.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    session_token = authorization[len("Bearer "):]
    session       = _get_session(session_token)

    if session["hw_id"] != req.hw_id:
        raise HTTPException(status_code=403, detail="Hardware mismatch")

    mode     = session["mode"]
    bin_path = _BINARIES / f"{mode}_mode.bin"
    if not bin_path.exists():
        raise HTTPException(status_code=404, detail=f"Binary not found for mode: {mode}")

    plaintext    = bin_path.read_bytes()
    delivery_key = _derive_delivery_key(req.hw_id, session_token)
    fernet_key   = base64.urlsafe_b64encode(delivery_key)
    ciphertext   = Fernet(fernet_key).encrypt(plaintext)

    return Response(content=ciphertext, media_type="application/octet-stream")


@app.post("/revoke")
def revoke(req: RevokeRequest):
    """Admin endpoint: remove a user from the whitelist and kill their sessions."""
    if req.admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Bad admin key")

    whitelist = _read(_WHITELIST)
    whitelist.pop(req.discord_id, None)
    _write(_WHITELIST, whitelist)

    sessions = _read(_SESSIONS)
    to_delete = [t for t, s in sessions.items() if s["discord_id"] == req.discord_id]
    for t in to_delete:
        del sessions[t]
    _write(_SESSIONS, sessions)

    return {"revoked": len(to_delete)}


@app.post("/tamper-report")
def tamper_report(report: TamperReport):
    """
    Receive a silent tamper signal from a client.
    Logs the incident and bumps security_version so all users re-download on
    their next launch.
    """
    session = _read(_SESSIONS).get(report.session_token, {})
    discord_id = session.get("discord_id", "unknown")

    new_sv = _increment_sv()

    # Append to tamper log
    log_path = Path("tamper_log.jsonl")
    with log_path.open("a") as f:
        f.write(json.dumps({
            "timestamp":  time.time(),
            "discord_id": discord_id,
            "hw_id":      report.hw_id,
            "evidence":   report.evidence,
        }) + "\n")

    return {"received": True, "new_security_version": new_sv}


@app.post("/security-update")
def security_update(admin_key: str):
    """Admin: manually trigger a security update (force all users to re-download)."""
    if admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Bad admin key")
    new_sv = _increment_sv()
    return {"new_security_version": new_sv}
