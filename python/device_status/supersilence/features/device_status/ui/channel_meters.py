"""Sixteen channel meters for one unit.

Drawn rather than assembled from progress bars: sixteen bars, a held peak line
on each, a ruled dB scale behind them, and a state colour per channel is one
paint pass, and it stays readable at the size a four-unit window can give it.

Each channel is a pair of bars, not one. The left, state-coloured bar is
root-mean-square level of the raw hardware signal — the white line above it is
its held peak — and never moves for gain: see the module docstring in
`infrastructure/acquisition/gain.py` for why. The right, blue bar is arithmetic
on the same measurement (RMS plus gain, both already in decibels — a second
measurement is not needed), not a separate reading, and it fluctuates with the
input exactly the way the raw bar does, because it is driven by the same
samples. Both carry their own held-peak line. At 0 dB gain the two bars are
identical, which is itself the information: gain is doing nothing.

The colour says what the operator should do about the raw bar — grey SILENT
means an input that is not delivering, red CLIP means the samples themselves
are wrong. Both are faults; the amber band in between is only loudness. The
gained bar is always the same blue: gain has no hardware fault of its own to
report.

A channel the operator has switched out of the array is still drawn, at its
real height, and captioned OFF. Drawn, because that bar is the only way to see
that a channel has come back — a channel painted as nothing would have to be
re-enabled on faith. Dimmed, because what it shows is no longer reaching any
direction estimate. Its speaker button stays live for the same reason the bar
does.
"""
from __future__ import annotations

from PySide6.QtCore import QRect, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import QSizePolicy, QStyle, QToolButton, QWidget

from supersilence.features.device_status.domain.meter_scale import (
    CLIPPING,
    NORMAL,
    SILENT,
    UNMEASURED,
    WARNING,
    MeterScale,
    gained_dbfs,
    state_of,
)
from supersilence.infrastructure.acquisition.levels import UnitLevels
from supersilence.shared.ui.theme import (
    DARK_PLOT_PALETTE,
    DENSE_LABEL_POINT_SIZE,
    plot_palette,
)

STATE_COLOURS = {
    NORMAL: "#3fb950",
    WARNING: "#d29922",
    CLIPPING: "#f85149",
    SILENT: "#6b7280",
    UNMEASURED: "#30363d",
}

PANEL_COLOUR = "#1c1f26"
GRID_COLOUR = "#2c313a"
TEXT_COLOUR = "#c8ccd4"
DIM_COLOUR = "#6b7280"
PEAK_COLOUR = "#ffffff"
GAIN_BAR_COLOUR = "#58a6ff"
#: A switched-out channel's bars. Still painted at their real height — see the
#: module docstring — but in one flat colour that reads as out of service
#: rather than as any of the five states.
DISABLED_BAR_COLOUR = "#3a3f4b"
DISABLED_PEAK_COLOUR = "#5a6270"
HEAR_BUTTON_BACKGROUND_COLOUR = "#f0f6fc"
HEAR_BUTTON_SELECTED_BACKGROUND_COLOUR = "#b6d7ff"
HEAR_BUTTON_DISABLED_BACKGROUND_COLOUR = "#9da7b3"
HEAR_BUTTON_BORDER_COLOUR = "#8c959f"

HEAR_BUTTON_STYLE = f"""
QToolButton {{
    background-color: {HEAR_BUTTON_BACKGROUND_COLOUR};
    border: 1px solid {HEAR_BUTTON_BORDER_COLOUR};
    border-radius: 4px;
    padding: 1px;
}}
QToolButton:hover {{
    background-color: #ffffff;
    border-color: {GAIN_BAR_COLOUR};
}}
QToolButton:checked {{
    background-color: {HEAR_BUTTON_SELECTED_BACKGROUND_COLOUR};
    border-color: {GAIN_BAR_COLOUR};
}}
QToolButton:pressed {{
    background-color: #9ccaff;
}}
QToolButton:disabled {{
    background-color: {HEAR_BUTTON_DISABLED_BACKGROUND_COLOUR};
    border-color: #c8ccd4;
}}
"""

