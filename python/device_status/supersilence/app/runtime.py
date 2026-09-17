"""Where the application is running from, and where it may write.

These three questions have different answers depending on whether the app was
started from a source checkout or from a built bundle, and getting them wrong
is not visible until the bundle is on an operator's machine:

* bundled resources live *inside* a read-only archive,
* the working directory is wherever the operator happened to launch from,
* the install folder may not be writable at all.

So nothing outside this module is allowed to build a path from ``__file__`` or
from a relative string. Ask here instead.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

#: Used for the per-user data folder. Lowercase on purpose — it becomes a
#: directory name on three operating systems with three different conventions.
APPLICATION_NAME = "supersilence"


def is_frozen() -> bool:
    """True when running from a PyInstaller bundle rather than from source."""
    return bool(getattr(sys, "frozen", False))


def resource_root() -> Path:
    """Folder that read-only bundled resources are addressed from.

    Frozen, PyInstaller unpacks data files under ``sys._MEIPASS``. From source,
    the equivalent root is the package folder itself, so a resource declared as
    ``features/triangulation/web/map.html`` resolves identically in both modes.
    """
    if is_frozen():
        bundle_dir = getattr(sys, "_MEIPASS", None)
        if bundle_dir:
            return Path(bundle_dir)
        # A bundle without _MEIPASS is a onefile build that failed to unpack, or
        # a future PyInstaller change. The executable's folder is the only other
        # defensible answer; guessing silently would be worse.
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def resource_path(*parts: str) -> Path:
    """Absolute path to a bundled resource, given its parts relative to the package."""
    return resource_root().joinpath(*parts)


def user_data_root() -> Path:
    """Per-user folder the application may write to.

    Deliberately not next to the executable: an installed bundle can sit in a
    location the operator has no write access to, and a cache or database that
    silently fails to open is the kind of fault that only shows up in the field.
    """
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        root = Path(base) if base else Path.home() / "AppData" / "Local"
    elif sys.platform == "darwin":
        root = Path.home() / "Library" / "Application Support"
    else:
        base = os.environ.get("XDG_DATA_HOME")
        root = Path(base) if base else Path.home() / ".local" / "share"
    return root / APPLICATION_NAME


def user_data_path(*parts: str, create_parents: bool = False) -> Path:
    """Absolute path inside the per-user data folder.

    ``create_parents`` makes the containing folders, not the file itself, so a
    caller can hand the result straight to sqlite3 or to an open() for writing.
    """
    path = user_data_root().joinpath(*parts)
    if create_parents:
        path.parent.mkdir(parents=True, exist_ok=True)
    return path


def describe() -> dict[str, str]:
    """Every path decision this module makes, for ``supersilence --paths``.

    Worth having as a command: when a bundle misbehaves on a machine we cannot
    attach a debugger to, the first question is always which paths it resolved.
    """
    return {
        "mode": "frozen" if is_frozen() else "source",
        "executable": str(Path(sys.executable).resolve()),
        "resource_root": str(resource_root()),
        "user_data_root": str(user_data_root()),
        "python": sys.version.split()[0],
    }
