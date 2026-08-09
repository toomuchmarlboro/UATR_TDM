#!/usr/bin/env python3
"""
Decode the RAW CAPTURE mode of tdm8_rx.

With C_RAW_CAPTURE = true, tdm8_rx stops extracting 24-bit samples and instead
publishes the first 192 BCLKs of each frame verbatim. Those 192 bits arrive in
the packet where channels 1-8 normally sit (TDM1) and channels 9-16 (TDM2), so
udp_monitor and timeline show nonsense while this mode is on - use this tool
instead.

192 BCLKs at 32 BCLKs per slot covers slots 1 to 6: all four channels of the
part holding slots 1-4, plus the first two channels of the part holding 5-8.
That means one capture shows a known-good part and a suspect part side by side,
bit for bit, on the same line and in the same frame.

What it answers: when a channel group reads "every sample exactly zero", is the
SDATA line genuinely idle, or is there data on it that the slot decode is
missing? Those are different faults and nothing else distinguishes them.

    python rawview.py                 # summarise slot activity
    python rawview.py -b              # also print example bit patterns
    python rawview.py -t 5            # capture for 5 seconds
"""

import argparse
import re
import socket
import sys

MAGIC       = bytes([0xAD, 0xA1, 0x97, 0x78])
HDR_LEN     = 10
FRAME_LEN   = 50
FRAMES_PKT  = 8
PAYLOAD_LEN = HDR_LEN + FRAMES_PKT * FRAME_LEN      # 410
RAW_BITS    = 192
SLOT_BCLKS  = 32
SLOTS       = RAW_BITS // SLOT_BCLKS                # 6

# which part owns which slot, from the CMAP writes in adau_sequencer
OWNER = {1: ("U19", "U37"), 2: ("U19", "U37"), 3: ("U19", "U37"),
         4: ("U19", "U37"), 5: ("U20", "U38"), 6: ("U20", "U38")}


def vhdl_bit_adj():
    """C_BIT_ADJ from tdm8_rx.vhd, so slot boundaries here match the RTL."""
    try:
        with open("tdm8_rx.vhd", encoding="utf-8", errors="replace") as f:
            m = re.search(r'C_BIT_ADJ\s*:\s*integer\s*:=\s*(-?\d+)', f.read())
            return int(m.group(1)) if m else 0
    except OSError:
        return 0


def raw_capture_on():
    try:
        with open("tdm8_rx.vhd", encoding="utf-8", errors="replace") as f:
            m = re.search(r'C_RAW_CAPTURE\s*:\s*boolean\s*:=\s*(true|false)',
                          f.read())
            return m.group(1) == "true" if m else None
    except OSError:
        return None


def grab(port, bind, timeout):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 32 << 20)
    s.bind((bind, port))
    s.settimeout(2.0)
    pkts = []
    import time
    t_end = time.time() + timeout
    try:
        while time.time() < t_end:
            p = s.recv(2048)
            if len(p) == PAYLOAD_LEN and p[0:4] == MAGIC:
                pkts.append(p)
    except socket.timeout:
        pass
    finally:
        s.close()
    return pkts


def frames(pkts):
    """Yield (raw_A, raw_B) as 192-bit ints, one pair per audio frame."""
    for p in pkts:
        off = HDR_LEN
        for _ in range(FRAMES_PKT):
            a = off + 2
            yield (int.from_bytes(p[a:a + 24], "big"),
                   int.from_bytes(p[a + 24:a + 48], "big"))
            off += FRAME_LEN


def bits_of(word):
    return format(word, "0%db" % RAW_BITS)


def slot_slice(bitstr, slot, adj=0):
    """Bits of `slot`, 1-based.

    No C_BIT_ADJ term here, deliberately. The raw capture is
    shift_reg(255+adj downto 64+adj) and the normal decode reads slot k from
    shift_reg(255+adj-32k downto 232+adj-32k) - both anchored on the same
    255+adj, so adj is already baked into where the capture starts. Applying it
    again shifts every cell one bit late, which makes cell 4 pick up the first
    bit of slot 5. That bit belongs to the always-driven part, so slot 4 read
    100% active while slots 1-3 read 22%. Slot boundaries are plain multiples
    of 32 relative to the start of the capture.
    """
    start = (slot - 1) * SLOT_BCLKS
    return bitstr[start:start + SLOT_BCLKS]


