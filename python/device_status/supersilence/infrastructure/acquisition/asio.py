"""Bounded full-open ASIO input, isolated from processing work.

ASIO devices are commonly exclusive and may refuse a partial channel open. The
adapter therefore opens every advertised input once, extracts the configured
sixteen inputs in the callback, and returns immediately after one bounded copy.
Filtering, metering, recording, and window construction belong to the service
worker and never run on PortAudio's callback thread.
"""
from __future__ import annotations

import os
import threading
from collections import deque
from dataclasses import dataclass
from typing import Protocol

import numpy as np

# python-sounddevice ships two PortAudio DLLs on Windows. This must be set
# before its first import or the non-ASIO one is chosen for the whole process.
os.environ.setdefault("SD_ENABLE_ASIO", "1")

import sounddevice as _sounddevice

from supersilence.infrastructure.acquisition.configuration import (
    AcquisitionConfiguration,
)
from supersilence.infrastructure.acquisition.uatr_tdm import CHANNEL_COUNT

SUPPORTED_SAMPLE_RATES = (24_000, 48_000, 72_000, 96_000, 144_000, 192_000)
DEFAULT_MAXIMUM_QUEUED_BLOCKS = 128


class SoundDeviceBackend(Protocol):
    def query_hostapis(self): ...

    def query_devices(self): ...

    def check_input_settings(self, **kwargs): ...

    def InputStream(self, **kwargs): ...


@dataclass(frozen=True)
class AsioDevice:
    index: int
    name: str
    host_api: str
    maximum_input_channels: int
    default_sample_rate: float


@dataclass(frozen=True)
class AsioInputBlock:
    samples: np.ndarray
    discontinuous: bool = False


def list_asio_input_devices(
    backend: SoundDeviceBackend = _sounddevice,
) -> tuple[AsioDevice, ...]:
    """Return input-capable ASIO devices in the backend's stable query order."""
    host_apis = backend.query_hostapis()
    devices: list[AsioDevice] = []
    for index, device in enumerate(backend.query_devices()):
        channels = int(device.get("max_input_channels", 0))
        host_index = int(device.get("hostapi", -1))
        if not 0 <= host_index < len(host_apis):
            continue
        host_name = str(host_apis[host_index].get("name", "")).strip()
        if channels <= 0 or "ASIO" not in host_name.upper():
            continue
        devices.append(
            AsioDevice(
                index,
                str(device.get("name", "")).strip(),
                host_name,
                channels,
                float(device.get("default_samplerate", 0.0)),
            )
        )
    return tuple(devices)


def resolve_asio_device(
    device_name: str,
    host_api: str,
    backend: SoundDeviceBackend = _sounddevice,
) -> AsioDevice:
    """Resolve one exact stored identity, refusing absence and ambiguity."""
    candidates = tuple(
        device
        for device in list_asio_input_devices(backend)
        if device.name == device_name and device.host_api == host_api
    )
    if not candidates:
        raise RuntimeError(
            f'ASIO input device "{device_name}" on host API "{host_api}" is unavailable'
        )
    if len(candidates) > 1:
        raise RuntimeError(
            f'ASIO input device "{device_name}" on host API "{host_api}" is ambiguous'
        )
    return candidates[0]


def choose_asio_sample_rate(
    device: AsioDevice,
    backend: SoundDeviceBackend = _sounddevice,
) -> int:
    """Choose the lowest supported integer multiple of the 24 kHz DSP rate."""
    for sample_rate in SUPPORTED_SAMPLE_RATES:
        try:
            backend.check_input_settings(
                device=device.index,
                channels=device.maximum_input_channels,
                dtype="float32",
                samplerate=sample_rate,
            )
        except Exception:
            continue
        return sample_rate
    raise RuntimeError(
        f'ASIO input device "{device.name}" supports no safe 24 kHz multiple'
    )


def _initialize_windows_com() -> None:
    """Initialize COM on the thread that asks the ASIO driver to open."""
    if os.name != "nt":
        return
    import ctypes

    ctypes.windll.ole32.CoInitialize(None)


