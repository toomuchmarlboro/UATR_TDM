"""Which of a unit's sixteen channels are used, and which are switched out.

A hydrophone dies, a cable floods, a preamplifier fails. The channel that
results is not quiet water — it is a number arriving at wire rate that means
nothing, and every stage downstream treats it as a measurement. In the
covariance it is an element with no signal and its own noise, so the model order
test counts it, the noise subspace is built partly from it, and the steering
vector still asks it what it heard. One dead element does not merely add
nothing; it steers the answer.

Disabling a channel here removes it from the array. Not muted, not zeroed:
zeroing leaves the element in the geometry with an amplitude of zero, which is a
measurement of silence in a direction, and it makes the covariance rank
deficient in a way the shrinkage estimator will happily regularise into a
plausible wrong answer. The channel is dropped from the sample matrix *and* from
the element positions, and the estimators run on the remaining sub-array.

What a disabled channel does **not** stop:

- the channel meters, which are how the operator decides whether it is really
  dead and whether it has come back;
- recording, which archives the raw sixteen so the decision can be revisited
  against the same water;
- speaker monitoring, for the same reason.

Only the direction estimators lose it. This store is live state, read by the
processing thread on every block and written by the operator from the Device
Status window; `channel_enable_configuration.py` is what makes it survive a
restart.
"""
from __future__ import annotations

import threading
from collections.abc import Iterable

from supersilence.infrastructure.acquisition.uatr_tdm import CHANNEL_COUNT

#: How few elements the array may be reduced to before the console refuses.
#:
#: Not a measured limit — there is no measurement here yet, and this number is
#: a floor on absurdity rather than on accuracy. Three reasons for four:
#: the MDL model order test can only choose an order below the element count,
#: so at two elements it can report at most one source and at one element none
#: at all; the array is three-dimensional, so separating azimuth from elevation
#: needs elements that are not collinear, and any two always are; and the OAS
#: shrinkage target is the scaled identity, which at very small element counts
#: is most of what is left of the covariance.
#:
#: An operator with fewer than four live channels on a unit has a hardware
#: failure to fix, not a setting to adjust. The refusal says so.
MINIMUM_ACTIVE_CHANNELS = 4

DEFAULT_CHANNELS_ENABLED: tuple[bool, ...] = (True,) * CHANNEL_COUNT


def validate_channels_enabled(enabled: Iterable[bool]) -> tuple[bool, ...]:
    """Sixteen flags, checked and returned as plain booleans.

    Integers are refused rather than coerced. A stored ``1`` and a stored
    ``True`` mean the same thing to a person and not to a round trip through
    JSON, and this file is the one place that decides which it was.
    """
    checked = tuple(enabled)
    if len(checked) != CHANNEL_COUNT:
        raise ValueError(
            f"expected {CHANNEL_COUNT} channel enable flags, got {len(checked)}"
        )
    if any(not isinstance(value, bool) for value in checked):
        raise ValueError("channel enable flags must be booleans")
    active = sum(1 for value in checked if value)
    if active < MINIMUM_ACTIVE_CHANNELS:
        raise ValueError(
            f"at least {MINIMUM_ACTIVE_CHANNELS} channels must stay enabled, "
            f"got {active}"
        )
    return checked


def active_channel_indices(enabled: Iterable[bool]) -> tuple[int, ...]:
    """The zero-based channel indices still in the array, in packet order.

    Packet order, not sorted-by-anything-else: this tuple is used to slice both
    the sample matrix and the element positions, and the two must agree column
    for column or every bearing is silently wrong.
    """
    return tuple(index for index, value in enumerate(enabled) if value)


class ChannelEnableStore:
    """Live per-unit channel selection, read by the processing thread.

    Mirrors `ChannelGainStore`: two representations kept side by side rather
    than recomputed on a hot path — the sixteen flags the UI edits, and the
    active-index tuple the pipeline stamps onto every window. Its own lock, and
    the only state it shares with anything.
    """

    def __init__(
        self,
        unit_identifiers: Iterable[int],
        *,
        initial_enabled: dict[int, tuple[bool, ...]] | None = None,
    ) -> None:
        self._lock = threading.Lock()
        self._enabled: dict[int, tuple[bool, ...]] = {}
        self._active: dict[int, tuple[int, ...]] = {}
        initial = initial_enabled or {}
        for unit_identifier in unit_identifiers:
            flags = validate_channels_enabled(
                initial.get(unit_identifier, DEFAULT_CHANNELS_ENABLED)
            )
            self._enabled[unit_identifier] = flags
            self._active[unit_identifier] = active_channel_indices(flags)

    def enabled(self, unit_identifier: int) -> tuple[bool, ...]:
        """One flag per channel, as the Device Status window shows them."""
        with self._lock:
            return self._enabled[unit_identifier]

    def active_channels(self, unit_identifier: int) -> tuple[int, ...]:
        """The channel indices the direction estimators will see."""
        with self._lock:
            return self._active[unit_identifier]

    def set_enabled(
        self, unit_identifier: int, channel_index: int, enabled: bool
    ) -> tuple[bool, ...]:
        """Switch one channel in or out. Takes effect on the unit's next block.

        Returns the unit's full flags afterwards, so a caller that has to
        persist them does not have to read back through the lock and risk
        storing someone else's later edit.
        """
        if not 0 <= channel_index < CHANNEL_COUNT:
            raise ValueError(
                f"channel index must be between 0 and {CHANNEL_COUNT - 1}, "
                f"got {channel_index!r}"
            )
        if not isinstance(enabled, bool):
            raise ValueError("channel enable flag must be a boolean")
        with self._lock:
            current = list(self._enabled[unit_identifier])
            current[channel_index] = enabled
            # Validated inside the lock and before anything is stored, so a
            # refused disable leaves the store exactly as it was.
            updated = validate_channels_enabled(current)
            self._enabled[unit_identifier] = updated
            self._active[unit_identifier] = active_channel_indices(updated)
            return updated
