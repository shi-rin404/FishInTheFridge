import json

from PySide6.QtWidgets import QMessageBox as _QMB


def on_create_preset(exception: Exception, base_function_name: str):
    from .handler_dispatcher import error_handlers
    from ui.manage_presets_page import ManagePresetsPage as _ManagePresetsPage

    _parent = _ManagePresetsPage.manage_presets_page

    def on_value_error():
        """A preset with that name already exists."""
        _QMB.warning(
            _parent, "Preset Already Exists",
            str(exception),
        )

    def on_file_not_found_error():
        """presets.json is missing — recreate it so the user can retry."""
        from core.variable_manager import program_variables
        path = program_variables.presets_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")
        _QMB.information(
            _parent, "Presets File Recreated",
            "presets.json was missing and has been recreated.\nPlease try again.",
        )

    def on_json_decode_error():
        """presets.json is empty or malformed."""
        _QMB.critical(
            _parent, "Corrupted Presets File",
            "presets.json is corrupted and could not be read.\n"
            "Fix or delete the file and try again.",
        )

    def on_permission_error():
        """No write access to presets.json."""
        _QMB.critical(
            _parent, "Permission Denied",
            "This application does not have permission to write to presets.json.\n"
            "Try restarting it as administrator.",
        )

    def on_os_error():
        """General filesystem error while writing presets.json."""
        _QMB.critical(
            _parent, "Filesystem Error",
            f"A filesystem error occurred while saving the preset:\n{exception}",
        )

    handlers = {
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
        error_handlers["unknown"](_parent, exception, base_function_name)
