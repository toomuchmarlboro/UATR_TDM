"""Choose the one live acquisition transport for an application run."""
from __future__ import annotations

from collections.abc import Callable

from supersilence.infrastructure.acquisition.asio_service import AsioAcquisitionService
from supersilence.infrastructure.acquisition.configuration import (
    AcquisitionConfiguration,
    AcquisitionMode,
)
from supersilence.infrastructure.acquisition.service import AcquisitionService
from supersilence.infrastructure.acquisition.service_protocol import (
    LiveAcquisitionService,
    assert_live_acquisition_surface,
)


def create_acquisition_service(
    configuration: AcquisitionConfiguration,
    *,
    initial_gains_db: dict[int, tuple[float, ...]] | None = None,
    initial_channels_enabled: dict[int, tuple[bool, ...]] | None = None,
    initial_channel_polarity: dict[int, tuple[bool, ...]] | None = None,
    ethernet_factory: Callable[..., object] = AcquisitionService,
    asio_factory: Callable[..., object] = AsioAcquisitionService,
) -> LiveAcquisitionService:
    factory = (
        asio_factory
        if configuration.mode is AcquisitionMode.ASIO
        else ethernet_factory
    )
    service = factory(
        configuration,
        initial_gains_db=initial_gains_db,
        initial_channels_enabled=initial_channels_enabled,
        initial_channel_polarity=initial_channel_polarity,
    )
    assert_live_acquisition_surface(service)
    return service  # type: ignore[return-value]
