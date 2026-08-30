#!/usr/bin/env python3
"""
WitMotion IMU/AHRS over TCP - the device at 192.168.3.1<buoy>1.

    python witmotion.py --buoy 3              # 192.168.3.131:8080
    python witmotion.py --connect 192.168.3.131:8080
    python witmotion.py --selftest            # no hardware needed
    python witmotion.py --raw                 # every packet, decoded

WHAT THIS IS, AND HOW IT WAS FOUND
==================================
Role 1 of each buoy - see gdat2.buoy_ip - was assumed to be the aux_vcu and
read with the $GDAT2 decoder, which reported ~300 unparsable sentences per
second and not one good one. Dumping the bytes instead of the text showed why:

    55 51 ...  55 52 ...  55 53 ...  55 54 ...  55 59 ...

That is WitMotion's protocol, not NMEA. Measured on buoy 3, 2026-08-29: 436
packets in one capture, 436 checksum passes, zero rejects, five packet types in
equal counts (~60 Hz each, hence ~300/s total).

The lesson is the one this repo keeps relearning: "the decoder found nothing"
and "the device is silent" look identical from the outside. Only the raw bytes
separate them.

FRAME FORMAT - fixed 11 bytes, no length field
    offset size  field
    0      1     0x55 header
    1      1     packet type
    2      8     four little-endian int16 values
    10     1     checksum = sum of bytes 0..9, truncated to 8 bits

    0x51 acceleration   ax ay az    +temperature
    0x52 angular rate   wx wy wz    +temperature
    0x53 ANGLE          roll pitch yaw  +version
    0x54 magnetic       hx hy hz    +temperature
    0x59 quaternion     q0 q1 q2 q3

SCALING - int16 fraction of full scale
    angle         raw / 32768 * 180      degrees
    acceleration  raw / 32768 * 16       g
    angular rate  raw / 32768 * 2000     deg/s
    quaternion    raw / 32768            unit
    magnetic      raw                    device units, uncalibrated

NOTE the aux_vcu at role 0 RELAYS this unit's attitude into $GDAT2 fields 4-6.
Measured simultaneously: GDAT2 AHRS Roll 2.1000 deg, this IMU roll +2.10 deg.
So the two are not independent measurements - if attitude looks wrong here, it
will look wrong there too, and vice versa.
"""

import argparse
import socket
import struct
import sys
import threading
import time

WIT_PORT = 8080
WIT_HEADER = 0x55

WIT_ACCEL = 0x51
WIT_GYRO = 0x52
WIT_ANGLE = 0x53
WIT_MAG = 0x54
WIT_QUAT = 0x59

WIT_NAMES = {0x50: "time", WIT_ACCEL: "accel", WIT_GYRO: "gyro",
             WIT_ANGLE: "angle", WIT_MAG: "mag", 0x55: "port",
             0x56: "baro", 0x57: "gps", 0x58: "gps-vel", WIT_QUAT: "quat",
             0x5A: "gps-acc"}

WIT_PACKET_LEN = 11

# Same purpose as gdat2.PLAUSIBLE: a value outside these is shown as suspect
# rather than drawn as a measurement. Pitch is +/-90 by convention; anything
# beyond that is a convention error, not an attitude.
ANGLE_LIMITS = ((-180.0, 180.0), (-90.0, 90.0), (-180.0, 360.0))


# ---------------------------------------------------------------- heading ---
# What each unit READS while its bow is physically pointed north. Subtracting
# it turns raw yaw into a compass heading.
#
# PER BUOY, not one global constant. This is not a property of the sensor, it
# is the sum of how the IMU happens to be bolted into that hull and what
# ferrous metal sits near it - so two units on the same bench will not share a
# value, and a global number would be wrong the moment the second one is
# calibrated.
#
#   buoy 3: measured -12.4 deg, 2026-08-29
#
# TO CALIBRATE: point the bow at north, read the RAW yaw (the compass caption
# shows it in brackets, or `python witmotion.py --buoy N`), and put that number
# here. Whether you sight true or magnetic north only decides what the
# corrected heading then means - the arithmetic is the same either way, so
# write down which one you used.
HEADING_OFFSET_DEG = {1: 0.0, 2: 0.0, 3: -12.4, 4: 0.0}


