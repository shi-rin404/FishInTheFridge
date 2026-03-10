import sys
from PySide6.QtWidgets import QApplication
from ui.main_page import MainPage

app = QApplication(sys.argv)
window = MainPage()

from modding.get_mods import get_mods
get_mods()

window.show()
sys.exit(app.exec())
