"""Ordered, quality-preserving sample assembly for one acquisition unit.

A lost packet used to leave a zero-filled hole marked `MISSING`, and a single
`MISSING` sample rejects the entire 24 kHz processing window it lands in. On a
link losing even 2% of datagrams that rejected most windows, and a rejected
window produces no observations, so the application went blind over losses it
could have bridged.

Very short gaps are now bridged linearly and marked `INTERPOLATED`, which is the
quality value this contract has always reserved for exactly this. The bound is
what limits the fabrication: two packets is sixteen sample frames, 167
microseconds at 96 kHz, while the lowest tonal of interest has a period of
milliseconds. Even that short bridge is reconstructed rather than measured,
which is why the quality tag and the downstream fraction gate remain mandatory.
It also removes a step discontinuity that otherwise smears broadband energy
across the whole spectrum — a zero-filled hole is not the neutral choice, it is
a click.

Anything longer stays `MISSING`, and a backwards jump or a restart stays
`DISCONTINUOUS`. Interpolation is a bridge over a crack, never a repair of a
hole.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from supersilence.infrastructure.acquisition.uatr_tdm import (
    CHANNEL_COUNT,
    DecodedPacket,
    FRAMES_PER_PACKET,
    SampleQuality,
)

SEQUENCE_MODULUS = 1 << 32
SEQUENCE_HALF_RANGE = 1 << 31

#: Gaps up to this many packets are bridged. Two packets is sixteen frames,
#: 167 microseconds at 96 kHz — far shorter than one cycle of the lowest tonal
#: this system looks for. It is still reconstructed signal, kept explicit by
#: `SampleQuality.INTERPOLATED` and the downstream fraction gate.
#:
#: The assembler's own default. What a running console uses comes from
#: `AcquisitionConfiguration.maximum_interpolated_packets`, which the operator
#: sets; this is what an assembler built without one falls back to.
DEFAULT_MAXIMUM_INTERPOLATED_PACKETS = 2


@dataclass(frozen=True)
class SampleBlock:
    """A contiguous sample block and one quality value per sample frame."""

    first_sequence: int
    samples: np.ndarray
    quality: tuple[SampleQuality, ...]


class OrderedSampleAssembler:
    """Turn decoded packets into ordered blocks without hiding packet faults."""

    def __init__(
        self,
        *,
        maximum_gap_packets: int = 4_096,
        maximum_interpolated_packets: int = DEFAULT_MAXIMUM_INTERPOLATED_PACKETS,
    ) -> None:
        if maximum_gap_packets <= 0:
            raise ValueError("maximum gap packets must be positive")
        if maximum_interpolated_packets < 0:
            raise ValueError("maximum interpolated packets cannot be negative")
        self._expected_sequence: int | None = None
        self._maximum_gap_packets = maximum_gap_packets
        # A caller who lowers the gap limit below the bridge limit means the
        # tighter of the two; interpolating past a gap the assembler will not
        # even accept would be meaningless.
        self._maximum_interpolated_packets = min(
            maximum_interpolated_packets, maximum_gap_packets
        )
        #: The last frame actually received, so a bridge has somewhere to start.
        #: Without one — the very first packet of a stream — there is nothing to
        #: interpolate from and the gap stays missing.
        self._last_frame: np.ndarray | None = None

    def append(self, packet: DecodedPacket) -> tuple[SampleBlock, ...]:
        """Append a packet and return received, missing, or discontinuous blocks."""
        if self._expected_sequence is None:
            self._expected_sequence = (packet.sequence + 1) % SEQUENCE_MODULUS
            self._last_frame = np.asarray(packet.samples, dtype=np.int32)[-1]
            return (self._block(packet.sequence, packet.samples, SampleQuality.RECEIVED),)

        expected = self._expected_sequence
        forward = (packet.sequence - expected) % SEQUENCE_MODULUS
        if forward == 0:
            self._expected_sequence = (packet.sequence + 1) % SEQUENCE_MODULUS
            self._last_frame = np.asarray(packet.samples, dtype=np.int32)[-1]
            return (self._block(packet.sequence, packet.samples, SampleQuality.RECEIVED),)

        if forward < SEQUENCE_HALF_RANGE and forward <= self._maximum_gap_packets:
            self._expected_sequence = (packet.sequence + 1) % SEQUENCE_MODULUS
            samples = np.asarray(packet.samples, dtype=np.int32)
            bridge, bridge_quality = self._gap(forward, samples[0])
            self._last_frame = samples[-1]
            bridge.setflags(write=False)
            return (
                SampleBlock(expected, bridge, (bridge_quality,) * bridge.shape[0]),
                self._block(packet.sequence, packet.samples, SampleQuality.RECEIVED),
            )

        # A backwards packet, restart, or unbounded gap cannot be safely
        # reconstructed. Preserve its samples and make the discontinuity explicit.
        self._expected_sequence = (packet.sequence + 1) % SEQUENCE_MODULUS
        self._last_frame = np.asarray(packet.samples, dtype=np.int32)[-1]
        return (
            self._block(packet.sequence, packet.samples, SampleQuality.DISCONTINUOUS),
        )

    def append_batch(
        self, sequences: np.ndarray, samples: np.ndarray
    ) -> SampleBlock | None:
        """Assemble a decoded array batch without per-packet sample copies."""
        sequence_values = np.asarray(sequences, dtype=np.uint32)
        sample_values = np.asarray(samples, dtype=np.int32)
        expected_shape = (
            sequence_values.shape[0],
            FRAMES_PER_PACKET,
            CHANNEL_COUNT,
        )
        if sequence_values.ndim != 1 or sample_values.shape != expected_shape:
            raise ValueError(
                f"batch samples must have shape {expected_shape}, got {sample_values.shape}"
            )
        if not sequence_values.size:
            return None

        pieces: list[np.ndarray] = []
        quality: list[SampleQuality] = []
        first_sequence: int | None = None
        for index, sequence_value in enumerate(sequence_values):
            sequence = int(sequence_value)
            packet_quality = SampleQuality.RECEIVED
            if self._expected_sequence is None:
                pass
            else:
                expected = self._expected_sequence
                forward = (sequence - expected) % SEQUENCE_MODULUS
                if forward == 0:
                    pass
                elif forward < SEQUENCE_HALF_RANGE and forward <= self._maximum_gap_packets:
                    if first_sequence is None:
                        first_sequence = expected
                    bridge, bridge_quality = self._gap(
                        forward, sample_values[index][0]
                    )
                    pieces.append(bridge)
                    quality.extend((bridge_quality,) * bridge.shape[0])
                else:
                    packet_quality = SampleQuality.DISCONTINUOUS
            if first_sequence is None:
                first_sequence = sequence
            pieces.append(sample_values[index])
            quality.extend((packet_quality,) * FRAMES_PER_PACKET)
            self._last_frame = sample_values[index][-1]
            self._expected_sequence = (sequence + 1) % SEQUENCE_MODULUS

        combined = np.concatenate(pieces, axis=0)
        combined.setflags(write=False)
        return SampleBlock(first_sequence, combined, tuple(quality))

    def _gap(
        self, packet_count: int, next_frame: np.ndarray
    ) -> tuple[np.ndarray, SampleQuality]:
        """Fill a gap: a short linear bridge, or an honest hole.

        The bridge runs from the last frame actually received to the first frame
        of the packet that ends the gap, exclusive of both, so the result joins
        two real samples rather than starting or ending on a guess.
        """
        frames = packet_count * FRAMES_PER_PACKET
        if (
            packet_count > self._maximum_interpolated_packets
            or self._last_frame is None
        ):
            return (
                np.zeros((frames, CHANNEL_COUNT), dtype=np.int32),
                SampleQuality.MISSING,
            )
        start = self._last_frame.astype(np.float64)
        end = np.asarray(next_frame, dtype=np.float64)
        steps = np.linspace(0.0, 1.0, frames + 2)[1:-1].reshape(-1, 1)
        bridge = start + (end - start) * steps
        return np.rint(bridge).astype(np.int32), SampleQuality.INTERPOLATED

    @staticmethod
    def _block(
        first_sequence: int,
        samples: np.ndarray,
        quality: SampleQuality,
    ) -> SampleBlock:
        values = np.asarray(samples, dtype=np.int32)
        if values.shape != (FRAMES_PER_PACKET, CHANNEL_COUNT):
            raise ValueError(
                "packet samples must have shape "
                f"({FRAMES_PER_PACKET}, {CHANNEL_COUNT}), got {values.shape}"
            )
        owned = values.copy()
        owned.setflags(write=False)
        return SampleBlock(first_sequence, owned, (quality,) * owned.shape[0])

    @staticmethod
    def _missing_block(sequence: int, packet_count: int) -> SampleBlock:
        samples = np.zeros(
            (packet_count * FRAMES_PER_PACKET, CHANNEL_COUNT), dtype=np.int32
        )
        samples.setflags(write=False)
        return SampleBlock(
            sequence,
            samples,
            (SampleQuality.MISSING,) * samples.shape[0],
        )
