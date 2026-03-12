import json

from PySide6.QtWidgets import QMessageBox as _QMB


def on_delete_preset(exception: Exception, base_function_name: str):
    from .handler_dispatcher import error_handlers
    from ui.manage_presets_page import ManagePresetsPage as _ManagePresetsPage

    _parent = _ManagePresetsPage.manage_presets_page

    def on_key_error():
        """Preset no longer exists in the database (stale combo)."""
        _QMB.warning(
            _parent, "Preset Not Found",
            "The selected preset was not found in the database.\n"
            "It may have already been deleted.",
        )

    def on_file_not_found_error():
        _QMB.critical(
            _parent, "Presets File Not Found",
            "presets.json could not be found.",
        )

    def on_json_decode_error():
        _QMB.critical(
            _parent, "Corrupted Presets File",
            "presets.json is corrupted and could not be read.\n"
            "Fix or delete the file and try again.",
        )

    def on_permission_error():
        _QMB.critical(
            _parent, "Permission Denied",
            "This application does not have permission to write to presets.json.\n"
            "Try restarting it as administrator.",
        )

    def on_os_error():
        _QMB.critical(
            _parent, "Filesystem Error",
            f"A filesystem error occurred while deleting the preset:\n{exception}",
        )

    handlers = {
        KeyError:             on_key_error,
        FileNotFoundError:    on_file_not_found_error,
        json.JSONDecodeError: on_json_decode_error,
        PermissionError:      on_permission_error,
        OSError:              on_os_error,
    }

    handler = handlers.get(type(exception))
    if handler is not None:
        handler()
    else:
        error_handlers["unknown"](_parent, exception, base_function_name)
