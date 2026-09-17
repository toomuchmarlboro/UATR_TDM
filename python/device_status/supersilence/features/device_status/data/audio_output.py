"""Bounded live-audio output through the operating system's default device.

Acquisition calls :meth:`DefaultAudioOutput.write` from its processing thread.
That method only converts a block and copies bytes into a bounded ring; Qt's
audio engine pulls those bytes independently. No device write, wait, or Qt
state transition occurs on the acquisition thread.

The output device is intentionally not an application setting. It is resolved
from ``QMediaDevices.defaultAudioOutput()`` whenever hearing starts, and an
operating-system output change restarts the sink on the new default.
"""
from __future__ import annotations

import threading
from collections.abc import Callable

import numpy as np
from PySide6.QtCore import QIODevice, QObject, Signal
from PySide6.QtMultimedia import QAudio, QAudioFormat, QAudioSink, QMediaDevices

from supersilence.infrastructure.acquisition.decimation import (
    PROCESSING_SAMPLE_RATE,
)

DEFAULT_MAXIMUM_BUFFER_SECONDS = 0.5


def _qt_enum_value(value) -> int:
    """Compare Qt enum wrappers by value across PySide binding scopes."""
    return int(getattr(value, "value", value))


class StreamingLinearResampler:
    """Continuous mono rate conversion with state across source blocks.

    The DSP stream is already band-limited below 10 kHz. Output devices are
    accepted only at 24 kHz or above, so interpolation cannot alias content
    into the audible band. Retaining the last input sample prevents a boundary
    click when acquisition supplies differently sized blocks.
    """

    def __init__(self, source_rate: int, target_rate: int) -> None:
        if source_rate <= 0 or target_rate < source_rate:
            raise ValueError("target sample rate must be at least the source rate")
        self._step = float(source_rate) / float(target_rate)
        self._input_position = 0
        self._next_output_position = 0.0
        self._previous: float | None = None

    def reset(self) -> None:
        self._input_position = 0
        self._next_output_position = 0.0
        self._previous = None

    def process(self, samples: np.ndarray) -> np.ndarray:
        values = np.asarray(samples, dtype=np.float32)
        if values.ndim != 1:
            raise ValueError("audio samples must be mono")
        if not values.size:
            return np.empty(0, dtype=np.float32)

        start = self._input_position
        stop = start + values.size - 1
        if self._previous is None:
            positions = np.arange(start, stop + 1, dtype=np.float64)
            interpolation_values = values
        else:
            positions = np.arange(start - 1, stop + 1, dtype=np.float64)
            interpolation_values = np.concatenate(
                (np.array([self._previous], dtype=np.float32), values)
            )

        available = stop - self._next_output_position
        count = 0 if available < -1e-12 else int(np.floor(available / self._step)) + 1
        output_positions = self._next_output_position + self._step * np.arange(count)
        result = np.interp(
            output_positions,
            positions,
            interpolation_values,
        ).astype(np.float32)
        self._next_output_position += count * self._step
        self._input_position += values.size
        self._previous = float(values[-1])
        result.setflags(write=False)
        return result


