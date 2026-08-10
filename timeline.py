#!/usr/bin/env python3
"""
Per-second channel timeline for the TDM_UATR soundcard.

    python timeline.py                 10 windows of 1 s
    python timeline.py --seconds 30
    python timeline.py --window 0.25   finer, for fast flicker

udp_monitor.py gives one number per channel over a whole capture, which hides
intermittency - a channel that is live for half the window and dead for the
other half just looks quiet. mixer_gui.py shows it live but a meter is hard to
read for pattern and impossible to quote. This bins the same capture into
fixed windows and prints one column per window, so a channel that comes and
goes is visible as a pattern rather than an average.

Each cell is that channel's RMS in dBFS for that window:

    -44     live, with the level
    ~       LSB dither only, below -120 dBFS: the ADC drives the bus but
            converts nothing
    .       exactly zero every sample: nothing driving that slot at all

The last column classifies the channel across the whole run. INTERMITTENT is
the one that matters - it means the slot genuinely stops and restarts, which an
averaged capture cannot distinguish from a low level.

Packets per window are printed underneath. If a window is short of packets the
figures in it are computed from less data and a drop there may be the host, not
the board - check that row before believing a gap.
"""

import argparse
import os
import socket
import struct
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import udp_monitor as um
import ctrl

OWNER = ["U19"] * 4 + ["U20"] * 4 + ["U37"] * 4 + ["U38"] * 4
ADDR = ["0x11"] * 4 + ["0x31"] * 4 + ["0x51"] * 4 + ["0x71"] * 4

SILENT_DB = -120.0          # LSB dither only


def capture(port, bind, seconds, window):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 64 << 20)
    except OSError:
        pass
    s.bind((bind, port))
    s.settimeout(0.5)

    nbin = int(round(seconds / window))
    bins = [[] for _ in range(nbin)]
    counts = [0] * nbin
    seqs = []
    t0 = None
    print("capturing %.0f s in %d windows of %.2f s ..." % (seconds, nbin, window))
    while True:
        try:
            d = s.recv(2048)
        except socket.timeout:
            if t0 is None:
                break
            if time.time() - t0 >= seconds:
                break
            continue
        if len(d) < um.PAYLOAD_LEN or d[:4] != um.MAGIC:
            continue
        now = time.time()
        if t0 is None:
            t0 = now
        k = int((now - t0) / window)
        if k >= nbin:
            break
        counts[k] += 1
        seqs.append(struct.unpack(">I", d[4:8])[0])
        bins[k].append(d)
    s.close()
    return bins, counts, seqs


def rms_db(blocks):
    """(rms_dbfs, all_exact_zero, fraction_of_samples_that_are_zero).

    The zero FRACTION is what matters, not just all-or-nothing. A window is
    24000 samples at 96 kHz, so np.all(x == 0) is only true if the part was
    silent for the entire quarter second. A part that drops out for 50 ms inside
    the window still left 200 ms of audio, so it counted as fully live and the
    channel was reported "steady" - while a level meter updating every 10 ms
    plainly showed it cutting in and out. That understated U19 for a long time.
    """
    if not blocks:
        return None, False, None
    x = np.concatenate(blocks, axis=0).astype(np.float64)
    zero = np.all(x == 0, axis=0)
    zfrac = np.mean(x == 0, axis=0)
    r = np.sqrt(np.mean(x * x, axis=0))
    db = np.where(r > 0, 20.0 * np.log10(np.maximum(r, 1e-12) / um.FULL_SCALE), -999.0)
    return db, zero, zfrac


