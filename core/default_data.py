import json
import shutil
from pathlib import Path
from typing import Any
from zipfile import ZipFile


DEFAULT_MEMORY = {
    "game_executable": None,
    "load_mods_on_launch": False,
    "load_mods_on_launch_preset": "",
    "background_color": "#EAE4D5",
    "custom_bg": False,
    "custom_bg_ext": None,
    "custom_bg_oppacity": None,
}

DEFAULT_PRESETS = {}
DEFAULT_MOD_LIST = {}
_3DM_EMPTY_DIRS = ("Mods", "ShaderCache")


def _copy_json_or_write(path: Path, default_path: Path, fallback: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    if default_path.exists():
        shutil.copy2(default_path, path)
        return
    with path.open("w", encoding="utf-8") as f:
        json.dump(fallback, f, indent=4)


def _copy_missing_children(default_dir: Path, target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    if not default_dir.exists():
        return
    for source in default_dir.iterdir():
        target = target_dir / source.name
        if target.exists():
            continue
        if source.is_dir():
            _copy_missing_children(source, target)
        else:
            shutil.copy2(source, target)


def _safe_zip_target(target_dir: Path, member_name: str) -> Path:
    target = target_dir / member_name
    resolved_target = target.resolve()
    resolved_target_dir = target_dir.resolve()
    if (
        resolved_target != resolved_target_dir
        and resolved_target_dir not in resolved_target.parents
    ):
        raise RuntimeError(f"Refusing to extract outside target directory: {member_name}")
    return target


def _extract_missing_children(default_zip: Path, target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    if not default_zip.exists():
        return
    with ZipFile(default_zip) as zf:
        for member in zf.infolist():
            target = _safe_zip_target(target_dir, member.filename)
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            if target.exists():
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member) as source, target.open("wb") as destination:
                shutil.copyfileobj(source, destination)


def _place_default_3dm(program_variables: type) -> None:
    default_zip = Path(program_variables.default_3dm_zip_path)
    target_dir = Path(program_variables._3dm_folder_path)
    if default_zip.exists():
        _extract_missing_children(default_zip, target_dir)
        return
    _copy_missing_children(Path(program_variables.default_3dm_folder_path), target_dir)


def ensure_user_data(program_variables: type) -> None:
    _copy_json_or_write(
        Path(program_variables.__memory_json__),
        Path(program_variables.default_memory_json),
        DEFAULT_MEMORY,
    )
    _copy_json_or_write(
        Path(program_variables.presets_path),
        Path(program_variables.default_presets_path),
        DEFAULT_PRESETS,
    )
    _copy_json_or_write(
        Path(program_variables.mod_list_path),
        Path(program_variables.default_mod_list_path),
        DEFAULT_MOD_LIST,
    )
    _place_default_3dm(program_variables)
    for folder_name in _3DM_EMPTY_DIRS:
        (Path(program_variables._3dm_folder_path) / folder_name).mkdir(
            parents=True,
            exist_ok=True,
        )
