import json
from pathlib import Path

from PySide6.QtWidgets import QComboBox

def load_json_list(combo: QComboBox, path: Path, path_dict: dict | None = None) -> bool:
    "path_dict = Path dictionary you want to update simultaneously."
    try:
        with open(path, encoding="utf-8") as f:
            loaded = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as exc:
        exc._json_path = path
        raise

    if path_dict is not None:
        for name, val in loaded.items():
            path_dict[name] = val
    else:
        path_dict = loaded

    combo.clear()
    for name, val in path_dict.items():
        combo.addItem(name, userData=val)
    return True
