#!/usr/bin/env python3
"""
imu_standalone.py - IMU/AHRS check over the aux_vcu $GDAT2 link, in ONE file.

Standard library only. No project imports, no third-party packages, no config.
Copy this single file anywhere - a deployment laptop, a colleague's machine, a
buoy-side box - and run it:

    python imu_standalone.py                       # active unit, 192.168.3.131
    python imu_standalone.py --selftest            # no hardware needed
    python imu_standalone.py --connect 10.0.0.7:8080
    python imu_standalone.py --expect moving       # warn if nothing changes
    python imu_standalone.py --raw                 # dump bytes, decode nothing
    python imu_standalone.py --listen 8080         # wait for the unit to dial in

READ THIS BEFORE TRUSTING IT
============================
This file is a SNAPSHOT, taken 2026-08-19, of gdat2.py + imu_test.py from the
UATR_TDM repo. Those two remain authoritative. Being standalone means it carries
its own copy of the field map - and a copied field map is the single defect this
tool exists to detect, because when the firmware adds a field, every value after
it slides one place and the copy keeps printing believable numbers under the
wrong headings.

So: if the aux_vcu firmware changes, re-snapshot this file. Do not edit the map
here and assume the repo agrees. `--selftest` checks the map against two real
captured sentences, which will catch a shift that moves a value out of range,
but it cannot catch a shift that lands one plausible number on another.


WHAT IT CHECKS
==============
That the link works is the easy half, and `--raw` covers it. The hard half is
that a telemetry field can frame, checksum, decode and print a perfectly
plausible value while carrying nothing at all:

  ZERO      decodes fine, reads 0.0 forever - the firmware never filled it.
            One frame of that is indistinguishable from level-and-north.

  CONSTANT  the same bits every frame. This is NOT by itself a fault. Buoy 3
            quantises attitude to 0.1 deg, so a stationary unit repeats one
            value indefinitely and is perfectly healthy. A still quantised
            sensor and a dead field are BIT-IDENTICAL - nothing in the stream
            separates them, so this reports UNPROVEN and asks you to move the
            unit rather than guessing. One observed change proves the axis
            alive for the rest of the session.

  SHIFTED   the field map moved. Caught only by plausible ranges, since the
            attitude itself stays believable - the giveaway is a leak sensor
            reading 18 V and an altimeter confidence of 4696 %.

An earlier version called CONSTANT a fault outright, on the reasoning that a
live AHRS always dithers in its low bits. That is true of a raw fusion output
and false of a quantised one, and it declared working hardware broken. The
distinction is preserved here deliberately.


PROTOCOL, as confirmed against buoy 3 on 2026-08-19
===================================================
    $GDAT2,<ulRaw[0]>,...,<ulRaw[9]>,<seq>,<cnt>*HH<CR><LF>   ~50 Hz, TCP

  * ulRaw[0..9] are hex, no 0x prefix. The spec says always 8 digits "even when
    carrying integer data"; the real device sends a bare "0", so tokens are
    left-padded rather than required to be 8 long. A strict 8-digit parser
    rejects every sentence this device has ever sent.
  * an f32 field is that u32 reinterpreted as IEEE-754. 0x42280000 = 42.0.
  * seq and cnt are DECIMAL ASCII, not hex. Reading them as hex silently breaks
    loss detection. seq is stuck at 0 on this firmware - use cnt, which wraps
    at 256 and works.
  * checksum: XOR of every byte between '$' and '*', both excluded.
  * the aux_vcu is the TCP SERVER. It streams on connect without being asked,
    so a socket that opens and stays quiet has not given you telemetry - but
    do not conclude "wrong device" from that alone. An embedded web server was
    once found answering 8080 on what is now a buoy telemetry address and then
    waiting, which is what a config page does with no HTTP request. Same
    symptom, different cause: it may be the wrong PORT on the right host.
"""

import argparse
import collections
import socket
import struct
import sys
import time

TALKER       = "GDAT2"
N_RAW        = 10
DEFAULT_PORT = 8080

