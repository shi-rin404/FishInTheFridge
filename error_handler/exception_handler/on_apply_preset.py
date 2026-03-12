import json

from PySide6.QtWidgets import QMessageBox as _QMB


def on_apply_preset(exception: Exception, base_function_name: str):
    from .handler_dispatcher import error_handlers
    from ui.main_page import MainPage as _MainPage

    _parent = _MainPage.main_page

    def on_key_error():
        """Skin or mod name in the preset is no longer in the local lists."""
        _QMB.warning(
            _parent, "Entry Not Found",
            str(exception),
        )

    def on_value_error():
        """Preset is empty — nothing to apply."""
        _QMB.warning(
            _parent, "Empty Preset",
            str(exception),
        )

    def on_runtime_error():
        """Game process is not running."""
        _QMB.critical(
            _parent, "Game Not Running",
            "The game process could not be found.\n"
            "Please launch the game and try again.",
        )

    def on_permission_error():
        """No access to the game process."""
        _QMB.critical(
            _parent, "Permission Denied",
            "Cannot open the game process.\n"
            "Try restarting this application as administrator.",
        )

    def on_file_not_found_error():
        """presets.json is missing."""
        _QMB.critical(
            _parent, "Presets File Not Found",
            "presets.json could not be found.\n"
            "Create a preset first, then try applying it.",
        )

    def on_json_decode_error():
        """presets.json is malformed."""
        _QMB.critical(
            _parent, "Corrupted Presets File",
            "presets.json is corrupted and could not be read.\n"
            "Fix or delete the file and try again.",
        )

    def on_os_error():
        _QMB.critical(
            _parent, "Filesystem Error",
            f"A filesystem error occurred while reading the preset:\n{exception}",
        )

    handlers = {
        KeyError:             on_key_error,
        ValueError:           on_value_error,
        RuntimeError:         on_runtime_error,
        PermissionError:      on_permission_error,
        FileNotFoundError:    on_file_not_found_error,
        json.JSONDecodeError: on_json_decode_error,
        OSError:              on_os_error,
    }

    handler = handlers.get(type(exception))
    if handler is not None:
        handler()
    else:
        error_handlers["unknown"](_parent, exception, base_function_name)
