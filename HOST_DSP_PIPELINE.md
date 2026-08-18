# Host DSP Pipeline — Decimate /4 + FLAC

**Status (2026-08-16): design agreed, not yet implemented.**

Reduces the 4-AFE aggregate stream from 70.8 GB/hr to ~9 GB/hr and cuts beamforming
cost 4×, entirely on the host. **No RTL, no PLL, no ADAU1978 register changes.**

---

## The Problem

Four AFEs, each 16 ch × 96 kHz × 24-bit, feeding one Python beamformer.

| | Per AFE | ×4 aggregate |
|---|---|---|
| Wire rate | 45.7 Mbps | 182.9 Mbps = **22.9 MB/s** |
| UDP payload | 4.9 MB/s | 19.7 MB/s |
| Audio samples | 4.6 MB/s | **18.4 MB/s** |
| Packet rate | 12,000 pkt/s | **48,000 pkt/s** |
| Storage | 17.7 GB/hr | **70.8 GB/hr** (566 GB / 8 hr) |

Note the units: **46 Mbps per AFE, not MB/s**. At 22.9 MB/s aggregate, a 1 GbE server
port sits at 18% and any SSD is bored. Neither network nor disk *bandwidth* is the
bottleneck. The two real constraints are **host CPU** and **storage capacity**.

---

## Architecture Decisions Log

### Why not the FPGA-Gzip-compressor core

