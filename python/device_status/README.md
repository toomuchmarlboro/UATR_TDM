# Device Status — vendored from HACAR_dash

HACAR_dash's Device Status window, copied whole into this repo so the valve
control can be added to it. PySide6, which is a third GUI toolkit here
alongside `mixer_gui.py` (tkinter) and `Host_RMI.py` (PyQt5).

```powershell
python run.py                    # all tabs, live services
python run.py --no-services      # the bare window, opens no sockets
python run.py --db bench.sqlite  # a settings database of your own
```

## What is here

| | |
|---|---|
| `supersilence/` | **Vendored. Do not edit.** 78 files, ~14,700 lines |
| `vendor.py` | Copies that tree out of HACAR_dash, and checks it is current |
| `run.py` | Composes the services and opens the window, mirroring `app/main.py` |

## The tabs

- **Buoys** — the AFE pages. One sub-tab per unit (T1–T4), each carrying
  sixteen channel meters, gain faders, channel enable and polarity, and the
  48 V phantom control.
- **Telemetry** — decoded `$GDAT2` fields per unit, link statistics, compass
  and horizon.
- **Pipeline** — needs a `target_provider`, which is the console's
  direction-finding stack. Not vendored, so this tab never appears here.

A tab is built only when the service behind it exists. That is the window's own
design, and deliberate — its comment reads *"a tab of ten dashes says a field
map is broken when the truth is that telemetry is switched off"*. `--no-services`
therefore shows "No acquisition or telemetry service is running.", which is the
window working, not a fault.

## Keeping the copy honest

`supersilence/` is generated, for the same reason `mixer_gui_standalone.py` is:
a hand-maintained copy of another project's source drifts silently — the window
still opens, still paints, and still shows numbers, just not the ones the other
repo now produces.

```powershell
python vendor.py            # refresh from HACAR_dash
python vendor.py --check    # exit 1 if stale, and name the files
python vendor.py --list     # what is in the closure, and how big
```

The source defaults to `../../../HACAR_dash/src` — a sibling checkout — and is
overridden with `--src` or `$SUPERSILENCE_SRC`. `--check` passes quietly when the
source is absent, so this repo stays buildable on a machine that has never had
HACAR_dash on it.

### What gets copied

The transitive import closure of four seeds, computed with `ast` rather than
swept up by a wildcard: the `device_status` feature, the acquisition factory,
the telemetry service, the settings repository, the SQLite schema and the
phantom-power command path. Nothing else from that repo comes along.

Package paths are preserved, so every `from supersilence.… import …` inside the
copied files is left exactly as written. That is why `run.py` puts its own
directory on `sys.path` and why the tree is not flattened the way the mixer GUI
is flattened.

## Addresses

These are **HACAR_dash's** defaults, not this array's. Its acquisition sources
and the `192.168.3.101–104` boards in `ctrl.py` are configured independently,
and nothing here rewrites one to match the other — a window that silently
retargeted the addresses in its own database would be the least debuggable
thing in either repo. Set them in the settings database, or point `--db` at one
that already holds them.

Telemetry also ships disabled: `default_telemetry_configuration()` has
`enabled=False`, so a fresh database connects to nothing until you turn it on.

## Next

The valve control goes on the Buoys page beside the 48 V control — the one
other place this window reaches past a service and into hardware. The command
itself already exists in this repo as `gdat2.rmcmd`, with `RMCMD_OPEN = 5` and
`RMCMD_CLOSE = 1`.
