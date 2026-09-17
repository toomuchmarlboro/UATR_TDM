"""Which of a unit's sixteen channels arrive with their signal inverted.

A balanced input decides the sign of what it records by which conductor lands on
which pin. Swap the two and the channel is not quieter, not noisier, not
delayed — it is multiplied by minus one, at every frequency, for as long as the
cable stays that way.

Nothing downstream notices on its own. The meters read the same, the recording
sounds the same, and the spectrum is identical. What breaks is direction
finding, because every estimator here compares the sixteen measured channels
against the sixteen a source at some bearing *would* have produced, and that
prediction has all sixteen elements in phase agreement. An inverted element is
half a wavelength of disagreement that no bearing explains, so the measurement
sits off the steering manifold for every direction at once: the peak flattens,
the detection gate refuses, and the console reports nothing while the hardware
is working.

Measured on the 2026-08-27 air captures of unit 1, with three channels inverted:
the share of the measured signal vector that the steering manifold could account
for was 0.31, and correcting only those three signs took it to 0.87. Bearing
error over four known source placements went from 4.64 degrees to 1.54.

This is a **hardware fact to record, not a preference to tune**. The setting
exists because the wiring is what it is; it is not a filter, and turning it on
for a correctly wired channel breaks that channel exactly as thoroughly as the
miswiring would have.

Where it is applied matters, and it is applied **before the recorder sees the
block** — the opposite of how gain is treated, for a reason that does not carry
over from gain. `AcquisitionService` still offers pre-gain blocks to the
recorder, so the operator's knob stays a recorded multiplier the archive can be
read without; but the sign is already in those samples, and the flags it came
from travel beside them into the sidecar as `channel_polarity_applied`.

Three things decide that placement:

- **Nothing is lost.** Multiplying by minus one is exactly invertible and its
  own inverse. This is not the case `channel_enable.py` reasons about, where
  zeroing a dead channel would destroy the only copy of what it heard; a
  polarity call made today can still be revisited against the same water
  tomorrow, by flipping it back.
- **A sidecar that is merely *readable* gets read without.** Any consumer that
  opens the WAV and skips the sidecar — a notebook, a script, another tool —
  gets a silently wrong array rather than an obviously broken one, because an
  inverted channel is not quieter, noisier or delayed. Correct-by-default beats
  correct-if-you-remember for a fact that has exactly one right answer.
- **It stays legible.** The flags are recorded, so the file can always say which
  channels were inverted at capture and what was done about it.
"""

from __future__ import annotations

import threading
from collections.abc import Iterable

import numpy as np

from supersilence.infrastructure.acquisition.uatr_tdm import CHANNEL_COUNT

#: True means "as delivered". False means "this channel arrives inverted, so
#: negate it". The default is every channel as delivered, which is the state of
#: an installation nobody has diagnosed yet — not a claim that the wiring is
#: correct.
DEFAULT_CHANNEL_POLARITY: tuple[bool, ...] = (True,) * CHANNEL_COUNT


def validate_channel_polarity(polarity: Iterable[bool]) -> tuple[bool, ...]:
    """Sixteen flags, checked and returned as plain booleans.

    Integers are refused rather than coerced, for the reason
    `validate_channels_enabled` gives: a stored ``1`` and a stored ``True`` mean
    the same thing to a person and not to a round trip through JSON.

    Unlike the channel enable flags there is no minimum here. Every channel
    being inverted is a legitimate state — it is one connector wired backwards
    at the array end rather than sixteen at the board end — and it is
    indistinguishable from none of them being inverted as far as bearing is
    concerned, since a common sign cancels in every phase difference.
    """
    checked = tuple(polarity)
    if len(checked) != CHANNEL_COUNT:
        raise ValueError(f"expected {CHANNEL_COUNT} channel polarity flags, got {len(checked)}")
    if any(not isinstance(value, bool) for value in checked):
        raise ValueError("channel polarity flags must be booleans")
    return checked


def polarity_signs(polarity: Iterable[bool]) -> np.ndarray:
    """The flags as the ``+1``/``-1`` array the processing thread multiplies by."""
    checked = validate_channel_polarity(polarity)
    signs = np.array([1.0 if value else -1.0 for value in checked], dtype=np.float32)
    signs.setflags(write=False)
    return signs


def inverted_channel_indices(polarity: Iterable[bool]) -> tuple[int, ...]:
    """Zero-based indices of the channels marked inverted, in packet order."""
    return tuple(index for index, value in enumerate(validate_channel_polarity(polarity)) if not value)


class ChannelPolarityStore:
    """Live per-unit channel polarity, read by the processing thread.

    Mirrors `ChannelGainStore` and `ChannelEnableStore`: two representations kept
    side by side rather than recomputed on a hot path — the sixteen flags the
    Device Status window edits, and the sign array the pipeline multiplies by.
    Its own lock, and the only state it shares with anything.
    """

    def __init__(
        self,
        unit_identifiers: Iterable[int],
        *,
        initial_polarity: dict[int, tuple[bool, ...]] | None = None,
    ) -> None:
        self._lock = threading.Lock()
        self._polarity: dict[int, tuple[bool, ...]] = {}
        self._signs: dict[int, np.ndarray] = {}
        initial = initial_polarity or {}
        for unit_identifier in unit_identifiers:
            flags = validate_channel_polarity(initial.get(unit_identifier, DEFAULT_CHANNEL_POLARITY))
            self._polarity[unit_identifier] = flags
            self._signs[unit_identifier] = polarity_signs(flags)

    def polarity(self, unit_identifier: int) -> tuple[bool, ...]:
        """One flag per channel, as the Device Status window shows them."""
        with self._lock:
            return self._polarity[unit_identifier]

    def signs(self, unit_identifier: int) -> np.ndarray:
        """The ``+1``/``-1`` array for this unit's sixteen channels."""
        with self._lock:
            return self._signs[unit_identifier]

    def set_polarity(self, unit_identifier: int, channel_index: int, as_delivered: bool) -> tuple[bool, ...]:
        """Set one channel's polarity. Takes effect on the unit's next block.

        Returns the unit's full flags afterwards, so a caller that has to
        persist them does not have to read back through the lock and risk
        storing someone else's later edit.
        """
        if not 0 <= channel_index < CHANNEL_COUNT:
            raise ValueError(f"channel index must be between 0 and {CHANNEL_COUNT - 1}, got {channel_index!r}")
        if not isinstance(as_delivered, bool):
            raise ValueError("channel polarity flag must be a boolean")
        with self._lock:
            current = list(self._polarity[unit_identifier])
            current[channel_index] = as_delivered
            updated = validate_channel_polarity(current)
            self._polarity[unit_identifier] = updated
            self._signs[unit_identifier] = polarity_signs(updated)
            return updated
