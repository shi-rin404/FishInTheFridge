import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path

from core.variable_manager import program_variables
from database.system.system_variables import system_variables


@dataclass(frozen=True)
class ReleaseAsset:
    version: str
    name: str
    download_url: str


@dataclass(frozen=True)
class UpdateCheckResult:
    update_available: bool
    current_version: str
    latest_version: str
    asset: ReleaseAsset | None = None


class UpdateError(RuntimeError):
    pass


def _parse_version(value: str) -> tuple[int, ...]:
    parts = re.findall(r"\d+", value)
    if not parts:
        raise ValueError(f"Invalid version: {value}")
    return tuple(int(part) for part in parts)


def _asset_version(asset_name: str) -> str | None:
    prefix = re.escape(system_variables.release_asset_prefix)
    match = re.fullmatch(rf"{prefix}-(\d+(?:-\d+)*)\.zip", asset_name)
    if not match:
        return None
    return match.group(1).replace("-", ".")


def _request_json(url: str) -> dict | list:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "Miyou-Loader-Updater",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def check_for_updates() -> UpdateCheckResult:
    releases_url = f"https://api.github.com/repos/{system_variables.github_repo}/releases"
    releases = _request_json(releases_url)
    if not isinstance(releases, list):
        raise UpdateError("GitHub returned an unexpected releases response.")

    current = _parse_version(system_variables.version)
    candidates: list[ReleaseAsset] = []

    for release in releases:
        if release.get("draft") or release.get("prerelease"):
            continue
        for asset in release.get("assets", []):
            name = asset.get("name", "")
            version = _asset_version(name)
            download_url = asset.get("browser_download_url")
            if version and download_url:
                candidates.append(ReleaseAsset(version, name, download_url))

    if not candidates:
        return UpdateCheckResult(False, system_variables.version, system_variables.version)

    latest = max(candidates, key=lambda asset: _parse_version(asset.version))
    update_available = _parse_version(latest.version) > current
    return UpdateCheckResult(
        update_available,
        system_variables.version,
        latest.version,
        latest if update_available else None,
    )


def _download_asset(asset: ReleaseAsset, destination: Path) -> None:
    request = urllib.request.Request(
        asset.download_url,
        headers={"User-Agent": "Miyou-Loader-Updater"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        with destination.open("wb") as f:
            shutil.copyfileobj(response, f)


def _archive_root(extract_dir: Path) -> Path:
    children = [child for child in extract_dir.iterdir() if child.name != "__MACOSX"]
    if len(children) == 1 and children[0].is_dir():
        return children[0]
    return extract_dir


def _safe_extract(zip_ref: zipfile.ZipFile, extract_dir: Path) -> None:
    extract_root = extract_dir.resolve()
    for member in zip_ref.infolist():
        target = (extract_dir / member.filename).resolve()
        if target != extract_root and extract_root not in target.parents:
            raise UpdateError(f"Unsafe path in update archive: {member.filename}")
    zip_ref.extractall(extract_dir)


def _restart_command() -> list[str]:
    if getattr(sys, "frozen", False):
        return [sys.executable, *sys.argv[1:]]
    return [sys.executable, str(Path(sys.argv[0]).resolve()), *sys.argv[1:]]


def _batch_quote(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _write_windows_installer(source_dir: Path, target_dir: Path) -> Path:
    restart_args = " ".join(_batch_quote(arg) for arg in _restart_command())
    script_path = Path(tempfile.mkdtemp(prefix="miyou-update-")) / "install_update.bat"
    script_path.write_text(
        "\n".join([
            "@echo off",
            "setlocal",
            f"set PID={os.getpid()}",
            ":wait",
            'tasklist /FI "PID eq %PID%" | find "%PID%" >nul',
            "if not errorlevel 1 (",
            "  timeout /t 1 /nobreak >nul",
            "  goto wait",
            ")",
            f"robocopy {_batch_quote(str(source_dir))} {_batch_quote(str(target_dir))} /E /NFL /NDL /NJH /NJS /NC /NS",
            "if %ERRORLEVEL% LEQ 7 set ERRORLEVEL=0",
            f"cd /d {_batch_quote(str(target_dir))}",
            f"start \"\" {restart_args}",
            "endlocal",
        ]),
        encoding="utf-8",
    )
    return script_path


def _copy_update_now(source_dir: Path, target_dir: Path) -> None:
    for source in source_dir.rglob("*"):
        relative_path = source.relative_to(source_dir)
        target = target_dir / relative_path
        if source.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)


def install_update(asset: ReleaseAsset) -> bool:
    temp_dir = Path(tempfile.mkdtemp(prefix="miyou-loader-update-"))
    zip_path = temp_dir / asset.name
    extract_dir = temp_dir / "extracted"
    extract_dir.mkdir()

    _download_asset(asset, zip_path)
    with zipfile.ZipFile(zip_path) as zip_ref:
        _safe_extract(zip_ref, extract_dir)

    source_dir = _archive_root(extract_dir)
    target_dir = Path(program_variables.project_root)

    if os.name == "nt":
        script_path = _write_windows_installer(source_dir, target_dir)
        creationflags = (
            getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            | getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )
        subprocess.Popen(
            ["cmd", "/c", str(script_path)],
            cwd=str(target_dir),
            creationflags=creationflags,
        )
    else:
        _copy_update_now(source_dir, target_dir)
        subprocess.Popen(_restart_command(), cwd=str(target_dir))

    return True
