#!/usr/bin/env python3
"""
$GDAT2 telemetry decoder and TCP link  (aux_vcu -> Control Station, ID = 37).

This is a NEW protocol for this repo. It has nothing to do with the FPGA's UDP
audio stream in udp_monitor.py - different device, different transport, different
framing. It lives in its own module so neither can break the other.

    $GDAT2,<ulRaw[0]>,...,<ulRaw[9]>,<seq>,<cnt>*HH<CR><LF>

    field            type   description                       decoded as
    ---------------------------------------------------------------------
    ulRaw[0]  u32    Leak sensor       voltage                 float, V
    ulRaw[1]  u32    Voltage monitor   main voltage            float, V
    ulRaw[2]  u32    Depth             water depth             float, m
    ulRaw[3]  u32    Depth temp        sensor temperature      float, degC
    ulRaw[4]  u32    AHRS Roll         roll angle              float, deg
    ulRaw[5]  u32    AHRS Pitch        pitch angle             float, deg
    ulRaw[6]  u32    AHRS Yaw          yaw angle               float, deg
    ulRaw[7]  u32    Altimeter dist    distance to seabed      integer, mm
    ulRaw[8]  u32    Altimeter conf    confidence 0-100        integer, %
    ulRaw[9]  u32    Digital I/O       bit0 = OPEN, bit1 = CLOSE
    seq       u32    sequence
    cnt       u8     packet counter, wraps at 256

Broadcast every ~20 ms, so ~50 sentences/s.


ENCODING  (confirmed by the hardware makers)
--------------------------------------------
  * ulRaw[0..9] are 8 HEX digits each, no 0x prefix, even when carrying integer
    data.  "42280000" is 0x42280000.
  * an f32 field is that u32 reinterpreted as an IEEE 754 32-bit float.
    0x42280000 = 42.0.
  * seq and cnt are unsigned DECIMAL ASCII, not hex.
  * checksum: XOR of every byte from the first '$' to the '*', exclusive of
    both; two hex chars.

The mixed radix in one sentence is the thing to keep hold of: the same digits
mean different numbers depending on which field they sit in. "100" is 256 as a
ulRaw field and 100 as cnt.


NOTE ON THE SPEC'S OWN EXAMPLE
------------------------------
The makers' note reads "42.5 degC = 0x42280000". 0x42280000 is 42.0; 42.5 is
0x422A0000. The hex is self-consistent with everything else, so it is the
decimal in the comment that is off by a typo. Worth confirming, but it changes
no code either way - the transform is hex -> f32 bits regardless.


STILL OPEN: CLIENT OR SERVER
----------------------------
Unknown which end listens, so Link does either: mode="client" dials the
aux_vcu, mode="server" waits for it to dial in. Does not block bring-up.

One aux_vcu per buoy on port 8080:
    buoy 1  192.168.3.110      buoy 3  192.168.3.130
    buoy 2  192.168.3.120      buoy 4  192.168.3.140

    python gdat2.py --buoy 2                         # dial that buoy
    python gdat2.py --connect 192.168.3.110:8080
    python gdat2.py --listen 8080                    # wait for it
    python gdat2.py --sim                            # fake source, no hardware
"""

import argparse
import math
import random
import socket
import struct
import sys
import threading
import time

TALKER   = "GDAT2"
MSG_ID   = 37
N_RAW    = 10                     # ulRaw[0..9]
PERIOD_S = 0.020                  # ~20 ms broadcast
DEFAULT_PORT = 8080

# One aux_vcu per buoy, all on port 8080.
BUOYS = (("buoy 1", "192.168.3.110"),
         ("buoy 2", "192.168.3.120"),
         ("buoy 3", "192.168.3.130"),
         ("buoy 4", "192.168.3.140"))
DEFAULT_HOST = BUOYS[0][1]

# name, unit, kind. kind drives how a bare integer token is reinterpreted.
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

DIO_OPEN  = 0x01
DIO_CLOSE = 0x02

