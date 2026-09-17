"""Operator-facing attitude from the decoded GDAT2 telemetry stream."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Callable

ATTITUDE_FRESH_SECONDS = 1.0
ATTITUDE_HOLD_SECONDS = 30.0
ALTIMETER_FRESH_SECONDS = 3.0
MAXIMUM_ALTIMETER_DISTANCE_MILLIMETRES = 150_000
WEAK_CONFIDENCE_PERCENT = 30


def normalise_signed_yaw(value: float) -> float:
    """Use north=0, east=+90, west=-90, and south=-180 degrees."""
    return (float(value) + 180.0) % 360.0 - 180.0


@dataclass(frozen=True)
class AttitudeReading:
    roll_degrees: float
    pitch_degrees: float
    heading_degrees: float
    source: str
    age_seconds: float


@dataclass(frozen=True)
class AltimeterReading:
    distance_metres: float
    confidence_percent: int
    quality: str
    age_seconds: float


@dataclass(frozen=True)
class TelemetryPresentation:
    attitude: AttitudeReading | None
    altimeter: AltimeterReading | None


class ImuAttitudeSelector:
    """Use decoded GDAT2 attitude and briefly hold it during reconnects."""

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._last_attitude: AttitudeReading | None = None
        self._last_direct_at: float | None = None

    def select(self, snapshot: object, compass_offset_degrees: float = 0.0) -> AttitudeReading | None:
        direct = _decoded_attitude(getattr(snapshot, "gdat2", None))
        now = self._clock()
        if direct is not None:
            self._last_attitude = _with_compass_offset(direct, compass_offset_degrees)
            self._last_direct_at = now
            return self._last_attitude
        if self._last_attitude is None or self._last_direct_at is None:
            return None
        held_age = now - self._last_direct_at
        if held_age >= ATTITUDE_HOLD_SECONDS:
            self._last_attitude = None
            self._last_direct_at = None
            return None
        return AttitudeReading(
            self._last_attitude.roll_degrees,
            self._last_attitude.pitch_degrees,
            self._last_attitude.heading_degrees,
            "GDAT2 decoder reconnecting",
            held_age,
        )


def select_telemetry_presentation(
    snapshot: object,
    *,
    attitude_selector: ImuAttitudeSelector | None = None,
    compass_offset_degrees: float = 0.0,
) -> TelemetryPresentation:
    """Select decoded GDAT2 attitude and Ping1D readings without infrastructure imports."""
    attitude = (
        attitude_selector.select(snapshot, compass_offset_degrees)
        if attitude_selector is not None
        else _with_compass_offset(_decoded_attitude(getattr(snapshot, "gdat2", None)), compass_offset_degrees)
    )
    return TelemetryPresentation(
        attitude,
        _altimeter_reading(getattr(snapshot, "altimeter", None)),
    )


def _decoded_attitude(snapshot: object | None) -> AttitudeReading | None:
    if snapshot is None or not _fresh(snapshot, "message_age_seconds", ATTITUDE_FRESH_SECONDS):
        return None
    sample = getattr(snapshot, "latest_sample", None)
    if sample is None:
        return None
    return _attitude(
        getattr(sample, "roll_deg", None),
        getattr(sample, "pitch_deg", None),
        getattr(sample, "yaw_deg", None),
        "GDAT2 decoder",
        getattr(snapshot, "message_age_seconds"),
    )


def _attitude(
    roll: object,
    pitch: object,
    yaw: object,
    source: str,
    age_seconds: float,
) -> AttitudeReading | None:
    if not all(_finite_number(value) for value in (roll, pitch, yaw)):
        return None
    roll_value, pitch_value, yaw_value = float(roll), float(pitch), float(yaw)
    if not -180.0 <= roll_value <= 180.0 or not -90.0 <= pitch_value <= 90.0:
        return None
    if not -180.0 <= yaw_value <= 360.0:
        return None
    return AttitudeReading(
        roll_value,
        pitch_value,
        normalise_signed_yaw(yaw_value),
        source,
        float(age_seconds),
    )


def _with_compass_offset(attitude: AttitudeReading | None, compass_offset_degrees: float) -> AttitudeReading | None:
    if attitude is None:
        return None
    if not _finite_number(compass_offset_degrees):
        return attitude
    return AttitudeReading(
        attitude.roll_degrees,
        attitude.pitch_degrees,
        normalise_signed_yaw(attitude.heading_degrees - float(compass_offset_degrees)),
        attitude.source,
        attitude.age_seconds,
    )


def _altimeter_reading(snapshot: object | None) -> AltimeterReading | None:
    if snapshot is None or not _fresh(snapshot, "reading_age_seconds", ALTIMETER_FRESH_SECONDS):
        return None
    distance = getattr(snapshot, "distance", None)
    if distance is None:
        return None
    millimetres = getattr(distance, "distance_millimetres", None)
    confidence = getattr(distance, "confidence_percent", None)
    if not isinstance(millimetres, int) or isinstance(millimetres, bool):
        return None
    if not isinstance(confidence, int) or isinstance(confidence, bool):
        return None
    if not 0 <= millimetres <= MAXIMUM_ALTIMETER_DISTANCE_MILLIMETRES:
        return None
    if not 0 <= confidence <= 100:
        return None
    quality = "no echo" if confidence == 0 else "weak" if confidence < WEAK_CONFIDENCE_PERCENT else "live"
    return AltimeterReading(
        millimetres / 1_000.0,
        confidence,
        quality,
        float(getattr(snapshot, "reading_age_seconds")),
    )


def _fresh(snapshot: object, age_name: str, maximum_age_seconds: float) -> bool:
    state = getattr(getattr(snapshot, "state", None), "value", getattr(snapshot, "state", None))
    age = getattr(snapshot, age_name, None)
    return state == "connected/fresh" and _finite_number(age) and 0.0 <= float(age) <= maximum_age_seconds


def _finite_number(value: object) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(float(value))
