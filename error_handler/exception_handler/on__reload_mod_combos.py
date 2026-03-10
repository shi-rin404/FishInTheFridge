from PySide6.QtWidgets import QMessageBox as _QMB

def on__reload_mod_combos(exception: Exception, base_function_name: str):
    from .handler_dispatcher import error_handlers
    from ui.main_page import MainPage as _MainPage

    def on_file_not_found_error():
        "mod_list.json was not found after being written — likely a filesystem permission or path issue"
        _QMB.critical(_MainPage.main_page, "Mod List Not Found",
            "The mod list file could not be found after saving.\n"
            "Check that the mod directory is accessible and try again.")

    def on_attribute_error():
        "An expected UI component (apply panel or mod combo) was missing on the page instance"
        _QMB.critical(_MainPage.main_page, "UI Reload Failed",
            "A UI component could not be refreshed after loading mods.\n"
            "Try reopening the window.")

    handlers = {
        FileNotFoundError: on_file_not_found_error,
        AttributeError:    on_attribute_error,
    }

    handler = handlers.get(type(exception))
    if handler is not None:
        handler()
    else:
        error_handlers["unknown"](_MainPage.main_page, exception, base_function_name)
