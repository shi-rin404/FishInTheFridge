import json
import re

from PySide6.QtWidgets import QPushButton

from core.variable_manager import program_variables

DEFAULT_BG = "#EAE4D5"
BG_MEMORY_KEY = "background_color"
_HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")

_ORIGINAL_BG = "#EAE4D5"
_ORIGINAL_TEXT = "#5a5549"
_ORIGINAL_BORDER = "#5a5549"
_ORIGINAL_MUTED = "#9a9585"


def is_hex_color(value: str) -> bool:
    return bool(_HEX_COLOR_RE.match(value or ""))


def _load_background_color() -> str:
    try:
        with open(program_variables.__memory_json__, "r", encoding="utf-8") as f:
            value = json.load(f).get(BG_MEMORY_KEY)
    except (OSError, json.JSONDecodeError, TypeError):
        return DEFAULT_BG
    return value.upper() if is_hex_color(value) else DEFAULT_BG


def _blend_hex(color: str, target: str, amount: float) -> str:
    color = color.lstrip("#")
    target = target.lstrip("#")
    mixed = []
    for idx in range(0, 6, 2):
        base = int(color[idx:idx + 2], 16)
        end = int(target[idx:idx + 2], 16)
        mixed.append(round(base + (end - base) * amount))
    return "#" + "".join(f"{channel:02X}" for channel in mixed)


def _hex_channels(color: str) -> tuple[int, int, int]:
    color = color.lstrip("#")
    return tuple(int(color[idx:idx + 2], 16) for idx in range(0, 6, 2))


def _format_channels(channels: tuple[int, int, int]) -> str:
    return "#" + "".join(f"{channel % 256:02X}" for channel in channels)


def _apply_original_delta(new_bg: str, original_color: str) -> str:
    bg_channels = _hex_channels(new_bg)
    original_bg_channels = _hex_channels(_ORIGINAL_BG)
    original_channels = _hex_channels(original_color)
    return _format_channels(tuple(
        bg + (original - original_bg)
        for bg, original, original_bg in zip(
            bg_channels,
            original_channels,
            original_bg_channels,
        )
    ))


def _luminance(color: str) -> float:
    color = color.lstrip("#")
    r, g, b = (int(color[idx:idx + 2], 16) for idx in range(0, 6, 2))
    return (0.299 * r) + (0.587 * g) + (0.114 * b)


# Palette
BG      = _load_background_color()
TEXT    = _apply_original_delta(BG, _ORIGINAL_TEXT)
BORDER  = _apply_original_delta(BG, _ORIGINAL_BORDER)
DANGER   = "#cc3333"
SUCCESS  = "#52a852"
WARNING  = "#eddd66"
MUTED    = _apply_original_delta(BG, _ORIGINAL_MUTED)
ORANGE   = "#C47A00"


def _sync_palette_to_background() -> None:
    global TEXT, BORDER, MUTED
    TEXT = _apply_original_delta(BG, _ORIGINAL_TEXT)
    BORDER = _apply_original_delta(BG, _ORIGINAL_BORDER)
    MUTED = _apply_original_delta(BG, _ORIGINAL_MUTED)


def _build_common_style() -> str:
    hover_bg = _blend_hex(BG, "#FFFFFF" if _luminance(BG) < 128 else "#000000", 0.12)
    return f"""
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
    background-color: {hover_bg};
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
    background-color: {hover_bg};
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
QPushButton#warning {{
    border-color: {WARNING};
    color: {WARNING};
}}
QPushButton#warning:hover {{
    background-color: #faf8dc;
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


COMMON_STYLE = _build_common_style()


def set_background_color(color: str) -> str:
    global BG, COMMON_STYLE
    if not is_hex_color(color):
        raise ValueError(f"Invalid hex color: {color}")
    BG = color.upper()
    _sync_palette_to_background()
    COMMON_STYLE = _build_common_style()
    return BG


def window_style(object_name: str, *, element: str = "QWidget") -> str:
    """Returns COMMON_STYLE + a 1px black outer border for a frameless window."""
    return COMMON_STYLE + f"{element}#{object_name} {{ border: 1px solid black; }}"


def set_tab(active_btn: QPushButton, inactive_btn: QPushButton) -> None:
    """Switch tab button visual states."""
    active_btn.setProperty("tab_state", "active")
    inactive_btn.setProperty("tab_state", "inactive")
    for btn in (active_btn, inactive_btn):
        btn.style().unpolish(btn)
        btn.style().polish(btn)
        btn.update()
