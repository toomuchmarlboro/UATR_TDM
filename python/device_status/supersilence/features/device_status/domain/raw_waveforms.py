"""Pure selection and summation rules for raw element waveforms."""

from __future__ import annotations

from enum import Enum

import numpy as np
from scipy.signal import butter, sosfiltfilt

ELEMENT_COUNT = 16
DEFAULT_BANDPASS_LOW_HZ = 100.0
DEFAULT_BANDPASS_HIGH_HZ = 5_000.0
DEFAULT_BANDPASS_ORDER = 4


class MatrixAnalysisMode(str, Enum):
    """Operator-visible correlation-matrix update behavior."""

    LIVE = "live"
    TIMED_MEAN = "timed_mean"


def validate_matrix_analysis_mode(value: MatrixAnalysisMode | str) -> MatrixAnalysisMode:
    try:
        return MatrixAnalysisMode(value)
    except ValueError as error:
        raise ValueError(f"unsupported matrix analysis mode: {value!r}") from error


class CorrelationMatrixAccumulator:
    """Keep bounded per-cell totals for a time-windowed correlation mean."""

    def __init__(self) -> None:
        self._totals = np.zeros((ELEMENT_COUNT, ELEMENT_COUNT), dtype=np.float64)
        self._counts = np.zeros((ELEMENT_COUNT, ELEMENT_COUNT), dtype=np.uint32)
        self._windows = 0

    @property
    def windows(self) -> int:
        return self._windows

    def append(self, matrix: np.ndarray) -> None:
        values = np.asarray(matrix, dtype=np.float64)
        if values.shape != (ELEMENT_COUNT, ELEMENT_COUNT):
            raise ValueError(f"correlation matrix must have shape ({ELEMENT_COUNT}, {ELEMENT_COUNT})")
        finite = np.isfinite(values)
        self._totals[finite] += values[finite]
        self._counts[finite] += 1
        self._windows += 1

    def mean(self) -> np.ndarray:
        result = np.full((ELEMENT_COUNT, ELEMENT_COUNT), np.nan, dtype=np.float64)
        populated = self._counts > 0
        result[populated] = self._totals[populated] / self._counts[populated]
        result.setflags(write=False)
        return result


def apply_polarity_signs(samples: np.ndarray, signs) -> np.ndarray:
    """Apply one verified +1/-1 Device Status polarity sign per element."""
    values = np.asarray(samples)
    if values.ndim != 2 or values.shape[1] != ELEMENT_COUNT:
        raise ValueError(f"waveforms must have shape (frames, {ELEMENT_COUNT})")
    polarity = np.asarray(tuple(signs), dtype=np.float64)
    if polarity.shape != (ELEMENT_COUNT,) or not np.isin(polarity, (-1.0, 1.0)).all():
        raise ValueError(f"polarity signs must contain {ELEMENT_COUNT} values of +1 or -1")
    corrected = values.astype(np.float64, copy=False) * polarity[None, :]
    corrected.setflags(write=False)
    return corrected


def signed_correlation(first: np.ndarray, second: np.ndarray) -> float | None:
    """Return finite zero-lag Pearson correlation, or ``None`` if undefined."""
    first_values = np.asarray(first, dtype=np.float64)
    second_values = np.asarray(second, dtype=np.float64)
    if first_values.ndim != 1 or second_values.ndim != 1:
        raise ValueError("correlation waveforms must be one-dimensional")
    if first_values.shape != second_values.shape:
        raise ValueError("correlation waveforms must have equal length")
    finite = np.isfinite(first_values) & np.isfinite(second_values)
    if np.count_nonzero(finite) < 2:
        return None
    first_centred = first_values[finite] - np.mean(first_values[finite])
    second_centred = second_values[finite] - np.mean(second_values[finite])
    denominator = float(np.linalg.norm(first_centred) * np.linalg.norm(second_centred))
    if denominator == 0.0 or not np.isfinite(denominator):
        return None
    return float(np.clip(np.dot(first_centred, second_centred) / denominator, -1.0, 1.0))


def validate_enabled_elements(values) -> tuple[bool, ...]:
    enabled = tuple(values)
    if len(enabled) != ELEMENT_COUNT or any(not isinstance(value, (bool, np.bool_)) for value in enabled):
        raise ValueError(f"enabled elements must contain {ELEMENT_COUNT} boolean values")
    return tuple(bool(value) for value in enabled)


def waveform_correlation_matrix(samples: np.ndarray, *, enabled=None) -> np.ndarray:
    """Return the signed 16-by-16 zero-lag correlation matrix."""
    values = np.asarray(samples)
    if values.ndim != 2 or values.shape[1] != ELEMENT_COUNT:
        raise ValueError(f"waveforms must have shape (frames, {ELEMENT_COUNT})")
    active = (True,) * ELEMENT_COUNT if enabled is None else validate_enabled_elements(enabled)
    matrix = np.full((ELEMENT_COUNT, ELEMENT_COUNT), np.nan, dtype=np.float64)
    for first in range(ELEMENT_COUNT):
        if not active[first]:
            continue
        for second in range(first, ELEMENT_COUNT):
            if not active[second]:
                continue
            correlation = signed_correlation(values[:, first], values[:, second])
            if correlation is not None:
                matrix[first, second] = correlation
                matrix[second, first] = correlation
    matrix.setflags(write=False)
    return matrix


