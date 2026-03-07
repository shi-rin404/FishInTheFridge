import json, os, re, zipfile
from ..database.user.user_variables import user_variables
from ..io.input.select_mod_zip import select_mod_zip

def _collect_mod_paths(data) -> list[str]:
    """Recursively collect all string values starting with mod/ or mod\\ from parsed JSON."""
    paths = []
    if isinstance(data, dict):
        for v in data.values():
            paths.extend(_collect_mod_paths(v))
    elif isinstance(data, list):
        for item in data:
            paths.extend(_collect_mod_paths(item))
    elif isinstance(data, str) and re.match(r'mod[\\/]', data):
        paths.append(data)
    return paths

def validate_mod(zip_path: str, mod_dir: str = user_variables.mod_dir) -> list[str]:
    """
    Validates mod.json paths against the ZIP and installed mods.
    - Own files (inside this ZIP): hard error if missing.
    - Dependency files (not in this ZIP): soft warning if not yet installed.
    Returns a list of warning strings for missing dependencies.
    """
    res_dir = mod_dir
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        mod_json_entries = [n for n in zip_ref.namelist() if os.path.basename(n) == "mod.json"]

        if not mod_json_entries:
            raise FileNotFoundError("mod.json not found in ZIP")

        if len(mod_json_entries) > 1:
            raise ValueError("Multiple mod.json entries found in ZIP")

        with zip_ref.open(mod_json_entries[0]) as f:
            mod_data = json.load(f)

        zip_names = {n.replace("\\", "/") for n in zip_ref.namelist()}

    mod_paths = _collect_mod_paths(mod_data)

    if not mod_paths:
        raise ValueError("No mod/ paths found in mod.json")

    own_paths, dep_paths = [], []
    for p in mod_paths:
        rel = re.sub(r'^mod[\\/]', '', p).replace("\\", "/")
        (own_paths if rel in zip_names else dep_paths).append(p)

    missing_own = [
        p for p in own_paths
        if not os.path.exists(os.path.join(res_dir, re.sub(r'[\\/]', os.sep, p)))
    ]
    if missing_own:
        raise FileNotFoundError(f"Missing mod files after extraction: {missing_own}")

    return [
        f"Dependency not installed (install separately): {p}"
        for p in dep_paths
        if not os.path.exists(os.path.join(res_dir, re.sub(r'[\\/]', os.sep, p)))
    ]

def install_mod(mod_dir:str = user_variables.mod_dir) -> bool | list[str]:
    """
    True → installed, all dependencies present
    list[str] → installed, but has unmet dependencies (non-empty warning strings)
    False → user cancelled
    """
    selected_mod = select_mod_zip()
    if selected_mod is None:
        return False

    warnings = validate_mod(selected_mod, mod_dir)

    with zipfile.ZipFile(selected_mod, 'r') as zip_ref:
        zip_ref.extractall(mod_dir)

    return warnings if warnings else True