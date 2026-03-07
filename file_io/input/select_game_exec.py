from PySide6.QtWidgets import QFileDialog

from ui.main_page import MainPage

def select_game_exec() -> str | None:    
    path, _ = QFileDialog.getOpenFileName(
        MainPage.main_page,
        "Select Game Executable",
        "",
        "dwrg.exe (dwrg.exe)",
    )
    if path and path.endswith("dwrg.exe"):
        return path
    return None
