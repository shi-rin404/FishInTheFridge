import json, os, re, zipfile
from database.user.user_variables import user_variables
from file_io.input.select_mod_zip import select_mod_zip


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

def validate_mod(zip_path: str) -> dict[str, list[str] | bool]:
    """
    Validates all mods inside a ZIP. Each mod must be in its own folder:
        zip > ModName/ > mod.json + mod/ files
    Supports multiple mods per ZIP.
    - Own files (inside this ZIP): hard error if missing.
    - Dependency files (not in this ZIP): soft warning if not yet installed.
    Returns a dict with a combined list of warning strings for missing dependencies and is it needs a single mod fix.
    """
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        mod_json_entries = [n for n in zip_ref.namelist() if os.path.basename(n) == "mod.json"]

        if not mod_json_entries:
            raise FileNotFoundError("mod.json not found in ZIP")

        single_mod = len(mod_json_entries) == 1
        single_mod_fix = False
        for entry in mod_json_entries:
            if '/' not in entry:
                if not single_mod:
                    raise ValueError(f"mod.json must be inside a mod folder, not at ZIP root: '{entry}'")
                single_mod_fix = True

        zip_names = {n.replace("\\", "/") for n in zip_ref.namelist()}
        all_warnings = []

        for mod_json_path in mod_json_entries:
            mod_folder = (mod_json_path.rsplit('/', 1)[0] + '/') if '/' in mod_json_path else ''

            with zip_ref.open(mod_json_path) as f:
                mod_data = json.load(f)

            mod_paths = _collect_mod_paths(mod_data)
            if not mod_paths:
                raise ValueError(f"No mod/ paths found in mod.json inside '{mod_folder}'")

            own_paths, dep_paths = [], []
            for p in mod_paths:
                stripped = re.sub(r'^mod[\\/]', '', p).replace("\\", "/")
                # single_mod_fix: files are at ZIP root, so strip one more folder level
                full_zip_path = stripped.split('/', 1)[-1] if single_mod_fix else stripped
                (own_paths if full_zip_path in zip_names else dep_paths).append(p)

            missing_own = []
            for p in own_paths:
                full_zip_path = re.sub(r'^mod[\\/]', '', p).replace("\\", "/")
                if single_mod_fix:
                    full_zip_path = full_zip_path.split('/', 1)[-1]
                if full_zip_path not in zip_names:
                    missing_own.append(p)

            if missing_own:
                raise FileNotFoundError(f"[{mod_folder}] Missing mod files in ZIP: {missing_own}")

            all_warnings.extend(
                f"[{mod_folder}] Dependency not included in ZIP (install separately): {p}"
                for p in dep_paths
                if re.sub(r'^mod[\\/]', '', p).replace("\\", "/") not in zip_names
            )

    return {"warnings": all_warnings, "single_mod_fix": single_mod_fix}

def install_mod(mod_dir:str = user_variables.mod_dir) -> bool | list[str]:
    """
    True → installed, all dependencies present
    list[str] → installed, but has unmet dependencies (non-empty warning strings)
    False → user cancelled
    """
    selected_mod = select_mod_zip()
    if selected_mod is None:
        return False

    """
    {
    "warnings": all_warnings: list[str],
    "single_mod_fix": single_mod_fix: bool
    }
    """
    validate_info:dict[str, list[str] | bool] = validate_mod(selected_mod)

    with zipfile.ZipFile(selected_mod, 'r') as zip_ref:
        if validate_info["single_mod_fix"]:
            target_mod_folder = os.path.join(mod_dir, os.path.splitext(os.path.basename(selected_mod))[0])
            if not os.path.exists(target_mod_folder):
                os.mkdir(target_mod_folder)
            zip_ref.extractall(target_mod_folder)
        else:
            zip_ref.extractall(mod_dir)

    from PySide6.QtWidgets import QMessageBox as _QMB
    from ui.main_page import MainPage as _MainPage

    feedback_content = "Mod(s) installed successfully."
    if validate_info["warnings"]:
        warnings_text = "\n".join(validate_info["warnings"])
        feedback_content = f"{feedback_content}\n\nMissing dependencies:\n{warnings_text}"
    
    _QMB.information(_MainPage.main_page, "Mod(s) Installed", feedback_content)

    return True