def heading(yaw, buoy=None, offset=None):
    """Raw yaw -> corrected compass heading in [0, 360).

    Wrapping is the whole reason this is a function. The offset pushes readings
    across the +/-180 seam that raw yaw uses, so a buoy near north reads -12.4
    one moment and +347 the next; taking it modulo 360 makes the number
    continuous around the circle and puts it in the range a heading is normally
    quoted in.
    """
    if offset is None:
        offset = HEADING_OFFSET_DEG.get(buoy, 0.0) if buoy else 0.0
    return (yaw - offset) % 360.0


# What each unit reads for (roll, pitch) while it is physically LEVEL.
# Subtracting it zeroes the horizon.
#
# Per buoy for the same reason as the heading offset: this is how the IMU is
# bolted into that particular hull, not a property of the sensor.
#
#   buoy 3: roll +2.15, pitch -4.66, measured 2026-08-29 over 1215 angle
#           packets - stdev 0.000 and 0.002 deg, so these are a real mounting
#           tilt and not noise being frozen into a constant.
#
# TO CALIBRATE: sit the buoy level, average a few seconds of raw roll and pitch
# (`python witmotion.py --buoy N`), and put them here.
#
# SMALL-ANGLE CORRECTION, deliberately. Strictly, a mounting misalignment is a
# rotation, and undoing it means rotating the gravity vector rather than
# subtracting two numbers - at large tilts roll and pitch interact and plain
# subtraction drifts. For the few degrees seen here the error is second order
# and far below what the display resolves. If a unit is ever mounted at a
# serious angle, this is the assumption that breaks.
LEVEL_OFFSET_DEG = {1: (0.0, 0.0), 2: (0.0, 0.0),
                    3: (2.15, -4.66), 4: (0.0, 0.0)}


def level(roll, pitch, buoy=None, offset=None):
    """Raw (roll, pitch) -> levelled, in degrees.

    Roll is wrapped back into [-180, 180) because the offset can push a reading
    across the seam; pitch is left alone, since it is physically bounded to
    +/-90 and wrapping it would turn an implausible value into a plausible one
    and hide the fault.
    """
    if offset is None:
        offset = LEVEL_OFFSET_DEG.get(buoy, (0.0, 0.0)) if buoy else (0.0, 0.0)
    r = ((roll - offset[0] + 180.0) % 360.0) - 180.0
    return r, pitch - offset[1]


def wit_checksum(pkt10):
    """Sum of the first ten bytes, low 8 bits."""
    return sum(pkt10) & 0xFF


def wit_build(ptype, vals):
    """Encode one packet. Used by the self-test and the simulator."""
    body = bytes([WIT_HEADER, ptype]) + struct.pack("<hhhh", *vals)
    return body + bytes([wit_checksum(body)])


def wit_decode(ptype, raw):
    """(type, four int16) -> dict of named, scaled values.

    Returns raw device units for magnetics because the scaling is
    calibration-dependent and inventing one would produce a confident number
    that means nothing.
    """
    a, b, c, d = raw
    if ptype == WIT_ANGLE:
        return {"roll": a / 32768.0 * 180.0, "pitch": b / 32768.0 * 180.0,
                "yaw": c / 32768.0 * 180.0, "version": d & 0xFFFF}
    if ptype == WIT_ACCEL:
        return {"ax": a / 32768.0 * 16.0, "ay": b / 32768.0 * 16.0,
                "az": c / 32768.0 * 16.0, "temp_raw": d}
    if ptype == WIT_GYRO:
        return {"wx": a / 32768.0 * 2000.0, "wy": b / 32768.0 * 2000.0,
                "wz": c / 32768.0 * 2000.0, "temp_raw": d}
    if ptype == WIT_QUAT:
        return {"q0": a / 32768.0, "q1": b / 32768.0,
                "q2": c / 32768.0, "q3": d / 32768.0}
    if ptype == WIT_MAG:
        return {"hx": a, "hy": b, "hz": c, "temp_raw": d}
    return {"v0": a, "v1": b, "v2": c, "v3": d}


