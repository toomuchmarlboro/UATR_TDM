"""The application-facing surface shared by live acquisition transports."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from supersilence.infrastructure.acquisition.levels import UnitLevels
from supersilence.infrastructure.acquisition.processing import (
    Preprocessor,
    ProcessingWindow,
    RecordingSink,
)
from supersilence.infrastructure.acquisition.raw_samples import RawSampleSink


class LiveAcquisitionService(Protocol):
    @property
    def unit_identifiers(self) -> tuple[int, ...]: ...

    @property
    def running(self) -> bool: ...

    @property
    def receiver_error(self) -> str: ...

    @property
    def supports_hardware_control(self) -> bool: ...

    def start(self) -> bool: ...

    def stop(self) -> None: ...

    def drain_windows(self, unit_identifier: int, maximum_windows: int = 0) -> tuple[ProcessingWindow, ...]: ...

    def levels(self) -> tuple[UnitLevels, ...]: ...

    def health(self) -> tuple[object, ...]: ...

    def channel_gains_db(self, unit_identifier: int) -> tuple[float, ...]: ...

    def set_channel_gain_db(self, unit_identifier: int, channel_index: int, gain_db: float) -> None: ...

    def channels_enabled(self, unit_identifier: int) -> tuple[bool, ...]: ...

    def active_channels(self, unit_identifier: int) -> tuple[int, ...]: ...

    def channel_polarity(self, unit_identifier: int) -> tuple[bool, ...]: ...

    def set_channel_polarity(self, unit_identifier: int, channel_index: int, as_delivered: bool) -> tuple[bool, ...]: ...

    def set_channel_enabled(self, unit_identifier: int, channel_index: int, enabled: bool) -> tuple[bool, ...]: ...

    def set_recording_sink(self, sink: RecordingSink | None) -> None: ...

    def set_pre_dsp_sink(self, sink: RecordingSink | None) -> None: ...

    def set_preprocessor_factory(self, factory: Callable[[int], Preprocessor | None]) -> None: ...

    def set_monitoring_sink(self, sink: RecordingSink | None) -> None: ...

    def set_capture_sink(self, sink: RecordingSink | None) -> None: ...

    def set_raw_sample_sink(self, sink: RawSampleSink | None) -> None: ...


def assert_live_acquisition_surface(service: object) -> None:
    """Fail at composition if a new transport omits an application contract."""
    required = (
        "unit_identifiers",
        "running",
        "receiver_error",
        "supports_hardware_control",
        "start",
        "stop",
        "drain_windows",
        "levels",
        "health",
        "channel_gains_db",
        "set_channel_gain_db",
        "channels_enabled",
        "active_channels",
        "set_channel_enabled",
        "channel_polarity",
        "set_channel_polarity",
        "set_recording_sink",
        "set_pre_dsp_sink",
        "set_preprocessor_factory",
        "set_monitoring_sink",
        "set_capture_sink",
        "set_raw_sample_sink",
    )
    missing = tuple(name for name in required if not hasattr(service, name))
    if missing:
        raise TypeError(f"live acquisition service is missing {', '.join(missing)}")
