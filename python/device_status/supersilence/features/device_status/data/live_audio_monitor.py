"""Exclusive live Hear control for the Device Status Buoys pages."""

from __future__ import annotations

import threading
from dataclasses import dataclass

import numpy as np
from PySide6.QtCore import QObject, Signal

from supersilence.features.device_status.data.audio_output import DefaultAudioOutput
from supersilence.features.device_status.domain.audio_monitor import (
    MonoMonitorConditioner,
)
from supersilence.infrastructure.acquisition.uatr_tdm import (
    CHANNEL_COUNT,
    SampleQuality,
)

PLAYABLE_QUALITY = frozenset((SampleQuality.RECEIVED, SampleQuality.INTERPOLATED))


@dataclass(frozen=True)
class HeardChannel:
    """The only fleet channel currently routed to the system speaker."""

    unit_identifier: int
    channel_index: int


class LiveAudioMonitor(QObject):
    """Own one speaker route without owning or consuming acquisition."""

    selection_changed = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        acquisition_service,
        parent: QObject | None = None,
        *,
        output=None,
    ) -> None:
        super().__init__(parent)
        self._acquisition_service = acquisition_service
        self._output = output or DefaultAudioOutput(self)
        self._output.failed.connect(self._on_output_failure)
        self._conditioner = MonoMonitorConditioner(CHANNEL_COUNT)
        self._selection: HeardChannel | None = None
        # Acquisition delivers blocks on its processing thread while selection
        # and close happen on the Qt thread. Holding this lock across the cheap
        # conversion/copy makes stop a hard boundary: after it returns, no old
        # callback can refill the deactivated output buffer.
        self._lock = threading.Lock()

    @property
    def selection(self) -> HeardChannel | None:
        with self._lock:
            return self._selection

    def toggle(self, unit_identifier: int, channel_index: int) -> bool:
        """Hear this channel, or mute it when it is already selected."""
        requested = HeardChannel(unit_identifier, channel_index)
        self._validate(requested)
        if self.selection == requested:
            self.stop()
            return False

        self.stop()
        try:
            self._output.start()
        except RuntimeError as error:
            self.failed.emit(str(error))
            return False
        with self._lock:
            self._selection = requested
            self._conditioner.reset()
            self._output.reset()
        self._acquisition_service.set_monitoring_sink(self._accept_block)
        self.selection_changed.emit(requested)
        return True

    def stop(self) -> None:
        """Detach first, then make the current output synchronously silent."""
        self._acquisition_service.set_monitoring_sink(None)
        with self._lock:
            was_selected = self._selection is not None
            self._selection = None
            self._output.stop()
        if was_selected:
            self.selection_changed.emit(None)

    def _accept_block(self, unit_identifier: int, block, multipliers, signs=None) -> None:
        """Condition only the selected channel and copy it to the bounded ring.

        The signs are accepted and ignored: the block already carries them, and
        a channel played back inverted sounds exactly like one that is not.
        """
        with self._lock:
            selection = self._selection
            if selection is None or selection.unit_identifier != unit_identifier:
                return
            if any(quality is SampleQuality.DISCONTINUOUS for quality in block.quality):
                self._conditioner.reset()
                self._output.reset()
            playable = np.fromiter(
                (quality in PLAYABLE_QUALITY for quality in block.quality),
                dtype=bool,
                count=len(block.quality),
            )
            gain_values = np.asarray(multipliers, dtype=np.float64)
            if gain_values.shape != (CHANNEL_COUNT,):
                raise ValueError(f"monitor gain must have shape ({CHANNEL_COUNT},), got {gain_values.shape}")
            mono = self._conditioner.condition(
                block.samples,
                selection.channel_index,
                float(gain_values[selection.channel_index]),
                playable=playable,
            )
            self._output.write(mono)

    def _validate(self, requested: HeardChannel) -> None:
        if requested.unit_identifier not in self._acquisition_service.unit_identifiers:
            raise ValueError(f"unit {requested.unit_identifier} has no live acquisition")
        if not 0 <= requested.channel_index < CHANNEL_COUNT:
            raise ValueError(f"channel index {requested.channel_index} is out of range")

    def _on_output_failure(self, message: str) -> None:
        self.stop()
        self.failed.emit(message)
