from typing import Literal

from core.variable_manager import program_variables
from modding.ui.load_json_lists import load_json_list


def _skin_combos() -> list[tuple]:
    """Returns (combo, list_path, path_dict) tuples for all live skin combos."""
    from modding.path_dictionary import skin_dict
    from ui.main_page import MainPage
    from ui.manage_mod_skin_page import ManageModSkinPage
    from ui.manage_presets_page import ManagePresetsPage

    combos = []

    if MainPage.main_page is not None:
        combos.append((MainPage.main_page.apply_panel.skin_combo,
                       program_variables.skin_list_path, skin_dict))

    page = ManageModSkinPage.manage_mod_skin_page
    if page is not None and page.editor_mode == "skin":
        combos.append((page.ms_combo, program_variables.skin_list_path, skin_dict))

    presets_page = ManagePresetsPage.manage_presets_page
    if presets_page is not None:
        combos.append((presets_page.skin_combo, program_variables.skin_list_path, skin_dict))

    return combos


def _mod_combos() -> list[tuple]:
    """Returns (combo, list_path, path_dict) tuples for all live mod combos."""
    from modding.path_dictionary import mod_dict
    from ui.main_page import MainPage
    from ui.manage_mod_skin_page import ManageModSkinPage
    from ui.manage_presets_page import ManagePresetsPage

    combos = []

    if MainPage.main_page is not None:
        combos.append((MainPage.main_page.apply_panel.mod_combo,
                       program_variables.mod_list_path, mod_dict))

    page = ManageModSkinPage.manage_mod_skin_page
    if page is not None and page.editor_mode == "mod":
        combos.append((page.ms_combo, program_variables.mod_list_path, mod_dict))

    presets_page = ManagePresetsPage.manage_presets_page
    if presets_page is not None:
        combos.append((presets_page.mod_combo, program_variables.mod_list_path, mod_dict))

    return combos


def _preset_combos() -> None:
    """Reload all live preset comboboxes from presets.json."""
    from ui.main_page import MainPage
    from ui.manage_presets_page import ManagePresetsPage
    from modding.path_dictionary import preset_dict
    from modding.preset_manager import read_presets

    data = read_presets() or {}
    preset_names = list(data.keys())
    preset_dict.clear()
    preset_dict.update(data)

    def reload_preset_combo(combo):
        current_text = combo.currentText()
        combo.blockSignals(True)
        combo.clear()
        combo.addItems(preset_names)
        index = combo.findText(current_text)
        combo.setCurrentIndex(index if index != -1 else -1)
        combo.blockSignals(False)

    main = MainPage.main_page
    if main is not None:
        reload_preset_combo(main.bottom_row.preset_combo)

    page = ManagePresetsPage.manage_presets_page
    if page is not None:
        page._reload_preset_combos()

    try:
        from ui.options_page import OptionsPage
    except ImportError:
        OptionsPage = None
    if OptionsPage is not None and OptionsPage.options_page is not None:
        reload_preset_combo(OptionsPage.options_page.launch_preset_combo)


def update_comboboxes(mode: Literal["skin", "mod", "preset", "all"] = "all"):
    """Reload all registered comboboxes for the given mode from their JSON source."""
    targets: list[tuple] = []

    if mode in ("skin", "all"):
        targets.extend(_skin_combos())
    if mode in ("skin", "mod", "all"):
        targets.extend(_mod_combos())

    for combo, list_path, path_dict in targets:
        load_json_list(combo, list_path, path_dict)

    if mode in ("mod", "all"):
        from ui.main_page import MainPage

        if (
            MainPage.main_page is not None
            and hasattr(MainPage.main_page, "apply_panel")
        ):
            MainPage.main_page.apply_panel.refresh_mod_filter()

    if mode in ("preset", "all"):
        _preset_combos()
