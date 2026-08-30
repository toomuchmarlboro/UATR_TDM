#!/usr/bin/env python3
"""
Blue Robotics Ping1D altimeter over TCP. Distance and confidence.

    python ping1d.py --buoy 3                # 192.168.3.132:8080
    python ping1d.py --connect 192.168.3.132:8080
    python ping1d.py --selftest              # no hardware needed
    python ping1d.py --sim                   # fake sonar, then --connect to it

One altimeter per buoy at 192.168.3.1<buoy>2, reached through a serial-to-TCP
bridge on port 8080. The bridge must be set to 115200 baud - the manufacturer's
own example calls that out, and a wrong baudrate looks exactly like a sensor
that opens a socket and never answers.

WHY NOT brping
==============
The manufacturer's example drives this through bluerobotics-ping. That library
is the reference implementation and it works, but their code also carries a
compatibility fallback for versions without connect_tcp() and an error string
about installed brping being "tidak konsisten". Since this is one request and
one 12-byte reply, it is implemented here directly instead: no dependency to
pin, no version to diagnose on a boat, and gdat2.py's standard-library-only
rule holds across the whole telemetry path.

WHY THAT IS SAFE, WHEN GUESSING A FIELD MAP IS NOT
==================================================
The recurring failure this codebase guards against is a decoder that frames,
checksums and prints believable numbers under the wrong headings. A binary
protocol with a length, a message id and a trailing checksum cannot do that. A
misread frame fails the checksum or the id and is dropped; it does not become a
plausible depth. So the risk here is "no readings", which is loud, rather than
"wrong readings", which is not.

FRAME FORMAT (Ping protocol v1)
    offset size  field
    0      2     'B','R'  (0x42 0x52)
    2      2     payload length, u16 little endian
    4      2     message id, u16 little endian
    6      1     source device id
    7      1     destination device id
    8      N     payload
    8+N    2     checksum, u16 little endian = sum of all preceding bytes

    general_request  id 6      payload: u16 of the id being asked for
    distance_simple  id 1212   payload: u32 distance mm, u8 confidence %

Ping1D does not stream by default: you ask, it answers. So the reader polls,
which is also why a poll interval appears below and not in gdat2.py.
"""

import argparse
import socket
import struct
import sys
import threading
import time

PING_PORT = 8080
PING_POLL_S = 0.05                      # 20 Hz, matching the vendor GUI's 50 ms

PING_HEADER = b"BR"
ID_GENERAL_REQUEST = 6

# Replies we understand. distance (1211) is what brping's get_distance() asks
# for, and therefore what the manufacturer's own GUI uses - so it is the one
# this firmware is known to answer. distance_simple (1212) is the smaller
# message and is tried as a fallback, because not every build implements both
# and asking for an unimplemented id gets you a NACK or silence, which is
# indistinguishable from a dead sensor unless you are watching for it.
ID_NACK = 1
ID_DEVICE_INFORMATION = 4
ID_PROTOCOL_VERSION = 5
ID_DISTANCE = 1211
ID_DISTANCE_SIMPLE = 1212

# Ping1D get/set ids. Worth writing down because the 12xx block is easy to
# misread: 1207 is gain_setting, NOT a temperature, and 1210 is general_info,
# NOT voltage_5. A probe here once labelled them wrongly and produced
# perfectly plausible nonsense.
ID_GENERAL_INFO = 1210          # fw major/minor u16, voltage_5 u16,
                                # ping_interval u16, gain u8, mode_auto u8
ID_SET_SPEED_OF_SOUND = 1002
ID_SET_MODE_AUTO = 1003
ID_SET_PING_INTERVAL = 1004
ID_SET_GAIN_SETTING = 1005
ID_SET_PING_ENABLE = 1006

# What the manufacturer's GUI writes when you press "Apply Settings". Its
# defaults, from their QSpinBox/QComboBox initial values.
VENDOR_DEFAULTS = {"interval": 50, "gain": 3, "sos": 1500000, "enable": 1}

# Tried in order until one answers, then locked to whichever worked.
DISTANCE_IDS = (ID_DISTANCE, ID_DISTANCE_SIMPLE)