# Index of each field, so callers name a field instead of hard-coding a number.
# A second copy of the field order is how a decoder silently goes one position
# out of step with the firmware and prints roll under the depth-temp heading.
I_LEAK, I_VBUS, I_DEPTH, I_DTEMP, I_ROLL, I_PITCH, I_YAW, \
    I_ALT_MM, I_ALT_PCT, I_DIO = range(N_RAW)

AHRS_IDX = (I_ROLL, I_PITCH, I_YAW)

# Physically plausible range per field, aligned with FIELDS. None = unbounded.
#
# These are sanity bounds, not calibration: a value outside them is far more
# likely to mean the field map has shifted (the number is reasonable for some
# OTHER quantity) than that the sensor read it. That is the failure this catches
# and a checksum cannot - a shifted map produces perfectly framed, perfectly
# checksummed, perfectly formatted nonsense.
#
# Yaw is the one bound that is a guess: the capture (26.28) and the simulator
# both sit in 0..360, but a 0-referenced +/-180 convention would be equally
# normal for an AHRS and is not ruled out by anything on hand, so the bound
# admits both rather than flagging a working device.
PLAUSIBLE = (
    (0.0,    5.0),        # Leak sensor, V - an ADC pin reading, 3.3/5 V rail
    (0.0,   60.0),        # Voltage monitor, V - 24 V nominal bus
    (-2.0,  500.0),       # Depth, m - slightly negative at the surface is real
    (-5.0,   50.0),       # Depth temp, degC - seawater plus self-heating
    (-180.0, 180.0),      # Roll, deg
    (-90.0,   90.0),      # Pitch, deg - a pitch outside this is a convention
                          # error, not an attitude
    (-180.0, 360.0),      # Yaw, deg - see note above, admits both conventions
    (0.0, 100000.0),      # Altimeter dist, mm - 100 m
    (0.0,    100.0),      # Altimeter conf, %
    (0.0,      3.0),      # Digital I/O - only bits 0 and 1 are defined
)


def implausible(vals):
    """-> [(index, value, lo, hi)] for every field outside PLAUSIBLE.

    Undecoded fields (None) are not reported here; they are already an error of
    their own and reporting them twice makes one fault read as two.
    """
    out = []
    for i, v in enumerate(vals):
        if v is None or PLAUSIBLE[i] is None:
            continue
        lo, hi = PLAUSIBLE[i]
        if not (lo <= v <= hi):
            out.append((i, v, lo, hi))
    return out


# ---------------------------------------------------------------- checksum ---
def checksum(body):
    """NMEA-0183 checksum: XOR of every byte between '$' and '*', exclusive."""
    c = 0
    for ch in body.encode("ascii", "replace"):
        c ^= ch
    return c


def build(raw, seq=0, cnt=0):
    """Encode 10 u32s into a sentence. Used by the simulator and the tests.

    ulRaw as 8 hex digits each, seq and cnt as unsigned decimal ASCII.
    """
    body = "%s,%s,%d,%d" % (TALKER, ",".join("%08X" % (int(v) & 0xFFFFFFFF)
                                             for v in raw), seq, cnt & 0xFF)
    return "$%s*%02X\r\n" % (body, checksum(body))


def f32_bits(x):
    """float -> the u32 that carries it. Inverse of the 'f32' decode."""
    return struct.unpack("<I", struct.pack("<f", float(x)))[0]


def bits_f32(v):
    """u32 -> the float its bits spell."""
    return struct.unpack("<f", struct.pack("<I", int(v) & 0xFFFFFFFF))[0]


# ------------------------------------------------------------------ decode ---
_HEX = set("0123456789abcdefABCDEF")


