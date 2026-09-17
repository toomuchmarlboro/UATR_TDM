"""Persist each unit's sixteen channel gains."""
from __future__ import annotations

from collections.abc import Iterable

from supersilence.infrastructure.acquisition.gain import (
    DEFAULT_GAINS_DB,
    validate_channel_gains_db,
)
from supersilence.infrastructure.settings.repository import (
    SCOPE_UNIT,
    SettingsRepository,
)

CHANNEL_GAIN_DB_KEY = "acquisition_channel_gain_db"


def load_channel_gains_db(
    settings: SettingsRepository, unit_identifier: int
) -> tuple[float, ...]:
    """One unit's stored channel gains, materializing 0 dB defaults if unset."""
    stored = settings.get(
        SCOPE_UNIT, CHANNEL_GAIN_DB_KEY, default=None, unit_id=unit_identifier
    )
    if stored is None:
        save_channel_gains_db(settings, unit_identifier, DEFAULT_GAINS_DB)
        return DEFAULT_GAINS_DB
    if isinstance(stored, (str, bytes)):
        raise ValueError("stored channel gains must be a list of numbers")
    try:
        return validate_channel_gains_db(stored)
    except TypeError as error:
        raise ValueError("stored channel gains must be an iterable list") from error


def save_channel_gains_db(
    settings: SettingsRepository, unit_identifier: int, gains_db: Iterable[float]
) -> None:
    checked = validate_channel_gains_db(gains_db)
    settings.set(
        SCOPE_UNIT,
        CHANNEL_GAIN_DB_KEY,
        list(checked),
        unit_id=unit_identifier,
    )
