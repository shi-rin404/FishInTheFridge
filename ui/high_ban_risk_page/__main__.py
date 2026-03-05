from PySide6.QtWidgets import QApplication
import sys

from . import HighBanRiskPage

app = QApplication(sys.argv)
window = HighBanRiskPage()
window.show()
sys.exit(app.exec())