class WitParser(object):
    """Incremental reassembly for a protocol with NO length field.

    That absence is the whole difficulty. Every packet is 11 bytes, so framing
    depends entirely on finding a real 0x55 - and 0x55 occurs inside payload
    data all the time. The checksum is therefore not a nicety here, it is the
    only thing that distinguishes a frame boundary from a coincidence, so a
    candidate that fails it advances by ONE byte rather than eleven.
    """

    def __init__(self):
        self.buf = bytearray()
        self.csum_err = 0

    def feed(self, data):
        """-> list of (ptype, (v0,v1,v2,v3)) for every valid packet."""
        self.buf.extend(data)
        out = []
        i = 0
        n = len(self.buf)
        while i + WIT_PACKET_LEN <= n:
            if self.buf[i] != WIT_HEADER:
                i += 1
                continue
            pkt = self.buf[i:i + WIT_PACKET_LEN]
            if wit_checksum(pkt[:10]) != pkt[10]:
                # A 0x55 that is payload, not a header. One byte, not eleven.
                self.csum_err += 1
                i += 1
                continue
            out.append((pkt[1], struct.unpack("<hhhh", bytes(pkt[2:10]))))
            i += WIT_PACKET_LEN
        del self.buf[:i]
        # Never let an unframeable stream grow without bound.
        if len(self.buf) > 4096:
            del self.buf[:-64]
        return out


class WitLink(threading.Thread):
    """Reads one WitMotion IMU over TCP. Reconnects; never raises.

    snapshot() mirrors gdat2.Link and ping1d.PingLink so all three devices can
    be rendered by the same code under the same health rules.
    """

    def __init__(self, host, port=WIT_PORT, on_packet=None):
        super().__init__(daemon=True)
        self.host, self.port = host, port
        self.on_packet = on_packet
        self.lock = threading.Lock()
        self.stop = False
        self.sock = None
        self.state = "idle"
        self.peer = ""
        self.angle = None           # dict from wit_decode, or None
        self.accel = None
        self.gyro = None
        self.quat = None
        self.t = None
        self.good = 0
        self.bad = 0
        self.rate = 0.0
        self._rt0 = time.time()
        self._rn = 0

    def snapshot(self):
        with self.lock:
            return dict(state=self.state, peer=self.peer, angle=self.angle,
                        accel=self.accel, gyro=self.gyro, quat=self.quat,
                        t=self.t, good=self.good, bad=self.bad, rate=self.rate)

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
        self.sock.settimeout(0.5)
        par = WitParser()
        try:
            while not self.stop:
                try:
                    d = self.sock.recv(4096)
                except socket.timeout:
                    continue
                if not d:
                    self._set("peer closed")
                    return
                frames = par.feed(d)
                if not frames:
                    continue

                # DECODE ONLY THE NEWEST OF EACH TYPE, and take the lock once.
                #
                # This unit sends ~1000 packets/s. Decoding every one into its
                # own dict, and locking per packet, is a thousand allocations
                # and a thousand lock round-trips a second spent producing
                # values that are immediately overwritten - nothing reads any
                # but the last. Under the GIL that cost is not paid by this
                # thread alone: it starved the altimeter link in the same
                # process down to 1 reading/s.
                #
                # on_packet still sees every packet, because --raw exists to
                # show exactly what arrives; that path is opt-in and off in the
                # GUI.
                if self.on_packet is not None:
                    for ptype, raw in frames:
                        try:
                            self.on_packet(ptype, wit_decode(ptype, raw))
                        except Exception:
                            pass

                latest = {}
                for ptype, raw in frames:
                    latest[ptype] = raw

                decoded = dict((pt, wit_decode(pt, rw))
                               for pt, rw in latest.items())
                with self.lock:
                    if WIT_ANGLE in decoded:
                        self.angle = decoded[WIT_ANGLE]
                    if WIT_ACCEL in decoded:
                        self.accel = decoded[WIT_ACCEL]
                    if WIT_GYRO in decoded:
                        self.gyro = decoded[WIT_GYRO]
                    if WIT_QUAT in decoded:
                        self.quat = decoded[WIT_QUAT]
                    self.t = time.time()
                    # Counted per PACKET, not per batch, so the rate still
                    # reports what the device is really sending.
                    self.good += len(frames)
                    self._rn += len(frames)
                    if self.t - self._rt0 >= 0.5:
                        self.rate = self._rn / (self.t - self._rt0)
                        self._rt0, self._rn = self.t, 0
                    self.bad = par.csum_err
        finally:
            try:
                self.sock.close()
            except OSError:
                pass
            self.sock = None


