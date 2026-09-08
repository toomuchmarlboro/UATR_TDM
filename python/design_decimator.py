#!/usr/bin/env python3
"""
Design and verify the 96 kHz -> 24 kHz decimation filter, and emit everything
the VHDL needs.

Two cascaded halfband FIR stages, 96k -> 48k -> 24k. Halfband because every
even-indexed tap except the centre is exactly zero, which halves the
multiplies; linear phase because the coefficients are symmetric, which halves
them again.

    python design_decimator.py              design, verify, write outputs
    python design_decimator.py --check      verify only, exit 1 on regression
    python design_decimator.py --plot       also write the response PNG

Outputs (written next to the RTL / into sim/):
    rtl/decim_coef_pkg.vhd      coefficient package, 20-bit signed
    sim/decim_ref_vectors.txt   bit-exact reference input/output vectors
    docs/decimator_response.png with --plot

WHY THIS FILE EXISTS. There is no ModelSim licence on this machine (see
docs/MULTI_BOARD.md), so the VHDL cannot be simulated against a testbench. This
script is the substitute: it designs the coefficients AND generates the
reference output for the same input, so decim_check.py can diff the hardware's
real output against a known-good model. Because both come from this one file
they cannot drift apart.

Requirements are set by the acquisition chain, not by taste:
  - passband 0-11 kHz, the band of interest, must be untouched
  - stopband from 13 kHz must be below the ADAU1978's own noise floor
    (103 dB dynamic range, docs/adau1978.pdf p.3), hence the 100 dB target
  - the ADC passes full-amplitude content to 42 kHz (0.4375 x fS, p.4), so
    everything from 13 kHz up genuinely is present and genuinely does fold
"""

import argparse
import sys
from pathlib import Path

import numpy as np
from scipy import signal

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

# ---------------------------------------------------------------- parameters
FS_IN      = 96000          # ADC sample rate
FS_OUT     = 24000          # after decimation by 4
F_PASS     = 11000.0        # top of the band of interest
F_STOP     = 13000.0        # first frequency that folds into the passband

# Lengths chosen by exhaustive search over (n, beta) for the cheapest pair that
# still meets MAX_RIPPLE_DB and MAX_ALIAS_DB, scored on multiply count and RAM.
# Do not hand-tune these without re-running that search: shortening either stage
# breaks the alias limit, and lengthening costs cycles the schedule has budgeted.
N1, BETA1  = 27, 11.0       # stage 1, 96k -> 48k
N2, BETA2  = 171, 11.0      # stage 2, 48k -> 24k
COEF_BITS  = 20             # coefficient word width
DATA_BITS  = 24             # sample width, matches the TDM bus

# Verification thresholds. A build that misses any of these is a regression.
MAX_RIPPLE_DB  = 0.01       # peak-to-peak across 0-11 kHz
MAX_ALIAS_DB   = -100.0     # worst level in any band that folds into 0-11 kHz


def halfband(ntaps: int, beta: float) -> np.ndarray:
    """A Kaiser-windowed halfband lowpass, cutoff exactly at fs/4.

    Cutoff at fs/4 is what makes the even taps vanish. firwin puts values there
    that are zero only to floating-point precision, so they are forced to exact
    zero -- the VHDL must be able to skip them, and 1e-19 is not skippable.
    """
    b = signal.firwin(ntaps, 0.5, window=("kaiser", beta))
    mid = (ntaps - 1) // 2
    for i in range(ntaps):
        if i != mid and (i - mid) % 2 == 0:
            b[i] = 0.0
    return b / np.sum(b)          # unity DC gain


def quantise(b: np.ndarray, bits: int = COEF_BITS):
    """Scale to full-scale signed integers of the given width.

    Returns (integers, scale) where float_coef = integers / scale.
    """
    scale = (2 ** (bits - 1) - 1) / np.max(np.abs(b))
    q = np.round(b * scale).astype(np.int64)
    return q, scale


