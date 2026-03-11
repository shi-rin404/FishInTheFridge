from PySide6.QtWidgets import QMessageBox as _QMB

def on_update_comboboxes(exception: Exception, base_function_name: str):
    from .handler_dispatcher import error_handlers
    from ui.main_page import MainPage as _MainPage

    def on_file_not_found_error():
        "skin_list.json or mod_list.json is missing"
        _QMB.critical(_MainPage.main_page, "List File Not Found",
            "A skin or mod list file could not be found while refreshing the dropdowns.\n"
            "Try restarting the application.")

    def on_json_decode_error():
        "skin_list.json or mod_list.json contains malformed JSON"
        _QMB.critical(_MainPage.main_page, "List File Corrupted",
            "A skin or mod list file is corrupted and could not be read.\n"
            "Fix or delete it and try again.")

    def on_attribute_error():
        "A combo widget or UI component was not available on the expected page"
        _QMB.critical(_MainPage.main_page, "UI Refresh Failed",
            "A dropdown could not be refreshed because a UI component was unavailable.\n"
            "Try reopening the window.")

    import json
    handlers = {
        FileNotFoundError:    on_file_not_found_error,
        json.JSONDecodeError: on_json_decode_error,
        AttributeError:       on_attribute_error,
    }

    handler = handlers.get(type(exception))
    if handler is not None:
        handler()
    else:
        error_handlers["unknown"](_MainPage.main_page, exception, base_function_name)
