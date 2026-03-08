from PySide6.QtWidgets import QFileDialog
import base64

def select_game_exec() -> str | None:    
    from ui.main_page import MainPage
    path, _ = QFileDialog.getOpenFileName(
        MainPage.main_page,
        "Select Game Executable",
        "",
        base64.decodebytes(b"ZHdyZy5leGUgKGR3cmcuZXhlKQ==").decode(),
    )
    if path and path.endswith(base64.decodebytes(b"ZHdyZy5leGU=").decode()):
        return path
    return None