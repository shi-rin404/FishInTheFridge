import sys
from PySide6.QtWidgets import QApplication
from ui.main_page import MainPage

app = QApplication(sys.argv)
window = MainPage()
window.show()
sys.exit(app.exec())
