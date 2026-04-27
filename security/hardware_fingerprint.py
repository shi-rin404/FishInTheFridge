import hashlib
import subprocess
import uuid


def get_hw_id() -> str:
    """Returns a stable SHA-256 hardware fingerprint for this machine."""
    board_uuid = ""
    cpu_id = ""

    try:
        out = subprocess.check_output(
            "wmic csproduct get uuid", shell=True, stderr=subprocess.DEVNULL
        ).decode()
        parts = out.strip().split()
        if len(parts) >= 2:
            board_uuid = parts[-1]
    except Exception:
        board_uuid = str(uuid.getnode())

    try:
        out = subprocess.check_output(
            "wmic cpu get processorid", shell=True, stderr=subprocess.DEVNULL
        ).decode()
        parts = out.strip().split()
        if len(parts) >= 2:
            cpu_id = parts[-1]
    except Exception:
        cpu_id = ""

    return hashlib.sha256(f"{board_uuid}{cpu_id}".encode()).hexdigest()