# 192.168.3.1<buoy><role>: role 1 = telemetry, role 2 = altimeter.
# Re-addressed by the manufacturer 2026-08-29 (.1x0 -> .1x1) when the altimeter
# was moved out to its own address. Older captures will show .110/.120/.130/.140.
# This file is deliberately standalone, so this is a hand-kept copy of
# gdat2.BUOYS - change one, change the other.
BUOYS = (("buoy 1", "192.168.3.111"),
         ("buoy 2", "192.168.3.121"),
         ("buoy 3", "192.168.3.131"),
         ("buoy 4", "192.168.3.141"))
ACTIVE_BUOY  = 3                      # the unit in service
DEFAULT_HOST = BUOYS[ACTIVE_BUOY - 1][1]

# name, unit, kind
FIELDS = (
    ("Leak sensor",     "V",    "f32"),
    ("Voltage monitor", "V",    "f32"),
    ("Depth",           "m",    "f32"),
    ("Depth temp",      "degC", "f32"),
    ("AHRS Roll",       "deg",  "f32"),
    ("AHRS Pitch",      "deg",  "f32"),
    ("AHRS Yaw",        "deg",  "f32"),
    ("Altimeter dist",  "mm",   "u32"),
    ("Altimeter conf",  "%",    "u32"),
    ("Digital I/O",     "",     "bits"),
)

I_LEAK, I_VBUS, I_DEPTH, I_DTEMP, I_ROLL, I_PITCH, I_YAW, \
    I_ALT_MM, I_ALT_PCT, I_DIO = range(N_RAW)
AHRS_IDX = (I_ROLL, I_PITCH, I_YAW)

# Sanity bounds, not calibration. A value outside these is far more likely to
# mean the field map shifted - the number is reasonable for some OTHER quantity
# - than that the sensor read it. Yaw admits both 0..360 and +/-180 conventions,
# since nothing on hand rules either out.
PLAUSIBLE = (
    (0.0,     5.0),       # leak, V
    (0.0,    60.0),       # bus, V
    (-2.0,  500.0),       # depth, m
    (-5.0,   50.0),       # depth temp, degC
    (-180.0, 180.0),      # roll
    (-90.0,   90.0),      # pitch
    (-180.0, 360.0),      # yaw
    (0.0, 100000.0),      # altimeter, mm
    (0.0,    100.0),      # confidence, %
    (0.0,      3.0),      # digital I/O, bits 0 and 1 only
)
assert len(PLAUSIBLE) == len(FIELDS) == N_RAW, "PLAUSIBLE must track FIELDS"

DIO_OPEN, DIO_CLOSE = 0x01, 0x02
DEFAULT_WINDOW_S = 3.0
STILL_MAX, MOVING_MIN = 5.0, 0.20
_HEX = set("0123456789abcdefABCDEF")


# ------------------------------------------------------------------ decode ---
def checksum(body):
    c = 0
    for ch in body.encode("ascii", "replace"):
        c ^= ch
    return c


def bits_f32(v):
    return struct.unpack("<f", struct.pack("<I", int(v) & 0xFFFFFFFF))[0]


def f32_bits(x):
    return struct.unpack("<I", struct.pack("<f", float(x)))[0]


def build(raw, seq=0, cnt=0):
    """Encode 10 u32s into a sentence. Used by --selftest and --sim."""
    body = "%s,%s,%d,%d" % (TALKER, ",".join("%08X" % (int(v) & 0xFFFFFFFF)
                                             for v in raw), seq, cnt & 0xFF)
    return "$%s*%02X\r\n" % (body, checksum(body))


def decode_field(tok, kind):
    """-> (raw_u32 or None, value or None). Hex, left-padded, never sniffed.

    No "does it look decimal" heuristic: "42280000" as decimal is 42,280,000,
    whose bits spell 1.96e-37, and hex digits include E so "3E000000" (0.125)
    would become a plausible, wrong 3.0.
    """
    tok = tok.strip()
    if tok[:2].lower() == "0x":
        tok = tok[2:]
    if not tok or len(tok) > 8 or any(c not in _HEX for c in tok):
        return None, None
    raw = int(tok, 16)
    if kind == "f32":
        v = bits_f32(raw)
        if v != v or v in (float("inf"), float("-inf")):    # NaN / inf
            return raw, None
        return raw, v
    return raw, float(raw)


