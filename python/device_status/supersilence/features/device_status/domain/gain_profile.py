"""A saved set of channel gains, as a file an operator can carry off the console.

Balancing sixteen channels on four buoys is measurement work, and until now the
only copy of the result lived in this console's SQLite settings. A console
reinstalled, a second console at the same site, or a set of gains an operator
wants back after trying something else all needed the whole calibration done
again. This module is the document format that makes those gains portable: a
plain JSON object, readable and editable by hand, with enough naming in it that
a file found later can be identified.

Pure, like everything else under `domain/`: no Qt, no file system, no settings
repository. The caller reads or writes the bytes and this decides what they
mean. The working range and the channel count are *given* rather than imported,
for the same reason `linked_gain.py` states — they are facts about the
acquisition path, and domain code does not reach into infrastructure for them.

Unit identifiers are JSON object keys, so they are strings on the wire and
integers on both sides of it. A file is accepted with unknown extra keys and
rejected with wrong ones: a future version may add fields, and refusing a file
because it says more than this version understands would make the format
unextendable.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

from supersilence.features.device_status.domain.linked_gain import GainRange

#: Written into every exported file and checked on every import. A JSON file
#: with the wrong marker is some other program's, and applying its numbers to
#: sixteen hydrophone channels because they happened to parse is worse than
#: refusing it.
PROFILE_FORMAT = "supersilence.channel_gain_profile"
PROFILE_VERSION = 1


def serialize_gain_profile(gains_by_unit: Mapping[int, Sequence[float]], gain_range: GainRange) -> dict:
    """The JSON-ready document for these units' gains.

    Every unit is validated against the range before it is written: a file that
    cannot be imported back is not worth exporting, and the moment to find that
    out is while the operator is still looking at the export dialog.
    """
    if not gains_by_unit:
        raise ValueError("there are no channel gains to export")
    units = {}
    for unit_identifier, gains_db in sorted(gains_by_unit.items()):
        units[str(int(unit_identifier))] = list(gain_range.validated(gains_db))
    return {
        "format": PROFILE_FORMAT,
        "version": PROFILE_VERSION,
        "channel_count": gain_range.channel_count,
        "units": units,
    }


def parse_gain_profile(payload: object, gain_range: GainRange) -> dict[int, tuple[float, ...]]:
    """The units and gains in a document read back from a file.

    Raises `ValueError` with a line the operator can act on. Nothing here is a
    programming error the console should crash on: every one of these failures
    is an ordinary consequence of choosing the wrong file.
    """
    if not isinstance(payload, Mapping):
        raise ValueError("this file does not contain a channel gain profile")
    if payload.get("format") != PROFILE_FORMAT:
        raise ValueError("this file is not a channel gain profile")
    version = payload.get("version")
    if not isinstance(version, int) or isinstance(version, bool) or version > PROFILE_VERSION:
        raise ValueError(f"this profile was written by a newer console (version {version!r})")
    units = payload.get("units")
    if not isinstance(units, Mapping) or not units:
        raise ValueError("this profile names no units")

    parsed: dict[int, tuple[float, ...]] = {}
    for key, gains_db in units.items():
        try:
            unit_identifier = int(key)
        except (TypeError, ValueError) as error:
            raise ValueError(f"{key!r} is not a unit identifier") from error
        if isinstance(gains_db, (str, bytes)) or not isinstance(gains_db, Sequence):
            raise ValueError(f"unit {unit_identifier} does not carry a list of channel gains")
        try:
            values = tuple(float(value) for value in gains_db)
        except (TypeError, ValueError) as error:
            raise ValueError(f"unit {unit_identifier} carries a channel gain that is not a number") from error
        if any(not math.isfinite(value) for value in values):
            raise ValueError(f"unit {unit_identifier} carries a channel gain that is not a finite number")
        try:
            parsed[unit_identifier] = gain_range.validated(values)
        except ValueError as error:
            raise ValueError(f"unit {unit_identifier}: {error}") from error
    return parsed


def select_unit_gains(profile: Mapping[int, Sequence[float]], unit_identifier: int) -> tuple[float, ...]:
    """The gains this unit should take from a profile.

    A file that names this unit answers directly. A file that carries exactly
    one unit answers too, and deliberately: gains exported from T1 and applied
    to T3 is a real operator action — the same hardware, moved — and refusing it
    would send the operator to a text editor to change one digit. A file with
    several units and none of them this one is ambiguous, and guessing which of
    them was meant is not this module's decision to make.
    """
    if unit_identifier in profile:
        return tuple(float(value) for value in profile[unit_identifier])
    if len(profile) == 1:
        (only,) = profile.values()
        return tuple(float(value) for value in only)
    named = ", ".join(str(identifier) for identifier in sorted(profile))
    raise ValueError(f"this profile carries units {named} and not unit {unit_identifier}")
