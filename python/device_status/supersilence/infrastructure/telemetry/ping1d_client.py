"""One read-only, reconnecting Ping1D TCP client."""

from __future__ import annotations

import socket
import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from supersilence.infrastructure.telemetry.ping1d import (
    DISTANCE_MESSAGE,
    DISTANCE_MESSAGES,
    DISTANCE_SIMPLE_MESSAGE,
    NACK_MESSAGE,
    PingDistance,
    PingFramer,
    decode_ping_distance,
    decode_ping_nack,
    encode_ping_request,
)
from supersilence.infrastructure.telemetry.tcp_client import TelemetryState

READ_SIZE_BYTES = 4_096
DEFAULT_POLL_INTERVAL_SECONDS = 0.05
DEFAULT_REPLY_TIMEOUT_SECONDS = 1.0
DEFAULT_SERIAL_BRIDGE_SETTLE_SECONDS = 1.0
DEFAULT_FALLBACK_AFTER_SECONDS = 2.0


#: How many undrained readings the queue keeps. The sensor is polled a few times
#: a second, so this is minutes of history for a console that has stopped
#: draining and nothing at all for one that has not.
DEFAULT_MAXIMUM_RECORDS = 256


@dataclass(frozen=True)
class ReceivedDistance:
    """One accepted distance reply and the wall-clock instant it arrived.

    Ping1D answers a request, so a reply carries no time of its own; the only
    honest timestamp is when this client took it off the socket. The message
    identifier is kept because the client falls back from the full distance
    message to the simple one, and a row that does not say which it answered
    cannot be told apart from one that does.
    """

    received_at: datetime
    distance: PingDistance
    message_identifier: int


@dataclass(frozen=True)
class Ping1dClientSnapshot:
    unit_identifier: int
    sensor_address: str
    port: int
    state: TelemetryState
    reading_age_seconds: float | None
    bytes_received: int
    valid_frames: int
    checksum_errors: int
    discarded_bytes: int
    requests_sent: int
    timeouts: int
    nacks: int
    last_nack: str
    requested_message_identifier: int
    answered_message_identifier: int | None
    connection_attempts: int
    successful_connections: int
    disconnects: int
    last_error: str
    distance: PingDistance | None