Evaluated [WangXuan95/FPGA-Gzip-compressor](https://github.com/WangXuan95/FPGA-Gzip-compressor)
and rejected on three independent grounds.

**1. It does not fit EP4CE6E22C8.** Published cost is 8,218 LUT6 + 25×BRAM36K on
Artix-7. Our device has 6,272 LE and 276,480 memory bits, with `TDM_UATR.fit.summary`
already showing 3,890 LE (62%) used — about 2,380 LE free. Ignoring Xilinx block
quantization and counting only irreducible storage:

| Item | Bits | % of device M9K pool |
|---|---|---|
| LZ77 window (16,383 B) | 131,064 | 47% |
| Hash table (4,096 entries) | ~57,000 | 21% |
| Deflate block buffer | 131,064 | 47% |
| **Total** | | **~115%** |

Over 100% of all device RAM before the existing 8,688 bits. Logic is worse: 8,218 LUT6
maps to roughly 12k–18k Cyclone IV 4-LUTs against 2,380 free. Off by 3–7×, not a tuning
margin. (Throughput was never the issue — 128 MB/s vs the 4.6 MB/s needed.)

**2. It would break the TX path.** `udp_tx_core.vhd:59` — `IP_CHECKSUM` is a
compile-time constant *precisely because* the length is fixed at 438. Variable-length
output makes IP total-length, UDP length and the checksum runtime logic, and invalidates
`PAYLOAD_BYTES := 410` and the `byte_cnt = TOTAL_BYTES` terminator.

**3. It is the wrong operation for the problem.** See below.

### Why decimation and not compression alone

Compressed data cannot be beamformed. It must be inflated back to 96 kHz × 64 ch first,
at which point the beamformer sees the identical array it sees today — same FFTs, same
delay-and-sum, same cost, plus the decode.

| | Compression (FLAC) | Decimation /4 |
|---|---|---|
| What is removed | statistical redundancy | the 12–48 kHz band |
| Reversible | yes, exactly | **no, never** |
| Output directly usable | no — must decode | yes — plain PCM |
| Reduces storage | yes | yes |
| **Reduces beamform CPU** | **no — adds decode cost** | **yes, exactly 4×** |
| Ratio | data-dependent | exactly 4×, guaranteed |

Beamforming cost scales as `N_samples × N_channels × N_beams`. Compression changes none
of those three. Decimation cuts the first by 4.

**They are orthogonal and compose.** Decimate first, then compress the result — low-pass
filtering raises sample-to-sample correlation, so FLAC's linear predictor typically does
*better* on decimated data than on the original.

| Approach | Storage | Beamform CPU |
|---|---|---|
| Now | 70.8 GB/hr | 1× |
| FLAC only | ~35 GB/hr | 1× + decode |
| Decimate /4 only | 17.7 GB/hr | 0.25× |
| **Decimate /4, then FLAC** | **~9 GB/hr** | **0.25×** |

### Why /4 and not some other factor

Advisor guidance was 22 kHz *frekuensi sampling* (sampling frequency, i.e. ~11 kHz of
usable band) for speech-band work. 96/22 is not an integer and fractional resampling is
far more expensive than integer, so:

| Decimate | Fs | Usable band | Reduction |
|---|---|---|---|
| /2 | 48 kHz | 24 kHz | 2× |
| /3 | 32 kHz | 16 kHz | 3× |
| **/4** | **24 kHz** | **12 kHz** | **4×** |
| /6 | 16 kHz | 8 kHz | 6× |

/4 gives 12 kHz of band — slightly more headroom than the 11 kHz asked for — on a clean
integer divisor.

Spatial-aliasing cross-check: for a 12 kHz band, `d ≤ c/(2·f_max) = 1500/24000 = 6.25 cm`
element spacing. **If hydrophone spacing ≤ 6.25 cm, /4 costs nothing usable.** If spacing
is wider, the array was already the limiting factor and the stream can be decimated
harder. *This has not been confirmed — see Open Items.*

### Why on the host and not in the FPGA

A time-multiplexed FIR decimator would fit (a few hundred LE, and there are 256 BCLKs per
audio frame at 24.576 MHz = 16 cycles per channel per sample). It would also cut network
and packet rate, which the host version does not.

It is still the wrong place to start. The clock tree on this board is demonstrably fussy:
commit `a4ba519` records 192×fS (18.432 MHz) *rejected on hardware*, and `tdm8_rx.vhd:27`
records the part reading `PLL_LOCK=0` at 18.4332 MHz while all four locked at 24.576 MHz.
Host-side decimation delivers 4× on both stated problems while `clk_18m` stays bolted to
PLL tap c2 and `adau_sequencer` never sees a changed MCS value.

Revisit the FPGA decimator only if packet rate or link load becomes the binding
constraint. It is not today.

### Naming hazard

`clk_18m` in `top_system.vhd` **carries 24.576 MHz**, not 18.432 MHz. It is wired to PLL
output c2 (`top_system.vhd:923-925`); the 18.432 MHz tap c1 is `open`. The name is legacy
from before 192×fS was rejected. Renaming it to `clk_bclk` or `clk_24m576` is a mechanical
change and would stop this recurring.

---

## Pipeline

```
  4× AFE (UDP :5005)                HOST
  ──────────────────                ────
  16 ch @ 96 kHz 24-bit
  12,000 pkt/s each      ┌──────────────────────────────────┐
        │                │ 1. INGEST (one process per AFE)  │
        ├───────────────►│    vectorized parse, seq-gap     │
        │                │    detect + zero-fill            │
        │                └───────────────┬──────────────────┘
        │                                │ (n,16) int32 @ 96 kHz
        │                ┌───────────────▼──────────────────┐
        │                │ 2. INTER-AFE ALIGNMENT           │
        │                │    MUST be at 96 kHz — see below │
        │                └───────────────┬──────────────────┘
        │                                │ aligned, 64 ch @ 96 kHz
        │                ┌───────────────▼──────────────────┐
        │                │ 3. ANTI-ALIAS FIR + /4 SUBSAMPLE │
        │                │    stateful, block-continuous    │
        │                │    one Decimator per AFE         │
        │                └───────────────┬──────────────────┘
        │                                │ (n/4,16) int32 @ 24 kHz
        │                     ┌──────────┴──────────┐
        │                     ▼                     ▼
        │          ┌────────────────────┐  ┌──────────────────┐
        │          │ 4a. BEAMFORMER     │  │ 4b. FLAC WRITER  │
        └─────────►│     64 ch working  │  │  8 files × 8 ch  │
                   │     set, 0.25× CPU │  │  ~9 GB/hr total  │
                   └────────────────────┘  └──────────────────┘
```

---

## Stage 1 — Ingest

**This is the current bottleneck and must be fixed first, independently of decimation.**

`udp_monitor.py:97-105` decodes with a nested Python loop calling `int.from_bytes` once
per sample: 48,000 pkt/s × 128 samples = **6.1M calls/s**, plus 48,000 `recv()` syscalls/s.
That cannot keep up at any data rate.

The correct vectorized pattern **already exists in this repo** at `mixer.py:78-83`:

```python
def decode(payload):
    """Payload bytes -> (frames, 16) int32."""
    body = payload[um.HDR_LEN:]
    n = len(body) // um.FRAME_LEN
    if n == 0:
        return None
    raw = np.frombuffer(body[:n * um.FRAME_LEN], dtype=np.uint8)
    raw = raw.reshape(n, um.FRAME_LEN)[:, 2:]          # drop debug + frame index
    raw = raw.reshape(n, um.CHANNELS, um.SAMPLE_BYTES).astype(np.int32)
    v = (raw[:, :, 0] << 16) | (raw[:, :, 1] << 8) | raw[:, :, 2]
    return np.where(v & 0x800000, v - 0x1000000, v)
```

Port this into the record/beamform path. Expect 50–100× on the parse.

**Syscall side:** `recvmmsg` is not in Python's stdlib `socket`, so the practical levers
are (a) one receiver process per AFE, and (b) larger packets in the FPGA. Raising
`packet_formatter` from 8 to 29 frames/packet (1460 B payload, still inside MTU) cuts
48,000 → 13,240 pkt/s. That is a small, well-understood RTL change and is worth more here
than its ~8% wire saving. Optional; not required for this pipeline.

**Sequence gaps are mandatory to handle.** Header bytes 4–7 carry `seq_num`
(`packet_formatter.vhd:90-93`). A dropped packet must be **zero-filled, not skipped** — a
skipped packet shifts every subsequent sample by 8 frames, which silently destroys both
the decimation phase and inter-channel beamforming alignment. Log gap count and location.

---

## Stage 2 — Inter-AFE alignment (must precede decimation)

The four AFEs run independent `pll_audio` instances from independent crystals, so their
sample grids drift relative to each other. Beamforming across AFEs requires them aligned
to a common grid.

**This stage must run at 96 kHz, before decimation.** The alignment granularity available
from integer sample shifts collapses when you decimate:

| Rate | 1 sample | Apparent element position error @ 1500 m/s |
|---|---|---|
| 96 kHz | 10.4 µs | **1.6 cm** |
| 24 kHz | 41.7 µs | **6.25 cm** — the entire assumed element spacing |

At 24 kHz a single-sample shift is as large as the array spacing the /4 decision was
justified against, so after decimation the AFEs **cannot be aligned by integer shifts at
all** — recovering what one sample buys at 96 kHz would require fractional-delay
interpolation. Align first, then decimate.

Consequence for stage 3: each AFE gets **its own `Decimator` instance**, fed from an
already-aligned stream. The class below is sized per channel count, not per AFE.

The alignment mechanism itself is unresolved — see Open Item 4. It is the one item on
this page that can invalidate the beamformer regardless of how well the DSP works.

---

## Stage 3 — Anti-alias filter and /4 subsample

### The filter is not optional

Naïve `x[::4]` folds everything between 12 kHz and 48 kHz back into the retained band as
false signal that is indistinguishable from real targets. The stream **must** be low-passed
below the new 12 kHz Nyquist first.

### Specification

| Parameter | Value | Rationale |
|---|---|---|
| Input Fs | 96,000 Hz | unchanged from ADC |
| Output Fs | 24,000 Hz | |
| Passband | 0 – 10,000 Hz | |
| Stopband | 12,000 Hz | new Nyquist |
| Stopband atten. | ≥ 100 dB | below the ~102 dB ADAU1978 DR floor |
| Phase | linear (FIR) | preserves inter-channel timing — **required for beamforming** |

**Use FIR, not IIR.** An IIR low-pass has non-linear phase, which applies a
frequency-dependent delay. Across a beamforming array that is indistinguishable from a
position error and will smear the beam pattern.

### Streaming structure

Block-based `resample_poly` / `decimate` calls do **not** maintain filter state, so each
block boundary injects a discontinuity. For a continuous recording that is unacceptable.
Carry state explicitly:

```python
from scipy.signal import firwin, lfilter
import numpy as np

DECIM   = 4
FS_IN   = 96000
FS_OUT  = FS_IN // DECIM          # 24000
NTAPS   = 321                     # odd -> integer group delay

# Kaiser-windowed FIR, ~100 dB stopband, 10 kHz -> 12 kHz transition.
# beta = 0.1102*(A - 8.7) = 10.06 for A = 100 dB; cutoff is the -6 dB point,
# i.e. the centre of the transition band. NTAPS from (A-8)/(2.285*dw) = 308 -> 321.
FIR = firwin(NTAPS, cutoff=11000, fs=FS_IN, window=('kaiser', 10.06))

class Decimator:
    """Stateful /4 with anti-alias FIR. Block-continuous, no edge artifacts."""
    def __init__(self, n_ch, taps=FIR, decim=DECIM):
        self.b = taps
        self.decim = decim
        self.zi = np.zeros((len(taps) - 1, n_ch))
        self.phase = 0                       # subsample phase across blocks

    def __call__(self, x):                   # x: (n, n_ch) float64
        y, self.zi = lfilter(self.b, 1.0, x, axis=0, zi=self.zi)
        out = y[self.phase::self.decim]
        # keep phase continuous into the next block
        self.phase = (self.phase - len(x)) % self.decim
        return out
```

`self.phase` is what makes this correct across blocks — without it, a block whose length
is not a multiple of 4 shifts the decimation grid and the channels drift apart.

### Cost, and the optimization if it does not keep up

Single-stage `lfilter` computes every input sample then discards 3 of 4:
`321 taps × 64 ch × 96,000 = 1.97 GMAC/s`. That is likely too slow for single-threaded
scipy. **Benchmark before assuming it works.**

If it does not, use a **two-stage halfband cascade** (/2 at 96 kHz, then /2 at 48 kHz).
Halfband filters have every other tap zero, and the second stage runs at half rate:

| Stage | Rate | Taps | Effective MAC/s (64 ch) |
|---|---|---|---|
| 1 (/2) | 96 kHz | 63 (32 non-zero) | ~98 M |
| 2 (/2) | 48 kHz | 63 (32 non-zero) | ~49 M |
| **Total** | | | **~150 M** — 13× cheaper |

Combined with polyphase evaluation (compute only retained outputs, via `upfirdn` with
manual state), this comfortably fits one core per AFE.

### Back to integer — do not skip the clip

`lfilter` returns float64; FLAC needs integers. A 321-tap FIR has passband ripple and can
overshoot a full-scale input past ±(2²³−1). An unchecked `.astype(np.int32)` truncates
toward zero and, worse, wraps silently on overflow — a full-scale positive peak becomes a
large negative sample. Clip explicitly:

```python
out = np.clip(np.rint(y_float), -(1 << 23), (1 << 23) - 1).astype(np.int32)
```

`np.rint` (round-half-even) rather than a bare cast, so the decimated stream is not biased
toward zero by up to 1 LSB on every sample.

---

## Stage 4b — FLAC writer

### Channel count constraint

**FLAC's format caps at 8 channels.** libFLAC, libsndfile and `soundfile` all enforce it.
64 channels cannot go in one file.

Natural split — **8 files of 8 channels**, two per AFE, matching the existing `tdm8_rx`
A/B halves and the ADAU1978 chip pairing in the README:

| File | AFE | Channels | Source |
|---|---|---|---|
| `afe0_A.flac` | 0 | 1–8 | `ch_data_A` (chips 0,1) |
| `afe0_B.flac` | 0 | 9–16 | `ch_data_B` (chips 2,3) |
| … | | | |
| `afe3_B.flac` | 3 | 9–16 | `ch_data_B` (chips 2,3) |

This keeps a file boundary on a boundary that already exists in the hardware.

### Settings

| Parameter | Value |
|---|---|
| Sample rate | 24,000 Hz |
| Bit depth | 24-bit (`PCM_24`) |
| Channels | 8 per file |
| Compression level | 5 (default) — level 8 costs much more CPU for ~1% |

```python
import soundfile as sf

w = sf.SoundFile(path, mode='w', samplerate=FS_OUT,
                 channels=8, subtype='PCM_24', format='FLAC')
w.write(block_int32)     # (n, 8) — SEE SCALING NOTE BELOW
```

### ⚠ Verify the int24 → int32 scaling before the soak test

**Unresolved: `soundfile` is not installed on this machine, so this was not tested.**

libsndfile's `sf_writef_int` may treat an int32 input array as **full-scale int32**, in
which case a 24-bit sample must be shifted `<< 8` before writing. If that is the case and
the shift is omitted, the recording lands **~48 dB below** where you think it is — quiet
but otherwise plausible-looking, which is exactly the kind of bug that survives a casual
listen and corrupts every level measurement downstream.

Settle it with a two-line discriminator before writing any real data:

```python
import numpy as np, soundfile as sf
v = 1 << 22
sf.write('t.flac', np.full((100, 8), v, dtype='int32'), 24000,
         subtype='PCM_24', format='FLAC')
print(hex(int(sf.read('t.flac', dtype='int32')[0][0, 0])))
# 0x400000  -> int24 convention, write as-is
# 0x40000000 -> full-scale int32 convention, shift << 8 on write
```

Validation item 4 (round-trip) will catch this, but it surfaces as a bit-exactness
failure rather than a level error, which is a confusing way to find it. Check it first.

Run the writer **off the ingest path** — separate process or thread with a bounded queue.
A blocked disk write must never stall the socket reader. Bound the queue and count drops
rather than growing memory without limit.

### Expected sizes

| Stage | Rate | Per hour |
|---|---|---|
| Raw 96 kHz 24-bit, 64 ch | 18.4 MB/s | 66.3 GB |
| After /4 | 4.6 MB/s | 16.6 GB |
| After /4 + FLAC (~50%) | ~2.3 MB/s | **~9 GB** |

FLAC ratio is signal-dependent and **has not been measured** — see Open Items.

---

## Validation

Before trusting the pipeline:

1. **Decimation correctness** — feed a synthetic 1 kHz tone at 96 kHz, confirm it appears
   at 1 kHz in the 24 kHz output at the same amplitude.
2. **Alias rejection** — feed an 18 kHz tone (inside the discarded band). It must be
   attenuated ≥ 100 dB, **not** appear as a 6 kHz artifact. This is the test that catches
   a missing or misconfigured anti-alias filter.
3. **Block continuity** — decimate a long ramp in blocks of deliberately non-multiple-of-4
   length (e.g. 1000, 999, 1001). Output must be identical to the same input decimated in
   one call. Catches `phase` and `zi` handling errors.
4. **FLAC round-trip** — write and read back, assert bit-exact against the input array.
   FLAC is lossless; anything else means a subtype or scaling bug.
5. **Inter-channel phase** — same tone into two channels with a known delay; confirm the
   delay survives decimation unchanged. This is what protects the beam pattern.
6. **No overflow wrap** — full-scale square wave in. FIR passband ripple overshoots
   ±(2²³−1); confirm the output clips rather than wrapping to large negative values.
7. **FLAC scaling** — the `1 << 22` discriminator above, run before anything else in
   this list.
8. **Sustained-rate soak** — 1 hour with all four AFEs live. Zero sequence gaps attributable
   to the host, bounded queue depth, storage rate matching the table above.

---

## Open Items

**1. Irreversibility of recording decimated-only.** Once the 12–48 kHz band is discarded
before recording, it is gone permanently. This is the requested design and the numbers
above assume it. Flagging it because it is a one-way door: if anything of interest to UATR
lives above 12 kHz (propeller cavitation and some DEMON analyses can), it cannot be
recovered later. **Suggested mitigation:** during the validation phase, record a full-rate
FLAC archive in parallel (~35 GB/hr) and confirm from real data that the 12–48 kHz band is
empty before committing to decimated-only recording.

**2. Hydrophone element spacing is unconfirmed.** The /4 choice assumes ≤ 6.25 cm. Confirm
against the actual array geometry.

**3. FLAC ratio is unmeasured.** `_raw.bin` is a decompressed PDF stream of the ADAU1978
datasheet, and both `Wireshark/*.pcapng` are dead-silent on every channel (constant
`0xFFFFFF` on ch 0–7, `0x000000` on ch 8–15; they predate the 4-ADC bringup). The ~50%
figure is a general expectation for hydrophone data, not a measurement of this system.
**A 10-second live capture with all four AFEs running would settle both this and Open
Item 2.**

**4. Inter-AFE sample alignment — the highest-risk item on this page.** Each AFE runs its
own `pll_audio` from its own crystal: four independent, drifting time bases. One sample of
skew at 96 kHz is 10.4 µs ≈ **1.6 cm of apparent element position error** at 1500 m/s, and
it accumulates over a run.

This is not merely orthogonal to the decimator — it **constrains the pipeline order**, which
is why it now has its own stage (Stage 2). Alignment must happen at 96 kHz, because at
24 kHz one sample is 6.25 cm, equal to the entire element spacing the /4 factor was
justified against.

Two things must be determined:

- **Is there shared MCLK/LRCLK distribution between AFEs, or any sync mechanism?**
  `top_system.vhd:304` notes MCLK and BCLK share a net *within* one board (pin 113 → U2
  fanout). Whether anything ties the four boards together is unknown from this repo.
- **If not, what is the measured drift rate?** Two AFEs recording the same acoustic event
  will show a slowly growing offset; that rate sets how often re-alignment is needed and
  whether a free-running arrangement is viable at all.

No amount of data-rate work matters if the four streams cannot be aligned. Resolve this
before or alongside the decimator.

**5. Stale constant.** `udp_monitor.py:38` — `EXPECTED_PPS = SAMPLE_RATE / FRAMES_PKT`
carries the comment `# 6000 at 48 kHz`. `SAMPLE_RATE` is 96000, so the value is 12000.
The arithmetic is right; the comment is stale.