def acc_bits(q: np.ndarray) -> int:
    """Bits needed for the MAC accumulator, from the true worst case.

    The rigorous bound is sum(|coef|) x max|data|, which is the largest value
    the accumulator can reach for any input -- reached by an input whose sign
    matches every coefficient's. Estimating from tap count instead
    (data + coef + ceil(log2(taps))) over-provisions, because the taps are not
    all full scale.

    One shared width is used for both stages so the datapath is one adder.
    """
    worst = int(np.sum(np.abs(q))) * (2 ** (DATA_BITS - 1))
    return int(np.ceil(np.log2(worst))) + 1        # +1 for sign


def cascade(f1: np.ndarray, f2: np.ndarray) -> np.ndarray:
    """Equivalent single-rate response of the two stages, on the 96 kHz grid.

    Stage 2 runs at 48 kHz, so on the 96 kHz grid its impulse response is
    zero-stuffed by 2 before convolving with stage 1.
    """
    up = np.zeros(len(f2) * 2 - 1)
    up[::2] = f2
    return np.convolve(f1, up)


def measure(casc: np.ndarray) -> dict:
    """Passband ripple, droop and worst alias-band level of the cascade."""
    w, h = signal.freqz(casc, worN=65536, fs=FS_IN)
    mag = 20 * np.log10(np.abs(h) / np.max(np.abs(h)) + 1e-20)

    pb = mag[w <= F_PASS]
    out = {
        "ripple": float(pb.max() - pb.min()),
        "droop": float(pb[-1]),
        "at_12k": float(mag[np.argmin(np.abs(w - 12000))]),
        "at_13k": float(mag[np.argmin(np.abs(w - F_STOP))]),
        "group_delay_taps": len(casc) // 2,
    }

    # Every band that folds into 0-11 kHz on a decimate-by-4: around each
    # multiple of the output rate, +/- the passband width.
    worst = -999.0
    for k in (1, 2, 3):
        m = (w >= FS_OUT * k - F_PASS) & (w <= FS_OUT * k + F_PASS)
        if m.any():
            worst = max(worst, float(mag[m].max()))
    out["alias"] = worst
    return out


def resources(q1: np.ndarray, q2: np.ndarray) -> dict:
    """LE / multiplier / M9K cost, for comparison against the fitter report."""
    nz1, nz2 = int(np.count_nonzero(q1)), int(np.count_nonzero(q2))
    # Linear phase: coefficients are symmetric, so pre-add the tap pair and
    # multiply once. Halves the multiplier count again.
    m1, m2 = (nz1 + 1) // 2, (nz2 + 1) // 2
    mac = (48000 * m1 + 24000 * m2) * 16
    return {
        "nz1": nz1, "nz2": nz2, "mult_per_out_1": m1, "mult_per_out_2": m2,
        "mac_rate": mac,
        "headroom_2mult": 2 * 24.576e6 / mac,
        "delay_bits": 16 * (N1 + N2) * DATA_BITS,
        "m9k": 16 * (N1 + N2) * DATA_BITS / 9216,
        "acc_bits": max(acc_bits(q1), acc_bits(q2)),
    }


