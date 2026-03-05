from PySide6.QtWidgets import QFrame, QPushButton, QComboBox, QVBoxLayout, QHBoxLayout


class ApplyPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sub_panel")
        self.setStyleSheet(
            "QFrame#sub_panel { border: 1.5px solid #5a5549; border-radius: 8px; }"
        )
        self.setFixedWidth(260)
        self._build()
        self.hide()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        _combo_style = "QComboBox { padding: 6px 16px; }"

        self.skin_combo = QComboBox()
        self.skin_combo.addItem("Select Skin  ▼")
        self.skin_combo.setMinimumWidth(200)
        self.skin_combo.setStyleSheet(_combo_style)

        self.mod_combo = QComboBox()
        self.mod_combo.addItem("Select Mod  ▼")
        self.mod_combo.setMinimumWidth(200)
        self.mod_combo.setStyleSheet(_combo_style)

        action_row = QHBoxLayout()
        action_row.setSpacing(8)
        self.unmod_btn = QPushButton("Unmod")
        self.unmod_btn.setObjectName("danger")
        self.action_apply_btn = QPushButton("Apply")
        action_row.addWidget(self.unmod_btn)
        action_row.addStretch()
        action_row.addWidget(self.action_apply_btn)

        layout.addWidget(self.skin_combo)
        layout.addWidget(self.mod_combo)
        layout.addLayout(action_row)

    def toggle(self):
        self.setVisible(not self.isVisible())
