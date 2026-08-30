#!/usr/bin/env python3
"""
Generate mixer_gui_standalone.py - the mixer GUI with no local-file imports.

    python make_gui_standalone.py            # writes mixer_gui_standalone.py
    python make_gui_standalone.py --check    # fail if the file is out of date

WHAT "STANDALONE" MEANS HERE
============================
No imports from other files in this directory: no gdat2, ctrl, udp_monitor or
imu_test. Installed libraries are fine and numpy is kept, exactly as the real
GUI uses it. The result is one file you can copy next to a Python with numpy
and run.

WHY A GENERATOR AND NOT A HAND-WRITTEN COPY
===========================================
The standalone file has to carry its own copy of the telemetry field map, the
packet geometry and the gain law. A hand-maintained copy of those is precisely
the defect this toolchain exists to catch: when the firmware adds a telemetry
field, every value after it slides one place and the copy keeps printing
believable numbers under the wrong headings. A copy that is REGENERATED cannot
drift - it is extracted from the real modules every time.

So: never edit mixer_gui_standalone.py. Edit the real modules and re-run this.
`--check` is the guard and belongs in any pre-release pass.

HOW
===
Definitions are sliced out of each source by name using `ast`, so what lands in
the output is the real text rather than a paraphrase. The GUI body is then taken
verbatim apart from its local imports, which are removed. A missing definition
or a failed substitution stops the build - emitting a file that dies on the
target machine is the one outcome worth failing loudly to avoid.
"""

import argparse
import ast
import builtins
import os
import symtable
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "mixer_gui_standalone.py")

# Imports the generated file needs at the top: the union of what every inlined
# module and the GUI body use. numpy included - it is an installed library, not
# a local file, so it stays.
PRELUDE_IMPORTS = ("argparse", "collections", "math", "os", "socket", "struct",
                   "sys", "threading", "time")


