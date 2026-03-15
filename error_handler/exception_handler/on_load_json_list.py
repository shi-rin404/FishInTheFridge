import json, os, sys
import subprocess
from PySide6.QtWidgets import QMessageBox as _QMB


def on_load_json_list(exception: Exception, base_function_name: str):
    from .handler_dispatcher import error_handlers

    json_path = getattr(exception, "_json_path", None)

    def _open_in_editor():
        if not json_path or not os.path.exists(str(json_path)):
            sys.stderr.write(f"[EDITOR] path not found: {json_path!r}\n")
            sys.stderr.flush()
            os._exit(1)

        _path = str(json_path)
        _line = getattr(exception, "lineno", 1)
        _col  = getattr(exception, "colno",  1)

        for cmd in [
            ["code", "--goto", f"{_path}:{_line}:{_col}"],
            ["notepad++", f"-n{_line}", _path],
        ]:
            try:
                sys.stderr.write(f"[EDITOR] trying: {cmd[0]}\n"); sys.stderr.flush()
                subprocess.Popen(cmd)
                sys.stderr.write(f"[EDITOR] launched: {cmd[0]}\n"); sys.stderr.flush()
                os._exit(1)
            except (FileNotFoundError, OSError) as e:
                sys.stderr.write(f"[EDITOR] failed: {e}\n"); sys.stderr.flush()
                continue

        sys.stderr.write("[EDITOR] falling back to os.startfile\n"); sys.stderr.flush()
        os.startfile(_path)
        os._exit(1)

    def on_json_decode_error():
        _QMB.critical(
            None,
            "Invalid JSON File",
            f"A data file contains a JSON syntax error and could not be loaded.\n\n"
            f"{exception}\n\n"
            "Please fix or restore the file and restart the application."
        )
        _open_in_editor()

    def on_file_not_found_error():
        _QMB.critical(
            None,
            "File Not Found",
            f"A required data file is missing:\n\n{json_path or exception}"
        )
        os._exit(1)

    handlers = {
        json.JSONDecodeError: on_json_decode_error,
        FileNotFoundError:    on_file_not_found_error,
    }

    handler = handlers.get(type(exception))
    if handler is not None:
        handler()
    else:
        error_handlers["unknown"](None, exception, base_function_name)
