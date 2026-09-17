"""Reading and writing settings.

Values are stored JSON-encoded, so a setting keeps its type: ``True`` comes back
as a boolean and not as the string ``"True"``. Type coercion scattered across
call sites is how a threshold ends up compared as text.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any

#: Settings shared by the whole console — window layout, theme, log policy.
SCOPE_SYSTEM = "system"
#: Settings for fusing several units into one picture.
SCOPE_TRIANGULATION = "triangulation"
#: Settings belonging to one acquisition unit.
SCOPE_UNIT = "unit"

SCOPES = (SCOPE_SYSTEM, SCOPE_TRIANGULATION, SCOPE_UNIT)

#: Stored in ``unit_id`` for rows that are not unit-scoped. Not NULL, because a
#: NULL inside a primary key disables the uniqueness this table depends on.
NO_UNIT = 0

_MISSING = object()


class SettingsRepository:
    """Scoped key-value settings, backed by SQLite.

    A key belongs to exactly one scope. That is enforced by the table's primary
    key rather than by convention, so the same name in two scopes is two distinct
    settings and can never be a silent overwrite of one by the other.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def get(self, scope: str, key: str, default: Any = None, unit_id: int = NO_UNIT) -> Any:
        row = self._connection.execute(
            "SELECT value FROM settings WHERE scope = ? AND unit_id = ? AND key = ?",
            (self._checked_scope(scope, unit_id), unit_id, key),
        ).fetchone()
        if row is None:
            return default
        return json.loads(row["value"])

    def set(self, scope: str, key: str, value: Any, unit_id: int = NO_UNIT) -> None:
        checked_scope = self._checked_scope(scope, unit_id)
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO settings (scope, unit_id, key, value, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (scope, unit_id, key)
                DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
                """,
                (
                    checked_scope,
                    unit_id,
                    key,
                    json.dumps(value),
                    datetime.now(timezone.utc).isoformat(timespec="seconds"),
                ),
            )

    def delete(self, scope: str, key: str, unit_id: int = NO_UNIT) -> bool:
        """Remove a setting. Returns whether there was one to remove."""
        with self._connection:
            cursor = self._connection.execute(
                "DELETE FROM settings WHERE scope = ? AND unit_id = ? AND key = ?",
                (self._checked_scope(scope, unit_id), unit_id, key),
            )
        return cursor.rowcount > 0

    def all_in_scope(self, scope: str, unit_id: int = NO_UNIT) -> dict[str, Any]:
        """Every setting in one scope, for export and for review dialogs."""
        rows = self._connection.execute(
            "SELECT key, value FROM settings WHERE scope = ? AND unit_id = ? ORDER BY key",
            (self._checked_scope(scope, unit_id), unit_id),
        ).fetchall()
        return {row["key"]: json.loads(row["value"]) for row in rows}

    @staticmethod
    def _checked_scope(scope: str, unit_id: int) -> str:
        """Reject a nonsensical scope/unit pairing before SQLite has to.

        The table constrains this too, but a Python error names the calling code;
        an sqlite3.IntegrityError names the table.
        """
        if scope not in SCOPES:
            raise ValueError(f"unknown settings scope: {scope!r}. Expected one of {SCOPES}.")
        if scope == SCOPE_UNIT and unit_id == NO_UNIT:
            raise ValueError("unit-scoped settings need a unit_id")
        if scope != SCOPE_UNIT and unit_id != NO_UNIT:
            raise ValueError(f"{scope!r} settings are shared and cannot carry a unit_id")
        return scope