class PcmAudioBuffer(QIODevice):
    """Thread-safe bounded PCM bytes; overflow drops the oldest sound."""

    def __init__(
        self,
        maximum_bytes: int,
        bytes_per_frame: int,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        if maximum_bytes <= 0 or bytes_per_frame <= 0:
            raise ValueError("audio buffer and frame sizes must be positive")
        maximum_bytes -= maximum_bytes % bytes_per_frame
        if maximum_bytes == 0:
            raise ValueError("audio buffer must hold at least one complete frame")
        self._maximum_bytes = maximum_bytes
        self._bytes_per_frame = bytes_per_frame
        self._data = bytearray()
        self._lock = threading.Lock()
        self._accepting = True
        self._dropped_bytes = 0
        self.open(QIODevice.OpenModeFlag.ReadOnly | QIODevice.OpenModeFlag.Unbuffered)

    @property
    def dropped_bytes(self) -> int:
        with self._lock:
            return self._dropped_bytes

    def append(self, payload: bytes) -> None:
        """Copy complete PCM frames without ever waiting for the reader."""
        if len(payload) % self._bytes_per_frame:
            raise ValueError("PCM payload must contain complete frames")
        with self._lock:
            if not self._accepting:
                return
            incoming = payload
            if len(incoming) >= self._maximum_bytes:
                self._dropped_bytes += len(self._data) + len(incoming) - self._maximum_bytes
                self._data[:] = incoming[-self._maximum_bytes :]
                return
            overflow = max(0, len(self._data) + len(incoming) - self._maximum_bytes)
            if overflow:
                # Both existing data and incoming blocks are frame aligned.
                del self._data[:overflow]
                self._dropped_bytes += overflow
            self._data.extend(incoming)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()

    def deactivate(self) -> None:
        with self._lock:
            self._accepting = False
            self._data.clear()

    def readData(self, maximum_length: int) -> bytes:  # noqa: N802 - Qt API
        length = maximum_length - maximum_length % self._bytes_per_frame
        if length <= 0:
            return b""
        with self._lock:
            count = min(length, len(self._data))
            count -= count % self._bytes_per_frame
            result = bytes(self._data[:count])
            del self._data[:count]
        # Continuous silence keeps the pull-mode sink alive during startup or a
        # short network gap; it never fabricates a signal for the operator.
        return result + bytes(length - count)

    def writeData(self, data: bytes) -> int:  # noqa: N802 - required by QIODevice
        del data
        return -1

    def bytesAvailable(self) -> int:  # noqa: N802 - Qt API
        with self._lock:
            available = len(self._data)
        return available + super().bytesAvailable()

    def isSequential(self) -> bool:  # noqa: N802 - Qt API
        return True


class DefaultAudioOutput(QObject):
    """One mono stream following the operating system's current default output."""

    failed = Signal(str)

    def __init__(
        self,
        parent: QObject | None = None,
        *,
        source_sample_rate: int = PROCESSING_SAMPLE_RATE,
        maximum_buffer_seconds: float = DEFAULT_MAXIMUM_BUFFER_SECONDS,
        media_devices=None,
        sink_factory: Callable[..., QAudioSink] = QAudioSink,
    ) -> None:
        super().__init__(parent)
        if source_sample_rate <= 0:
            raise ValueError("source sample rate must be positive")
        if maximum_buffer_seconds <= 0.0:
            raise ValueError("maximum buffer seconds must be positive")
        self._source_sample_rate = int(source_sample_rate)
        self._maximum_buffer_seconds = float(maximum_buffer_seconds)
        self._media_devices = media_devices or QMediaDevices(self)
        self._sink_factory = sink_factory
        self._sink = None
        self._buffer: PcmAudioBuffer | None = None
        self._resampler: StreamingLinearResampler | None = None
        self._format: QAudioFormat | None = None
        self._device_identifier: bytes | None = None
        self._write_lock = threading.Lock()
        self._stopping = False
        outputs_changed = getattr(self._media_devices, "audioOutputsChanged", None)
        if outputs_changed is not None:
            outputs_changed.connect(self._follow_system_default)

    @property
    def running(self) -> bool:
        return self._sink is not None

    @property
    def dropped_bytes(self) -> int:
        buffer = self._buffer
        return 0 if buffer is None else buffer.dropped_bytes

    def start(self) -> None:
        """Open the current system default, replacing any previous sink."""
        self.stop()
        device = self._media_devices.defaultAudioOutput()
        if device.isNull():
            raise RuntimeError("No system audio output is available")
        audio_format = self._choose_format(device)
        target_rate = audio_format.sampleRate()
        bytes_per_frame = audio_format.bytesPerFrame()
        maximum_bytes = max(
            bytes_per_frame,
            int(target_rate * bytes_per_frame * self._maximum_buffer_seconds),
        )
        buffer = PcmAudioBuffer(maximum_bytes, bytes_per_frame, self)
        sink = self._sink_factory(device, audio_format, self)
        state_changed = getattr(sink, "stateChanged", None)
        if state_changed is not None:
            state_changed.connect(self._on_state_changed)

        with self._write_lock:
            self._format = audio_format
            self._resampler = StreamingLinearResampler(
                self._source_sample_rate, target_rate
            )
            self._buffer = buffer
            self._sink = sink
            self._device_identifier = bytes(device.id())
        sink.start(buffer)
        sink_error = sink.error()
        acceptable_errors = {
            _qt_enum_value(QAudio.Error.NoError),
            _qt_enum_value(QAudio.Error.UnderrunError),
        }
        if _qt_enum_value(sink_error) not in acceptable_errors:
            message = self._error_message(sink_error)
            self.stop()
            raise RuntimeError(message)

    def stop(self) -> None:
        """Stop synchronously; no later acquisition callback can refill audio."""
        self._stopping = True
        with self._write_lock:
            sink, self._sink = self._sink, None
            buffer, self._buffer = self._buffer, None
            self._resampler = None
            self._format = None
            self._device_identifier = None
            if buffer is not None:
                buffer.deactivate()
        if sink is not None:
            sink.stop()
            sink.deleteLater()
        if buffer is not None:
            buffer.close()
            buffer.deleteLater()
        self._stopping = False

    def reset(self) -> None:
        """Discard the old timeline after a channel switch or discontinuity."""
        with self._write_lock:
            if self._resampler is not None:
                self._resampler.reset()
            if self._buffer is not None:
                self._buffer.clear()

    def write(self, mono_samples: np.ndarray) -> None:
        """Convert and enqueue one block; safe on the acquisition thread."""
        with self._write_lock:
            resampler = self._resampler
            audio_format = self._format
            buffer = self._buffer
            if resampler is None or audio_format is None or buffer is None:
                return
            converted = resampler.process(mono_samples)
            if not converted.size:
                return
            pcm = np.rint(np.clip(converted, -1.0, 1.0) * 32767.0).astype(
                np.int16
            )
            if audio_format.channelCount() > 1:
                pcm = np.repeat(
                    pcm.reshape(-1, 1), audio_format.channelCount(), axis=1
                )
            buffer.append(pcm.tobytes())

    def _choose_format(self, device) -> QAudioFormat:
        preferred = device.preferredFormat()
        rates = tuple(
            dict.fromkeys(
                (
                    self._source_sample_rate,
                    preferred.sampleRate(),
                    48_000,
                )
            )
        )
        channels = (1, 2) if preferred.channelCount() > 1 else (1,)
        for rate in rates:
            if rate < self._source_sample_rate:
                continue
            for channel_count in channels:
                candidate = QAudioFormat()
                candidate.setSampleRate(rate)
                candidate.setChannelCount(channel_count)
                candidate.setSampleFormat(QAudioFormat.SampleFormat.Int16)
                if device.isFormatSupported(candidate):
                    return candidate
        raise RuntimeError(
            f"System audio output {device.description()!r} supports no "
            "24 kHz-or-higher mono/stereo signed 16-bit format"
        )

    def _follow_system_default(self) -> None:
        if not self.running:
            return
        device = self._media_devices.defaultAudioOutput()
        identifier = None if device.isNull() else bytes(device.id())
        if identifier == self._device_identifier:
            return
        try:
            self.start()
        except RuntimeError as error:
            self.failed.emit(str(error))

    def _on_state_changed(self, state) -> None:
        sink = self._sink
        if (
            self._stopping
            or sink is None
            or _qt_enum_value(state) != _qt_enum_value(QAudio.State.StoppedState)
        ):
            return
        error = sink.error()
        if _qt_enum_value(error) == _qt_enum_value(QAudio.Error.NoError):
            return
        message = self._error_message(error)
        self.stop()
        self.failed.emit(message)

    @staticmethod
    def _error_message(error) -> str:
        descriptions = {
            _qt_enum_value(QAudio.Error.OpenError): (
                "The system audio output could not be opened"
            ),
            _qt_enum_value(QAudio.Error.IOError): (
                "The system audio output stopped responding"
            ),
            _qt_enum_value(QAudio.Error.UnderrunError): (
                "The system audio output ran out of data"
            ),
            _qt_enum_value(QAudio.Error.FatalError): "The system audio output failed",
        }
        return descriptions.get(
            _qt_enum_value(error), "The system audio output failed"
        )