def slot_data(bitstr, slot):
    """The 24 sample bits of a slot: left justified, so the first 24 of 32."""
    return slot_slice(bitstr, slot)[:24]


def slot_pad(bitstr, slot):
    """The 8 trailing BCLKs of a 32-BCLK slot. 24-bit data left justified in a
    32-BCLK slot means these should be zero. Bits here mean either the capture
    is misaligned or something else is driving those BCLKs."""
    return slot_slice(bitstr, slot)[24:]


def runs(flags):
    """Run-length encode a list of bools into [(value, length), ...]."""
    out = []
    for f in flags:
        if out and out[-1][0] == f:
            out[-1][1] += 1
        else:
            out.append([f, 1])
    return out


def findpad(fr, adj):
    """Locate the 8 pad BCLKs of each slot, and from them the true alignment.

    24-bit data left justified in a 32-BCLK slot leaves 8 trailing BCLKs that
    are always zero. Fold every frame together and the pad shows up as the
    quietest run of 8. This needs no audio and no correlation metric - it reads
    frame structure directly, which is why it works with floating inputs where
    udp_monitor's --align scan ties across every offset.

    Counting how OFTEN each position is set, not merely whether it ever was.
    A boolean OR over ~10^5 frames is decided by the single noisiest frame in
    the capture: one glitched bit marks a position as "data" forever, so a pad
    that is zero 99.99% of the time still reads as active. Frequencies are
    robust to that - a real pad sits near 0%, data MSBs sit near 50% (sign
    bits) and data LSBs near 50% too.

    Per slot, never folded together. Two parts share a line and they are not
    comparable: one may be driven every frame and the other one frame in ten,
    and a gain probe can leave one 30 dB louder. Folding them averages a loud
    always-present signal with a quiet mostly-absent one, and any pad turns
    into a flat floor. Idle slots are skipped too - counting their zeros drags
    every position down uniformly, which hides the gap it is meant to reveal.
    """
    out = {}
    for name, idx in (("TDM1", 0), ("TDM2", 1)):
        per = {}
        for s in range(1, SLOTS + 1):
            per[s] = ([0] * SLOT_BCLKS, 0)
        for pair in fr:
            word = pair[idx]
            if word == 0:
                continue
            bs = bits_of(word)
            for s in range(1, SLOTS + 1):
                cell = slot_slice(bs, s)
                if "1" not in cell:
                    continue                # this slot idle this frame
                cnt, tot = per[s]
                per[s] = (cnt, tot + 1)
                for j, c in enumerate(cell):
                    if c == "1":
                        cnt[j] += 1
        # align on the busiest slot: most samples, so the cleanest statistics
        best_slot = max(per, key=lambda s: per[s][1])
        cnt, total = per[best_slot]
        pcts = {s: [100.0 * c / t if t else 0.0 for c in per[s][0]]
                for s, (_, t) in ((s, per[s]) for s in per)
                for t in [per[s][1]]}
        if total == 0:
            out[name] = (None, pcts, per, 0, None,
                         "line never driven - nothing to align")
            continue
        pct = pcts[best_slot]
        # the 8 consecutive positions with the least activity are the pad
        best_sum, best_start = None, 0
        for start in range(SLOT_BCLKS):
            tot = sum(pct[(start + k) % SLOT_BCLKS] for k in range(8))
            if best_sum is None or tot < best_sum:
                best_sum, best_start = tot, start
        inside  = [pct[(best_start + k) % SLOT_BCLKS] for k in range(8)]
        outside = [pct[j] for j in range(SLOT_BCLKS)
                   if all(j != (best_start + k) % SLOT_BCLKS for k in range(8))]
        worst_in  = max(inside)
        least_out = min(outside)
        d = (best_start + 8) % SLOT_BCLKS
        err = None
        if worst_in > 5.0:
            err = ("quietest 8 BCLKs still average %.1f%% - no pad-shaped gap, "
                   "so the data is not on a fixed 32-BCLK grid" % (best_sum / 8))
        elif worst_in >= least_out:
            err = ("pad and data activity overlap (worst pad %.2f%% vs quietest "
                   "data %.2f%%) - offset not separable" % (worst_in, least_out))
        out[name] = ((d, best_start, worst_in, least_out), pcts, per,
                     total, best_slot, err)
    return out


