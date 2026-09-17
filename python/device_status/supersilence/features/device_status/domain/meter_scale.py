"""Turning a channel level in dBFS into something that can be drawn.

Kept away from Qt so the decisions that matter — where the bar ends, what colour
it is, which channels an operator should look at first — are testable without a
display, and so the same scale can drive a different widget later.

The scale is logarithmic because hearing is: a contact at -60 dBFS and one at
-30 dBFS are both audible and both matter, and a linear bar would draw the first
as nothing at all.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

#: Bottom of the drawn scale. Below this a channel is drawn as empty; the
#: SILENT state, not the bar, is what says a channel is not delivering.
DEFAULT_FLOOR_DBFS = -100.0

#: Loud enough that an operator should notice before full scale arrives.
DEFAULT_WARNING_DBFS = -12.0

#: Colour names, not Qt colours: this module does not import a toolkit.
NORMAL = "normal"
WARNING = "warning"
CLIPPING = "clipping"
SILENT = "silent"
UNMEASURED = "unmeasured"


@dataclass(frozen=True)
class MeterScale:
    """Where a level sits on a drawn meter, and what state it is in."""

    floor_dbfs: float = DEFAULT_FLOOR_DBFS
    ceiling_dbfs: float = 0.0
    warning_dbfs: float = DEFAULT_WARNING_DBFS

    def __post_init__(self) -> None:
        for value, label in (
            (self.floor_dbfs, "floor"),
            (self.ceiling_dbfs, "ceiling"),
            (self.warning_dbfs, "warning"),
        ):
            if not math.isfinite(value):
                raise ValueError(f"meter {label} must be a finite level")
        if self.floor_dbfs >= self.ceiling_dbfs:
            raise ValueError("meter floor must be below its ceiling")
        if not self.floor_dbfs < self.warning_dbfs <= self.ceiling_dbfs:
            raise ValueError("meter warning level must sit between floor and ceiling")

    def fraction(self, level_dbfs: float) -> float:
        """How full the bar is, 0.0 at the floor and 1.0 at the ceiling."""
        if not math.isfinite(level_dbfs):
            return 0.0
        span = self.ceiling_dbfs - self.floor_dbfs
        return min(1.0, max(0.0, (level_dbfs - self.floor_dbfs) / span))

    def gridlines(self, step_db: float = 20.0) -> tuple[float, ...]:
        """Levels to rule the scale at, from the ceiling downward."""
        if not math.isfinite(step_db) or step_db <= 0.0:
            raise ValueError("gridline step must be finite and positive")
        lines = []
        level = self.ceiling_dbfs
        while level >= self.floor_dbfs:
            lines.append(level)
            level -= step_db
        return tuple(lines)


def gained_dbfs(level_dbfs: float, gain_db: float) -> float:
    """What a measured level would read after a linear gain, in decibels.

    Gain is a per-channel multiplier applied downstream of where the meter is
    measured (see `infrastructure/acquisition/gain.py`), so the meter itself
    never moves when gain changes. This is the number a second, gain-aware
    indicator shows instead: a decibel gain adds directly to a decibel level,
    because both are already logarithms of the same amplitude ratio.
    """
    return level_dbfs + gain_db


def state_of(channel, measured: bool) -> str:
    """What an operator should read this channel as.

    Order matters. Clipping outranks everything because it means the samples are
    wrong, not merely loud. Silence outranks the level bands because a channel
    that is not delivering is a hardware fault, and drawing it in the same colour
    as quiet water would hide exactly the thing this window exists to show.
    """
    if not measured:
        return UNMEASURED
    if channel.clipping:
        return CLIPPING
    if channel.silent:
        return SILENT
    if channel.rms_dbfs >= DEFAULT_WARNING_DBFS:
        return WARNING
    return NORMAL


def summarize(levels) -> str:
    """One line for a window title or a status bar."""
    if not levels.measured:
        return "no samples yet"
    silent = sum(1 for channel in levels.channels if channel.silent)
    clipping = sum(1 for channel in levels.channels if channel.clipping)
    parts = [f"{len(levels.channels) - silent}/{len(levels.channels)} channels live"]
    if silent:
        parts.append(f"{silent} silent")
    if clipping:
        parts.append(f"{clipping} clipping")
    return ", ".join(parts)
