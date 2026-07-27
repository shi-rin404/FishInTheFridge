from PySide6.QtWidgets import (
    QWidget, QPushButton, QComboBox, QLabel, QCompleter,
    QHBoxLayout, QVBoxLayout, QSizePolicy, QFrame, QLineEdit
)
from PySide6.QtCore import Qt, QSize, QTimer, QRect, Signal, QPoint, QRegularExpression

from .. import _style
from .._style import SUCCESS, ORANGE
from PySide6.QtGui import (
    QIcon, QPixmap, QCursor, QPainter, QColor, QImage,
    QRegularExpressionValidator, QLinearGradient,
)

from core.variable_manager import program_variables
from modding.ui.load_json_lists import load_json_list
from modding.path_dictionary import preset_dict


class _PresetPopup(QFrame):
    def __init__(self, dropdown_btn: QPushButton):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.Popup | Qt.FramelessWindowHint)
        self._dropdown_btn = dropdown_btn
        self.closed_by_dropdown = False

    def hideEvent(self, event):
        cursor_pos = QCursor.pos()
        tl = self._dropdown_btn.mapToGlobal(self._dropdown_btn.rect().topLeft())
        self.closed_by_dropdown = QRect(tl, self._dropdown_btn.size()).contains(cursor_pos)
        super().hideEvent(event)


class _ColorPickerPopup(QFrame):
    def __init__(self, trigger_btn: QPushButton):
        super().__init__()
        self.setObjectName("color_picker_popup")
        self.setWindowFlags(Qt.WindowType.Popup | Qt.FramelessWindowHint)
        self._trigger_btn = trigger_btn
        self.closed_by_trigger = False

    def hideEvent(self, event):
        cursor_pos = QCursor.pos()
        tl = self._trigger_btn.mapToGlobal(self._trigger_btn.rect().topLeft())
        self.closed_by_trigger = QRect(tl, self._trigger_btn.size()).contains(cursor_pos)
        super().hideEvent(event)


class _HexPickerCanvas(QWidget):
    color_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(240, 240)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self._image = QImage("assets/hex_color_picker.png")
        self._cursor_pixmap = self._load_cursor_pixmap()
        self._cursor_pos = QPoint(self.width() // 2, self.height() // 2)
        self._samples = None

    def _load_cursor_pixmap(self) -> QPixmap:
        pixmap = QPixmap("assets/color_cursor.png")
        image = pixmap.toImage()
        min_x, min_y = image.width(), image.height()
        max_x, max_y = -1, -1
        for y in range(image.height()):
            for x in range(image.width()):
                if image.pixelColor(x, y).alpha() > 0:
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)
        if max_x >= min_x and max_y >= min_y:
            pixmap = pixmap.copy(min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)
        return pixmap.scaled(
            24, 24,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawImage(self.rect(), self._image)
        cursor_rect = QRect(0, 0, 24, 24)
        cursor_rect.moveCenter(self._cursor_pos)
        painter.drawPixmap(cursor_rect, self._cursor_pixmap)
        super().paintEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._select_at(event.position().toPoint())

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._select_at(event.position().toPoint())

    def set_color(self, color: str):
        if not _style.is_hex_color(color) or self._image.isNull():
            return
        target = QColor(color)
        samples = self._color_samples()
        best_x, best_y = 0, 0
        best_distance = None
        for x, y, r, g, b in samples:
            distance = (
                (r - target.red()) ** 2
                + (g - target.green()) ** 2
                + (b - target.blue()) ** 2
            )
            if best_distance is None or distance < best_distance:
                best_distance = distance
                best_x, best_y = x, y
        self._cursor_pos = QPoint(
            round(best_x * (self.width() - 1) / max(1, self._image.width() - 1)),
            round(best_y * (self.height() - 1) / max(1, self._image.height() - 1)),
        )
        self.update()

    def _select_at(self, pos: QPoint):
        if self._image.isNull():
            return
        x = min(max(pos.x(), 0), self.width() - 1)
        y = min(max(pos.y(), 0), self.height() - 1)
        image_x = round(x * (self._image.width() - 1) / max(1, self.width() - 1))
        image_y = round(y * (self._image.height() - 1) / max(1, self.height() - 1))
        color = self._image.pixelColor(image_x, image_y)
        self._cursor_pos = QPoint(x, y)
        self.update()
        self.color_changed.emit(f"#{color.red():02X}{color.green():02X}{color.blue():02X}")

    def _color_samples(self):
        if self._samples is None:
            samples = []
            step = 2
            for y in range(0, self._image.height(), step):
                for x in range(0, self._image.width(), step):
                    color = self._image.pixelColor(x, y)
                    samples.append((x, y, color.red(), color.green(), color.blue()))
            self._samples = samples
        return self._samples


class _BrightnessBar(QWidget):
    value_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(240, 24)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self._cursor_x = 0

    def paintEvent(self, event):
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0.0, QColor("#FFFFFF"))
        gradient.setColorAt(1.0, QColor("#000000"))
        painter.fillRect(self.rect(), gradient)
        painter.setPen(QColor("#5a5549"))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))

        painter.setPen(QColor("#FFFFFF") if self._cursor_value() < 128 else QColor("#000000"))
        painter.drawLine(self._cursor_x, 2, self._cursor_x, self.height() - 3)
        super().paintEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._select_at(event.position().toPoint())

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._select_at(event.position().toPoint())

    def set_value(self, value: int):
        value = min(max(value, 0), 255)
        self._cursor_x = round((255 - value) * (self.width() - 1) / 255)
        self.update()

    def value(self) -> int:
        return self._cursor_value()

    def _select_at(self, pos: QPoint):
        self._cursor_x = min(max(pos.x(), 0), self.width() - 1)
        self.update()
        self.value_changed.emit(self._cursor_value())

    def _cursor_value(self) -> int:
        return round(255 - (self._cursor_x * 255 / max(1, self.width() - 1)))


