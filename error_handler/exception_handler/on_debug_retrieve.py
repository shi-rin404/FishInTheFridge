from PySide6.QtWidgets import QMessageBox as _QMB


def on_debug_retrieve(exception: Exception, base_function_name: str):
    from .handler_dispatcher import error_handlers
    from ui.debug_mode_page import DebugModePage as _Page

    def on_runtime_error():
        _QMB.critical(_Page.debug_mode_page, "Game Not Running",
                      "The game doesn't appear to be running.\nPlease launch the game first, then try again.")

    def on_permission_error():
        _QMB.critical(_Page.debug_mode_page, "Permission Denied",
                      "This app needs administrator rights.\nPlease restart it as administrator and try again.")

    handlers = {
        RuntimeError:    on_runtime_error,
        PermissionError: on_permission_error,
    }

    handler = handlers.get(type(exception))
    if handler is not None:
        handler()
    else:
        error_handlers["unknown"](_Page.debug_mode_page, exception, base_function_name)
