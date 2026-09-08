# 96 kHz → 24 kHz decimation, and the gain budget that goes with it

Written 2026-09-07. Covers two independent changes that came out of the same
conversation:

1. **Set the ADC PGA.** A runtime change, no rebuild, worth ~24 dB of SNR that
   is currently being thrown away. Do this first — it is free.
2. **Move the 4× decimation onto the FPGA.** Cuts the uplink 4×, which takes the
   four-board array from *needs gigabit* to *fits in 100BASE-TX*.

They are unrelated in the hardware and can be done in either order. The gain
setting is reversible in seconds; the decimator is a build.

---

## Part 1 — The gain budget

### The chain as built

```
hydrophone  -173 dBV re 1 uPa
    |
THAT1512 preamp, +12 dB          on the PCB
    |
OPA1632 differential driver
    |
ADAU1978, PGA 0 to +60 dB        register 0x0A-0x0D, gain = 60 - 0.375 x N
    |                            103 dB dynamic range typ (109 max)
24-bit sample
```

### The numbers

Ambient ocean noise at sea state 2, integrated over 10 Hz – 11 kHz, is about
100 dB re 1 µPa. Through a −173 dBV element that is:

```
signal at element          -73.1 dBV  =  221 uV
+12 dB THAT1512            -61.1 dBV
ADC full scale (2 V rms)     6.0 dBV
                           ---------
level at converter         -67.1 dBFS
```

Now compare the two noise sources that matter:

```
THAT1512 input noise  ~1.3 nV/rtHz x sqrt(11 kHz) = 136 nV = -137 dBV
  x12 dB, referred to ADC full scale                       = -131 dBFS
ADAU1978 noise floor (103 dB dynamic range)                = -103 dBFS
                                                             --------
the converter is noisier than the analog chain by            ~28 dB
```

**The THAT1512 is doing its job — it is quiet enough that the converter cannot
see how quiet it is.** With the PGA at its default the system is limited by the
ADC, not by the preamp or the sea, and roughly 28 dB of achievable SNR is going
unused.

### What to set

The PGA sits *after* the preamp and *before* the converter's noise, so raising
it lifts the signal above the ADC floor without amplifying that floor.

| PGA | byte | level at ADC | headroom above ambient | penalty |
|---|---|---|---|---|
| 0 dB (default) | `0xA0` | −67 dBFS | 67 dB | wasting ~28 dB |
| **+24 dB** | **`0x60`** | **−43 dBFS** | **43 dB** | **~1 dB — start here** |
| +30 dB | `0x50` | −37 dBFS | 37 dB | ~0.5 dB |

```
python python/ctrl.py --node 1 --all 0x60
```

Runtime, over the existing UDP control path, no rebuild. Encoding is
`gain = 60 − 0.375 × N` (`rtl/adau_sequencer.vhd:159`).

**+24 dB is the recommended starting point** — it captures nearly all the
available SNR while keeping 43 dB of headroom for vessel transients, which run
well above ambient.

Then check `clip seen:` in `udp_monitor.py`. `ASDC_CLIP` (0x19) is polled
continuously (`adau_sequencer.vhd:230`) and surfaced in `dbg_status6`, so it
reports immediately if a setting is too hot. Back off one step if it trips on
transients rather than continuously.

### Two things to verify

- **Source impedance.** The THAT1512 is a bipolar-input mic preamp designed for
  ~150 Ω sources: low voltage noise, but meaningful *current* noise, which
  becomes voltage across a high source impedance. If the hydrophone is a bare
  piezo element (capacitive, high-Z at low frequencies) rather than one with an
  integral buffer, current noise may dominate below a few hundred Hz and the
  figures above are optimistic at the bottom of the band. Worth knowing the
  element's output impedance before trusting the 10 Hz end.
- **The 10 Hz end itself.** Nothing in the decimation path affects it. It is set
  by the input AC-coupling (C304 etc.) and the ADAU1978's HPF setting. Confirm
  10 Hz actually survives to the ADC output before designing around it.

### No analog anti-alias filter

The THAT1512 is wideband (MHz) and passes everything to the converter. All
anti-alias protection above 48 kHz is therefore the ADAU1978's own decimator:
**79 dB stop-band attenuation, stopband from 0.5625 × fS = 54 kHz**
(`docs/adau1978.pdf` p.4). That is adequate for what is known to be up there,
but it means there is no analog filter in the chain — worth confirming whether
any RC network exists ahead of the OPA1632.

### The altimeter question, settled

