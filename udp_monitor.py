#!/usr/bin/env python3
"""
TDM_UATR receive-side monitor.

Captures the FPGA's UDP audio stream, then reports link throughput, packet loss
and per-channel audio quality. Standard library only.

    python udp_monitor.py                 # 5 second capture, full report
    python udp_monitor.py -s 10           # longer capture
    python udp_monitor.py --wav out       # also write out_ch01.wav .. out_ch16.wav
    python udp_monitor.py --align         # scan for TDM bit-alignment offset

Packet format produced by packet_formatter.vhd (410 byte payload):
    header, 10 bytes   AD A1 97 78 | seq_num(4, BE) | frame_count(2, BE) = 8
    then 8 frames of 50 bytes each:
        frame_index(2, BE) | 48 bytes audio
    the 48 bytes are 16 channels x 24-bit signed big-endian, channel 1 first
"""

import argparse
import math
import socket
import struct
import sys
import time
import wave

MAGIC        = bytes([0xAD, 0xA1, 0x97, 0x78])
HDR_LEN      = 10
FRAME_LEN    = 50
FRAMES_PKT   = 8
PAYLOAD_LEN  = HDR_LEN + FRAMES_PKT * FRAME_LEN      # 410
WIRE_LEN     = 452                                    # incl. eth+ip+udp headers
CHANNELS     = 16
SAMPLE_BYTES = 3
FULL_SCALE   = 1 << 23                                # 24-bit signed
SAMPLE_RATE   = 96000
EXPECTED_PPS = SAMPLE_RATE / FRAMES_PKT               # 6000 at 48 kHz


# ----------------------------------------------------------------- capture ---
def capture(port, seconds, bind):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:                       # big buffer so the kernel does not drop on us
        s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 64 << 20)
    except OSError:
        pass
    actual = s.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
    s.bind((bind, port))
    s.settimeout(3.0)

    print("listening on %s:%d for %.1f s  (rcvbuf %.1f MB)"
          % (bind or "0.0.0.0", port, seconds, actual / 1e6))

    pkts = []
    try:
        first = s.recv(2048)
    except socket.timeout:
        print("\nNo packets received in 3 s.")
        print("  - is the FPGA powered and the link up?")
        print("  - is this PC on 192.168.1.0/24?")
        print("  - Windows Firewall will silently drop inbound UDP: allow python,")
        print("    or test with the firewall off on the private profile.")
        return None, 0.0
    pkts.append(first)

    t0 = time.perf_counter()
    deadline = t0 + seconds
    while time.perf_counter() < deadline:
        try:
            pkts.append(s.recv(2048))
        except socket.timeout:
            break
    elapsed = time.perf_counter() - t0
    s.close()
    return pkts, elapsed


# ------------------------------------------------------------------ parse ----
def parse(pkts):
    """-> (samples[ch][n], stats dict). samples are ints, -2^23..2^23-1"""
    samples = [[] for _ in range(CHANNELS)]
    seqs = []
    bad_magic = bad_len = bad_index = 0

    for p in pkts:
        if len(p) != PAYLOAD_LEN:
            bad_len += 1
            continue
        if p[0:4] != MAGIC:
            bad_magic += 1
            continue
        seqs.append(struct.unpack(">I", p[4:8])[0])

        off = HDR_LEN
        for f in range(FRAMES_PKT):
            # byte 0 of each frame is the I2C status byte, byte 1 the index
            if p[off + 1] != f:
                bad_index += 1
            a = off + 2
            for c in range(CHANNELS):
                b = a + c * SAMPLE_BYTES
                samples[c].append(
                    int.from_bytes(p[b:b + SAMPLE_BYTES], "big", signed=True))
            off += FRAME_LEN

    return samples, {"seqs": seqs, "bad_magic": bad_magic,
                     "bad_len": bad_len, "bad_index": bad_index}


def loss_report(seqs):
    """-> (expected, received, lost, resets)"""
    if len(seqs) < 2:
        return 0, len(seqs), 0, 0
    lost = resets = 0
    expected = 0
    for a, b in zip(seqs, seqs[1:]):
        d = (b - a) & 0xFFFFFFFF
        if d == 1:
            expected += 1
        elif 1 < d < 1000:
            lost += d - 1
            expected += d
        else:
            resets += 1          # restart or huge gap, do not count as loss
    return expected + 1, len(seqs), lost, resets


