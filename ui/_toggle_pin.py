import os

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Signal, Property, QPropertyAnimation, QEasingCurve, QRect, QRectF
from PySide6.QtGui import QPainter, QColor, QPixmap

_PIN_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "pin.png")

_GRAY = QColor("#9a9585")
_BLUE = QColor("#689fda")
_PAD  = 3
_W, _H = 60, 30


def _lerp_color(a: QColor, b: QColor, t: float) -> QColor:
    return QColor(
        int(a.red()   + t * (b.red()   - a.red())),
        int(a.green() + t * (b.green() - a.green())),
        int(a.blue()  + t * (b.blue()  - a.blue())),
    )


class TogglePin(QWidget):
    """
    Animated toggle with a pin icon that is revealed as the circle slides right.

    Signals
    -------
    toggled(bool)  — emitted on every click with the new checked state.
    """

    toggled = Signal(bool)

    def __init__(self, _checked:bool = False, parent=None):
        super().__init__(parent)
        self._checked = _checked
        self.__pos: float = 1.0 if _checked else 0.0
        self._pin = QPixmap(_PIN_PATH)
        self.setFixedSize(_W, _H)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._anim = QPropertyAnimation(self, b"anim_pos", self)
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

    # ── Animated property ──────────────────────────────────────
    def _get_pos(self) -> float:
        return self.__pos

    def _set_pos(self, value: float):
        self.__pos = value
        self.update()

    anim_pos = Property(float, _get_pos, _set_pos)

    # ── Public ─────────────────────────────────────────────────
    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, state: bool):
        if state == self._checked:
            return
        self._checked = state
        self._anim.stop()
        self._anim.setStartValue(self.__pos)
        self._anim.setEndValue(1.0 if state else 0.0)
        self._anim.start()

    # ── Interaction ────────────────────────────────────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._checked = not self._checked
            self._anim.stop()
            self._anim.setStartValue(self.__pos)
            self._anim.setEndValue(1.0 if self._checked else 0.0)
            self._anim.start()
            self.toggled.emit(self._checked)

    # ── Painting ───────────────────────────────────────────────
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        w, h = self.width(), self.height()
        t    = self.__pos
        d    = h - 2 * _PAD          # circle diameter
        r    = h / 2                 # pill corner radius

        # Background pill
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(_lerp_color(_GRAY, _BLUE, t))
        p.drawRoundedRect(0, 0, w, h, r, r)

        # Circle x position (slides from left to right)
        circle_x = _PAD + t * (w - 2 * _PAD - d)

        # Pin image clipped to everything left of the circle's left edge
        if t > 0 and not self._pin.isNull():
            clip_w = int(circle_x - _PAD)
            if clip_w > 0:
                p.save()
                p.setClipRect(QRect(_PAD, _PAD, clip_w, d))
                p.drawPixmap(QRect(_PAD, _PAD, d, d), self._pin, self._pin.rect())
                p.restore()

        # White circle (drawn on top so it masks whatever is underneath)
        p.setBrush(QColor("white"))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(circle_x, _PAD, d, d))

        p.end()
