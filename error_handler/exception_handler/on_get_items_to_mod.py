from PySide6.QtWidgets import QMessageBox as _QMB

def on_get_items_to_mod(exception: Exception, _function_name: str):
    from ui.main_page import MainPage as _MainPage
    def on_key_error():
        "skin_dict or mod_dict lookup failed — selected combo item has no matching path entry"
        _QMB.critical(_MainPage.main_page, "Unknown Selection", f"The selected item was not found in the database.\nCalled from: {_function_name}\nKey: {exception}")
        
    def on_unknown():
            "Unrecognised exception — re-raise so it is not silently swallowed"
            _QMB.critical(_MainPage.main_page, "Unexpected Error", f"An unexpected error occurred in {_function_name}:\n{type(exception).__name__}: {exception}")


    handlers = {
            KeyError: on_key_error,
    }
    
    handlers.get(type(exception), on_unknown)()