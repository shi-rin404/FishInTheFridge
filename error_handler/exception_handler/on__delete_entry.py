from PySide6.QtWidgets import QMessageBox as _QMB

def on__delete_entry(exception: Exception, base_function_name: str):
    from .handler_dispatcher import error_handlers
    from ui.main_page import MainPage as _MainPage

    def on_os_error():
        "Filesystem error while reading a mod.json or deleting the mod folder"
        _QMB.critical(_MainPage.main_page, "Delete Failed",
            f"A filesystem error occurred while deleting the entry:\n{exception}")

    def on_json_decode_error():
        "A mod.json file in the mod directory is malformed and could not be parsed"
        _QMB.critical(_MainPage.main_page, "Malformed mod.json",
            "A mod.json file in the mod directory is corrupted and could not be read.\n"
            "Fix or remove it and try again.")

    def on_file_not_found_error():
        "skin_list.json or mod_list.json is missing"
        _QMB.critical(_MainPage.main_page, "List File Not Found",
            "The skin/mod list file could not be found.\n"
            "Try restarting the application.")

    import json
    handlers = {
        OSError:               on_os_error,
        json.JSONDecodeError:  on_json_decode_error,
        FileNotFoundError:     on_file_not_found_error,
    }

    handler = handlers.get(type(exception))
    if handler is not None:
        handler()
    else:
        error_handlers["unknown"](_MainPage.main_page, exception, base_function_name)