# ------------------------------------------------------------------ stats ----
def chan_stats(x):
    n = len(x)
    if n == 0:
        return None
    mn, mx = min(x), max(x)
    mean = sum(x) / n
    var = sum((v - mean) ** 2 for v in x) / n
    rms = math.sqrt(var)                       # AC-coupled RMS
    peak = max(abs(mn), abs(mx))
    # first-difference energy: low ratio => sample-to-sample correlation (real audio)
    if n > 1:
        d = sum(abs(x[i] - x[i - 1]) for i in range(1, n)) / (n - 1)
    else:
        d = 0.0
    # distinct over the WHOLE capture, not x[:4000]. With 4000 samples that is
    # 83 ms of a 5 s capture, so a channel that happened to be held for the
    # first 83 ms was labelled "STUCK at <value>" while its own min/max/RMS
    # showed it varying. It made healthy channels flip between "active" and
    # "STUCK" from run to run depending only on where the capture started.
    distinct = len(set(x))
    # Longest run of identical consecutive samples, and what it held. A real
    # converter dithers, so any long run means the part stopped producing new
    # samples - which is a different fault from tri-stating, where the pull-down
    # gives exact zeros. Reported so "held" can be distinguished from "absent".
    # Also WHERE the longest hold starts, how many separate holds there are, and
    # what fraction of the capture is zero. Length alone cannot distinguish one
    # long gap at the very start - which is a capture or boot artefact, not board
    # behaviour - from repeated dropouts spread through the run.
    hold_len, hold_val, hold_at = 1, x[0], 0
    run, prev, run_start = 1, x[0], 0
    holds = 0
    for i, v in enumerate(x[1:], start=1):
        if v == prev:
            run += 1
            if run > hold_len:
                hold_len, hold_val, hold_at = run, v, run_start
        else:
            if run >= 64:
                holds += 1
            run, run_start = 1, i
        prev = v
    if run >= 64:
        holds += 1
    zero_frac = 100.0 * sum(1 for v in x if v == 0) / n
    # Lengths of every zero run >= 64 samples. A marginal contact should miss a
    # sync edge and recover on the next frame - 10.4 us at 96 kHz - so gaps ought
    # to be short and exponentially distributed. Measured gaps are ~167 ms, which
    # is 16000 frames, and 167 ms keeps recurring across different builds and
    # clock rates. Random bounce does not repeat a duration, so the spread of
    # these lengths is what tells systematic apart from mechanical.
    gaps = []
    run0 = 0
    for v in x:
        if v == 0:
            run0 += 1
        else:
            if run0 >= 64:
                gaps.append(run0)
            run0 = 0
    if run0 >= 64:
        gaps.append(run0)
    # Single-sample outliers. Real audio is band limited, so consecutive samples
    # are correlated and the second difference stays small. One flipped bit in a
    # 24-bit word shows up as a lone spike, which barely moves the RMS but lifts
    # the window PEAK by tens of dB - exactly what makes a channel read "steady"
    # in timeline.py while a level meter flickers. Counted here so bit errors can
    # be told apart from a genuinely varying signal.
    glitch = 0
    if n > 2 and rms > 0:
        thr = 8.0 * rms
        i = 1
        while i < n - 1:
            if abs(2 * x[i] - x[i - 1] - x[i + 1]) > thr:
                glitch += 1
                i += 3      # one spike trips three adjacent tests; count it once
            else:
                i += 1
    glitch_rate = glitch / (n / float(SAMPLE_RATE)) if n else 0.0
    return {"min": mn, "max": mx, "mean": mean, "rms": rms, "peak": peak,
            "diff": d, "distinct": distinct, "n": n,
            "hold_len": hold_len, "hold_val": hold_val, "hold_at": hold_at,
            "holds": holds, "zero_frac": zero_frac,
            "glitch": glitch, "glitch_rate": glitch_rate, "gaps": gaps}


