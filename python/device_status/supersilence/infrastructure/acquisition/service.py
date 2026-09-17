"""Application-owned acquisition consumption, lifecycle, and health."""

from __future__ import annotations

import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from itertools import chain

import numpy as np

from supersilence.infrastructure.acquisition.channel_enable import ChannelEnableStore
from supersilence.infrastructure.acquisition.channel_polarity import (
    ChannelPolarityStore,
)
from supersilence.infrastructure.acquisition.configuration import (
    AcquisitionConfiguration,
)
from supersilence.infrastructure.acquisition.decimation import DecimatedBlock
from supersilence.infrastructure.acquisition.gain import ChannelGainStore
from supersilence.infrastructure.acquisition.levels import (
    ChannelLevelMeter,
    UnitLevels,
)
from supersilence.infrastructure.acquisition.processing import (
    Preprocessor,
    ProcessingWindow,
    RecordingSink,
    UnitProcessingPipeline,
)
from supersilence.infrastructure.acquisition.raw_samples import (
    RawSampleBlock,
    RawSampleSink,
)
from supersilence.infrastructure.acquisition.receiver import (
    MultiUnitUdpReceiver,
    ReceiverStatus,
    UnitReceiverSnapshot,
)
from supersilence.infrastructure.acquisition.samples import (
    OrderedSampleAssembler,
    SampleBlock,
)
from supersilence.infrastructure.acquisition.uatr_tdm import (
    PhantomPowerReadback,
    decode_phantom_power,
    decode_sample_blob,
)


@dataclass(frozen=True)
class AcquisitionUnitHealth:
    unit_identifier: int
    source_address: str
    packet_rate: float
    packet_age_seconds: float | None
    received_packets: int
    accepted_packets: int
    lost_packets: int
    sequence_restarts: int
    invalid_packets: int
    duplicate_packets: int
    out_of_order_packets: int
    queue_overflow_packets: int
    queued_packets: int
    sample_queue_overflow_blocks: int
    queued_sample_blocks: int
    window_queue_overflow_windows: int
    queued_windows: int
    unknown_source_packets: int
    receiver_error: str
    #: The receive buffer the kernel granted, shared by every unit on the one
    #: socket. Zero when the receiver is not running.
    receive_buffer_bytes: int = 0
    #: What was asked for. A kernel that cannot honour the request grants less
    #: without saying so, and the difference is a burst-loss cause the operator
    #: has no other way to see. Zero when the receiver is not running.
    requested_receive_buffer_bytes: int = 0
    #: Bytes the kernel is still holding for this unit. Packet age is only
    #: trustworthy while this is small — see `UnitReceiverSnapshot`.
    receive_backlog_bytes: int = 0
    #: That backlog as time, at the rate this unit's own thread is draining it.
    receive_backlog_seconds: float = 0.0
    #: Datagrams the kernel dropped on this unit's own socket, read from the
    #: kernel's table rather than inferred. It splits `lost_packets` into the
    #: two faults that need different fixes: what this host had and did not
    #: read, and what never arrived. `None` where the kernel does not publish
    #: it, which is anything that is not Linux.
    kernel_dropped_packets: int | None = None
    #: What this unit's board says it is doing with 48 V, decoded from the
    #: status byte in every audio packet. `None` where there is no answer: the
    #: unit has sent nothing since the last start, or it is running a bitstream
    #: older than the readback. Never inferred from what the console last
    #: commanded — the whole value of this field is that it is the board's
    #: word and not the console's.
    phantom_power: PhantomPowerReadback | None = None


