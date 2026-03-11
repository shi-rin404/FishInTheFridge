Never ever pass or continue an exception without triggering an error message.

Default Error Handler is error_handler module in the root folder.

## Error Handler Pattern
- Handler files: `error_handler/exception_handler/on_<func_name>.py`
- Function named `on_<func_name>(exception, base_function_name)`
- Dispatcher key = filename stem stripped of "on_" prefix → matches `func.__name__`
- Leading-underscore functions: `_foo` → `on__foo.py` (double underscore)
- Call site: `ensure_exception(func, (args,))` — never bare try/except
- Unhandled types fall through to `error_handlers["unknown"]`

## Combobox Registry
- `core/automatic_processes/update_comboboxes.py` — central reload for all live combos
- `update_comboboxes(mode)` where mode = "skin" | "mod" | "all"
- Registered combos: `apply_panel.skin_combo`, `apply_panel.mod_combo`, `ManageModSkinPage.ms_combo`, `ManagePresetsPage.skin_combo`, `ManagePresetsPage.mod_combo`
- No try/except inside — guard with `is not None` checks instead

## Key Class References (singletons)
- `MainPage.main_page` — set in `MainPage.__init__`
- `ManageModSkinPage.manage_mod_skin_page` — set in `ManageModSkinPage.__init__` (class attribute)
- `apply_panel` lives on `MainPage.main_page.apply_panel`

## mod_list.json Structure
- `{mod_name: {data_type: path}}` e.g. `{"Tikisha": {"skin": "mod/Tikisha/main.gim"}}`
- Keys come from `"name"` field in `mod.json`; remaining fields become the value dict

## manage_mod_skin_page Mixin Order
- `ManageModSkinPage(_SaveMixin, _TypeComboMixin, _TabLogicMixin, _PanelsMixin, QWidget)`
- `_delete_entry` lives in `_TabLogicMixin`, connected via `ensure_exception` in `_panels.py`