class AsioInputAdapter:
    """Own one exclusive ASIO stream and a bounded queue of mapped blocks."""

    def __init__(
        self,
        configuration: AcquisitionConfiguration,
        *,
        backend: SoundDeviceBackend = _sounddevice,
        maximum_queued_blocks: int = DEFAULT_MAXIMUM_QUEUED_BLOCKS,
    ) -> None:
        if maximum_queued_blocks <= 0:
            raise ValueError("maximum queued ASIO blocks must be positive")
        self._configuration = configuration
        self._backend = backend
        self._blocks: deque[AsioInputBlock] = deque(maxlen=maximum_queued_blocks)
        self._lock = threading.Lock()
        self._stream = None
        self._running = False
        self._device: AsioDevice | None = None
        self._sample_rate = 0
        self._dropped_blocks = 0
        self._callback_faults = 0
        self._last_callback_status = ""
        self._discontinuity_pending = False

    @property
    def running(self) -> bool:
        with self._lock:
            return self._running

    @property
    def device(self) -> AsioDevice | None:
        return self._device

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    @property
    def dropped_blocks(self) -> int:
        with self._lock:
            return self._dropped_blocks

    @property
    def callback_faults(self) -> int:
        with self._lock:
            return self._callback_faults

    @property
    def last_callback_status(self) -> str:
        with self._lock:
            return self._last_callback_status

    def start(self) -> None:
        if self.running:
            return
        _initialize_windows_com()
        device = resolve_asio_device(
            self._configuration.asio_device_name,
            self._configuration.asio_host_api,
            self._backend,
        )
        channel_map = self._configuration.asio_channel_map
        if max(channel_map) >= device.maximum_input_channels:
            raise RuntimeError(
                f'ASIO input device "{device.name}" has '
                f"{device.maximum_input_channels} inputs but the channel map requires "
                f"input {max(channel_map) + 1}"
            )
        sample_rate = choose_asio_sample_rate(device, self._backend)
        stream = self._backend.InputStream(
            device=device.index,
            channels=device.maximum_input_channels,
            samplerate=sample_rate,
            dtype="float32",
            blocksize=0,
            latency="low",
            callback=self._callback,
        )
        with self._lock:
            self._blocks.clear()
            self._dropped_blocks = 0
            self._callback_faults = 0
            self._last_callback_status = ""
            self._discontinuity_pending = False
            self._device = device
            self._sample_rate = sample_rate
            self._stream = stream
            self._running = True
        try:
            stream.start()
        except Exception:
            with self._lock:
                self._running = False
                self._stream = None
            try:
                stream.close()
            finally:
                raise

    def stop(self) -> None:
        with self._lock:
            self._running = False
            stream, self._stream = self._stream, None
        if stream is not None:
            try:
                stream.stop()
            finally:
                stream.close()
        with self._lock:
            self._blocks.clear()

    def drain_blocks(self) -> tuple[AsioInputBlock, ...]:
        with self._lock:
            blocks = tuple(self._blocks)
            self._blocks.clear()
        return blocks

    def _callback(self, input_data, frames, time_information, status) -> None:
        del frames, time_information
        with self._lock:
            if not self._running:
                return
        mapped = np.asarray(
            input_data[:, self._configuration.asio_channel_map], dtype=np.float32
        ).copy()
        mapped.setflags(write=False)
        with self._lock:
            if not self._running:
                return
            callback_fault = bool(status)
            if callback_fault:
                self._callback_faults += 1
                self._last_callback_status = str(status)
                self._discontinuity_pending = True
            if len(self._blocks) == self._blocks.maxlen:
                self._blocks.popleft()
                self._dropped_blocks += 1
                self._discontinuity_pending = True
            discontinuous = self._discontinuity_pending
            self._discontinuity_pending = False
            self._blocks.append(AsioInputBlock(mapped, discontinuous))
