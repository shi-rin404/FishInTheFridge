from PySide6.QtWidgets import QApplication
import sys

from . import SettingsPage

app = QApplication(sys.argv)
window = SettingsPage()
window.show()
sys.exit(app.exec())
