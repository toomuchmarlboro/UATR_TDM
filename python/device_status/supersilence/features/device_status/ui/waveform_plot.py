"""Small dependency-free Qt plot for one raw waveform."""

from __future__ import annotations

import math

import numpy as np
from PySide6.QtCore import QLineF, QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QSizePolicy, QWidget

from supersilence.shared.ui.theme import DENSE_LABEL_POINT_SIZE, plot_palette

CAPTION_HEIGHT = 22.0
PLOT_MARGIN = 5.0


def pixel_envelope(waveform: np.ndarray, maximum_columns: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Reduce a waveform to finite min/max values for each horizontal bin."""
    values = np.asarray(waveform)
    if values.ndim != 1:
        raise ValueError("waveform must be one-dimensional")
    if maximum_columns <= 0:
        raise ValueError("maximum columns must be positive")
    if not values.size:
        empty = np.empty(0, dtype=np.float64)
        empty.setflags(write=False)
        return empty, empty, empty

    column_count = min(values.size, maximum_columns)
    edges = np.linspace(0, values.size, column_count + 1, dtype=np.int64)
    denominator = max(1, values.size - 1)
    positions = ((edges[:-1] + edges[1:] - 1) * 0.5) / denominator
    finite = np.isfinite(values)
    minima = np.minimum.reduceat(np.where(finite, values, np.inf), edges[:-1]).astype(np.float64, copy=False)
    maxima = np.maximum.reduceat(np.where(finite, values, -np.inf), edges[:-1]).astype(np.float64, copy=False)
    empty_bins = ~np.isfinite(minima) | ~np.isfinite(maxima)
    minima[empty_bins] = np.nan
    maxima[empty_bins] = np.nan
    for result in (positions, minima, maxima):
        result.setflags(write=False)
    return positions, minima, maxima


class WaveformPlot(QWidget):
    """Cache a pixel-width envelope image while preserving retained samples."""

    def __init__(self, caption: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.caption = caption
        self._waveform = np.empty(0, dtype=np.float32)
        self._y_limit: float | None = None
        self._cached_image: QImage | None = None
        self.setMinimumSize(180, 100)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_waveform(self, values: np.ndarray, *, y_limit: float | None = None) -> None:
        waveform = np.asarray(values)
        if waveform.ndim != 1:
            raise ValueError("waveform must be one-dimensional")
        if y_limit is not None and (not math.isfinite(y_limit) or y_limit <= 0.0):
            raise ValueError("waveform amplitude limit must be finite and positive")
        waveform = waveform.copy()
        waveform.setflags(write=False)
        self._waveform = waveform
        self._y_limit = y_limit
        self._cached_image = None
        self.update()

    def waveform(self) -> np.ndarray:
        return self._waveform

    def amplitude_limit(self) -> float:
        if self._y_limit is not None:
            return self._y_limit
        if not self._waveform.size:
            return 1.0
        finite = np.asarray(self._waveform[np.isfinite(self._waveform)], dtype=np.float64)
        return max(1.0, float(np.max(np.abs(finite)))) if finite.size else 1.0

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt naming
        del event
        if self._cached_image is None:
            self._cached_image = self._render_image()
        QPainter(self).drawImage(0, 0, self._cached_image)

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
        painter.drawText(QRectF(PLOT_MARGIN, 0.0, self.width() - 2 * PLOT_MARGIN, CAPTION_HEIGHT), Qt.AlignmentFlag.AlignLeft, self.caption)

        plot = QRectF(
            PLOT_MARGIN,
            CAPTION_HEIGHT,
            max(1.0, self.width() - 2 * PLOT_MARGIN),
            max(1.0, self.height() - CAPTION_HEIGHT - PLOT_MARGIN),
        )
        painter.setPen(QPen(QColor(colours.grid), 1.0))
        painter.drawRect(plot)
        middle = plot.center().y()
        painter.drawLine(QPointF(plot.left(), middle), QPointF(plot.right(), middle))

        if not self._waveform.size:
            painter.setPen(QColor(colours.dim))
            painter.drawText(plot, Qt.AlignmentFlag.AlignCenter, "No raw samples")
            painter.end()
            return image

        limit = self.amplitude_limit()
        count = self._waveform.size
        painter.setPen(QPen(QColor(colours.trace), 1.0))
        maximum_columns = max(1, int(plot.width()))
        if count <= maximum_columns:
            denominator = max(1, count - 1)
            points = QPolygonF()
            for index, value in enumerate(self._waveform):
                if not np.isfinite(value):
                    continue
                x = plot.left() + plot.width() * index / denominator
                normalized = max(-1.0, min(1.0, float(value) / limit))
                y = middle - normalized * plot.height() / 2.0
                points.append(QPointF(x, y))
            if len(points) == 1:
                painter.drawPoint(points[0])
            elif points:
                painter.drawPolyline(points)
        else:
            positions, minima, maxima = pixel_envelope(self._waveform, maximum_columns)
            lines = []
            for position, minimum, maximum in zip(positions, minima, maxima, strict=True):
                if not (math.isfinite(minimum) and math.isfinite(maximum)):
                    continue
                x = plot.left() + plot.width() * float(position)
                minimum = max(-1.0, min(1.0, float(minimum) / limit))
                maximum = max(-1.0, min(1.0, float(maximum) / limit))
                lines.append(
                    QLineF(
                        QPointF(x, middle - maximum * plot.height() / 2.0),
                        QPointF(x, middle - minimum * plot.height() / 2.0),
                    )
                )
            if lines:
                painter.drawLines(lines)
        painter.end()
        return image


__all__ = ["WaveformPlot", "pixel_envelope"]
