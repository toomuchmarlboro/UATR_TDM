"""Read-only framing and decoding for the deployed Ping1D altimeter."""

from __future__ import annotations

import struct
from dataclasses import dataclass

PING_HEADER = b"BR"
PING_MAXIMUM_PAYLOAD_BYTES = 1_024

NACK_MESSAGE = 1
GENERAL_REQUEST_MESSAGE = 6
DISTANCE_MESSAGE = 1_211
DISTANCE_SIMPLE_MESSAGE = 1_212
DISTANCE_MESSAGES = (DISTANCE_MESSAGE, DISTANCE_SIMPLE_MESSAGE)


@dataclass(frozen=True)
class PingFrame:
    message_identifier: int
    source_identifier: int
    destination_identifier: int
    payload: bytes


@dataclass(frozen=True)
class PingFramingResult:
    frames: tuple[PingFrame, ...]
    checksum_errors: int
    discarded_bytes: int


@dataclass(frozen=True)
class PingDistance:
    distance_millimetres: int
    confidence_percent: int


def ping_checksum(frame_without_checksum: bytes) -> int:
    return sum(frame_without_checksum) & 0xFFFF


def encode_ping_frame(
    message_identifier: int,
    payload: bytes = b"",
    *,
    source_identifier: int = 0,
    destination_identifier: int = 0,
) -> bytes:
    """Encode a protocol frame for read requests and parity tests."""
    for value, name, maximum in (
        (message_identifier, "message identifier", 0xFFFF),
        (source_identifier, "source identifier", 0xFF),
        (destination_identifier, "destination identifier", 0xFF),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= maximum:
            raise ValueError(f"Ping {name} must be between 0 and {maximum}")
    if not isinstance(payload, bytes):
        raise TypeError("Ping payload must be bytes")
    if len(payload) > PING_MAXIMUM_PAYLOAD_BYTES:
        raise ValueError("Ping payload is too large")
    header = PING_HEADER + struct.pack(
        "<HHBB",
        len(payload),
        message_identifier,
        source_identifier,
        destination_identifier,
    )
    body = header + payload
    return body + struct.pack("<H", ping_checksum(body))


def encode_ping_request(message_identifier: int) -> bytes:
    """Build the only command this module sends: request one reported value."""
    return encode_ping_frame(GENERAL_REQUEST_MESSAGE, struct.pack("<H", message_identifier))


def decode_ping_distance(payload: bytes) -> PingDistance | None:
    """Decode the deployed five-byte or documented wider distance payload."""
    if len(payload) == 5:
        distance, confidence = struct.unpack("<IB", payload)
        return PingDistance(distance, confidence)
    if len(payload) >= 6:
        distance, confidence = struct.unpack("<IH", payload[:6])
        return PingDistance(distance, confidence)
    return None


def decode_ping_nack(payload: bytes) -> tuple[int | None, str]:
    if len(payload) < 2:
        return None, ""
    message_identifier = struct.unpack("<H", payload[:2])[0]
    explanation = payload[2:].split(b"\0", 1)[0].decode("ascii", "replace").strip()
    return message_identifier, explanation


class PingFramer:
    """Bounded Ping v1 reassembly with header scanning after corruption."""

    def __init__(self, *, maximum_payload_bytes: int = PING_MAXIMUM_PAYLOAD_BYTES) -> None:
        if maximum_payload_bytes <= 0:
            raise ValueError("Ping maximum payload must be positive")
        self._maximum_payload_bytes = maximum_payload_bytes
        self._buffer = bytearray()

    @property
    def buffered_bytes(self) -> int:
        return len(self._buffer)

    def reset(self) -> None:
        self._buffer.clear()

    def feed(self, data: bytes) -> PingFramingResult:
        if not isinstance(data, bytes):
            raise TypeError("Ping framer input must be bytes")
        self._buffer.extend(data)
        frames: list[PingFrame] = []
        checksum_errors = 0
        discarded_bytes = 0

        while True:
            header_index = self._buffer.find(PING_HEADER)
            if header_index < 0:
                keep = 1 if self._buffer.endswith(PING_HEADER[:1]) else 0
                removed = len(self._buffer) - keep
                if removed > 0:
                    del self._buffer[:removed]
                    discarded_bytes += removed
                break
            if header_index:
                del self._buffer[:header_index]
                discarded_bytes += header_index
            if len(self._buffer) < 10:
                break
            payload_bytes, message_identifier, source, destination = struct.unpack("<HHBB", self._buffer[2:8])
            if payload_bytes > self._maximum_payload_bytes:
                del self._buffer[:2]
                discarded_bytes += 2
                continue
            frame_bytes = 8 + payload_bytes + 2
            if len(self._buffer) < frame_bytes:
                break
            candidate = bytes(self._buffer[:frame_bytes])
            expected = struct.unpack("<H", candidate[-2:])[0]
            if ping_checksum(candidate[:-2]) != expected:
                del self._buffer[:2]
                checksum_errors += 1
                discarded_bytes += 2
                continue
            frames.append(
                PingFrame(
                    message_identifier,
                    source,
                    destination,
                    candidate[8:-2],
                )
            )
            del self._buffer[:frame_bytes]

        return PingFramingResult(tuple(frames), checksum_errors, discarded_bytes)
