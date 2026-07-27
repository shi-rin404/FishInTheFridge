from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton
)
from PySide6.QtCore import Qt

from .._style import window_style
from .._widgets import StylePaintMixin

_TYPES = ["skin", "item", "accessory", "other"]


class SelectDataTypeDialog(StylePaintMixin, QDialog):
    """
    Modal popup to pick a data type.

    Usage
    -----
    dlg = SelectDataTypeDialog(parent=self)
    if dlg.exec() == QDialog.DialogCode.Accepted:
        data_type = dlg.result_type   # str
    """

    def __init__(self, parent=None, initial_type: str = ""):
        super().__init__(parent, Qt.WindowType.Dialog)
        self.setObjectName("select_data_type_dialog")
        self.setStyleSheet(window_style("select_data_type_dialog", element="QDialog"))
        self.setWindowTitle("Select Data Type")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.result_type: str = ""
        self._initial_type = initial_type
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        layout.addWidget(QLabel("Data type:"))

        self.combo = QComboBox()
        self.combo.addItems(_TYPES)
        if self._initial_type in _TYPES:
            self.combo.setCurrentText(self._initial_type)
        self.combo.currentTextChanged.connect(self._on_type_changed)
        layout.addWidget(self.combo)

        self.custom_input = QLineEdit()
        self.custom_input.setPlaceholderText("Enter custom data type…")
        self.custom_input.hide()
        layout.addWidget(self.custom_input)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        select_btn = QPushButton("Select")
        select_btn.setObjectName("success")
        select_btn.clicked.connect(self._on_select)
        btn_row.addWidget(select_btn)
        layout.addLayout(btn_row)

    def _on_type_changed(self, text: str):
        self.custom_input.setVisible(text == "other")
        self.adjustSize()

    def _on_select(self):
        if self.combo.currentText() == "other":
            self.result_type = self.custom_input.text().strip() or "other"
        else:
            self.result_type = self.combo.currentText()
        self.accept()
