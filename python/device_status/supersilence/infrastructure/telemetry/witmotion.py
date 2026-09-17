"""Bounded framing and decoding for the deployed WitMotion IMU."""

from __future__ import annotations

import struct
from dataclasses import dataclass

WITMOTION_HEADER = 0x55
WITMOTION_PACKET_BYTES = 11
WITMOTION_MAXIMUM_BUFFER_BYTES = 4_096

ACCELERATION_PACKET = 0x51
ANGULAR_RATE_PACKET = 0x52
ANGLE_PACKET = 0x53
MAGNETIC_PACKET = 0x54
QUATERNION_PACKET = 0x59


@dataclass(frozen=True)
class WitMotionAngle:
    roll_degrees: float
    pitch_degrees: float
    yaw_degrees: float
    version: int


@dataclass(frozen=True)
class WitMotionAcceleration:
    x_g: float
    y_g: float
    z_g: float
    temperature_raw: int


@dataclass(frozen=True)
class WitMotionAngularRate:
    x_degrees_per_second: float
    y_degrees_per_second: float
    z_degrees_per_second: float
    temperature_raw: int


@dataclass(frozen=True)
class WitMotionMagnetic:
    x_raw: int
    y_raw: int
    z_raw: int
    temperature_raw: int


@dataclass(frozen=True)
class WitMotionQuaternion:
    q0: float
    q1: float
    q2: float
    q3: float


WitMotionValue = WitMotionAngle | WitMotionAcceleration | WitMotionAngularRate | WitMotionMagnetic | WitMotionQuaternion | tuple[int, int, int, int]


@dataclass(frozen=True)
class WitMotionPacket:
    packet_type: int
    raw_values: tuple[int, int, int, int]
    value: WitMotionValue


@dataclass(frozen=True)
class WitMotionFramingResult:
    packets: tuple[WitMotionPacket, ...]
    checksum_errors: int
    discarded_bytes: int


def witmotion_checksum(first_ten_bytes: bytes) -> int:
    """Return the low eight bits of the first ten frame bytes."""
    if len(first_ten_bytes) != WITMOTION_PACKET_BYTES - 1:
        raise ValueError("WitMotion checksum input must contain ten bytes")
    return sum(first_ten_bytes) & 0xFF


def encode_witmotion_packet(packet_type: int, raw_values: tuple[int, int, int, int]) -> bytes:
    """Encode one packet for captured-frame parity tests and simulators."""
    if not 0 <= packet_type <= 0xFF:
        raise ValueError("WitMotion packet type must be an unsigned byte")
    if len(raw_values) != 4:
        raise ValueError("WitMotion packets carry four signed 16-bit values")
    try:
        body = bytes((WITMOTION_HEADER, packet_type)) + struct.pack("<hhhh", *raw_values)
    except struct.error as error:
        raise ValueError("WitMotion raw values must be signed 16-bit integers") from error
    return body + bytes((witmotion_checksum(body),))


def decode_witmotion(packet_type: int, raw_values: tuple[int, int, int, int]) -> WitMotionValue:
    """Decode the verified packet types without inventing magnetic scaling."""
    first, second, third, fourth = raw_values
    if packet_type == ANGLE_PACKET:
        scale = 180.0 / 32_768.0
        return WitMotionAngle(
            first * scale,
            second * scale,
            third * scale,
            fourth & 0xFFFF,
        )
    if packet_type == ACCELERATION_PACKET:
        scale = 16.0 / 32_768.0
        return WitMotionAcceleration(first * scale, second * scale, third * scale, fourth)
    if packet_type == ANGULAR_RATE_PACKET:
        scale = 2_000.0 / 32_768.0
        return WitMotionAngularRate(first * scale, second * scale, third * scale, fourth)
    if packet_type == QUATERNION_PACKET:
        scale = 1.0 / 32_768.0
        return WitMotionQuaternion(first * scale, second * scale, third * scale, fourth * scale)
    if packet_type == MAGNETIC_PACKET:
        return WitMotionMagnetic(first, second, third, fourth)
    return raw_values


class WitMotionFramer:
    """Reassemble a fixed-length stream whose payload may also contain ``0x55``."""

    def __init__(self, *, maximum_buffer_bytes: int = WITMOTION_MAXIMUM_BUFFER_BYTES) -> None:
        if maximum_buffer_bytes < WITMOTION_PACKET_BYTES:
            raise ValueError("WitMotion maximum buffer must hold one packet")
        self._maximum_buffer_bytes = maximum_buffer_bytes
        self._buffer = bytearray()

    @property
    def buffered_bytes(self) -> int:
        return len(self._buffer)

    def reset(self) -> None:
        self._buffer.clear()

    def feed(self, data: bytes) -> WitMotionFramingResult:
        if not isinstance(data, bytes):
            raise TypeError("WitMotion framer input must be bytes")
        self._buffer.extend(data)
        packets: list[WitMotionPacket] = []
        checksum_errors = 0
        discarded_bytes = 0

        while len(self._buffer) >= WITMOTION_PACKET_BYTES:
            if self._buffer[0] != WITMOTION_HEADER:
                del self._buffer[0]
                discarded_bytes += 1
                continue
            candidate = bytes(self._buffer[:WITMOTION_PACKET_BYTES])
            if witmotion_checksum(candidate[:10]) != candidate[10]:
                # A payload byte can be 0x55. Move one byte, never one frame,
                # so a genuine packet immediately after a false header survives.
                del self._buffer[0]
                checksum_errors += 1
                discarded_bytes += 1
                continue
            packet_type = candidate[1]
            raw_values = struct.unpack("<hhhh", candidate[2:10])
            packets.append(
                WitMotionPacket(
                    packet_type,
                    raw_values,
                    decode_witmotion(packet_type, raw_values),
                )
            )
            del self._buffer[:WITMOTION_PACKET_BYTES]

        if len(self._buffer) > self._maximum_buffer_bytes:
            # Retain only a possible partial frame. There is no length field,
            # so anything older than ten trailing bytes cannot become valid.
            removed = len(self._buffer) - (WITMOTION_PACKET_BYTES - 1)
            del self._buffer[:removed]
            discarded_bytes += removed
        return WitMotionFramingResult(tuple(packets), checksum_errors, discarded_bytes)
