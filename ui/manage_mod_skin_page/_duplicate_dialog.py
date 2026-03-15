from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QStackedWidget, QWidget
)
from PySide6.QtCore import Qt

from .._style import window_style
from .._widgets import StylePaintMixin


class DuplicateDialog(StylePaintMixin, QDialog):
    """
    Shown when a (skin_name, data_type) pair already exists in the database.

    After exec() == Accepted:
      self.action      → "overwrite" | "rename"
      self.new_name    → final skin name to use
      self.new_dtype   → final data type to use
    """

    def __init__(self, skin_name: str, data_type: str, parent=None):
        super().__init__(parent, Qt.WindowType.Dialog)
        self.setObjectName("duplicate_dialog")
        self.setStyleSheet(window_style("duplicate_dialog", element="QDialog"))
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)

        self.action: str = ""
        self.new_name: str = skin_name
        self.new_dtype: str = data_type

        self._skin_name = skin_name
        self._data_type = data_type

        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(12)

        self._info_label = QLabel(
            f"<b>'{self._data_type}'</b> already exists for <b>'{self._skin_name}'</b>.<br>"
            "What would you like to do?"
        )
        self._info_label.setWordWrap(True)
        root.addWidget(self._info_label)

        self._stack = QStackedWidget()
        root.addWidget(self._stack)

        # ── Page 0: action buttons ────────────────────────────
        action_page = QWidget()
        action_layout = QHBoxLayout(action_page)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(8)

        overwrite_btn = QPushButton("Overwrite")
        overwrite_btn.setObjectName("danger")
        overwrite_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        overwrite_btn.clicked.connect(self._on_overwrite)

        rename_btn = QPushButton("Rename")
        rename_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        rename_btn.clicked.connect(self._show_rename)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)

        action_layout.addWidget(overwrite_btn)
        action_layout.addWidget(rename_btn)
        action_layout.addStretch()
        action_layout.addWidget(cancel_btn)

        self._stack.addWidget(action_page)

        # ── Page 1: rename inputs ─────────────────────────────
        rename_page = QWidget()
        rename_layout = QVBoxLayout(rename_page)
        rename_layout.setContentsMargins(0, 0, 0, 0)
        rename_layout.setSpacing(8)

        rename_layout.addWidget(QLabel("Skin name:"))
        self._name_input = QLineEdit(self._skin_name)
        rename_layout.addWidget(self._name_input)

        rename_layout.addWidget(QLabel("Data type:"))
        self._dtype_input = QLineEdit(self._data_type)
        rename_layout.addWidget(self._dtype_input)

        confirm_row = QHBoxLayout()
        confirm_row.addStretch()

        back_btn = QPushButton("Back")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(lambda: self._stack.setCurrentIndex(0))

        confirm_btn = QPushButton("Confirm")
        confirm_btn.setObjectName("success")
        confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        confirm_btn.clicked.connect(self._on_confirm_rename)

        confirm_row.addWidget(back_btn)
        confirm_row.addWidget(confirm_btn)
        rename_layout.addLayout(confirm_row)

        self._stack.addWidget(rename_page)

    def _on_overwrite(self):
        self.action = "overwrite"
        self.new_name = self._skin_name
        self.new_dtype = self._data_type
        self.accept()

    def _show_rename(self):
        self._stack.setCurrentIndex(1)
        self.adjustSize()

    def _on_confirm_rename(self):
        name = self._name_input.text().strip()
        dtype = self._dtype_input.text().strip()
        if not name or not dtype:
            return
        self.action = "rename"
        self.new_name = name
        self.new_dtype = dtype
        self.accept()