Each buoy carries a Blue Robotics Ping1D altimeter pinging at **115 kHz, every
50 ms** (`docs/TELEMETRY_INTEGRATION.md:146`). It is not connected to the FPGA,
but that is not why it is harmless — it is an acoustic source in the same water
as the hydrophones, and coupling would be acoustic, not electrical.

Nor is "we don't listen that high" protective: sampling at 96 kHz folds 115 kHz
to |115 − 96| = 19 kHz, and the ÷4 would fold 19 kHz to **5 kHz**, mid-band.
Being far above the band of interest is exactly the condition that produces
aliasing.

**It is nonetheless a non-issue**, because 115 kHz sits well inside the
ADAU1978's stopband and is crushed by that 79 dB *inside the converter*, before
the FPGA sees anything. Combined with a downward-beaming transducer and
hydrophones that roll off above their design band, there is nothing to fix.

Recorded because the mechanism matters: a future sensor operating *below*
42 kHz would sit in the ADC's passband and get no such protection.

Cheap confirmation, if wanted: coupling would appear as transients at exactly
20 Hz (the 50 ms ping interval) in `udp_monitor.py`'s glitch detection.

---

## Part 2 — The decimator

### Why not a CIC

A CIC (cascaded integrator-comb) is the obvious multiplier-free choice and it
**does not work for this band**. At N=3, R=4, fS=96 kHz:

| frequency | role | response |
|---|---|---|
| 11 kHz | top of the band of interest | **−9.2 dB** droop |
| 13 kHz | folds onto 11 kHz | **−13.3 dB** |

A 13 kHz tone would land on top of the 11 kHz signal only **4.1 dB below it**.
Raising the order makes it worse, not better — N=5 gives −15.3 dB of droop at
11 kHz. The CIC's first null is pinned at 24 kHz and no choice of N moves the
transition down to 11 kHz.

CIC is the right answer for a narrow band (it would be fine for 100–1500 Hz).
**11 kHz out of a 12 kHz Nyquist is 92% of the band — a brick-wall requirement,
and a CIC is the bluntest filter there is.**

And plain sample-dropping is worse still: discarding 3 of every 4 samples with
no filter folds everything from 13 kHz to 42 kHz into the band at **full
amplitude, 0 dB rejection**. The ADAU1978 passes content to 42 kHz
(0.4375 × fS), so that energy genuinely is present.

### What is built instead

Two cascaded **halfband FIR** stages, 96k → 48k → 24k. Halfband because every
even tap except the centre is exactly zero (halving the multiplies), and linear
phase because the coefficients are symmetric (halving them again).

| stage | rate | length | non-zero | folded taps (multiplies/output) |
|---|---|---|---|---|
| 1 | 96 → 48 kHz | 27 | 15 | 8 @ 48 kHz |
| 2 | 48 → 24 kHz | 171 | 87 | 44 @ 24 kHz |

Lengths were chosen by exhaustive search over (n, beta) for the cheapest pair
still meeting the ripple and alias limits. Do not hand-tune them: shortening
either stage breaks the alias limit, and lengthening costs cycles the schedule
has budgeted.

Coefficients are 20-bit signed, generated by `python/design_decimator.py` into
`rtl/decim_coef_pkg.vhd`.

### Measured response

Verified on the quantised cascade, not the float design:

```
passband ripple 0-11 kHz      0.00015 dB      (limit 0.01)
droop at 11 kHz              -0.0001  dB
worst alias band             -102.5   dB      (limit -100)
at 12 kHz (output Nyquist)     -6.0   dB
at 13 kHz                    -120.3   dB
group delay                     1.91  ms
```

**−102 dB of alias rejection sits below the ADAU1978's own 103 dB dynamic
range**, so aliased content lands under the converter's noise floor and cannot
degrade anything, whatever is actually up there. This is why no spectrum
measurement was needed to size the filter — designing to the noise floor is
assumption-free, and the headroom made the optimisation not worth a bench
session.

Passband droop of 0.0001 dB means **no compensation FIR is needed**. That was
flagged as an open question; it is answered.

### Built and fitted — measured, not estimated

Quartus 25.1std, `EP4CE6E22C8`, all four node images:

```
Total logic elements   5,308-5,343 / 6,272  (85%)   24K images
                       3,429-3,455 / 6,272  (55%)   96K images
Dedicated registers          3,603 / 6,272  (57%)
Embedded multipliers            14 / 30     (47%)
Total memory bits          164,194 / 276,480 (59%)
Design-wide TNS       0.0 on setup, hold, recovery, removal, min pulse width
```