def classify(st):
    if st is None:
        return "no data"
    if st["distinct"] == 1:
        v = st["min"]
        if v == 0:
            return "STUCK at 0"
        if v == -1:
            return "STUCK at -1 (all ones)"
        return "STUCK at %d" % v
    if st["peak"] >= FULL_SCALE - 2 and st["rms"] > FULL_SCALE * 0.4:
        return "RAILED / clipping"
    if st["rms"] < 8:
        return "silent (near zero)"
    if st["distinct"] < 8:
        return "quantised, %d levels" % st["distinct"]
    # random bit garbage decorrelates: mean |diff| approaches the RMS scale
    if st["rms"] > 0 and st["diff"] / st["rms"] > 1.2:
        return "NOISE / misaligned?"
    # A converter that dithers never repeats a sample many times over. A long
    # run means the part held its output: framing survived but conversion
    # stopped. Distinct from tri-stating, which reads as exact zeros.
    if st["glitch_rate"] > 1.0:
        return "%d bit glitches (%.0f/s) - marginal capture" % (
            st["glitch"], st["glitch_rate"])
    if st["hold_len"] >= 64:
        where = "at start" if st["hold_at"] < 64 else \
                "from %.2f s" % (st["hold_at"] / float(SAMPLE_RATE))
        return "%s %.0f ms %s, %d gap%s, %.0f%% zero" % (
            "ZERO" if st["hold_val"] == 0 else "HELD %d" % st["hold_val"],
            1000.0 * st["hold_len"] / SAMPLE_RATE, where,
            st["holds"], "" if st["holds"] == 1 else "s", st["zero_frac"])
    return "active"


def dbfs(v):
    return -math.inf if v <= 0 else 20 * math.log10(v / FULL_SCALE)


def fmt_db(v):
    d = dbfs(v)
    return " -inf " if d == -math.inf else "%6.1f" % d


