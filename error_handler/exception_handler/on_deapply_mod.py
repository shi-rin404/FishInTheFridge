from PySide6.QtWidgets import QMessageBox as _QMB


def on_deapply_mod(exception: Exception, base_function_name: str):
    from .handler_dispatcher import error_handlers
    from ui.main_page import MainPage as _MainPage
    def on_key_error():
        "No addresses found in cache for placeholder"
        _QMB.critical(_MainPage.main_page, "No Addresses Found to Unmod", "No addresses found for the placeholder. The skin you've selected might not be modded properly.")
    
    def on_value_error():
        "WHAT THE FUCK YOU DID IT JUST BEFORE?!"
        _QMB.critical(_MainPage.main_page, "HOW", "HOW A VARIABLE MIGHT BE SHORTER THAN ITSELF")
    
    handlers = {
        KeyError: on_key_error,
        ValueError: on_value_error
    }

    handler = handlers.get(type(exception))
    if handler is not None:
        handler()
    else:
        error_handlers["unknown"](_MainPage.main_page, exception, base_function_name)