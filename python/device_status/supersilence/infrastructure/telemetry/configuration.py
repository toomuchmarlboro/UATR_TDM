"""Persisted system-wide configuration for three telemetry devices per buoy."""

from __future__ import annotations

import ipaddress
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType

from supersilence.infrastructure.settings.repository import (
    SCOPE_SYSTEM,
    SettingsRepository,
)

DEFAULT_SENSOR_ADDRESSES = {
    1: "127.0.0.12",
    2: "127.0.0.13",
    3: "127.0.0.14",
    4: "127.0.0.15",
}
DEFAULT_IMU_SENSOR_ADDRESSES = {
    1: "127.0.0.22",
    2: "127.0.0.23",
    3: "127.0.0.24",
    4: "127.0.0.25",
}
DEFAULT_ALTIMETER_SENSOR_ADDRESSES = {
    1: "127.0.0.32",
    2: "127.0.0.33",
    3: "127.0.0.34",
    4: "127.0.0.35",
}
DEFAULT_PORT = 8_080
DEFAULT_CONNECTION_TIMEOUT_SECONDS = 3.0
DEFAULT_RECONNECT_INTERVAL_SECONDS = 5.0
DEFAULT_STALE_THRESHOLD_SECONDS = 1.0

ENABLED_KEY = "telemetry.enabled"
SENSOR_ADDRESSES_KEY = "telemetry.sensor_addresses"
GDAT2_SENSOR_ADDRESSES_KEY = "telemetry.gdat2_sensor_addresses"
IMU_SENSOR_ADDRESSES_KEY = "telemetry.imu_sensor_addresses"
ALTIMETER_SENSOR_ADDRESSES_KEY = "telemetry.altimeter_sensor_addresses"
PORT_KEY = "telemetry.port"
CONNECTION_TIMEOUT_KEY = "telemetry.connection_timeout_seconds"
RECONNECT_INTERVAL_KEY = "telemetry.reconnect_interval_seconds"
STALE_THRESHOLD_KEY = "telemetry.stale_threshold_seconds"
COMPASS_OFFSETS_KEY = "telemetry.compass_offsets_degrees"
DEFAULT_COMPASS_OFFSETS = {identifier: 0.0 for identifier in DEFAULT_SENSOR_ADDRESSES}


@dataclass(frozen=True)
class TelemetryConfiguration:
    enabled: bool
    sensor_addresses: Mapping[int, str]
    port: int
    connection_timeout_seconds: float
    reconnect_interval_seconds: float
    stale_threshold_seconds: float
    imu_sensor_addresses: Mapping[int, str] | None = None
    altimeter_sensor_addresses: Mapping[int, str] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.enabled, bool):
            raise ValueError("telemetry enabled state must be a boolean")
        addresses = _validated_addresses(self.sensor_addresses, "GDAT2")
        imu_addresses = _validated_addresses(self.imu_sensor_addresses or DEFAULT_IMU_SENSOR_ADDRESSES, "IMU")
        altimeter_addresses = _validated_addresses(
            self.altimeter_sensor_addresses or DEFAULT_ALTIMETER_SENSOR_ADDRESSES,
            "altimeter",
        )
        all_addresses = (*addresses.values(), *imu_addresses.values(), *altimeter_addresses.values())
        if len(set(all_addresses)) != len(all_addresses):
            raise ValueError("telemetry device addresses must be unique across all roles")
        if isinstance(self.port, bool) or not isinstance(self.port, int):
            raise ValueError("telemetry port must be an integer")
        if not 1 <= self.port <= 65_535:
            raise ValueError("telemetry port must be between 1 and 65535")
        for value, label in (
            (self.connection_timeout_seconds, "connection timeout"),
            (self.reconnect_interval_seconds, "reconnect interval"),
            (self.stale_threshold_seconds, "stale threshold"),
        ):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"telemetry {label} must be a number")
            if not math.isfinite(float(value)) or float(value) <= 0:
                raise ValueError(f"telemetry {label} must be positive")
        object.__setattr__(self, "sensor_addresses", MappingProxyType(addresses))
        object.__setattr__(self, "imu_sensor_addresses", MappingProxyType(imu_addresses))
        object.__setattr__(
            self,
            "altimeter_sensor_addresses",
            MappingProxyType(altimeter_addresses),
        )
        object.__setattr__(self, "connection_timeout_seconds", float(self.connection_timeout_seconds))
        object.__setattr__(self, "reconnect_interval_seconds", float(self.reconnect_interval_seconds))
        object.__setattr__(self, "stale_threshold_seconds", float(self.stale_threshold_seconds))

    def save(self, settings: SettingsRepository) -> None:
        settings.set(SCOPE_SYSTEM, ENABLED_KEY, self.enabled)
        settings.set(
            SCOPE_SYSTEM,
            SENSOR_ADDRESSES_KEY,
            [self.sensor_addresses[index] for index in range(1, 5)],
        )
        settings.set(
            SCOPE_SYSTEM,
            GDAT2_SENSOR_ADDRESSES_KEY,
            [self.sensor_addresses[index] for index in range(1, 5)],
        )
        settings.set(
            SCOPE_SYSTEM,
            IMU_SENSOR_ADDRESSES_KEY,
            [self.imu_sensor_addresses[index] for index in range(1, 5)],
        )
        settings.set(
            SCOPE_SYSTEM,
            ALTIMETER_SENSOR_ADDRESSES_KEY,
            [self.altimeter_sensor_addresses[index] for index in range(1, 5)],
        )
        settings.set(SCOPE_SYSTEM, PORT_KEY, self.port)
        settings.set(SCOPE_SYSTEM, CONNECTION_TIMEOUT_KEY, self.connection_timeout_seconds)
        settings.set(SCOPE_SYSTEM, RECONNECT_INTERVAL_KEY, self.reconnect_interval_seconds)
        settings.set(SCOPE_SYSTEM, STALE_THRESHOLD_KEY, self.stale_threshold_seconds)