# -------------------------------------------------------------- alignment ----
def alignment_scan(pkts, span=24):
    """
    The ADAU1978's TDM data can sit a bit or two off from where tdm8_rx snapshots,
    which rotates every channel. Rebuild the raw 384-bit word, rotate it, and pick
    the offset that makes samples most correlated sample-to-sample.
    """
    words = []
    for p in pkts[:400]:
        if len(p) != PAYLOAD_LEN or p[0:4] != MAGIC:
            continue
        off = HDR_LEN
        for f in range(FRAMES_PKT):
            words.append(int.from_bytes(p[off + 2:off + 50], "big"))
            off += FRAME_LEN
    if len(words) < 32:
        return None

    W = 384
    results = []
    for k in range(-span, span + 1):
        chans = [[] for _ in range(CHANNELS)]
        for w in words:
            r = ((w << (k % W)) | (w >> (W - (k % W)))) & ((1 << W) - 1) if k else w
            for c in range(CHANNELS):
                v = (r >> (W - 24 * (c + 1))) & 0xFFFFFF
                chans[c].append(v - (1 << 24) if v & 0x800000 else v)
        ratios = []
        for x in chans:
            m = sum(x) / len(x)
            rms = math.sqrt(sum((v - m) ** 2 for v in x) / len(x))
            if rms < 8:
                continue
            d = sum(abs(x[i] - x[i - 1]) for i in range(1, len(x))) / (len(x) - 1)
            ratios.append(d / rms)
        if ratios:
            ratios.sort()
            results.append((ratios[len(ratios) // 2], k, len(ratios)))
    if not results:
        return None
    results.sort()
    return results


# ------------------------------------------------------------------- wav -----
def write_wavs(samples, prefix):
    written = 0
    for c, x in enumerate(samples):
        if not x:
            continue
        with wave.open("%s_ch%02d.wav" % (prefix, c + 1), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(3)
            w.setframerate(SAMPLE_RATE)
            w.writeframes(b"".join(
                (v & 0xFFFFFF).to_bytes(3, "little") for v in x))
        written += 1
    print("\nwrote %d WAV files as %s_chNN.wav (%d-bit, %d Hz)"
          % (written, prefix, 24, SAMPLE_RATE))


# ------------------------------------------------------------------- main ----
def main():
    ap = argparse.ArgumentParser(description="TDM_UATR UDP stream monitor")
    ap.add_argument("-p", "--port", type=int, default=5005)
    ap.add_argument("-s", "--seconds", type=float, default=5.0)
    ap.add_argument("-b", "--bind", default="")
    ap.add_argument("--wav", metavar="PREFIX", help="write per-channel WAV files")
    ap.add_argument("--align", action="store_true",
                    help="scan for a TDM bit-alignment offset")
    args = ap.parse_args()

    pkts, elapsed = capture(args.port, args.seconds, args.bind)
    if not pkts:
        return 1

    samples, info = parse(pkts)
    exp, got, lost, resets = loss_report(info["seqs"])

    # ---------------- link ----------------
    pps = len(pkts) / elapsed
    mbps_payload = len(pkts) * PAYLOAD_LEN * 8 / elapsed / 1e6
    mbps_wire = len(pkts) * (WIRE_LEN + 8 + 4 + 12) * 8 / elapsed / 1e6
    nsamp = len(samples[0]) if samples[0] else 0

    print("\n" + "=" * 62)
    print("LINK")
    print("=" * 62)
    print("  packets captured   %d in %.2f s" % (len(pkts), elapsed))
    print("  packet rate        %.0f /s   (expected %.0f)" % (pps, EXPECTED_PPS))
    print("  payload throughput %.2f Mbit/s" % mbps_payload)
    print("  wire throughput    %.2f Mbit/s  (%.0f%% of 100BASE-TX)"
          % (mbps_wire, mbps_wire))
    print("  effective fs       %.0f Hz per channel  (nominal %d)"
          % (pps * FRAMES_PKT, SAMPLE_RATE))
    print("  audio frames       %d  (%.3f s)" % (nsamp, nsamp / SAMPLE_RATE))

    print("\n" + "=" * 62)
    print("INTEGRITY")
    print("=" * 62)
    print("  sequence gaps      %d lost of %d expected  (%.4f%%)"
          % (lost, exp, 100.0 * lost / exp if exp else 0.0))
    if resets:
        print("  sequence restarts  %d  (FPGA reset, or capture gap)" % resets)
    print("  bad magic word     %d" % info["bad_magic"])
    print("  wrong length       %d" % info["bad_len"])
    print("  frame index errors %d" % info["bad_index"])
    if pps < EXPECTED_PPS * 0.97 and lost == 0:
        print("  NOTE: rate is low but no sequence gaps -> the FPGA is under-running,")
        print("        not the network. Check LRCLK / the audio clock chain.")
    if lost:
        print("  NOTE: real loss. At ~44 Mbit/s this is usually the receiving host")
        print("        (socket buffer, or a slow disk if something is recording).")

    # ---------------- SDATA line activity ----------------
    # I2C diagnostics live in i2c_scan.py now; this file covers the link,
    # packet integrity and the audio itself.
    if pkts and len(pkts[0]) == PAYLOAD_LEN:
        a_act = pkts[0][HDR_LEN + 5 * FRAME_LEN]
        b_act = pkts[0][HDR_LEN + 6 * FRAME_LEN]
        print("\n" + "=" * 62)
        print("FAULT COUNTERS   (since power-up, saturate at 255)")
        print("=" * 62)
        # dbg_status6/7 used to be SDATA edge counters, which contradicted the
        # channel data often enough to be worthless. They now carry fault
        # counts instead: how often the FPGA PLL lost lock, and how often that
        # re-asserted adc_rst_n and reset all four ADCs for 100 ms.
        # dbg_status6 = [7:4] config drift ever, [3:0] ADC clip ever, per part.
        # Every register used to be checked once at boot and never again, so a
        # part that silently lost its configuration went quiet unnoticed.
        parts = ("U19", "U20", "U37", "U38")
        drift, clip = (a_act >> 4) & 0xF, a_act & 0xF
        print("    runtime register check   (0x00, 0x05, 0x06 re-read continuously)")
        for i, nm in enumerate(parts):
            print("      %-4s %-28s clip seen: %s"
                  % (nm,
                     "*** CONFIG DRIFTED ***" if (drift >> i) & 1 else "config holding",
                     "yes" if (clip >> i) & 1 else "no"))
        if drift:
            print()
            print("    A part whose registers no longer match what was written has")
            print("    lost its configuration at runtime - it will have reverted to")
            print("    stereo mode and stopped driving its TDM slots.")
        # dbg_status7 now carries runtime overtemperature: [7:4] ever tripped,
        # [3:0] tripped right now, one bit per part. 0x09 bit 0 is OT, and it
        # was previously only read once at boot - so a part heating up, muting
        # and recovering was invisible.
        parts = ("U19", "U20", "U37", "U38")
        ever, lost = (b_act >> 4) & 0xF, b_act & 0xF
        print("    sticky faults            (latched, survive between polls)")
        for i, nm in enumerate(parts):
            f = []
            if (ever >> i) & 1:
                f.append("OVERTEMPERATURE")
            if (lost >> i) & 1:
                f.append("*** PLL LOST LOCK ***")
            print("      %-4s %s" % (nm, ", ".join(f) if f else "no faults latched"))
        if lost:
            print()
            print("    A PLL that unlocks stops the serial port framing, so SDATAOUT")
            print("    goes high-Z and the pull-down reads as exact zeros - which is")
            print("    what the timeline shows. Look at MCLK reaching those parts.")
        if ever:
            print()
            print("    Overtemperature mutes the part. Table 8: the exposed pad is the")
            print("    only thermal path - \"THE EXPOSED PAD MUST BE CONNECTED TO THE")
            print("    GROUND PLANE\" - so a degraded pad joint after repeated reflow")
            print("    gives exactly this: intermittent dropouts that worsen with time.")

    print("\n" + "=" * 62)
    print("CHANNELS   (24-bit signed, full scale = %d)" % FULL_SCALE)
    print("=" * 62)
    print("  ch    min        max        DC offset     RMS    peak dBFS  state")
    print("  " + "-" * 68)
    sts = []
    for c in range(CHANNELS):
        st = chan_stats(samples[c])
        sts.append(st)
        if st is None:
            print("  %2d    (no data)" % (c + 1))
            continue
        print("  %2d  %9d  %9d  %11.1f  %8.1f    %s   %s"
              % (c + 1, st["min"], st["max"], st["mean"], st["rms"],
                 fmt_db(st["peak"]), classify(st)))

    # Distribution of dropout lengths, for channels that have any. A part that
    # misses one sync edge should recover on the next frame - 10.4 us at 96 kHz.
    # Gaps of ~167 ms are 16000 frames, and that duration has recurred across
    # different builds and clock rates. Tightly clustered lengths point at
    # something systematic with its own time constant; a broad spread points at
    # a mechanical contact. This is the measurement that separates them.
    gappy = [c for c in range(CHANNELS) if sts[c] and sts[c]["gaps"]]
    if gappy:
        print("\n" + "=" * 62)
        print("DROPOUT LENGTHS   (runs of exact zero, >= 64 samples)")
        print("=" * 62)
        print("  one frame = %.1f us, so anything in ms means the part stayed off"
              % (1e6 / SAMPLE_RATE))
        print()
        print("  ch   gaps   min ms   med ms   max ms   total ms   spread")
        print("  " + "-" * 60)
        for c in gappy:
            g = sorted(sts[c]["gaps"])
            ms = lambda k: 1000.0 * k / SAMPLE_RATE
            spread = "tight - systematic?" if ms(g[-1]) - ms(g[0]) < 0.25 * ms(
                g[len(g) // 2]) else "broad - mechanical?"
            print("  %2d   %4d   %6.1f   %6.1f   %6.1f   %8.1f   %s"
                  % (c + 1, len(g), ms(g[0]), ms(g[len(g) // 2]), ms(g[-1]),
                     ms(sum(g)), spread))

    src = "ADC A (U19/U20 via TDM1)", "ADC B (U37/U38 via TDM2)"
    print("\n  channels 1-8  = %s" % src[0])
    print("  channels 9-16 = %s" % src[1])

    # ---------------- alignment ----------------
    if args.align:
        print("\n" + "=" * 62)
        print("TDM BIT ALIGNMENT SCAN")
        print("=" * 62)
        res = alignment_scan(pkts)
        if not res:
            print("  not enough non-silent data to judge alignment")
        else:
            print("  lower score = more sample-to-sample correlation = more like audio")
            for score, k, nch in res[:8]:
                mark = "  <== current" if k == 0 else ""
                print("    rotate %+3d bits : score %.3f  (%d live channels)%s"
                      % (k, score, nch, mark))
            best = res[0]
            if best[1] != 0:
                print("\n  Best offset is %+d bits, not 0. That means tdm8_rx is latching"
                      % best[1])
                print("  the shift register off the true TDM slot boundary - adjust the")
                print("  lrclk_in snapshot point in tdm8_rx.vhd by that many BCLKs.")
            else:
                print("\n  Current alignment is best. No rotation needed.")

    if args.wav:
        write_wavs(samples, args.wav)

    return 0


if __name__ == "__main__":
    sys.exit(main())
