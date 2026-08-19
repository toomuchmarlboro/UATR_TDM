#!/usr/bin/env python3
"""
IMU / AHRS connection test - roll, pitch and yaw out of the aux_vcu $GDAT2 link.

WHICH IMU THIS TALKS TO
-----------------------
The only IMU this repo knows about is the AHRS inside the aux_vcu. It is not
wired to the FPGA and not on a serial port here: its attitude arrives already
fused, as three IEEE-754 floats inside the $GDAT2 telemetry sentence that the
aux_vcu broadcasts over TCP every ~20 ms.

    ulRaw[4] AHRS Roll   ulRaw[5] AHRS Pitch   ulRaw[6] AHRS Yaw    all deg

So "connecting to the IMU" means opening that link and watching those three
fields. There is no separate handshake, no register map, no polling - if the
sentence arrives, the IMU is on the wire. See docs/GDAT2_TELEMETRY.md.

If you meant a DIFFERENT IMU - a part you are wiring to a USB-serial adapter or
onto the FPGA's I2C bus - this script does not cover it, and nothing in the repo
names such a part yet. Start with `--raw` below pointed at whatever port it
appears on, look at the actual bytes, and write the decoder from those. Do not
start from a register map recalled from memory; that is how a plausible-looking
decoder gets built for the wrong device.


WHAT THIS CHECKS THAT gdat2.py DOES NOT
---------------------------------------
`python gdat2.py --connect ...` already prints every field once a second. That
proves the link. It does not prove the IMU, because the three ways an attitude
source fails all survive framing, checksum and formatting untouched:

  FROZEN   the same bits arrive frame after frame. A real AHRS dithers in the
           low bits even bolted to a bench - fusion output that is bit-identical
           across hundreds of frames is a firmware field that stopped being
           updated, or a sensor that stopped being polled, not a steady boat.
           Checked on the RAW u32, not the printed float: a value rounded to
           two decimals hides exactly the dither that distinguishes the two.

  ZERO     the field decodes fine and reads 0.0 forever. Means the firmware
           never filled it. Indistinguishable from "level and pointing north"
           if you only look at one frame, which is why this looks over a window.

  SHIFTED  the field map moved (firmware adds a field, everything after it
           slides one place) and roll is being read out of the depth-temp slot.
           Every number stays perfectly formatted with the right unit next to
           it. Caught only by plausible ranges - a pitch of 130 deg is not an
           attitude, it is a wrong slot. Bounds live in gdat2.PLAUSIBLE.

The field names, order and ranges are IMPORTED from gdat2.py, never copied. A
copied field map is the origin of the SHIFTED failure above: two maps drift
apart silently and both keep printing.


RUNNING IT
----------
    python imu_test.py --selftest                 # decoder + verdict logic
    python gdat2.py --sim                         # fake aux_vcu, one terminal
    python imu_test.py --connect 127.0.0.1        # this one, in another

    python imu_test.py --buoy 1                   # 192.168.3.110:8080
    python imu_test.py --buoy 1 --expect still    # bench: should be steady
    python imu_test.py --buoy 1 --expect moving   # in the water: should move
    python imu_test.py --buoy 1 --n-frames 200    # stop after 200 good frames
    python imu_test.py --listen 8080              # if the aux_vcu dials us
    python imu_test.py --connect 127.0.0.1 --raw  # bytes only, no decoding
"""

import argparse
import collections
import socket
import sys
import threading
import time

try:
    import gdat2
except ImportError:                                   # run from the repo root
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
    import gdat2

AXES = tuple(gdat2.FIELDS[i][0] for i in gdat2.AHRS_IDX)   # AHRS Roll/Pitch/Yaw

# A window has to be long enough that a slow, genuine attitude change is not
# mistaken for a freeze. 3 s is 150 sentences at the 20 ms broadcast rate.
DEFAULT_WINDOW_S = 3.0

# Expectation thresholds, in degrees of span across the window.
#
# STILL_MAX is deliberately loose: a buoy on a bench still gets nudged, and a
# test that cries wolf when someone leans on the table gets ignored, which is
# worse than not running it.
STILL_MAX  = 5.0        # --expect still: more span than this is not "still"
MOVING_MIN = 0.20       # --expect moving: less span than this is not "moving"