def _int10(tok):
    """seq/cnt are decimal. Base 10 explicitly - base 0 rejects "08"."""
    try:
        return int(tok.strip(), 10)
    except (ValueError, AttributeError):
        return None


def parse(line):
    """Decode one sentence. Returns a dict always; never raises."""
    out = {"ok": False, "err": None, "csum_ok": None, "raw": [None] * N_RAW,
           "vals": [None] * N_RAW, "wire": [""] * N_RAW,
           "seq": None, "cnt": None, "line": line, "t": time.time()}
    s = line.strip()
    if not s:
        out["err"] = "empty"
        return out
    if not s.startswith("$"):
        out["err"] = "no '$'"
        return out
    s = s[1:]

    if "*" in s:
        body, _, tail = s.partition("*")
        hh = tail[:2]
        try:
            out["csum_ok"] = (int(hh, 16) == checksum(body))
        except ValueError:
            out["csum_ok"] = False
        if not out["csum_ok"]:
            out["err"] = "checksum (got %s, want %02X)" % (hh, checksum(body))
            # Fall through and decode anyway: during bring-up it is usually the
            # checksum CONVENTION that differs, not the data, and discarding
            # the sentence hides the evidence for that.
    else:
        body = s

    parts = body.split(",")
    if parts[0] != TALKER:
        out["err"] = "talker %r, want %r" % (parts[0], TALKER)
        return out
    nums = parts[1:]
    if len(nums) < N_RAW:
        out["err"] = "%d fields, need at least %d" % (len(nums), N_RAW)
        return out

    for i in range(N_RAW):
        out["wire"][i] = nums[i].strip()
        out["raw"][i], out["vals"][i] = decode_field(nums[i], FIELDS[i][2])
    if any(r is None for r in out["raw"]) and out["err"] is None:
        bad = [i for i, r in enumerate(out["raw"]) if r is None]
        out["err"] = "field %s not hex" % ",".join(str(i) for i in bad)

    extra = nums[N_RAW:]
    if len(extra) >= 2:
        out["seq"], out["cnt"] = _int10(extra[0]), _int10(extra[1])
    elif len(extra) == 1:
        out["cnt"] = _int10(extra[0])

    out["ok"] = out["err"] is None
    return out


def implausible(vals):
    """-> [(index, value, lo, hi)] for each field outside PLAUSIBLE."""
    out = []
    for i, v in enumerate(vals):
        if v is None:
            continue
        lo, hi = PLAUSIBLE[i]
        if not (lo <= v <= hi):
            out.append((i, v, lo, hi))
    return out


def dio_text(raw):
    if raw is None:
        return "-"
    o, c = bool(int(raw) & DIO_OPEN), bool(int(raw) & DIO_CLOSE)
    if o and c:
        return "OPEN+CLOSE (invalid)"
    return "OPEN" if o else "CLOSE" if c else "idle"


# ------------------------------------------------------------------ motion ---
def wrapped_span(vals):
    """Peak-to-peak of an angle series, honouring the 360 wrap.

    Yaw crossing north reads 359.5 then 0.5; a plain max-minus-min calls that a
    359 deg swing and inverts every verdict at the heading a buoy most likely
    sits at. Correct while the true step between frames is under 180 deg, i.e.
    9000 deg/s at 20 ms - past any real vehicle and past the gyro's range.
    """
    if not vals:
        return 0.0
    acc, out = float(vals[0]), [float(vals[0])]
    for a, b in zip(vals, vals[1:]):
        acc += (float(b) - float(a) + 180.0) % 360.0 - 180.0
        out.append(acc)
    return max(out) - min(out)


