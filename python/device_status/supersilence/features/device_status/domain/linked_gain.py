"""Common-delta gain movement for the Device Status fader link.

Pure arithmetic on a vector of decibel values, and deliberately ignorant of
where that vector comes from. The working range and the channel count are
*given* rather than imported: they are facts about the acquisition path
(`infrastructure/acquisition/gain.py` owns them), and a domain module that
reached for them would be domain code depending on infrastructure — which is
the one thing the folder rules forbid, and which the architecture test caught.

Passing them in costs the caller one argument and buys this module a headless
test that needs no acquisition stack at all.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class GainRange:
    """How many channels there are and how far their gain may travel."""

    channel_count: int
    minimum_db: float
    maximum_db: float

    def __post_init__(self) -> None:
        if self.channel_count <= 0:
            raise ValueError("channel count must be positive")
        if not self.minimum_db < self.maximum_db:
            raise ValueError("minimum gain must be below maximum gain")

    def validated(self, gains_db: Iterable[float]) -> tuple[float, ...]:
        """The vector, checked against this range and returned as plain floats."""
        checked = tuple(float(value) for value in gains_db)
        if len(checked) != self.channel_count:
            raise ValueError(f"expected {self.channel_count} channel gains, got {len(checked)}")
        for value in checked:
            self.validated_value(value)
        return checked

    def validated_value(self, gain_db: float) -> float:
        value = float(gain_db)
        if not math.isfinite(value) or not self.minimum_db <= value <= self.maximum_db:
            raise ValueError(f"channel gain must be between {self.minimum_db} and {self.maximum_db} dB, got {gain_db!r}")
        return value


def linked_gains_db(
    current_gains_db: Iterable[float],
    changed_channel_index: int,
    requested_gain_db: float,
    gain_range: GainRange,
) -> tuple[float, ...]:
    """Move every channel by one achievable delta.

    Existing differences between channels are preserved. If the requested
    movement would push any channel outside the working range, the one shared
    delta is shortened for every channel; independently clamping channels would
    silently destroy the offsets the link is meant to preserve.
    """
    current = gain_range.validated(current_gains_db)
    if not 0 <= changed_channel_index < gain_range.channel_count:
        raise ValueError(f"channel index must be between 0 and {gain_range.channel_count - 1}, got {changed_channel_index!r}")
    requested = gain_range.validated_value(requested_gain_db)
    requested_delta = requested - current[changed_channel_index]
    minimum_delta = max(gain_range.minimum_db - value for value in current)
    maximum_delta = min(gain_range.maximum_db - value for value in current)
    applied_delta = max(minimum_delta, min(maximum_delta, requested_delta))
    return gain_range.validated(value + applied_delta for value in current)
