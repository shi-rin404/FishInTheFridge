skin_dict = {}
mod_dict = {}
preset_dict = {}
NO_CHARACTER_INFO = "No Character Info"
character_dict = {}
skin_character_dict = {}
mod_character_dict = {}


def sync_character_group(group_key: str, item_characters: dict[str, str]) -> None:
    for character_data in character_dict.values():
        character_data.setdefault(group_key, []).clear()

    for item_name, character in item_characters.items():
        character_data = character_dict.setdefault(
            character,
            {"skins": [], "mods": []},
        )
        character_data.setdefault(group_key, []).append(item_name)

    empty_characters = [
        character
        for character, character_data in character_dict.items()
        if not character_data.get("skins") and not character_data.get("mods")
    ]
    for character in empty_characters:
        character_dict.pop(character, None)

    for character_data in character_dict.values():
        character_data.setdefault("skins", []).sort(key=str.casefold)
        character_data.setdefault("mods", []).sort(key=str.casefold)