def report_findpad(fr, adj):
    res = findpad(fr, adj)
    bar = "=" * 78
    print()
    print(bar)
    print("PAD DETECTION -> TRUE ALIGNMENT")
    print(bar)
    print()
    print("  How often each of the 32 BCLKs in a slot is set, over every driven")
    print("  frame. '.' <1%   ',' <5%   ':' <20%   '+' <50%   '#' >=50%")
    print("  A pad BCLK sits near 0%. Data bits sit high - sign bits near 50%.")
    print()
    for name in ("TDM1", "TDM2"):
        found, pcts, per, total, best_slot, err = res[name]

        def sym(v):
            return ("." if v < 1 else "," if v < 5 else
                    ":" if v < 20 else "+" if v < 50 else "#")

        print("  %s   position  %s"
              % (name, "".join(str(j % 10) for j in range(SLOT_BCLKS))))
        for s in range(1, SLOTS + 1):
            owner = OWNER[s][0 if name == "TDM1" else 1]
            n = per[s][1]
            mark = "  <-- aligning on this one" if s == best_slot and n else ""
            print("         slot %d %-4s %s  %6d frames%s"
                  % (s, owner, "".join(sym(v) for v in pcts[s]), n, mark))
        if err:
            print("         %s" % err)
            print()
            continue
        pct = pcts[best_slot]
        print()
        print("         slot %d numbers, two rows of 16:" % best_slot)
        for half in (0, 16):
            print("         %s"
                  % " ".join("%4.1f" % pct[j] for j in range(half, half + 16)))
        d, pstart, worst_in, least_out = found
        print("        pad = 8 BCLKs at position %d, busiest %.2f%%; "
              "quietest data BCLK %.2f%%" % (pstart, worst_in, least_out))
        print("        first data BCLK at position %d" % d)
        new_adj = adj - d
        print()
        print("        C_BIT_ADJ should be %+d   (built as %+d, shift by %d)"
              % (new_adj, adj, d))
        if new_adj < -8 or new_adj > 8:
            print("        NOTE: outside the -8..+8 the shift register allows.")
            print("        %+d is the same sampling point one slot over, which"
                  % (new_adj + SLOT_BCLKS))
            print("        also rotates which channel lands where - say so and")
            print("        I will widen shift_reg instead.")
        print()
    return 0


