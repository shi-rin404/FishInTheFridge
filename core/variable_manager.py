from pathlib import Path

class ProgramVariables():    
    __memory_json__ = Path(__file__).parent.parent / "database" / "user" / "memory.json"
    __system_variables_json__ = Path(__file__).parent.parent / "database" / "system" / "system_variables.json"
    skin_list_path = Path(__file__).parent.parent / "database" / "modding" / "skin_list.json"
    mod_list_path = Path(__file__).parent.parent / "database" / "modding" / "mod_list.json"
    presets_path = Path(__file__).parent.parent / "database" / "user" / "presets.json"
    auth_file    = Path(__file__).parent.parent / "database" / "user" / "auth.dat"
    _3dm_folder_path = Path(__file__).parent.parent / "modding" / "3dm"

program_variables = ProgramVariables()