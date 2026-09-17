"""Normalize already-24 kHz UATR-TDM audio for the DSP consumer boundary."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from supersilence.infrastructure.acquisition.uatr_tdm import (
    CHANNEL_COUNT,
    MAXIMUM_SAMPLE,
    SAMPLE_RATE,
    SampleQuality,
)

PROCESSING_SAMPLE_RATE = 24_000
DECIMATION_FACTOR = SAMPLE_RATE // PROCESSING_SAMPLE_RATE
FILTER_TAP_COUNT = 1
FILTER_GROUP_DELAY_INPUT_SAMPLES = 0
FILTER_GROUP_DELAY_OUTPUT_SAMPLES = 0
PASSBAND_EDGE_HZ = 10_000
STOPBAND_EDGE_HZ = 12_000
NORMALIZATION_SCALE = float(MAXIMUM_SAMPLE + 1)

_QUALITY_TO_CODE = {
    SampleQuality.RECEIVED: 0,
    SampleQuality.INTERPOLATED: 1,
    SampleQuality.MISSING: 2,
    SampleQuality.DISCONTINUOUS: 3,
}
_CODE_TO_QUALITY = tuple(quality for quality, _ in sorted(_QUALITY_TO_CODE.items(), key=lambda item: item[1]))


# Kept as a one-tap identity for consumers that name the processing boundary
# after its former decimator. The FPGA has already performed the rate reduction,
# so a host FIR would add delay and change the delivered 24 kHz signal.
FILTER_COEFFICIENTS = np.ones(1, dtype=np.float32)
FILTER_COEFFICIENTS.setflags(write=False)


@dataclass(frozen=True)
class DecimatedBlock:
    """One contiguous, source-local block at 24 kHz."""

    stream_generation: int
    first_sample: int
    samples: np.ndarray
    quality: tuple[SampleQuality, ...]


class StatefulDecimator:
    """Preserve a source-local 24 kHz stream at the existing DSP boundary."""

    def __init__(self) -> None:
        self._stream_generation = 0
        self._next_output_sample = 0
        self._has_input = False

    def process(
        self,
        samples: np.ndarray,
        quality: tuple[SampleQuality, ...],
        *,
        force_discontinuity: bool = False,
    ) -> tuple[DecimatedBlock, ...]:
        """Normalize arbitrary source batches without resampling or filtering."""
        values = np.asarray(samples)
        if values.ndim != 2 or values.shape[1] != CHANNEL_COUNT:
            raise ValueError(f"samples must have shape (frames, {CHANNEL_COUNT}), got {values.shape}")
        if len(quality) != values.shape[0]:
            raise ValueError("quality must contain one value per sample frame")
        if not values.shape[0]:
            return ()

        codes = np.fromiter(
            (_QUALITY_TO_CODE[item] for item in quality),
            dtype=np.uint8,
            count=len(quality),
        )
        reset_points = list(
            np.flatnonzero(
                (codes == _QUALITY_TO_CODE[SampleQuality.DISCONTINUOUS])
                & np.concatenate(
                    (
                        np.array([True]),
                        codes[:-1] != _QUALITY_TO_CODE[SampleQuality.DISCONTINUOUS],
                    )
                )
            )
        )
        if force_discontinuity and 0 not in reset_points:
            reset_points.insert(0, 0)

        boundaries = sorted(set(reset_points + [values.shape[0]]))
        result: list[DecimatedBlock] = []
        start = 0
        for stop in boundaries:
            if stop > start:
                block = self._process_contiguous(values[start:stop], codes[start:stop])
                if block is not None:
                    result.append(block)
            if stop < values.shape[0]:
                self._reset_for_discontinuity()
            start = stop
        return tuple(result)

    def _process_contiguous(self, samples: np.ndarray, quality_codes: np.ndarray) -> DecimatedBlock | None:
        output_samples = np.asarray(samples, dtype=np.float32) / NORMALIZATION_SCALE
        output_samples = output_samples.copy()
        self._has_input = True
        first_sample = self._next_output_sample
        self._next_output_sample += output_samples.shape[0]
        output_samples.setflags(write=False)
        output_quality = tuple(_CODE_TO_QUALITY[int(code)] for code in quality_codes)
        return DecimatedBlock(
            self._stream_generation,
            first_sample,
            output_samples,
            output_quality,
        )

    def _reset_for_discontinuity(self) -> None:
        if self._has_input:
            self._stream_generation += 1
        self._next_output_sample = 0
        self._has_input = False