Worst-case setup slack is +3.643 ns on `rmii_clk`, the pre-existing Ethernet
path, unchanged by this work. The decimator costs ~1,880 LEs, which is the
measured difference between the two image sets.

> ⚠ **SignalTap had to be removed from the QSF to make this fit.**
> `ENABLE_SIGNALTAP` was `ON` with `signaltap_rmii.stp`, and its capture buffer
> was consuming M9K blocks the decimator needs. It is a debug instrument, not
> part of the design, and it should not have been in deployment images anyway —
> but be aware the four 96 kHz NODE images were built *with* it. Re-enabling it
> will break the fit while `C_DECIMATE` is true.

#### Three things the fit taught that the paper design did not

1. **`mod` on a non-power-of-two synthesises a hardware divider.** `D2` was
   briefly 192, and `mod D2` produced two `lpm_divide` instances — **282 LEs**
   of real divider. The wrap is now a conditional subtract. Never write `mod`
   on these address paths.
2. **Memory BLOCKS bind before memory BITS.** At 24-bit width an M9K holds only
   256 words, so the design can exhaust all 30 blocks while showing 60% bit
   utilisation. Padding `D2` from 171 to 256 costs nothing in LEs and costs 11
   extra M9K — it broke the fit.
3. **Quartus duplicates a RAM that needs two reads plus a write**, whether or
   not you ask it to. Two reads + one write does not map to one M9K's two
   ports, so `ram2` became `ram2_rtl_0` and `ram2_rtl_1` automatically. The
   duplication is unavoidable; what matters is keeping its depth exact.

### Resources, against a device that is already 64% full

The shipping build (`output_files/TDM_UATR.fit.summary`) uses:

```
logic elements   4,025 / 6,272  (64%)
registers        3,047
multipliers          0 / 30     (0%)     <- completely unused
memory bits      8,674 / 276,480 (3%)
```

The decimator is therefore built as **one time-multiplexed core, not 16 parallel
instances.** `tdm16_valid` fires once per audio frame in the 24.576 MHz
`clk_18m` domain — **256 clock cycles between samples** — so there is ample time
to sequence all 16 channels through shared arithmetic.

```
two independent engines, one multiplier and one deadline each:
  engine 1  fires every 2 frames ( 512 cyc)  uses 144  ->  28%
  engine 2  fires every 4 frames (1024 cyc)  uses 720  ->  70%

multipliers   2 of 30   (14 of 30 nine-bit elements)
delay RAM     ram1 duplicated (2R+1W), ram2 single true-dual-port
coeff ROM     52 x 20 bit
accumulator   sum(|coef|) x max|data|, exact   =  45 bits

Both engines are PIPELINED, one tap per cycle. An ADDR/MAC two-state loop costs
two cycles per tap and puts engine 2 at 1,440 cycles - over its deadline, where
e2_go pulses are missed and output frames vanish silently. See
docs/DECIMATOR_FINDINGS.md section 3.2.
```

**Sixteen parallel instances would not fit.** At 30-bit accumulators a parallel
CIC alone needs ~274 flip-flops per channel — 4,384 registers against 6,272
total, of which 3,047 are already used. Cyclone IV E has one flip-flop per LE
and no LUT-based distributed RAM, so every array lands in M9K regardless. The
time-multiplexed form spends the multipliers and M9K blocks that are sitting
idle instead of the LEs that are nearly gone.

### Where it goes

`tdm16_merge` emits a **flat 384-bit parallel register** with a one-cycle strobe
(`rtl/tdm16_merge.vhd:65`), and `packet_formatter` consumes exactly that. So the
decimator is a **drop-in with identical ports on both sides**, spliced between
`u_merge` and `u_fmt` at `rtl/top_system.vhd:1396-1410`.

No slot decoder or encoder is needed — the merged bus is already a parallel
snapshot of all 16 channels, not a serial TDM stream.

Channel alignment is preserved for free: `tdm16_merge.vhd:28-40` documents that
A and B are captured on the same clock edge from the same LRCLK chain, so all 16
channels are mutually aligned by construction. One shared decimator schedule
keeps them that way — which is what GCC-PHAT cross-correlation needs.

> ⚠ **Naming collision.** "TDM16" means two different things in this repo.
> `tdm16_merge` is active and shipping. `tdm16_rx` is a *board-level* config
> putting all four ADCs on one SDATA net at 16-bit — **not active**, and it
> requires fitting the R21/R122 jumper (`docs/TDM16_BRINGUP.md`). The decimator
> concerns the former only. Do not fit the jumper.

