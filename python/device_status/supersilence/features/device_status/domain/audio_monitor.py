"""Pure mono signal conditioning for live channel monitoring.

The acquisition path already owns decoding, gap quality, and the 96 kHz to
24 kHz anti-alias filter.  Hearing starts from that 24 kHz block: this module
only chooses one channel, applies the same digital gain the blue Device Status
bar represents, and bounds the result before it reaches a speaker backend.

That multiplier is gain alone. Polarity is applied upstream, to the block
itself, before either the recorder or this monitor sees it (see
`infrastructure/acquisition/processing.py`), so an inverted channel arrives
here already corrected and the multiplier is positive. Either way the sound is
the same: a sign flip does not change what a single channel sounds like. A
negative multiplier is still accepted rather than refused, because a session
replayed from a version 1 sidecar carries its polarity that way.

There is deliberately no automatic gain control.  Normalising every block
would turn quiet electronics noise into full-volume sound and make loudness
changes meaningless.  The operator's channel gain remains the explicit way to
raise or lower what is heard.
"""

from __future__ import annotations

import numpy as np

DEFAULT_OUTPUT_HEADROOM = 0.7
DEFAULT_START_RAMP_FRAMES = 240  # 10 ms at the processing rate of 24 kHz.


class MonoMonitorConditioner:
    """Select and safely bound one channel without changing its dynamics."""

    def __init__(
        self,
        channel_count: int,
        *,
        output_headroom: float = DEFAULT_OUTPUT_HEADROOM,
        start_ramp_frames: int = DEFAULT_START_RAMP_FRAMES,
    ) -> None:
        if channel_count <= 0:
            raise ValueError("channel count must be positive")
        if not 0.0 < output_headroom <= 1.0:
            raise ValueError("output headroom must be above zero and at most one")
        if start_ramp_frames < 0:
            raise ValueError("start ramp frames cannot be negative")
        self._channel_count = int(channel_count)
        self._output_headroom = float(output_headroom)
        self._start_ramp_frames = int(start_ramp_frames)
        self._ramp_position = 0

    def reset(self) -> None:
        """Start the click-suppressing fade again after a switch or discontinuity."""
        self._ramp_position = 0

    def condition(
        self,
        samples: np.ndarray,
        channel_index: int,
        gain_multiplier: float,
        *,
        playable: np.ndarray | None = None,
    ) -> np.ndarray:
        """Return immutable float32 mono samples within the configured headroom.

        ``playable`` names samples whose acquisition quality may be heard.
        Missing or discontinuous frames arrive as ``False`` and become silence;
        received and explicitly interpolated frames remain audible.

        ``gain_multiplier`` may be negative: that is a channel marked INV, and
        the sign is applied rather than refused.
        """
        values = np.asarray(samples)
        if values.ndim != 2 or values.shape[1] != self._channel_count:
            raise ValueError(f"samples must have shape (frames, {self._channel_count}), got {values.shape}")
        if not 0 <= channel_index < self._channel_count:
            raise ValueError(f"channel index {channel_index} is out of range")
        if not np.isfinite(gain_multiplier):
            raise ValueError("gain multiplier must be finite")

        if playable is None:
            playable_values = np.ones(values.shape[0], dtype=bool)
        else:
            playable_values = np.asarray(playable, dtype=bool)
            if playable_values.shape != (values.shape[0],):
                raise ValueError("playable must contain one value per sample frame")

        mono = np.asarray(values[:, channel_index], dtype=np.float32).copy()
        mono *= float(gain_multiplier)
        mono[~playable_values] = 0.0
        # A malformed upstream float must never become an unbounded PCM value.
        np.nan_to_num(
            mono,
            copy=False,
            nan=0.0,
            posinf=self._output_headroom,
            neginf=-self._output_headroom,
        )
        np.clip(
            mono,
            -self._output_headroom,
            self._output_headroom,
            out=mono,
        )
        self._apply_start_ramp(mono)
        mono.setflags(write=False)
        return mono

    def _apply_start_ramp(self, mono: np.ndarray) -> None:
        if not mono.size or self._start_ramp_frames == 0:
            self._ramp_position = self._start_ramp_frames
            return
        remaining = self._start_ramp_frames - self._ramp_position
        if remaining <= 0:
            return
        count = min(mono.size, remaining)
        positions = np.arange(
            self._ramp_position + 1,
            self._ramp_position + count + 1,
            dtype=np.float32,
        )
        mono[:count] *= positions / self._start_ramp_frames
        self._ramp_position += count
