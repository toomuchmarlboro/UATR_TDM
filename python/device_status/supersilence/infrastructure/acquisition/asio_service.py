"""Application lifecycle and common processing surface for one ASIO unit."""

from __future__ import annotations

import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass

from supersilence.infrastructure.acquisition.asio import AsioInputAdapter
from supersilence.infrastructure.acquisition.asio_processing import AsioRateConverter
from supersilence.infrastructure.acquisition.channel_enable import ChannelEnableStore
from supersilence.infrastructure.acquisition.channel_polarity import (
    ChannelPolarityStore,
)
from supersilence.infrastructure.acquisition.configuration import AcquisitionConfiguration
from supersilence.infrastructure.acquisition.gain import ChannelGainStore
from supersilence.infrastructure.acquisition.levels import ChannelLevelMeter, UnitLevels
from supersilence.infrastructure.acquisition.processing import (
    DecimatedBlock,
    Preprocessor,
    ProcessingWindow,
    RecordingSink,
    UnitProcessingPipeline,
)
from supersilence.infrastructure.acquisition.raw_samples import (
    RawSampleBlock,
    RawSampleSink,
)


@dataclass(frozen=True)
class AsioAcquisitionHealth:
    unit_identifier: int
    source: str
    device_name: str
    host_api: str
    input_sample_rate: int
    callback_faults: int
    dropped_input_blocks: int
    queued_windows: int
    window_queue_overflow_windows: int
    last_callback_status: str
    receiver_error: str