def bandpass_waveforms(
    samples: np.ndarray,
    low_hz: float,
    high_hz: float,
    *,
    sample_rate: float,
    order: int = DEFAULT_BANDPASS_ORDER,
) -> np.ndarray:
    """Apply a zero-phase Butterworth band-pass along the frame axis."""
    values = np.asarray(samples)
    if values.ndim != 2 or values.shape[1] != ELEMENT_COUNT:
        raise ValueError(f"waveforms must have shape (frames, {ELEMENT_COUNT})")
    low = float(low_hz)
    high = float(high_hz)
    rate = float(sample_rate)
    if not np.isfinite((low, high, rate)).all() or rate <= 0.0:
        raise ValueError("band-pass frequencies and sample rate must be finite and positive")
    if not 0.0 < low < high < rate / 2.0:
        raise ValueError("band-pass frequencies must satisfy 0 < low < high < Nyquist")
    if not isinstance(order, int) or isinstance(order, bool) or order <= 0:
        raise ValueError("band-pass order must be a positive integer")
    if not values.shape[0]:
        filtered = values.astype(np.float64, copy=True)
    else:
        sections = butter(order, (low, high), btype="bandpass", fs=rate, output="sos")
        try:
            filtered = sosfiltfilt(sections, values.astype(np.float64, copy=False), axis=0)
        except ValueError as error:
            raise ValueError("waveform window is too short for zero-phase band-pass filtering") from error
    filtered.setflags(write=False)
    return filtered


def min_max_normalize(waveform: np.ndarray) -> np.ndarray:
    """Map one current waveform window onto ``[-1, 1]`` as float64."""
    values = np.asarray(waveform)
    if values.ndim != 1:
        raise ValueError("waveform must be one-dimensional")
    normalized = values.astype(np.float64, copy=True)
    finite = np.isfinite(normalized)
    if np.any(finite):
        minimum = float(np.min(normalized[finite]))
        maximum = float(np.max(normalized[finite]))
        if minimum == maximum:
            normalized[finite] = 0.0
        else:
            normalized[finite] = 2.0 * (normalized[finite] - minimum) / (maximum - minimum) - 1.0
    normalized.setflags(write=False)
    return normalized


def validate_element_to_channel(values) -> tuple[int, ...]:
    mapping = tuple(values)
    if len(mapping) != ELEMENT_COUNT or set(mapping) != set(range(ELEMENT_COUNT)):
        raise ValueError("element-to-channel mapping must contain every channel index once")
    return mapping


def selected_waveforms(
    samples: np.ndarray,
    first_element: int,
    second_element: int,
    *,
    sum_gain_multipliers: tuple[float, float] | None = None,
    enabled=None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Normalize two elements independently, then return their optional gain-weighted sum."""
    values = np.asarray(samples)
    if values.ndim != 2 or values.shape[1] != ELEMENT_COUNT:
        raise ValueError(f"waveforms must have shape (frames, {ELEMENT_COUNT})")
    if not 0 <= first_element < ELEMENT_COUNT or not 0 <= second_element < ELEMENT_COUNT:
        raise ValueError("element index is out of range")
    if first_element == second_element:
        raise ValueError("two different elements must be selected")
    if enabled is not None:
        active = validate_enabled_elements(enabled)
        if not active[first_element] or not active[second_element]:
            raise ValueError("selected elements must be enabled")
    first = min_max_normalize(values[:, first_element])
    second = min_max_normalize(values[:, second_element])
    if sum_gain_multipliers is None:
        first_multiplier = second_multiplier = 1.0
    else:
        first_multiplier, second_multiplier = (float(value) for value in sum_gain_multipliers)
        if not np.isfinite((first_multiplier, second_multiplier)).all() or first_multiplier <= 0.0 or second_multiplier <= 0.0:
            raise ValueError("sum gain multipliers must be finite and positive")
    summed = first_multiplier * first + second_multiplier * second
    summed.setflags(write=False)
    return first, second, summed


__all__ = [
    "CorrelationMatrixAccumulator",
    "DEFAULT_BANDPASS_HIGH_HZ",
    "DEFAULT_BANDPASS_LOW_HZ",
    "DEFAULT_BANDPASS_ORDER",
    "ELEMENT_COUNT",
    "MatrixAnalysisMode",
    "apply_polarity_signs",
    "bandpass_waveforms",
    "min_max_normalize",
    "selected_waveforms",
    "signed_correlation",
    "validate_enabled_elements",
    "validate_matrix_analysis_mode",
    "validate_element_to_channel",
    "waveform_correlation_matrix",
]