class Ping1dTcpClient:
    """Poll distance without ever writing Ping1D configuration state."""

    def __init__(
        self,
        unit_identifier: int,
        sensor_address: str,
        port: int,
        *,
        enabled: bool = True,
        connection_timeout_seconds: float = 3.0,
        reconnect_interval_seconds: float = 5.0,
        stale_threshold_seconds: float = 3.0,
        poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS,
        reply_timeout_seconds: float = DEFAULT_REPLY_TIMEOUT_SECONDS,
        settle_seconds: float = DEFAULT_SERIAL_BRIDGE_SETTLE_SECONDS,
        fallback_after_seconds: float = DEFAULT_FALLBACK_AFTER_SECONDS,
        clock: Callable[[], float] = time.monotonic,
        wall_clock: Callable[[], datetime] = datetime.now,
        connector: Callable[..., socket.socket] = socket.create_connection,
        maximum_records: int = DEFAULT_MAXIMUM_RECORDS,
    ) -> None:
        if unit_identifier <= 0:
            raise ValueError("unit identifier must be positive")
        for value, label, allow_zero in (
            (connection_timeout_seconds, "connection timeout", False),
            (reconnect_interval_seconds, "reconnect interval", False),
            (stale_threshold_seconds, "stale threshold", False),
            (poll_interval_seconds, "poll interval", False),
            (reply_timeout_seconds, "reply timeout", False),
            (settle_seconds, "serial bridge settle time", True),
            (fallback_after_seconds, "message fallback time", False),
        ):
            if value < 0 or (not allow_zero and value == 0):
                raise ValueError(f"{label} must be {'nonnegative' if allow_zero else 'positive'}")
        self.unit_identifier = unit_identifier
        self.sensor_address = sensor_address
        self.port = port
        self._enabled = enabled
        self._connection_timeout_seconds = connection_timeout_seconds
        self._reconnect_interval_seconds = reconnect_interval_seconds
        self._stale_threshold_seconds = stale_threshold_seconds
        self._poll_interval_seconds = poll_interval_seconds
        self._reply_timeout_seconds = reply_timeout_seconds
        self._settle_seconds = settle_seconds
        self._fallback_after_seconds = fallback_after_seconds
        self._clock = clock
        self._wall_clock = wall_clock
        self._connector = connector
        self._records: deque[ReceivedDistance] = deque(maxlen=maximum_records)
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
        self._last_reading_monotonic: float | None = None
        self._bytes_received = 0
        self._valid_frames = 0
        self._checksum_errors = 0
        self._discarded_bytes = 0
        self._requests_sent = 0
        self._timeouts = 0
        self._nacks = 0
        self._last_nack = ""
        self._requested_message_identifier = DISTANCE_MESSAGES[0]
        self._answered_message_identifier: int | None = None
        self._connection_attempts = 0
        self._successful_connections = 0
        self._disconnects = 0
        self._last_error = ""
        self._distance: PingDistance | None = None

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
            name=f"ping1d-unit-{self.unit_identifier}",
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

    def drain_records(self, maximum_records: int = 0) -> tuple[ReceivedDistance, ...]:
        """The queued readings with the instant each arrived, oldest first.

        Draining removes them: the recorder is the only caller, and the status
        window reads the latest distance off the snapshot instead.
        """
        with self._lock:
            count = len(self._records)
            if maximum_records > 0:
                count = min(count, maximum_records)
            return tuple(self._records.popleft() for _ in range(count))

    def snapshot(self) -> Ping1dClientSnapshot:
        now = self._clock()
        with self._lock:
            age = None if self._last_reading_monotonic is None else max(0.0, now - self._last_reading_monotonic)
            return Ping1dClientSnapshot(
                self.unit_identifier,
                self.sensor_address,
                self.port,
                self._state(age),
                age,
                self._bytes_received,
                self._valid_frames,
                self._checksum_errors,
                self._discarded_bytes,
                self._requests_sent,
                self._timeouts,
                self._nacks,
                self._last_nack,
                self._requested_message_identifier,
                self._answered_message_identifier,
                self._connection_attempts,
                self._successful_connections,
                self._disconnects,
                self._last_error,
                self._distance,
            )

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
        framer = PingFramer()
        while not self._stop.is_set():
            with self._lock:
                self._connecting = True
                self._connection_attempts += 1
            try:
                connection = self._connector(
                    (self.sensor_address, self.port),
                    timeout=self._connection_timeout_seconds,
                )
                connection.settimeout(min(self._reply_timeout_seconds, max(0.01, self._poll_interval_seconds)))
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
                if not self._stop.wait(self._settle_seconds):
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

    def _read_connection(self, connection: socket.socket, framer: PingFramer) -> None:
        request_index = 0
        requested = DISTANCE_MESSAGES[request_index]
        first_request_at = self._clock()
        last_request_at: float | None = None
        next_request_at = first_request_at
        pending = False
        locked_to_answer = False

        while not self._stop.is_set():
            now = self._clock()
            if pending and last_request_at is not None:
                if now - last_request_at >= self._reply_timeout_seconds:
                    with self._lock:
                        self._timeouts += 1
                    if self._connection_has_gone_silent():
                        raise TimeoutError("Ping1D connection stopped answering distance requests")
                    pending = False
                    next_request_at = now
            if not locked_to_answer and now - first_request_at >= self._fallback_after_seconds and requested == DISTANCE_MESSAGE:
                request_index = 1
                requested = DISTANCE_MESSAGES[request_index]
                pending = False
                next_request_at = now
            if not pending and now >= next_request_at:
                connection.sendall(encode_ping_request(requested))
                with self._lock:
                    self._requests_sent += 1
                    self._requested_message_identifier = requested
                pending = True
                last_request_at = now

            try:
                data = connection.recv(READ_SIZE_BYTES)
            except socket.timeout:
                continue
            if not data:
                return
            result = framer.feed(data)
            with self._lock:
                self._bytes_received += len(data)
                self._valid_frames += len(result.frames)
                self._checksum_errors += result.checksum_errors
                self._discarded_bytes += result.discarded_bytes
            for frame in result.frames:
                if frame.message_identifier == NACK_MESSAGE:
                    nacked, explanation = decode_ping_nack(frame.payload)
                    with self._lock:
                        self._nacks += 1
                        self._last_nack = f"{nacked}: {explanation or '(no explanation)'}"
                    if nacked == requested and requested == DISTANCE_MESSAGE:
                        requested = DISTANCE_SIMPLE_MESSAGE
                        pending = False
                        next_request_at = self._clock()
                    continue
                if frame.message_identifier not in DISTANCE_MESSAGES:
                    continue
                distance = decode_ping_distance(frame.payload)
                if distance is None:
                    continue
                received_at = self._clock()
                arrived_at = self._wall_clock()
                with self._lock:
                    self._distance = distance
                    self._last_reading_monotonic = received_at
                    self._records.append(ReceivedDistance(arrived_at, distance, frame.message_identifier))
                    self._answered_message_identifier = frame.message_identifier
                    self._requested_message_identifier = frame.message_identifier
                requested = frame.message_identifier
                locked_to_answer = True
                pending = False
                next_request_at = received_at + self._poll_interval_seconds

    def _connection_has_gone_silent(self) -> bool:
        """Whether an open Ping1D connection has outlived its reply allowance."""
        now = self._clock()
        with self._lock:
            last_activity = max(value for value in (self._connected_at_monotonic, self._last_reading_monotonic) if value is not None)
        return now - last_activity > self._stale_threshold_seconds