# ------------------------------------------------------------------- window ---
def wrapped_span(vals):
    """Peak-to-peak of an angle series, in degrees, honouring the 360 wrap.

    Yaw crossing north reads 359.5 then 0.5. A plain max-minus-min calls that a
    359 deg swing and every freeze/motion verdict built on it is inverted at the
    one heading the buoy is most likely to sit at. Consecutive differences are
    wrapped into +/-180 and re-accumulated, so the series is unwrapped first.

    This is correct only while the true step between frames is under 180 deg. At
    20 ms that is a 9000 deg/s slew - well past any real vehicle, and past the
    gyro's own range.
    """
    if not vals:
        return 0.0
    acc, out = float(vals[0]), [float(vals[0])]
    for a, b in zip(vals, vals[1:]):
        d = (float(b) - float(a) + 180.0) % 360.0 - 180.0
        acc += d
        out.append(acc)
    return max(out) - min(out)


class AxisWindow(object):
    """Rolling window over one attitude axis, and the verdict it supports."""

    def __init__(self, name, window_s=DEFAULT_WINDOW_S):
        self.name = name
        self.window_s = window_s
        self.samples = collections.deque()     # (t, raw_u32, value_deg)

    def feed(self, t, raw, val):
        self.samples.append((t, raw, val))
        cut = t - self.window_s
        while self.samples and self.samples[0][0] < cut:
            self.samples.popleft()

    # -- derived ----------------------------------------------------------
    @property
    def n(self):
        return len(self.samples)

    @property
    def span(self):
        return wrapped_span([s[2] for s in self.samples if s[2] is not None])

    @property
    def last(self):
        return self.samples[-1][2] if self.samples else None

    @property
    def distinct_raw(self):
        """Distinct raw bit patterns in the window. 1 means frozen."""
        return len(set(s[1] for s in self.samples if s[1] is not None))

    @property
    def all_zero(self):
        return bool(self.samples) and all(s[1] == 0 for s in self.samples)

    def drift_deg_per_min(self):
        """Signed end-to-end rate across the window, wrap-aware.

        On a stationary vehicle this is uncorrected gyro bias on yaw. It is a
        number to report, not to judge: what counts as too much drift depends
        on the mission length, which this script does not know.
        """
        if self.n < 2:
            return 0.0
        (t0, _r0, v0), (t1, _r1, v1) = self.samples[0], self.samples[-1]
        if v0 is None or v1 is None or t1 <= t0:
            return 0.0
        d = (float(v1) - float(v0) + 180.0) % 360.0 - 180.0
        return d / (t1 - t0) * 60.0

    def verdict(self, expect=None, min_samples=10):
        """-> (tag, text). tag is 'ok' | 'warn' | 'wait'.

        Order matters: ZERO is reported ahead of FROZEN because an all-zero
        field is also frozen, and "the firmware never filled this" is the more
        actionable of the two readings of the same evidence.
        """
        if self.n < min_samples:
            return "wait", "%d samples, need %d" % (self.n, min_samples)
        if self.all_zero:
            return "warn", ("ZERO for %.1fs - firmware is not filling this "
                            "field" % self.window_s)
        if self.distinct_raw == 1:
            return "warn", ("FROZEN - %d frames, one identical bit pattern; "
                            "a live AHRS dithers" % self.n)

        span = self.span
        if expect == "still" and span > STILL_MAX:
            return "warn", ("span %.2f deg over %.1fs - expected still, "
                            "something is moving it" % (span, self.window_s))
        if expect == "moving" and span < MOVING_MIN:
            return "warn", ("span %.3f deg over %.1fs - expected motion, this "
                            "is dither only" % (span, self.window_s))
        return "ok", "live, span %.3f deg over %.1fs" % (span, self.window_s)


