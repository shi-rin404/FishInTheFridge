import json

from PySide6.QtWidgets import QMessageBox as _QMB

def on_get_game_executable(exception: Exception, base_function_name: str):
    from .handler_dispatcher import error_handlers
    from ui.main_page import MainPage as _MainPage
    from core.variable_manager import program_variables

    def develop_memory_json():
        with open(program_variables.__memory_json__, 'w') as f:
            json.dump({
                "game_executable": None
                }, f)   
        
        from database.user.user_variables import user_variables
        user_variables.set_game_executable()

    def on_json_error():        
        _QMB.critical(_MainPage.main_page, f"Invalid JSON [{type(exception).__name__}]", f"{program_variables.__memory_json__} is not a valid JSON file")

    def on_permission_error():
        _QMB.critical(_MainPage.main_page, "Permission Denied", f"It is not able to read {program_variables.__memory_json__} . Check your permissions.")

    def on_file_not_found_error():
        _QMB.critical(_MainPage.main_page, "memory.json is Lost", "It might caused by your Miyou Loader is damaged. The file will be created automatically. But keep it in your mind.")
             
        develop_memory_json()

    def on_key_error():
        _QMB.critical(_MainPage.main_page, "memory.json is Damaged", "It might caused by your Miyou Loader is damaged. The file will be re-created automatically. But keep it in your mind.")

        develop_memory_json()

    def on_unicode_decode_error():
        _QMB.critical(_MainPage.main_page, "memory.json is Encoded Wrong", "It might caused by your Miyou Loader is damaged. The file will be re-created automatically. But keep it in your mind.")

        develop_memory_json()

    handlers = {
        json.JSONDecodeError: on_json_error,
        PermissionError:      on_permission_error,
        FileNotFoundError:    on_file_not_found_error,
        KeyError:             on_key_error,
        UnicodeDecodeError:   on_unicode_decode_error
    }

    handler = handlers.get(type(exception))
    if handler is not None:
        handler()
    else:
        error_handlers["unknown"](_MainPage.main_page, exception, base_function_name)