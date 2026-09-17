"""Persist which of each unit's sixteen channels are in the array."""
from __future__ import annotations

from collections.abc import Iterable

from supersilence.infrastructure.acquisition.channel_enable import (
    DEFAULT_CHANNELS_ENABLED,
    validate_channels_enabled,
)
from supersilence.infrastructure.settings.repository import (
    SCOPE_UNIT,
    SettingsRepository,
)

CHANNELS_ENABLED_KEY = "acquisition_channel_enabled"


def load_channels_enabled(
    settings: SettingsRepository, unit_identifier: int
) -> tuple[bool, ...]:
    """One unit's stored channel selection, materializing all-enabled if unset."""
    stored = settings.get(
        SCOPE_UNIT, CHANNELS_ENABLED_KEY, default=None, unit_id=unit_identifier
    )
    if stored is None:
        save_channels_enabled(settings, unit_identifier, DEFAULT_CHANNELS_ENABLED)
        return DEFAULT_CHANNELS_ENABLED
    if isinstance(stored, (str, bytes)):
        raise ValueError("stored channel selection must be a list of booleans")
    try:
        return validate_channels_enabled(stored)
    except TypeError as error:
        raise ValueError("stored channel selection must be an iterable list") from error


def save_channels_enabled(
    settings: SettingsRepository, unit_identifier: int, enabled: Iterable[bool]
) -> None:
    checked = validate_channels_enabled(enabled)
    settings.set(
        SCOPE_UNIT,
        CHANNELS_ENABLED_KEY,
        list(checked),
        unit_id=unit_identifier,
    )
