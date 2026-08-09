#!/usr/bin/env python3
"""
Live 16-channel meter for the TDM_UATR hydrophone soundcard.

A mixer-style view that updates continuously, for the jobs udp_monitor.py is
awkward at: tapping a hydrophone and seeing which channel moves, checking that
a gain change did what you expected, watching for intermittent dropouts.

    python mixer.py                 default, 15 fps
    python mixer.py --fps 25
    python mixer.py --peak-hold 3   seconds before the peak marker decays
    python mixer.py --port 5005 --bind 0.0.0.0

Ctrl-C to quit.

Packet geometry and the sample rate come from udp_monitor.py, so the two
cannot drift apart - change it there and both follow. check_sync.py already
verifies udp_monitor against the RTL.

Reading the display
    PEAK   loudest sample in the last window, dBFS. 0.0 means clipping.
    RMS    average level, dBFS. This is what you judge a noise floor by.
    the bar shows RMS, the marker shows held peak.

    SILENT      RMS below -120 dBFS. With inputs open this is normal; with a
                hydrophone connected and phantom on it means no signal path.
    CLIP        peak at full scale. Open XLRs with 48 V on them do this and it
                means nothing - only trust it on a connected channel.
"""

import argparse
import os
import socket
import struct
import sys
import time

import numpy as np

# geometry from the existing decoder, so there is one definition of the packet
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import udp_monitor as um

# which ADC owns which channels - matches adau_sequencer's get_i2c_addr and the
# CMAP slot patch, and is verified against the netlist address straps.
OWNER = ([("U19", "0x11")] * 4 + [("U20", "0x31")] * 4 +
         [("U37", "0x51")] * 4 + [("U38", "0x71")] * 4)

BAR_W = 44
DB_LO = -100.0          # left edge of the meter


def enable_ansi():
    """Windows consoles need VT processing turned on explicitly."""
    if os.name != "nt":
        return
    try:
        import ctypes
        k = ctypes.windll.kernel32
        h = k.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if k.GetConsoleMode(h, ctypes.byref(mode)):
            k.SetConsoleMode(h, mode.value | 0x0004)
    except Exception:
        pass


def dbfs(v):
    return -999.0 if v <= 0 else 20.0 * np.log10(v / um.FULL_SCALE)


def decode(payload):
    """Payload bytes -> (frames, 16) int32. Mirrors udp_monitor.parse()."""
    body = payload[um.HDR_LEN:]
    n = len(body) // um.FRAME_LEN
    if n == 0:
        return None
    raw = np.frombuffer(body[:n * um.FRAME_LEN], dtype=np.uint8)
    raw = raw.reshape(n, um.FRAME_LEN)[:, 2:]          # drop debug + frame index
    raw = raw.reshape(n, um.CHANNELS, um.SAMPLE_BYTES).astype(np.int32)
    # 24-bit big-endian signed
    v = (raw[:, :, 0] << 16) | (raw[:, :, 1] << 8) | raw[:, :, 2]
    return np.where(v & 0x800000, v - 0x1000000, v)


def bar(db, held, clipped, silent):
    if silent:
        return "\x1b[90m" + "-" * BAR_W + "\x1b[0m"
    span = -DB_LO
    fill = 0 if db <= DB_LO else min(BAR_W, int((db - DB_LO) / span * BAR_W))
    mark = None
    if held > DB_LO:
        mark = min(BAR_W - 1, int((held - DB_LO) / span * BAR_W))
    cells = []
    for i in range(BAR_W):
        frac = i / BAR_W
        colour = "\x1b[32m" if frac < 0.75 else ("\x1b[33m" if frac < 0.92 else "\x1b[31m")
        if i == mark:
            cells.append("\x1b[97m|\x1b[0m")
        elif i < fill:
            cells.append(colour + "#" + "\x1b[0m")
        else:
            cells.append("\x1b[90m.\x1b[0m")
    s = "".join(cells)
    return s + ("  \x1b[91mCLIP\x1b[0m" if clipped else "")


