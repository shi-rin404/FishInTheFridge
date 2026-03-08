import json

from PySide6.QtWidgets import QMessageBox as _QMB


def on_set_game_executable(exception: Exception, base_function_name: str):
    from .handler_dispatcher import error_handlers
    from ui.main_page import MainPage as _MainPage
    from core.variable_manager import program_variables

    def recreate_and_retry():
        with open(program_variables.__memory_json__, "w", encoding="utf-8") as f:
            json.dump({"game_executable": None}, f)

        from database.user.user_variables import user_variables
        user_variables.set_game_executable()

    def on_permission_error():
        _QMB.critical(
            _MainPage.main_page,
            "Permission Denied",
            f"It is not able to write {program_variables.__memory_json__}. Check your permissions.",
        )

    def on_file_not_found_error():
        _QMB.warning(
            _MainPage.main_page,
            "memory.json is Lost",
            "memory.json was not found and will be created automatically.",
        )
        recreate_and_retry()

    def on_json_decode_error():
        _QMB.warning(
            _MainPage.main_page,
            "memory.json is Damaged",
            "memory.json is not valid JSON and will be re-created automatically.",
        )
        recreate_and_retry()

    def on_unicode_decode_error():
        _QMB.warning(
            _MainPage.main_page,
            "memory.json Encoding Error",
            "memory.json cannot be decoded as UTF-8 and will be re-created automatically.",
        )
        recreate_and_retry()

    def on_type_error():
        _QMB.warning(
            _MainPage.main_page,
            "memory.json Structure Error",
            "memory.json structure is invalid and will be re-created automatically.",
        )
        recreate_and_retry()

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