class BottomRow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Left: preset controls ─────────────────────────────
        from ._apply_panel import _SelectAllFilter

        preset_col = QVBoxLayout()
        preset_col.setSpacing(8)

        preset_row = QHBoxLayout()
        preset_row.setSpacing(8)
        preset_label = QLabel("Active Mod Preset")

        self.preset_combo = QComboBox()
        load_json_list(self.preset_combo, program_variables.presets_path, preset_dict)
        self.preset_combo.setEditable(True)
        self.preset_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.preset_combo.lineEdit().setPlaceholderText("Select Preset" if preset_dict else "No Presets")
        self.preset_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.preset_combo.setMinimumWidth(160)
        QTimer.singleShot(0, lambda: (
            self.preset_combo.setCurrentIndex(-1),
            self.preset_combo.lineEdit().clear()
        ))

        _preset_completer = QCompleter(self.preset_combo.model(), self.preset_combo)
        _preset_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        _preset_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.preset_combo.setCompleter(_preset_completer)
        self.preset_combo.lineEdit().installEventFilter(
            _SelectAllFilter(self.preset_combo, self)
        )
        self.preset_combo.lineEdit().textEdited.connect(
            lambda t: (
                self.preset_combo.completer().setCompletionPrefix(""),
                self.preset_combo.completer().complete()
            ) if not t else None
        )

        [preset_row.addWidget(item) for item in (preset_label, self.preset_combo)]
        preset_row.addStretch()

        self._apply_preset_col_widget = QWidget()
        _apply_preset_split = QHBoxLayout(self._apply_preset_col_widget)
        _apply_preset_split.setSpacing(0)
        _apply_preset_split.setContentsMargins(0, 0, 0, 0)

        self.apply_preset_btn = QPushButton("Apply Preset")
        self.apply_preset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.apply_preset_btn.setMinimumWidth(160)
        self.apply_preset_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.apply_preset_btn.setStyleSheet(
            "QPushButton { border-top-right-radius: 0; border-bottom-right-radius: 0; }"
            "QPushButton:hover { border-top-right-radius: 0; border-bottom-right-radius: 0; }"
        )

        self._apply_preset_dropdown_btn = QPushButton("▼")
        self._apply_preset_dropdown_btn.setFixedWidth(22)
        self._apply_preset_dropdown_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_preset_dropdown_btn.setStyleSheet(
            "QPushButton { border-top-left-radius: 0; border-bottom-left-radius: 0; border-left: none; padding: 8px 4px; }"
            "QPushButton:hover { border-top-left-radius: 0; border-bottom-left-radius: 0; }"
        )

        _apply_preset_split.addWidget(self.apply_preset_btn)
        _apply_preset_split.addWidget(self._apply_preset_dropdown_btn)

        self._apply_preset_popup = _PresetPopup(self._apply_preset_dropdown_btn)
        self._apply_preset_popup.setStyleSheet(_style.COMMON_STYLE)
        _popup_layout = QVBoxLayout(self._apply_preset_popup)
        _popup_layout.setContentsMargins(0, 0, 0, 0)
        _popup_layout.setSpacing(0)
        self.force_apply_preset_btn = QPushButton("Force Apply Preset")
        self.force_apply_preset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.force_apply_preset_btn.setStyleSheet("QPushButton { font-size: 11px; padding: 8px 6px; }")
        _popup_layout.addWidget(self.force_apply_preset_btn)

        self.apply_preset_btn.clicked.connect(self._on_apply_preset)
        self._apply_preset_dropdown_btn.clicked.connect(self._toggle_force_apply_preset)
        self.force_apply_preset_btn.clicked.connect(self._on_force_apply_preset)

        self._preset_feedback_label = QLabel()
        self._preset_feedback_label.hide()
        self._preset_feedback_timer = QTimer(self)
        self._preset_feedback_timer.setSingleShot(True)
        self._preset_feedback_timer.setInterval(5000)
        self._preset_feedback_timer.timeout.connect(self._preset_feedback_label.hide)

        apply_preset_row = QHBoxLayout()
        apply_preset_row.setSpacing(8)
        apply_preset_row.addWidget(self._apply_preset_col_widget)
        apply_preset_row.addWidget(self._preset_feedback_label)
        apply_preset_row.addStretch()

        preset_col.addLayout(preset_row)
        preset_col.addLayout(apply_preset_row)

        layout.addLayout(preset_col)
        layout.addStretch()

        # ── Right: icons + manage combo ───────────────────────
        icons_row = QHBoxLayout()
        icons_row.setSpacing(8)
        icons_row.setAlignment(Qt.AlignRight | Qt.AlignBottom)

        self.color_picker_btn = QPushButton()
        self.color_picker_btn.setIcon(QIcon("assets/color-picker.png"))
        self.color_picker_btn.setIconSize(QSize(32, 32))
        self.color_picker_btn.setFixedSize(32, 32)
        self.color_picker_btn.setToolTip("Background Color")
        self.color_picker_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.color_picker_btn.setStyleSheet(
            "QPushButton { border: none; background: transparent; padding: 0px; }"
        )
        self._build_color_picker_popup()

        tools_btn = QPushButton("🔧")
        tools_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        tools_btn.setObjectName("icon_btn")
        tools_btn.setFixedSize(32, 32)
        tools_btn.setToolTip("Debug Mode")
        tools_btn.clicked.connect(self.on_tools_clicked)

        self.manage_combo = QComboBox()
        self.manage_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.manage_combo.addItems(["Presets", "Mods", "Skins"])
        self.manage_combo.setPlaceholderText("Manage ▲")
        self.manage_combo.setCurrentIndex(-1)
        self.manage_combo.setMinimumWidth(120)
        self.manage_combo.currentIndexChanged.connect(self.manage_combo_dispatch)

        for item in (self.color_picker_btn, tools_btn, self.manage_combo):
            item.setCursor(Qt.CursorShape.PointingHandCursor)
            icons_row.addWidget(item)

        layout.addLayout(icons_row)

    def _build_color_picker_popup(self):
        self._color_picker_popup = _ColorPickerPopup(self.color_picker_btn)
        self._color_picker_popup.setStyleSheet(self._color_picker_popup_style())

        popup_layout = QVBoxLayout(self._color_picker_popup)
        popup_layout.setContentsMargins(8, 8, 8, 8)
        popup_layout.setSpacing(8)

        self.hex_picker = _HexPickerCanvas(self._color_picker_popup)
        popup_layout.addWidget(self.hex_picker)

        self.brightness_bar = _BrightnessBar(self._color_picker_popup)
        popup_layout.addWidget(self.brightness_bar)

        controls_row = QHBoxLayout()
        controls_row.setSpacing(6)

        self.clean_color_btn = QPushButton()
        self.clean_color_btn.setObjectName("clean_color_btn")
        self.clean_color_btn.setFixedSize(32, 32)
        self.clean_color_btn.setToolTip("Clean")
        self.clean_color_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        hex_label = QLabel("HEX: ")
        hash_label = QLabel("#")
        self.hex_input = QLineEdit()
        self.hex_input.setObjectName("hex_input")
        self.hex_input.setMaxLength(7)
        self.hex_input.setFixedWidth(82)
        self.hex_input.setValidator(
            QRegularExpressionValidator(QRegularExpression("^#?[0-9A-Fa-f]{0,6}$"), self.hex_input)
        )

        controls_row.addWidget(self.clean_color_btn)
        controls_row.addSpacing(4)
        controls_row.addWidget(hex_label)
        controls_row.addWidget(hash_label)
        controls_row.addWidget(self.hex_input)
        controls_row.addStretch()
        popup_layout.addLayout(controls_row)

        self._saved_background_color = _style.BG
        self._syncing_from_hex_picker = False
        self._syncing_from_brightness_bar = False
        self._base_picker_color = self._base_color_from_result(_style.BG)
        self._brightness_value = self._brightness_from_result(_style.BG)
        self.hex_input.blockSignals(True)
        self.hex_input.setText(_style.BG.lstrip("#"))
        self.hex_input.blockSignals(False)
        self.hex_picker.set_color(self._base_picker_color)
        self.brightness_bar.set_value(self._brightness_value)
        self._update_clean_icon(_style.BG)

        self.color_picker_btn.clicked.connect(self._toggle_color_picker_popup)
        self.hex_picker.color_changed.connect(self._set_hex_from_picker)
        self.brightness_bar.value_changed.connect(self._set_hex_from_brightness_bar)
        self.hex_input.textChanged.connect(self._on_hex_text_changed)
        self.clean_color_btn.clicked.connect(self._reset_background_color)

    def _color_picker_popup_style(self) -> str:
        return _style.COMMON_STYLE + """
QFrame#color_picker_popup {
    border: 1.5px solid #5a5549;
    border-radius: 8px;
}
QPushButton#clean_color_btn {
    border: none;
    padding: 0px;
    min-width: 32px;
    max-width: 32px;
    min-height: 32px;
    max-height: 32px;
}
QLineEdit#hex_input {
    padding: 6px 8px;
}
"""

    def _toggle_color_picker_popup(self):
        if self._color_picker_popup.closed_by_trigger:
            self._color_picker_popup.closed_by_trigger = False
            return
        self._color_picker_popup.adjustSize()
        button_top_left = self.color_picker_btn.mapToGlobal(
            self.color_picker_btn.rect().topLeft()
        )
        self._color_picker_popup.move(
            button_top_left.x(),
            button_top_left.y() - self._color_picker_popup.height() - 4,
        )
        self._color_picker_popup.show()

    def _set_hex_from_picker(self, color: str):
        self._syncing_from_hex_picker = True
        try:
            self._base_picker_color = color.upper()
            self.hex_input.setText(
                self._blend_base_with_brightness(
                    self._base_picker_color,
                    self._brightness_value,
                ).lstrip("#")
            )
        finally:
            self._syncing_from_hex_picker = False

    def _set_hex_from_brightness_bar(self, value: int):
        self._syncing_from_brightness_bar = True
        try:
            self._brightness_value = value
            self.hex_input.setText(
                self._blend_base_with_brightness(
                    self._base_picker_color,
                    self._brightness_value,
                ).lstrip("#")
            )
        finally:
            self._syncing_from_brightness_bar = False

    def _on_hex_text_changed(self, text: str):
        cleaned = text.strip().lstrip("#").upper()
        if cleaned != text:
            cursor_pos = self.hex_input.cursorPosition()
            self.hex_input.blockSignals(True)
            self.hex_input.setText(cleaned)
            self.hex_input.setCursorPosition(min(cursor_pos, len(cleaned)))
            self.hex_input.blockSignals(False)
        if len(cleaned) != 6:
            return

        color = f"#{cleaned}"
        if _style.is_hex_color(color):
            self._preview_background_color(color)

    def _preview_background_color(self, color: str):
        _style.set_background_color(color)
        self._refresh_common_styles()
        if not self._syncing_from_hex_picker and not self._syncing_from_brightness_bar:
            self._base_picker_color = self._base_color_from_result(color)
            self._brightness_value = self._brightness_from_result(color)
            self.hex_picker.set_color(self._base_picker_color)
            self.brightness_bar.set_value(self._brightness_value)
        self._update_clean_icon(color)
        self._save_background_color(color)

    def _blend_base_with_brightness(self, base_color: str, brightness: int) -> str:
        qcolor = QColor(base_color)
        brightness = min(max(brightness, 0), 255)
        channels = (
            round(qcolor.red() * brightness / 255),
            round(qcolor.green() * brightness / 255),
            round(qcolor.blue() * brightness / 255),
        )
        return "#" + "".join(f"{channel:02X}" for channel in channels)

    def _brightness_from_result(self, color: str) -> int:
        qcolor = QColor(color)
        return max(qcolor.red(), qcolor.green(), qcolor.blue())

    def _base_color_from_result(self, color: str) -> str:
        qcolor = QColor(color)
        brightness = self._brightness_from_result(color)
        if brightness == 0:
            return "#FFFFFF"
        channels = (
            round(qcolor.red() * 255 / brightness),
            round(qcolor.green() * 255 / brightness),
            round(qcolor.blue() * 255 / brightness),
        )
        return "#" + "".join(f"{min(channel, 255):02X}" for channel in channels)

    def _refresh_common_styles(self):
        window = self.window()
        if window is not None:
            window.setStyleSheet(_style.COMMON_STYLE)
            top_row = getattr(window, "top_row", None)
            if top_row is not None and hasattr(top_row, "_install_popup"):
                top_row._install_popup.setStyleSheet(_style.COMMON_STYLE)
            apply_panel = getattr(window, "apply_panel", None)
            if apply_panel is not None and hasattr(apply_panel, "_force_popup"):
                apply_panel._force_popup.setStyleSheet(_style.COMMON_STYLE)
        self._apply_preset_popup.setStyleSheet(_style.COMMON_STYLE)
        self._color_picker_popup.setStyleSheet(self._color_picker_popup_style())

    def _update_clean_icon(self, color: str):
        color = color.lstrip("#")
        r, g, b = (int(color[idx:idx + 2], 16) for idx in range(0, 6, 2))
        luminance = (0.299 * r) + (0.587 * g) + (0.114 * b)
        icon_path = "assets/clean_black.png" if luminance > 140 else "assets/clean_white.png"
        self.clean_color_btn.setIcon(QIcon(icon_path))
        self.clean_color_btn.setIconSize(QSize(28, 28))

    def _save_background_color(self, color: str):
        if color == self._saved_background_color:
            return
        from file_io.output.edit_json import edit_json
        edit_json(str(program_variables.__memory_json__), _style.BG_MEMORY_KEY, color)
        self._saved_background_color = color

    def _reset_background_color(self):
        default_hex = _style.DEFAULT_BG.lstrip("#")
        if self.hex_input.text() == default_hex:
            self._preview_background_color(_style.DEFAULT_BG)
            return
        self.hex_input.setText(default_hex)

    def _set_preset_feedback(self, text: str, *, success: bool = False, error: bool = False):
        color = SUCCESS if success else ("#CC2200" if error else ORANGE)
        self._preset_feedback_label.setText(text)
        self._preset_feedback_label.setStyleSheet(f"color: {color}; font-weight: bold;")
        self._preset_feedback_label.show()
        self._preset_feedback_timer.start()

    def _on_apply_preset(self):
        self._apply_preset(force=False)

    def _on_force_apply_preset(self):
        self._apply_preset_popup.hide()
        self._apply_preset(force=True)

    def _toggle_force_apply_preset(self):
        if self._apply_preset_popup.closed_by_dropdown:
            self._apply_preset_popup.closed_by_dropdown = False
            return
        col_global = self._apply_preset_col_widget.mapToGlobal(
            self._apply_preset_col_widget.rect().bottomLeft()
        )
        self._apply_preset_popup.adjustSize()
        self._apply_preset_popup.setFixedWidth(self._apply_preset_col_widget.width())
        self._apply_preset_popup.move(col_global.x(), col_global.y() + 4)
        self._apply_preset_popup.show()

    def _apply_preset(self, *, force: bool = False):
        from modding.preset_manager import apply_preset
        preset_name = self.preset_combo.currentText().strip()
        if not preset_name:
            return
        self._set_preset_feedback("Searching for skin pathes..")
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()
        try:
            apply_preset(preset_name, force=force)
            message = "Force preset applied successfully" if force else "Preset applied successfully"
            self._set_preset_feedback(message, success=True)
        except Exception:
            self._set_preset_feedback("An error occured upon modding", error=True)
            raise

    def reset_manage_combo(self):
        self.manage_combo.setCurrentIndex(-1)
        self.manage_combo.setPlaceholderText("Manage ▲")

    def manage_combo_dispatch(self):
        def manage_presets():
            from ui import manage_presets_page
            manage_presets_page.ManagePresetsPage(self).show()

        from typing import Literal
        def manage_mod_skin(editor_mode_set=Literal["skin", "mod"]):
            from ui.manage_mod_skin_page import ManageModSkinPage
            from ui.main_page import MainPage
            manage_mod_skin_page = ManageModSkinPage(editor_mode=editor_mode_set, parent=MainPage.main_page)
            manage_mod_skin_page.show()

        def empty_selection():
            pass

        dispatcher = {
            -1: empty_selection,
            0: manage_presets,
            1: lambda: manage_mod_skin("mod"),
            2: lambda: manage_mod_skin("skin")
        }

        dispatcher[self.manage_combo.currentIndex()]()
        self.reset_manage_combo()

    def on_tools_clicked(self):        
        from ui import debug_mode_page

        debug_mode_page.DebugModePage(self).show()