def _selftest():
    # The exact packet captured from buoy 3, 2026-08-29.
    real = bytes.fromhex("55537F01D6FC584CFF46E3")
    assert len(real) == WIT_PACKET_LEN
    assert wit_checksum(real[:10]) == real[10] == 0xE3

    p = WitParser()
    out = p.feed(real)
    assert len(out) == 1 and out[0][0] == WIT_ANGLE
    a = wit_decode(*out[0])
    assert abs(a["roll"] - 2.1039) < 1e-3, a["roll"]
    assert abs(a["pitch"] + 4.4494) < 1e-3, a["pitch"]
    assert abs(a["yaw"] - 107.3584) < 1e-3, a["yaw"]

    # Split one byte at a time - a recv() boundary must not lose a packet.
    p = WitParser()
    got = []
    for i in range(len(real)):
        got += p.feed(real[i:i + 1])
    assert len(got) == 1

    # Leading garbage, including a bare 0x55 that is NOT a header. With no
    # length field this is the case that separates a real parser from a broken
    # one: advancing 11 bytes on a checksum failure would swallow the genuine
    # packet that follows.
    p = WitParser()
    got = p.feed(b"\x55\x00\x11\x22" + real)
    assert len(got) == 1, got
    assert p.csum_err >= 1

    # Round trip through the builder, and a negative value.
    enc = wit_build(WIT_ANGLE, (383, -810, 19544, 18175))
    assert enc == real, (enc.hex(), real.hex())
    p = WitParser()
    d = wit_decode(*p.feed(enc)[0])
    assert abs(d["yaw"] - 107.3584) < 1e-3

    # Two packets plus a fragment in one chunk.
    q = wit_build(WIT_QUAT, (16384, 0, 0, 0))
    p = WitParser()
    got = p.feed(real + q + real[:5])
    assert len(got) == 2
    assert abs(wit_decode(*got[1])["q0"] - 0.5) < 1e-6
    assert len(p.feed(real[5:])) == 1        # fragment completes

    # A corrupt packet is dropped, not decoded.
    p = WitParser()
    bad = real[:10] + bytes([real[10] ^ 0xFF])
    assert p.feed(bad) == []
    assert p.csum_err >= 1

    # Heading correction. The measured case is the one that matters: buoy 3
    # reading -12.4 while pointed north must correct to 0, not to 347.6.
    assert abs(heading(-12.4, buoy=3) - 0.0) < 1e-6, heading(-12.4, buoy=3)
    assert abs(heading(104.9, buoy=3) - 117.3) < 1e-6
    assert abs(heading(0.0, buoy=3) - 12.4) < 1e-6
    # Uncalibrated buoys pass straight through, wrapped into [0, 360).
    assert abs(heading(-90.0, buoy=1) - 270.0) < 1e-6
    assert abs(heading(-90.0) - 270.0) < 1e-6
    # Every output is a legal heading, including across the seam.
    for y in (-180.0, -179.9, -12.4, 0.0, 179.9, 180.0):
        h = heading(y, buoy=3)
        assert 0.0 <= h < 360.0, (y, h)
    assert abs(heading(175.0, buoy=3) - 187.4) < 1e-6      # wraps past 180

    # Level correction. The measured case: buoy 3 sitting level reads
    # +2.15 / -4.66, and must come out at zero.
    r, pch = level(2.15, -4.66, buoy=3)
    assert abs(r) < 1e-9 and abs(pch) < 1e-9, (r, pch)
    # A real tilt still shows through, reduced by the offset.
    r, pch = level(12.15, 5.34, buoy=3)
    assert abs(r - 10.0) < 1e-9 and abs(pch - 10.0) < 1e-9, (r, pch)
    # Uncalibrated buoys pass straight through.
    assert level(3.0, -4.0, buoy=1) == (3.0, -4.0)
    assert level(3.0, -4.0) == (3.0, -4.0)
    # Roll wraps at the seam rather than reading 181 degrees.
    r, _ = level(-179.0, 0.0, buoy=3)
    assert -180.0 <= r < 180.0 and abs(r - 178.85) < 1e-6, r
    # Pitch is NOT wrapped: an implausible value must stay implausible.
    _, pch = level(0.0, 95.0, buoy=3)
    assert pch > 90.0, pch

    print("witmotion self-test OK  (real captured frame, split reads, "
          "false 0x55 resync, bad checksum, heading + level offsets)")
    return 0


