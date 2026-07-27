from pathlib import Path

class ProgramVariables():
    project_root = Path(__file__).parent.parent
    defaults_path = project_root / "defaults"
    __memory_json__ = project_root / "database" / "user" / "memory.json"
    __system_variables_json__ = project_root / "database" / "system" / "system_variables.json"
    skin_list_path = project_root / "database" / "modding" / "skin_list.json"
    mod_list_path = project_root / "database" / "modding" / "mod_list.json"
    presets_path = project_root / "database" / "user" / "presets.json"
    default_memory_json = defaults_path / "user" / "memory.json"
    default_presets_path = defaults_path / "user" / "presets.json"
    default_mod_list_path = defaults_path / "modding" / "mod_list.json"
    default_3dm_folder_path = defaults_path / "3dm"
    _3dm_folder_path = project_root / "modding" / "3dm"


from core.default_data import ensure_user_data

ensure_user_data(ProgramVariables)

program_variables = ProgramVariables()
