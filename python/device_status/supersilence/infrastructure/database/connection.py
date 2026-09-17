"""Opening the application database.

One place decides where the file lives and how the connection is configured, so
those two answers cannot differ between callers.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from supersilence.app import runtime

#: Name of the database file inside the per-user data folder.
DATABASE_FILENAME = "supersilence.sqlite3"


def database_path() -> Path:
    """Where the database lives.

    Under the per-user data folder, never beside the executable: an installed
    bundle can sit somewhere the operator cannot write.
    """
    return runtime.user_data_path("database", DATABASE_FILENAME, create_parents=True)


def open_database(path: Path | str | None = None) -> sqlite3.Connection:
    """Open a connection with the settings the rest of the application assumes.

    ``path`` is for tests, which pass a temporary file or ``:memory:``.
    """
    target = str(path) if path is not None else str(database_path())
    connection = sqlite3.connect(target)
    connection.row_factory = sqlite3.Row

    # Enforced per connection, not stored in the file: SQLite defaults foreign
    # keys OFF for backwards compatibility, so a connection that forgets this
    # silently accepts rows the schema was written to reject.
    connection.execute("PRAGMA foreign_keys = ON")

    # Write-ahead logging: a reader is not blocked by a writer. The console reads
    # settings while the operator is editing them, and the default rollback
    # journal turns that into lock contention.
    connection.execute("PRAGMA journal_mode = WAL")

    return connection