class AxisWindow(object):
    """Two timescales, and the difference between them is the whole point.

    the WINDOW  answers "is it moving right now"
    the SESSION answers "has it EVER moved", which is what proves it alive
    """

    def __init__(self, name, window_s=DEFAULT_WINDOW_S):
        self.name, self.window_s = name, window_s
        self.samples = collections.deque()      # (t, raw_u32, value)
        self.session_raw = set()
        self.session_vals = set()
        self.changes = 0
        self._prev_raw = None

    def feed(self, t, raw, val):
        self.samples.append((t, raw, val))
        cut = t - self.window_s
        while self.samples and self.samples[0][0] < cut:
            self.samples.popleft()
        if self._prev_raw is not None and raw != self._prev_raw:
            self.changes += 1
        self._prev_raw = raw
        if len(self.session_raw) < 4096:        # bounded: 50 Hz all day
            self.session_raw.add(raw)
            if val is not None:
                self.session_vals.add(round(float(val), 6))

    @property
    def n(self):
        return len(self.samples)

    @property
    def last(self):
        return self.samples[-1][2] if self.samples else None

    @property
    def distinct_raw(self):
        return len(set(s[1] for s in self.samples if s[1] is not None))

    @property
    def all_zero(self):
        return bool(self.samples) and all(s[1] == 0 for s in self.samples)

    @property
    def ever_moved(self):
        return self.changes > 0

    @property
    def span(self):
        return wrapped_span([s[2] for s in self.samples if s[2] is not None])

    def resolution(self):
        """Apparent quantisation step, derived from the data, else None.

        Derived rather than assumed: a firmware sending full float precision
        reports None here and its dither stays meaningful, so this cannot
        excuse a genuinely stuck field.
        """
        vs = sorted(self.session_vals)
        if len(vs) < 2:
            return None
        for q in (1.0, 0.5, 0.25, 0.1, 0.05, 0.01):
            if all(abs(v / q - round(v / q)) < 1e-4 for v in vs):
                return q
        return None

    def drift_deg_per_min(self):
        if self.n < 2:
            return 0.0
        (t0, _a, v0), (t1, _b, v1) = self.samples[0], self.samples[-1]
        if v0 is None or v1 is None or t1 <= t0:
            return 0.0
        d = (float(v1) - float(v0) + 180.0) % 360.0 - 180.0
        return d / (t1 - t0) * 60.0

    def verdict(self, expect=None, min_samples=10):
        """-> (tag, text); tag is 'ok' | 'warn' | 'unproven' | 'wait'."""
        if self.n < min_samples:
            return "wait", "%d samples, need %d" % (self.n, min_samples)
        if self.all_zero and not self.ever_moved:
            return "warn", ("ZERO for %.1fs - firmware is not filling this "
                            "field" % self.window_s)

        if self.distinct_raw == 1:
            res = self.resolution()
            step = (" at %g deg resolution" % res) if res else ""
            if self.ever_moved:
                if expect == "moving":
                    return "warn", ("steady%s while motion was expected "
                                    "(moved %d times earlier)"
                                    % (step, self.changes))
                return "ok", ("steady%s - live, moved %d times this session"
                              % (step, self.changes))
            if expect == "moving":
                return "warn", ("constant%s through expected motion - suspect "
                                "it is not being updated" % step)
            return "unproven", ("constant%s - stationary and not-updated look "
                                "identical here; MOVE the unit to tell them "
                                "apart" % step)

        span = self.span
        if expect == "still" and span > STILL_MAX:
            return "warn", ("span %.2f deg over %.1fs - expected still, "
                            "something is moving it" % (span, self.window_s))
        if expect == "moving" and span < MOVING_MIN:
            return "warn", ("span %.3f deg over %.1fs - expected motion, this "
                            "is dither only" % (span, self.window_s))
        return "ok", "live, span %.3f deg over %.1fs" % (span, self.window_s)


