from PySide6.QtWidgets import QFileDialog

from ...ui.main_page.MainPage import main_page

def select_game_exec() -> str | None:
    path, _ = QFileDialog.getOpenFileName(
        main_page,
        "Select Game Executable",
        "",
        "dwrg.exe (dwrg.exe)",
    )
    if path and path.endswith("dwrg.exe"):
        return path
    return None