class ImuWatch(object):
    """Collects $GDAT2 frames off the link thread; the main thread reads them.

    The callback runs on gdat2.Link's reader thread. Everything it touches is
    either behind this lock or a bounded queue - printing from that thread would
    put terminal I/O in the path of a 50 Hz socket reader.
    """

    def __init__(self, window_s=DEFAULT_WINDOW_S):
        self.lock = threading.Lock()
        self.axes = [AxisWindow(n, window_s) for n in AXES]
        self.good = 0            # frames whose AHRS fields all decoded
        self.skipped = 0         # frames dropped before they reached the axes
        self.shifted = collections.Counter()   # field index -> times implausible
        # Drained once a second against a 50 Hz feed. Sized well past that: at
        # 64 the first print cycle that slips past ~1.3 s starts dropping
        # frames from --every, silently and only under load.
        self.pending = collections.deque(maxlen=512)

    def feed(self, r):
        """gdat2.Link.on_frame callback. Never raises into the link."""
        # A sentence that failed its checksum is still decoded and still shown
        # by gdat2, but it must not feed the motion window: one corrupted float
        # is a spike that reads as motion, and this script's whole job is to
        # tell motion from no motion.
        if not r["ok"]:
            with self.lock:
                self.skipped += 1
            return
        vals, raw, t = r["vals"], r["raw"], r["t"]
        if any(vals[i] is None for i in gdat2.AHRS_IDX):
            with self.lock:
                self.skipped += 1
            return

        bad = dict((i, True) for i, _v, _lo, _hi in gdat2.implausible(vals))
        with self.lock:
            self.good += 1
            for k, i in enumerate(gdat2.AHRS_IDX):
                self.axes[k].feed(t, raw[i], vals[i])
            for i in bad:
                self.shifted[i] += 1
            self.pending.append((t, tuple(vals[i] for i in gdat2.AHRS_IDX)))

    def drain(self):
        with self.lock:
            out = list(self.pending)
            self.pending.clear()
            return out

    def report(self, expect=None):
        with self.lock:
            return [(a.name, a.last, a.verdict(expect), a.drift_deg_per_min())
                    for a in self.axes], self.good, self.skipped, \
                   dict(self.shifted)


# ---------------------------------------------------------------- printing ---
_MARK = {"ok": "  ok  ", "warn": " WARN ", "wait": " ...  "}


def print_report(watch, link, expect, t0):
    rows, good, skipped, shifted = watch.report(expect)
    s = link.snapshot()
    print("\n[%6.1fs] %s %s   %.0f sentences/s   good %d  csum %d  bad %d  lost %d"
          % (time.time() - t0, s["state"], s["peer"], s["rate"], s["good"],
             s["csum_err"], s["parse_err"], s["lost"]))
    for name, last, (tag, text), drift in rows:
        val = "%8.2f deg" % last if last is not None else "       -  "
        print("  %-6s %-12s %s  %s" % (_MARK.get(tag, "  ?   "), name.replace(
            "AHRS ", ""), val, text))
    yaw = rows[2]
    if abs(yaw[3]) > 0.01:
        print("         yaw drift %+.2f deg/min over the window%s"
              % (yaw[3], "  (stationary: this is gyro bias)"
                 if expect == "still" else ""))
    if shifted:
        # Reported loudly and separately: an out-of-range field is evidence
        # about the SENTENCE, not about the IMU, and the two must not be
        # confused. The IMU can be perfect and still be read out of the wrong
        # slot.
        print("  !! fields outside plausible range - suspect a SHIFTED field "
              "map, not a broken sensor:")
        for i, n in sorted(shifted.items()):
            lo, hi = gdat2.PLAUSIBLE[i]
            print("       ulRaw[%d] %-16s %d frames outside %g..%g %s"
                  % (i, gdat2.FIELDS[i][0], n, lo, hi, gdat2.FIELDS[i][1]))
    if skipped:
        print("  (%d frames not fed to the window: checksum or field error)"
              % skipped)


# --------------------------------------------------------------------- raw ---
def run_raw(host, port):
    """Dump bytes as they arrive, decode nothing. Works on any device.

    This is the right first step for hardware whose framing is not yet known -
    let the bytes say what the format is. It is also the fastest way to tell
    "nothing is connected" from "something is connected and I am misreading it".
    """
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


