from PySide6.QtWidgets import QPushButton

# ── Palette ──────────────────────────────────────────────────
BG      = "#EAE4D5"
TEXT    = "#5a5549"
BORDER  = "#5a5549"
DANGER  = "#cc3333"
SUCCESS = "#52a852"
MUTED   = "#9a9585"

# ── Shared stylesheet ─────────────────────────────────────────
COMMON_STYLE = f"""
* {{
    background-color: {BG};
    color: {TEXT};
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}}
QLabel {{
    border: none;
    background: transparent;
}}
QLabel#title {{
    font-family: Georgia, "Times New Roman", serif;
    font-size: 38px;
    font-weight: normal;
    background: transparent;
    border: none;
}}
QPushButton {{
    background-color: {BG};
    border: 1.5px solid {BORDER};
    padding: 8px 18px;
    border-radius: 8px;
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: #DDD8C8;
}}
QPushButton[tab_state="active"] {{
    border: 2px solid {BORDER};
    font-weight: 700;
}}
QPushButton[tab_state="inactive"] {{
    border: 1px solid #b0ac9e;
    color: {MUTED};
    font-weight: 500;
}}
QPushButton[tab_state="inactive"]:hover {{
    background-color: #DDD8C8;
    color: {TEXT};
}}
QPushButton#danger {{
    border-color: {DANGER};
    color: {DANGER};
}}
QPushButton#danger:hover {{
    background-color: #f5dede;
}}
QPushButton#success {{
    border-color: {SUCCESS};
    color: {SUCCESS};
}}
QPushButton#success:hover {{
    background-color: #dff0df;
}}
QPushButton#icon_btn {{
    border: none;
    padding: 4px;
    min-width: 28px;
    font-weight: normal;
}}
QPushButton#close_btn {{
    border: none;
    padding: 4px;
    min-width: 28px;
    font-weight: normal;
}}
QPushButton#close_btn:hover {{
    background-color: {DANGER};
    color: white;
}}
QPushButton#help_btn {{
    background-color: #1a1a1a;
    color: white;
    border-radius: 12px;
    border: none;
    font-weight: 700;
    font-size: 12px;
    min-width: 24px;
    max-width: 24px;
    min-height: 24px;
    max-height: 24px;
    padding: 0px;
}}
QComboBox {{
    background-color: {BG};
    border: 1.5px solid {BORDER};
    padding: 8px 16px;
    border-radius: 8px;
    font-weight: 600;
}}
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: right center;
    width: 24px;
    border: none;
}}
QLineEdit {{
    background-color: {BG};
    border: 1.5px solid {BORDER};
    padding: 8px 12px;
    border-radius: 8px;
}}
QTextEdit {{
    background-color: {BG};
    border: 1.5px solid {BORDER};
    padding: 8px;
    border-radius: 8px;
}}
QCheckBox {{
    background: transparent;
    border: none;
    spacing: 6px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1.5px solid {BORDER};
    border-radius: 3px;
    background-color: {BG};
}}
QCheckBox::indicator:checked {{
    background-color: {TEXT};
}}
QFrame#v_divider {{
    background-color: {BORDER};
    max-width: 2px;
    min-width: 2px;
}}
QFrame#h_divider {{
    background-color: {BORDER};
    max-height: 2px;
    min-height: 2px;
}}
"""


def set_tab(active_btn: QPushButton, inactive_btn: QPushButton) -> None:
    """Switch tab button visual states."""
    active_btn.setProperty("tab_state", "active")
    inactive_btn.setProperty("tab_state", "inactive")
    for btn in (active_btn, inactive_btn):
        btn.style().unpolish(btn)
        btn.style().polish(btn)
        btn.update()
