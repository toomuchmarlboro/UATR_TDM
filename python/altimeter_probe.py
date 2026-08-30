#!/usr/bin/env python3
"""
Find out what the altimeter actually speaks, before anything is written to
decode it.

    python altimeter_probe.py 192.168.3.112            # try the usual suspects
    python altimeter_probe.py 192.168.3.112 --port 9000
    python altimeter_probe.py 192.168.3.112 --udp --port 5000
    python altimeter_probe.py --buoy 2                 # -> 192.168.3.122
    python altimeter_probe.py --buoy 3 --role 1        # -> 192.168.3.131

Addressing is 192.168.3.1<buoy><role>, role 1 = telemetry, 2 = altimeter.

The altimeter used to arrive inside the aux_vcu's $GDAT2 sentence as
FIELDS[7:9] ("Altimeter dist" mm, "Altimeter conf" %). The manufacturer moved
it to its own address, so the GUI needs to read it directly, and that needs the
wire format.

USEFUL ON THE TELEMETRY ADDRESS TOO (--role 1). An embedded web server was once
found answering 8080 on what is now a buoy telemetry address and then sitting
silent - which is indistinguishable from a dead aux_vcu until you look at what
actually replied. If .1x1:8080 connects and streams nothing, sweep it.

WHY A PROBE AND NOT A GUESS
===========================
A decoder written against an assumed field map does not fail loudly. It frames,
it checksums, and it prints perfectly formatted values under the wrong
headings - which is the exact failure gdat2.py's own header argues about at
length, and the reason its telemetry tab carries a "live" column at all. So the
format gets read off the wire first.

WHAT IT REPORTS
    - whether the port is open at all, and how it refuses if not
    - whether the device streams on connect or waits to be asked
    - a hex + ASCII dump of the first bytes, so framing is visible
    - a verdict: NMEA-style ASCII, other line-based text, or binary
    - if it IS NMEA-style, the talker and field count, and whether gdat2's
      existing parser would accept it unchanged

Standard library only, except an optional gdat2 import for that last check.
"""

import argparse
import socket
import string
import sys
import time

# Ports worth trying when none is given. Serial-to-Ethernet bridges are the
# usual way a sonar altimeter gets onto a network, so their defaults dominate.
LIKELY = (
    (8080, "same as the aux_vcu on this network"),
    (4001, "Moxa NPort, serial bridge"),
    (10001, "Lantronix, serial bridge"),
    (23,   "raw telnet, common on cheap bridges"),
    (2101, "serial bridge"),
    (9000, "vendor default"),
    (5000, "vendor default"),
    (502,  "Modbus TCP"),
    (80,   "web config - not data, but proves the host is up"),
)

def buoy_ip(n, role):
    """192.168.3.1<buoy><role>. role 1 = telemetry, 2 = altimeter.

    Deferred to gdat2 when it is importable so there is one definition of the
    scheme, with a local fallback so this file still runs if copied out on its
    own - which is the whole point of a probe you hand to someone on a boat.
    """
    try:
        import gdat2
        return gdat2.buoy_ip(n, role)
    except ImportError:
        return "192.168.3.1%d%d" % (n, role)


def hexdump(b, width=16, limit=256):
    out = []
    b = b[:limit]
    for off in range(0, len(b), width):
        chunk = b[off:off + width]
        hx = " ".join("%02X" % c for c in chunk)
        asc = "".join(chr(c) if chr(c) in string.printable[:95] else "."
                      for c in chunk)
        out.append("  %04X  %-*s  |%s|" % (off, width * 3 - 1, hx, asc))
    if len(b) == limit:
        out.append("  ... truncated")
    return "\n".join(out)


def classify(b):
    """-> (verdict, detail). What kind of thing is this."""
    if not b:
        return "nothing", "connected but sent no data"
    printable = sum(1 for c in b if 32 <= c < 127 or c in (9, 10, 13))
    ratio = printable / float(len(b))
    if ratio < 0.85:
        return "binary", ("%.0f%% of bytes are non-printable - a packed struct "
                          "or a framed binary protocol, not text" % (100 * (1 - ratio)))
    text = b.decode("ascii", "replace")
    if "\n" not in text and "\r" not in text:
        return "text, unframed", ("printable but no CR/LF in %d bytes - either "
                                  "fixed-width records or a different "
                                  "delimiter" % len(b))
    lines = [ln for ln in text.replace("\r", "\n").split("\n") if ln.strip()]
    if lines and lines[0].lstrip().startswith("$"):
        return "NMEA-style ASCII", "%d line(s), '$' prefixed" % len(lines)
    return "line-based text", "%d line(s), no '$' prefix" % len(lines)


