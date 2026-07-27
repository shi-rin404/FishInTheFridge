import shutil
from pathlib import Path

from PySide6.QtCore import QPoint, Qt, QRect, QSize
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QLabel, QSlider, QWidget

from core.options_memory import read_memory, set_memory_value
from core.variable_manager import program_variables
from ui import _style


CUSTOM_BG_STEM = "custom_bg_image"
SUPPORTED_EXTS = {"png", "jpg", "jpeg"}
DEFAULT_OPACITY = 1.0


def custom_background_path() -> Path | None:
    memory = read_memory()
    if not memory.get("custom_bg"):
        return None
    ext = str(memory.get("custom_bg_ext") or "").lower().lstrip(".")
    if ext not in SUPPORTED_EXTS:
        return None
    path = Path(program_variables.__memory_json__).parent / f"{CUSTOM_BG_STEM}.{ext}"
    return path if path.exists() else None


def custom_background_opacity() -> float:
    value = read_memory().get("custom_bg_oppacity")
    if value is None:
        return DEFAULT_OPACITY
    try:
        return min(1.0, max(0.0, float(value)))
    except (TypeError, ValueError):
        return DEFAULT_OPACITY


def clear_custom_background() -> None:
    user_dir = Path(program_variables.__memory_json__).parent
    for ext in SUPPORTED_EXTS:
        path = user_dir / f"{CUSTOM_BG_STEM}.{ext}"
        if path.exists():
            path.unlink()
    set_memory_value("custom_bg", False)
    set_memory_value("custom_bg_ext", None)
    set_memory_value("custom_bg_oppacity", None)


class BackgroundImageEditor(QWidget):
    def __init__(self, main_page):
        super().__init__(main_page)
        self.main_page = main_page
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.hide()
        self.source_path: Path | None = None
        self.source_pixmap = QPixmap()
        self.scale = 1.0
        self.opacity = DEFAULT_OPACITY
        self.offset = QPoint()
        self._drag_start: QPoint | None = None
        self._drag_origin = QPoint()

        self.instruction_label = QLabel("Move/scale the Image", self)
        self.instruction_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.instruction_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.instruction_label.setStyleSheet(self._instruction_style())
        self.instruction_label.setFixedSize(190, 42)

        self.opacity_slider = QSlider(Qt.Orientation.Vertical, self)
        self.opacity_slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.setFixedSize(36, 170)
        self.opacity_slider.setToolTip("Background Image Opacity")
        self.opacity_slider.valueChanged.connect(self._set_opacity_from_slider)

    def _instruction_style(self) -> str:
        bg = QColor(_style.BG)
        return (
            "QLabel {"
            f"background-color: rgba({bg.red()}, {bg.green()}, {bg.blue()}, 166);"
            "border: 1px solid rgba(90, 85, 73, 166);"
            "border-radius: 8px;"
            "font-weight: 700;"
            "}"
        )

    def begin(self, path: str) -> bool:
        pixmap = QPixmap(path)
        if pixmap.isNull():
            return False
        self.source_path = Path(path)
        self.source_pixmap = pixmap
        self.scale = 1.0
        self.opacity = custom_background_opacity()
        self.opacity_slider.blockSignals(True)
        self.opacity_slider.setValue(round(self.opacity * 100))
        self.opacity_slider.blockSignals(False)
        self.offset = QPoint(
            (self.main_page.width() - pixmap.width()) // 2,
            (self.main_page.height() - pixmap.height()) // 2,
        )
        self.setGeometry(self.main_page.rect())
        self.instruction_label.setStyleSheet(self._instruction_style())
        self._position_controls()
        self.show()
        self.raise_()
        self.update()
        return True

    def resizeEvent(self, event):
        self.setGeometry(self.main_page.rect())
        self._position_controls()
        super().resizeEvent(event)

    def _position_controls(self):
        self.instruction_label.move(
            (self.width() - self.instruction_label.width()) // 2,
            (self.height() - self.instruction_label.height()) // 2,
        )
        self.opacity_slider.move(
            self.width() - self.opacity_slider.width() - 16,
            (self.height() - self.opacity_slider.height()) // 2,
        )

    def _set_opacity_from_slider(self, value: int):
        self.opacity = min(1.0, max(0.0, value / 100))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 1))
        self._draw_image(painter, self.rect(), opacity=self.opacity)
        super().paintEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.position().toPoint()
            self._drag_origin = QPoint(self.offset)

    def mouseMoveEvent(self, event):
        if self._drag_start is None:
            return
        delta = event.position().toPoint() - self._drag_start
        self.offset = self._drag_origin + delta
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = None

    def wheelEvent(self, event):
        if self.source_pixmap.isNull():
            return
        old_scale = self.scale
        delta = event.angleDelta().y() or event.pixelDelta().y()
        if delta == 0:
            return
        self.scale = min(1.0, max(0.0, self.scale + (delta / 1200)))
        if old_scale == self.scale:
            return

        cursor = event.position().toPoint()
        if old_scale > 0:
            image_x = (cursor.x() - self.offset.x()) / old_scale
            image_y = (cursor.y() - self.offset.y()) / old_scale
            self.offset = QPoint(
                round(cursor.x() - image_x * self.scale),
                round(cursor.y() - image_y * self.scale),
            )
        self.update()

    def _draw_image(self, painter: QPainter, target_rect: QRect, *, opacity: float | None = None) -> None:
        if self.source_pixmap.isNull() or self.scale <= 0:
            return
        scaled_size = QSize(
            round(self.source_pixmap.width() * self.scale),
            round(self.source_pixmap.height() * self.scale),
        )
        if scaled_size.width() <= 0 or scaled_size.height() <= 0:
            return
        scaled = self.source_pixmap.scaled(
            scaled_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        painter.save()
        painter.setOpacity(self.opacity if opacity is None else opacity)
        painter.drawPixmap(self.offset, scaled)
        painter.restore()

    def render_to_file(self) -> Path:
        if self.source_path is None or self.source_pixmap.isNull():
            raise RuntimeError("No background image selected.")
        ext = self.source_path.suffix.lower().lstrip(".")
        if ext not in SUPPORTED_EXTS:
            ext = "png"

        user_dir = Path(program_variables.__memory_json__).parent
        user_dir.mkdir(parents=True, exist_ok=True)
        clear_custom_background()
        output_path = user_dir / f"{CUSTOM_BG_STEM}.{ext}"

        result = QPixmap(self.main_page.size())
        result.fill(QColor(_style.BG))
        painter = QPainter(result)
        self._draw_image(painter, QRect(QPoint(0, 0), self.main_page.size()), opacity=1.0)
        painter.end()

        if not result.save(str(output_path)):
            shutil.copy2(self.source_path, output_path)

        set_memory_value("custom_bg", True)
        set_memory_value("custom_bg_ext", ext)
        set_memory_value("custom_bg_oppacity", self.opacity)
        self.hide()
        return output_path
