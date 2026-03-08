from PySide6.QtWidgets import QMessageBox as _QMB

def on_apply_mod(exception: Exception, base_function_name: str):
    from .handler_dispatcher import error_handlers
    from ui.main_page import MainPage as _MainPage
    def on_runtime_error():
        "Target process is not running — _pid_by_name found no matching entry in EnumProcesses"
        _QMB.critical(_MainPage.main_page, "Game Not Running", "The game doesn't appear to be running.\nPlease launch the game first, then try again.")

    def on_permission_error():
        "OpenProcess was denied — user must run as administrator to attach to the target process"
        _QMB.critical(_MainPage.main_page, "Permission Denied", "This app needs administrator rights to apply mods.\nPlease restart it as administrator and try again.")

    def on_attribute_error():
        "original_to_mod is None, or a key inside it is None (None.keys() / None.encode() fails)"
        _QMB.critical(_MainPage.main_page, "Nothing Selected", "Please select both a skin and a mod before applying.")

    def on_type_error():
        "A value inside original_to_mod is None — len(None) fails in _build_payload"
        _QMB.critical(_MainPage.main_page, "Invalid Mod", "The selected mod path is invalid.\nPlease re-select the mod and try again.")

    def on_value_error():
        "Mod path is longer than placeholder path"
        _QMB.critical(_MainPage.main_page, "Mod Path Is Too Long", "The mod path is longer than skin path. Select another skin or fix the mod path.")

    handlers = {
        RuntimeError:    on_runtime_error,
        PermissionError: on_permission_error,
        AttributeError:  on_attribute_error,
        TypeError:       on_type_error,
        ValueError:      on_value_error,
    }

    handler = handlers.get(type(exception))
    if handler is not None:
        handler()
    else:
        error_handlers["unknown"](_MainPage.main_page, exception, base_function_name)