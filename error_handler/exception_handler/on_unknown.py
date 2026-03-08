from PySide6.QtWidgets import QMessageBox as _QMB, QWidget

def on_unknown(window: QWidget, exception: Exception, base_function_name: str):
    "Unrecognised exception — re-raise so it is not silently swallowed"
    _QMB.critical(window, f"Unexpected Error [{base_function_name}]", f"Something went wrong while running {base_function_name}.\n\n{type(exception).__name__}: {exception}")
