from typing import Callable, Any, Iterable

from error_handler.exception_handler.handler_dispatcher import error_handlers

def ensure_exception(func: Callable, args: Iterable[Any]):
    try:
        return func(*args)
    except Exception as e:
        try:
            error_handlers[func.__name__](e, func.__name__)
        except KeyError:
            from PySide6.QtWidgets import QMessageBox as _QMB
            _QMB.critical(None, "ensure_exception", f"Unhandled error on {func.__name__} due to the function name is not exist in error_handler.exception_handler.handler_dispatcher.error_handlers:\n{type(e).__name__}: {e}")