def default_telemetry_configuration() -> TelemetryConfiguration:
    return TelemetryConfiguration(
        False,
        DEFAULT_SENSOR_ADDRESSES,
        DEFAULT_PORT,
        DEFAULT_CONNECTION_TIMEOUT_SECONDS,
        DEFAULT_RECONNECT_INTERVAL_SECONDS,
        DEFAULT_STALE_THRESHOLD_SECONDS,
        DEFAULT_IMU_SENSOR_ADDRESSES,
        DEFAULT_ALTIMETER_SENSOR_ADDRESSES,
    )


def load_telemetry_configuration(
    settings: SettingsRepository,
) -> TelemetryConfiguration:
    """Load and materialize a complete validated system-wide configuration."""
    defaults = default_telemetry_configuration()
    enabled = settings.get(SCOPE_SYSTEM, ENABLED_KEY, defaults.enabled)
    legacy_addresses = _stored_address_list(
        settings,
        SENSOR_ADDRESSES_KEY,
        list(defaults.sensor_addresses.values()),
        "telemetry",
    )
    stored_addresses = _stored_address_list(
        settings,
        GDAT2_SENSOR_ADDRESSES_KEY,
        legacy_addresses,
        "GDAT2",
    )
    official_roles = _derived_official_role_addresses(stored_addresses)
    imu_addresses = _stored_address_list(
        settings,
        IMU_SENSOR_ADDRESSES_KEY,
        (official_roles[0] if official_roles is not None else list(defaults.imu_sensor_addresses.values())),
        "IMU",
    )
    altimeter_addresses = _stored_address_list(
        settings,
        ALTIMETER_SENSOR_ADDRESSES_KEY,
        (official_roles[1] if official_roles is not None else list(defaults.altimeter_sensor_addresses.values())),
        "altimeter",
    )
    configuration = TelemetryConfiguration(
        enabled,
        {index: stored_addresses[index - 1] for index in range(1, 5)},
        settings.get(SCOPE_SYSTEM, PORT_KEY, defaults.port),
        settings.get(
            SCOPE_SYSTEM,
            CONNECTION_TIMEOUT_KEY,
            defaults.connection_timeout_seconds,
        ),
        settings.get(
            SCOPE_SYSTEM,
            RECONNECT_INTERVAL_KEY,
            defaults.reconnect_interval_seconds,
        ),
        settings.get(
            SCOPE_SYSTEM,
            STALE_THRESHOLD_KEY,
            defaults.stale_threshold_seconds,
        ),
        {index: imu_addresses[index - 1] for index in range(1, 5)},
        {index: altimeter_addresses[index - 1] for index in range(1, 5)},
    )
    configuration.save(settings)
    return configuration


