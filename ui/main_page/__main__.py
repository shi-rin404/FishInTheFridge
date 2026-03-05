from PySide6.QtWidgets import QApplication
import sys

from . import MainPage

app = QApplication(sys.argv)
window = MainPage()
window.show()
sys.exit(app.exec())
