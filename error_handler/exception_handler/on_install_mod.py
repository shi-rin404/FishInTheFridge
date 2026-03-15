import zipfile
from PySide6.QtWidgets import QMessageBox as _QMB

def on_install_mod(exception: Exception, base_function_name: str):
    from .handler_dispatcher import error_handlers
    from ui.main_page import MainPage as _MainPage

    def on_permission_error():
        _QMB.critical(_MainPage.main_page, "Permission Denied",
            "This app doesn't have permission to write to the mod directory.\nPlease restart it as administrator and try again.")

    def on_file_not_found_error():
        """The mod directory doesn't exist."""
        from os import mkdir
        from database.user.user_variables import user_variables
        
        mkdir(user_variables.mod_dir)
        _QMB.information(_MainPage.main_page, "Mod Directory Created Automaticly", "Please re-select your mod")
                    
        from modding.install_mod import install_mod
        try:
            install_mod()
        except Exception:
            pass

    def on_bad_zip_file():
        _QMB.critical(_MainPage.main_page, "Invalid ZIP",
            "The selected file is not a valid ZIP archive or is corrupted.")

    handlers = {
        PermissionError:    on_permission_error,
        FileNotFoundError:  on_file_not_found_error,
        zipfile.BadZipFile: on_bad_zip_file,
    }

    handler = handlers.get(type(exception))
    if handler is not None:
        handler()
    else:
        error_handlers["unknown"](_MainPage.main_page, exception, base_function_name)