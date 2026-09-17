"""Cached Qt image for the signed sixteen-element correlation matrix."""

from __future__ import annotations

import math

import numpy as np
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from supersilence.features.device_status.domain.raw_waveforms import ELEMENT_COUNT, validate_enabled_elements
from supersilence.shared.ui.theme import DENSE_LABEL_POINT_SIZE, plot_palette

HEADER_HEIGHT = 34.0
LABEL_WIDTH = 30.0
LEGEND_WIDTH = 74.0
MARGIN = 8.0


def correlation_colour(value: float) -> QColor:
    """Map signed correlation to blue (inverse), neutral, or red (positive)."""
    bounded = max(-1.0, min(1.0, float(value)))
    neutral = (232, 235, 239)
    target = (38, 105, 210) if bounded < 0.0 else (210, 55, 55)
    amount = abs(bounded)
    return QColor(*(round(neutral[index] + amount * (target[index] - neutral[index])) for index in range(3)))


def correlation_cell(value: float, enabled: bool, panel_colour: str, dim_colour: str) -> tuple[QColor, QColor, str]:
    """Return unambiguous fill, text colour, and text for one matrix cell."""
    if not enabled:
        return QColor("black"), QColor("white"), "OFF"
    if math.isfinite(value):
        return correlation_colour(value), QColor("white") if abs(value) >= 0.55 else QColor("black"), f"{value:+.2f}"
    return QColor(panel_colour), QColor(dim_colour), "N/A"


class CorrelationMatrixPlot(QWidget):
    """Render numeric signed correlations once and reuse the resulting image."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._matrix = np.full((ELEMENT_COUNT, ELEMENT_COUNT), np.nan, dtype=np.float64)
        self._matrix.setflags(write=False)
        self._enabled = (True,) * ELEMENT_COUNT
        self._cached_image: QImage | None = None
        self.setMinimumSize(620, 620)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_matrix(self, matrix: np.ndarray, *, enabled=None) -> None:
        values = np.asarray(matrix, dtype=np.float64)
        if values.shape != (ELEMENT_COUNT, ELEMENT_COUNT):
            raise ValueError(f"correlation matrix must have shape ({ELEMENT_COUNT}, {ELEMENT_COUNT})")
        copied = values.copy()
        copied.setflags(write=False)
        self._matrix = copied
        if enabled is not None:
            self._enabled = validate_enabled_elements(enabled)
        self._cached_image = None
        self.update()

    def matrix(self) -> np.ndarray:
        return self._matrix

    def enabled_elements(self) -> tuple[bool, ...]:
        return self._enabled

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt naming
        del event
        if self._cached_image is None:
            self._cached_image = self._render_image()
        painter = QPainter(self)
        painter.drawImage(0, 0, self._cached_image)
        painter.end()

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt naming
        self._cached_image = None
        super().resizeEvent(event)

    def _render_image(self) -> QImage:
        pixel_ratio = self.devicePixelRatioF()
        image = QImage(
            max(1, round(self.width() * pixel_ratio)),
            max(1, round(self.height() * pixel_ratio)),
            QImage.Format.Format_ARGB32_Premultiplied,
        )
        image.setDevicePixelRatio(pixel_ratio)
        colours = plot_palette()
        painter = QPainter(image)
        painter.fillRect(QRectF(0.0, 0.0, self.width(), self.height()), QColor(colours.panel))
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.setFont(QFont(painter.font().family(), DENSE_LABEL_POINT_SIZE))
        painter.setPen(QColor(colours.text))
        painter.drawText(
            QRectF(MARGIN, 0.0, self.width() - 2.0 * MARGIN, HEADER_HEIGHT),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            "Signed zero-lag Pearson correlation · red +1 · neutral 0 · blue -1",
        )

        available_width = max(1.0, self.width() - LABEL_WIDTH - LEGEND_WIDTH - 3.0 * MARGIN)
        available_height = max(1.0, self.height() - HEADER_HEIGHT - LABEL_WIDTH - 2.0 * MARGIN)
        side = min(available_width, available_height)
        cell = side / ELEMENT_COUNT
        left = MARGIN + LABEL_WIDTH
        top = HEADER_HEIGHT + LABEL_WIDTH
        painter.setPen(QColor(colours.text))
        for index in range(ELEMENT_COUNT):
            label = str(index + 1)
            painter.drawText(QRectF(left + index * cell, HEADER_HEIGHT, cell, LABEL_WIDTH), Qt.AlignmentFlag.AlignCenter, label)
            painter.drawText(QRectF(MARGIN, top + index * cell, LABEL_WIDTH, cell), Qt.AlignmentFlag.AlignCenter, label)

        painter.setPen(QPen(QColor(colours.grid), 1.0))
        for row in range(ELEMENT_COUNT):
            for column in range(ELEMENT_COUNT):
                rect = QRectF(left + column * cell, top + row * cell, cell, cell)
                value = self._matrix[row, column]
                enabled = self._enabled[row] and self._enabled[column]
                fill, text_colour, text = correlation_cell(float(value), enabled, colours.panel, colours.dim)
                painter.fillRect(rect, fill)
                painter.setPen(text_colour)
                painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
                painter.setPen(QColor(colours.grid))
                painter.drawRect(rect)
        painter.end()
        return image


__all__ = ["CorrelationMatrixPlot", "correlation_cell", "correlation_colour"]
