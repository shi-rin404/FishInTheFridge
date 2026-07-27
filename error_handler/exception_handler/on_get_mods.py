from PySide6.QtWidgets import QMessageBox as _QMB

def on_get_mods(exception: Exception, base_function_name: str):
    from .handler_dispatcher import error_handlers
    from ui.main_page import MainPage as _MainPage

    def on_file_not_found_error():
        "mod_dir path does not exist — game directory likely not configured yet"
        from database.user.user_variables import user_variables
        _QMB.warning(_MainPage.main_page, "Mod Directory Not Found",
            f"The mod directory could not be found:\n{user_variables.mod_dir}\n\n"
            "Please set your game executable path in settings.")

    def on_type_error():
        "mod_dir is None — game executable has not been set"
        _QMB.warning(_MainPage.main_page, "Game Path Not Set",
            "No game directory is configured.\n"
            "Please set your game executable path in settings before loading mods.")

    def on_permission_error():
        "mod_dir exists but is not readable"
        _QMB.critical(_MainPage.main_page, "Permission Denied",
            "This app doesn't have permission to read the mod directory.\n"
            "Please restart it as administrator and try again.")

    handlers = {
        FileNotFoundError: on_file_not_found_error,
        TypeError:         on_type_error,
        PermissionError:   on_permission_error,
    }

    handler = handlers.get(type(exception))
    if handler is not None:
        handler()
    else:
        error_handlers["unknown"](_MainPage.main_page, exception, base_function_name)
