"""Strict parsing, encoding, and newline framing for GDAT2 telemetry."""

from __future__ import annotations

import math
import re
import struct
from dataclasses import dataclass

#: The field map, from `UATR_TDM/docs/GDAT2_TELEMETRY.md`, confirmed against
#: buoy 3 on 2026-08-19 with a captured sentence carrying real values.
#:
#: **This map was wrong until 2026-08-23 and every field was shifted by one.**
#: The previous map came from the legacy console's `GDAT2_VERSI = '2026-08-08'`,
#: which begins with a `cpu_temp_c` the firmware does not send and has no
#: `depth_temp_c`, which it does. Nothing catches that: the sentence frames, the
#: checksum passes, and every value decodes to a plausible number for the field
#: one place along. What it actually produced on the captured sentence:
#:
#:     depth_m            18.6 m   was the depth sensor's TEMPERATURE, 18.6 C
#:                                 (the real depth, 13.3 m, was read as voltage)
#:     roll_deg            2.5     was pitch
#:     pitch_deg          26.3     was yaw
#:     yaw_deg         6.6e-42     was the altimeter distance, a u32 read as f32
#:
#: Two consequences worth keeping in mind when reading anything recorded before
#: that date. Yaw always decoded to approximately zero, so a heading from
#: telemetry was never available and looked exactly like a field the firmware
#: never fills. And tilt was read as 26 degrees, past the ten-degree limit in
#: `domain/orientation.py`, so every live orientation transform was refused.
GDAT2_FLOAT_FIELD_INDICES = frozenset((0, 1, 2, 3, 4, 5, 6))
GDAT2_FIELD_NAMES = (
    "leak_v",
    "voltage_v",
    "depth_m",
    "depth_temp_c",
    "roll_deg",
    "pitch_deg",
    "yaw_deg",
    "altimeter_dist_mm",
    "altimeter_conf_pct",
    "digital_io",
)
MAXIMUM_UINT32 = (1 << 32) - 1
MAXIMUM_UINT8 = (1 << 8) - 1
DEFAULT_MAXIMUM_LINE_BYTES = 1_024
DEFAULT_MAXIMUM_BUFFER_BYTES = 4_096

_HEX_FIELD = re.compile(r"[0-9A-Fa-f]{1,8}\Z")
_CHECKSUM = re.compile(r"[0-9A-Fa-f]{2}\Z")


class Gdat2DecodeError(ValueError):
    """One GDAT2 sentence failed structural or checksum validation."""


@dataclass(frozen=True)
class Gdat2Sample:
    """Decoded values from one accepted GDAT2 sentence.

    The optional sequence and counter are retained but deliberately have no
    hardware meaning assigned to them: no authoritative specification for
    those fields is available.
    """

    leak_v: float
    voltage_v: float
    depth_m: float
    #: The depth sensor's own temperature, not the water's, and not the board's.
    #: It is here because the firmware sends it, not because anything uses it.
    depth_temp_c: float
    roll_deg: float
    pitch_deg: float
    yaw_deg: float
    altimeter_dist_mm: int
    altimeter_conf_pct: int
    #: bit 0 = OPEN, bit 1 = CLOSE, on the motor actuator.
    digital_io: int
    sequence: int | None = None
    counter: int | None = None
    raw_fields: tuple[str, ...] = ()

    def values(self) -> tuple[float | int, ...]:
        return (
            self.leak_v,
            self.voltage_v,
            self.depth_m,
            self.depth_temp_c,
            self.roll_deg,
            self.pitch_deg,
            self.yaw_deg,
            self.altimeter_dist_mm,
            self.altimeter_conf_pct,
            self.digital_io,
        )


@dataclass(frozen=True)
class FramingResult:
    lines: tuple[bytes, ...]
    oversized_frames: int


class Gdat2LineFramer:
    """Retain incomplete TCP data and emit complete bounded newline frames."""

    def __init__(
        self,
        *,
        maximum_line_bytes: int = DEFAULT_MAXIMUM_LINE_BYTES,
        maximum_buffer_bytes: int = DEFAULT_MAXIMUM_BUFFER_BYTES,
    ) -> None:
        if maximum_line_bytes <= 0:
            raise ValueError("maximum line bytes must be positive")
        if maximum_buffer_bytes < maximum_line_bytes:
            raise ValueError("maximum buffer bytes cannot be smaller than a line")
        self._maximum_line_bytes = maximum_line_bytes
        self._maximum_buffer_bytes = maximum_buffer_bytes
        self._buffer = bytearray()

    @property
    def buffered_bytes(self) -> int:
        return len(self._buffer)

    def reset(self) -> None:
        self._buffer.clear()

    def feed(self, data: bytes) -> FramingResult:
        if not isinstance(data, bytes):
            raise TypeError("framer input must be bytes")
        self._buffer.extend(data)
        lines: list[bytes] = []
        oversized = 0

        while True:
            newline = self._buffer.find(b"\n")
            if newline < 0:
                break
            line = bytes(self._buffer[:newline])
            del self._buffer[: newline + 1]
            if line.endswith(b"\r"):
                line = line[:-1]
            if len(line) > self._maximum_line_bytes:
                oversized += 1
            elif line:
                lines.append(line)

        if len(self._buffer) > self._maximum_buffer_bytes:
            self._buffer.clear()
            oversized += 1
        return FramingResult(tuple(lines), oversized)


