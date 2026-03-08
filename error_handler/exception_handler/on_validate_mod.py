import json, zipfile
from PySide6.QtWidgets import QMessageBox as _QMB

def on_validate_mod(exception: Exception, base_function_name: str):
    from .handler_dispatcher import error_handlers
    from ui.main_page import MainPage as _MainPage

    def on_file_not_found_error():
        _QMB.critical(_MainPage.main_page, "Mod File Missing",
            f"A required file was not found:\n\n{exception}")

    def on_value_error():
        _QMB.critical(_MainPage.main_page, "Invalid Mod Structure",
            f"The mod ZIP is not structured correctly:\n\n{exception}")

    def on_bad_zip_file():
        _QMB.critical(_MainPage.main_page, "Invalid ZIP",
            "The selected file is not a valid ZIP archive or is corrupted.")

    def on_json_decode_error():
        _QMB.critical(_MainPage.main_page, "Invalid mod.json",
            f"mod.json could not be parsed:\n\n{exception}")

    handlers = {
        FileNotFoundError:      on_file_not_found_error,
        ValueError:             on_value_error,
        zipfile.BadZipFile:     on_bad_zip_file,
        json.JSONDecodeError:   on_json_decode_error
    }

    handler = handlers.get(type(exception))
    if handler is not None:
        handler()
    else:
        error_handlers["unknown"](_MainPage.main_page, exception, base_function_name)