# The manufacturer's example sleeps 1 s after connect_tcp() with the comment
# "beri waktu TCP-to-serial converter membuka jalur serial fisik". The TCP
# accept happens in the bridge, not the sonar, so the socket is up before the
# serial side is - requests sent in that window are dropped on the floor.
SETTLE_S = 1.0

# How long one reply may take. Generous on purpose: it bounds a REQUEST that
# went unanswered, not the polling rate. The next request is sent as soon as
# the previous one is answered, so a healthy link runs far faster than this.
REPLY_TIMEOUT_S = 1.0

# Plausible bounds, same idea as gdat2.PLAUSIBLE: a number outside these is
# reported rather than drawn as though it were a measurement. Ping1D is
# specified to 30 m in water; the extra headroom admits an in-air bench test.
# Measured: this unit reports ~90 m at 15-35 % confidence with no target,
# which is the sonar saying "nothing found", not a bad reading. The ceiling
# is therefore well above the 30 m in-water spec, and CONFIDENCE is the
# field that tells a range from a shrug.
DIST_MAX_MM = 150000
CONF_MAX = 100


def ping_checksum(frame_wo_csum):
    """Sum of every byte before the checksum field, truncated to u16."""
    return sum(frame_wo_csum) & 0xFFFF


def ping_build(msg_id, payload=b"", src=0, dst=0):
    head = PING_HEADER + struct.pack("<HHBB", len(payload), msg_id, src, dst)
    body = head + payload
    return body + struct.pack("<H", ping_checksum(body))


def ping_request(msg_id):
    """A general_request asking the device to send msg_id once."""
    return ping_build(ID_GENERAL_REQUEST, struct.pack("<H", msg_id))


class PingParser(object):
    """Incremental frame reassembly.

    TCP is a byte stream: one recv() routinely holds part of a frame, or two
    frames and a fragment. Anything that treats a recv() as a message will
    corrupt roughly every other reading - the same reason gdat2.Link buffers
    and splits on newlines rather than trusting recv() boundaries.

    Resynchronises by scanning for the 'BR' header, so a bridge that powers up
    mid-frame recovers on the next one instead of staying broken.
    """

    MAX_PAYLOAD = 1024              # anything larger is a desync, not a frame

    def __init__(self):
        self.buf = bytearray()
        self.csum_err = 0
        self.resync = 0

    def feed(self, data):
        """-> list of (msg_id, payload) for every complete, valid frame."""
        self.buf.extend(data)
        out = []
        while True:
            i = self.buf.find(PING_HEADER)
            if i < 0:
                # No header at all. Keep one byte in case 'B' is the last byte
                # received and 'R' arrives next.
                if len(self.buf) > 1:
                    del self.buf[:-1]
                return out
            if i:
                self.resync += 1
                del self.buf[:i]
            if len(self.buf) < 10:              # header+len+id+ids+csum minimum
                return out
            (plen, mid, _src, _dst) = struct.unpack("<HHBB", self.buf[2:8])
            if plen > self.MAX_PAYLOAD:
                # Not a real frame; drop this 'BR' and look for the next.
                self.resync += 1
                del self.buf[:2]
                continue
            total = 8 + plen + 2
            if len(self.buf) < total:
                return out
            frame = bytes(self.buf[:total])
            got = struct.unpack("<H", frame[-2:])[0]
            if got == ping_checksum(frame[:-2]):
                out.append((mid, frame[8:8 + plen]))
                del self.buf[:total]
            else:
                # Bad checksum means this was probably not a frame boundary at
                # all. Skip the header and rescan rather than trusting plen.
                self.csum_err += 1
                del self.buf[:2]


def parse_distance_simple(payload):
    """distance_simple (1212): u32 mm, u8 %. -> (mm, %) or None."""
    if len(payload) < 5:
        return None
    dist, conf = struct.unpack("<IB", payload[:5])
    return dist, conf


