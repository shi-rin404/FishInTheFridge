import json

from PySide6.QtWidgets import QMessageBox as _QMB


def on_add_entry(exception: Exception, base_function_name: str):
    from .handler_dispatcher import error_handlers
    from ui.manage_presets_page import ManagePresetsPage as _ManagePresetsPage

    def on_key_error():
        """Selected preset no longer exists in the database (stale combo)."""
        _QMB.warning(
            _ManagePresetsPage.manage_presets_page, "Preset Not Found",
            "The selected preset was not found in the database.\n"
            "It may have been deleted. Please select a different preset and try again.",
        )

    def on_value_error():
        """Skin already has an entry in this preset."""
        _QMB.warning(
            _ManagePresetsPage.manage_presets_page, "Duplicate Entry",
            str(exception),
        )

    def on_file_not_found_error():
        """presets.json is missing — guide user to create a preset first."""
        _QMB.critical(
            _ManagePresetsPage.manage_presets_page, "Presets File Not Found",
            "presets.json could not be found.\n"
            "Create a preset first, then try adding an entry.",
        )

    def on_json_decode_error():
        """presets.json is empty or malformed."""
        _QMB.critical(
            _ManagePresetsPage.manage_presets_page, "Corrupted Presets File",
            "presets.json is corrupted and could not be read.\n"
            "Fix or delete the file and try again.",
        )

    def on_permission_error():
        """No write access to presets.json."""
        _QMB.critical(
            _ManagePresetsPage.manage_presets_page, "Permission Denied",
            "This application does not have permission to write to presets.json.\n"
            "Try restarting it as administrator.",
        )

    def on_os_error():
        """General filesystem error while writing presets.json."""
        _QMB.critical(
            _ManagePresetsPage.manage_presets_page, "Filesystem Error",
            f"A filesystem error occurred while saving the entry:\n{exception}",
        )

    handlers = {
        KeyError:             on_key_error,
        ValueError:           on_value_error,
        FileNotFoundError:    on_file_not_found_error,
        json.JSONDecodeError: on_json_decode_error,
        PermissionError:      on_permission_error,
        OSError:              on_os_error,
    }

    handler = handlers.get(type(exception))
    if handler is not None:
        handler()
    else:
        error_handlers["unknown"](_ManagePresetsPage.manage_presets_page, exception, base_function_name)
