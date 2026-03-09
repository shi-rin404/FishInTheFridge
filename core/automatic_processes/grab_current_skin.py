import re

# All of them are m.group(1)
SKIN_NAME_PATTERN = r"separate_dir[\\/](\w+_[cde]_\w+)[\\/].*?\.gim"
SURVIVOR_NAME_PATTERN = r"chr[\\/]player[\\/](dm65_survivor_girl|dm65_survivor_m|h55_survivor_puppet|dm65_survivor_w)[\\/]((?:h55|dm65)_survivor_(?:(?:m|w)_)?\w+)[\\/]"
HUNTER_NAME_PATTERN = r"chr[\\/]boss[\\/](\w+))[\\/]]"
ITEM_NAME_PATTERN = r"chr[\\/]prop[\\/](h55_pendant_\w+)[\\/]"
ACCESSORY_NAME_PATTERN = r"chr[\\/]guajian[\\/](h55_guajian_\w+)[\\/]]"

###
SKIN_PATH_PATTERN_SURVIVOR = r"chr[\\/]player[\\/](?:dm65_survivor_girl|dm65_survivor_m|h55_survivor_puppet|dm65_survivor_w)[\\/](?:(?:h55|dm65)_survivor_(?:(?:m|w)_)?\w+)[\\/]separate_dir[\\/]SKINNAME[\\/]SKINNAME.gim"
SKIN_PATH_PATTERN_HUNTER = r"chr[\\/]boss[\\/].*?[\\/]separate_dir[\\/]SKINNAME[\\/]SKINNAME.gim"
SKIN_ITEM_NAME_PATTERN = r"chr[\\/]prop[\\/](?:h55_pendant_\w+)[\\/]separete_dir[\\/]SKINNAME[\\/]SKINNAME.gim"

###
GENERIC_SKIN_PATH_BRUTE_FORCE = r"chr[\\/]TYPEHINT[\\/](?:.*?[\\/])+separate_dir[\\/](?:\w+[\\/])+(?:\w+_[cde]_[^_]+)\.gim"

def fix_item_cases(potantial_item_path: str) -> str:
    if potantial_item_path == None:
        return None    

    if "separate_dir" in potantial_item_path:
        skin_name = re.search(SKIN_NAME_PATTERN, potantial_item_path).group(1)
        type_hint = None
        if "player" in potantial_item_path:
            type_hint = "player"
            ret = grab_current_skin("SURVIVOR", re.compile(SKIN_PATH_PATTERN_SURVIVOR.replace("SKINNAME", skin_name)))
        elif "boss" in potantial_item_path:
            type_hint = "boss"
            ret = grab_current_skin("HUNTER", re.compile(SKIN_PATH_PATTERN_HUNTER.replace("SKINNAME", skin_name)))
        elif "prop" in potantial_item_path:
            type_hint = "prop"
            ret = grab_current_skin("ITEM", re.compile(SKIN_ITEM_NAME_PATTERN.replace("SKINNAME", skin_name)))
        
        if ret is None:            
            return grab_current_skin("ALL", re.compile(GENERIC_SKIN_PATH_BRUTE_FORCE.replace("TYPEHINT", type_hint)))
        else:
            return ret

    return potantial_item_path

patterns = {
    "CHARACTER": r"chr[\\/](?:player|boss)[\\/](?:\w+[\\/])+\w+\.gim",
    "SURVIVOR": r"chr[\\/]player[\\/](?:\w+[\\/])+\w+\.gim",
    "HUNTER": r"chr[\\/]boss[\\/](?:\w+[\\/])+\w+\.gim",
    "ITEM": r"chr[\\/]prop[\\/](?:\w+[\\/])+\w+\.gim",
    "ACCESSORY": r"chr[\\/]guajian[\\/](?:\w+[\\/])+\w+\.gim",
    "ALL": r"chr[\\/](?:\w+[\\/])+\w+\.gim"
}

from typing import Literal
def grab_current_skin(search_mode:Literal["CHARACTER", "SURVIVOR", "HUNTER", "ITEM", "ACCESSORY", "ALL"] = "CHARACTER", pattern:re.Pattern = None) -> str | None:
    search_mode = search_mode.upper() 

    from database.user.user_variables import user_variables
    with open(user_variables.game_logs, "r", encoding="utf-8") as f:
        matches = re.findall(patterns[search_mode] if pattern == None else pattern, f.read())
        last_match = matches[-1] if matches else None

    if last_match is None: return "No skin path found"

    if (pattern == None and
        not "guajian" in last_match and
                last_match != None):
                    return fix_item_cases(last_match)

    return last_match if last_match else "No skin path found"

if __name__ == "__main__":
    print(grab_current_skin())