### What it buys

```
                      per board      four boards
now (96 kHz)          45.7 Mbit/s    182.8 Mbit/s   <- needs gigabit
after 4x decimation   11.4 Mbit/s     45.7 Mbit/s   <- fits 100BASE-TX
+ max-MTU packing     10.1 Mbit/s     40.5 Mbit/s
```

This removes the gigabit requirement documented in `docs/MULTI_BOARD.md`
("That does not fit in 100BASE-TX. The switch uplink and the PC NIC must be
gigabit"), which matters given the 7 km fiber and media converters.

Packet rate drops from ~12,000/s to ~3,000/s, which matters more than the
bandwidth — host-side packet rate is the usual real bottleneck.

---

## Part 3 — Verification without ModelSim

`docs/MULTI_BOARD.md` records that **there is no simulator licence on this
machine**, which is why `top_system.vhd` carries static concurrent assertions
that Quartus evaluates at elaboration and fails the build on.

`python/design_decimator.py` is built around that constraint. The same script
that designs the coefficients also emits a **bit-exact fixed-point reference
model** of the output, into `sim/decim_ref_vectors.txt`. Because coefficients
and reference come from one file, they cannot drift apart.

```
python python/design_decimator.py           design, verify, write outputs
python python/design_decimator.py --check   verify only, exit 1 on regression
python python/design_decimator.py --plot    also write the response PNG
```

`--check` is the regression gate: it re-measures ripple and alias rejection
against the stated limits and fails if a coefficient edit breaks them. It is a
natural addition to whatever runs `check_sync.py`.

Test cases in the vector file: impulse (exercises the full impulse response),
full-scale DC (overflow), tones at 1 kHz / 11 kHz (passband edge) / 13 kHz and
19 kHz (stopband and the fold-down case), and full-scale noise.

### The integration bug to watch for

`valid_out` pulses at 24 kHz, not 96 kHz. Everything downstream must **wait for
the strobe** rather than assume a sample is present every frame. This is the
single most common CIC/FIR decimator integration bug, and here it would present
as a packet rate 4× too high with repeated samples — a symptom this project has
seen before, from the `tdm16_merge` level-versus-edge bug fixed in `927aac7`.

---

## Part 4 — Transport: UDP is already the right choice

Asked and answered, recorded so it is not re-litigated:

| option | verdict |
|---|---|
| **UDP (current)** | **Correct. Keep it.** |
| TCP | Not feasible on this FPGA (connection state, retransmit buffers, congestion control) and *wrong* for continuous acquisition — head-of-line blocking turns one lost packet into a multi-ms stall of the whole stream |
| Raw Ethernet L2 | Saves 28 bytes (~6%), costs raw sockets, admin rights, npcap on Windows, and all existing tooling. Not worth it |
| AES67 / Dante / AVB-TSN | Buys interoperability and PTP clock sync that a closed point-to-point link where you own both ends does not need. PTP hardware timestamping alone would dwarf the decimator |
| RTP over UDP | 12 bytes for standard-tooling compatibility. The `AD A1 97 78` magic + 32-bit sequence number already do the essential job. Only worth it for off-the-shelf receivers like GStreamer |

### The remaining win is packet size, not protocol

```
now (8 frames/pkt):    410 B payload in 476 B on wire  ->  86% efficient, 3000 pkt/s
max MTU (28 frames):  1410 B payload in 1476 B on wire ->  95% efficient,  857 pkt/s
```

Another ~11% off the wire and a 3.5× drop in packet rate, for 1.17 ms of
buffering instead of 0.33 ms.

> ⚠ The README warns about exactly this: *"Changing the payload size requires the
> IPv4 total length, UDP length, FIFO terminator, packet parser, and
> checksum-related checks to be updated together."* Do it as its own commit, not
> bundled with the decimator.

---

## Part 5 — Data quality under packet loss

### The invariant that matters most

**A lost packet must be replaced, not skipped.** If the host concatenates only
what arrives, every subsequent sample shifts earlier. At 24 kHz one lost 8-frame
packet shifts everything by 333 µs — **50 cm of acoustic path** at 1500 m/s,
permanently and cumulatively. For bearing work that is fatal.

The README already specifies gap-filling rather than shifting, and
`loss_report()` (`python/udp_monitor.py:112`) detects gaps from the sequence
number. Keep that invariant rigid in any new host code.

### Mark gaps, do not merely fill them

Zero-fill (with a short fade to avoid a broadband click) preserves timing;
hold-last-value does not — a held DC step is a wideband transient that smears a
correlation. Better still, carry a per-window "contains fabricated samples" flag
so GCC-PHAT can **exclude** those windows rather than correlate on invented
data. A bearing computed from zero-fill is worse than no bearing.

### Where loss actually comes from here

On a dedicated point-to-point path (FPGA → media converter → 7 km fiber →
converter → NIC) with no competing traffic, wire loss is essentially zero —
7 km of SM fiber at BER 1e-12 is roughly one FCS-dropped frame per day. The
README reports **zero FPGA-side sequence gaps**.

So in practice "packet loss" here means **host socket buffer overflow**, and
`udp_monitor.py:445` already says so in its own diagnostics.

**Which makes decimation the single best loss-resilience change available** — it
cuts bandwidth, packet rate and host CPU load 4× at once. `SO_RCVBUF` is already
at 64 MB (`udp_monitor.py:46`), so the host side is otherwise well built.

### If measured loss turns out non-zero

XOR FEC is the FPGA-friendly answer: one parity packet per N data packets
(parity = XOR of all N payloads) makes any single loss in a group exactly
recoverable, for a 410-byte accumulator and an XOR. Cost is 1/N bandwidth
(N=8 → 12.5%), affordable at 45.7 Mbit/s aggregate.

**Do not build it speculatively — measure first.**

Retransmission via the existing `udp_rx_core` back-channel is technically
possible but would need ~60% of M9K for the replay buffer, competing directly
with the decimator's delay lines. Not worth it.

---

## Order of work

1. **Set the PGA to `0x60`** — runtime, no rebuild, ~24 dB of SNR. Check
   `clip seen:` after.
2. **Confirm the source-impedance and 10 Hz questions** in Part 1.
3. **Build the decimator** — coefficients already generated; splice between
   `u_merge` and `u_fmt`.
4. **Resize packets toward max MTU** — separate commit.
5. **XOR FEC only if measured loss is non-zero.**

## The four images

Built with `C_DECIMATE = true`. `C_NODE` is the only per-board edit.

| node | IP | UDP port | image |
|---|---|---|---|
| 1 | 192.168.1.101 | 5005 | `output_files/24K_NODE1_192-168-1-101.jic` |
| 2 | 192.168.1.102 | 5006 | `output_files/24K_NODE2_192-168-1-102.jic` |
| 3 | 192.168.1.103 | 5007 | `output_files/24K_NODE3_192-168-1-103.jic` |
| 4 | 192.168.1.104 | 5008 | `output_files/24K_NODE4_192-168-1-104.jic` |

The 96 kHz `96K_NODE*` images remain in `output_files/` and are the fallback.

**Flash and verify one board at a time**, per `docs/MULTI_BOARD.md` — check the
number in the filename against the board actually connected, then `ping`,
`arp -a` to confirm the MAC, then capture. Four near-identical images is exactly
the situation where the wrong one lands on the wrong board, and the symptom
looks like a network fault rather than a flashing mistake.

### What to expect on the first capture

| check | 96 kHz (before) | 24 kHz (after) |
|---|---|---|
| packet rate | ~12,000/s | **~3,000/s** |
| per-board wire rate | 45.7 Mbit/s | **11.4 Mbit/s** |
| packet layout | 410 B, unchanged | 410 B, unchanged |
| byte-60 phantom readback | works | works |

**A packet rate of ~12,000/s with the decimating image means `valid_out` is
being ignored somewhere downstream** — that is the integration bug described
above, not a filter problem.

Host scripts need their sample-rate constant changed from 96000 to 24000 for
WAV writing and any seconds-from-packet-count arithmetic. The wire format is
otherwise identical, so nothing else moves.

### Not yet done

- **Nothing has been on hardware.** The design is verified in simulation-free
  form only: numerically against scipy, and structurally by Quartus. The
  reference vectors exist precisely so the first capture can be diffed rather
  than eyeballed.
- `python/check_sync.py` does not yet know about the decimator. It cross-checks
  host constants against the RTL and would be the natural place to assert that
  the host sample rate matches `C_DECIMATE`.

## Files

- `python/design_decimator.py` — designs, verifies, and emits everything below
- `rtl/decimator.vhd` — the two-engine time-multiplexed implementation
- `rtl/decim_coef_pkg.vhd` — generated coefficient package, do not hand-edit
- `sim/decim_ref_vectors.txt` — generated bit-exact reference vectors
- `docs/decimator_response.png` — generated response plot
