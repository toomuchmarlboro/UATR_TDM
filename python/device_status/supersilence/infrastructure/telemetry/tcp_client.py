"""One bounded, reconnecting GDAT2 TCP client."""

from __future__ import annotations

import socket
import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from supersilence.infrastructure.telemetry.gdat2 import (
    Gdat2DecodeError,
    Gdat2LineFramer,
    Gdat2Sample,
    parse_gdat2,
)

DEFAULT_MAXIMUM_SAMPLES = 256
READ_SIZE_BYTES = 4_096


@dataclass(frozen=True)
class ReceivedSample:
    """One accepted sentence and the wall-clock instant it arrived.

    GDAT2 carries no time of its own, so the only timestamp anyone can honestly
    put on a reading is when this client took it off the socket. It is stamped
    here, on arrival, rather than by whoever later drains the queue: a caller
    polling once a second would otherwise date a whole second of readings to the
    moment it happened to ask, and an archive would carry that as fact.

    The reading is wall clock, not the monotonic clock used for staleness. A
    monotonic count is the right way to ask *how old is this*, and useless as
    the answer to *when was it*.
    """

    received_at: datetime
    sample: Gdat2Sample


class TelemetryState(str, Enum):
    DISABLED = "disabled"
    CONNECTING = "connecting"
    CONNECTED_STALE = "connected/stale"
    CONNECTED_FRESH = "connected/fresh"
    RECONNECTING = "reconnecting"
    STOPPED = "stopped"


@dataclass(frozen=True)
class TelemetryClientSnapshot:
    unit_identifier: int
    sensor_address: str
    port: int
    state: TelemetryState
    message_age_seconds: float | None
    bytes_received: int
    valid_messages: int
    invalid_messages: int
    oversized_frames: int
    connection_attempts: int
    successful_connections: int
    disconnects: int
    queued_samples: int
    dropped_samples: int
    last_error: str
    latest_sample: Gdat2Sample | None