def main():
    ap = argparse.ArgumentParser(description="decode tdm8_rx raw capture")
    ap.add_argument("-p", "--port", type=int, default=5005)
    ap.add_argument("-b", "--bind", default="")
    ap.add_argument("-t", "--time", type=float, default=2.0,
                    help="seconds to capture (default 2)")
    ap.add_argument("--bits", "-B", action="store_true",
                    help="print example bit patterns")
    ap.add_argument("--findpad", action="store_true",
                    help="locate the pad BCLKs and report the true C_BIT_ADJ")
    ap.add_argument("--force", action="store_true",
                    help="run even if C_RAW_CAPTURE is false in the source")
    a = ap.parse_args()

    on = raw_capture_on()
    if on is False and not a.force:
        print("*** REFUSING TO RUN ***")
        print()
        print("  C_RAW_CAPTURE is false in tdm8_rx.vhd, so the packets almost")
        print("  certainly carry DECODED 24-bit samples, not raw BCLKs. Reading")
        print("  samples as raw bits produces confident-looking nonsense: 18-bit")
        print("  values with sign-extended tops set every bit position, which")
        print("  shows up as 'no always-zero run', and a dead line shows up as")
        print("  'never driven'. Both are artefacts of the wrong bitstream.")
        print()
        print("  Flash a build whose source had C_RAW_CAPTURE = true, then")
        print("  re-run. Use --force only if you know the loaded bitstream is a")
        print("  raw-capture build that no longer matches this working tree.")
        print()
        return 1

    pkts = grab(a.port, a.bind, a.time)
    if not pkts:
        print("No valid packets on %s:%d." % (a.bind or "0.0.0.0", a.port))
        return 1

    adj = vhdl_bit_adj()
    fr = list(frames(pkts))

    if a.findpad:
        print("=" * 78)
        print("RAW TDM CAPTURE   %d packets, %d frames, C_BIT_ADJ = %+d"
              % (len(pkts), len(fr), adj))
        print("=" * 78)
        return report_findpad(fr, adj)

    # per line, per slot: how many frames had any bit set, split data vs pad
    nz   = {"TDM1": [0] * (SLOTS + 1), "TDM2": [0] * (SLOTS + 1)}
    npad = {"TDM1": [0] * (SLOTS + 1), "TDM2": [0] * (SLOTS + 1)}
    allzero = {"TDM1": 0, "TDM2": 0}
    examples = {"TDM1": [], "TDM2": []}
    # was the slots 1-4 part driving, frame by frame - for run lengths
    drv = {"TDM1": [], "TDM2": []}

    for raw_a, raw_b in fr:
        for name, word in (("TDM1", raw_a), ("TDM2", raw_b)):
            if word == 0:
                allzero[name] += 1
            bs = bits_of(word)
            for s in range(1, SLOTS + 1):
                if "1" in slot_data(bs, s):
                    nz[name][s] += 1
                if "1" in slot_pad(bs, s):
                    npad[name][s] += 1
            drv[name].append("1" in slot_data(bs, 1) or "1" in slot_data(bs, 2))
            if len(examples[name]) < 3 and word != 0:
                examples[name].append(bs)

    n = len(fr)
    bar = "=" * 78
    print(bar)
    print("RAW TDM CAPTURE   %d packets, %d frames, C_BIT_ADJ = %+d"
          % (len(pkts), n, adj))
    print(bar)
    print()
    print("  First 192 BCLKs of each frame, verbatim. 32 BCLKs per slot, so")
    print("  slots 1-6 are visible: all of the slots 1-4 part, and the first")
    print("  two channels of the slots 5-8 part.")
    print()
    print("  line   slot  owner   24 data BCLKs      8 pad BCLKs")
    print("  " + "-" * 62)
    for name in ("TDM1", "TDM2"):
        for s in range(1, SLOTS + 1):
            owner = OWNER[s][0 if name == "TDM1" else 1]
            pct = 100.0 * nz[name][s] / n if n else 0.0
            pp  = 100.0 * npad[name][s] / n if n else 0.0
            flag = ""
            if pct == 0.0:
                flag = "  <-- never driven"
            elif pct < 99.0:
                flag = "  <-- intermittent"
            if pp > 1.0:
                flag += "  PAD SET"
            print("  %-5s  %d     %-5s   %6d  %5.1f%%      %6d  %5.1f%%%s"
                  % (name, s, owner, nz[name][s], pct, npad[name][s], pp, flag))
        print("  %-5s  whole frame idle (all 192 bits zero): %d / %d  %.1f%%"
              % (name, allzero[name], n, 100.0 * allzero[name] / n if n else 0))

        # Periodicity. A part that slips against the frame clock drives in
        # regular bursts; one with a marginal signal drops out at random.
        rl = runs(drv[name])
        on  = sorted((L for v, L in rl if v), reverse=True)[:6]
        off = sorted((L for v, L in rl if not v), reverse=True)[:6]
        if on:
            print("  %-5s  driven runs (frames): %s" % (name, on))
            print("  %-5s  idle   runs (frames): %s" % (name, off))
        print()

    print(bar)
    print("HOW TO READ THIS")
    print(bar)
    print()
    print("  A slot at 0.0% means no device drove those BCLKs - the ADC is")
    print("  tri-stated (DRV_HIZ=1) because it never found frame sync, and the")
    print("  pull-down resistor holds the line low. The fault is upstream of")
    print("  the FPGA: clocks, configuration, or the part itself.")
    print()
    print("  A slot with bits set, while timeline.py reports that channel as")
    print("  'every sample exactly zero', means the data IS on the wire and the")
    print("  slot decode is missing it. That is an FPGA-side alignment fault,")
    print("  and C_BIT_ADJ in tdm8_rx is the knob.")
    print()
    print("  Compare slots 1-4 against slots 5-6 on the same line: same frame,")
    print("  same BCLK, same decode. A difference between them is the part.")

    if a.bits:
        print()
        print(bar)
        print("EXAMPLE FRAMES   (| marks a 32-BCLK slot boundary)")
        print(bar)
        for name in ("TDM1", "TDM2"):
            print()
            print("  %s" % name)
            if not examples[name]:
                print("    every captured frame was all zeros")
                continue
            for bs in examples[name]:
                cells = [slot_slice(bs, s, adj) for s in range(1, SLOTS + 1)]
                print("    " + "|".join(cells))
    return 0


if __name__ == "__main__":
    sys.exit(main())
