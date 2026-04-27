import sys
import traceback
from PySide6.QtWidgets import QApplication
from ui.dispatch_page import DispatchPage
from error_handler.exception_handler.handler_dispatcher import error_handlers


def _exception_hook(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

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

DEBUG = True  # set False before building

app = QApplication(sys.argv)
window = DispatchPage(debug=DEBUG)
window.show()
sys.exit(app.exec())
