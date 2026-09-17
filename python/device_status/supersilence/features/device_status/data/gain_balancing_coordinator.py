"""Application-facing lifecycle for one controlled gain-balancing capture."""

from __future__ import annotations

from pathlib import Path

from supersilence.features.device_status.data.gain_balancing_capture import (
    CompletedGainCapture,
    GainBalancingCapture,
)


class GainBalancingCoordinator:
    """Attach the bounded capture consumer only while an element is recording."""

    def __init__(self, acquisition_service, root: Path, *, sample_rate: int) -> None:
        self._service = acquisition_service
        self._capture = GainBalancingCapture(root, sample_rate=sample_rate)

    def start(self, unit_identifier: int, channel_index: int, duration_seconds: float) -> Path:
        path = self._capture.start(unit_identifier, channel_index, duration_seconds)
        self._service.set_capture_sink(self._capture.accept)
        return path

    def completed(self) -> CompletedGainCapture | None:
        completed = self._capture.take_completed()
        if completed is not None:
            self._service.set_capture_sink(None)
        return completed

    def cancel(self) -> None:
        self._service.set_capture_sink(None)
        self._capture.cancel()
