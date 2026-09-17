"""Unprocessed sample blocks exposed by a waveform source."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from supersilence.infrastructure.acquisition.uatr_tdm import CHANNEL_COUNT


@dataclass(frozen=True)
class RawSampleBlock:
    """One immutable source-rate block before later correction or processing.

    ``discontinuous`` means the block must not be joined visually to the
    preceding block. A live transport supplies native samples; replay supplies
    the pre-gain samples preserved by its archive. The source reports a break;
    it does not fill it.
    """

    unit_identifier: int
    samples: np.ndarray
    discontinuous: bool = False

    def __post_init__(self) -> None:
        values = np.asarray(self.samples)
        if values.ndim != 2 or values.shape[1] != CHANNEL_COUNT:
            raise ValueError(f"raw samples must have shape (frames, {CHANNEL_COUNT}), got {values.shape}")
        if values.shape[0] == 0:
            raise ValueError("raw samples must contain at least one frame")
        if values.flags.writeable:
            values = values.copy()
            values.setflags(write=False)
        object.__setattr__(self, "samples", values)


RawSampleSink = Callable[[RawSampleBlock], None]


__all__ = ["RawSampleBlock", "RawSampleSink"]