# ---------------------------------------------------------------- selftest ---
def _selftest():
    """No hardware. Checks the decode, the wrap, and every verdict branch."""
    # The captured sentence from docs/GDAT2_TELEMETRY.md, and the attitude it
    # is documented to carry. This is the one end-to-end fact available without
    # the buoy: if this drifts, the decoder has changed under us.
    cap = ("$GDAT2,3CC85BA9,41C0DBB2,41545BB3,419494F9,40AAE6D3,402149B0,"
           "41D23D71,00001258,0000005F,00000001,145,149*52")
    r = gdat2.parse(cap)
    assert r["csum_ok"] is True, "captured sentence checksum"
    assert r["ok"], r["err"]
    got = [r["vals"][i] for i in gdat2.AHRS_IDX]
    for name, v, want in zip(AXES, got, (5.341, 2.520, 26.280)):
        assert abs(v - want) < 5e-4, "%s: %r != %r" % (name, v, want)
    assert (r["seq"], r["cnt"]) == (145, 149), "seq/cnt are decimal, not hex"
    assert not gdat2.implausible(r["vals"]), "captured sentence is plausible"

    # A shifted field map is caught by the bounds, and by pitch first: 13.27 m
    # of depth landing in the pitch slot is still a legal pitch, but the depth
    # slot then holds a temperature and so on down the line.
    shifted = list(r["vals"])
    shifted[gdat2.I_PITCH] = 130.0                  # not an attitude
    bad = gdat2.implausible(shifted)
    assert [i for i, _v, _lo, _hi in bad] == [gdat2.I_PITCH], bad

    # Wrap: 350 -> 10 is a 20 deg swing, not 340.
    assert abs(wrapped_span([350.0, 355.0, 0.0, 5.0, 10.0]) - 20.0) < 1e-6
    assert abs(wrapped_span([10.0, 12.0, 11.0]) - 2.0) < 1e-6
    assert wrapped_span([]) == 0.0 and wrapped_span([7.0]) == 0.0

    # Verdicts. Raw bits drive FROZEN, so the frozen case must repeat the same
    # u32 - which is exactly what a float comparison at 2 dp would miss.
    w = AxisWindow("t", window_s=10.0)
    assert w.verdict()[0] == "wait"
    for k in range(20):
        w.feed(1000.0 + k * 0.02, gdat2.f32_bits(12.5), 12.5)
    assert w.verdict()[0] == "warn" and "FROZEN" in w.verdict()[1], w.verdict()

    z = AxisWindow("t", window_s=10.0)
    for k in range(20):
        z.feed(1000.0 + k * 0.02, 0, 0.0)
    assert "ZERO" in z.verdict()[1], z.verdict()

    # Dither only: live, but not "moving".
    d = AxisWindow("t", window_s=10.0)
    for k in range(20):
        v = 12.5 + 0.001 * (k % 3)
        d.feed(1000.0 + k * 0.02, gdat2.f32_bits(v), v)
    assert d.verdict()[0] == "ok", d.verdict()
    assert d.verdict("still")[0] == "ok", d.verdict("still")
    assert d.verdict("moving")[0] == "warn", d.verdict("moving")

    # Real motion: moving is satisfied, still is not.
    m = AxisWindow("t", window_s=10.0)
    for k in range(20):
        v = 12.5 + 0.9 * k
        m.feed(1000.0 + k * 0.02, gdat2.f32_bits(v), v)
    assert m.verdict("moving")[0] == "ok", m.verdict("moving")
    assert m.verdict("still")[0] == "warn", m.verdict("still")

    # The window really is a window: old samples must leave, or a freeze that
    # started a minute ago never registers.
    e = AxisWindow("t", window_s=1.0)
    e.feed(1000.0, gdat2.f32_bits(1.0), 1.0)
    e.feed(1002.0, gdat2.f32_bits(2.0), 2.0)
    assert e.n == 1, e.n

    # ImuWatch must reject what it is told to reject. A bad-checksum frame
    # carrying a wild float would otherwise register as motion.
    watch = ImuWatch(window_s=10.0)
    ok = gdat2.parse(cap)
    watch.feed(ok)
    bad_frame = gdat2.parse(cap.replace("*52", "*53"))
    watch.feed(bad_frame)
    assert watch.good == 1 and watch.skipped == 1, (watch.good, watch.skipped)

    print("imu_test selftest OK  (roll %.3f  pitch %.3f  yaw %.3f from the "
          "captured sentence)" % tuple(got))
    return 0