def main():
    ap = argparse.ArgumentParser(description="WitMotion IMU over TCP")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--buoy", type=int, choices=(1, 2, 3, 4))
    g.add_argument("--connect", metavar="HOST[:PORT]")
    g.add_argument("--selftest", action="store_true")
    ap.add_argument("--port", type=int, default=WIT_PORT)
    ap.add_argument("--raw", action="store_true", help="print every packet")
    a = ap.parse_args()

    if a.selftest:
        return _selftest()
    if a.buoy:
        try:
            import gdat2
            host = gdat2.buoy_ip(a.buoy, gdat2.ROLE_IMU)
        except ImportError:
            host = "192.168.3.1%d1" % a.buoy
        port = a.port
    elif a.connect:
        host, _, p = a.connect.partition(":")
        port = int(p) if p else a.port
    else:
        ap.print_help()
        return 1

    def dump(ptype, vals):
        print("    %-5s %s" % (WIT_NAMES.get(ptype, "0x%02X" % ptype),
                               " ".join("%s=%.3f" % (k, v)
                                        if isinstance(v, float) else
                                        "%s=%s" % (k, v)
                                        for k, v in sorted(vals.items()))))

    link = WitLink(host, port, on_packet=dump if a.raw else None)
    link.start()
    try:
        while True:
            time.sleep(1.0)
            s = link.snapshot()
            age = "-" if s["t"] is None else "%.1f s" % (time.time() - s["t"])
            ang = s["angle"]
            print("[%s] %s  %.0f pkt/s  good %d  csum %d  age %s"
                  % (s["state"], s["peer"], s["rate"], s["good"], s["bad"], age))
            if ang:
                print("    roll %+8.2f   pitch %+8.2f   yaw %+8.2f  deg"
                      % (ang["roll"], ang["pitch"], ang["yaw"]))
            if s["accel"]:
                ac = s["accel"]
                print("    accel %+6.3f %+6.3f %+6.3f g"
                      % (ac["ax"], ac["ay"], ac["az"]))
    except KeyboardInterrupt:
        link.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