def decode_field(tok, kind):
    """-> (raw_u32_or_None, value_or_None). Strictly 8 hex digits, no prefix.

    Hex is not a guess here, it is the encoding - see ENCODING above. Two traps
    that an earlier decimal-first reading of this fell into, both silent:

      "42280000" is 0x42280000 = 42.0. Read as decimal it is 42,280,000, whose
      bits spell 1.96e-37. Every field is all-digits often enough that this
      would have looked like a working link producing absurd numbers.

      "3E000000" is 0.125. Hex digits include 'E', so any heuristic that treats
      an 'e' as a float exponent turns this into the literal 3.0 - a plausible
      value, silently wrong, on a field that happened to contain an E.

    Hence: no sniffing. The wire format is fixed, so parse it as what it is.
    """
    tok = tok.strip()
    if tok[:2].lower() == "0x":          # tolerated, not expected
        tok = tok[2:]
    if not tok or len(tok) > 8 or any(c not in _HEX for c in tok):
        return None, None
    raw = int(tok, 16)
    if kind == "f32":
        v = bits_f32(raw)
        # NaN/inf means the bits are not a float at all - an integer sent where
        # a float was documented. Report raw so the GUI can say so, not "nan".
        if math.isnan(v) or math.isinf(v):
            return raw, None
        return raw, v
    return raw, float(raw)


def parse(line):
    """Decode one sentence.

    Returns a dict, always - a rejected sentence still reports why. Never
    raises: this sits on a socket fed by another vendor's firmware, and one
    malformed sentence must not take the link down.
    """
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
            # fall through and still decode: a checksum error on an otherwise
            # readable sentence is far more useful shown than discarded, and
            # during bring-up it is usually the checksum convention that is
            # wrong, not the data.
    else:
        body = s                       # no checksum present; not an error

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
        out["err"] = "field %s not 8-digit hex" % ",".join(str(i) for i in bad)

    # 12 fields = ulRaw + seq + cnt as documented. 11 = no seq. Accept both:
    # the spec's field table lists cnt but not seq, so the sender may well omit
    # it, and refusing the sentence over that would block the whole tab.
    extra = nums[N_RAW:]
    if len(extra) >= 2:
        out["seq"] = _int_or_none(extra[0])
        out["cnt"] = _int_or_none(extra[1])
    elif len(extra) == 1:
        out["cnt"] = _int_or_none(extra[0])

    out["ok"] = out["err"] is None
    return out


def _int_or_none(tok):
    """seq and cnt are unsigned decimal ASCII - base 10, explicitly.

    Not base 0: Python rejects a leading zero there, so a zero-padded "08"
    would have come back None and silently disabled loss counting.
    """
    try:
        return int(tok.strip(), 10)
    except (ValueError, AttributeError):
        return None


def dio_text(raw):
    """Motor actuator state from ulRaw[9]."""
    if raw is None:
        return "-"
    o, c = bool(raw & DIO_OPEN), bool(raw & DIO_CLOSE)
    if o and c:
        return "OPEN+CLOSE (invalid)"
    return "OPEN" if o else "CLOSE" if c else "idle"