def load_compass_offsets(settings: SettingsRepository) -> Mapping[int, float]:
    """Load validated per-unit compass offsets, materializing defaults when absent."""
    missing = object()
    stored = settings.get(SCOPE_SYSTEM, COMPASS_OFFSETS_KEY, missing)
    materialize_defaults = stored is missing
    if materialize_defaults:
        stored = DEFAULT_COMPASS_OFFSETS
    if not isinstance(stored, Mapping):
        raise ValueError("stored compass offsets must be a mapping")
    offsets: dict[int, float] = {}
    for identifier in DEFAULT_SENSOR_ADDRESSES:
        value = stored.get(str(identifier), stored.get(identifier, 0.0))
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise ValueError(f"compass offset for unit {identifier} must be a finite number")
        offsets[identifier] = _normalise_signed_yaw(float(value))
    if materialize_defaults:
        settings.set(SCOPE_SYSTEM, COMPASS_OFFSETS_KEY, {str(identifier): value for identifier, value in offsets.items()})
    return MappingProxyType(offsets)


def save_compass_offset(settings: SettingsRepository, unit_identifier: int, offset_degrees: float) -> Mapping[int, float]:
    """Persist one signed compass offset without changing the array mounting offsets."""
    if unit_identifier not in DEFAULT_SENSOR_ADDRESSES:
        raise ValueError("compass offset unit must be between 1 and 4")
    if isinstance(offset_degrees, bool) or not isinstance(offset_degrees, (int, float)) or not math.isfinite(float(offset_degrees)):
        raise ValueError("compass offset must be a finite number")
    offsets = dict(load_compass_offsets(settings))
    offsets[unit_identifier] = _normalise_signed_yaw(float(offset_degrees))
    settings.set(SCOPE_SYSTEM, COMPASS_OFFSETS_KEY, {str(identifier): value for identifier, value in offsets.items()})
    return MappingProxyType(offsets)


def _normalise_signed_yaw(value: float) -> float:
    """Use north=0, east=+90, west=-90, and south=-180 degrees."""
    return (value + 180.0) % 360.0 - 180.0


def _validated_addresses(addresses: Mapping[int, str], role: str) -> dict[int, str]:
    if set(addresses) != set(DEFAULT_SENSOR_ADDRESSES):
        raise ValueError(f"{role} telemetry configuration must contain units 1 through 4")
    validated = {identifier: str(address) for identifier, address in addresses.items()}
    if len(set(validated.values())) != len(validated):
        raise ValueError(f"{role} telemetry sensor addresses must be unique")
    for unit_identifier, address in validated.items():
        try:
            ipaddress.IPv4Address(address)
        except ValueError as error:
            raise ValueError(f"{role} sensor address for unit {unit_identifier} must be an IPv4 address") from error
    return validated


def _stored_address_list(
    settings: SettingsRepository,
    key: str,
    default: Sequence[str],
    role: str,
) -> list[str]:
    stored = settings.get(SCOPE_SYSTEM, key, list(default))
    if isinstance(stored, (str, bytes)) or not isinstance(stored, Sequence):
        raise ValueError(f"stored {role} sensor addresses must be a four-item list")
    if len(stored) != 4:
        raise ValueError(f"stored {role} sensor addresses must contain four entries")
    return [str(address) for address in stored]


def _derived_official_role_addresses(
    gdat2_addresses: Sequence[str],
) -> tuple[list[str], list[str]] | None:
    """Expand only the verified ``192.168.3.1<buoy>0`` topology.

    Arbitrary operator addresses are not arithmetic templates. Leaving their
    new roles on disabled-development loopbacks is safer than dialing a guessed
    neighbour which may be a real, different device.
    """
    expected = [f"192.168.3.{100 + unit * 10}" for unit in range(1, 5)]
    if list(gdat2_addresses) != expected:
        return None
    return (
        [f"192.168.3.{101 + unit * 10}" for unit in range(1, 5)],
        [f"192.168.3.{102 + unit * 10}" for unit in range(1, 5)],
    )
