"""Reusable compass and artificial-horizon widgets."""

from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QPolygonF
from PySide6.QtWidgets import QSizePolicy, QWidget

BACKGROUND = QColor("#0d1724")
RING = QColor("#7f8fa6")
TEXT = QColor("#e6edf3")
ACCENT = QColor("#f0c674")
SKY = QColor("#2878b5")
GROUND = QColor("#8b572a")


class CompassWidget(QWidget):
    """A heading card with a fixed top lubber mark."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.heading_degrees: float | None = None
        self.setMinimumSize(150, 150)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_heading(self, heading_degrees: float | None) -> None:
        self.heading_degrees = None if heading_degrees is None else (float(heading_degrees) + 180.0) % 360.0 - 180.0
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        diameter = max(20.0, min(self.width(), self.height()) - 12.0)
        circle = QRectF((self.width() - diameter) / 2, (self.height() - diameter) / 2, diameter, diameter)
        centre = circle.center()
        radius = diameter / 2
        painter.setPen(QPen(RING, 2))
        painter.setBrush(BACKGROUND)
        painter.drawEllipse(circle)

        if self.heading_degrees is None:
            painter.setPen(TEXT)
            painter.drawText(circle, Qt.AlignmentFlag.AlignCenter, "—")
            return

        painter.save()
        painter.translate(centre)
        painter.rotate(-self.heading_degrees)
        for bearing in range(0, 360, 10):
            painter.save()
            painter.rotate(bearing)
            length = 12.0 if bearing % 30 == 0 else 6.0
            painter.setPen(QPen(TEXT, 2 if bearing % 30 == 0 else 1))
            painter.drawLine(QPointF(0, -radius + 5), QPointF(0, -radius + 5 + length))
            painter.restore()
        painter.setPen(TEXT)
        font = QFont(painter.font())
        font.setBold(True)
        painter.setFont(font)
        for label, bearing in (("N", 0), ("E", 90), ("S", 180), ("W", 270)):
            angle = math.radians(bearing - 90)
            point = QPointF(math.cos(angle) * (radius - 28), math.sin(angle) * (radius - 28))
            painter.drawText(QRectF(point.x() - 10, point.y() - 9, 20, 18), Qt.AlignmentFlag.AlignCenter, label)
        painter.restore()

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(ACCENT)
        painter.drawPolygon(
            QPolygonF(
                (
                    QPointF(centre.x(), circle.top() + 3),
                    QPointF(centre.x() - 6, circle.top() + 16),
                    QPointF(centre.x() + 6, circle.top() + 16),
                )
            )
        )
        painter.setPen(TEXT)
        painter.drawText(
            QRectF(circle.left(), centre.y() - 11, diameter, 22),
            Qt.AlignmentFlag.AlignCenter,
            f"{self.heading_degrees:.0f}°",
        )


class ArtificialHorizonWidget(QWidget):
    """Bank and pitch presentation modelled after an aircraft attitude indicator."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.roll_degrees: float | None = None
        self.pitch_degrees: float | None = None
        self.setMinimumSize(150, 150)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_attitude(self, roll_degrees: float | None, pitch_degrees: float | None) -> None:
        self.roll_degrees = roll_degrees
        self.pitch_degrees = pitch_degrees
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        diameter = max(20.0, min(self.width(), self.height()) - 12.0)
        circle = QRectF((self.width() - diameter) / 2, (self.height() - diameter) / 2, diameter, diameter)
        centre = circle.center()
        painter.setPen(QPen(RING, 2))
        painter.setBrush(BACKGROUND)
        painter.drawEllipse(circle)
        if self.roll_degrees is None or self.pitch_degrees is None:
            painter.setPen(TEXT)
            painter.drawText(circle, Qt.AlignmentFlag.AlignCenter, "—")
            return

        clip = QPainterPath()
        clip.addEllipse(circle.adjusted(3, 3, -3, -3))
        painter.save()
        painter.setClipPath(clip)
        painter.translate(centre)
        painter.rotate(-self.roll_degrees)
        pitch_offset = max(-diameter, min(diameter, self.pitch_degrees * diameter / 90.0))
        painter.fillRect(QRectF(-diameter, -diameter * 2 + pitch_offset, diameter * 2, diameter * 2), SKY)
        painter.fillRect(QRectF(-diameter, pitch_offset, diameter * 2, diameter * 2), GROUND)
        painter.setPen(QPen(TEXT, 2))
        painter.drawLine(QPointF(-diameter, pitch_offset), QPointF(diameter, pitch_offset))
        for pitch in (-30, -20, -10, 10, 20, 30):
            y = pitch_offset + pitch * diameter / 90.0
            width = diameter * (0.22 if pitch % 20 else 0.32)
            painter.drawLine(QPointF(-width, y), QPointF(width, y))
        painter.restore()

        painter.setPen(QPen(ACCENT, 3))
        painter.drawLine(QPointF(centre.x() - diameter * 0.28, centre.y()), QPointF(centre.x() - 8, centre.y()))
        painter.drawLine(QPointF(centre.x() + 8, centre.y()), QPointF(centre.x() + diameter * 0.28, centre.y()))
        painter.drawEllipse(QPointF(centre.x(), centre.y()), 4, 4)
        painter.setPen(QPen(RING, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(circle)
