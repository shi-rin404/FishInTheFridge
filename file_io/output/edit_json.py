import json
from typing import Any

def edit_json(file_path: str, key: str, value: Any) -> bool:
    with open(file_path, 'r+', encoding="utf-8") as f:
        data = json.load(f)
        data[key] = value
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()
    
    return True

def merge_dict_json(file_path: str, key: str, value: dict) -> bool:
    with open(file_path, 'r+', encoding="utf-8") as f:
        data = json.load(f)
        data[key].update(value)
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()
    
    return True