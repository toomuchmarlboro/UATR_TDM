"""Schema migrations.

Forward-only, one step at a time, never a jump from version 1 to version 4. A
direct jump cannot be tested in isolation: you can only verify the end state, not
that each intermediate schema was reachable from the one before it. The previous
version of this project settled on the same rule for the same reason.

Adding a migration means appending to :data:`MIGRATIONS` and never editing an
entry that has already shipped — an installed database has already run it.
"""
from __future__ import annotations

import sqlite3
from collections.abc import Callable

#: Every migration, in order. Index + 1 is the schema version it produces.
Migration = Callable[[sqlite3.Connection], None]


def _create_settings(connection: sqlite3.Connection) -> None:
    """Version 1 — the scoped settings table.

    One table, three scopes. The old project kept the same information in three
    JSON files and needed a test to prove no field appeared in two of them; a
    duplicated field drifted, and whichever file loaded last silently won. Here
    the primary key makes that impossible at write time.

    ``unit_id`` is NOT NULL with a default of 0 rather than nullable, and that is
    load-bearing: in SQLite ``NULL != NULL``, so a nullable column inside a
    primary key stops enforcing uniqueness altogether — the exact guarantee this
    table exists to provide would quietly not hold.
    """
    connection.execute(
        """
        CREATE TABLE settings (
            scope      TEXT    NOT NULL CHECK (scope IN ('system', 'triangulation', 'unit')),
            unit_id    INTEGER NOT NULL DEFAULT 0,
            key        TEXT    NOT NULL,
            value      TEXT    NOT NULL,
            updated_at TEXT    NOT NULL,
            PRIMARY KEY (scope, unit_id, key),
            -- A unit-scoped row without a unit, or a shared row carrying one,
            -- is a bug in the caller. Reject it here rather than store it.
            CHECK ((scope = 'unit') = (unit_id != 0))
        )
        """
    )


def _create_iff_records(connection: sqlite3.Connection) -> None:
    """Version 2 — operator-maintained IFF identity records."""
    connection.execute(
        """
        CREATE TABLE iff_records (
            identifier TEXT PRIMARY KEY NOT NULL CHECK (length(trim(identifier)) > 0),
            platform   TEXT NOT NULL CHECK (length(trim(platform)) > 0),
            notes      TEXT NOT NULL DEFAULT ''
        )
        """
    )


def _create_iff_signatures(connection: sqlite3.Connection) -> None:
    """Version 3 — acoustic signatures, replacing bare identity records.

    Version 2 stored an identity and nothing to compare a detection against.
    Classification needs measured evidence, so a signature now carries tonal
    lines and optional DEMON shaft rate plus blade count.

    Tonal lines live in their own table rather than a delimited column. A
    signature has one *or more* of them, they are compared individually, and a
    text column would push both the parsing and the uniqueness guarantee up into
    Python where nothing enforces them.

    Every version 2 row is carried across with no tonal lines, so an operator's
    existing records survive the upgrade. They are unmatchable until measured
    lines are added, which is visible rather than silent. ``iff_records`` is
    deliberately left in place and never read again: dropping it would destroy
    the only copy of that data if this migration turns out to have translated it
    wrongly.
    """
    connection.execute(
        """
        CREATE TABLE iff_signatures (
            name                  TEXT PRIMARY KEY NOT NULL CHECK (length(trim(name)) > 0),
            vessel_class          TEXT NOT NULL CHECK (length(trim(vessel_class)) > 0),
            demon_shaft_rate_hz   REAL
                CHECK (demon_shaft_rate_hz IS NULL OR demon_shaft_rate_hz > 0),
            propeller_blade_count INTEGER
                CHECK (propeller_blade_count IS NULL OR propeller_blade_count >= 2),
            notes                 TEXT NOT NULL DEFAULT ''
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE iff_signature_tonals (
            signature_name TEXT NOT NULL
                REFERENCES iff_signatures (name) ON DELETE CASCADE,
            frequency_hz   REAL NOT NULL CHECK (frequency_hz > 0),
            -- One line cannot be listed twice for one signature, and the
            -- primary key is also the lookup order when loading a signature.
            PRIMARY KEY (signature_name, frequency_hz)
        )
        """
    )
    connection.execute(
        """
        INSERT INTO iff_signatures (name, vessel_class, notes)
        SELECT identifier, platform, notes FROM iff_records
        """
    )


def _add_signature_disposition(connection: sqlite3.Connection) -> None:
    """Version 4 — friend, known, or threat, stored against the vessel.

    The label an operator sees is not derived from a signature's acoustics or
    from the text of its class. It is a decision recorded about that vessel, and
    the previous system stored it the same way for the same reason: a vessel's
    disposition is intelligence, not a measurement.

    ``UNKNOWN`` is deliberately absent from the CHECK. It is the outcome when no
    signature matches well enough, never a stored value, so a row can never
    assert that a vessel is unidentifiable.

    Existing rows become ``KNOWN``: it neither hides a contact the way FRIEND
    would nor raises an alarm the way THREAT would.
    """
    connection.execute(
        """
        ALTER TABLE iff_signatures ADD COLUMN disposition TEXT NOT NULL DEFAULT 'KNOWN'
            CHECK (disposition IN ('FRIEND', 'KNOWN', 'THREAT'))
        """
    )


MIGRATIONS: list[Migration] = [
    _create_settings,
    _create_iff_records,
    _create_iff_signatures,
    _add_signature_disposition,
]

#: Schema version the current code expects.
TARGET_VERSION = len(MIGRATIONS)


def current_version(connection: sqlite3.Connection) -> int:
    """Schema version of this database. Zero means empty."""
    connection.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)")
    row = connection.execute("SELECT version FROM schema_version").fetchone()
    return int(row["version"]) if row is not None else 0


def apply_migrations(connection: sqlite3.Connection) -> int:
    """Bring the database up to :data:`TARGET_VERSION`. Returns the new version.

    Running this on an up-to-date database does nothing, so it is safe on every
    launch — which is the point, since that is where it is called from.
    """
    version = current_version(connection)

    if version > TARGET_VERSION:
        # Downgrading would have to guess what a newer schema meant. Refusing is
        # the only honest answer: the operator has opened a database written by a
        # newer build than the one they are running.
        raise RuntimeError(
            f"database schema is version {version}, but this build only understands "
            f"{TARGET_VERSION}. It was written by a newer version of the application."
        )

    for step in range(version, TARGET_VERSION):
        with connection:  # one transaction per migration — a failure leaves the previous version intact
            MIGRATIONS[step](connection)
            connection.execute("DELETE FROM schema_version")
            connection.execute("INSERT INTO schema_version (version) VALUES (?)", (step + 1,))

    return TARGET_VERSION
