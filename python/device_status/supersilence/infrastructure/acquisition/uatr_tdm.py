"""Current UATR-TDM UDP payload format and sample decoding."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

import numpy as np

MAGIC = b"\xad\xa1\x97\x78"
# The deployed FPGA now sends the DSP-rate stream directly.  Packet geometry
# and all diagnostic bytes remain unchanged; only the cadence changed.
SAMPLE_RATE = 24_000
CHANNEL_COUNT = 16
FRAMES_PER_PACKET = 8
FRAME_SIZE = 50
PAYLOAD_SIZE = 10 + FRAMES_PER_PACKET * FRAME_SIZE
DEFAULT_PORT = 5005

#: The UDP source port every unit transmits from.
#:
#: A constant in the firmware, not an ephemeral port: `udp_tx_core.vhd` writes
#: it into the UDP header beside the destination — "Source Port MSB (5005 =
#: x138D)". It is part of the wire contract, which is why it lives here with the
#: rest of it, and it is what lets a receiver hold one socket per unit: a
#: connected socket matches on the whole address pair, and the pair is only
#: stable because this port is.
FIRMWARE_SOURCE_PORT = 5005

# Readbacks emitted by the current packet_formatter.vhd header.
PLL_CONTROL_READBACK = 0x03
SAI_CONTROL_READBACK = 0x5B

#: Which frame's status byte carries the 48 V phantom readback.
#:
#: `packet_formatter.vhd` puts one status byte in each frame's index-MSB
#: position — the byte that was always zero because a frame index never exceeds
#: seven. Frame 1 holds `dbg_status2`, which `top_system.vhd` fills with the
#: phantom gates. That is payload byte 60, and the firmware's own
#: `docs/PHANTOM_POWER.md` diagnosing table is written against byte 60.
PHANTOM_STATUS_FRAME = 1

#: Bit 7 of that byte is hard-wired '1' in `dbg_status2_int`. It is the only
#: way to tell a populated status byte from the zero pad an older bitstream
#: sent, and an older bitstream is exactly what a field unit that has not been
#: reflashed is running.
_PHANTOM_POPULATED_BIT = 0x80
_PHANTOM_DRIVEN_BIT = 0x40
_PHANTOM_REQUESTED_BIT = 0x20
_PHANTOM_STAGED_BIT = 0x10
_PHANTOM_PERMITTED_BIT = 0x08

MINIMUM_SAMPLE = -(1 << 23)
MAXIMUM_SAMPLE = (1 << 23) - 1

__all__ = [
    "CHANNEL_COUNT",
    "DEFAULT_PORT",
    "FIRMWARE_SOURCE_PORT",
    "FRAMES_PER_PACKET",
    "FRAME_SIZE",
    "MAGIC",
    "MAXIMUM_SAMPLE",
    "MINIMUM_SAMPLE",
    "PAYLOAD_SIZE",
    "PHANTOM_STATUS_FRAME",
    "PLL_CONTROL_READBACK",
    "SAI_CONTROL_READBACK",
    "SAMPLE_RATE",
    "DecodedPacket",
    "DecodedPacketBatch",
    "DecodedSampleBatch",
    "PhantomPowerReadback",
    "SampleQuality",
    "decode_packet",
    "decode_phantom_power",
    "encode_phantom_power_status",
    "decode_packets",
    "decode_sample_batch",
    "decode_sample_blob",
    "encode_packet",
    "encode_packets",
]


class SampleQuality(Enum):
    """Quality attached to each sample in an assembled stream."""

    RECEIVED = "received"
    INTERPOLATED = "interpolated"
    MISSING = "missing"
    DISCONTINUOUS = "discontinuous"


@dataclass(frozen=True)
class PhantomPowerReadback:
    """What the board says it is doing with 48 V, decoded from one packet.

    Asserted, not measured. `en_48v` is an FPGA output with no sense line back,
    so a dead DC-DC converter, a blown fuse or an open enable trace all still
    read here as on. This answers "is the FPGA driving the enable", which is
    the only question the hardware can answer, and it is still far better than
    the alternative the console had before — showing the operator whatever
    button they last pressed.

    `driven` is the AND of the other three gates, so whichever one is false
    names the cause. All three set with `driven` false is the watchdog, which
    needs no bit of its own because nothing else produces that combination.
    """

    driven: bool
    requested: bool
    staged: bool
    permitted: bool

    @property
    def watchdog_tripped(self) -> bool:
        """Every gate open and the pin still low — the FPGA is overriding.

        Only reachable on a bitstream built with `C_PHANTOM_WATCHDOG` true.
        """
        return not self.driven and self.requested and self.staged and self.permitted


def decode_phantom_power(diagnostic_bytes: Sequence[int]) -> PhantomPowerReadback | None:
    """Decode the 48 V readback out of one packet's per-frame status bytes.

    `None` where there is no answer to give: too few status bytes, or a
    bitstream that predates the readback and leaves the byte as the zero pad it
    used to be. A unit that has not been reflashed is the ordinary reason, so
    this is a normal outcome and not an error — the caller shows "unknown"
    rather than inventing an off.
    """
    if len(diagnostic_bytes) <= PHANTOM_STATUS_FRAME:
        return None
    status = int(diagnostic_bytes[PHANTOM_STATUS_FRAME])
    if not status & _PHANTOM_POPULATED_BIT:
        return None
    return PhantomPowerReadback(
        bool(status & _PHANTOM_DRIVEN_BIT),
        bool(status & _PHANTOM_REQUESTED_BIT),
        bool(status & _PHANTOM_STAGED_BIT),
        bool(status & _PHANTOM_PERMITTED_BIT),
    )


def encode_phantom_power_status(
    readback: PhantomPowerReadback,
) -> int:
    """The status byte a board reporting `readback` would send.

    The inverse of :func:`decode_phantom_power` for one byte, so a simulator or
    a test can produce a packet the real decoder reads the same way it reads
    hardware. The low three bits are the I2C self-test bits, which belong to a
    different reader and are left clear here.
    """
    status = _PHANTOM_POPULATED_BIT
    if readback.driven:
        status |= _PHANTOM_DRIVEN_BIT
    if readback.requested:
        status |= _PHANTOM_REQUESTED_BIT
    if readback.staged:
        status |= _PHANTOM_STAGED_BIT
    if readback.permitted:
        status |= _PHANTOM_PERMITTED_BIT
    return status


@dataclass(frozen=True)
class DecodedPacket:
    """One validated wire packet, decoded into signed channel samples."""

    sequence: int
    samples: np.ndarray
    diagnostic_bytes: tuple[int, ...]
    frame_indices: tuple[int, ...]
    pll_control: int
    sai_control: int


@dataclass(frozen=True)
class DecodedPacketBatch:
    """Valid decoded packets plus the number rejected during batch validation."""

    packets: tuple[DecodedPacket, ...]
    invalid_packets: int


@dataclass(frozen=True)
class DecodedSampleBatch:
    """Vectorized packet fields used by the real-time acquisition consumer."""

    sequences: np.ndarray
    samples: np.ndarray
    diagnostic_bytes: np.ndarray
    pll_controls: np.ndarray
    sai_controls: np.ndarray
    invalid_packets: int


def decode_packet(payload: bytes) -> DecodedPacket:
    """Validate and decode one current-firmware UATR-TDM packet.

    The returned sample array has shape ``(8, 16)`` and dtype ``int32``.
    Validation is deliberately strict: malformed frames must not enter the
    sample stream where they could be mistaken for valid silence.
    """
    result = decode_packets((payload,))
    if result.invalid_packets:
        if len(payload) != PAYLOAD_SIZE:
            raise ValueError(f"expected {PAYLOAD_SIZE}-byte payload, got {len(payload)}")
        if payload[:4] != MAGIC:
            raise ValueError("invalid UATR-TDM packet magic")
        raise ValueError("invalid UATR-TDM frame index sequence")
    return result.packets[0]


def decode_packets(payloads: Sequence[bytes]) -> DecodedPacketBatch:
    """Validate and decode a packet batch with no Python per-sample loop.

    Invalid payloads are omitted and counted so one malformed datagram cannot
    discard the surrounding valid stream. The heavy int24 conversion is one
    vectorized NumPy operation over the entire valid batch.
    """
    batch = decode_sample_batch(payloads)
    frame_indices = tuple(range(FRAMES_PER_PACKET))
    decoded = tuple(
        DecodedPacket(
            int(batch.sequences[index]),
            batch.samples[index],
            tuple(int(value) for value in batch.diagnostic_bytes[index]),
            frame_indices,
            int(batch.pll_controls[index]),
            int(batch.sai_controls[index]),
        )
        for index in range(batch.samples.shape[0])
    )
    return DecodedPacketBatch(decoded, batch.invalid_packets)


def decode_sample_batch(payloads: Sequence[bytes]) -> DecodedSampleBatch:
    """Decode directly to immutable arrays for the real-time consumer path."""
    candidates = [payload for payload in payloads if len(payload) == PAYLOAD_SIZE and payload[:4] == MAGIC]
    invalid_packets = len(payloads) - len(candidates)
    if not candidates:
        return _empty_sample_batch(invalid_packets)
    return _decode_wire(
        np.frombuffer(b"".join(candidates), dtype=np.uint8).reshape(len(candidates), PAYLOAD_SIZE),
        invalid_packets,
    )


def decode_sample_blob(blob: bytes, packet_count: int) -> DecodedSampleBatch:
    """Decode packets that are already contiguous and already the right size.

    The receive path stages datagrams end to end in one buffer, so the join and
    the per-packet size filter that :func:`decode_sample_batch` has to do are
    both unnecessary work here. Magic is still checked, vectorized: a wrong-magic
    datagram from the right source address is a real possibility and is counted
    as invalid rather than decoded.
    """
    if packet_count <= 0:
        return _empty_sample_batch(0)
    wire = np.frombuffer(blob, dtype=np.uint8, count=packet_count * PAYLOAD_SIZE)
    wire = wire.reshape(packet_count, PAYLOAD_SIZE)
    magic = np.frombuffer(MAGIC, dtype=np.uint8)
    correct_magic = np.all(wire[:, :4] == magic, axis=1)
    invalid_packets = int(np.count_nonzero(~correct_magic))
    if invalid_packets:
        wire = wire[correct_magic]
    if not wire.shape[0]:
        return _empty_sample_batch(invalid_packets)
    return _decode_wire(wire, invalid_packets)


def _decode_wire(wire: np.ndarray, invalid_packets: int) -> DecodedSampleBatch:
    """Shared vectorized decode for both entry points."""
    frames = wire[:, 10:].reshape(wire.shape[0], FRAMES_PER_PACKET, FRAME_SIZE)
    expected_indices = np.arange(FRAMES_PER_PACKET, dtype=np.uint8)
    valid_indices = np.all(frames[:, :, 1] == expected_indices, axis=1)
    invalid_packets += int(np.count_nonzero(~valid_indices))
    if not np.any(valid_indices):
        return _empty_sample_batch(invalid_packets)

    valid_wire = wire[valid_indices]
    valid_frames = frames[valid_indices]
    packed = valid_frames[:, :, 2:].reshape(-1, FRAMES_PER_PACKET, CHANNEL_COUNT, 3).astype(np.int32)
    unsigned = (packed[:, :, :, 0] << 16) | (packed[:, :, :, 1] << 8) | packed[:, :, :, 2]
    samples = (unsigned ^ 0x800000) - 0x800000
    sequences = (
        (valid_wire[:, 4].astype(np.uint32) << 24)
        | (valid_wire[:, 5].astype(np.uint32) << 16)
        | (valid_wire[:, 6].astype(np.uint32) << 8)
        | valid_wire[:, 7].astype(np.uint32)
    )
    diagnostics = valid_frames[:, :, 0].copy()
    pll_controls = valid_wire[:, 8].copy()
    sai_controls = valid_wire[:, 9].copy()
    for values in (sequences, samples, diagnostics, pll_controls, sai_controls):
        values.setflags(write=False)
    return DecodedSampleBatch(
        sequences,
        samples,
        diagnostics,
        pll_controls,
        sai_controls,
        invalid_packets,
    )


def _empty_sample_batch(invalid_packets: int) -> DecodedSampleBatch:
    sequences = np.empty(0, dtype=np.uint32)
    samples = np.empty((0, FRAMES_PER_PACKET, CHANNEL_COUNT), dtype=np.int32)
    diagnostics = np.empty((0, FRAMES_PER_PACKET), dtype=np.uint8)
    controls = np.empty(0, dtype=np.uint8)
    for values in (sequences, samples, diagnostics, controls):
        values.setflags(write=False)
    return DecodedSampleBatch(
        sequences,
        samples,
        diagnostics,
        controls,
        controls,
        invalid_packets,
    )


def encode_packet(
    sequence: int,
    samples: np.ndarray,
    *,
    diagnostic_bytes: bytes = bytes(8),
    pll_control: int = PLL_CONTROL_READBACK,
    sai_control: int = SAI_CONTROL_READBACK,
) -> bytes:
    """Encode eight frames of signed 24-bit, 16-channel audio."""
    return encode_packets(
        sequence,
        samples,
        diagnostic_bytes=diagnostic_bytes,
        pll_control=pll_control,
        sai_control=sai_control,
    )[0]


def encode_packets(
    first_sequence: int,
    samples: np.ndarray,
    *,
    diagnostic_bytes: bytes = bytes(8),
    pll_control: int = PLL_CONTROL_READBACK,
    sai_control: int = SAI_CONTROL_READBACK,
) -> tuple[bytes, ...]:
    """Encode a batch whose frame count is a positive multiple of eight."""
    values = np.asarray(samples)
    if values.ndim != 2 or values.shape[1] != CHANNEL_COUNT or values.shape[0] == 0 or values.shape[0] % FRAMES_PER_PACKET:
        raise ValueError(f"samples must have shape (positive multiple of 8, 16), got {values.shape}")
    if np.any(values < MINIMUM_SAMPLE) or np.any(values > MAXIMUM_SAMPLE):
        raise ValueError("samples exceed the signed 24-bit range")
    if len(diagnostic_bytes) != FRAMES_PER_PACKET:
        raise ValueError("diagnostic_bytes must contain exactly eight bytes")

    packet_count = values.shape[0] // FRAMES_PER_PACKET
    packets = np.empty((packet_count, PAYLOAD_SIZE), dtype=np.uint8)
    packets[:, :4] = np.frombuffer(MAGIC, dtype=np.uint8)
    sequences = (np.arange(packet_count, dtype=np.uint64) + first_sequence) & 0xFFFFFFFF
    packets[:, 4] = sequences >> 24
    packets[:, 5] = sequences >> 16
    packets[:, 6] = sequences >> 8
    packets[:, 7] = sequences
    packets[:, 8] = pll_control & 0xFF
    packets[:, 9] = sai_control & 0xFF

    unsigned = values.astype(np.int64, copy=False) & 0xFFFFFF
    audio = np.empty((values.shape[0], CHANNEL_COUNT, 3), dtype=np.uint8)
    audio[:, :, 0] = unsigned >> 16
    audio[:, :, 1] = unsigned >> 8
    audio[:, :, 2] = unsigned
    frames = np.empty((values.shape[0], FRAME_SIZE), dtype=np.uint8)
    frames[:, 0] = np.tile(np.frombuffer(diagnostic_bytes, dtype=np.uint8), packet_count)
    frames[:, 1] = np.tile(np.arange(FRAMES_PER_PACKET, dtype=np.uint8), packet_count)
    frames[:, 2:] = audio.reshape(values.shape[0], CHANNEL_COUNT * 3)
    packets[:, 10:] = frames.reshape(packet_count, FRAMES_PER_PACKET * FRAME_SIZE)
    return tuple(row.tobytes() for row in packets)
