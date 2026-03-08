from PySide6.QtWidgets import QFileDialog

from ui.main_page import MainPage

def select_mod_zip() -> str | None:
    path, _ = QFileDialog.getOpenFileName(
        MainPage.main_page,
        "Select Mod ZIP",
        "",
        "ZIP Files (*.zip)",
    )
    if path and path.endswith(".zip"):
        return path
    return None
