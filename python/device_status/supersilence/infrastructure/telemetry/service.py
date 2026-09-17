"""Application-owned lifecycle for three independent telemetry roles per unit."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from supersilence.infrastructure.telemetry.configuration import TelemetryConfiguration
from supersilence.infrastructure.telemetry.gdat2 import Gdat2Sample
from supersilence.infrastructure.telemetry.valve import (
    ValveCommand,
    build_valve_command,
)
from supersilence.infrastructure.telemetry.ping1d_client import (
    Ping1dClientSnapshot,
    Ping1dTcpClient,
    ReceivedDistance,
)
from supersilence.infrastructure.telemetry.tcp_client import (
    Gdat2TcpClient,
    ReceivedSample,
    TelemetryClientSnapshot,
)
from supersilence.infrastructure.telemetry.witmotion_client import (
    ReceivedAttitude,
    WitMotionClientSnapshot,
    WitMotionTcpClient,
)

#: How many readings one unit's queue holds before the oldest is dropped.
#:
#: Was 256, which was ample while nothing drained the queue and only
#: `latest_sample` was read. Recording drains it on the console's one-second
#: health cadence, and the queue is now the buffer that stands between a console
#: that stalls for a moment and a hole in the archive. At the simulator's 50 Hz
#: — Legacy-derived and, note, **not established by `UATR_TDM`, which carries no
#: GDAT2 specification at all** — 256 was 5.1 seconds of cover and this is about
#: forty. The cost is a few megabytes per unit in the worst case.
DEFAULT_SAMPLES_PER_UNIT = 2_048
DEFAULT_ALTIMETER_STALE_THRESHOLD_SECONDS = 3.0


@dataclass(frozen=True)
class UnitTelemetrySnapshot:
    """One unit's three links sampled together for presentation."""

    unit_identifier: int
    gdat2: TelemetryClientSnapshot
    imu: WitMotionClientSnapshot
    altimeter: Ping1dClientSnapshot


