"""Pure contracts for controlled single-element gain balancing.

The calibration measures a known continuous tone in each element's retained
capture.  It deliberately has no knowledge of Qt, files, or live acquisition:
the same calculation can be checked again from the saved WAVs.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import median
from typing import Sequence

import numpy as np

DEFAULT_TONE_FREQUENCY_HZ = 500.0
DEFAULT_CAPTURE_SECONDS = 30.0
MINIMUM_CAPTURE_SECONDS = 1.0
MAXIMUM_CAPTURE_SECONDS = 120.0


@dataclass(frozen=True)
class ToneMeasurement:
    """One retained element capture's measured tone level and stability."""

    channel_index: int
    tone_level_dbfs: float
    level_spread_db: float
    valid: bool
    reason: str | None = None


@dataclass(frozen=True)
class GainProposal:
    """One visible, reviewable DSP-gain proposal."""

    channel_index: int
    measured_level_dbfs: float
    current_gain_db: float
    proposed_gain_db: float
    clamped: bool


def validate_capture_request(frequency_hz: float, duration_seconds: float) -> tuple[float, float]:
    """Return a usable tone request, refusing values outside this diagnostic's contract."""
    frequency = float(frequency_hz)
    duration = float(duration_seconds)
    if not math.isfinite(frequency) or not 1.0 <= frequency < 12_000.0:
        raise ValueError("tone frequency must be finite and between 1 Hz and 12 kHz")
    if not math.isfinite(duration) or not MINIMUM_CAPTURE_SECONDS <= duration <= MAXIMUM_CAPTURE_SECONDS:
        raise ValueError(f"capture duration must be between {MINIMUM_CAPTURE_SECONDS:g} and {MAXIMUM_CAPTURE_SECONDS:g} seconds")
    return frequency, duration


def measure_tone(
    samples: np.ndarray,
    *,
    channel_index: int,
    sample_rate: int,
    frequency_hz: float,
    window_seconds: float = 1.0,
) -> ToneMeasurement:
    """Measure a single tone using one-bin complex projection per short window.

    A direct projection (the Goertzel-equivalent result at one frequency) is
    used instead of total energy, so unrelated broadband water noise does not
    become a channel-gain correction. The window-to-window spread remains
    visible to the operator, but calibration uses the mean regardless.
    """
    values = np.asarray(samples, dtype=np.float64)
    if values.ndim != 1 or not values.size:
        return ToneMeasurement(channel_index, float("nan"), float("inf"), False, "no captured samples")
    if sample_rate <= 0:
        raise ValueError("sample rate must be positive")
    frequency, _ = validate_capture_request(frequency_hz, MINIMUM_CAPTURE_SECONDS)
    if frequency >= sample_rate / 2:
        return ToneMeasurement(channel_index, float("nan"), float("inf"), False, "tone is at or above Nyquist")
    window_frames = max(1, int(round(window_seconds * sample_rate)))
    complete_windows = values.size // window_frames
    if complete_windows == 0:
        return ToneMeasurement(channel_index, float("nan"), float("inf"), False, "capture is shorter than one analysis window")

    levels: list[float] = []
    frame_indices = np.arange(window_frames, dtype=np.float64)
    reference = np.exp(-2j * np.pi * frequency * frame_indices / sample_rate)
    for start in range(0, complete_windows * window_frames, window_frames):
        segment = values[start : start + window_frames]
        segment = segment - np.mean(segment)
        amplitude = 2.0 * abs(np.dot(segment, reference)) / window_frames
        levels.append(_amplitude_dbfs(amplitude / math.sqrt(2.0)))

    measured = float(np.mean(levels))
    spread = max(levels) - min(levels)
    if not math.isfinite(measured):
        return ToneMeasurement(channel_index, measured, spread, False, "tone level is not finite")
    return ToneMeasurement(channel_index, measured, spread, True)


def propose_gains(
    measurements: Sequence[ToneMeasurement],
    current_gains_db: Sequence[float],
    *,
    minimum_gain_db: float,
    maximum_gain_db: float,
) -> tuple[GainProposal, ...]:
    """Return compensating DSP gains against the median valid response.

    Existing fader values are included before the median is found, so a second
    controlled run refines a prior calibration instead of silently discarding
    it.  Invalid captures are excluded and receive no proposal.

    The correction is not quantised. The Device Status faders move in 0.5 dB
    steps because a hand on a slider needs a step; a measured compensation does
    not, and rounding it would leave a systematic error the measurement had
    already resolved.
    """
    current = tuple(float(value) for value in current_gains_db)
    valid = tuple(item for item in measurements if item.valid and 0 <= item.channel_index < len(current))
    if not valid:
        return ()
    target = float(median(item.tone_level_dbfs + current[item.channel_index] for item in valid))
    proposals = []
    for item in valid:
        requested = current[item.channel_index] + target - (item.tone_level_dbfs + current[item.channel_index])
        proposed = max(minimum_gain_db, min(maximum_gain_db, requested))
        proposals.append(
            GainProposal(
                item.channel_index,
                item.tone_level_dbfs,
                current[item.channel_index],
                proposed,
                proposed != requested,
            )
        )
    return tuple(proposals)


def _amplitude_dbfs(amplitude: float) -> float:
    if amplitude <= 0.0:
        return -140.0
    return max(-140.0, 20.0 * math.log10(amplitude))
