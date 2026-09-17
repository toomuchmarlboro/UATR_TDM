"""Per-unit DSP window boundary and source-local cadence."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, replace

import numpy as np

from supersilence.infrastructure.acquisition.channel_enable import (
    DEFAULT_CHANNELS_ENABLED,
    active_channel_indices,
)
from supersilence.infrastructure.acquisition.decimation import (
    DecimatedBlock,
    StatefulDecimator,
)
from supersilence.infrastructure.acquisition.samples import SampleBlock
from supersilence.infrastructure.acquisition.uatr_tdm import (
    CHANNEL_COUNT,
    SampleQuality,
)

WINDOW_SAMPLES = 24_000
WINDOW_HOP_SAMPLES = 2_400

#: Every channel in the array, which is what a window carries unless an operator
#: has switched one out.
ALL_CHANNELS_ACTIVE = active_channel_indices(DEFAULT_CHANNELS_ENABLED)


@dataclass(frozen=True)
class ProcessingWindow:
    """An immutable one-second frame in one unit's source-local timeline."""

    unit_identifier: int
    stream_generation: int
    first_sample: int
    samples: np.ndarray
    quality: tuple[SampleQuality, ...]
    published_monotonic: float
    #: Changes when one source seeks within its own recorded timeline.
    source_revision: int = 0
    #: Changes when the application selects a different window source.
    source_selection: int = 0
    #: The channels the direction estimators should use, as zero-based indices
    #: into `samples`, in packet order.
    #:
    #: The samples themselves stay sixteen wide. A disabled channel is still
    #: metered, still recorded and still audible on the monitor speaker —
    #: those are how an operator decides whether it is really dead and whether
    #: it has come back — so the window carries the whole block and says which
    #: of it is array.
    #:
    #: Stamped when the window is emitted, from the selection in force at that
    #: moment. A window whose last block arrived after the operator switched a
    #: channel out therefore excludes that channel for its whole second,
    #: including the samples captured before the change. That is the intended
    #: reading: the operator is declaring the channel untrustworthy, not
    #: timestamping the moment it failed.
    active_channels: tuple[int, ...] = ALL_CHANNELS_ACTIVE


