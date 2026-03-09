from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton
)
from PySide6.QtCore import Qt

from .._style import COMMON_STYLE

_TYPES = ["skin", "item", "accessory", "other"]


class SelectDataTypeDialog(QDialog):
    """
    Modal popup to pick a data type.

    Usage
    -----
    dlg = SelectDataTypeDialog(parent=self)
    if dlg.exec() == QDialog.DialogCode.Accepted:
        data_type = dlg.result_type   # str
    """

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Dialog)
        self.setStyleSheet(COMMON_STYLE)
        self.setWindowTitle("Select Data Type")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.result_type: str = ""
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        layout.addWidget(QLabel("Data type:"))

        self.combo = QComboBox()
        self.combo.addItems(_TYPES)
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