class Gdat2TcpClient:
    """Keep one sensor connection alive without blocking any application caller."""

    def __init__(
        self,
        unit_identifier: int,
        sensor_address: str,
        port: int,
        *,
        enabled: bool = True,
        connection_timeout_seconds: float = 3.0,
        reconnect_interval_seconds: float = 5.0,
        stale_threshold_seconds: float = 1.0,
        maximum_samples: int = DEFAULT_MAXIMUM_SAMPLES,
        clock: Callable[[], float] = time.monotonic,
        wall_clock: Callable[[], datetime] = datetime.now,
        connector: Callable[..., socket.socket] = socket.create_connection,
    ) -> None:
        if unit_identifier <= 0:
            raise ValueError("unit identifier must be positive")
        if maximum_samples <= 0:
            raise ValueError("maximum samples must be positive")
        for value, label in (
            (connection_timeout_seconds, "connection timeout"),
            (reconnect_interval_seconds, "reconnect interval"),
            (stale_threshold_seconds, "stale threshold"),
        ):
            if value <= 0:
                raise ValueError(f"{label} must be positive")
        self.unit_identifier = unit_identifier
        self.sensor_address = sensor_address
        self.port = port
        self._enabled = enabled
        self._connection_timeout_seconds = connection_timeout_seconds
        self._reconnect_interval_seconds = reconnect_interval_seconds
        self._stale_threshold_seconds = stale_threshold_seconds
        self._clock = clock
        self._wall_clock = wall_clock
        self._connector = connector
        self._samples: deque[ReceivedSample] = deque(maxlen=maximum_samples)
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._socket: socket.socket | None = None
        self._started = False
        self._stopped = False
        self._connecting = False
        self._connected = False
        self._connected_at_monotonic: float | None = None
        self._has_attempted = False
        self._last_valid_monotonic: float | None = None
        self._latest_sample: Gdat2Sample | None = None
        self._bytes_received = 0
        self._valid_messages = 0
        self._invalid_messages = 0
        self._oversized_frames = 0
        self._connection_attempts = 0
        self._successful_connections = 0
        self._disconnects = 0
        self._dropped_samples = 0
        self._last_error = ""

    @property
    def running(self) -> bool:
        return bool(self._thread is not None and self._thread.is_alive())

    def start(self) -> None:
        if self.running:
            return
        self._started = True
        self._stopped = False
        if not self._enabled:
            return
        self._stop.clear()
        with self._lock:
            self._connecting = True
            self._connected = False
        self._thread = threading.Thread(
            target=self._run,
            daemon=True,
            name=f"gdat2-unit-{self.unit_identifier}",
        )
        self._thread.start()

    def stop(self, timeout_seconds: float = 2.0) -> None:
        self._stop.set()
        with self._lock:
            connection = self._socket
        if connection is not None:
            try:
                connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                connection.close()
            except OSError:
                pass
        thread, self._thread = self._thread, None
        if thread is not None and thread.is_alive():
            thread.join(timeout=timeout_seconds)
        with self._lock:
            self._socket = None
            self._connecting = False
            self._connected = False
            self._connected_at_monotonic = None
            self._stopped = True

    def send(self, payload: bytes) -> str:
        """Write one sentence back to the buoy. -> "" on success, else why not.

        THE ONLY WRITE PATH ON THIS CLIENT. Everything else here reads, and the
        one thing that is sent - a valve command - moves hardware, so this
        returns a reason rather than raising: the caller is a button, and a
        refused command must not take the telemetry link down with it.

        Goes out on the SAME socket the sentences arrive on. Not a second
        connection: the aux_vcu accepts commands on the one it is already
        streaming over, and these embedded TCP servers take a single client, so
        dialling again would be refused or would displace the stream.

        SUCCESS MEANS THE BYTES LEFT, nothing more. The far end does not
        acknowledge, so what the hardware did with them shows up in the
        telemetry and nowhere else.
        """
        # The reader thread owns _socket and clears it on disconnect, so take
        # the reference under the lock and send outside it - sendall must not
        # hold the lock the reader wants. A socket closed in the gap raises
        # OSError, which is already the failure path rather than a new one.
        # Same shape as stop() above, for the same reason.
        with self._lock:
            connection = self._socket
        if connection is None:
            return "not connected"
        try:
            connection.sendall(payload)
        except OSError as error:
            return str(error) or error.__class__.__name__
        return ""

    def snapshot(self) -> TelemetryClientSnapshot:
        now = self._clock()
        with self._lock:
            age = None if self._last_valid_monotonic is None else max(0.0, now - self._last_valid_monotonic)
            return TelemetryClientSnapshot(
                self.unit_identifier,
                self.sensor_address,
                self.port,
                self._state(age),
                age,
                self._bytes_received,
                self._valid_messages,
                self._invalid_messages,
                self._oversized_frames,
                self._connection_attempts,
                self._successful_connections,
                self._disconnects,
                len(self._samples),
                self._dropped_samples,
                self._last_error,
                self._latest_sample,
            )

    def drain_samples(self, maximum_samples: int = 0) -> tuple[Gdat2Sample, ...]:
        """The queued readings, oldest first, without their arrival times."""
        return tuple(record.sample for record in self.drain_records(maximum_samples))

    def drain_records(self, maximum_samples: int = 0) -> tuple[ReceivedSample, ...]:
        """The queued readings with the instant each arrived, oldest first.

        Draining removes them: two callers cannot both have the queue, which is
        why the recorder is the only thing that drains it and the status window
        reads `latest_sample` off the snapshot instead.
        """
        with self._lock:
            count = len(self._samples)
            if maximum_samples > 0:
                count = min(count, maximum_samples)
            return tuple(self._samples.popleft() for _ in range(count))

    def _state(self, age: float | None) -> TelemetryState:
        if self._stopped:
            return TelemetryState.STOPPED
        if not self._enabled:
            return TelemetryState.DISABLED
        if not self._started:
            return TelemetryState.STOPPED
        if self._connected:
            if age is not None and age <= self._stale_threshold_seconds:
                return TelemetryState.CONNECTED_FRESH
            return TelemetryState.CONNECTED_STALE
        if self._connecting and not self._has_attempted:
            return TelemetryState.CONNECTING
        return TelemetryState.RECONNECTING

    def _run(self) -> None:
        framer = Gdat2LineFramer()
        while not self._stop.is_set():
            with self._lock:
                self._connecting = True
                self._connection_attempts += 1
            try:
                connection = self._connector(
                    (self.sensor_address, self.port),
                    timeout=self._connection_timeout_seconds,
                )
                connection.settimeout(min(self._connection_timeout_seconds, 0.2))
            except OSError as error:
                with self._lock:
                    self._has_attempted = True
                    self._connecting = False
                    self._last_error = str(error)
                self._stop.wait(self._reconnect_interval_seconds)
                continue

            framer.reset()
            with self._lock:
                self._socket = connection
                self._has_attempted = True
                self._connecting = False
                self._connected = True
                self._connected_at_monotonic = self._clock()
                self._successful_connections += 1
                self._last_error = ""
            try:
                self._read_connection(connection, framer)
            except OSError as error:
                if not self._stop.is_set():
                    with self._lock:
                        self._last_error = str(error)
            finally:
                try:
                    connection.close()
                except OSError:
                    pass
                with self._lock:
                    self._socket = None
                    was_connected = self._connected
                    self._connected = False
                    self._connected_at_monotonic = None
                    if was_connected and not self._stop.is_set():
                        self._disconnects += 1
                        if not self._last_error:
                            self._last_error = "connection closed by peer"
            if not self._stop.is_set():
                self._stop.wait(self._reconnect_interval_seconds)

    def _read_connection(self, connection: socket.socket, framer: Gdat2LineFramer) -> None:
        while not self._stop.is_set():
            try:
                data = connection.recv(READ_SIZE_BYTES)
            except socket.timeout:
                if self._connection_has_gone_silent():
                    raise TimeoutError("telemetry connection stopped delivering valid sentences")
                continue
            if not data:
                return
            result = framer.feed(data)
            with self._lock:
                self._bytes_received += len(data)
                self._oversized_frames += result.oversized_frames
                self._invalid_messages += result.oversized_frames
            for line in result.lines:
                try:
                    sample = parse_gdat2(line)
                except Gdat2DecodeError:
                    with self._lock:
                        self._invalid_messages += 1
                    continue
                now = self._clock()
                arrived_at = self._wall_clock()
                with self._lock:
                    if len(self._samples) == self._samples.maxlen:
                        self._dropped_samples += 1
                    self._samples.append(ReceivedSample(arrived_at, sample))
                    self._latest_sample = sample
                    self._last_valid_monotonic = now
                    self._valid_messages += 1

    def _connection_has_gone_silent(self) -> bool:
        """Whether this open socket has outlived its valid-message allowance."""
        now = self._clock()
        with self._lock:
            last_activity = max(value for value in (self._connected_at_monotonic, self._last_valid_monotonic) if value is not None)
        return now - last_activity > self._stale_threshold_seconds
