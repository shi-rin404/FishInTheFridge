import json
import shutil
from pathlib import Path
from typing import Any


DEFAULT_MEMORY = {
    "game_executable": None,
    "load_mods_on_launch": False,
    "load_mods_on_launch_preset": "",
    "background_color": "#EAE4D5",
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
    _copy_missing_children(
        Path(program_variables.default_3dm_folder_path),
        Path(program_variables._3dm_folder_path),
    )
    for folder_name in _3DM_EMPTY_DIRS:
        (Path(program_variables._3dm_folder_path) / folder_name).mkdir(
            parents=True,
            exist_ok=True,
        )
