"""Per-channel signal levels for the sixteen hydrophone channels of one unit.

This exists so an operator can answer "is channel 7 actually hearing anything"
without reading a spectrum. It is a meter, not analysis: root-mean-square level,
a held peak, and two states that mean something specific about the hardware.

**SILENT** is the important one. The ADC dithers its least significant bit even
with nothing connected, so a genuinely dead analog path does not read exactly
zero — it reads a handful of counts. A channel below the silence floor is
therefore not "quiet water"; it is an input that is not delivering, which on a
deployed array means a hydrophone, a cable, or a preamplifier, not a calm sea.

**CLIPPING** is at digital full scale. It is only meaningful on a channel that
has something connected: an open input with phantom power on it clips and says
nothing at all.

Levels are computed where the samples already are — in the acquisition
processing thread, on the assembled block before decimation — so the meter sees
the true 96 kHz channel, and nothing has to consume the sample stream twice.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from supersilence.infrastructure.acquisition.uatr_tdm import CHANNEL_COUNT

#: Signed 24-bit samples: full scale is 2**23, matching the decoder.
FULL_SCALE = 1 << 23

#: Reported instead of negative infinity for a mathematically silent channel,
#: so display code never has to special-case a float it cannot draw.
SILENCE_FLOOR_DBFS = -140.0

#: Below this, the analog path is not delivering. See the module docstring.
DEFAULT_SILENT_DBFS = -120.0

#: How long a peak stays up before it starts following the signal down again.
#: Short enough to track a moving contact, long enough for an eye to catch a
#: transient between two redraws.
DEFAULT_PEAK_HOLD_SECONDS = 1.5


def to_dbfs(amplitude: float) -> float:
    """Amplitude in sample counts as decibels relative to full scale."""
    if amplitude <= 0.0:
        return SILENCE_FLOOR_DBFS
    value = 20.0 * math.log10(amplitude / FULL_SCALE)
    return max(SILENCE_FLOOR_DBFS, value)


@dataclass(frozen=True)
class ChannelLevel:
    """One channel's level, as the operator should read it."""

    channel_number: int
    rms_dbfs: float
    peak_dbfs: float
    silent: bool
    clipping: bool


@dataclass(frozen=True)
class UnitLevels:
    """Every channel of one unit, from one moment.

    ``measured`` is false before any samples have arrived. That is not the same
    as silence, and the display must not draw it as though it were.
    """

    unit_identifier: int
    measured: bool
    channels: tuple[ChannelLevel, ...]


def _unmeasured_channels() -> tuple[ChannelLevel, ...]:
    return tuple(
        ChannelLevel(number + 1, SILENCE_FLOOR_DBFS, SILENCE_FLOOR_DBFS, False, False)
        for number in range(CHANNEL_COUNT)
    )


class ChannelLevelMeter:
    """Running level state for one unit's sixteen channels.

    Owned by the acquisition service and updated from its processing thread;
    :meth:`snapshot` is what other threads read.
    """

    def __init__(
        self,
        unit_identifier: int,
        *,
        silent_dbfs: float = DEFAULT_SILENT_DBFS,
        peak_hold_seconds: float = DEFAULT_PEAK_HOLD_SECONDS,
        full_scale: float = FULL_SCALE,
    ) -> None:
        if not math.isfinite(silent_dbfs) or silent_dbfs >= 0.0:
            raise ValueError("silence threshold must be finite and below full scale")
        if not math.isfinite(peak_hold_seconds) or peak_hold_seconds <= 0.0:
            raise ValueError("peak hold must be finite and positive")
        if not math.isfinite(full_scale) or full_scale <= 0.0:
            raise ValueError("full scale must be finite and positive")
        self.unit_identifier = unit_identifier
        self._silent_dbfs = silent_dbfs
        self._peak_hold_seconds = peak_hold_seconds
        self._full_scale = float(full_scale)
        self._rms = np.zeros(CHANNEL_COUNT, dtype=np.float64)
        self._peak = np.zeros(CHANNEL_COUNT, dtype=np.float64)
        self._peak_set_at = np.full(CHANNEL_COUNT, -math.inf, dtype=np.float64)
        self._clipped = np.zeros(CHANNEL_COUNT, dtype=bool)
        self._measured = False

    def update(self, samples: np.ndarray, now: float) -> None:
        """Fold one block of ``(frames, 16)`` samples into the meter."""
        if samples.ndim != 2 or samples.shape[1] != CHANNEL_COUNT:
            raise ValueError(
                f"level meter expects (frames, {CHANNEL_COUNT}) samples, "
                f"got {samples.shape}"
            )
        if not samples.shape[0]:
            return
        values = samples.astype(np.float64, copy=False)
        self._rms = np.sqrt(np.mean(np.square(values), axis=0))
        block_peak = np.max(np.abs(values), axis=0)
        # A peak is held, then released, rather than smoothed: an operator
        # watching for an intermittent fault needs the highest value to stay put
        # long enough to be seen, and an average would hide it entirely.
        expired = (now - self._peak_set_at) > self._peak_hold_seconds
        replaced = block_peak >= self._peak
        refresh = expired | replaced
        self._peak = np.where(refresh, block_peak, self._peak)
        self._peak_set_at = np.where(refresh, now, self._peak_set_at)
        self._clipped = block_peak >= self._full_scale * (1.0 - 1e-7)
        self._measured = True

    def snapshot(self) -> UnitLevels:
        if not self._measured:
            return UnitLevels(self.unit_identifier, False, _unmeasured_channels())
        channels = []
        for index in range(CHANNEL_COUNT):
            rms_dbfs = self._to_dbfs(float(self._rms[index]))
            channels.append(
                ChannelLevel(
                    channel_number=index + 1,
                    rms_dbfs=rms_dbfs,
                    peak_dbfs=self._to_dbfs(float(self._peak[index])),
                    silent=rms_dbfs <= self._silent_dbfs,
                    clipping=bool(self._clipped[index]),
                )
            )
        return UnitLevels(self.unit_identifier, True, tuple(channels))

    def _to_dbfs(self, amplitude: float) -> float:
        if amplitude <= 0.0:
            return SILENCE_FLOOR_DBFS
        value = 20.0 * math.log10(amplitude / self._full_scale)
        return max(SILENCE_FLOOR_DBFS, value)