def main():
    ap = argparse.ArgumentParser(description="per-second channel timeline")
    ap.add_argument("--port", type=int, default=5005)
    ap.add_argument("--bind", default="0.0.0.0")
    ap.add_argument("--seconds", type=float, default=10.0)
    ap.add_argument("--window", type=float, default=1.0)
    a = ap.parse_args()

    bins, counts, seqs = capture(a.port, a.bind, a.seconds, a.window)
    n = len(bins)
    if not any(counts):
        print("no packets received - is the board streaming?")
        sys.exit(2)

    cols, zeros, zfracs = [], [], []
    for b in bins:
        db, z, zf = rms_db([blk for blk in (ctrl.decode(d) for d in b)
                            if blk is not None])
        cols.append(db)
        zeros.append(z)
        zfracs.append(zf)

    # 40 columns at 6 chars each overruns any normal terminal and the cells run
    # together, so print in blocks that fit.
    PER = 16
    exp = max(seqs) - min(seqs) + 1 if seqs else 0
    lost = exp - len(seqs) if exp else 0
    print()
    print("CHANNEL TIMELINE   %d x %.2f s      %d packets, %d lost (%.2f%%)"
          % (n, a.window, len(seqs), lost, 100.0 * lost / exp if exp else 0))

    def cell(c, k):
        db = cols[k]
        if db is None:
            return "%5s" % "?"
        if zeros[k][c]:
            return "%5s" % "."
        if db[c] < SILENT_DB:
            return "%5s" % "~"
        # partially silent: show how much of the window was zero. This is the
        # case the old all-or-nothing test could not see at all.
        if zfracs[k] is not None and zfracs[k][c] > 0.02:
            return "%4.0f%%" % (100.0 * zfracs[k][c])
        return "%5.0f" % db[c]

    # "live" now also requires the window to be free of partial silence. A
    # channel that streams for 200 ms and drops for 50 ms is not steady, and
    # counting it as such is what made timeline disagree with the level meter.
    live = [sum(1 for k in range(n)
                if cols[k] is not None and not zeros[k][c]
                and cols[k][c] >= SILENT_DB
                and (zfracs[k] is None or zfracs[k][c] <= 0.02))
            for c in range(um.CHANNELS)]
    # worst partial-silence fraction seen on each channel, for the verdict
    worst_z = [max((zfracs[k][c] for k in range(n)
                    if zfracs[k] is not None and not zeros[k][c]), default=0.0)
               for c in range(um.CHANNELS)]

    for lo in range(0, n, PER):
        hi = min(n, lo + PER)
        w = 5 * (hi - lo)
        print()
        print("  windows %d-%d" % (lo + 1, hi))
        print("  ch  ADC   " + "".join("%5d" % (i + 1) for i in range(lo, hi)))
        print("  " + "-" * (10 + w))
        for c in range(um.CHANNELS):
            print("  %2d  %-4s %s" % (c + 1, OWNER[c],
                                      "".join(cell(c, k) for k in range(lo, hi))))
        print("  pkts     " + "".join("%5d" % counts[k] for k in range(lo, hi)))

    print()
    print("  VERDICT")
    for c in range(um.CHANNELS):
        if live[c] == 0:
            allz = all(zeros[k][c] for k in range(n) if cols[k] is not None)
            v = "dead - nothing drives the slot" if allz else "silent - dither only"
        elif live[c] == n:
            v = "steady"
        else:
            v = "*** INTERMITTENT %d/%d ***" % (live[c], n)
            if worst_z[c] > 0.02:
                v += "   (up to %.0f%% of a window silent - sub-window"                      " dropouts)" % (100.0 * worst_z[c])
        print("  %2d  %-4s %-5s %s" % (c + 1, OWNER[c], ADDR[c], v))
    print()
    print("  NN% = that percentage of the window was exactly zero, i.e. the part")
    print("        dropped out INSIDE the window. A quarter second is 24000")
    print("        samples at 96 kHz, so a 50 ms dropout used to be invisible.")
    print("  . = every sample exactly zero    ~ = dither only, below %.0f dBFS"
          % SILENT_DB)
    print("  Check the pkts row before reading a gap as board behaviour - a")
    print("  window short of packets is the host dropping them, not the ADC.")


if __name__ == "__main__":
    main()
