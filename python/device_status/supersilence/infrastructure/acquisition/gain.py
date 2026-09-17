"""Per-channel digital gain, applied after decimation and before the rest of DSP.

This is a software preprocessing stage, not a hardware control: nothing here is
ever sent to a unit. It exists to correct for sensitivity differences between
the sixteen hydrophone channels on one buoy — a channel that reads consistently
hot or quiet next to its neighbours, for reasons upstream of the console (the
hydrophone itself, its cable, its preamplifier) that the operator cannot reach
from here but can compensate for here.

Applied after decimation deliberately: the channel meters on the Device Status
page are metered on the raw, pre-decimation block so they keep showing the true
hardware signal (see `levels.py`). Gain changes are therefore invisible on those
meters by design — they only show up in what DSP downstream of decimation sees.

Values are stored and edited in decibels, because that is how an operator
thinks about "turn this one down a bit"; the pipeline itself multiplies by the
linear equivalent.
"""

from __future__ import annotations

import math
import threading
from collections.abc import Iterable, Sequence
from statistics import median

import numpy as np

from supersilence.infrastructure.acquisition.uatr_tdm import CHANNEL_COUNT

#: The operator-requested working range for software sensitivity correction.
#: This is not a measured hardware limit — the value never touches the ADC.
#: At the two ends the DSP multiplier is 0.001 or 1,000, so the range can expose
#: an extreme mismatch without pretending that amplifying a channel also
#: improves its signal-to-noise ratio.
MINIMUM_GAIN_DB = -60.0
MAXIMUM_GAIN_DB = 60.0
DEFAULT_GAIN_DB = 0.0

DEFAULT_GAINS_DB: tuple[float, ...] = (DEFAULT_GAIN_DB,) * CHANNEL_COUNT


def validate_gain_db(gain_db: float) -> float:
    """A single channel's gain, checked and returned as a plain float."""
    value = float(gain_db)
    if not math.isfinite(value) or not MINIMUM_GAIN_DB <= value <= MAXIMUM_GAIN_DB:
        raise ValueError(f"channel gain must be between {MINIMUM_GAIN_DB} and {MAXIMUM_GAIN_DB} dB, got {gain_db!r}")
    return value


def validate_channel_gains_db(gains_db: Iterable[float]) -> tuple[float, ...]:
    """Sixteen channel gains, checked and returned as a plain tuple."""
    checked = tuple(validate_gain_db(value) for value in gains_db)
    if len(checked) != CHANNEL_COUNT:
        raise ValueError(f"expected {CHANNEL_COUNT} channel gains, got {len(checked)}")
    return checked


def gain_db_to_linear(gain_db: float) -> float:
    """A decibel value as the multiplier the pipeline actually applies."""
    return 10.0 ** (gain_db / 20.0)


def clamp_gain_db(gain_db: float) -> float:
    """A gain forced into the working range, rather than refused.

    `validate_gain_db` raises, which is right for an operator's own typed or
    dragged value — a mistake worth stopping on. A *computed* gain (see
    `balance_gains_db`) is different: a channel fifty decibels quieter than its
    neighbours is real and worth reporting, and the honest response is the
    largest correction the software range allows, not an exception that drops
    every other channel's calculation with it.
    """
    return max(MINIMUM_GAIN_DB, min(MAXIMUM_GAIN_DB, gain_db))


def balance_gains_db(
    raw_rms_dbfs: Sequence[float],
    excluded: Sequence[bool],
    current_gains_db: Sequence[float],
) -> tuple[float, ...]:
    """Gains that bring every included channel's post-gain level to the same mark.

    For calibration: sensitivity differs channel to channel, so the same water
    reads at sixteen different levels even though nothing about the water does.
    The target is the *median* raw level across the included channels. The
    median minimizes their total absolute correction and, unlike the mean,
    does not let one unusually weak or hot eligible channel move the target
    away from the typical response. Matching the loudest would raise every
    quiet channel's gain (and its noise floor); matching the quietest would
    throw away headroom on the loud ones.

    `excluded[i]` true means channel `i` is not used to compute the target and
    is not touched — its own gain is carried through from `current_gains_db`
    unchanged. Silent and clipping channels must both be excluded by the
    caller: silence is a hardware fault no gain corrects (see `levels.py`'s own
    SILENT threshold), and a clipped reading is the sample being wrong, not a
    real level to calibrate against — either one included would pull every
    other channel's target toward a number that means nothing.

    A channel whose correction would fall outside `MINIMUM_GAIN_DB` to
    `MAXIMUM_GAIN_DB` is clamped rather than left unbalanced or raising: see
    `clamp_gain_db`.
    """
    included = [index for index, skip in enumerate(excluded) if not skip]
    result = list(current_gains_db)
    if not included:
        return tuple(result)
    target_dbfs = float(median(raw_rms_dbfs[index] for index in included))
    for index in included:
        result[index] = clamp_gain_db(target_dbfs - raw_rms_dbfs[index])
    return tuple(result)


def _multipliers(gains_db: tuple[float, ...]) -> np.ndarray:
    values = np.array([gain_db_to_linear(value) for value in gains_db], dtype=np.float32)
    values.setflags(write=False)
    return values


class ChannelGainStore:
    """Live per-unit, per-channel gain: read every processing block, written by
    the operator from the Device Status window.

    Two representations are kept side by side rather than converted on every
    read: `gains_db` is what the UI shows and edits, `multipliers` is what the
    processing thread multiplies samples by many times a second. Guarded by its
    own lock, independent of anything else in the acquisition service — the only
    state shared between the UI thread and the processing thread here is this.
    """

    def __init__(
        self,
        unit_identifiers: Iterable[int],
        *,
        initial_gains_db: dict[int, tuple[float, ...]] | None = None,
    ) -> None:
        self._lock = threading.Lock()
        self._gains_db: dict[int, tuple[float, ...]] = {}
        self._multipliers: dict[int, np.ndarray] = {}
        initial = initial_gains_db or {}
        for unit_identifier in unit_identifiers:
            gains = validate_channel_gains_db(initial.get(unit_identifier, DEFAULT_GAINS_DB))
            self._gains_db[unit_identifier] = gains
            self._multipliers[unit_identifier] = _multipliers(gains)

    def multipliers(self, unit_identifier: int) -> np.ndarray:
        """The current linear multiplier for each of the sixteen channels."""
        with self._lock:
            return self._multipliers[unit_identifier]

    def gains_db(self, unit_identifier: int) -> tuple[float, ...]:
        """The current gain for each of the sixteen channels, in decibels."""
        with self._lock:
            return self._gains_db[unit_identifier]

    def set_gain_db(self, unit_identifier: int, channel_index: int, gain_db: float) -> None:
        """Set one channel's gain. Takes effect on the unit's next block."""
        if not 0 <= channel_index < CHANNEL_COUNT:
            raise ValueError(f"channel index must be between 0 and {CHANNEL_COUNT - 1}, got {channel_index!r}")
        value = validate_gain_db(gain_db)
        with self._lock:
            current = list(self._gains_db[unit_identifier])
            current[channel_index] = value
            updated = tuple(current)
            self._gains_db[unit_identifier] = updated
            self._multipliers[unit_identifier] = _multipliers(updated)