def nmea_detail(b):
    """Talker, field count, and whether gdat2.parse would take it."""
    text = b.decode("ascii", "replace").replace("\r", "\n")
    lines = [ln.strip() for ln in text.split("\n") if ln.strip().startswith("$")]
    if not lines:
        return
    # The first line may be a fragment - we joined mid-stream - so prefer a
    # middle one, which is whole by construction.
    ln = lines[len(lines) // 2] if len(lines) > 2 else lines[0]
    body = ln[1:].partition("*")[0]
    parts = body.split(",")
    print("    talker        %r" % parts[0])
    print("    fields        %d after the talker" % (len(parts) - 1))
    print("    sample        %s" % ln[:100])
    try:
        import gdat2
    except ImportError:
        return
    r = gdat2.parse(ln)
    if r["ok"]:
        print("    *** gdat2.parse ACCEPTS this unchanged ***")
        print("    Altimeter dist = %s mm, conf = %s %%"
              % (r["vals"][7], r["vals"][8]))
    else:
        print("    gdat2.parse    rejects it: %s" % r["err"])
        if parts[0] != gdat2.TALKER:
            print("    -> different talker (%r vs %r). If the field layout is"
                  % (parts[0], gdat2.TALKER))
            print("       otherwise the same, this is a small change.")
        # Checksum convention is the usual bring-up mismatch, so say whether
        # the sentence carries one at all rather than leaving it implied.
        print("    checksum      %s" % ("present, %s"
              % ("valid" if r["csum_ok"] else "MISMATCH")
              if r["csum_ok"] is not None else "absent"))


def try_tcp(host, port, secs, poke):
    print("\n--- TCP %s:%d" % (host, port))
    try:
        s = socket.create_connection((host, port), timeout=3.0)
    except socket.timeout:
        print("    timed out - filtered, or nothing listening")
        return False
    except OSError as e:
        print("    %s" % e)
        return False
    print("    connected")
    s.settimeout(secs)
    buf = b""
    t0 = time.time()
    try:
        while time.time() - t0 < secs:
            try:
                d = s.recv(4096)
            except socket.timeout:
                break
            if not d:
                print("    peer closed the connection")
                break
            buf += d
            if len(buf) > 4096:
                break
        if not buf and poke:
            # Some devices answer only when asked. A bare newline is the
            # least-committal thing to send and is what most line-oriented
            # firmwares treat as an empty command.
            print("    nothing in %.1fs - sending a bare newline" % secs)
            s.sendall(b"\r\n")
            try:
                buf = s.recv(4096)
            except socket.timeout:
                pass
    finally:
        try:
            s.close()
        except OSError:
            pass

    verdict, detail = classify(buf)
    print("    received      %d bytes in %.1fs" % (len(buf), time.time() - t0))
    print("    verdict       %s - %s" % (verdict, detail))
    if buf:
        print(hexdump(buf))
        if verdict == "NMEA-style ASCII":
            nmea_detail(buf)
    return bool(buf)


def try_udp(port, secs, bind):
    print("\n--- UDP, listening on %s:%d" % (bind or "0.0.0.0", port))
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind((bind, port))
    except OSError as e:
        print("    cannot bind: %s" % e)
        return False
    s.settimeout(secs)
    try:
        d, addr = s.recvfrom(65535)
    except socket.timeout:
        print("    nothing in %.1fs. If the device only sends when asked, or"
              % secs)
        print("    only to a registered listener, this will stay silent.")
        return False
    finally:
        s.close()
    print("    from          %s:%d" % addr)
    verdict, detail = classify(d)
    print("    received      %d bytes" % len(d))
    print("    verdict       %s - %s" % (verdict, detail))
    print(hexdump(d))
    if verdict == "NMEA-style ASCII":
        nmea_detail(d)
    return True


def main():
    ap = argparse.ArgumentParser(
        description="Identify the altimeter's wire format")
    ap.add_argument("host", nargs="?", help="altimeter address")
    ap.add_argument("--buoy", type=int, choices=(1, 2, 3, 4),
                    help="probe that buoy: 192.168.3.1<buoy><role>")
    ap.add_argument("--role", type=int, choices=(1, 2), default=2,
                    help="with --buoy: 1 = telemetry (aux_vcu), "
                         "2 = altimeter (default). The sweep works on either - "
                         "use 1 to find which port the aux_vcu streams on.")
    ap.add_argument("--port", type=int, help="one port instead of the scan")
    ap.add_argument("--udp", action="store_true",
                    help="listen for UDP rather than dialling TCP")
    ap.add_argument("--bind", default="", help="UDP bind address")
    ap.add_argument("--secs", type=float, default=3.0,
                    help="how long to wait for data")
    ap.add_argument("--no-poke", action="store_true",
                    help="do not send a newline to a silent device")
    a = ap.parse_args()

    if a.buoy:
        a.host = buoy_ip(a.buoy, a.role)
    if a.udp:
        if not a.port:
            ap.error("--udp needs --port")
        return 0 if try_udp(a.port, a.secs, a.bind) else 1
    if not a.host:
        ap.error("give a host, or --buoy N")

    print("Probing %s" % a.host)
    if a.port:
        return 0 if try_tcp(a.host, a.port, a.secs, not a.no_poke) else 1

    print("No --port given, trying the usual suspects. Ctrl-C to stop.")
    hit = False
    for port, why in LIKELY:
        print("\n[%d - %s]" % (port, why), end="")
        if try_tcp(a.host, port, min(a.secs, 2.0), not a.no_poke):
            hit = True
    if not hit:
        print("\nNothing streamed on any port tried.")
        print("  - is the altimeter powered and on this segment? try: ping %s"
              % a.host)
        print("  - it may be UDP: python altimeter_probe.py --udp --port N")
        print("  - it may need a command first; the vendor manual will say")
    return 0 if hit else 1


if __name__ == "__main__":
    sys.exit(main())