class AcquisitionService:
    """Drain raw receivers through bounded per-unit processing stages."""

    def __init__(
        self,
        configuration: AcquisitionConfiguration,
        *,
        receiver_factory: Callable[..., MultiUnitUdpReceiver] = MultiUnitUdpReceiver,
        clock: Callable[[], float] = time.monotonic,
        maximum_sample_blocks_per_unit: int = 128,
        maximum_windows_per_unit: int = 8,
        consumer_batch_packets: int = 512,
        processing_factory: Callable[[int], UnitProcessingPipeline] | None = None,
        initial_gains_db: dict[int, tuple[float, ...]] | None = None,
        initial_channels_enabled: dict[int, tuple[bool, ...]] | None = None,
        initial_channel_polarity: dict[int, tuple[bool, ...]] | None = None,
    ) -> None:
        if maximum_sample_blocks_per_unit <= 0:
            raise ValueError("maximum sample blocks per unit must be positive")
        if consumer_batch_packets <= 0:
            raise ValueError("consumer batch packets must be positive")
        if maximum_windows_per_unit <= 0:
            raise ValueError("maximum windows per unit must be positive")
        self._configuration = configuration
        self._receiver_factory = receiver_factory
        self._clock = clock
        self._consumer_batch_packets = consumer_batch_packets
        self._processing_factory = processing_factory
        # Built before `_new_processors()` runs, and never rebuilt by a restart:
        # gain is an operator setting, not per-connection state, and a restart
        # must not silently zero out what the operator dialled in.
        self._gain_store = ChannelGainStore(self.unit_identifiers, initial_gains_db=initial_gains_db)
        # Same reasoning, and the same lifetime: a channel switched out because
        # its hydrophone is flooded is still flooded after a restart, so this
        # is built once and survives `_reset_processing_state`.
        self._channel_enable_store = ChannelEnableStore(self.unit_identifiers, initial_enabled=initial_channels_enabled)
        # Same lifetime again, and the strongest case of the three: a cable
        # wired with pin 2 and pin 3 swapped is still swapped after a restart.
        self._channel_polarity_store = ChannelPolarityStore(self.unit_identifiers, initial_polarity=initial_channel_polarity)
        self._recording_sink: RecordingSink | None = None
        self._pre_dsp_sink: RecordingSink | None = None
        self._recording_error: str | None = None
        # Live speaker monitoring consumes the same pre-gain decimated block as
        # recording but has an independent lifecycle and failure state. A bad
        # output device must never detach an active archive, or vice versa.
        self._monitoring_sink: RecordingSink | None = None
        self._monitoring_error: str | None = None
        # A bounded diagnostic capture is another independently-owned consumer
        # of pre-gain samples.  It must not replace an operator's archive or
        # speaker monitor merely because a calibration is under way.
        self._capture_sink: RecordingSink | None = None
        self._capture_error: str | None = None
        # The waveform inspector receives decoded packet values before the
        # ordered assembler can bridge gaps and before normalization or DSP.
        self._raw_sample_sink: RawSampleSink | None = None
        self._raw_sample_error: str | None = None
        self._raw_expected_sequence: dict[int, int | None] = dict.fromkeys(self.unit_identifiers, None)
        self._receiver: MultiUnitUdpReceiver | None = None
        self._consumer_thread: threading.Thread | None = None
        self._processing_thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._assemblers = self._new_assemblers()
        self._processing_blocks = {unit_identifier: deque(maxlen=maximum_sample_blocks_per_unit) for unit_identifier in self.unit_identifiers}
        self._windows = {unit_identifier: deque(maxlen=maximum_windows_per_unit) for unit_identifier in self.unit_identifiers}
        self._processors = self._new_processors()
        self._decoded_invalid = dict.fromkeys(self.unit_identifiers, 0)
        self._sample_queue_overflow = dict.fromkeys(self.unit_identifiers, 0)
        self._window_queue_overflow = dict.fromkeys(self.unit_identifiers, 0)
        self._processing_discontinuity_pending = dict.fromkeys(self.unit_identifiers, False)
        self._level_meters = {unit_identifier: ChannelLevelMeter(unit_identifier) for unit_identifier in self.unit_identifiers}
        self._phantom_power: dict[int, PhantomPowerReadback | None] = dict.fromkeys(self.unit_identifiers, None)
        self._last_poll: float | None = None
        self._last_received: dict[int, int] = {}
        self._startup_error = ""
        self._processing_error = ""

    @property
    def running(self) -> bool:
        receiver_running = bool(self._receiver is not None and self._receiver.running)
        consumer_running = bool(self._consumer_thread is not None and self._consumer_thread.is_alive())
        processing_running = bool(self._processing_thread is not None and self._processing_thread.is_alive())
        return receiver_running and consumer_running and processing_running

    @property
    def supports_hardware_control(self) -> bool:
        """Ethernet acquisition can address each UATR board directly."""
        return True

    @property
    def ports(self) -> dict[int, int]:
        """The configured or currently bound receiver port, per unit.

        Only the deployed fleet: a buoy switched off on the Acquisition page has
        a stored port and no socket, and reporting it here would have the console
        describe a binding that does not exist.
        """
        if self._receiver is None:
            return {unit_identifier: port for unit_identifier, port in self._configuration.ports.items() if unit_identifier in self.unit_identifiers}
        return self._receiver.ports

    def port_for(self, unit_identifier: int) -> int:
        return self.ports[unit_identifier]

    @property
    def unit_identifiers(self) -> tuple[int, ...]:
        """The buoys this console is deployed with, smallest identifier first.

        The stored fleet is always four; this is the part of it the operator says
        is in the water. Everything downstream sizes itself from this — the
        receiver's sockets, the per-unit pipelines, the fleet epoch's roll call,
        the buoy menu — so switching a unit off removes it from the console
        rather than leaving it reported as a unit that has gone quiet.
        """
        return self._configuration.active_unit_identifiers

    def start(self) -> bool:
        """Start acquisition, returning false while preserving an offline error state."""
        if self.running:
            return True
        if self._receiver is not None or self._consumer_thread is not None or self._processing_thread is not None:
            self.stop()
        deployed = set(self.unit_identifiers)
        receiver = self._receiver_factory(
            self._configuration.bind_address,
            {unit_identifier: port for unit_identifier, port in self._configuration.ports.items() if unit_identifier in deployed},
            {address: unit_identifier for unit_identifier, address in self._configuration.source_addresses.items() if unit_identifier in deployed},
            receive_buffer_bytes=self._configuration.receive_buffer_bytes,
            # The staging cap is the operator's, in the same window as the
            # receive buffer, because it is the same trade one layer up: staged
            # audio the consumer has not reached is tolerance of a stall bought
            # with memory and staleness. A restart rebuilds the receiver, so a
            # changed setting reaches it here and nowhere else.
            maximum_packets_per_unit=self._configuration.staging_packets_per_unit,
        )
        try:
            receiver.start()
        except OSError as error:
            receiver.stop()
            self._startup_error = str(error)
            return False

        self._receiver = receiver
        self._startup_error = ""
        self._processing_error = ""
        self._reset_processing_state()
        self._stop.clear()
        self._last_poll = self._clock()
        self._last_received = dict.fromkeys(self.unit_identifiers, 0)
        self._consumer_thread = threading.Thread(
            target=self._consume,
            daemon=True,
            name="acquisition-consumer",
        )
        self._processing_thread = threading.Thread(
            target=self._process,
            daemon=True,
            name="acquisition-processing",
        )
        self._consumer_thread.start()
        self._processing_thread.start()
        return True

    def stop(self) -> None:
        self._stop.set()
        receiver, self._receiver = self._receiver, None
        if receiver is not None:
            receiver.stop()
        consumer, self._consumer_thread = self._consumer_thread, None
        if consumer is not None and consumer.is_alive():
            consumer.join(timeout=1.0)
        processing, self._processing_thread = self._processing_thread, None
        if processing is not None and processing.is_alive():
            processing.join(timeout=1.0)
        self._last_poll = None
        self._last_received = {}
        with self._lock:
            self._phantom_power = dict.fromkeys(self.unit_identifiers, None)

    def drain_windows(self, unit_identifier: int, maximum_windows: int = 0) -> tuple[ProcessingWindow, ...]:
        """Return completed DSP windows without blocking upstream processing."""
        windows = self._windows[unit_identifier]
        with self._lock:
            count = len(windows)
            if maximum_windows > 0:
                count = min(count, maximum_windows)
            return tuple(windows.popleft() for _ in range(count))

    def levels(self) -> tuple[UnitLevels, ...]:
        """Per-channel signal levels for every unit, newest measurement.

        Snapshots are taken under the same lock the processing thread writes
        under: a half-updated meter would show one channel from this block and
        fifteen from the last.
        """
        with self._lock:
            return tuple(self._level_meters[unit_identifier].snapshot() for unit_identifier in self.unit_identifiers)

    def health(self) -> tuple[AcquisitionUnitHealth, ...]:
        now = self._clock()
        previous_poll = self._last_poll
        elapsed = max(now - previous_poll, 1e-9) if previous_poll is not None else 1.0
        receiver = self._receiver
        if receiver is None:
            status = ReceiverStatus(0, self.receiver_error, 0, 0)
            snapshots = tuple(self._offline_snapshot(unit) for unit in self.unit_identifiers)
        else:
            status = receiver.status()
            snapshots = receiver.snapshots()
        result = tuple(self._health(snapshot, status, elapsed, now) for snapshot in snapshots)
        self._last_poll = now
        return result

    @property
    def receiver_error(self) -> str:
        if self._startup_error:
            return self._startup_error
        if self._processing_error:
            return self._processing_error
        if self._receiver is not None:
            return self._receiver.status().last_error
        return ""

    def _consume(self) -> None:
        try:
            while not self._stop.is_set():
                consumed = False
                receiver = self._receiver
                if receiver is None:
                    return
                for unit_identifier in self.unit_identifiers:
                    blob, packet_count = receiver.drain_blob(unit_identifier, self._consumer_batch_packets)
                    if not packet_count:
                        continue
                    consumed = True
                    self._consume_payloads(unit_identifier, blob, packet_count)
                if not consumed:
                    self._stop.wait(0.001)
        except Exception as error:  # keep the receiver alive and make failure visible
            self._processing_error = str(error)

    def _process(self) -> None:
        try:
            while not self._stop.is_set():
                for unit_identifier in self.unit_identifiers:
                    with self._lock:
                        queue = self._processing_blocks[unit_identifier]
                        if not queue:
                            continue
                        blocks = tuple(queue)
                        queue.clear()
                        force_discontinuity = self._processing_discontinuity_pending[unit_identifier]
                        self._processing_discontinuity_pending[unit_identifier] = False
                    block = self._combine_blocks(blocks)
                    # Metered here, on the assembled block before normalization, so
                    # the operator sees the true 24 kHz channel and nothing has
                    # to consume the sample stream a second time.
                    with self._lock:
                        self._level_meters[unit_identifier].update(block.samples, self._clock())
                    windows = self._processors[unit_identifier].process(block, force_discontinuity=force_discontinuity)
                    if windows:
                        self._publish_windows(unit_identifier, windows)
                # Acquisition arrives in small receiver flushes. A short yield lets
                # those flushes coalesce and prevents DSP bookkeeping from competing
                # with the UDP receive thread for every packet-sized fragment.
                self._stop.wait(0.001)
        except Exception as error:  # keep reception alive and expose DSP failure
            self._processing_error = str(error)

    def _new_assemblers(self) -> dict[int, OrderedSampleAssembler]:
        """One assembler per unit, all on the operator's bridging limit.

        Built in one place because a restart rebuilds them, and an assembler
        rebuilt with a different limit from the one it started on would change
        what counts as a hole without anything saying so.
        """
        return {
            unit_identifier: OrderedSampleAssembler(maximum_interpolated_packets=(self._configuration.maximum_interpolated_packets))
            for unit_identifier in self.unit_identifiers
        }

    def _reset_processing_state(self) -> None:
        self._assemblers = self._new_assemblers()
        self._processors = self._new_processors()
        with self._lock:
            # A restart is a new deployment as far as the meters are concerned:
            # holding a peak from before it would describe a signal path that is
            # no longer the one being watched.
            self._level_meters = {unit_identifier: ChannelLevelMeter(unit_identifier) for unit_identifier in self.unit_identifiers}
            for queue in self._processing_blocks.values():
                queue.clear()
            for queue in self._windows.values():
                queue.clear()
            self._decoded_invalid = dict.fromkeys(self.unit_identifiers, 0)
            self._sample_queue_overflow = dict.fromkeys(self.unit_identifiers, 0)
            self._window_queue_overflow = dict.fromkeys(self.unit_identifiers, 0)
            self._processing_discontinuity_pending = dict.fromkeys(self.unit_identifiers, False)
            self._raw_expected_sequence = dict.fromkeys(self.unit_identifiers, None)
            # A phantom reading is only as good as the packet it came from.
            # Carrying one across a restart would let the console assert 48 V
            # is live on a board it has not heard from since.
            self._phantom_power = dict.fromkeys(self.unit_identifiers, None)

    def _new_processors(self) -> dict[int, UnitProcessingPipeline]:
        if self._processing_factory is None:
            return {
                unit_identifier: UnitProcessingPipeline(
                    unit_identifier,
                    clock=self._clock,
                    gain_source=self._gain_source(unit_identifier),
                    polarity_source=self._polarity_source(unit_identifier),
                    active_channels_source=self._active_channels_source(unit_identifier),
                    recording_sink=self._offer_to_sinks,
                    pre_dsp_sink=self._pre_dsp_sink,
                )
                for unit_identifier in self.unit_identifiers
            }
        return {unit_identifier: self._processing_factory(unit_identifier) for unit_identifier in self.unit_identifiers}

    def _gain_source(self, unit_identifier: int) -> Callable[[], np.ndarray]:
        """The operator's per-channel multiplier, and nothing else.

        Sign is not here. Gain is *recorded* rather than applied — the archive
        keeps pre-gain samples so a session recorded at the wrong gain is still
        the sea — and polarity is applied, because the two are not the same kind
        of fact. See `_polarity_source`.
        """
        return lambda: self._gain_store.multipliers(unit_identifier)

    def _polarity_source(self, unit_identifier: int) -> Callable[[], np.ndarray]:
        """The ``+1``/``-1`` array applied to the samples the recorder receives.

        Applied and recorded, which is the opposite of gain's treatment, and
        deliberately: a swapped pair of conductors is the wiring rather than a
        setting, multiplying by minus one is exactly invertible so nothing is
        lost by baking it in, and an archive that merely *mentions* the
        inversion in a sidecar is an archive that gets read without it. The
        applied flags travel to the recorder alongside the block, so the file
        still says which channels were inverted and anyone who later decides the
        call was wrong can flip them back.
        """
        return lambda: self._channel_polarity_store.signs(unit_identifier)

    def _active_channels_source(self, unit_identifier: int) -> Callable[[], tuple[int, ...]]:
        return lambda: self._channel_enable_store.active_channels(unit_identifier)

    def set_recording_sink(self, sink: RecordingSink | None) -> None:
        """Start or stop offering decimated blocks to a recorder.

        Set at runtime rather than taken in the constructor because recording
        starts and stops while acquisition keeps running, and because this is
        infrastructure: it may not know what a recording session is. The
        application owns the recorder and hands in something that accepts
        blocks.
        """
        with self._lock:
            self._recording_sink = sink
            if sink is not None:
                self._recording_error = None

    def set_pre_dsp_sink(self, sink: RecordingSink | None) -> None:
        with self._lock:
            self._pre_dsp_sink = sink
            for processor in self._processors.values():
                processor.replace_pre_dsp_sink(sink)

    def set_preprocessor_factory(self, factory: Callable[[int], Preprocessor | None]) -> None:
        with self._lock:
            for identifier, processor in self._processors.items():
                processor.replace_preprocessor(factory(identifier))

    def set_monitoring_sink(self, sink: RecordingSink | None) -> None:
        """Attach or detach the non-blocking live-audio monitor consumer.

        Monitoring is separate from recording because either operation may
        start or stop while the other remains active. The application-provided
        sink must only copy into a bounded buffer; speaker I/O never belongs on
        this real-time processing thread.
        """
        with self._lock:
            self._monitoring_sink = sink
            if sink is not None:
                self._monitoring_error = None

    def set_capture_sink(self, sink: RecordingSink | None) -> None:
        """Attach one bounded diagnostic capture without disturbing other sinks."""
        with self._lock:
            self._capture_sink = sink
            if sink is not None:
                self._capture_error = None

    def set_raw_sample_sink(self, sink: RawSampleSink | None) -> None:
        """Attach one non-blocking observer to decoded, unprocessed samples."""
        with self._lock:
            self._raw_sample_sink = sink
            self._raw_expected_sequence = dict.fromkeys(self.unit_identifiers, None)
            if sink is not None:
                self._raw_sample_error = None

    @property
    def raw_sample_error(self) -> str | None:
        with self._lock:
            return self._raw_sample_error

    @property
    def recording_error(self) -> str | None:
        """The last failure a recording sink raised, if it ever raised one."""
        with self._lock:
            return self._recording_error

    @property
    def monitoring_error(self) -> str | None:
        """The last failure raised by the live-audio monitor, if any."""
        with self._lock:
            return self._monitoring_error

    def _offer_to_sinks(self, unit_identifier: int, block: DecimatedBlock, multipliers, signs) -> None:
        """Offer one pre-gain block independently to recording and monitoring.

        Guarded, and deliberately so: this is called from the processing thread,
        and either consumer throwing must not take live acquisition or the other
        consumer down with it. Failures stay where the console can show them.
        """
        with self._lock:
            recording_sink = self._recording_sink
            monitoring_sink = self._monitoring_sink
            capture_sink = self._capture_sink
        self._offer_to_sink(
            "_recording_sink",
            "_recording_error",
            recording_sink,
            unit_identifier,
            block,
            multipliers,
            signs,
        )
        self._offer_to_sink(
            "_capture_sink",
            "_capture_error",
            capture_sink,
            unit_identifier,
            block,
            multipliers,
            signs,
        )
        self._offer_to_sink(
            "_monitoring_sink",
            "_monitoring_error",
            monitoring_sink,
            unit_identifier,
            block,
            multipliers,
            signs,
        )

    def _offer_to_sink(
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
        except Exception as error:  # an output consumer must never stop acquisition
            with self._lock:
                # Do not detach a replacement installed while the failed call
                # was outside the lock.
                if getattr(self, sink_attribute) is sink:
                    setattr(self, sink_attribute, None)
                    setattr(self, error_attribute, str(error))

    def channel_gains_db(self, unit_identifier: int) -> tuple[float, ...]:
        """One unit's sixteen channel gains, in decibels."""
        return self._gain_store.gains_db(unit_identifier)

    def set_channel_gain_db(self, unit_identifier: int, channel_index: int, gain_db: float) -> None:
        """Set one channel's gain. Takes effect on the unit's next block."""
        self._gain_store.set_gain_db(unit_identifier, channel_index, gain_db)

    def channels_enabled(self, unit_identifier: int) -> tuple[bool, ...]:
        """One flag per channel: whether it is part of this unit's array."""
        return self._channel_enable_store.enabled(unit_identifier)

    def active_channels(self, unit_identifier: int) -> tuple[int, ...]:
        """The channel indices the direction estimators currently see."""
        return self._channel_enable_store.active_channels(unit_identifier)

    def set_channel_enabled(self, unit_identifier: int, channel_index: int, enabled: bool) -> tuple[bool, ...]:
        """Switch one channel in or out of the array.

        Takes effect on the unit's next completed window, and raises rather
        than leaving a unit with too few elements to estimate a direction from
        — see `channel_enable.MINIMUM_ACTIVE_CHANNELS`. Metering, recording and
        speaker monitoring are unaffected either way.
        """
        return self._channel_enable_store.set_enabled(unit_identifier, channel_index, enabled)

    def channel_polarity(self, unit_identifier: int) -> tuple[bool, ...]:
        """One flag per channel: whether it arrives the way it was delivered."""
        return self._channel_polarity_store.polarity(unit_identifier)

    def set_channel_polarity(self, unit_identifier: int, channel_index: int, as_delivered: bool) -> tuple[bool, ...]:
        """Mark one channel as delivered or inverted.

        Takes effect on the unit's next block. Metering and speaker monitoring
        follow the corrected sign because they share the same multiplier; the
        archive does not, because it is written pre-gain.
        """
        return self._channel_polarity_store.set_polarity(unit_identifier, channel_index, as_delivered)

    @staticmethod
    def _combine_blocks(blocks: tuple[SampleBlock, ...]) -> SampleBlock:
        if len(blocks) == 1:
            return blocks[0]
        samples = np.concatenate([block.samples for block in blocks], axis=0)
        samples.setflags(write=False)
        quality = tuple(chain.from_iterable(block.quality for block in blocks))
        return SampleBlock(blocks[0].first_sequence, samples, quality)

    def _consume_payloads(self, unit_identifier: int, blob: bytes, packet_count: int) -> None:
        decoded = decode_sample_blob(blob, packet_count)
        if decoded.invalid_packets:
            with self._lock:
                self._decoded_invalid[unit_identifier] += decoded.invalid_packets
        if decoded.diagnostic_bytes.shape[0]:
            # The newest packet in the batch, not the oldest: this is a live
            # state, and the operator asking "is 48 V on right now" is not
            # served by an answer from the far end of a drained backlog. Kept
            # here rather than recomputed in _health() because this is the only
            # place the packet bytes exist at all.
            reading = decode_phantom_power(decoded.diagnostic_bytes[-1])
            with self._lock:
                # A packet from a bitstream without the readback decodes to
                # None. That must not erase a real reading taken moments ago
                # from a unit that does have it - only a restart clears it.
                if reading is not None:
                    self._phantom_power[unit_identifier] = reading
        self._offer_raw_samples(unit_identifier, decoded.sequences, decoded.samples)
        assembler = self._assemblers[unit_identifier]
        combined = assembler.append_batch(decoded.sequences, decoded.samples)
        if combined is None:
            return
        with self._lock:
            queue = self._processing_blocks[unit_identifier]
            if len(queue) == queue.maxlen:
                self._sample_queue_overflow[unit_identifier] += 1
                self._processing_discontinuity_pending[unit_identifier] = True
            queue.append(combined)

    def _offer_raw_samples(self, unit_identifier: int, sequences: np.ndarray, samples: np.ndarray) -> None:
        """Publish contiguous decoded packet runs without repairing sequence gaps."""
        if not sequences.size:
            return
        with self._lock:
            sink = self._raw_sample_sink
            expected = self._raw_expected_sequence[unit_identifier]
        if sink is None:
            return

        start = 0
        first_discontinuous = expected is not None and int(sequences[0]) != expected
        for index in range(1, sequences.size):
            previous = (int(sequences[index - 1]) + 1) % (1 << 32)
            if int(sequences[index]) == previous:
                continue
            if not self._publish_raw_run(sink, unit_identifier, samples[start:index], first_discontinuous):
                return
            start = index
            first_discontinuous = True
        if not self._publish_raw_run(sink, unit_identifier, samples[start:], first_discontinuous):
            return
        with self._lock:
            if self._raw_sample_sink is sink:
                self._raw_expected_sequence[unit_identifier] = (int(sequences[-1]) + 1) % (1 << 32)

    def _publish_raw_run(self, sink: RawSampleSink, unit_identifier: int, packet_samples: np.ndarray, discontinuous: bool) -> bool:
        values = packet_samples.reshape(-1, packet_samples.shape[-1])
        try:
            sink(RawSampleBlock(unit_identifier, values, discontinuous))
        except Exception as error:
            with self._lock:
                if self._raw_sample_sink is sink:
                    self._raw_sample_sink = None
                    self._raw_sample_error = str(error)
            return False
        return True

    def _publish_windows(self, unit_identifier: int, windows: tuple[ProcessingWindow, ...]) -> None:
        with self._lock:
            queue = self._windows[unit_identifier]
            for window in windows:
                if len(queue) == queue.maxlen:
                    self._window_queue_overflow[unit_identifier] += 1
                queue.append(window)

    def _health(
        self,
        snapshot: UnitReceiverSnapshot,
        status: ReceiverStatus,
        elapsed: float,
        now: float,
    ) -> AcquisitionUnitHealth:
        previous = self._last_received.get(snapshot.unit_identifier, 0)
        self._last_received[snapshot.unit_identifier] = snapshot.received_packets
        age = None if snapshot.last_packet_monotonic is None else max(0.0, now - snapshot.last_packet_monotonic)
        with self._lock:
            decoded_invalid = self._decoded_invalid[snapshot.unit_identifier]
            sample_overflow = self._sample_queue_overflow[snapshot.unit_identifier]
            queued_sample_blocks = len(self._processing_blocks[snapshot.unit_identifier])
            window_overflow = self._window_queue_overflow[snapshot.unit_identifier]
            queued_windows = len(self._windows[snapshot.unit_identifier])
            phantom_power = self._phantom_power[snapshot.unit_identifier]
        error = self.receiver_error or status.last_error
        return AcquisitionUnitHealth(
            snapshot.unit_identifier,
            snapshot.source_address,
            max(0.0, snapshot.received_packets - previous) / elapsed,
            age,
            snapshot.received_packets,
            snapshot.accepted_packets,
            snapshot.lost_packets,
            snapshot.sequence_restarts,
            snapshot.invalid_packets + decoded_invalid,
            snapshot.duplicate_packets,
            snapshot.out_of_order_packets,
            snapshot.discarded_buffer_packets,
            snapshot.queued_packets,
            sample_overflow,
            queued_sample_blocks,
            window_overflow,
            queued_windows,
            status.unknown_source_packets,
            error,
            status.receive_buffer_bytes,
            status.requested_receive_buffer_bytes,
            snapshot.receive_backlog_bytes,
            snapshot.receive_backlog_seconds,
            snapshot.kernel_dropped_packets,
            phantom_power,
        )

    def _offline_snapshot(self, unit_identifier: int) -> UnitReceiverSnapshot:
        return UnitReceiverSnapshot(
            unit_identifier,
            self._configuration.source_addresses[unit_identifier],
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            None,
        )
