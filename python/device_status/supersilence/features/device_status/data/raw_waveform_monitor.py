"""Bounded, thread-safe retention of live or replay waveform samples."""

from __future__ import annotations

import threading
from dataclasses import dataclass

import numpy as np

from supersilence.features.device_status.domain.raw_waveforms import (
    ELEMENT_COUNT,
    validate_element_to_channel,
)
from supersilence.infrastructure.acquisition.raw_samples import RawSampleBlock
from supersilence.infrastructure.acquisition.uatr_tdm import SAMPLE_RATE

DISPLAY_WINDOW_SECONDS = 0.05
DEFAULT_RETAINED_FRAMES = int(round(SAMPLE_RATE * DISPLAY_WINDOW_SECONDS))
LIVE_SOURCE_DESCRIPTION = "Live native device samples · x-axis: sample index · no gain, polarity correction, filtering or estimator processing"
REPLAY_SOURCE_DESCRIPTION = "Replay archive samples · 24 kHz · pre-gain · recorded polarity · before configurable filtering and estimator processing"


@dataclass(frozen=True)
class RawWaveformSnapshot:
    unit_identifier: int
    samples: np.ndarray


class RawWaveformMonitor:
    """Attach one raw observer and retain only each unit's newest frames."""

    def __init__(
        self,
        acquisition_service,
        element_to_channel,
        *,
        maximum_frames: int = DEFAULT_RETAINED_FRAMES,
        unit_identifiers=None,
        source_description: str = LIVE_SOURCE_DESCRIPTION,
        polarity_already_applied: bool = False,
    ) -> None:
        if maximum_frames <= 0:
            raise ValueError("maximum retained frames must be positive")
        self._service = acquisition_service
        self._unit_identifiers = tuple(getattr(acquisition_service, "unit_identifiers", ()) if unit_identifiers is None else unit_identifiers)
        self._source_description = source_description
        self._polarity_already_applied = bool(polarity_already_applied)
        self._source_revision = int(getattr(acquisition_service, "raw_sample_revision", 0))
        self._source_generation = 0
        self._sink = self._sink_for(self._source_generation)
        self._element_to_channel = validate_element_to_channel(element_to_channel)
        self._maximum_frames = maximum_frames
        self._samples: dict[int, np.ndarray] = {}
        self._lock = threading.Lock()
        self._running = False

    @property
    def running(self) -> bool:
        with self._lock:
            return self._running

    @property
    def unit_identifiers(self) -> tuple[int, ...]:
        with self._lock:
            return self._unit_identifiers

    @property
    def source_description(self) -> str:
        with self._lock:
            return self._source_description

    @property
    def polarity_already_applied(self) -> bool:
        with self._lock:
            return self._polarity_already_applied

    def start(self) -> None:
        with self._lock:
            if self._running:
                return
            self._running = True
            service = self._service
            sink = self._sink
        service.set_raw_sample_sink(sink)

    def stop(self) -> None:
        with self._lock:
            service = self._service
            self._running = False
            self._samples.clear()
        service.set_raw_sample_sink(None)

    def replace_source(
        self,
        service,
        *,
        unit_identifiers=None,
        source_description: str,
        polarity_already_applied: bool = False,
    ) -> None:
        """Switch waveform input without retaining or accepting the old source."""
        with self._lock:
            previous = self._service
            running = self._running
            self._source_generation += 1
            self._service = service
            self._unit_identifiers = tuple(getattr(service, "unit_identifiers", ()) if unit_identifiers is None else unit_identifiers)
            self._source_description = source_description
            self._polarity_already_applied = bool(polarity_already_applied)
            self._source_revision = int(getattr(service, "raw_sample_revision", 0))
            self._sink = self._sink_for(self._source_generation)
            sink = self._sink
            self._samples.clear()
        if running:
            previous.set_raw_sample_sink(None)
            service.set_raw_sample_sink(sink)

    def snapshot(self, unit_identifier: int) -> RawWaveformSnapshot:
        revision = int(getattr(self._service, "raw_sample_revision", 0))
        with self._lock:
            if revision != self._source_revision:
                self._source_revision = revision
                self._samples.clear()
            values = self._samples.get(unit_identifier)
            if values is None:
                values = np.empty((0, ELEMENT_COUNT), dtype=np.float32)
            else:
                values = values.copy()
        values.setflags(write=False)
        return RawWaveformSnapshot(unit_identifier, values)

    def _sink_for(self, generation: int):
        return lambda block: self._accept(block, generation)

    def _accept(self, block: RawSampleBlock, generation: int) -> None:
        reordered = np.asarray(block.samples[:, self._element_to_channel])
        with self._lock:
            if not self._running or generation != self._source_generation:
                return
            previous = None if block.discontinuous else self._samples.get(block.unit_identifier)
            if previous is None or reordered.shape[0] >= self._maximum_frames:
                combined = reordered[-self._maximum_frames :].copy()
            else:
                keep_previous = self._maximum_frames - reordered.shape[0]
                combined = np.concatenate((previous[-keep_previous:], reordered), axis=0)[-self._maximum_frames :]
            combined.setflags(write=False)
            self._samples[block.unit_identifier] = combined


__all__ = [
    "DEFAULT_RETAINED_FRAMES",
    "DISPLAY_WINDOW_SECONDS",
    "LIVE_SOURCE_DESCRIPTION",
    "REPLAY_SOURCE_DESCRIPTION",
    "RawWaveformMonitor",
    "RawWaveformSnapshot",
]
