import json, os, sys
import subprocess
from PySide6.QtWidgets import QMessageBox


def on_update_ms_list(exception: Exception, base_function_name: str):
    from .handler_dispatcher import error_handlers

    json_path     = getattr(exception, "_json_path",     "unknown")
    function_mode = getattr(exception, "_function_mode", "unknown")

    def _open_in_editor():
        sys.stderr.write(f"[DEBUG] json_path={json_path!r} exists={os.path.exists(str(json_path))}\n")
        sys.stderr.flush()

        if os.path.exists(str(json_path)):
            _path = str(json_path)
            _line = getattr(exception, "lineno", 1)
            _col  = getattr(exception, "colno",  1)

            for cmd in [
                ["code", "--goto", f"{_path}:{_line}:{_col}"],
                ["notepad++", f"-n{_line}", _path],
            ]:
                try:
                    subprocess.Popen(cmd)
                    os._exit(1)
                except (FileNotFoundError, OSError) as e:
                    sys.stderr.write(f"[EDITOR] {cmd[0]} failed: {e}\n")
                    sys.stderr.flush()

            # Guaranteed Windows fallback
            os.startfile(_path)

        os._exit(1)

    def on_json_decode_error():
        QMessageBox.critical(
            None,
            f"Failed to load {function_mode} list",
            f"JSON syntax error: {exception}"
            f"\n\nFile: {json_path}"
            f"\n\nThe application will now exit."
        )
        _open_in_editor()

    def on_file_not_found_error():
        QMessageBox.critical(
            None,
            f"Missing {function_mode} list",
            f"Required file not found:\n\n{json_path}"
            f"\n\nThe application will now exit."
        )

    handlers = {
        json.JSONDecodeError: on_json_decode_error,
        FileNotFoundError:    on_file_not_found_error,
    }

    handler = handlers.get(type(exception))
    if handler is not None:
        handler()
    else:
        error_handlers["unknown"](None, exception, base_function_name)