def parse_distance(payload):
    """distance (1211) -> (mm, %) or None.

    DISPATCHES ON PAYLOAD LENGTH, NOT ON THE MESSAGE ID, because the hardware
    does not agree with the spec here.

    The documented distance message is 24 bytes - distance u32, confidence
    u16, transmit_duration u16, ping_number u32, scan_start u32, scan_length
    u32, gain_setting u32. The unit on buoy 3 answers id 1211 with FIVE bytes:
    u32 distance + u8 confidence, i.e. the distance_simple layout under the
    distance id. Measured 2026-08-29, e.g.

        frame id 1211 len 5   B3 5C 01 00 1B   ->  89267 mm, conf 27

    An earlier version required 6 bytes and therefore rejected every single
    frame this device sent, reporting "connected, nothing decoded" while the
    sonar was in fact answering every request. Length is the reliable
    discriminator: 5 bytes can only be u32+u8, and 6 or more carries the u16
    confidence of the full message.
    """
    if len(payload) == 5:
        dist, conf = struct.unpack("<IB", payload)
        return dist, conf
    if len(payload) >= 6:
        dist, conf = struct.unpack("<IH", payload[:6])
        return dist, conf
    return None


def parse_general_info(payload):
    """general_info (1210) -> dict, or None.

    Ten bytes: fw_major u16, fw_minor u16, voltage_5 u16 (mV),
    ping_interval u16 (ms), gain_setting u8, mode_auto u8.

    This is the single most useful message for "is the sonar actually
    configured to measure": it reports the ping interval and gain the device is
    really running, not what someone believes they set. Measured on buoy 3 it
    read interval 250 ms, i.e. 4 pings/s, while the host was asking 10x faster
    and simply re-reading the same measurement.
    """
    if len(payload) < 10:
        return None
    maj, minr, mv, interval, gain, auto = struct.unpack("<HHHHBB", payload[:10])
    return {"fw": "%d.%d" % (maj, minr), "voltage_5_mv": mv,
            "ping_interval_ms": interval, "gain_setting": gain,
            "mode_auto": auto}


def set_message(kind, value):
    """Build one setter frame. Mirrors the commands the vendor GUI sends.

    Payload widths follow the Ping1D message set: speed of sound is u32 mm/s,
    ping interval u16 ms, and gain/enable/auto are single bytes.
    """
    if kind == "sos":
        return ping_build(ID_SET_SPEED_OF_SOUND, struct.pack("<I", int(value)))
    if kind == "interval":
        return ping_build(ID_SET_PING_INTERVAL, struct.pack("<H", int(value)))
    if kind == "gain":
        return ping_build(ID_SET_GAIN_SETTING, struct.pack("<B", int(value)))
    if kind == "enable":
        return ping_build(ID_SET_PING_ENABLE, struct.pack("<B", 1 if value else 0))
    if kind == "auto":
        return ping_build(ID_SET_MODE_AUTO, struct.pack("<B", 1 if value else 0))
    raise ValueError("unknown setting %r" % (kind,))


def parse_nack(payload):
    """nack (1) -> (nacked_message_id, text).

    Worth decoding rather than ignoring: a NACK is the device explicitly
    saying it will not answer, and which id it refused. That turns "connected
    but no readings" - which looks identical to a wiring fault - into a
    sentence naming the cause.
    """
    if len(payload) < 2:
        return None, ""
    nacked = struct.unpack("<H", payload[:2])[0]
    txt = payload[2:].split(b"\x00")[0].decode("ascii", "replace").strip()
    return nacked, txt


