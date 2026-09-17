"""Continuous conversion from normalized ASIO samples to 24 kHz blocks."""
from __future__ import annotations

import numpy as np
from scipy.signal import firwin, kaiserord, lfilter

from supersilence.infrastructure.acquisition.decimation import (
    DecimatedBlock,
    PASSBAND_EDGE_HZ,
    PROCESSING_SAMPLE_RATE,
    STOPBAND_EDGE_HZ,
)
from supersilence.infrastructure.acquisition.uatr_tdm import (
    CHANNEL_COUNT,
    SampleQuality,
)

STOPBAND_ATTENUATION_DB = 80.0


def design_asio_filter(input_sample_rate: int) -> np.ndarray:
    """Design a linear-phase filter for one exact integer-rate conversion."""
    if input_sample_rate == PROCESSING_SAMPLE_RATE:
        coefficients = np.ones(1, dtype=np.float32)
        coefficients.setflags(write=False)
        return coefficients
    transition_width = STOPBAND_EDGE_HZ - PASSBAND_EDGE_HZ
    tap_count, beta = kaiserord(
        STOPBAND_ATTENUATION_DB,
        transition_width / (input_sample_rate / 2.0),
    )
    # Odd length gives an integer input-sample group delay.
    if tap_count % 2 == 0:
        tap_count += 1
    coefficients = firwin(
        tap_count,
        (PASSBAND_EDGE_HZ + STOPBAND_EDGE_HZ) / 2.0,
        window=("kaiser", beta),
        fs=input_sample_rate,
    ).astype(np.float32)
    coefficients.setflags(write=False)
    return coefficients


class AsioRateConverter:
    """Stateful integer decimation with explicit discontinuity generations."""

    def __init__(self, input_sample_rate: int) -> None:
        if (
            isinstance(input_sample_rate, bool)
            or input_sample_rate < PROCESSING_SAMPLE_RATE
            or input_sample_rate % PROCESSING_SAMPLE_RATE
        ):
            raise ValueError(
                "ASIO input sample rate must be an integer multiple of 24 kHz"
            )
        self.input_sample_rate = input_sample_rate
        self.factor = input_sample_rate // PROCESSING_SAMPLE_RATE
        self.coefficients = design_asio_filter(input_sample_rate)
        history = self.coefficients.size - 1
        self._filter_state = np.zeros((history, CHANNEL_COUNT), dtype=np.float32)
        self._quality_history = np.full(
            history, 3, dtype=np.uint8
        )
        self._phase = 0
        self._stream_generation = 0
        self._next_output_sample = 0
        self._has_input = False

    def process(
        self, samples: np.ndarray, *, force_discontinuity: bool = False
    ) -> tuple[DecimatedBlock, ...]:
        values = np.asarray(samples, dtype=np.float32)
        if values.ndim != 2 or values.shape[1] != CHANNEL_COUNT:
            raise ValueError(
                f"ASIO samples must have shape (frames, {CHANNEL_COUNT})"
            )
        if not values.shape[0]:
            return ()
        if force_discontinuity:
            self._reset_for_discontinuity()

        filtered, self._filter_state = lfilter(
            self.coefficients,
            np.array([1.0], dtype=np.float32),
            values,
            axis=0,
            zi=self._filter_state,
        )
        received = np.zeros(values.shape[0], dtype=np.uint8)
        if self.coefficients.size == 1:
            supported_quality = received
        else:
            combined = np.concatenate((self._quality_history, received))
            supported_quality = np.lib.stride_tricks.sliding_window_view(
                combined, self.coefficients.size
            ).max(axis=1)
            self._quality_history = combined[-(self.coefficients.size - 1) :].copy()

        offset = self._phase
        output = filtered[offset:: self.factor].copy()
        quality_codes = supported_quality[offset:: self.factor]
        self._phase = (offset - values.shape[0]) % self.factor
        self._has_input = True
        if not output.shape[0]:
            return ()

        first_sample = self._next_output_sample
        self._next_output_sample += output.shape[0]
        output.setflags(write=False)
        qualities = (
            SampleQuality.RECEIVED,
            SampleQuality.INTERPOLATED,
            SampleQuality.MISSING,
            SampleQuality.DISCONTINUOUS,
        )
        return (
            DecimatedBlock(
                self._stream_generation,
                first_sample,
                output,
                tuple(qualities[int(code)] for code in quality_codes),
            ),
        )

    def _reset_for_discontinuity(self) -> None:
        if self._has_input:
            self._stream_generation += 1
        self._next_output_sample = 0
        self._filter_state.fill(0)
        self._quality_history.fill(3)
        self._phase = 0
        self._has_input = False
