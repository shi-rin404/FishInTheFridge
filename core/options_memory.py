import json
from typing import Any

from core.default_data import DEFAULT_MEMORY
from core.variable_manager import program_variables


def read_memory() -> dict[str, Any]:
    with open(program_variables.__memory_json__, "r", encoding="utf-8") as f:
        data = json.load(f)
    changed = False
    for key, value in DEFAULT_MEMORY.items():
        if key not in data:
            data[key] = value
            changed = True
    if changed:
        write_memory(data)
    return data


def write_memory(data: dict[str, Any]) -> None:
    with open(program_variables.__memory_json__, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def set_memory_value(key: str, value: Any) -> None:
    data = read_memory()
    data[key] = value
    write_memory(data)


def load_mods_on_launch() -> bool:
    return bool(read_memory().get("load_mods_on_launch", False))


def launch_preset() -> str:
    return str(read_memory().get("load_mods_on_launch_preset", "") or "")
