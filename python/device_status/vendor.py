#!/usr/bin/env python3
"""Vendor HACAR_dash's Device Status window into this repo, imports unchanged.

    python vendor.py                 # copy / refresh supersilence/
    python vendor.py --check         # fail if the copy is out of date
    python vendor.py --list          # what would be copied, and how big

WHY A SCRIPT AND NOT A HAND COPY
================================
The same argument make_gui_standalone.py makes about the telemetry field map.
A hand-maintained copy of another project's source drifts the moment that
project changes, and it drifts SILENTLY: the window still opens, still paints,
and still shows numbers - just not the ones the other repo is now producing.
A copy that is REGENERATED cannot drift, and `--check` says so out loud.

WHAT IS COPIED
==============
The transitive import closure of supersilence.features.device_status, and
nothing else. That is a real boundary rather than a guess: this window was
written to be HANDED its acquisition and telemetry services rather than to
import them, so the closure stops at the service interfaces instead of
dragging in the whole console. 46 files at the time of writing, against a
source tree many times that.

Package paths are preserved, so every `from supersilence.… import …` inside the
copied files is left exactly as written - which is the point of vendoring the
tree rather than flattening it the way the mixer GUI is flattened.

WHERE THE SOURCE COMES FROM
===========================
$SUPERSILENCE_SRC if set, else ../../../HACAR_dash/src, i.e. a sibling checkout
of this repo. Pass --src to override. A missing source is not an error for
--check when the copy already exists: this repo has to stay buildable on a
machine that does not have HACAR_dash checked out at all.
"""

import argparse
import ast
import collections
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEST = os.path.join(HERE, "supersilence")
PKG = "supersilence"

# WHAT THE COPY IS SEEDED FROM. The window alone is only the view - it is handed
# its services and builds a tab only when the service behind it exists, so
# seeding on the feature package alone produces a window that opens and says
# "No acquisition or telemetry service is running." The services are named here
# as well, so what lands in this repo is the working thing rather than its
# shell.
#
# A directory is walked whole; a dotted module is taken with its closure.
SEEDS = (
    "supersilence.features.device_status",            # the window and its tabs
    "supersilence.infrastructure.acquisition.factory",   # create_acquisition_service
    "supersilence.infrastructure.telemetry.service",     # TelemetryService
    "supersilence.infrastructure.settings.repository",   # persisted gains, offsets
    "supersilence.infrastructure.database",              # the SQLite schema behind it
    "supersilence.infrastructure.control.phantom_power",  # the 48 V command path
)

# ------------------------------------------------------ local work, pending --
# THE VALVE DOES NOT EXIST UPSTREAM. `grep -rn RMCMD` over HACAR_dash returns
# nothing: that project has never had an actuator. The files below are ours,
# written in its architecture so they can be merged back, and until they are
# this script must not treat them as drift.
#
# Without this, the two halves of the tool both do the wrong thing: `--check`
# calls our new modules ORPHANs and our edits STALE, and a plain `vendor.py`
# DELETES the new files and overwrites the edited ones with the upstream
# version. That second one is the reason this list is not merely cosmetic.

#: Ours entirely. Copied from nowhere, so never stale and never orphaned.
LOCAL_ONLY = frozenset({
    os.path.join(PKG, "infrastructure", "telemetry", "valve.py"),
    os.path.join(PKG, "features", "device_status", "domain", "valve.py"),
    os.path.join(PKG, "features", "device_status", "ui", "valve_control.py"),
    os.path.join(PKG, "features", "device_status", "ui", "claw.py"),
    os.path.join(PKG, "features", "device_status", "ui", "telemetry_connection.py"),
})

#: Upstream files carrying local edits. A refresh would throw those edits away,
#: so refreshing one is refused unless --force says to, and then it is on the
#: operator to re-apply them.
LOCALLY_MODIFIED = frozenset({
    # send(), the only write path on a client that otherwise only reads.
    os.path.join(PKG, "infrastructure", "telemetry", "tcp_client.py"),
    # send_valve_command(), and reconfigure() for the connect button.
    os.path.join(PKG, "infrastructure", "telemetry", "service.py"),
    # The connect bar on the telemetry tab, and the handlers behind it and the
    # valve.
    os.path.join(PKG, "features", "device_status", "ui", "window.py"),
    # The Valve box beside Compass / Artificial horizon / Altimeter, and the
    # IMU row dropped from the role status bar.
    os.path.join(PKG, "features", "device_status", "ui", "attitude_instruments.py"),
    # The two altimeter rows, fed from the Ping1D link instead of reading zero.
    os.path.join(PKG, "features", "device_status", "ui", "telemetry_fields.py"),
})

DEFAULT_SRC = os.path.normpath(
    os.path.join(HERE, "..", "..", "..", "HACAR_dash", "src"))


def module_path(src, mod):
    """Dotted module name -> its file, or None if it is not a module here."""
    base = os.path.join(src, *mod.split("."))
    for cand in (base + ".py", os.path.join(base, "__init__.py")):
        if os.path.isfile(cand):
            return cand
    return None