def gdat2_checksum(body: str) -> int:
    """Return the XOR of ASCII bytes between ``$`` and ``*``."""
    checksum = 0
    try:
        encoded = body.encode("ascii", "strict")
    except UnicodeEncodeError as error:
        raise ValueError("GDAT2 checksum body must be ASCII") from error
    for byte in encoded:
        checksum ^= byte
    return checksum


def parse_gdat2(sentence: bytes | str) -> Gdat2Sample:
    """Decode one complete GDAT2 sentence.

    The ten ``ulRaw`` words are hexadecimal. The optional sequence and counter
    suffix is decimal ASCII: an eleven-field sentence carries only the counter,
    while the hardware-confirmed twelve-field form carries sequence then
    counter. Keeping those radices separate is part of the wire contract.
    """
    if isinstance(sentence, bytes):
        try:
            text = sentence.decode("ascii", "strict")
        except UnicodeDecodeError as error:
            raise Gdat2DecodeError("GDAT2 sentence must be ASCII") from error
    elif isinstance(sentence, str):
        text = sentence
        try:
            text.encode("ascii", "strict")
        except UnicodeEncodeError as error:
            raise Gdat2DecodeError("GDAT2 sentence must be ASCII") from error
    else:
        raise TypeError("GDAT2 sentence must be bytes or text")

    text = text.rstrip("\r\n")
    if not text.startswith("$") or text.count("*") != 1:
        raise Gdat2DecodeError("GDAT2 sentence must contain one '$...*checksum' frame")
    body, checksum_text = text[1:].split("*", 1)
    if _CHECKSUM.fullmatch(checksum_text) is None:
        raise Gdat2DecodeError("GDAT2 checksum must contain exactly two hexadecimal digits")
    if gdat2_checksum(body) != int(checksum_text, 16):
        raise Gdat2DecodeError("GDAT2 checksum mismatch")

    fields = body.split(",")
    if not fields or fields[0] != "GDAT2":
        raise Gdat2DecodeError("unsupported telemetry sentence type")
    encoded_fields = fields[1:]
    if len(encoded_fields) not in (10, 11, 12):
        raise Gdat2DecodeError("GDAT2 sentence must contain 10, 11, or 12 fields")
    for value in encoded_fields[:10]:
        if _HEX_FIELD.fullmatch(value) is None:
            raise Gdat2DecodeError("GDAT2 raw fields must contain 1 to 8 hexadecimal digits")

    raw_fields = tuple(value.upper() for value in encoded_fields[:10])
    decoded: list[float | int] = []
    for index, value in enumerate(raw_fields):
        raw = int(value, 16)
        if index in GDAT2_FLOAT_FIELD_INDICES:
            decoded.append(struct.unpack(">f", struct.pack(">I", raw))[0])
        else:
            decoded.append(raw)
    sequence = None
    counter = None
    if len(encoded_fields) == 12:
        sequence = _parse_decimal_unsigned(encoded_fields[10], "sequence", MAXIMUM_UINT32)
        counter = _parse_decimal_unsigned(encoded_fields[11], "counter", MAXIMUM_UINT8)
    elif len(encoded_fields) == 11:
        counter = _parse_decimal_unsigned(encoded_fields[10], "counter", MAXIMUM_UINT8)
    # Cast by the field's own kind rather than by a hand-written list of
    # positions: the list is a second copy of the field map, and the two drifting
    # apart is exactly the defect that shifted this decoder by one field.
    return Gdat2Sample(
        *(float(value) if index in GDAT2_FLOAT_FIELD_INDICES else int(value) for index, value in enumerate(decoded)),
        sequence,
        counter,
        raw_fields,
    )


def encode_gdat2(sample: Gdat2Sample) -> bytes:
    """Encode a sample using canonical eight-digit uppercase raw fields."""
    fields: list[str] = []
    for index, value in enumerate(sample.values()):
        if index in GDAT2_FLOAT_FIELD_INDICES:
            number = float(value)
            if not math.isfinite(number):
                raise ValueError(f"{GDAT2_FIELD_NAMES[index]} must be finite")
            try:
                raw = struct.unpack(">I", struct.pack(">f", number))[0]
            except OverflowError as error:
                raise ValueError(f"{GDAT2_FIELD_NAMES[index]} cannot be represented as float32") from error
        else:
            raw = _checked_uint32(value, GDAT2_FIELD_NAMES[index])
        fields.append(f"{raw:08X}")

    if sample.sequence is not None and sample.counter is None:
        raise ValueError("GDAT2 sequence requires a counter")
    if sample.sequence is not None:
        fields.append(str(_checked_unsigned(sample.sequence, "sequence", MAXIMUM_UINT32)))
    if sample.counter is not None:
        fields.append(str(_checked_unsigned(sample.counter, "counter", MAXIMUM_UINT8)))
    body = "GDAT2," + ",".join(fields)
    return f"${body}*{gdat2_checksum(body):02X}".encode("ascii")


def _checked_uint32(value: object, name: str) -> int:
    return _checked_unsigned(value, name, MAXIMUM_UINT32)


def _checked_unsigned(value: object, name: str, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an unsigned integer from 0 to {maximum}")
    if not 0 <= value <= maximum:
        raise ValueError(f"{name} must be an unsigned integer from 0 to {maximum}")
    return value


def _parse_decimal_unsigned(value: str, name: str, maximum: int) -> int:
    if not value or not value.isascii() or not value.isdecimal():
        raise Gdat2DecodeError(f"GDAT2 {name} must be unsigned decimal ASCII")
    parsed = int(value, 10)
    if parsed > maximum:
        raise Gdat2DecodeError(f"GDAT2 {name} must be between 0 and {maximum}")
    return parsed