class PingLink(threading.Thread):
    """Polls one Ping1D over TCP. Reconnects on its own; never raises.

    snapshot() deliberately mirrors gdat2.Link's shape - state, peer, rate,
    counters - so the GUI can render an altimeter and an aux_vcu with the same
    code and the same health rules.
    """

    def __init__(self, host, port=PING_PORT, poll_s=PING_POLL_S,
                 on_frame=None, settings=VENDOR_DEFAULTS):
        super().__init__(daemon=True)
        self.host, self.port, self.poll_s = host, port, poll_s
        # Written to the device once per connection. THIS CHANGES SENSOR STATE,
        # which is why it is a visible argument and not buried in _session.
        #
        # It is on by default because the device's own power-up state is not
        # usable: measured on buoy 3 it boots with ping_interval = 250 ms, so
        # it measures four times a second while the host asks ten times faster
        # and re-reads the same stale result. Confidence sat at 0 and the range
        # wandered 54-92 m. After writing these - which is exactly what the
        # vendor GUI's "Apply Settings" button sends - confidence came up to
        # 22-51 % and the range settled to 91-95 m.
        #
        # Pass settings=None to connect without touching the sensor.
        self.settings = settings
        # Called with (msg_id, payload) for EVERY valid frame, on the link
        # thread. --raw uses it. The point is that a frame which checksums but
        # whose id we do not handle is evidence, not noise: it says the device
        # is alive and talking, and names what it chose to send.
        self.on_frame = on_frame
        self.asked = None           # id currently being requested
        self.answered_id = None     # id that actually replied
        self.nacks = 0
        self.last_nack = ""
        self.other_ids = set()      # ids seen that we do not decode
        self.applied = None         # settings actually written, if any
        self.lock = threading.Lock()
        self.stop = False
        self.sock = None
        self.state = "idle"
        self.peer = ""
        self.dist = None            # mm
        self.conf = None            # %
        self.t = None               # time of the last good reading
        self.good = 0
        self.bad = 0                # checksum failures
        self.timeouts = 0
        self.rate = 0.0
        self._rt0 = time.time()
        self._rn = 0

    def snapshot(self):
        with self.lock:
            return dict(state=self.state, peer=self.peer, dist=self.dist,
                        conf=self.conf, t=self.t, good=self.good, bad=self.bad,
                        timeouts=self.timeouts, rate=self.rate,
                        asked=self.asked, answered_id=self.answered_id,
                        nacks=self.nacks, last_nack=self.last_nack,
                        other_ids=sorted(self.other_ids),
                        applied=self.applied)

    def close(self):
        self.stop = True
        try:
            if self.sock:
                self.sock.close()
        except OSError:
            pass

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
            except Exception as e:
                self._set("error: %r" % e)
            if self.stop:
                return
            self._set("reconnecting")
            for _ in range(20):
                if self.stop:
                    return
                time.sleep(0.1)

    def _session(self):
        self._set("connecting to %s:%d" % (self.host, self.port))
        self.sock = socket.create_connection((self.host, self.port), timeout=3.0)
        self._set("connected", peer="%s:%d" % (self.host, self.port))
        # The recv timeout must not exceed the poll interval. With a 0.5 s
        # timeout and a 50 ms interval the loop blocks in recv until the
        # timeout expires, so requests go out at 2 Hz instead of 20 and the
        # rate reads an order of magnitude low - while everything else about
        # the link looks perfectly healthy.
        # REQUEST / RESPONSE, not fire-and-forget polling.
        #
        # This used to set the recv timeout to the poll interval and re-request
        # on every expiry. That works alone and collapses in company: with the
        # IMU link delivering ~1000 packets/s in the same process, the 50 ms
        # windows get eaten by GIL contention and nearly every request is
        # abandoned before its answer arrives. Measured 1 reading/s inside the
        # GUI against 12-16/s standalone - the sonar was answering fine, this
        # code just was not there to hear it.
        #
        # brping's get_distance(), which the manufacturer's GUI uses, blocks
        # until the reply lands and then asks again. Same here: the timeout is
        # now the time a REPLY may take, and the next request goes out as soon
        # as the last one is answered. That self-paces to whatever the device
        # and the bridge can do instead of guessing.
        self.sock.settimeout(REPLY_TIMEOUT_S)

        # See SETTLE_S. Requests sent before the bridge has opened the serial
        # side are simply lost, and the symptom is a link that connects and
        # never answers - which reads as a dead sensor.
        t_settle = time.time() + SETTLE_S
        self._set("connected, waiting %.0f ms for the serial bridge"
                  % (SETTLE_S * 1000))
        while time.time() < t_settle and not self.stop:
            time.sleep(0.05)
        if self.stop:
            return
        self._set("connected")

        if self.settings:
            # Order follows the vendor GUI: enable first, then the parameters.
            # Spaced out because these go over a 115200 serial bridge and the
            # sonar acknowledges nothing - back-to-back writes can be dropped.
            for key in ("enable", "gain", "interval", "sos"):
                if key in self.settings:
                    try:
                        self.sock.sendall(set_message(key, self.settings[key]))
                    except OSError:
                        break
                    time.sleep(0.25)
            with self.lock:
                self.applied = dict(self.settings)
            time.sleep(0.5)

        par = PingParser()
        # Ask for the id the manufacturer's own GUI uses first, and fall back
        # only if it stays silent. Locking on after the first good reply means
        # a firmware that implements both does not keep alternating.
        idx = 0
        self.asked = DISTANCE_IDS[idx]
        req = ping_request(self.asked)
        last_req = 0.0
        pending = False
        tried_at = time.time()
        try:
            while not self.stop:
                now = time.time()
                # No answer to this id for a while: try the next one. Without
                # this, asking for a message the firmware does not implement
                # looks exactly like a broken cable, forever.
                if self.good == 0 and now - tried_at > 2.0 \
                        and len(DISTANCE_IDS) > 1:
                    idx = (idx + 1) % len(DISTANCE_IDS)
                    self.asked = DISTANCE_IDS[idx]
                    req = ping_request(self.asked)
                    tried_at = now
                    self._set("connected, no reply to %d - trying %d"
                              % (DISTANCE_IDS[idx - 1], self.asked))
                # Ask only when nothing is outstanding, or when the previous
                # request has gone unanswered for long enough to be lost.
                if not pending or (now - last_req) >= REPLY_TIMEOUT_S:
                    last_req = now
                    pending = True
                    self.sock.sendall(req)
                try:
                    d = self.sock.recv(4096)
                except socket.timeout:
                    # With request/response pacing this is a genuine miss: a
                    # request was outstanding for the whole reply window and
                    # nothing came back.
                    if pending:
                        with self.lock:
                            self.timeouts += 1
                        pending = False
                    continue
                if not d:
                    self._set("peer closed")
                    return
                for mid, payload in par.feed(d):
                    if self.on_frame is not None:
                        try:
                            self.on_frame(mid, payload)
                        except Exception:
                            pass
                    if mid == ID_NACK:
                        nacked, txt = parse_nack(payload)
                        with self.lock:
                            self.nacks += 1
                            self.last_nack = "%d: %s" % (nacked, txt or "(no text)")
                        pending = False
                        self._set("NACK on msg %d - %s" % (nacked, txt))
                        continue
                    if mid == ID_DISTANCE:
                        got = parse_distance(payload)
                    elif mid == ID_DISTANCE_SIMPLE:
                        got = parse_distance_simple(payload)
                    else:
                        with self.lock:
                            self.other_ids.add(mid)
                        continue
                    if got is None:
                        continue
                    dist, conf = got
                    pending = False
                    with self.lock:
                        # self.state is written directly, NOT via _set(): we
                        # already hold self.lock and it is a plain Lock, not an
                        # RLock, so _set() here would deadlock the reader
                        # thread on its first successful reading.
                        self.state = "connected"
                        self.answered_id = mid
                        self.dist, self.conf = dist, conf
                        self.t = time.time()
                        self.good += 1
                        self._rn += 1
                        if self.t - self._rt0 >= 0.5:
                            self.rate = self._rn / (self.t - self._rt0)
                            self._rt0, self._rn = self.t, 0
                with self.lock:
                    self.bad = par.csum_err
        finally:
            try:
                self.sock.close()
            except OSError:
                pass
            self.sock = None