# -------------------------------------------------------------------- link ---
class Link(object):
    """Blocking line-buffered TCP reader. Reconnects; never raises out.

    TCP is a byte stream, not a message stream: at 20 ms two sentences routinely
    land in one recv() and a third splits across two, so sentences are recovered
    by buffering and splitting on newlines. Treating each recv() as one message
    corrupts roughly every other reading.
    """

    def __init__(self, mode="client", host=DEFAULT_HOST, port=DEFAULT_PORT):
        self.mode, self.host, self.port = mode, host, port
        self.sock = self.srv = None
        self.state = "idle"
        self.peer = ""
        self.good = self.csum_err = self.parse_err = self.lost = self.lines = 0
        self.cnt_prev = None
        self.rate = 0.0
        self._rt0, self._rn = time.time(), 0
        self._buf = b""

    def close(self):
        for s in (self.sock, self.srv):
            try:
                if s:
                    s.close()
            except OSError:
                pass
        self.sock = self.srv = None

    def _connect(self):
        if self.mode == "server":
            self.srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.srv.bind(("0.0.0.0", self.port))
            self.srv.listen(1)
            self.srv.settimeout(0.5)
            self.state = "listening on :%d" % self.port
            while True:
                try:
                    self.sock, addr = self.srv.accept()
                    break
                except socket.timeout:
                    return False
            self.peer = "%s:%d" % addr
            self.srv.close()
            self.srv = None
        else:
            self.state = "connecting to %s:%d" % (self.host, self.port)
            self.sock = socket.create_connection((self.host, self.port),
                                                 timeout=3.0)
            self.peer = "%s:%d" % (self.host, self.port)
        self.state = "connected"
        self.sock.settimeout(0.5)
        self._buf = b""
        return True

    def poll(self):
        """-> list of parsed dicts. Non-blocking-ish: returns within ~0.5 s."""
        if self.sock is None:
            try:
                if not self._connect():
                    return []
            except OSError as e:
                self.state = "not reachable (%s)" % e
                self.close()
                time.sleep(0.5)
                return []
        try:
            d = self.sock.recv(4096)
        except socket.timeout:
            return []
        except OSError as e:
            self.state = "lost (%s)" % e
            self.close()
            return []
        if not d:
            self.state = "peer closed"
            self.close()
            return []

        self._buf += d
        if len(self._buf) > 65536:           # a peer with no newline at all
            self._buf = self._buf[-4096:]
        out = []
        while b"\n" in self._buf:
            ln, _, self._buf = self._buf.partition(b"\n")
            text = ln.decode("ascii", "replace").strip("\r")
            if not text.strip():
                continue
            r = parse(text)
            self.lines += 1
            self._rn += 1
            now = time.time()
            if now - self._rt0 >= 0.5:
                self.rate = self._rn / (now - self._rt0)
                self._rt0, self._rn = now, 0
            # Disjoint buckets. A corrupt sentence usually fails BOTH the
            # checksum and the field parse; counting it twice makes one fault
            # read as two independent problems.
            if r["csum_ok"] is False:
                self.csum_err += 1
            elif r["ok"]:
                self.good += 1
            else:
                self.parse_err += 1
            c = r["cnt"]
            if c is not None:
                if self.cnt_prev is not None:
                    step = (c - self.cnt_prev) & 0xFF
                    if 1 < step < 64:            # a big jump is a restart
                        self.lost += step - 1
                self.cnt_prev = c
            out.append(r)
        return out


# ---------------------------------------------------------------- printing ---
_MARK = {"ok": "  ok  ", "warn": " WARN ", "wait": " ...  ",
         "unproven": "  ??  "}