# -------------------------------------------------------------------- link ---
class Link(threading.Thread):
    """TCP transport. Reconnects on its own; never raises into the GUI.

    TCP is a byte stream, not a message stream, so sentences are recovered by
    buffering and splitting on newlines. A 20 ms broadcast will routinely land
    two sentences in one recv() and split a third across two, and treating each
    recv() as one message would corrupt roughly every other reading.
    """

    def __init__(self, mode="client", host="127.0.0.1", port=DEFAULT_PORT,
                 on_frame=None):
        super().__init__(daemon=True)
        self.mode, self.host, self.port = mode, host, port
        # Called with every parsed sentence, good or bad, on the link thread.
        # snapshot() only ever shows the LAST sentence, so a consumer that
        # needs each one (imu_test.py, which measures how the attitude moves
        # between frames) would otherwise have to re-parse the tail and drift
        # away from this decoder.
        self.on_frame = on_frame
        self.lock = threading.Lock()
        self.stop = False
        self.sock = None
        self.srv = None
        self.state = "idle"
        self.peer = ""
        self.last = None            # most recent parsed dict
        self.lines = 0              # sentences seen
        self.good = 0
        self.csum_err = 0
        self.parse_err = 0
        self.lost = 0               # from the cnt field
        self.cnt_prev = None
        self.rate = 0.0
        self._rt0 = time.time()
        self._rn = 0
        self.tail = ""              # raw text ring for the GUI

    # -- public ------------------------------------------------------------
    def snapshot(self):
        with self.lock:
            return dict(state=self.state, peer=self.peer, last=self.last,
                        lines=self.lines, good=self.good,
                        csum_err=self.csum_err, parse_err=self.parse_err,
                        lost=self.lost, rate=self.rate, tail=self.tail)

    def close(self):
        self.stop = True
        for s in (self.sock, self.srv):
            try:
                if s:
                    s.close()
            except OSError:
                pass

    # -- internals ---------------------------------------------------------
    def _set(self, state, peer=None):
        with self.lock:
            self.state = state
            if peer is not None:
                self.peer = peer

    def run(self):
        while not self.stop:
            try:
                self._session()
            except OSError as e:
                self._set("error: %s" % e)
            except Exception as e:                  # never kill the thread
                self._set("error: %r" % e)
            if self.stop:
                break
            self._set("reconnecting")
            for _ in range(20):                     # 2 s, but responsive to stop
                if self.stop:
                    return
                time.sleep(0.1)

    def _session(self):
        if self.mode == "server":
            self.srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.srv.bind(("0.0.0.0", self.port))
            self.srv.listen(1)
            self.srv.settimeout(0.5)
            self._set("listening on :%d" % self.port, peer="")
            while not self.stop:
                try:
                    self.sock, addr = self.srv.accept()
                    break
                except socket.timeout:
                    continue
            else:
                return
            self._set("connected", peer="%s:%d" % addr)
            try:
                self.srv.close()
            except OSError:
                pass
            self.srv = None
        else:
            self._set("connecting to %s:%d" % (self.host, self.port))
            self.sock = socket.create_connection((self.host, self.port),
                                                 timeout=3.0)
            self._set("connected", peer="%s:%d" % (self.host, self.port))

        self.sock.settimeout(0.5)
        buf = b""
        try:
            while not self.stop:
                try:
                    d = self.sock.recv(4096)
                except socket.timeout:
                    continue
                if not d:
                    self._set("peer closed")
                    return
                buf += d
                # Cap the buffer. A peer that sends megabytes without a newline
                # would otherwise grow this without bound.
                if len(buf) > 65536:
                    buf = buf[-4096:]
                while b"\n" in buf:
                    ln, _, buf = buf.partition(b"\n")
                    self._ingest(ln.decode("ascii", "replace").strip("\r"))
        finally:
            try:
                self.sock.close()
            except OSError:
                pass
            self.sock = None

    def _ingest(self, text):
        if not text.strip():
            return
        r = parse(text)
        with self.lock:
            self.lines += 1
            self._rn += 1
            now = time.time()
            if now - self._rt0 >= 0.5:
                self.rate = self._rn / (now - self._rt0)
                self._rt0, self._rn = now, 0
            # The two error buckets are disjoint. A corrupted sentence usually
            # fails the checksum AND the field parse, and counting it in both
            # made one fault read as two independent problems - which is the
            # opposite of what an error tally is for. Checksum wins, because it
            # names the cause; only a sentence with a good (or absent) checksum
            # that still will not decode is "unparsable".
            if r["csum_ok"] is False:
                self.csum_err += 1
                if r["raw"][0] is not None:
                    self.last = r      # readable but failed checksum: still show
            elif r["ok"]:
                self.good += 1
                self.last = r
            else:
                self.parse_err += 1
            # cnt is a u8 that wraps at 256. Anything but +1 is loss - unless it
            # is a restart, which shows up as a large jump and is not counted.
            c = r["cnt"]
            if c is not None:
                if self.cnt_prev is not None:
                    d = (c - self.cnt_prev) & 0xFF
                    if 1 < d < 64:
                        self.lost += d - 1
                self.cnt_prev = c
            self.tail = (self.tail + text + "\n")[-1200:]
        # Outside the lock: a consumer that blocks must not stall the reader,
        # and a consumer that raises must not take the link down - this thread
        # is the whole transport.
        if self.on_frame is not None:
            try:
                self.on_frame(r)
            except Exception:
                pass