def main():
    ap = argparse.ArgumentParser(description="live 16-channel meter")
    ap.add_argument("--port", type=int, default=5005)
    ap.add_argument("--bind", default="0.0.0.0")
    ap.add_argument("--fps", type=float, default=15.0)
    ap.add_argument("--peak-hold", type=float, default=2.0,
                    help="seconds the peak marker holds before decaying")
    a = ap.parse_args()

    enable_ansi()

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 64 << 20)
    except OSError:
        pass
    s.bind((a.bind, a.port))
    s.settimeout(0.2)

    period = 1.0 / a.fps
    held = np.full(um.CHANNELS, -999.0)
    held_at = np.zeros(um.CHANNELS)
    acc = []
    pkts = seq_prev = lost = 0
    t_win = t_rate = time.time()
    pps = 0.0
    first = True

    print("\x1b[2J", end="")
    try:
        while True:
            try:
                d, _ = s.recvfrom(2048)
            except socket.timeout:
                d = None
            if d and len(d) >= um.PAYLOAD_LEN and d[:4] == um.MAGIC:
                pkts += 1
                seq = struct.unpack(">I", d[4:8])[0]
                if seq_prev and seq > seq_prev + 1:
                    lost += seq - seq_prev - 1
                seq_prev = seq
                blk = decode(d)
                if blk is not None:
                    acc.append(blk)

            now = time.time()
            if now - t_rate >= 1.0:
                pps = pkts / (now - t_rate)
                pkts = 0
                t_rate = now
            if now - t_win < period:
                continue
            t_win = now

            if acc:
                x = np.concatenate(acc, axis=0).astype(np.float64)
                acc = []
                rms = np.sqrt(np.mean(x * x, axis=0))
                pk = np.max(np.abs(x), axis=0)
            else:
                rms = np.zeros(um.CHANNELS)
                pk = np.zeros(um.CHANNELS)

            rms_db = np.array([dbfs(v) for v in rms])
            pk_db = np.array([dbfs(v) for v in pk])
            for i in range(um.CHANNELS):
                if pk_db[i] > held[i] or now - held_at[i] > a.peak_hold:
                    held[i] = pk_db[i]
                    held_at[i] = now

            out = ["\x1b[H"]
            out.append("\x1b[1mUATR 16-CHANNEL LIVE MIXER\x1b[0m   "
                       "%d Hz   %.0f pkt/s   lost %d   \x1b[90mCtrl-C to quit\x1b[0m\x1b[K"
                       % (um.SAMPLE_RATE, pps, lost))
            out.append("\x1b[K")
            out.append("\x1b[90m ch  ADC   addr     rms     peak   %s%s\x1b[0m\x1b[K"
                       % ("-100".ljust(BAR_W // 2), "0".rjust(BAR_W // 2)))
            for i in range(um.CHANNELS):
                who, addr = OWNER[i]
                silent = rms_db[i] < -120
                clipped = pk[i] >= um.FULL_SCALE - 1
                out.append(" %2d  %-4s %-6s %7s %7s  %s\x1b[K"
                           % (i + 1, who, addr,
                              "  -inf" if silent else "%6.1f" % rms_db[i],
                              "  -inf" if silent else "%6.1f" % pk_db[i],
                              bar(rms_db[i], held[i], clipped, silent)))
                if i in (3, 7, 11):
                    out.append("\x1b[90m" + " " * 4 + "-" * (BAR_W + 30) + "\x1b[0m\x1b[K")
            out.append("\x1b[K")
            out.append("\x1b[90mbar = RMS, white marker = held peak. "
                       "CLIP on an open XLR with phantom on is meaningless.\x1b[0m\x1b[K")
            sys.stdout.write("\n".join(out))
            sys.stdout.flush()
            first = False
    except KeyboardInterrupt:
        print("\x1b[0m\n")


if __name__ == "__main__":
    main()