class ProcessingWindowBuilder:
    """Create overlapping windows without joining separate stream generations."""

    def __init__(
        self,
        unit_identifier: int,
        *,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._unit_identifier = unit_identifier
        self._clock = clock
        self._generation: int | None = None
        self._first_sample = 0
        self._samples = np.empty((0, CHANNEL_COUNT), dtype=np.float32)
        self._quality: tuple[SampleQuality, ...] = ()

    def append(
        self,
        block: DecimatedBlock,
        active_channels: tuple[int, ...] = ALL_CHANNELS_ACTIVE,
    ) -> tuple[ProcessingWindow, ...]:
        if self._generation != block.stream_generation or block.first_sample != self._first_sample + self._samples.shape[0]:
            self._generation = block.stream_generation
            self._first_sample = block.first_sample
            self._samples = np.empty((0, CHANNEL_COUNT), dtype=np.float32)
            self._quality = ()

        self._samples = np.concatenate((self._samples, block.samples), axis=0)
        self._quality += block.quality
        windows: list[ProcessingWindow] = []
        while self._samples.shape[0] >= WINDOW_SAMPLES:
            samples = self._samples[:WINDOW_SAMPLES].copy()
            samples.setflags(write=False)
            windows.append(
                ProcessingWindow(
                    self._unit_identifier,
                    block.stream_generation,
                    self._first_sample,
                    samples,
                    self._quality[:WINDOW_SAMPLES],
                    self._clock(),
                    active_channels=active_channels,
                )
            )
            self._samples = self._samples[WINDOW_HOP_SAMPLES:].copy()
            self._quality = self._quality[WINDOW_HOP_SAMPLES:]
            self._first_sample += WINDOW_HOP_SAMPLES
        return tuple(windows)


#: Offered each decimated block after polarity and before gain, with the gain in
#: force at the time and the polarity that has already been applied to it.
#:
#: The two corrections are handed over differently because they are different
#: kinds of fact. Gain is an operator's knob, recorded and not applied, so a
#: session recorded at the wrong gain is still the sea. Polarity is the wiring,
#: applied and recorded, because a sign is exactly invertible: an archive that
#: carries it can be un-flipped by anyone who later decides the call was wrong,
#: and an archive that merely mentions it in a sidecar gets read without it.
#:
#: The block, not a window: windows overlap ten to one, so anything recording
#: from them would write every sample ten times. The block is the last point at
#: which the feed is still exactly once through.
#:
#: A sink must not raise. It runs on the processing thread, and an exception
#: escaping it would stop the console's live acquisition to protect a recording.
RecordingSink = Callable[[int, DecimatedBlock, "np.ndarray | None", "np.ndarray | None"], None]
Preprocessor = Callable[[DecimatedBlock], DecimatedBlock]


class UnitProcessingPipeline:
    """Pass one unit's ordered 24 kHz blocks to bounded-consumer windows.

    Channel gain, when a source is given, is applied to each normalized block
    before it reaches the window builder — at the DSP boundary, so it is a DSP
    preprocessing step rather than a change to what the channel meters show
    (those are metered earlier, on the raw pre-decimation block; see
    `levels.py`). The source is a callable rather than a fixed array so a gain
    change the operator makes reaches the very next block with no pipeline
    rebuild.

    The channel selection, when a source is given, is read once per block and
    stamped onto any window that block completes. It does not change the shape
    of anything here: the block and the window stay sixteen channels wide, and
    what the selection carries is which of those sixteen the direction
    estimators should treat as array. Recording and monitoring are deliberately
    downstream of nothing — they see every channel either way.

    Channel polarity, when a source is given, is applied *before* that, and it
    is the one correction the archive keeps. A channel whose two conductors are
    swapped records inverted, which no gain setting and no bearing can explain,
    and a consumer that reads the WAV without consulting the sidecar gets a
    silently wrong array. Multiplying by minus one loses nothing — it is its own
    inverse — so the safe default is the opposite of gain's: apply it, and write
    down which channels it was applied to.

    A recording sink, when given, is offered the polarity-corrected block
    *before* gain is applied, along with the multipliers that are about to be
    applied to it and the signs that already have been. An archive of pre-gain
    samples plus the gain in force reproduces exactly what the DSP saw, and
    stays useful if the operator had the gain wrong; an archive of post-gain
    samples cannot be undone.
    """

    def __init__(
        self,
        unit_identifier: int,
        *,
        clock: Callable[[], float] = time.monotonic,
        gain_source: Callable[[], np.ndarray] | None = None,
        polarity_source: Callable[[], np.ndarray] | None = None,
        active_channels_source: Callable[[], tuple[int, ...]] | None = None,
        recording_sink: RecordingSink | None = None,
        preprocessor: Preprocessor | None = None,
        pre_dsp_sink: RecordingSink | None = None,
    ) -> None:
        self._unit_identifier = unit_identifier
        self._decimator = StatefulDecimator()
        self._windows = ProcessingWindowBuilder(unit_identifier, clock=clock)
        self._gain_source = gain_source
        self._polarity_source = polarity_source
        self._active_channels_source = active_channels_source
        self._recording_sink = recording_sink
        self._preprocessor = preprocessor
        self._pre_dsp_sink = pre_dsp_sink

    def process(self, block: SampleBlock, *, force_discontinuity: bool = False) -> tuple[ProcessingWindow, ...]:
        result: list[ProcessingWindow] = []
        for decimated in self._decimator.process(
            block.samples,
            block.quality,
            force_discontinuity=force_discontinuity,
        ):
            result.extend(self.process_decimated(decimated))
        return tuple(result)

    def process_decimated(self, block: DecimatedBlock) -> tuple[ProcessingWindow, ...]:
        """Accept a normalized 24 kHz block from a non-UATR live source."""
        signs = None if self._polarity_source is None else self._polarity_source()
        corrected = self._scale(block, signs)
        multipliers = None if self._gain_source is None else self._gain_source()
        if self._recording_sink is not None:
            self._recording_sink(self._unit_identifier, corrected, multipliers, signs)
        prepared = self._scale(corrected, multipliers)
        if self._preprocessor is not None:
            prepared = self._preprocessor(prepared)
        if self._pre_dsp_sink is not None:
            self._pre_dsp_sink(self._unit_identifier, prepared, None, signs)
        active_channels = ALL_CHANNELS_ACTIVE if self._active_channels_source is None else self._active_channels_source()
        return self._windows.append(prepared, active_channels)

    def replace_preprocessor(self, preprocessor: Preprocessor | None) -> None:
        """Adopt a new pre-DSP processor at a block boundary."""
        self._preprocessor = preprocessor

    def replace_pre_dsp_sink(self, sink: RecordingSink | None) -> None:
        self._pre_dsp_sink = sink

    def _scale(self, decimated: DecimatedBlock, multipliers: np.ndarray | None) -> DecimatedBlock:
        if multipliers is None:
            return decimated
        samples = (decimated.samples * multipliers).astype(np.float32, copy=False)
        samples.setflags(write=False)
        return replace(decimated, samples=samples)
