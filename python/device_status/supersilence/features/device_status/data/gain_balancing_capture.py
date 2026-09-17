"""Bounded, retained pre-gain captures for the Gain Balancing diagnosis."""

from __future__ import annotations

import json
import threading
import wave
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class CompletedGainCapture:
    """One selected element's retained WAV and the exact samples analysed."""

    channel_index: int
    wav_path: Path
    samples: np.ndarray


class GainBalancingCapture:
    """Accept exactly one channel's pre-gain blocks without owning acquisition.

    The service calls :meth:`accept` on its processing thread.  Writing is
    intentionally small and bounded to the requested duration; reaching the
    limit closes a valid WAV before the UI is told that analysis can begin.
    """

    def __init__(self, root: Path, *, sample_rate: int) -> None:
        self._root = Path(root)
        self._sample_rate = int(sample_rate)
        self._lock = threading.Lock()
        self._unit_identifier: int | None = None
        self._channel_index: int | None = None
        self._frames_remaining = 0
        self._handle: wave.Wave_write | None = None
        self._path: Path | None = None
        self._parts: list[np.ndarray] = []
        self._completed: CompletedGainCapture | None = None

    @property
    def active(self) -> bool:
        with self._lock:
            return self._handle is not None

    def start(self, unit_identifier: int, channel_index: int, duration_seconds: float) -> Path:
        if duration_seconds <= 0.0:
            raise ValueError("capture duration must be positive")
        with self._lock:
            if self._handle is not None:
                raise RuntimeError("a gain-balancing capture is already active")
            folder = self._root / datetime.now().strftime("%Y-%m-%d_%H%M%S")
            folder.mkdir(parents=True, exist_ok=True)
            path = folder / f"element_{channel_index + 1:02d}.wav"
            handle = wave.open(str(path), "wb")
            handle.setnchannels(1)
            handle.setsampwidth(3)
            handle.setframerate(self._sample_rate)
            self._unit_identifier = int(unit_identifier)
            self._channel_index = int(channel_index)
            self._frames_remaining = int(round(duration_seconds * self._sample_rate))
            self._handle = handle
            self._path = path
            self._parts = []
            self._completed = None
            return path

    def accept(self, unit_identifier: int, block, _multipliers, _signs=None) -> None:
        with self._lock:
            if self._handle is None or unit_identifier != self._unit_identifier:
                return
            count = min(self._frames_remaining, block.samples.shape[0])
            if count <= 0:
                return
            selected = np.asarray(block.samples[:count, self._channel_index], dtype=np.float32).copy()
            self._handle.writeframesraw(_pcm24(selected))
            self._parts.append(selected)
            self._frames_remaining -= count
            if self._frames_remaining == 0:
                self._finish_locked()

    def take_completed(self) -> CompletedGainCapture | None:
        with self._lock:
            completed = self._completed
            self._completed = None
            return completed

    def cancel(self) -> None:
        with self._lock:
            if self._handle is not None:
                self._handle.close()
            self._reset_locked()

    def _finish_locked(self) -> None:
        assert self._handle is not None and self._path is not None and self._channel_index is not None
        self._handle.close()
        samples = np.concatenate(self._parts) if self._parts else np.empty(0, dtype=np.float32)
        metadata_path = self._path.with_suffix(".json")
        metadata_path.write_text(
            json.dumps(
                {
                    "channel_number": self._channel_index + 1,
                    "sample_rate_hz": self._sample_rate,
                    "frames": int(samples.size),
                    "wav": self._path.name,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        self._completed = CompletedGainCapture(self._channel_index, self._path, samples)
        self._handle = None
        self._unit_identifier = None
        self._channel_index = None
        self._frames_remaining = 0
        self._parts = []

    def _reset_locked(self) -> None:
        self._handle = None
        self._unit_identifier = None
        self._channel_index = None
        self._frames_remaining = 0
        self._path = None
        self._parts = []


def _pcm24(samples: np.ndarray) -> bytes:
    values = np.rint(np.clip(samples, -1.0, 1.0 - 1.0 / (1 << 23)) * (1 << 23)).astype("<i4")
    return values.view(np.uint8).reshape(-1, 4)[:, :3].tobytes()