class AsioAcquisitionService:
    """Feed one configured unit through the same post-decimation contract."""

    def __init__(
        self,
        configuration: AcquisitionConfiguration,
        *,
        input_factory: Callable[[AcquisitionConfiguration], AsioInputAdapter] = (AsioInputAdapter),
        clock: Callable[[], float] = time.monotonic,
        maximum_windows: int = 8,
        initial_gains_db: dict[int, tuple[float, ...]] | None = None,
        initial_channels_enabled: dict[int, tuple[bool, ...]] | None = None,
        initial_channel_polarity: dict[int, tuple[bool, ...]] | None = None,
    ) -> None:
        if maximum_windows <= 0:
            raise ValueError("maximum ASIO windows must be positive")
        self._configuration = configuration
        self._input_factory = input_factory
        self._clock = clock
        self._input: AsioInputAdapter | None = None
        self._converter: AsioRateConverter | None = None
        self._stop = threading.Event()
        self._worker: threading.Thread | None = None
        self._lock = threading.Lock()
        self._windows: deque[ProcessingWindow] = deque(maxlen=maximum_windows)
        self._window_overflow = 0
        self._startup_error = ""
        self._processing_error = ""
        self._recording_sink: RecordingSink | None = None
        self._pre_dsp_sink: RecordingSink | None = None
        self._recording_error: str | None = None
        self._monitoring_sink: RecordingSink | None = None
        self._capture_sink: RecordingSink | None = None
        self._monitoring_error: str | None = None
        self._capture_error: str | None = None
        self._raw_sample_sink: RawSampleSink | None = None
        self._raw_sample_error: str | None = None
        self._gain_store = ChannelGainStore(self.unit_identifiers, initial_gains_db=initial_gains_db)
        self._channel_enable_store = ChannelEnableStore(self.unit_identifiers, initial_enabled=initial_channels_enabled)
        self._channel_polarity_store = ChannelPolarityStore(self.unit_identifiers, initial_polarity=initial_channel_polarity)
        self._level_meter = ChannelLevelMeter(self.unit_identifiers[0], full_scale=1.0)
        self._processor = self._new_processor()

    @property
    def unit_identifiers(self) -> tuple[int, ...]:
        return self._configuration.active_unit_identifiers

    @property
    def running(self) -> bool:
        input_running = bool(self._input is not None and self._input.running)
        worker_running = bool(self._worker is not None and self._worker.is_alive())
        return input_running and worker_running

    @property
    def supports_hardware_control(self) -> bool:
        """ASIO has no path to the UATR board's network control endpoint."""
        return False

    @property
    def receiver_error(self) -> str:
        return self._startup_error or self._processing_error

    def start(self) -> bool:
        if self.running:
            return True
        if self._input is not None or self._worker is not None:
            self.stop()
        candidate = self._input_factory(self._configuration)
        try:
            candidate.start()
            converter = AsioRateConverter(candidate.sample_rate)
        except Exception as error:
            try:
                candidate.stop()
            except Exception:
                pass
            self._startup_error = str(error)
            return False
        self._input = candidate
        self._converter = converter
        self._startup_error = ""
        self._processing_error = ""
        self._stop.clear()
        with self._lock:
            self._windows.clear()
            self._window_overflow = 0
            self._level_meter = ChannelLevelMeter(self.unit_identifiers[0], full_scale=1.0)
        self._processor = self._new_processor()
        self._worker = threading.Thread(
            target=self._process,
            name="asio-acquisition-processing",
            daemon=True,
        )
        self._worker.start()
        return True

    def stop(self) -> None:
        self._stop.set()
        input_adapter, self._input = self._input, None
        if input_adapter is not None:
            input_adapter.stop()
        worker, self._worker = self._worker, None
        if worker is not None and worker.is_alive():
            worker.join(timeout=1.0)
        self._converter = None

    def drain_windows(self, unit_identifier: int, maximum_windows: int = 0) -> tuple[ProcessingWindow, ...]:
        if unit_identifier not in self.unit_identifiers:
            return ()
        with self._lock:
            count = len(self._windows)
            if maximum_windows > 0:
                count = min(count, maximum_windows)
            return tuple(self._windows.popleft() for _ in range(count))

    def levels(self) -> tuple[UnitLevels, ...]:
        with self._lock:
            return (self._level_meter.snapshot(),)

    def health(self) -> tuple[AsioAcquisitionHealth, ...]:
        input_adapter = self._input
        device = None if input_adapter is None else input_adapter.device
        with self._lock:
            queued_windows = len(self._windows)
            overflow = self._window_overflow
        return (
            AsioAcquisitionHealth(
                self.unit_identifiers[0],
                "asio",
                self._configuration.asio_device_name if device is None else device.name,
                self._configuration.asio_host_api if device is None else device.host_api,
                0 if input_adapter is None else input_adapter.sample_rate,
                0 if input_adapter is None else input_adapter.callback_faults,
                0 if input_adapter is None else input_adapter.dropped_blocks,
                queued_windows,
                overflow,
                "" if input_adapter is None else input_adapter.last_callback_status,
                self.receiver_error,
            ),
        )

    def channel_gains_db(self, unit_identifier: int) -> tuple[float, ...]:
        return self._gain_store.gains_db(unit_identifier)

    def set_channel_gain_db(self, unit_identifier: int, channel_index: int, gain_db: float) -> None:
        self._gain_store.set_gain_db(unit_identifier, channel_index, gain_db)

    def channels_enabled(self, unit_identifier: int) -> tuple[bool, ...]:
        return self._channel_enable_store.enabled(unit_identifier)

    def active_channels(self, unit_identifier: int) -> tuple[int, ...]:
        return self._channel_enable_store.active_channels(unit_identifier)

    def set_channel_enabled(self, unit_identifier: int, channel_index: int, enabled: bool) -> tuple[bool, ...]:
        return self._channel_enable_store.set_enabled(unit_identifier, channel_index, enabled)

    def channel_polarity(self, unit_identifier: int) -> tuple[bool, ...]:
        return self._channel_polarity_store.polarity(unit_identifier)

    def set_channel_polarity(self, unit_identifier: int, channel_index: int, as_delivered: bool) -> tuple[bool, ...]:
        return self._channel_polarity_store.set_polarity(unit_identifier, channel_index, as_delivered)

    def set_recording_sink(self, sink: RecordingSink | None) -> None:
        with self._lock:
            self._recording_sink = sink
            if sink is not None:
                self._recording_error = None

    def set_pre_dsp_sink(self, sink: RecordingSink | None) -> None:
        with self._lock:
            self._pre_dsp_sink = sink
            self._processor.replace_pre_dsp_sink(sink)

    def set_preprocessor_factory(self, factory: Callable[[int], Preprocessor | None]) -> None:
        with self._lock:
            self._processor.replace_preprocessor(factory(self.unit_identifiers[0]))

    def set_monitoring_sink(self, sink: RecordingSink | None) -> None:
        with self._lock:
            self._monitoring_sink = sink

    def set_capture_sink(self, sink: RecordingSink | None) -> None:
        with self._lock:
            self._capture_sink = sink
            if sink is not None:
                self._capture_error = None

    def set_raw_sample_sink(self, sink: RawSampleSink | None) -> None:
        """Attach one observer before ASIO rate conversion or common DSP."""
        with self._lock:
            self._raw_sample_sink = sink
            if sink is not None:
                self._raw_sample_error = None

    @property
    def raw_sample_error(self) -> str | None:
        with self._lock:
            return self._raw_sample_error

    @property
    def recording_error(self) -> str | None:
        with self._lock:
            return self._recording_error

    @property
    def monitoring_error(self) -> str | None:
        with self._lock:
            return self._monitoring_error

    def _new_processor(self) -> UnitProcessingPipeline:
        unit_identifier = self.unit_identifiers[0]
        return UnitProcessingPipeline(
            unit_identifier,
            clock=self._clock,
            gain_source=lambda: self._gain_store.multipliers(unit_identifier),
            polarity_source=lambda: self._channel_polarity_store.signs(unit_identifier),
            active_channels_source=lambda: self._channel_enable_store.active_channels(unit_identifier),
            recording_sink=self._offer_to_sinks,
            pre_dsp_sink=self._pre_dsp_sink,
        )

    def _process(self) -> None:
        try:
            while not self._stop.is_set():
                input_adapter = self._input
                converter = self._converter
                if input_adapter is None or converter is None:
                    return
                blocks = input_adapter.drain_blocks()
                if not blocks:
                    self._stop.wait(0.001)
                    continue
                for block in blocks:
                    self._offer_raw_samples(block)
                    with self._lock:
                        self._level_meter.update(block.samples, self._clock())
                    for decimated in converter.process(block.samples, force_discontinuity=block.discontinuous):
                        self._publish(self._processor.process_decimated(decimated))
        except Exception as error:
            self._processing_error = str(error)

    def _offer_raw_samples(self, block) -> None:
        with self._lock:
            sink = self._raw_sample_sink
        if sink is None:
            return
        try:
            sink(RawSampleBlock(self.unit_identifiers[0], block.samples, block.discontinuous))
        except Exception as error:
            with self._lock:
                if self._raw_sample_sink is sink:
                    self._raw_sample_sink = None
                    self._raw_sample_error = str(error)

    def _publish(self, windows: tuple[ProcessingWindow, ...]) -> None:
        with self._lock:
            for window in windows:
                if len(self._windows) == self._windows.maxlen:
                    self._window_overflow += 1
                self._windows.append(window)

    def _offer_to_sinks(self, unit_identifier: int, block: DecimatedBlock, multipliers, signs) -> None:
        with self._lock:
            recording = self._recording_sink
            monitoring = self._monitoring_sink
            capture = self._capture_sink
        self._offer(
            "_recording_sink",
            "_recording_error",
            recording,
            unit_identifier,
            block,
            multipliers,
            signs,
        )
        self._offer(
            "_monitoring_sink",
            "_monitoring_error",
            monitoring,
            unit_identifier,
            block,
            multipliers,
            signs,
        )
        self._offer(
            "_capture_sink",
            "_capture_error",
            capture,
            unit_identifier,
            block,
            multipliers,
            signs,
        )

    def _offer(
        self,
        sink_attribute: str,
        error_attribute: str,
        sink: RecordingSink | None,
        unit_identifier: int,
        block: DecimatedBlock,
        multipliers,
        signs,
    ) -> None:
        if sink is None:
            return
        try:
            sink(unit_identifier, block, multipliers, signs)
        except Exception as error:
            with self._lock:
                if getattr(self, sink_attribute) is sink:
                    setattr(self, sink_attribute, None)
                    setattr(self, error_attribute, str(error))
