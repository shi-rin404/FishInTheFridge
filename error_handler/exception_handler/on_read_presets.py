import json

from PySide6.QtWidgets import QMessageBox as _QMB


def on_read_presets(exception: Exception, base_function_name: str):
    from .handler_dispatcher import error_handlers
    from ui.manage_presets_page import ManagePresetsPage as _ManagePresetsPage

    _parent = _ManagePresetsPage.manage_presets_page

    def on_file_not_found_error():
        """presets.json does not exist yet — no presets have been created."""
        _QMB.information(
            _parent, "No Presets Found",
            "presets.json could not be found.\n"
            "Create a preset first.",
        )

    def on_json_decode_error():
        """presets.json is empty or malformed."""
        _QMB.critical(
            _parent, "Corrupted Presets File",
            "presets.json is corrupted and could not be read.\n"
            "Fix or delete the file and try again.",
        )

    handlers = {
        FileNotFoundError:    on_file_not_found_error,
        json.JSONDecodeError: on_json_decode_error,
    }

    handler = handlers.get(type(exception))
    if handler is not None:
        handler()
    else:
        error_handlers["unknown"](_parent, exception, base_function_name)
