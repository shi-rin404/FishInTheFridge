import json

from core.variable_manager import program_variables


def read_presets() -> dict:
    """Return the full presets database.

    Raises:
        FileNotFoundError: presets.json does not exist.
        json.JSONDecodeError: presets.json is malformed / empty.
    """
    with open(program_variables.presets_path, encoding="utf-8") as f:
        return json.load(f)


def read_preset_entries(preset_name: str) -> dict:
    """Return the skin→mod mapping for one preset.

    Raises:
        FileNotFoundError: presets.json does not exist.
        json.JSONDecodeError: presets.json is malformed / empty.
        KeyError: preset_name is not a key in the database.
    """
    with open(program_variables.presets_path, encoding="utf-8") as f:
        data = json.load(f)
    if preset_name not in data:
        raise KeyError(f"Preset '{preset_name}' does not exist.")
    return data[preset_name]


def create_preset(preset_name: str) -> bool:
    """Create a new empty preset in presets.json.

    Raises:
        FileNotFoundError: presets.json does not exist.
        json.JSONDecodeError: presets.json is malformed / empty.
        ValueError: a preset with that name already exists.
        PermissionError: no write access to presets.json.
        OSError: other filesystem error.
    """
    path = program_variables.presets_path
    with open(path, "r+", encoding="utf-8") as f:
        data = json.load(f)
        if preset_name in data:
            raise ValueError(f"Preset '{preset_name}' already exists.")
        data[preset_name] = {}
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()
    return True


def delete_preset(preset_name: str) -> bool:
    """Delete an entire preset from presets.json.

    Raises:
        FileNotFoundError: presets.json does not exist.
        json.JSONDecodeError: presets.json is malformed / empty.
        KeyError: preset_name is not a key in the database.
        PermissionError: no write access to presets.json.
        OSError: other filesystem error.
    """
    path = program_variables.presets_path
    with open(path, "r+", encoding="utf-8") as f:
        data = json.load(f)
        if preset_name not in data:
            raise KeyError(f"Preset '{preset_name}' does not exist.")
        del data[preset_name]
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()
    return True


def delete_entry(preset_name: str, skin_name: str) -> bool:
    """Delete a skin→mod pair from an existing preset in presets.json.

    Raises:
        FileNotFoundError: presets.json does not exist.
        json.JSONDecodeError: presets.json is malformed / empty.
        KeyError: preset_name or skin_name is not found in the database.
        PermissionError: no write access to presets.json.
        OSError: other filesystem error.
    """
    path = program_variables.presets_path
    with open(path, "r+", encoding="utf-8") as f:
        data = json.load(f)
        if preset_name not in data:
            raise KeyError(f"Preset '{preset_name}' does not exist.")
        if skin_name not in data[preset_name]:
            raise KeyError(
                f"Entry '{skin_name}' does not exist in preset '{preset_name}'."
            )
        del data[preset_name][skin_name]
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()
    return True


def apply_preset(preset_name: str) -> bool:
    """Apply every skin→mod pair in a preset via in-memory patching.

    Raises:
        FileNotFoundError: presets.json does not exist.
        json.JSONDecodeError: presets.json is malformed / empty.
        KeyError: preset_name not found, or a skin/mod name in the preset is no
                  longer present in skin_list.json / mod_list.json.
        ValueError: preset is empty (nothing to patch).
        RuntimeError: the game process is not running.
        PermissionError: cannot open the game process (run as administrator).
    """
    from modding.apply_mod import apply_mod
    from modding.path_dictionary import skin_dict, mod_dict

    entries = read_preset_entries(preset_name)   # {skin_name: mod_name}

    if not entries:
        raise ValueError(f"Preset '{preset_name}' is empty — nothing to apply.")

    original_to_mod: dict[str, str] = {}
    for skin_name, mod_name in entries.items():
        if skin_name not in skin_dict:
            raise KeyError(
                f"Skin '{skin_name}' was not found in skin_list.json.\n"
                "The skin list may be outdated — try refreshing it."
            )
        if mod_name not in mod_dict:
            raise KeyError(
                f"Mod '{mod_name}' was not found in mod_list.json.\n"
                "The mod list may be outdated — try refreshing it."
            )
        skin_record = skin_dict[skin_name]
        mod_record  = mod_dict[mod_name]
        for key in skin_record:
            if key in mod_record:
                original_to_mod[skin_record[key]] = mod_record[key]

    return apply_mod(original_to_mod)


def add_entry(preset_name: str, skin_name: str, mod_name: str) -> bool:
    """Add a skin→mod pair to an existing preset in presets.json.

    Raises:
        FileNotFoundError: presets.json does not exist.
        json.JSONDecodeError: presets.json is malformed / empty.
        KeyError: preset_name is not a key in the database (stale combo selection).
        ValueError: skin_name already has an entry in this preset.
        PermissionError: no write access to presets.json.
        OSError: other filesystem error.
    """
    path = program_variables.presets_path
    with open(path, "r+", encoding="utf-8") as f:
        data = json.load(f)
        if preset_name not in data:
            raise KeyError(f"Preset '{preset_name}' does not exist.")
        if skin_name in data[preset_name]:
            raise ValueError(
                f"Skin '{skin_name}' already has an entry in preset '{preset_name}'."
            )
        data[preset_name][skin_name] = mod_name
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()
    return True