# -------------------------------------------------------------------- main ---
def main():
    ap = argparse.ArgumentParser(
        description="IMU/AHRS connection test over the aux_vcu $GDAT2 link")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--buoy", type=int, choices=(1, 2, 3, 4),
                   help="dial that buoy's aux_vcu (%s)"
                        % ", ".join("%d=%s" % (i + 1, ip)
                                    for i, (_n, ip) in enumerate(gdat2.BUOYS)))
    g.add_argument("--connect", metavar="HOST[:PORT]", help="dial the aux_vcu")
    g.add_argument("--listen", type=int, metavar="PORT", help="wait for it")
    g.add_argument("--selftest", action="store_true",
                   help="decoder and verdict logic, no hardware")
    ap.add_argument("--port", type=int, default=gdat2.DEFAULT_PORT)
    ap.add_argument("--raw", action="store_true",
                    help="dump bytes, decode nothing (any device, any framing)")
    ap.add_argument("--expect", choices=("still", "moving"), default=None,
                    help="what the buoy is doing: 'still' on the bench, "
                         "'moving' in the water. Default: report only, judge "
                         "nothing beyond frozen/zero.")
    ap.add_argument("--window", type=float, default=DEFAULT_WINDOW_S,
                    metavar="S", help="motion window, seconds (default %.1f)"
                                      % DEFAULT_WINDOW_S)
    ap.add_argument("--n-frames", type=int, default=None, metavar="N",
                    help="stop after N good frames (default: run until ctrl-C)")
    ap.add_argument("--every", type=int, default=0, metavar="N",
                    help="also print every Nth frame's raw attitude "
                         "(0 = summary only)")
    a = ap.parse_args()

    if a.selftest:
        return _selftest()

    if a.listen:
        mode, host, port = "server", "0.0.0.0", a.listen
    elif a.buoy:
        mode, host, port = "client", gdat2.BUOYS[a.buoy - 1][1], a.port
    elif a.connect:
        h, _, p = a.connect.partition(":")
        mode, host, port = "client", h, int(p) if p else a.port
    else:
        ap.print_help()
        return 1

    if a.raw:
        if mode != "client":
            print("--raw dials out; use --connect or --buoy with it")
            return 1
        return run_raw(host, port)

    watch = ImuWatch(window_s=a.window)
    link = gdat2.Link(mode, host, port, on_frame=watch.feed)
    print("IMU/AHRS via $GDAT2 %s %s:%d   window %.1fs   expect %s"
          % ("<-" if mode == "server" else "->", host, port, a.window,
             a.expect or "(nothing)"))
    print("roll/pitch/yaw are ulRaw[%d..%d]; every other GDAT2 field is decoded "
          "too and\nchecked for range, because a shifted map shows up there "
          "first." % (gdat2.I_ROLL, gdat2.I_YAW))
    link.start()

    t0 = time.time()
    shown = 0
    try:
        while True:
            time.sleep(1.0)
            if a.every:
                for t, (roll, pitch, yaw) in watch.drain():
                    shown += 1
                    if shown % a.every == 0:
                        print("  [%7.2fs] roll %8.2f  pitch %8.2f  yaw %8.2f"
                              % (t - t0, roll, pitch, yaw))
            else:
                watch.drain()          # keep the deque from going stale
            print_report(watch, link, a.expect, t0)
            if a.n_frames is not None and watch.good >= a.n_frames:
                print("\n%d good frames reached - stopping." % a.n_frames)
                break
    except KeyboardInterrupt:
        print("\nstopped by operator.")
    finally:
        link.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
