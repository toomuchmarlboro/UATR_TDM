"""Persist which of each unit's sixteen channels arrive inverted."""
from __future__ import annotations

from collections.abc import Iterable

from supersilence.infrastructure.acquisition.channel_polarity import (
    DEFAULT_CHANNEL_POLARITY,
    validate_channel_polarity,
)
from supersilence.infrastructure.settings.repository import (
    SCOPE_UNIT,
    SettingsRepository,
)

CHANNEL_POLARITY_KEY = "acquisition_channel_polarity"


def load_channel_polarity(
    settings: SettingsRepository, unit_identifier: int
) -> tuple[bool, ...]:
    """One unit's stored polarity, materializing all-as-delivered if unset."""
    stored = settings.get(
        SCOPE_UNIT, CHANNEL_POLARITY_KEY, default=None, unit_id=unit_identifier
    )
    if stored is None:
        save_channel_polarity(settings, unit_identifier, DEFAULT_CHANNEL_POLARITY)
        return DEFAULT_CHANNEL_POLARITY
    if isinstance(stored, (str, bytes)):
        raise ValueError("stored channel polarity must be a list of booleans")
    try:
        return validate_channel_polarity(stored)
    except TypeError as error:
        raise ValueError("stored channel polarity must be an iterable list") from error


def save_channel_polarity(
    settings: SettingsRepository, unit_identifier: int, polarity: Iterable[bool]
) -> None:
    checked = validate_channel_polarity(polarity)
    settings.set(
        SCOPE_UNIT,
        CHANNEL_POLARITY_KEY,
        list(checked),
        unit_id=unit_identifier,
    )