def _report(axes, link, expect, t0, shifted, skipped, good):
    if good == 0:
        # Categorise; do not echo the state string. A client alternates
        # "connecting"/"not reachable" every retry, so keying the message on
        # the state reprints the whole hint each cycle for one situation.
        if link.state == "connected":
            cat, hint = "silent", (
                "  !! connected, but no sentence has decoded. A GDAT2 source "
                "streams on connect\n     without being asked - check WHAT "
                "answered (--raw dumps the bytes).")
        elif link.mode == "server":
            cat, hint = "nobody", "  !! listening - nothing has dialled in yet."
        else:
            cat, hint = "unreachable", (
                "  !! not reachable. Check the unit is powered and on this "
                "subnet. If\n     'ping %s' fails at the ARP level it is not "
                "on this segment at\n     all, and no amount of retrying will "
                "find it." % link.host)
        if cat != getattr(_report, "_cat", None):
            _report._cat = cat
            print("\n[%6.1fs] %s" % (time.time() - t0, link.state))
            print(hint)
        else:
            sys.stdout.write(".")
            sys.stdout.flush()
        return
    _report._cat = None

    print("\n[%6.1fs] %s %s   %.0f sentences/s   good %d  csum %d  bad %d  "
          "lost %d" % (time.time() - t0, link.state, link.peer, link.rate,
                       link.good, link.csum_err, link.parse_err, link.lost))
    for a in axes:
        tag, text = a.verdict(expect)
        val = "%8.2f deg" % a.last if a.last is not None else "       -  "
        print("  %-6s %-12s %s  %s" % (_MARK.get(tag, "  ?   "),
                                       a.name.replace("AHRS ", ""), val, text))
    d = axes[2].drift_deg_per_min()
    if abs(d) > 0.01:
        print("         yaw drift %+.2f deg/min%s"
              % (d, "  (stationary: this is gyro bias)"
                 if expect == "still" else ""))
    if shifted:
        print("  !! fields outside plausible range - suspect a SHIFTED field "
              "map, not a broken sensor:")
        for i, n in sorted(shifted.items()):
            lo, hi = PLAUSIBLE[i]
            print("       ulRaw[%d] %-16s %d frames outside %g..%g %s"
                  % (i, FIELDS[i][0], n, lo, hi, FIELDS[i][1]))
    if skipped:
        print("  (%d frames not fed to the window: checksum or field error)"
              % skipped)


# --------------------------------------------------------------------- raw ---
def run_raw(host, port):
    """Dump bytes, decode nothing. Right first step for unknown framing."""
    print("raw dump from %s:%d - ctrl-C to stop" % (host, port))
    sock = socket.create_connection((host, port), timeout=5.0)
    sock.settimeout(1.0)
    n = 0
    try:
        while True:
            try:
                d = sock.recv(4096)
            except socket.timeout:
                print("  ... no data for 1 s")
                continue
            if not d:
                print("peer closed after %d bytes" % n)
                return 0
            n += len(d)
            sys.stdout.write(d.decode("ascii", "replace"))
            sys.stdout.flush()
    except KeyboardInterrupt:
        print("\nstopped after %d bytes" % n)
        return 0
    finally:
        sock.close()