class TelemetryService:
    def __init__(
        self,
        configuration: TelemetryConfiguration,
        *,
        client_factory: Callable[..., Gdat2TcpClient] = Gdat2TcpClient,
        imu_client_factory: Callable[..., WitMotionTcpClient] = WitMotionTcpClient,
        altimeter_client_factory: Callable[..., Ping1dTcpClient] = Ping1dTcpClient,
        maximum_samples_per_unit: int = DEFAULT_SAMPLES_PER_UNIT,
    ) -> None:
        self._client_factory = client_factory
        self._imu_client_factory = imu_client_factory
        self._altimeter_client_factory = altimeter_client_factory
        self._maximum_samples_per_unit = maximum_samples_per_unit
        self._build_clients(configuration)

    def reconfigure(self, configuration: TelemetryConfiguration) -> None:
        """Point this service at different endpoints, in place.

        IN PLACE, AND THAT IS THE POINT. Callers hold this object — the device
        status window is handed it once and keeps the reference — so pointing
        the console at a different buoy by constructing a second service would
        leave every one of them reading the first one forever. Rebuilding the
        clients behind a stable identity is the only version of this that does
        not require every holder to be found and updated.

        Stops the old clients first. Their threads own sockets, and a rebuild
        that merely dropped the references would leave the previous addresses
        still connected and still counted as running.
        """
        self.stop()
        self._build_clients(configuration)

    def _build_clients(self, configuration: TelemetryConfiguration) -> None:
        self._configuration = configuration
        if configuration.imu_sensor_addresses is None or configuration.altimeter_sensor_addresses is None:
            raise ValueError("telemetry configuration must define all three device roles")
        client_factory = self._client_factory
        imu_client_factory = self._imu_client_factory
        altimeter_client_factory = self._altimeter_client_factory
        maximum_samples_per_unit = self._maximum_samples_per_unit
        self._clients = {
            unit_identifier: client_factory(
                unit_identifier,
                address,
                configuration.port,
                enabled=configuration.enabled,
                connection_timeout_seconds=configuration.connection_timeout_seconds,
                reconnect_interval_seconds=configuration.reconnect_interval_seconds,
                stale_threshold_seconds=configuration.stale_threshold_seconds,
                maximum_samples=maximum_samples_per_unit,
            )
            for unit_identifier, address in configuration.sensor_addresses.items()
        }
        self._imu_clients = {
            unit_identifier: imu_client_factory(
                unit_identifier,
                address,
                configuration.port,
                enabled=configuration.enabled,
                connection_timeout_seconds=configuration.connection_timeout_seconds,
                reconnect_interval_seconds=configuration.reconnect_interval_seconds,
                stale_threshold_seconds=configuration.stale_threshold_seconds,
            )
            for unit_identifier, address in configuration.imu_sensor_addresses.items()
        }
        self._altimeter_clients = {
            unit_identifier: altimeter_client_factory(
                unit_identifier,
                address,
                configuration.port,
                enabled=configuration.enabled,
                connection_timeout_seconds=configuration.connection_timeout_seconds,
                reconnect_interval_seconds=configuration.reconnect_interval_seconds,
                stale_threshold_seconds=DEFAULT_ALTIMETER_STALE_THRESHOLD_SECONDS,
            )
            for unit_identifier, address in configuration.altimeter_sensor_addresses.items()
        }

    def _all_clients(self) -> tuple[object, ...]:
        return (
            *self._clients.values(),
            *self._imu_clients.values(),
            *self._altimeter_clients.values(),
        )

    @property
    def unit_identifiers(self) -> tuple[int, ...]:
        return tuple(sorted(self._clients))

    @property
    def running(self) -> bool:
        return self._configuration.enabled and all(client.running for client in self._all_clients())

    def start(self) -> bool:
        for client in self._all_clients():
            client.start()
        return self.running

    def stop(self) -> None:
        for client in self._all_clients():
            client.stop()

    def health(self) -> tuple[TelemetryClientSnapshot, ...]:
        """GDAT2-only compatibility view used by recording and orientation."""
        return tuple(self._clients[index].snapshot() for index in self.unit_identifiers)

    def unit_health(self) -> tuple[UnitTelemetrySnapshot, ...]:
        return tuple(
            UnitTelemetrySnapshot(
                index,
                self._clients[index].snapshot(),
                self._imu_clients[index].snapshot(),
                self._altimeter_clients[index].snapshot(),
            )
            for index in self.unit_identifiers
        )

    def send_valve_command(self, unit_identifier: int, command: ValveCommand) -> str:
        """Drive one unit's valve. -> "" on success, else why not. Never raises.

        The only method on this service that WRITES. It is named for the
        actuator rather than offered as a general "send to unit", because a
        general write path invites a second kind of traffic onto a link whose
        whole contract is that it is read-only apart from this.

        An unknown unit is a returned reason, not a KeyError: the caller is a
        button on a page that was built from a unit list which can legitimately
        have changed underneath it.
        """
        client = self._clients.get(unit_identifier)
        if client is None:
            return f"unit {unit_identifier} has no telemetry link"
        return client.send(build_valve_command(command))

    def drain_samples(self, unit_identifier: int, maximum_samples: int = 0) -> tuple[Gdat2Sample, ...]:
        return self._clients[unit_identifier].drain_samples(maximum_samples)

    def drain_records(self, unit_identifier: int, maximum_samples: int = 0) -> tuple[ReceivedSample, ...]:
        """One unit's queued readings, each with the instant it arrived."""
        return self._clients[unit_identifier].drain_records(maximum_samples)

    def drain_all_attitude_records(self, maximum_records: int = 0) -> dict[int, tuple[ReceivedAttitude, ...]]:
        """Every unit's queued attitude bursts, keyed by unit, empties omitted.

        The same contract as `drain_all_records`, for the link the artificial
        horizon is drawn from. Draining removes them, so only the recorder calls
        this; the status window reads the latest packet off the snapshot.
        """
        drained = {unit_identifier: self._imu_clients[unit_identifier].drain_records(maximum_records) for unit_identifier in self.unit_identifiers}
        return {unit: records for unit, records in drained.items() if records}

    def drain_all_altimeter_records(self, maximum_records: int = 0) -> dict[int, tuple[ReceivedDistance, ...]]:
        """Every unit's queued altimeter replies, keyed by unit, empties omitted."""
        drained = {unit_identifier: self._altimeter_clients[unit_identifier].drain_records(maximum_records) for unit_identifier in self.unit_identifiers}
        return {unit: records for unit, records in drained.items() if records}

    def drain_all_records(self, maximum_samples: int = 0) -> dict[int, tuple[ReceivedSample, ...]]:
        """Every unit's queued readings, keyed by unit, units with none omitted.

        Omitting the empty ones rather than mapping them to an empty tuple is
        what lets a caller write "a unit that reported nothing produces no file"
        without restating the rule.
        """
        drained = {unit_identifier: self.drain_records(unit_identifier, maximum_samples) for unit_identifier in self.unit_identifiers}
        return {unit: records for unit, records in drained.items() if records}
