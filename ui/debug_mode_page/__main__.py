from PySide6.QtWidgets import QApplication
import sys

from . import DebugModePage

app = QApplication(sys.argv)
window = DebugModePage()
window.show()
sys.exit(app.exec())
