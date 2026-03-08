from PySide6.QtWidgets import QApplication
import sys

from . import ManageModSkinPage

app = QApplication(sys.argv)
window = ManageModSkinPage()
window.show()
sys.exit(app.exec())
