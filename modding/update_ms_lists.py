from typing import Literal
import json

def update_ms_list(function_mode=Literal["skin", "mod", "preset"]) -> bool:
    from core.variable_manager import program_variables
    
    if function_mode == "skin":
        json_path = program_variables.skin_list_path
        from modding.path_dictionary import skin_dict as ms_dict
    elif function_mode == "mod":
        json_path = program_variables.mod_list_path
        from modding.path_dictionary import mod_dict as ms_dict
    elif function_mode == "preset":
        json_path = program_variables.presets_path
        from modding.path_dictionary import preset_dict as ms_dict
    else:
        raise ValueError("Invalid function_mode. You can only set \"skin\", \"mod\" or \"preset\".")
    
    with open(json_path, 'r', encoding="utf-8") as f:
        new_dict = json.load(f)

        for key, value in new_dict.items():
            ms_dict[key] = value

    return True