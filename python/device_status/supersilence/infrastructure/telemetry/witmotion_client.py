"""One bounded, reconnecting WitMotion TCP client."""

from __future__ import annotations

import socket
import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from supersilence.infrastructure.telemetry.tcp_client import TelemetryState
from supersilence.infrastructure.telemetry.witmotion import (
    ACCELERATION_PACKET,
    ANGLE_PACKET,
    ANGULAR_RATE_PACKET,
    MAGNETIC_PACKET,
    QUATERNION_PACKET,
    WitMotionAcceleration,
    WitMotionAngle,
    WitMotionAngularRate,
    WitMotionFramer,
    WitMotionMagnetic,
    WitMotionQuaternion,
)

READ_SIZE_BYTES = 4_096

#: How many undrained records the queue keeps. The console drains once a second
#: and this sensor sends a handful of packets in that time, so the bound is only
#: reached when nothing is draining at all — a console recording nothing.
DEFAULT_MAXIMUM_RECORDS = 256


@dataclass(frozen=True)
class ReceivedAttitude:
    """The decoded packets of one read, and the instant they arrived.

    One record per read rather than one per packet: the sensor sends its five
    packet types as a burst, and splitting a burst into five rows an archive
    would have to re-join is work with no reader. A type absent from a burst is
    `None` here and empty in the archive, which is the honest reading — it says
    the sensor did not send it, not that it sent a zero.

    Wall clock, stamped on arrival, for the same reason `ReceivedSample` is: a
    caller that polls once a second would otherwise date a whole second of
    readings to the moment it happened to ask.
    """

    received_at: datetime
    angle: WitMotionAngle | None = None
    acceleration: WitMotionAcceleration | None = None
    angular_rate: WitMotionAngularRate | None = None
    magnetic: WitMotionMagnetic | None = None
    quaternion: WitMotionQuaternion | None = None


@dataclass(frozen=True)
class WitMotionClientSnapshot:
    unit_identifier: int
    sensor_address: str
    port: int
    state: TelemetryState
    packet_age_seconds: float | None
    angle_age_seconds: float | None
    bytes_received: int
    valid_packets: int
    checksum_errors: int
    discarded_bytes: int
    connection_attempts: int
    successful_connections: int
    disconnects: int
    last_error: str
    angle: WitMotionAngle | None
    acceleration: WitMotionAcceleration | None
    angular_rate: WitMotionAngularRate | None
    magnetic: WitMotionMagnetic | None
    quaternion: WitMotionQuaternion | None


class WitMotionTcpClient:
    """Read one IMU without blocking application callers or trusting socket age."""

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
        clock: Callable[[], float] = time.monotonic,
        wall_clock: Callable[[], datetime] = datetime.now,
        connector: Callable[..., socket.socket] = socket.create_connection,
        maximum_records: int = DEFAULT_MAXIMUM_RECORDS,
    ) -> None:
        if unit_identifier <= 0:
            raise ValueError("unit identifier must be positive")
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
        self._records: deque[ReceivedAttitude] = deque(maxlen=maximum_records)
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
        self._last_packet_monotonic: float | None = None
        self._last_angle_monotonic: float | None = None
        self._bytes_received = 0
        self._valid_packets = 0
        self._checksum_errors = 0
        self._discarded_bytes = 0
        self._connection_attempts = 0
        self._successful_connections = 0
        self._disconnects = 0
        self._last_error = ""
        self._angle: WitMotionAngle | None = None
        self._acceleration: WitMotionAcceleration | None = None
        self._angular_rate: WitMotionAngularRate | None = None
        self._magnetic: WitMotionMagnetic | None = None
        self._quaternion: WitMotionQuaternion | None = None

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
            name=f"witmotion-unit-{self.unit_identifier}",
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

    def snapshot(self) -> WitMotionClientSnapshot:
        now = self._clock()
        with self._lock:
            packet_age = self._age(now, self._last_packet_monotonic)
            angle_age = self._age(now, self._last_angle_monotonic)
            return WitMotionClientSnapshot(
                self.unit_identifier,
                self.sensor_address,
                self.port,
                self._state(packet_age),
                packet_age,
                angle_age,
                self._bytes_received,
                self._valid_packets,
                self._checksum_errors,
                self._discarded_bytes,
                self._connection_attempts,
                self._successful_connections,
                self._disconnects,
                self._last_error,
                self._angle,
                self._acceleration,
                self._angular_rate,
                self._magnetic,
                self._quaternion,
            )

    def drain_records(self, maximum_records: int = 0) -> tuple[ReceivedAttitude, ...]:
        """The queued readings with the instant each arrived, oldest first.

        Draining removes them, so the recorder is the only thing that drains;
        the status window reads the latest packet off the snapshot instead.
        """
        with self._lock:
            count = len(self._records)
            if maximum_records > 0:
                count = min(count, maximum_records)
            return tuple(self._records.popleft() for _ in range(count))

    @staticmethod
    def _age(now: float, then: float | None) -> float | None:
        return None if then is None else max(0.0, now - then)

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
        framer = WitMotionFramer()
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

    def _read_connection(self, connection: socket.socket, framer: WitMotionFramer) -> None:
        while not self._stop.is_set():
            try:
                data = connection.recv(READ_SIZE_BYTES)
            except socket.timeout:
                if self._connection_has_gone_silent():
                    raise TimeoutError("IMU connection stopped delivering valid packets")
                continue
            if not data:
                return
            result = framer.feed(data)
            now = self._clock()
            arrived_at = self._wall_clock()
            latest = {packet.packet_type: packet.value for packet in result.packets}
            with self._lock:
                self._bytes_received += len(data)
                self._checksum_errors += result.checksum_errors
                self._discarded_bytes += result.discarded_bytes
                self._valid_packets += len(result.packets)
                if result.packets:
                    self._last_packet_monotonic = now
                if ANGLE_PACKET in latest:
                    self._angle = latest[ANGLE_PACKET]
                    self._last_angle_monotonic = now
                if ACCELERATION_PACKET in latest:
                    self._acceleration = latest[ACCELERATION_PACKET]
                if ANGULAR_RATE_PACKET in latest:
                    self._angular_rate = latest[ANGULAR_RATE_PACKET]
                if MAGNETIC_PACKET in latest:
                    self._magnetic = latest[MAGNETIC_PACKET]
                if QUATERNION_PACKET in latest:
                    self._quaternion = latest[QUATERNION_PACKET]
                if result.packets:
                    self._records.append(
                        ReceivedAttitude(
                            arrived_at,
                            latest.get(ANGLE_PACKET),
                            latest.get(ACCELERATION_PACKET),
                            latest.get(ANGULAR_RATE_PACKET),
                            latest.get(MAGNETIC_PACKET),
                            latest.get(QUATERNION_PACKET),
                        )
                    )

    def _connection_has_gone_silent(self) -> bool:
        """Whether this open socket has outlived its valid-packet allowance."""
        now = self._clock()
        with self._lock:
            last_activity = max(value for value in (self._connected_at_monotonic, self._last_packet_monotonic) if value is not None)
        return now - last_activity > self._stale_threshold_seconds
