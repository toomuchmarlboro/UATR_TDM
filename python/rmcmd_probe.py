#!/usr/bin/env python3
"""Find out what actually moves the actuator, with no GUI in the way.

    python rmcmd_probe.py --buoy 1                 # just watch ulRaw[9]
    python rmcmd_probe.py --buoy 1 --send 5        # send one code, watch
    python rmcmd_probe.py --buoy 1 --toggle        # send 5, then 1
    python rmcmd_probe.py --buoy 1 --sweep         # try every code 0-15
    python rmcmd_probe.py --connect 192.168.3.110 --send 5

WHY THIS EXISTS
===============
A button that does nothing has three possible causes and they need different
fixes:

    the bytes never left this host        - a transport or address fault
    the bytes left and nothing changed    - the code is wrong, or the
                                            firmware wants something else
    the bytes left and ulRaw[9] changed   - the command works and the
                                            MECHANISM did not move

This tells them apart, which neither GUI can: both of them report "sent"
truthfully and then have nothing further to say, because $RMCMD is never
acknowledged. Here the sentence is printed as it goes out and the digital I/O
field is printed as it comes back, so the three cases look different.

WHAT --sweep IS FOR
===================
The two codes this repo uses came from the manufacturer's own host, and their
labelling of them was already wrong once - what they called ENABLE_1 closes.
That is reason enough not to assume the SET of codes is right either. --sweep
sends each code in turn and reports which ones moved ulRaw[9], so the answer
comes off the hardware instead of out of a comment.

IT DRIVES REAL HARDWARE. --sweep will operate the actuator repeatedly. Do it
with the unit somewhere it can move freely, not with the jaws around
something.
"""

import argparse
import sys
import time

import gdat2


def watch(link, seconds, label=""):
    """Print ulRaw[9] whenever it changes. -> the values seen, in order."""
    seen = []
    deadline = time.time() + seconds
    last = object()
    while time.time() < deadline:
        snap = link.snapshot()
        record = snap["last"]
        if record is not None:
            raw = record["raw"][gdat2.I_DIO]
            if raw != last:
                last = raw
                seen.append(raw)
                print("    %-8s dio = %s  (%s)"
                      % (label, "-" if raw is None else "0x%02X" % raw,
                         gdat2.dio_text(raw)))
        time.sleep(0.05)
    return seen


def require_link(link, seconds=6.0):
    """Wait for the first decoded sentence, or explain what went wrong."""
    deadline = time.time() + seconds
    while time.time() < deadline:
        snap = link.snapshot()
        if snap["good"]:
            print("connected to %s   %.0f sentence/s"
                  % (snap["peer"], snap["rate"]))
            return True
        time.sleep(0.1)
    snap = link.snapshot()
    print("NO TELEMETRY: state %r, %d lines seen, %d checksum errors."
          % (snap["state"], snap["lines"], snap["csum_err"]))
    print("Nothing below would mean anything without a link, so stopping here.")
    return False


def send(link, code, settle):
    """Send one code and report what the actuator did about it."""
    sentence = gdat2.rmcmd(code)
    before = link.snapshot()["last"]
    before_dio = None if before is None else before["raw"][gdat2.I_DIO]

    ok, detail = link.send(sentence)
    print("  -> %-14s %s"
          % (sentence.strip(), "sent" if ok else "NOT SENT: %s" % detail))
    if not ok:
        # The bytes never left. Nothing about the actuator is being tested.
        return None

    seen = watch(link, settle, label="code %d" % code)
    after = link.snapshot()["last"]
    after_dio = None if after is None else after["raw"][gdat2.I_DIO]
    moved = any(v != before_dio for v in seen) or after_dio != before_dio
    print("     %s  %s -> %s"
          % ("CHANGED" if moved else "no change",
             "-" if before_dio is None else "0x%02X" % before_dio,
             "-" if after_dio is None else "0x%02X" % after_dio))
    return moved


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    target = ap.add_mutually_exclusive_group(required=True)
    target.add_argument("--buoy", type=int, choices=(1, 2, 3, 4),
                        help="dial that buoy's aux_vcu")
    target.add_argument("--connect", metavar="HOST",
                        help="dial this address instead")
    action = ap.add_mutually_exclusive_group()
    action.add_argument("--send", type=int, metavar="CODE",
                        help="send one $RMCMD code")
    action.add_argument("--toggle", action="store_true",
                        help="send OPEN (%d) then CLOSE (%d)"
                             % (gdat2.RMCMD_OPEN, gdat2.RMCMD_CLOSE))
    action.add_argument("--sweep", action="store_true",
                        help="try every code in --range, reporting which move "
                             "ulRaw[9]. DRIVES THE ACTUATOR REPEATEDLY.")
    ap.add_argument("--range", default="0-15", metavar="LO-HI",
                    help="codes --sweep tries (default 0-15)")
    ap.add_argument("--port", type=int, default=gdat2.DEFAULT_PORT)
    ap.add_argument("--settle", type=float, default=3.0, metavar="S",
                    help="seconds to watch after each command (default 3)")
    a = ap.parse_args()

    host = a.connect or gdat2.buoy_ip(a.buoy, gdat2.ROLE_GDAT2)
    print("aux_vcu %s:%d" % (host, a.port))
    print("OPEN is code %d, CLOSE is code %d - the opposite of the vendor's "
          "own labels." % (gdat2.RMCMD_OPEN, gdat2.RMCMD_CLOSE))
    print()

    link = gdat2.Link("client", host, a.port)
    link.start()
    try:
        if not require_link(link):
            return 1

        if a.sweep:
            try:
                lo, _, hi = a.range.partition("-")
                codes = range(int(lo), int(hi) + 1)
            except ValueError:
                ap.error("--range wants LO-HI, e.g. 0-15")
            print("\nsweeping codes %s - this drives the actuator\n" % a.range)
            moved = []
            for code in codes:
                print("code %d:" % code)
                if send(link, code, a.settle):
                    moved.append(code)
                print()
            print("=" * 60)
            if moved:
                print("codes that moved ulRaw[9]: %s"
                      % ", ".join(str(c) for c in moved))
            else:
                print("NO CODE IN %s MOVED ulRaw[9]." % a.range)
                print("The link is up and the sentences are going out, so this")
                print("is the firmware declining all of them - a different")
                print("talker, a different framing, or a control path that is")
                print("not $RMCMD at all. Capture what the vendor's own host")
                print("puts on the wire and compare it byte for byte.")
            return 0

        if a.send is not None:
            print("\nbaseline:")
            watch(link, 2.0, label="idle")
            print("\nsending:")
            send(link, a.send, a.settle)
            return 0

        if a.toggle:
            print("\nbaseline:")
            watch(link, 2.0, label="idle")
            for code in (gdat2.RMCMD_OPEN, gdat2.RMCMD_CLOSE):
                print("\n%s:" % ("OPEN" if code == gdat2.RMCMD_OPEN else "CLOSE"))
                send(link, code, a.settle)
            return 0

        print("\nwatching ulRaw[9] - ctrl-C to stop. Operate the actuator by")
        print("any other means and this will show whether the field follows.")
        while True:
            watch(link, 5.0, label="watch")
    except KeyboardInterrupt:
        pass
    finally:
        link.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