# --------------------------------------------------------------------- sim ---
def run_sim(port):
    """Fake aux_vcu so this file can be proven with no hardware present.

    Quantises attitude to 0.1 deg like the real unit, and holds it constant -
    so the UNPROVEN path, which is the one that was got wrong on real hardware,
    is what a bare run exercises.
    """
    import math
    import random
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", port))
    srv.listen(2)
    print("simulated aux_vcu on 0.0.0.0:%d - ctrl-C to stop" % port)
    t = 0.0
    seq = cnt = 0
    try:
        while True:
            c, _ = srv.accept()
            try:
                while True:
                    t += 0.02
                    moving = (int(t) // 5) % 2 == 1      # still, then moving
                    q = lambda x: round(x, 1)            # 0.1 deg quantisation
                    raw = [f32_bits(1.50 + 0.01 * random.random()),
                           f32_bits(0.0), f32_bits(0.0), f32_bits(0.0),
                           f32_bits(q(1.2 + (2.0 * math.sin(t) if moving else 0))),
                           f32_bits(q(3.2 + (1.0 * math.cos(t) if moving else 0))),
                           f32_bits(q(152.3 + (t * 5 % 30 if moving else 0))),
                           0, 0, 0]
                    c.sendall(build(raw, seq, cnt).encode("ascii"))
                    seq = (seq + 1) & 0xFFFFFFFF
                    cnt = (cnt + 1) & 0xFF
                    time.sleep(0.02)
            except OSError:
                pass
            finally:
                c.close()
    except KeyboardInterrupt:
        srv.close()
        return 0


# ---------------------------------------------------------------- selftest ---
def _selftest():
    # 1. The makers' documented capture. Values are from docs/GDAT2_TELEMETRY.md
    cap = ("$GDAT2,3CC85BA9,41C0DBB2,41545BB3,419494F9,40AAE6D3,402149B0,"
           "41D23D71,00001258,0000005F,00000001,145,149*52")
    r = parse(cap)
    assert r["csum_ok"] is True and r["ok"], (r["err"], r["csum_ok"])
    for i, want in zip(AHRS_IDX, (5.341, 2.520, 26.280)):
        assert abs(r["vals"][i] - want) < 5e-4, (i, r["vals"][i], want)
    assert (r["seq"], r["cnt"]) == (145, 149), "seq/cnt are decimal, not hex"
    assert not implausible(r["vals"])

    # 2. A real sentence off buoy 3, 2026-08-19. Covers two things the makers'
    #    example does not: fields that are NOT 8 hex digits (a bare "0"), and
    #    seq stuck at 0. A stricter parser rejects every sentence this device
    #    has ever sent.
    real = "$GDAT2,3FBFF666,0,0,0,3F8CCCCD,40466666,4331B333,0,0,0,0,222*5C"
    rr = parse(real)
    assert rr["csum_ok"] is True and rr["ok"], (rr["err"], rr["csum_ok"])
    assert rr["seq"] == 0 and rr["cnt"] == 222, (rr["seq"], rr["cnt"])
    assert abs(rr["vals"][I_LEAK] - 1.4997) < 1e-3, rr["vals"][I_LEAK]
    for i, want in zip(AHRS_IDX, (1.1, 3.1, 177.7)):
        assert abs(rr["vals"][i] - want) < 1e-4, (i, rr["vals"][i], want)
    assert not implausible(rr["vals"])

    # 3. Round trip, and the encoder's own worked example.
    assert "%08X" % f32_bits(42.0) == "42280000"
    assert abs(bits_f32(0x42280000) - 42.0) < 1e-6
    rt = parse(build([f32_bits(1.5)] * 7 + [10, 20, 1], 7, 9))
    assert rt["ok"] and rt["seq"] == 7 and rt["cnt"] == 9, rt

    # 4. A shifted map is caught by the bounds.
    sh = list(r["vals"])
    sh[I_PITCH] = 130.0
    assert [i for i, _v, _lo, _hi in implausible(sh)] == [I_PITCH]

    # 5. Wrap.
    assert abs(wrapped_span([350.0, 355.0, 0.0, 5.0, 10.0]) - 20.0) < 1e-6
    assert abs(wrapped_span([10.0, 12.0, 11.0]) - 2.0) < 1e-6
    assert wrapped_span([]) == 0.0 and wrapped_span([7.0]) == 0.0

    # 6. Verdicts. A constant axis is UNPROVEN, not a fault - the regression
    #    for the wrong call made on real hardware.
    w = AxisWindow("t", window_s=10.0)
    assert w.verdict()[0] == "wait"
    for k in range(20):
        w.feed(1000.0 + k * 0.02, f32_bits(12.5), 12.5)
    assert w.verdict()[0] == "unproven" and "MOVE" in w.verdict()[1], w.verdict()
    assert w.verdict("moving")[0] == "warn", w.verdict("moving")
    for k in range(20, 60):
        w.feed(1000.0 + k * 0.02, f32_bits(12.6), 12.6)
    assert w.ever_moved and w.changes == 1, (w.ever_moved, w.changes)
    assert w.verdict()[0] == "ok" and "live" in w.verdict()[1], w.verdict()
    assert w.resolution() == 0.1, w.resolution()

    # Full float precision must NOT read as quantised, or this would excuse a
    # genuinely stuck field on a device that does dither.
    fw = AxisWindow("t", window_s=10.0)
    for k in range(20):
        v = 12.5 + 0.00137 * k
        fw.feed(1000.0 + k * 0.02, f32_bits(v), v)
    assert fw.resolution() is None, fw.resolution()

    z = AxisWindow("t", window_s=10.0)
    for k in range(20):
        z.feed(1000.0 + k * 0.02, 0, 0.0)
    assert "ZERO" in z.verdict()[1], z.verdict()

    m = AxisWindow("t", window_s=10.0)
    for k in range(20):
        v = 12.5 + 0.9 * k
        m.feed(1000.0 + k * 0.02, f32_bits(v), v)
    assert m.verdict("moving")[0] == "ok" and m.verdict("still")[0] == "warn"

    e = AxisWindow("t", window_s=1.0)          # the window really is a window
    e.feed(1000.0, f32_bits(1.0), 1.0)
    e.feed(1002.0, f32_bits(2.0), 2.0)
    assert e.n == 1, e.n

    print("imu_standalone selftest OK  (documented capture %.3f/%.3f/%.3f, "
          "buoy 3 capture %.1f/%.1f/%.1f)"
          % tuple([r["vals"][i] for i in AHRS_IDX]
                  + [rr["vals"][i] for i in AHRS_IDX]))
    return 0


# -------------------------------------------------------------------- main ---
def main():
    ap = argparse.ArgumentParser(
        description="IMU/AHRS check over the aux_vcu $GDAT2 link (standalone)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--buoy", type=int, choices=(1, 2, 3, 4),
                   help="dial that buoy (%s)"
                        % ", ".join("%d=%s" % (i + 1, ip)
                                    for i, (_n, ip) in enumerate(BUOYS)))
    g.add_argument("--connect", metavar="HOST[:PORT]")
    g.add_argument("--listen", type=int, metavar="PORT")
    g.add_argument("--sim", type=int, nargs="?", const=DEFAULT_PORT,
                   metavar="PORT", help="run a fake aux_vcu, no hardware")
    g.add_argument("--selftest", action="store_true")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--raw", action="store_true",
                    help="dump bytes, decode nothing")
    ap.add_argument("--expect", choices=("still", "moving"), default=None)
    ap.add_argument("--window", type=float, default=DEFAULT_WINDOW_S,
                    metavar="S")
    ap.add_argument("--n-frames", type=int, default=None, metavar="N")
    a = ap.parse_args()

    if a.selftest:
        return _selftest()
    if a.sim is not None:
        return run_sim(a.sim)

    if a.listen:
        mode, host, port = "server", "0.0.0.0", a.listen
    elif a.buoy:
        mode, host, port = "client", BUOYS[a.buoy - 1][1], a.port
    elif a.connect:
        h, _, p = a.connect.partition(":")
        mode, host, port = "client", h, int(p) if p else a.port
    else:
        mode, host, port = "client", DEFAULT_HOST, a.port
        print("no target given - using the active unit, buoy %d (%s)"
              % (ACTIVE_BUOY, DEFAULT_HOST))

    if a.raw:
        if mode != "client":
            print("--raw dials out; use --connect or --buoy with it")
            return 1
        return run_raw(host, port)

    link = Link(mode, host, port)
    axes = [AxisWindow(FIELDS[i][0], a.window) for i in AHRS_IDX]
    shifted = collections.Counter()
    skipped = 0
    good = 0
    t0 = last_print = time.time()

    print("IMU/AHRS via $GDAT2 %s %s:%d   window %.1fs   expect %s"
          % ("<-" if mode == "server" else "->", host, port, a.window,
             a.expect or "(nothing)"))
    try:
        while True:
            for r in link.poll():
                # A bad-checksum sentence is not fed to the window: one
                # corrupted float is a spike that reads as motion, and telling
                # motion from stillness is this tool's entire job.
                if not r["ok"] or any(r["vals"][i] is None for i in AHRS_IDX):
                    skipped += 1
                    continue
                good += 1
                for k, i in enumerate(AHRS_IDX):
                    axes[k].feed(r["t"], r["raw"][i], r["vals"][i])
                for i, _v, _lo, _hi in implausible(r["vals"]):
                    shifted[i] += 1
            now = time.time()
            if now - last_print >= 1.0:
                last_print = now
                _report(axes, link, a.expect, t0, dict(shifted), skipped, good)
                if a.n_frames is not None and good >= a.n_frames:
                    print("\n%d good frames reached - stopping." % a.n_frames)
                    break
    except KeyboardInterrupt:
        print("\nstopped by operator.")
    finally:
        link.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