def _src(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        return f.read()


def top_level_names(source):
    """-> set of names bound at module level. Used to catch collisions."""
    out = set()
    for node in ast.parse(source).body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            out.add(node.name)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    out.add(t.id)
                elif isinstance(t, ast.Tuple):
                    out.update(e.id for e in t.elts if isinstance(e, ast.Name))
    return out


def slice_defs(source, names):
    """Return the source text of the named top-level definitions, in order.

    Uses ast so a definition is taken whole - decorators, body, comments inside
    it - rather than matched by a regex that breaks the first time someone adds
    a blank line.
    """
    tree = ast.parse(source)
    lines = source.splitlines(True)
    span = {}
    for node in tree.body:
        keys = []
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            keys = [node.name]
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    keys.append(t.id)
                elif isinstance(t, ast.Tuple):
                    keys += [e.id for e in t.elts if isinstance(e, ast.Name)]
        for key in keys:
            start = min([node.lineno] + [d.lineno for d in
                                         getattr(node, "decorator_list", [])])
            span.setdefault(key, (start, node.end_lineno))

    out, seen = [], set()
    for n in names:
        if n not in span:
            raise SystemExit("make_gui_standalone: %r not found - renamed or "
                             "removed upstream" % n)
        a, b = span[n]
        if (a, b) in seen:            # tuple assignment requested by two names
            continue
        seen.add((a, b))
        out.append("".join(lines[a - 1:b]).rstrip() + "\n")
    return "\n".join(out)


def undefined_globals(source):
    """-> names the source reads as globals but never defines or imports.

    Extracting definitions by name is only as good as the list of names, and a
    private helper is exactly what gets forgotten: the first build of this file
    pulled decode_field but not the _HEX set it reads, so the generated GUI
    imported cleanly and then raised NameError the first time a sentence
    arrived. A missing name must fail the BUILD, not the deployment.

    symtable does the scope analysis properly - locals, parameters,
    comprehension variables and closures are all accounted for, which a plain
    walk over ast.Name would get wrong.
    """
    st = symtable.symtable(source, "generated", "exec")
    top = set(st.get_identifiers())
    missing = set()

    def walk(table):
        for sym in table.get_symbols():
            if sym.is_global() and not sym.is_assigned():
                n = sym.get_name()
                if n not in top and not hasattr(builtins, n):
                    missing.add(n)
        for child in table.get_children():
            walk(child)

    walk(st)
    return missing


def sub_once(text, old, new, what):
    """Replace exactly once, or fail loudly."""
    n = text.count(old)
    if n != 1:
        raise SystemExit("make_gui_standalone: expected 1 occurrence of %s, "
                         "found %d. mixer_gui.py changed - update this script."
                         % (what, n))
    return text.replace(old, new)


HEADER = '''#!/usr/bin/env python3
"""
UATR control station - hydrophone mixer, buoy telemetry and sonar, in ONE file.

    python mixer_gui_standalone.py                # everything
    python mixer_gui_standalone.py --nodes 1,3    # only the boards you have
    python mixer_gui_standalone.py --gdat-buoy 3 --gdat-connect

Copy this single file anywhere with Python, numpy and tkinter. It imports
nothing from its own directory.

  DO NOT EDIT THIS FILE - it is GENERATED. Edit the modules it is built from
  and re-run the generator:

      python make_gui_standalone.py            # rebuild
      python make_gui_standalone.py --check    # fail if stale

  Editing here creates a second, diverging copy of the telemetry field map,
  which is the exact fault this toolchain exists to catch: a map shifted by one
  place still frames, still checksums, and still prints perfectly formatted
  values under the wrong headings.


TABS
====
  AFE 1-4     16 hydrophone channels each - meters, gain faders, mute, 48 V.
              Own UDP port per board (5005-5008), own control IP
              (192.168.1.101-.104). Only the visible tab decodes; hidden tabs
              keep draining their sockets so the loss counters stay honest.
  Telemetry   All four buoys at a glance, plus compass and artificial horizon.
  Altimeter   Ping1D sonar: range, confidence, and its sensor settings.


THE FOUR THINGS WORTH KNOWING
=============================
1. THREE SENSORS PER BUOY, one digit apart, all on port 8080:

       192.168.3.1<buoy>0   $GDAT2 telemetry   (aux_vcu)
       192.168.3.1<buoy>1   WitMotion IMU      (binary, NOT $GDAT2)
       192.168.3.1<buoy>2   Ping1D altimeter   (Ping protocol)

   A wrong last digit reaches a REAL device that is not the one you meant, so
   the symptom is a decoder finding nothing rather than a connection error.

2. STALE IS WORSE THAN DISCONNECTED. A socket can stay open while the far end
   stops talking, and the last values sit there looking healthy. Every device
   cell here shows its packet rate when live and says STALE when not - it is
   never described as "connected" on the strength of the socket alone.

3. ATTITUDE IS CALIBRATED PER BUOY. Each unit reads a fixed heading error and
   a fixed tilt, set by how its IMU is bolted into that hull. The compass and
   horizon show the CORRECTED values and print the raw ones in brackets, so an
   applied offset is always visible. Buoy 3: heading -12.4 deg, level
   +2.15/-4.66 deg.

4. THE ALTIMETER NEEDS ITS SETTINGS WRITTEN. It powers up at a 250 ms ping
   interval - four measurements a second - and reads confidence 0 with the
   range wandering. The Altimeter tab writes the vendor settings on connect;
   "apply settings" rewrites them. Confidence, not range, tells you whether the
   sonar found anything: ~90 m at 0 % is its ceiling, meaning no echo.


READING THE TELEMETRY TAB
=========================
  ALL BUOYS   one row per buoy, one cell per device. A healthy device shows its
              rate; a sick one shows the fault in the same cell.
  Instruments compass and horizon for the SELECTED buoy. The caption says which
              device is driving them - the IMU when it is up, otherwise the
              aux_vcu, which relays the same attitude twenty times slower.
  Field table every $GDAT2 field with the bytes that produced it, so a decode
              can be checked without a capture. The "live" column is the one
              that stops a number being believed just because it is well
              formatted:
                live N      seen to change N times - proven alive
                constant ?  never changed. NOT a fault by itself: attitude is
                            quantised to 0.1 deg, so a still unit repeats one
                            value. Move it to settle the question
                zero        exactly zero forever - not being filled
              Out-of-range values turn red in place. That is how a shifted
              field map shows itself: attitude stays believable while the leak
              sensor reads 18 V.

  Known dead on this firmware: Altimeter dist/conf (the sonar is its own device
  - use the Altimeter tab), Voltage monitor, and Depth is unreliable.


IF NOTHING CONNECTS
===================
The host needs an address on the sensors' subnet. An adapter configured for the
FPGA soundcards (192.168.1.x) cannot reach 192.168.3.x at all, and the traffic
leaves over Wi-Fi instead. Windows allows a second address on one NIC:

    netsh interface ipv4 add address name="Ethernet" 192.168.3.240 255.255.255.0

If a link connects but decodes nothing, dump the bytes before suspecting the
sensor - that is how the IMU was found being read as $GDAT2.

See docs/TELEMETRY_INTEGRATION.md for the module contracts, the calibration
procedure, and how to lift the decoders into the PyQt application.
"""

'''

NS_DOC = '''

class _NS(object):
    """A stand-in for an imported module, so the GUI body needs no rewriting.

    The body still says gdat2.Link, um.CHANNELS, ctrl.decode,
    imu_test.AxisWindow. Keeping those spellings means this file is the real GUI
    source with its imports satisfied differently, rather than a fork of it that
    would have to be re-reviewed line by line.
    """

    def __init__(self, **kw):
        self.__dict__.update(kw)


'''


def build():
    gd, it = _src("gdat2.py"), _src("imu_test.py")
    ct, um_ = _src("ctrl.py"), _src("udp_monitor.py")
    p1 = _src("ping1d.py")
    wm = _src("witmotion.py")
    gui = _src("mixer_gui.py")

    parts = [HEADER]
    parts.append("".join("import %s\n" % m for m in PRELUDE_IMPORTS))
    parts.append("import tkinter as tk\n"
                 "from tkinter import ttk\n\n"
                 "import numpy as np\n")
    parts.append(NS_DOC)

    um_names = ["MAGIC", "HDR_LEN", "FRAME_LEN", "FRAMES_PKT", "PAYLOAD_LEN",
                "CHANNELS", "SAMPLE_BYTES", "FULL_SCALE", "SAMPLE_RATE"]
    ct_names = ["FPGA_IP", "FPGA_PORT", "STREAM_PORT", "MUTE", "ZERO_DB",
                "PHANTOM_FRAME", "node_ip", "node_stream_port", "gain_byte",
                "gain_db", "send_gain", "send_flags", "phantom_state",
                "phantom_reason", "decode"]
    # buoy_ip MUST precede BUOYS: BUOYS calls it at module level, and these are
    # emitted in list order, so putting it after would raise NameError on
    # import of the generated file.
    # ROLE_* must precede buoy_ip: they are its default argument and its
    # validation set, both evaluated at definition time.
    gd_names = ["TALKER", "N_RAW", "DEFAULT_PORT",
                "ROLE_GDAT2", "ROLE_IMU", "ROLE_ALTIMETER",
                "buoy_ip", "BUOYS", "IMUS", "ALTIMETERS", "ACTIVE_BUOY",
                "DEFAULT_HOST", "FIELDS", "DIO_OPEN", "DIO_CLOSE", "I_LEAK",
                "AHRS_IDX", "PLAUSIBLE", "implausible", "checksum", "build",
                "f32_bits", "bits_f32", "_HEX", "decode_field", "parse",
                "_int_or_none", "dio_text", "Link"]
    it_names = ["DEFAULT_WINDOW_S", "STILL_MAX", "MOVING_MIN", "wrapped_span",
                "AxisWindow"]
    # ping1d's module-level names are all prefixed (ping_build, PingLink,
    # PING_PORT ...) precisely so they can share this flat namespace with
    # gdat2's build/checksum/Link/Sim/DEFAULT_PORT. Everything is emitted into
    # one module here, and the collision check below only compares the GUI body
    # against the inlined set - not the inlined modules against each other - so
    # a clash between two of them would silently keep whichever came last.
    p1_names = ["PING_PORT", "PING_POLL_S", "PING_HEADER", "ID_GENERAL_REQUEST",
                "ID_NACK", "ID_DEVICE_INFORMATION", "ID_PROTOCOL_VERSION",
                "ID_DISTANCE", "ID_DISTANCE_SIMPLE", "DISTANCE_IDS", "SETTLE_S",
                "REPLY_TIMEOUT_S", "ID_GENERAL_INFO",
                "ID_SET_SPEED_OF_SOUND", "ID_SET_MODE_AUTO",
                "ID_SET_PING_INTERVAL", "ID_SET_GAIN_SETTING",
                "ID_SET_PING_ENABLE", "VENDOR_DEFAULTS",
                "parse_general_info", "set_message",
                "DIST_MAX_MM", "CONF_MAX",
                "ping_checksum", "ping_build", "ping_request", "PingParser",
                "parse_distance_simple", "parse_distance", "parse_nack",
                "PingLink"]
    # Same prefixing rule as ping1d: WitLink/WitParser/wit_* rather than
    # Link/Parser/checksum, so three protocol modules can share one namespace.
    wm_names = ["WIT_PORT", "WIT_HEADER", "WIT_ACCEL", "WIT_GYRO", "WIT_ANGLE",
                "WIT_MAG", "WIT_QUAT", "WIT_NAMES", "WIT_PACKET_LEN",
                "ANGLE_LIMITS", "HEADING_OFFSET_DEG", "heading", "LEVEL_OFFSET_DEG", "level", "wit_checksum", "wit_build", "wit_decode",
                "WitParser", "WitLink"]

    parts.append("# " + "-" * 66 + " inlined from udp_monitor.py ---\n")
    parts.append(slice_defs(um_, um_names))
    parts.append("\n# " + "-" * 73 + " inlined from ctrl.py ---\n")
    parts.append(slice_defs(ct, ct_names))
    parts.append("\n# " + "-" * 72 + " inlined from gdat2.py ---\n")
    parts.append(slice_defs(gd, gd_names))
    parts.append("\n# " + "-" * 69 + " inlined from imu_test.py ---\n")
    parts.append(slice_defs(it, it_names))
    parts.append("\n# " + "-" * 71 + " inlined from ping1d.py ---\n")
    parts.append(slice_defs(p1, p1_names))

    parts.append("\n# " + "-" * 65 + " module stand-ins ---\n")
    parts.append(
        "um = _NS(MAGIC=MAGIC, HDR_LEN=HDR_LEN, FRAME_LEN=FRAME_LEN,\n"
        "         FRAMES_PKT=FRAMES_PKT, PAYLOAD_LEN=PAYLOAD_LEN,\n"
        "         CHANNELS=CHANNELS, SAMPLE_BYTES=SAMPLE_BYTES,\n"
        "         FULL_SCALE=FULL_SCALE, SAMPLE_RATE=SAMPLE_RATE)\n"
        "ctrl = _NS(FPGA_IP=FPGA_IP, FPGA_PORT=FPGA_PORT,\n"
        "           STREAM_PORT=STREAM_PORT, MUTE=MUTE, ZERO_DB=ZERO_DB,\n"
        "           PHANTOM_FRAME=PHANTOM_FRAME, gain_byte=gain_byte,\n"
        "           gain_db=gain_db, send_gain=send_gain,\n"
        "           send_flags=send_flags, phantom_state=phantom_state,\n"
        "           phantom_reason=phantom_reason, decode=decode,\n"
        "           node_ip=node_ip, node_stream_port=node_stream_port)\n"
        "gdat2 = _NS(TALKER=TALKER, N_RAW=N_RAW, BUOYS=BUOYS, IMUS=IMUS,\n"
        "            ALTIMETERS=ALTIMETERS, buoy_ip=buoy_ip,\n"
        "            ROLE_GDAT2=ROLE_GDAT2, ROLE_IMU=ROLE_IMU,\n"
        "            ROLE_ALTIMETER=ROLE_ALTIMETER,\n"
        "            ACTIVE_BUOY=ACTIVE_BUOY, DEFAULT_HOST=DEFAULT_HOST,\n"
        "            DEFAULT_PORT=DEFAULT_PORT, FIELDS=FIELDS,\n"
        "            PLAUSIBLE=PLAUSIBLE, implausible=implausible,\n"
        "            dio_text=dio_text, parse=parse, build=build,\n"
        "            f32_bits=f32_bits, bits_f32=bits_f32, Link=Link)\n"
        "imu_test = _NS(AxisWindow=AxisWindow, wrapped_span=wrapped_span)\n"
        "ping1d = _NS(PingLink=PingLink, PING_PORT=PING_PORT,\n"
        "             DIST_MAX_MM=DIST_MAX_MM, CONF_MAX=CONF_MAX,\n"
        "             VENDOR_DEFAULTS=VENDOR_DEFAULTS,\n"
        "             set_message=set_message,\n"
        "             parse_general_info=parse_general_info)\n")

    # ---- the GUI body, verbatim apart from its imports ----
    body = gui
    # Drop the module docstring: the generated header replaces it, and two
    # docstrings would leave the wrong one visible to help().
    tree = ast.parse(body)
    if (tree.body and isinstance(tree.body[0], ast.Expr)
            and isinstance(tree.body[0].value, ast.Constant)):
        body = "".join(body.splitlines(True)[tree.body[0].end_lineno:])

    # The whole point: no imports from files in this directory.
    for imp in ("import udp_monitor as um\n", "import ctrl\n",
                "import gdat2\n", "import ping1d\n"):
        body = sub_once(body, imp, "", imp.strip())
    body = sub_once(body,
                    "import imu_test          # AxisWindow: one implementation "
                    'of "has this moved?"\n', "", "imu_test import")
    # Library imports are hoisted into the prelude instead of left mid-file.
    for imp in ["import numpy as np\n", "import tkinter as tk\n",
                "from tkinter import ttk\n"] + \
               ["import %s\n" % m for m in PRELUDE_IMPORTS]:
        if body.count(imp) == 1:
            body = body.replace(imp, "")

    # A name defined by the GUI body that is also inlined above would silently
    # shadow the inlined one - the GUI body comes last. Catch it here.
    # Inlined modules share one flat namespace, so check them against EACH
    # OTHER as well as against the GUI body. ping1d and gdat2 both naturally
    # want Link, Sim, build, checksum and DEFAULT_PORT; ping1d's are prefixed
    # to avoid it, and this is what keeps that true if either file grows.
    inlined, seen = set(), {}
    for tag, src, names in (("udp_monitor", um_, um_names), ("ctrl", ct, ct_names),
                            ("gdat2", gd, gd_names), ("imu_test", it, it_names),
                            ("ping1d", p1, p1_names), ("witmotion", wm, wm_names)):
        got = top_level_names(src) & set(names)
        for n in got:
            if n in seen:
                raise SystemExit(
                    "make_gui_standalone: %r is inlined from both %s and %s. "
                    "They land in one namespace and the later one would "
                    "silently win. Rename it in one of them."
                    % (n, seen[n], tag))
            seen[n] = tag
        inlined |= got
    clash = inlined & top_level_names(body)
    if clash:
        raise SystemExit("make_gui_standalone: mixer_gui.py defines %s at "
                         "module level, which would shadow the inlined copy. "
                         "Rename one." % ", ".join(sorted(clash)))

    parts.append("\n# " + "-" * 62 + " mixer_gui.py body (verbatim) ---\n")
    parts.append(body.lstrip("\n"))
    text = "".join(parts)

    missing = undefined_globals(text)
    if missing:
        raise SystemExit(
            "make_gui_standalone: the generated file reads %s but never "
            "defines %s. Add %s to the extraction lists above."
            % (", ".join(sorted(missing)),
               "them" if len(missing) > 1 else "it",
               "them" if len(missing) > 1 else "it"))
    return text


def main():
    ap = argparse.ArgumentParser(
        description="Generate mixer_gui_standalone.py (no local-file imports)")
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if the generated file is missing or stale")
    a = ap.parse_args()

    text = build()
    if a.check:
        if not os.path.exists(OUT):
            print("STALE: %s does not exist" % os.path.basename(OUT))
            return 1
        with open(OUT, encoding="utf-8") as f:
            if f.read() != text:
                print("STALE: %s differs from what the sources generate - "
                      "re-run 'python make_gui_standalone.py'"
                      % os.path.basename(OUT))
                return 1
        print("up to date: %s" % os.path.basename(OUT))
        return 0

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("wrote %s  (%d lines, no local-file imports)"
          % (os.path.basename(OUT), text.count("\n") + 1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