#: Gap, in pixels, between one channel's raw bar and its gained bar.
BAR_GAP = 2

#: Room under the bars for the channel number and its state word.
LABEL_HEIGHT = 34

#: An icon-only control centered above each raw/gained bar pair.
HEAR_BUTTON_SIZE = 24
HEAR_BUTTON_ROW_HEIGHT = 30

#: Room to the left of the bars for the dB scale.
SCALE_WIDTH = 42


class ChannelMeterStrip(QWidget):
    """One unit's sixteen channels, as bars against a dB scale."""

    #: Replaced at the top of every paint by `_refresh_colours`. A class
    #: attribute rather than nothing, so a helper reached before the first
    #: paint draws in the shipped dark palette instead of raising.
    _colours = DARK_PLOT_PALETTE

    hear_requested = Signal(int, int)

    def __init__(
        self,
        unit_identifier: int,
        parent: QWidget | None = None,
        *,
        scale: MeterScale | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName(f"channel_meters_{unit_identifier}")
        self.unit_identifier = unit_identifier
        self.scale = scale or MeterScale()
        self._levels: UnitLevels | None = None
        self._gains_db: tuple[float, ...] = ()
        self._channels_enabled: tuple[bool, ...] = ()
        self._heard_channel: int | None = None
        self._speaker_icon = self.style().standardIcon(
            QStyle.StandardPixmap.SP_MediaVolume
        )
        self._muted_icon = self.style().standardIcon(
            QStyle.StandardPixmap.SP_MediaVolumeMuted
        )
        self._hear_buttons: list[QToolButton] = []
        for channel_index in range(16):
            button = QToolButton(self)
            button.setObjectName(
                f"hear_channel_{unit_identifier}_{channel_index}"
            )
            button.setAutoRaise(False)
            button.setCheckable(True)
            button.setStyleSheet(HEAR_BUTTON_STYLE)
            button.clicked.connect(
                lambda _checked=False, index=channel_index: self.hear_requested.emit(
                    self.unit_identifier, index
                )
            )
            self._hear_buttons.append(button)
        self.set_heard_channel(None)
        # The chart is the flexible vertical surface. Keeping its minimum at
        # 200 px leaves room for the board-wide phantom-power control while
        # preserving the complete 720 px Device Status composition.
        self.setMinimumHeight(200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setToolTip(
            "Left, state-coloured bar: raw hardware signal. Right, blue bar: "
            "the same channel after its gain. White line on either: held peak."
        )

    def hear_button(self, channel_index: int) -> QToolButton:
        return self._hear_buttons[channel_index]

    def heard_channel(self) -> int | None:
        return self._heard_channel

    def set_hearing_available(self, available: bool) -> None:
        """Disable controls on a telemetry-only unit with no audio stream."""
        for index, button in enumerate(self._hear_buttons):
            button.setEnabled(available)
            if not available:
                button.setToolTip(
                    f"Unit {self.unit_identifier} channel {index + 1} has no "
                    "live acquisition"
                )
        if available:
            self.set_heard_channel(self._heard_channel)

    def set_heard_channel(self, channel_index: int | None) -> None:
        """Draw exactly one speaker icon, or sixteen muted icons."""
        if channel_index is not None and not 0 <= channel_index < len(
            self._hear_buttons
        ):
            raise ValueError(f"channel index {channel_index} is out of range")
        self._heard_channel = channel_index
        for index, button in enumerate(self._hear_buttons):
            active = index == channel_index
            button.setChecked(active)
            button.setIcon(self._speaker_icon if active else self._muted_icon)
            action = "Mute" if active else "Hear"
            description = (
                f"{action} unit {self.unit_identifier} channel {index + 1}"
            )
            button.setAccessibleName(description)
            button.setToolTip(description)

    def set_levels(self, levels: UnitLevels) -> None:
        self._levels = levels
        self.update()

    def levels(self) -> UnitLevels | None:
        return self._levels

    def set_gains_db(self, gains_db: tuple[float, ...]) -> None:
        """The current gain for each channel, for the gained bar only.

        Does not touch `_levels`: the raw bar is never gained. See the module
        docstring.
        """
        self._gains_db = gains_db
        self.update()

    def _gain_db(self, index: int) -> float:
        return self._gains_db[index] if index < len(self._gains_db) else 0.0

    def set_channels_enabled(self, enabled: tuple[bool, ...]) -> None:
        """Which channels are still part of the array, for the OFF caption.

        Does not touch `_levels` either: a switched-out channel is still
        measured, and its bar still moves. Only what the caption says and how
        the bar is coloured change.
        """
        self._channels_enabled = tuple(bool(value) for value in enabled)
        self.update()

    def channels_enabled(self) -> tuple[bool, ...]:
        return self._channels_enabled

    def _is_enabled(self, index: int) -> bool:
        if index >= len(self._channels_enabled):
            return True
        return self._channels_enabled[index]

    def gained_bar_rectangles(self) -> tuple[QRect, ...]:
        """Where each channel's after-gain bar would be painted.

        One per channel, always — including at 0 dB gain, where it lands on
        exactly the same rectangle as `bar_rectangles()`'s. That equality is
        itself the readable state: gain doing nothing.
        """
        if self._levels is None or not self._levels.channels:
            return ()
        count = len(self._levels.channels)
        top, height = self._meter_area()
        width = max(1, (self.width() - SCALE_WIDTH) // count)
        bar_width = self._bar_width(width)
        rectangles = []
        for index, channel in enumerate(self._levels.channels):
            gained = gained_dbfs(channel.rms_dbfs, self._gain_db(index))
            filled = int(height * self.scale.fraction(gained))
            left = SCALE_WIDTH + index * width + 2 + bar_width + BAR_GAP
            rectangles.append(QRect(left, top + height - filled, bar_width, filled))
        return tuple(rectangles)

    @staticmethod
    def _bar_width(column_width: int) -> int:
        return max(1, (column_width - 4 - BAR_GAP) // 2)

    def channel_states(self) -> tuple[str, ...]:
        """What each channel would be drawn as. Exists so this is testable."""
        if self._levels is None:
            return ()
        return tuple(
            state_of(channel, self._levels.measured)
            for channel in self._levels.channels
        )

    def bar_rectangles(self) -> tuple[QRect, ...]:
        """Where each raw bar would be painted, at the current widget size.

        The left half of each channel's column; `gained_bar_rectangles()` is
        the right half, same height rule, same width.
        """
        if self._levels is None or not self._levels.channels:
            return ()
        count = len(self._levels.channels)
        top, height = self._meter_area()
        width = max(1, (self.width() - SCALE_WIDTH) // count)
        bar_width = self._bar_width(width)
        rectangles = []
        for index, channel in enumerate(self._levels.channels):
            filled = int(height * self.scale.fraction(channel.rms_dbfs))
            left = SCALE_WIDTH + index * width + 2
            rectangles.append(QRect(left, top + height - filled, bar_width, filled))
        return tuple(rectangles)

    def _meter_area(self) -> tuple[int, int]:
        top = HEAR_BUTTON_ROW_HEIGHT + 4
        return top, max(1, self.height() - LABEL_HEIGHT - top)

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt API
        super().resizeEvent(event)
        count = len(self._hear_buttons)
        column_width = max(1, (self.width() - SCALE_WIDTH) // count)
        size = max(1, min(HEAR_BUTTON_SIZE, column_width - 2))
        for index, button in enumerate(self._hear_buttons):
            column_left = SCALE_WIDTH + index * column_width
            left = column_left + max(0, (column_width - size) // 2)
            button.setGeometry(left, 2, size, size)

    def _refresh_colours(self):
        """Re-read the desktop's theme for this paint, and hold it for the helpers."""
        self._colours = plot_palette()
        return self._colours

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt naming
        del event
        painter = QPainter(self)
        colours = self._refresh_colours()
        painter.fillRect(self.rect(), QColor(colours.raised_panel))
        top, height = self._meter_area()
        self._paint_scale(painter, top, height)
        if self._levels is None:
            self._paint_placeholder(painter, "no acquisition service")
            painter.end()
            return
        if not self._levels.channels:
            self._paint_placeholder(painter, "no channels reported")
            painter.end()
            return
        self._paint_channels(painter, top, height)
        painter.end()

    def _paint_placeholder(self, painter: QPainter, message: str) -> None:
        painter.setPen(QColor(self._colours.dim))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, message)

    def _paint_scale(self, painter: QPainter, top: int, height: int) -> None:
        font = QFont(painter.font())
        font.setPointSize(DENSE_LABEL_POINT_SIZE)
        painter.setFont(font)
        for level in self.scale.gridlines():
            y = top + height - int(height * self.scale.fraction(level))
            painter.setPen(QColor(self._colours.grid))
            painter.drawLine(SCALE_WIDTH, y, self.width(), y)
            painter.setPen(QColor(self._colours.dim))
            painter.drawText(
                QRect(0, y - 8, SCALE_WIDTH - 6, 16),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                f"{level:.0f}",
            )

    def _paint_channels(self, painter: QPainter, top: int, height: int) -> None:
        levels = self._levels
        assert levels is not None
        states = self.channel_states()
        raw_rectangles = self.bar_rectangles()
        gained_rectangles = self.gained_bar_rectangles()
        for index, channel in enumerate(levels.channels):
            in_array = self._is_enabled(index)
            colour = QColor(
                STATE_COLOURS[states[index]] if in_array else DISABLED_BAR_COLOUR
            )
            peak_colour = QColor(
                self._colours.accent if in_array else DISABLED_PEAK_COLOUR
            )
            raw_rect = raw_rectangles[index]
            painter.fillRect(raw_rect, colour)
            if levels.measured:
                peak_y = top + height - int(height * self.scale.fraction(channel.peak_dbfs))
                painter.setPen(peak_colour)
                painter.drawLine(raw_rect.left(), peak_y, raw_rect.right(), peak_y)

            gained_rect = gained_rectangles[index]
            painter.fillRect(
                gained_rect,
                QColor(GAIN_BAR_COLOUR if in_array else DISABLED_BAR_COLOUR),
            )
            if levels.measured:
                gained_peak_y = top + height - int(
                    height
                    * self.scale.fraction(
                        gained_dbfs(channel.peak_dbfs, self._gain_db(index))
                    )
                )
                painter.setPen(peak_colour)
                painter.drawLine(
                    gained_rect.left(), gained_peak_y, gained_rect.right(), gained_peak_y
                )

            column_left = raw_rect.left() - 2
            column_width = gained_rect.right() - column_left
            painter.setPen(
                QColor(self._colours.text if in_array else self._colours.dim)
            )
            painter.drawText(
                QRect(column_left, top + height + 2, column_width, 14),
                Qt.AlignmentFlag.AlignCenter,
                str(channel.channel_number),
            )
            painter.setPen(QColor(colour))
            painter.drawText(
                QRect(column_left, top + height + 16, column_width, 14),
                Qt.AlignmentFlag.AlignCenter,
                self._caption(channel, states[index], in_array),
            )

    @staticmethod
    def _caption(channel, state: str, in_array: bool = True) -> str:
        # OFF outranks every state word. A switched-out channel that reads
        # SILENT and one that reads -42 dB are the same thing to the estimator,
        # and the operator's question about both is the same: is it in.
        if not in_array:
            return "OFF"
        if state == UNMEASURED:
            return "—"
        if state == CLIPPING:
            return "CLIP"
        if state == SILENT:
            return "SILENT"
        return f"{channel.rms_dbfs:.0f}"
