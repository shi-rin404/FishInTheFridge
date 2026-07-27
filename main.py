import sys
import traceback
from PySide6.QtWidgets import QApplication


def _exception_hook(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    from error_handler.exception_handler.handler_dispatcher import error_handlers

    frames = traceback.extract_tb(exc_traceback)
    func_name = next(
        (f.name for f in frames if f.name in error_handlers),
        None
    )

    if func_name:
        error_handlers[func_name](exc_value, func_name)
    else:
        error_handlers["unknown"](None, exc_value, frames[-1].name if frames else "unknown")


sys.excepthook = _exception_hook

app = QApplication(sys.argv)

from ui.main_page import MainPage
from modding.get_mods import get_mods

get_mods()
window = MainPage()
window.show()
sys.exit(app.exec())