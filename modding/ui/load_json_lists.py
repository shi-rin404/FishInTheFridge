import json
from pathlib import Path

from PySide6.QtWidgets import QComboBox

from core.variable_manager import program_variables
from modding.character_lookup import (
    character_from_skin_record,
    load_character_keywords,
)
from modding import path_dictionary as pd


def _sync_skin_characters(path: Path, loaded: dict) -> None:
    if Path(path) != Path(program_variables.skin_list_path):
        return
    character_keywords = load_character_keywords()
    skin_characters = {
        skin_name: character_from_skin_record(record, character_keywords)
        for skin_name, record in loaded.items()
        if isinstance(record, dict)
    }
    pd.skin_character_dict.clear()
    pd.skin_character_dict.update(skin_characters)
    pd.sync_character_group("skins", skin_characters)


def load_json_list(combo: QComboBox, path: Path, path_dict: dict | None = None) -> bool:
    "path_dict = Path dictionary you want to update simultaneously."
    try:
        with open(path, encoding="utf-8") as f:
            loaded = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as exc:
        exc._json_path = path
        raise

    _sync_skin_characters(path, loaded)

    if path_dict is not None:
        for name, val in loaded.items():
            path_dict[name] = val
    else:
        path_dict = loaded

    combo.clear()
    for name, val in path_dict.items():
        combo.addItem(name, userData=val)
    return True