class PingSim(threading.Thread):
    """A fake Ping1D, so the GUI path can be proven before the boat.

    Answers general_request(1212) with a moving distance. Also emits an
    occasional corrupt frame, because a parser that has only ever seen clean
    input has not been tested.
    """

    def __init__(self, port=PING_PORT, glitch=True, simple_ok=True,
                 full_ok=True):
        super().__init__(daemon=True)
        self.port, self.glitch, self.stop = port, glitch, False
        self.full_ok = full_ok      # answer distance (1211)?
        # simple_ok=False imitates firmware that implements distance (1211)
        # but not distance_simple (1212), which is the case the id fallback
        # exists for. Being able to reproduce it is the difference between
        # having written that fallback and having tested it.
        self.simple_ok = simple_ok

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
        par = PingParser()
        n = 0
        c.settimeout(0.5)
        try:
            while not self.stop:
                try:
                    d = c.recv(1024)
                except socket.timeout:
                    continue
                if not d:
                    return
                for mid, payload in par.feed(d):
                    if mid != ID_GENERAL_REQUEST:
                        continue
                    want = struct.unpack("<H", payload[:2])[0]
                    n += 1
                    dist = 3000 + (n * 37) % 4000
                    conf = 90 + n % 10
                    if want == ID_DISTANCE and self.full_ok:
                        # Full distance message: the extra fields are sonar
                        # internals, filled with plausible constants so the
                        # payload is the right LENGTH - which is what a decoder
                        # reading only the first six bytes must tolerate.
                        frame = ping_build(ID_DISTANCE, struct.pack(
                            "<IHHIIII", dist, conf, 500, n, 0, 30000, 3))
                    elif want == ID_DISTANCE_SIMPLE and self.simple_ok:
                        frame = ping_build(ID_DISTANCE_SIMPLE,
                                           struct.pack("<IB", dist, conf))
                    else:
                        # Refuse anything else the way real firmware does, so
                        # the NACK path is exercised rather than assumed.
                        frame = ping_build(ID_NACK, struct.pack("<H", want)
                                           + b"not supported\x00")
                    if self.glitch and n % 40 == 0:
                        frame = frame[:-1] + bytes([frame[-1] ^ 0xFF])
                    c.sendall(frame)
        except OSError:
            pass
        finally:
            try:
                c.close()
            except OSError:
                pass


