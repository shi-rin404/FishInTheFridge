import json
from typing import Any

def edit_json(file_path: str, value: Any) -> bool:
    with open(file_path, 'r+', encoding="utf-8") as f:
        data = json.load(f)
        data["game_executable"] = value
        f.seek(0)
        json.dump(data, f)
        f.truncate()
    
    return True