from PySide6.QtWidgets import QMessageBox as _QMB

def on_get_items_to_mod(exception: Exception, _function_name: str, base_function_name: str):
    from .handler_dispatcher import error_handlers
    from ui.main_page import MainPage as _MainPage
    def on_key_error():
        "skin_dict or mod_dict lookup failed — selected combo item has no matching path entry"
        _QMB.critical(_MainPage.main_page, "Unknown Selection", f"The selected item was not found in the database.\nCalled from: {_function_name}\nKey: {exception}")

    handlers = {
            KeyError: on_key_error,
    }
    
    handler = handlers.get(type(exception))
    if handler is not None:
        handler()
    else:
        error_handlers["unknown"](_MainPage.main_page, exception, base_function_name)