def _selftest():
    # Round trip a frame through the builder and the parser.
    f = ping_build(ID_DISTANCE_SIMPLE, struct.pack("<IB", 4271, 93))
    assert f[:2] == b"BR"
    assert struct.unpack("<H", f[2:4])[0] == 5           # payload length
    assert struct.unpack("<H", f[4:6])[0] == ID_DISTANCE_SIMPLE
    assert len(f) == 8 + 5 + 2
    p = PingParser()
    out = p.feed(f)
    assert out == [(ID_DISTANCE_SIMPLE, struct.pack("<IB", 4271, 93))], out
    assert parse_distance_simple(out[0][1]) == (4271, 93)

    # Split across recv() boundaries, one byte at a time. This is the case that
    # breaks any parser which assumes a recv() is a message.
    p = PingParser()
    got = []
    for i in range(len(f)):
        got += p.feed(f[i:i + 1])
    assert len(got) == 1 and parse_distance_simple(got[0][1]) == (4271, 93)

    # Two frames plus a fragment in one chunk.
    g = ping_build(ID_DISTANCE_SIMPLE, struct.pack("<IB", 1234, 50))
    p = PingParser()
    got = p.feed(f + g + f[:4])
    assert len(got) == 2, got
    assert parse_distance_simple(got[1][1]) == (1234, 50)
    assert p.feed(f[4:]) and True                        # fragment completes

    # Corrupt checksum must be dropped, not decoded.
    p = PingParser()
    bad = f[:-1] + bytes([f[-1] ^ 0xFF])
    assert p.feed(bad) == []
    assert p.csum_err == 1

    # Leading garbage must resynchronise rather than wedge.
    p = PingParser()
    got = p.feed(b"\x00\x01rubbish\xff" + f)
    assert len(got) == 1 and p.resync >= 1

    # A silly length field must not make the parser wait forever for bytes that
    # will never come. This is what a desync looks like on the wire.
    p = PingParser()
    junk = PING_HEADER + struct.pack("<HHBB", 60000, 1212, 0, 0)
    got = p.feed(junk + f)
    assert len(got) == 1, "parser wedged on an implausible length"

    # Short payload is reported as undecodable rather than unpacked blindly.
    assert parse_distance_simple(b"\x01\x02") is None
    assert parse_distance(b"\x01\x02") is None

    # distance (1211): 24-byte payload, confidence is u16 here not u8.
    full = struct.pack("<IHHIIII", 4271, 93, 500, 7, 0, 30000, 3)
    assert len(full) == 24
    assert parse_distance(full) == (4271, 93)
    p = PingParser()
    out = p.feed(ping_build(ID_DISTANCE, full))
    assert out[0][0] == ID_DISTANCE
    assert parse_distance(out[0][1]) == (4271, 93)

    # The two distance messages must NOT be decoded by each other's layout.
    # distance_simple's 5-byte payload read as distance would take two bytes of
    # nothing as the top half of confidence; reading distance as simple takes
    # the low byte of a u16 confidence and calls it the whole field. Both
    # produce a number, which is why they get separate functions.
    assert parse_distance_simple(full) == (4271, 93 & 0xFF)   # coincides here
    other = struct.pack("<IHHIIII", 4271, 300, 500, 7, 0, 30000, 3)
    assert parse_distance(other)[1] == 300
    assert parse_distance_simple(other)[1] == 300 & 0xFF      # 44 - wrong
    assert parse_distance(other)[1] != parse_distance_simple(other)[1]

    # NACK carries the id it refused, which is the whole diagnostic value.
    nid, txt = parse_nack(struct.pack("<H", 1212) + b"not supported\x00")
    assert (nid, txt) == (1212, "not supported"), (nid, txt)
    assert parse_nack(b"") == (None, "")

    print("ping1d self-test OK  (frame build/parse, split reads, resync, "
          "bad checksum, bogus length)")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Ping1D altimeter over TCP")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--buoy", type=int, choices=(1, 2, 3, 4),
                   help="that buoy's altimeter, 192.168.3.1<buoy>2")
    g.add_argument("--connect", metavar="HOST[:PORT]")
    g.add_argument("--sim", action="store_true", help="run a fake Ping1D")
    g.add_argument("--selftest", action="store_true")
    ap.add_argument("--port", type=int, default=PING_PORT)
    ap.add_argument("--raw", action="store_true",
                    help="print every valid frame as id + payload hex. Use "
                         "this when nothing decodes: a frame that checksums "
                         "but is not understood still proves the device is "
                         "alive, and names what it actually sent.")
    ap.add_argument("--no-apply", action="store_true",
                    help="connect WITHOUT writing the vendor settings. The "
                         "device boots at 250 ms ping interval, which reads "
                         "confidence 0 - so this is for inspection, not use.")
    ap.add_argument("--no-sim-simple", action="store_true",
                    help="with --sim: refuse distance_simple, to exercise the "
                         "message-id fallback")
    a = ap.parse_args()

    if a.selftest:
        return _selftest()
    if a.sim:
        s = PingSim(a.port, simple_ok=not a.no_sim_simple)
        s.start()
        print("simulated Ping1D on 0.0.0.0:%d - ctrl-C to stop" % a.port)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            s.stop = True
        return 0

    if a.buoy:
        try:
            import gdat2
            host = gdat2.buoy_ip(a.buoy, 2)
        except ImportError:
            host = "192.168.3.1%d2" % a.buoy
        port = a.port
    elif a.connect:
        host, _, p = a.connect.partition(":")
        port = int(p) if p else a.port
    else:
        ap.print_help()
        return 1

    def dump(mid, payload):
        print("    frame id %-5d len %-3d  %s"
              % (mid, len(payload),
                 " ".join("%02X" % b for b in payload[:32])))

    link = PingLink(host, port, on_frame=dump if a.raw else None,
                    settings=None if a.no_apply else VENDOR_DEFAULTS)
    link.start()
    try:
        while True:
            time.sleep(1.0)
            s = link.snapshot()
            age = "-" if s["t"] is None else "%.1f s" % (time.time() - s["t"])
            print("[%s] %s  %.1f/s  good %d  csum %d  timeouts %d  "
                  "dist %s mm  conf %s  age %s"
                  % (s["state"], s["peer"], s["rate"], s["good"], s["bad"],
                     s["timeouts"], s["dist"], s["conf"], age))
            # Everything below is for the case that actually happens on a
            # boat: it connected and produced nothing. Say what was asked, what
            # came back, and what was refused - otherwise the only information
            # available is "no", which fits every possible cause equally well.
            if s["good"] == 0:
                print("    asked for msg %s, nothing decoded yet"
                      % (s["asked"],))
                if s["nacks"]:
                    print("    device NACKed %d time(s), last %s"
                          % (s["nacks"], s["last_nack"]))
                    print("    -> it IS talking. The message id is wrong for "
                          "this firmware, not the wiring.")
                elif s["other_ids"]:
                    print("    but it sent ids %s - alive, different messages."
                          % (s["other_ids"],))
                    print("    -> re-run with --raw to see them.")
                elif s["state"].startswith("connected"):
                    print("    socket is open and NOTHING has come back. That "
                          "is the serial side of the")
                    print("    bridge, not the network: check it is set to "
                          "115200 baud, and that the")
                    print("    sonar is powered - the bridge accepts TCP "
                          "either way.")
            elif s["answered_id"] is not None:
                print("    answering on msg %d" % s["answered_id"])
    except KeyboardInterrupt:
        link.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
