import json

from PySide6.QtWidgets import QMessageBox as _QMB


def on_read_preset_entries(exception: Exception, base_function_name: str):
    from .handler_dispatcher import error_handlers
    from ui.manage_presets_page import ManagePresetsPage as _ManagePresetsPage

    _parent = _ManagePresetsPage.manage_presets_page

    def on_key_error():
        """Selected preset no longer exists in the database (stale combo)."""
        _QMB.warning(
            _parent, "Preset Not Found",
            "The selected preset was not found in the database.\n"
            "It may have been deleted. Please select a different preset and try again.",
        )

    def on_file_not_found_error():
        """presets.json does not exist."""
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
        KeyError:             on_key_error,
        FileNotFoundError:    on_file_not_found_error,
        json.JSONDecodeError: on_json_decode_error,
    }

    handler = handlers.get(type(exception))
    if handler is not None:
        handler()
    else:
        error_handlers["unknown"](_parent, exception, base_function_name)