# --------------------------------------------------------------- simulator ---
class Sim(threading.Thread):
    """Fake aux_vcu, so the GUI tab can be proven before the hardware exists.

    Serves TCP on --sim-port and pushes sentences at the real 20 ms cadence.
    Every so often it emits a corrupt sentence and skips a counter, because a
    telemetry view that has only ever seen clean data has not been tested.
    """

    def __init__(self, port=DEFAULT_PORT, glitch=True):
        super().__init__(daemon=True)
        self.port, self.glitch, self.stop = port, glitch, False

    def run(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("0.0.0.0", self.port))
        srv.listen(2)
        srv.settimeout(0.5)
        while not self.stop:
            try:
                c, _ = srv.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            threading.Thread(target=self._feed, args=(c,), daemon=True).start()
        try:
            srv.close()
        except OSError:
            pass

    def _feed(self, c):
        seq, cnt, t = 0, 0, 0.0
        try:
            while not self.stop:
                t += PERIOD_S
                raw = [
                    f32_bits(0.02 + 0.005 * random.random()),        # leak, V
                    f32_bits(23.8 + 0.4 * math.sin(t * 0.3)),        # bus, V
                    f32_bits(12.0 + 3.0 * math.sin(t * 0.15)),       # depth, m
                    f32_bits(18.5 + 0.5 * math.sin(t * 0.05)),       # temp
                    f32_bits(6.0 * math.sin(t * 0.7)),               # roll
                    f32_bits(4.0 * math.sin(t * 0.5 + 1.0)),         # pitch
                    f32_bits((t * 9.0) % 360.0),                     # yaw
                    int(4200 + 900 * math.sin(t * 0.2)),             # alt, mm
                    int(88 + 10 * random.random()),                  # conf, %
                    (DIO_OPEN if int(t) % 10 < 3 else
                     DIO_CLOSE if int(t) % 10 < 6 else 0),           # dio
                ]
                s = build(raw, seq, cnt)
                # Roughly every 2 s and every 1 s respectively. Frequent enough
                # that a short run exercises the error paths - a simulator whose
                # faults only appear after minutes does not get used to test
                # them, which defeats the point of injecting faults at all.
                if self.glitch and seq and seq % 97 == 0:
                    s = s[:12] + "X" + s[13:]        # corrupt -> checksum fails
                if self.glitch and seq and seq % 53 == 0:
                    cnt = (cnt + 2) & 0xFF           # skip one -> loss counted
                c.sendall(s.encode("ascii"))
                seq = (seq + 1) & 0xFFFFFFFF
                cnt = (cnt + 1) & 0xFF
                time.sleep(PERIOD_S)
        except OSError:
            pass
        finally:
            try:
                c.close()
            except OSError:
                pass