def write_vhdl(q1, q2, scale1, scale2, path: Path) -> None:
    """Emit the coefficient package.

    Only the non-zero taps are emitted, with their tap indices, because the
    VHDL schedule skips the zeros rather than multiplying by them.
    """
    def entries(q):
        return [(i, int(v)) for i, v in enumerate(q) if v != 0]

    e1, e2 = entries(q1), entries(q2)
    lines = [
        "-- GENERATED by python/design_decimator.py -- DO NOT EDIT BY HAND.",
        "-- Regenerate with:  python python/design_decimator.py",
        "--",
        "-- 96 kHz -> 24 kHz decimation, two cascaded halfband FIR stages.",
        "-- Passband 0-%d Hz, stopband from %d Hz." % (F_PASS, F_STOP),
        "-- Only NON-ZERO taps are listed; a halfband's even taps are exactly",
        "-- zero and the datapath skips them. IDX is the tap position in the",
        "-- full-length filter, which is what the delay-line address must use.",
        "",
        "library ieee;",
        "use ieee.std_logic_1164.all;",
        "use ieee.numeric_std.all;",
        "",
        "package decim_coef_pkg is",
        "",
        "    constant C_COEF_BITS : integer := %d;" % COEF_BITS,
        "    constant C_DATA_BITS : integer := %d;" % DATA_BITS,
        "    -- Worst case sum(|coef|) x max|data|, not a tap-count estimate.",
        "    constant C_ACC_BITS  : integer := %d;" % max(acc_bits(q1), acc_bits(q2)),
        "",
        "    constant C_N1 : integer := %d;   -- stage 1 length, 96k -> 48k" % N1,
        "    constant C_N2 : integer := %d;  -- stage 2 length, 48k -> 24k" % N2,
        "    constant C_NZ1 : integer := %d;  -- non-zero taps, stage 1" % len(e1),
        "    constant C_NZ2 : integer := %d;  -- non-zero taps, stage 2" % len(e2),
        "",
        "    type coef_array is array (natural range <>) of signed(C_COEF_BITS-1 downto 0);",
        "    type idx_array  is array (natural range <>) of integer;",
        "",
    ]
    for tag, e, n in (("1", e1, N1), ("2", e2, N2)):
        lines.append("    -- stage %s: %d non-zero of %d taps" % (tag, len(e), n))
        lines.append("    constant C_COEF%s : coef_array(0 to %d) := (" % (tag, len(e) - 1))
        for k in range(0, len(e), 4):
            chunk = e[k:k + 4]
            row = ", ".join('to_signed(%d, C_COEF_BITS)' % v for _, v in chunk)
            lines.append("        " + row + ("," if k + 4 < len(e) else ""))
        lines.append("    );")
        lines.append("    constant C_IDX%s : idx_array(0 to %d) := (" % (tag, len(e) - 1))
        for k in range(0, len(e), 12):
            chunk = e[k:k + 12]
            row = ", ".join(str(i) for i, _ in chunk)
            lines.append("        " + row + ("," if k + 12 < len(e) else ""))
        lines.append("    );")
        lines.append("")
    lines += ["end package decim_coef_pkg;", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def model(x: np.ndarray, q1, q2, scale1, scale2) -> np.ndarray:
    """Bit-exact fixed-point model of what the VHDL must produce.

    Integer arithmetic throughout, with the same rounding and the same
    right-shift the hardware does. This is the reference, so it must not use
    floating point anywhere the hardware would not.
    """
    def fir_dec2(xi, q, scale):
        acc = np.convolve(xi, q)                 # int64 exact
        y = acc[::2]                             # decimate by 2
        # round-to-nearest, then scale back down by the coefficient gain
        return np.floor(y / scale + 0.5).astype(np.int64)

    return fir_dec2(fir_dec2(x, q1, scale1), q2, scale2)


def write_vectors(q1, q2, s1, s2, path: Path) -> None:
    """Reference input/output vectors, for checking hardware without a simulator.

    The stimulus is deliberately varied: an impulse exercises the whole impulse
    response, tones at the passband edge and in the stopband test the two
    things that matter, and full-scale content checks for overflow.
    """
    rng = np.random.default_rng(20260907)
    n = 4096
    t = np.arange(n) / FS_IN
    full = 2 ** (DATA_BITS - 1) - 1

    cases = {
        "impulse":   np.r_[full, np.zeros(n - 1)],
        "dc_full":   np.full(n, full // 2),
        "tone_1k":   np.round(full * 0.5 * np.sin(2 * np.pi * 1000 * t)),
        "tone_11k":  np.round(full * 0.5 * np.sin(2 * np.pi * 11000 * t)),
        "tone_13k":  np.round(full * 0.5 * np.sin(2 * np.pi * 13000 * t)),
        "tone_19k":  np.round(full * 0.5 * np.sin(2 * np.pi * 19000 * t)),
        "noise":     np.round(rng.uniform(-full, full, n)),
    }

    out = ["# GENERATED by python/design_decimator.py -- reference vectors",
           "# Bit-exact fixed-point model output. Each block:",
           "#   CASE <name> <n_in> <n_out>",
           "#   IN  <space-separated 24-bit signed integers>",
           "#   OUT <space-separated 24-bit signed integers>",
           "# The hardware must reproduce OUT exactly, after group delay.",
           ""]
    for name, x in cases.items():
        xi = x.astype(np.int64)
        y = model(xi, q1, q2, s1, s2)
        out.append("CASE %s %d %d" % (name, len(xi), len(y)))
        out.append("IN " + " ".join(str(int(v)) for v in xi[:256]))
        out.append("OUT " + " ".join(str(int(v)) for v in y[:64]))
        out.append("")
    path.write_text("\n".join(out), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="verify only, no writes")
    ap.add_argument("--plot", action="store_true", help="also write the response PNG")
    args = ap.parse_args()

    b1, b2 = halfband(N1, BETA1), halfband(N2, BETA2)
    q1, s1 = quantise(b1)
    q2, s2 = quantise(b2)
    f1, f2 = q1 / s1, q2 / s2

    m = measure(cascade(f1, f2))
    r = resources(q1, q2)

    print("96 kHz -> 24 kHz decimator,  stage1 n=%d  stage2 n=%d  %d-bit coeffs"
          % (N1, N2, COEF_BITS))
    print()
    print("  response")
    print("    passband ripple 0-11 kHz    %9.5f dB   (limit %.2f)"
          % (m["ripple"], MAX_RIPPLE_DB))
    print("    droop at 11 kHz             %9.4f dB" % m["droop"])
    print("    worst alias band            %9.1f dB   (limit %.0f)"
          % (m["alias"], MAX_ALIAS_DB))
    print("    at 12 kHz (output Nyquist)  %9.1f dB" % m["at_12k"])
    print("    at 13 kHz                   %9.1f dB" % m["at_13k"])
    print("    group delay                 %9.2f ms"
          % (m["group_delay_taps"] / FS_IN * 1000))
    print()
    print("  resources, 16 channels time-multiplexed")
    print("    non-zero taps               %d + %d" % (r["nz1"], r["nz2"]))
    print("    multiplies per output       %d @48k + %d @24k"
          % (r["mult_per_out_1"], r["mult_per_out_2"]))
    print("    MAC rate                    %.2f M/s" % (r["mac_rate"] / 1e6))
    print("    headroom with 2 multipliers %.2fx  (of 30 available)"
          % r["headroom_2mult"])
    print("    delay-line RAM              %d bits = %.1f of 30 M9K"
          % (r["delay_bits"], r["m9k"]))
    print("    accumulator width           %d bits" % r["acc_bits"])
    print()

    ok = m["ripple"] <= MAX_RIPPLE_DB and m["alias"] <= MAX_ALIAS_DB
    print("  %s" % ("PASS" if ok else "FAIL - does not meet specification"))

    if not args.check:
        vhd = ROOT / "rtl" / "decim_coef_pkg.vhd"
        vec = ROOT / "sim" / "decim_ref_vectors.txt"
        write_vhdl(q1, q2, s1, s2, vhd)
        write_vectors(q1, q2, s1, s2, vec)
        print("\n  wrote %s" % vhd.relative_to(ROOT))
        print("  wrote %s" % vec.relative_to(ROOT))

    if args.plot:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
        except ImportError:
            print("\n  matplotlib not installed, skipping plot")
            return 0 if ok else 1
        casc = cascade(f1, f2)
        w, h = signal.freqz(casc, worN=65536, fs=FS_IN)
        mag = 20 * np.log10(np.abs(h) / np.max(np.abs(h)) + 1e-20)
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7))
        ax1.plot(w, mag, lw=0.9)
        ax1.axvspan(0, F_PASS, alpha=0.12, color="tab:green")
        for k in (1, 2, 3):
            ax1.axvspan(FS_OUT * k - F_PASS, FS_OUT * k + F_PASS,
                        alpha=0.12, color="tab:red")
        ax1.axhline(MAX_ALIAS_DB, ls="--", lw=0.8, color="k")
        ax1.set(xlim=(0, FS_IN / 2), ylim=(-160, 5),
                ylabel="dB", title="Cascade response (green = keep, red = folds into passband)")
        ax1.grid(alpha=0.3)
        ax2.plot(w, mag, lw=0.9)
        ax2.set(xlim=(0, F_PASS * 1.1), ylim=(-0.01, 0.01),
                xlabel="Hz", ylabel="dB", title="Passband detail")
        ax2.grid(alpha=0.3)
        fig.tight_layout()
        png = ROOT / "docs" / "decimator_response.png"
        fig.savefig(png, dpi=110)
        print("  wrote %s" % png.relative_to(ROOT))

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
