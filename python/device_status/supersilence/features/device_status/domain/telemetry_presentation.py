"""Compatibility exports for the shared telemetry presentation policy."""

from supersilence.shared.telemetry_presentation import (
    ALTIMETER_FRESH_SECONDS,
    ATTITUDE_FRESH_SECONDS,
    MAXIMUM_ALTIMETER_DISTANCE_MILLIMETRES,
    WEAK_CONFIDENCE_PERCENT,
    AltimeterReading,
    AttitudeReading,
    TelemetryPresentation,
    select_telemetry_presentation,
)

__all__ = (
    "ALTIMETER_FRESH_SECONDS",
    "ATTITUDE_FRESH_SECONDS",
    "MAXIMUM_ALTIMETER_DISTANCE_MILLIMETRES",
    "WEAK_CONFIDENCE_PERCENT",
    "AltimeterReading",
    "AttitudeReading",
    "TelemetryPresentation",
    "select_telemetry_presentation",
)