# -------------------------------------------------------------------- main ---
def _selftest():
    """Round-trip the encoder against the decoder. No hardware needed."""
    # The makers' own worked example, and the value it really carries.
    assert "%08X" % f32_bits(42.0) == "42280000"
    assert abs(bits_f32(0x42280000) - 42.0) < 1e-6
    assert "%08X" % f32_bits(42.5) == "422A0000"

    # Hex, not decimal. Both of these used to decode wrongly and silently.
    assert abs(decode_field("42280000", "f32")[1] - 42.0) < 1e-6
    assert abs(decode_field("3E000000", "f32")[1] - 0.125) < 1e-9  # 'E' is a digit
    assert decode_field("000010E1", "u32")[1] == 4321
    assert decode_field("0000000A", "u32")[1] == 10                # not 10 decimal
    assert decode_field("", "u32") == (None, None)
    assert decode_field("12345678901", "u32") == (None, None)      # too long
    assert decode_field("GG00", "u32") == (None, None)             # not hex

    vals = [0.0234, 23.9, 12.34, 18.6, -3.5, 2.25, 271.5]
    raw = [f32_bits(v) for v in vals] + [4321, 93, DIO_OPEN]
    line = build(raw, seq=7, cnt=9)
    assert line.startswith("$GDAT2,") and line.endswith("\r\n")
    body = line[1:line.index("*")]
    for tok in body.split(",")[1:1 + N_RAW]:
        assert len(tok) == 8 and all(c in _HEX for c in tok), tok
    assert body.split(",")[N_RAW + 1:] == ["7", "9"]      # seq/cnt decimal

    r = parse(line)
    assert r["ok"], r["err"]
    assert r["csum_ok"] is True
    for i, v in enumerate(vals):
        assert abs(r["vals"][i] - v) < 1e-3, (i, r["vals"][i], v)
    assert r["vals"][7] == 4321 and r["vals"][8] == 93
    assert dio_text(r["raw"][9]) == "OPEN"
    assert r["seq"] == 7 and r["cnt"] == 9
    assert r["wire"][7] == "000010E1"

    # zero-padded cnt must still count; base 0 would have rejected it
    b2 = "%s,%s,0,08" % (TALKER, ",".join("%08X" % v for v in raw))
    z = parse("$%s*%02X" % (b2, checksum(b2)))
    assert z["ok"] and z["cnt"] == 8, z

    # checksum is a plain XOR from '$' to '*', exclusive of both, 2 hex chars
    assert checksum("A") == 0x41
    assert checksum("AB") == 0x41 ^ 0x42
    assert checksum("") == 0
    corrupt = line[:12] + ("Y" if line[12] != "Y" else "Z") + line[13:]
    assert parse(corrupt)["csum_ok"] is False

    nocsum = "$%s" % body
    assert parse(nocsum)["csum_ok"] is None and parse(nocsum)["ok"]

    assert not parse("$%s,1,2,3*00" % TALKER)["ok"]        # too few fields
    assert not parse("garbage")["ok"]
    assert not parse("")["ok"]
    print("gdat2 self-test OK  (%d fields, ID=%d, ~%.0f Hz, hex-encoded)"
          % (N_RAW, MSG_ID, 1.0 / PERIOD_S))
    return 0


def main():
    ap = argparse.ArgumentParser(description="$GDAT2 telemetry link")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--buoy", type=int, choices=(1, 2, 3, 4),
                   help="dial that buoy's aux_vcu (%s)"
                        % ", ".join("%d=%s" % (i + 1, ip)
                                    for i, (_n, ip) in enumerate(BUOYS)))
    g.add_argument("--connect", metavar="HOST[:PORT]", help="dial the aux_vcu")
    g.add_argument("--listen", type=int, metavar="PORT", help="wait for it")
    g.add_argument("--sim", action="store_true", help="run the fake source")
    g.add_argument("--selftest", action="store_true")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--sim-port", type=int, default=DEFAULT_PORT)
    a = ap.parse_args()

    if a.selftest:
        return _selftest()
    if a.sim:
        s = Sim(a.sim_port)
        s.start()
        print("simulated aux_vcu on 0.0.0.0:%d - ctrl-C to stop" % a.sim_port)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            s.stop = True
        return 0

    if a.listen:
        link = Link("server", port=a.listen)
    elif a.buoy:
        link = Link("client", BUOYS[a.buoy - 1][1], a.port)
    elif a.connect:
        host, _, p = a.connect.partition(":")
        link = Link("client", host, int(p) if p else a.port)
    else:
        ap.print_help()
        return 1

    link.start()
    try:
        while True:
            time.sleep(1.0)
            s = link.snapshot()
            r = s["last"]
            print("[%s] %s  %.0f/s  good %d  csum %d  bad %d  lost %d"
                  % (s["state"], s["peer"], s["rate"], s["good"],
                     s["csum_err"], s["parse_err"], s["lost"]))
            if r:
                for i, (nm, unit, _k) in enumerate(FIELDS):
                    v = r["vals"][i]
                    txt = dio_text(r["raw"][i]) if i == 9 else (
                        "%12.4f %s" % (v, unit) if v is not None else "-")
                    print("    %-16s %-8s %s" % (nm, r["wire"][i], txt))
    except KeyboardInterrupt:
        link.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
