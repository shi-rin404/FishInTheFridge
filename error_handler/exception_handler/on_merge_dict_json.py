import json

from PySide6.QtWidgets import QMessageBox as _QMB


def on_merge_dict_json(exception: Exception, base_function_name: str):
    from .handler_dispatcher import error_handlers
    from ui.main_page import MainPage as _MainPage
    
    def target_path() -> str:
        return str(getattr(exception, "filename", None) or "the target JSON file")

    def on_permission_error():
        _QMB.critical(
            _MainPage.main_page,
            "Permission Denied",
            f"It is not able to access {target_path()}. Check your permissions.",
        )

    def on_file_not_found_error():
        _QMB.warning(
            _MainPage.main_page,
            "JSON File Not Found",
            f"Could not find {target_path()}.",
        )

    def on_json_decode_error():
        line = getattr(exception, "lineno", "?")
        column = getattr(exception, "colno", "?")
        _QMB.warning(
            _MainPage.main_page,
            "Invalid JSON",
            f"{target_path()} is not valid JSON.\nLine: {line}, Column: {column}",
        )

    def on_unicode_decode_error():
        _QMB.warning(
            _MainPage.main_page,
            "Encoding Error",
            f"{target_path()} could not be decoded as text.\n{type(exception).__name__}: {exception}",
        )

    def on_type_error():
        _QMB.warning(
            _MainPage.main_page,
            "JSON Structure Error",
            f"Unexpected JSON structure in {target_path()}.\n{type(exception).__name__}: {exception}",
        )

    handlers = {
        PermissionError:      on_permission_error,
        FileNotFoundError:    on_file_not_found_error,
        json.JSONDecodeError: on_json_decode_error,
        UnicodeDecodeError:   on_unicode_decode_error,
        TypeError:            on_type_error,
    }

    handlers.get(
        type(exception),
        lambda: error_handlers["unknown"](_MainPage.main_page, exception, base_function_name),
    )()