def closure(src):
    """-> sorted relative paths of every file the seed package needs.

    Walks imports with `ast`, so what lands here is what the code actually
    reads rather than what a wildcard would sweep up.

    `from x.y import z` is ambiguous in Python - z can be a name in x.y or a
    submodule of it - so both readings are queued and whichever exists on disk
    wins. Missing that is how a vendored tree imports cleanly and then raises
    ModuleNotFoundError on the one screen nobody opened during testing.
    """
    seen, queue = set(), collections.deque()

    for seed in SEEDS:
        seed_dir = os.path.join(src, *seed.split("."))
        if os.path.isdir(seed_dir):
            for root, _dirs, files in os.walk(seed_dir):
                for f in files:
                    if f.endswith(".py"):
                        rel = os.path.relpath(os.path.join(root, f), src)
                        mod = rel[:-3].replace(os.sep, ".")
                        queue.append(mod[:-9] if mod.endswith(".__init__")
                                     else mod)
        elif module_path(src, seed):
            queue.append(seed)
        else:
            raise SystemExit("vendor: no %s under %s - renamed or moved "
                             "upstream" % (seed, src))

    while queue:
        mod = queue.popleft()
        if mod in seen:
            continue
        seen.add(mod)
        path = module_path(src, mod)
        if path is None:
            continue
        with open(path, encoding="utf-8") as fh:
            tree = ast.parse(fh.read(), path)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.level or not node.module:
                    # Relative imports resolve inside a package that is copied
                    # whole, so they need no follow-up. Bare `from . import x`
                    # is likewise already covered by the directory walk.
                    continue
                if node.module.startswith(PKG):
                    queue.append(node.module)
                    for alias in node.names:
                        sub = "%s.%s" % (node.module, alias.name)
                        if module_path(src, sub):
                            queue.append(sub)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith(PKG):
                        queue.append(alias.name)

    files = set()
    for mod in seen:
        path = module_path(src, mod)
        if path is None:
            continue
        rel = os.path.relpath(path, src)
        files.add(rel)
        # Every parent package needs its __init__.py or the import machinery
        # cannot reach the module at all. These are pulled in implicitly at
        # runtime and so are never named by an import statement - the one class
        # of file an import-following walk will always miss.
        d = os.path.dirname(rel)
        while d and d != PKG and os.sep in d:
            init = os.path.join(d, "__init__.py")
            if os.path.isfile(os.path.join(src, init)):
                files.add(init)
            d = os.path.dirname(d)
        root_init = os.path.join(PKG, "__init__.py")
        if os.path.isfile(os.path.join(src, root_init)):
            files.add(root_init)
    return sorted(files)


def read(path):
    with open(path, "rb") as fh:
        return fh.read()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--src", default=os.environ.get("SUPERSILENCE_SRC",
                                                    DEFAULT_SRC),
                    help="HACAR_dash's src/ directory")
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if the vendored copy differs from the source")
    ap.add_argument("--list", action="store_true",
                    help="show what would be copied, and copy nothing")
    ap.add_argument("--force", action="store_true",
                    help="refresh even over files carrying local edits, "
                         "discarding them")
    a = ap.parse_args()

    if not os.path.isdir(a.src):
        if a.check and os.path.isdir(DEST):
            # Deliberately not a failure. This repo must stay buildable on a
            # machine without HACAR_dash checked out, and "I cannot see the
            # source" is not evidence that the copy is wrong.
            print("vendor: source not found at %s - skipping check" % a.src)
            return 0
        raise SystemExit("vendor: source not found at %s\n"
                         "        pass --src or set SUPERSILENCE_SRC" % a.src)

    files = closure(a.src)
    total = sum(len(read(os.path.join(a.src, f)).splitlines()) for f in files)

    if a.list:
        for f in files:
            print("   ", f)
        print("\n%d files, %d lines" % (len(files), total))
        return 0

    if a.check:
        stale, diverged = [], []
        for f in files:
            dst = os.path.join(HERE, f)
            if not os.path.exists(dst) or read(dst) != read(os.path.join(a.src, f)):
                (diverged if f in LOCALLY_MODIFIED else stale).append(f)
        extra, local = [], []
        for root, _d, fs in os.walk(DEST):
            for f in fs:
                if not f.endswith(".py"):
                    continue
                rel = os.path.relpath(os.path.join(root, f), HERE)
                if rel in LOCAL_ONLY:
                    local.append(rel)
                elif rel not in files:
                    extra.append(rel)
        for f in sorted(local):
            print("LOCAL:   %s  (ours; not upstream yet)" % f)
        for f in sorted(diverged):
            print("PATCHED: %s  (upstream file with local edits)" % f)
        if stale or extra:
            for f in stale:
                print("STALE:   %s" % f)
            for f in extra:
                print("ORPHAN:  %s  (no longer in the closure)" % f)
            print("\nre-run 'python vendor.py'")
            return 1
        print("up to date: %d files, %d lines (+%d local, %d patched)"
              % (len(files), total, len(local), len(diverged)))
        return 0

    # Files we would be about to overwrite local work in. Refused by default:
    # losing a hand-written module to a refresh is not a thing to discover
    # afterwards from a diff.
    at_risk = sorted(f for f in files
                     if f in LOCALLY_MODIFIED and os.path.exists(os.path.join(HERE, f)))
    if at_risk and not a.force:
        for f in at_risk:
            print("REFUSING: %s carries local edits" % f)
        print("\nThese are upstream files this repo has changed - the valve and\n"
              "the telemetry connect bar. Refreshing would discard those edits.\n"
              "Merge them upstream first, or re-run with --force and re-apply\n"
              "them by hand.")
        return 1

    # Remove the old tree first, so a module deleted upstream does not linger
    # here as an orphan that still imports - but keep what is ours.
    preserved = {}
    for rel in LOCAL_ONLY:
        path = os.path.join(HERE, rel)
        if os.path.isfile(path):
            preserved[rel] = read(path)
    if os.path.isdir(DEST):
        shutil.rmtree(DEST)
    for f in files:
        dst = os.path.join(HERE, f)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(os.path.join(a.src, f), dst)
    for rel, blob in preserved.items():
        dst = os.path.join(HERE, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "wb") as fh:
            fh.write(blob)
    print("vendored %d files, %d lines, from %s%s"
          % (len(files), total, a.src,
             "  (%d local files kept)" % len(preserved) if preserved else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
