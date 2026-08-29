# Moving the LRCLK launch phase — step by step

Written 2026-08-21, for the ADC3/ADC4 intermittent dropouts that survived the LRCLK
falling-edge fix, three cable rebuilds, and a 49.9 → 100 Ω termination change.

**Read section 0 before compiling anything.** The RTL is in place and the phase is one
value in the MegaWizard, but *which direction to move it is not yet known*, and half the
reason this document exists is to stop that being guessed.

---

## 0. What this fixes, and the honest case against it

The ADAU1978 samples LRCLK on the BCLK **rising** edge (Table 5, tALS/tALH, slave mode):

```
T = 1/24.576 MHz                          40.690 ns
window = [tALH, T - tALS] = [5.00, 30.69] ns      width 25.69 ns
current launch = BCLK falling edge = T/2  20.345 ns
    hold margin  20.345 - 5.00  = 15.35 ns
    setup margin 30.69 - 20.345 = 10.34 ns
```

20.345 ns is not a choice — it is the only value a falling-edge launch can produce.
Registering LRCLK onto a phase-shifted copy of the same PLL clock puts it anywhere in the
period. That is all this change does.

The model reconciles with Quartus to within clock uncertainty, using the 1.257 ns pad skew
from `LRCLK_HOLD_VIOLATION.md`:

| | computed | Quartus reported | diff |
|---|---|---|---|
| hold | 15.35 + 1.257 = 16.61 | 16.520 | 0.09 |
| setup | 10.34 − 1.257 = 9.08 | 8.382 | 0.70 |

### Why this may well be the wrong fix

Be clear-eyed about this before spending a bench session on it. **No mechanism has been
found that is big enough to consume the available margin:**

| source of LRCLK-vs-BCLK differential | size |
|---|---|
| cable flight time | ~5 ns/m, but **cancels** — LRCLK_3 and BCLK_3 are both on J18, same harness |
| RC differential (U2's Y1 drives R15+R16, U1's Y1 drives R6 alone) | ~0.6 ns — each branch has its own series R, so τ barely moves |
| U1 vs U2 part-to-part spread | 1–2 ns |
| pad skew | 0.6–1.26 ns |
| **total** | **~3 ns against 10.34 ns of margin** |

The RC argument that motivated this — that LRCLK's once-per-frame pulse rises from a
settled line while BCLK's edges start partly charged — does not survive arithmetic. At
τ ≈ 4.6 ns against a 20.3 ns half period, BCLK settles ~4.4 time constants per edge. It is
not partly charged. All four PLLs locking is independent proof of the same thing.

**The competing explanation, which fits the history better, is amplitude at the threshold.**
A signal sitting *at* V_IH = 0.7 × IOVDD = 2.31 V is the textbook intermittent failure —
noise decides each frame. It explains what timing does not:

- widening the pulse 1 → 4 BCLK helped — that is **dwell above V_IH**, not timing
- 100 Ω made it worse — less drive, lower amplitude on a slow edge
- three cable rebuilds changed nothing — same length, same capacitance, same amplitude

Phase shifting cannot fix amplitude. Section 1 tests both.

---

## 1. Step 0 — before any recompile

### 1a. Undo the termination change

Put **49.9 Ω** back on `R5 R6 R15 R16 R19 R20`. The 100 Ω was a bad suggestion of mine
based on transmission-line matching, which does not apply here: with ~20 ns edges into a
sub-metre harness the line is a lumped capacitor, and the added resistance only slows it.

Leave `R7 R8 R13 R14 R17 R18` alone — those feed U19/U20, which work.

| part | ch | MCLK | BCLK | LRCLK | crosses a connector? |
|---|---|---|---|---|---|
| U19 | 1–4 | R13 | R14 | R7 | no |
| U20 | 5–8 | R17 | R18 | R8 | no |
| U37 | 9–12 | R16 | R15 | **R6** | J18↔J20 |
| U38 | 13–16 | R19 | R20 | **R5** | J19↔J21 |

### 1b. Two measurements that phase shift cannot substitute for

Neither has ever been taken, and both test amplitude/threshold rather than timing.

1. **IOVDD at U37 pin 12 and U38 pin 12.** V_IH scales directly with it. Never measured on
   any part.
2. **DC between mainboard GND and daughterboard GND, running.** Should be a few mV. Tens of
   mV means supply return current is flowing through the signal connector's ground pins,
   and that offset lands straight on the clock thresholds. The daughterboard takes its 3V3
   on a *different* connector (J28/J29, J26/J27) than its clocks, so the return paths are
   genuinely separate.

### 1c. The sign test — this decides which phase to build

Set **R6 → 22 Ω** and **R15, R16 → 150 Ω**. That deliberately makes LRCLK fast and BCLK
slow, driving hard in the *LRCLK-relatively-earlier* direction. Run `udp_monitor.py` and
compare channels 9–12 against the 49.9 Ω baseline from 1a.

| result | reading | build |
|---|---|---|
| ADC3/4 **improve** | setup-limited, LRCLK was arriving late | **105°**, 11870 ps |
| ADC3/4 **get worse** | hold-limited, LRCLK was arriving early | **225°**, 25431 ps |
| **no change at all** | not a timing problem — see 1b, and the R6/R7 cross-wire | neither, yet |

Put the resistors back to 49.9 Ω afterwards either way.

### Or determine the sign in firmware instead — both images exist

Since `96K_LRPHASE_105.jic` and `96K_LRPHASE_225.jic` are both built (section 5), the sign
test can be done with two flashes and no soldering iron. They sit on **opposite sides** of
the current 180° operating point, so between them they cover both failure modes:

```
window   [ 5.00 ....................................... 30.69 ] ns
225 deg                                          ^ 25.43
180 deg                                    ^ 20.35   (every image until now)
105 deg                     ^ 11.87
```

Flash one, run `udp_monitor.py`, flash the other, compare channels 9–16:

| | reading |
|---|---|
| **105° better** | setup-limited — LRCLK was arriving late. Keep 105°, consider stepping to 90° |
| **225° better** | hold-limited — LRCLK was arriving early. Keep 225°, consider stepping to 240° |
| **both the same as before** | not a timing problem. Stop here and go to 1b and section 7 |

That third outcome is a real result, not a failed experiment — it eliminates the entire
timing hypothesis in one bench session, which is more than three cable rebuilds achieved.
Given section 0's argument that the mechanism is only ~3 ns against 10.34 ns of margin, it
is also the outcome to expect.

**Watch channels 1–8 on both.** They are the control group — see section 6.

---

## 2. The PLL — already done, by hand

`c3` has been added to `ip/pll_audio/pll_audio.vhd` directly rather than through the
MegaWizard: entity port, `sub_wire8 <= sub_wire3(3)`, the four `clk3_*` generics, and
`port_clk3 => "PORT_USED"`. `pll_audio.cmp` was updated to match. No `.qsf` change — the
`.qip` is already referenced at line 158.

`c3` uses the **identical** ratio to c2, `× 1536 / 3125`. That matters: same ratio means
the same counter setting, so the two are frequency-identical by construction and differ
only in VCO phase tap. They can never drift apart.

**Changing the phase is one string**, `clk3_phase_shift`, in picoseconds:

| value | phase | launch | for | C_BIT_ADJ |
|---|---|---|---|---|
| `"11870"` | 105° | 11.870 ns | setup-limited | −2 |
| `"25431"` | 225° | 25.431 ns | hold-limited | −1 |
| `"20345"` | 180° | 20.345 ns | control build | −2 |

Currently set to `"11870"`. **Do not build until section 1c has told you the sign.**

### Why the GUI state was not updated

The `Retrieval info` block at the bottom of `pll_audio.vhd` is MegaWizard GUI state, not
compiled code, and it is **already inconsistent** with the generated design — it records
`CLK2_MULTIPLY_BY NUMERIC "1"` where the generic map says `1536`. Reconstructing matching
c3 entries by hand would add guesswork on top of a record that is already wrong, so it was
left alone deliberately.

**Consequence:** opening this IP in the MegaWizard and clicking Finish will regenerate from
that stale state and drop `c3`. That fails *loudly* — `top_system`'s component declaration
names `c3`, so the build stops with a port mismatch on `u_pll` rather than quietly
producing an image with the wrong phase. If it happens, re-apply the six edits listed in
the header comment of `pll_audio.vhd`.

### If you would rather use the wizard anyway

Project Navigator → dropdown → **IP Components** → right-click `pll_audio` → *Edit in
Parameter Editor*. Then **Output Clocks → clk c3** → tick *Use this clock* → *Enter output
clock parameters* → multiply `1536`, divide `3125`, duty `50`, phase shift in **ps**.

Two things to read before Finish. Cyclone IV quantizes phase to about an eighth of the VCO
period (~200 ps here), so the value you type gets rounded — irrelevant against 11.87 ns,
but don't be surprised. And check the Summary reports the **same actual frequency for c2
and c3**: 24.576 MHz cannot be produced exactly from 50 MHz on this PLL, because
`24.576/50 = 1536/3125` needs M divisible by 1536 and Cyclone IV caps M near 512. c2 has
always run at a close approximation. Harmless — every clock comes off the same PLL so
everything stays coherent — but c3 must land on the same value.

---

## 3. The RTL — already done

Committed with this document, in three places in `rtl/top_system.vhd`:

- `component pll_audio` gains `c3 : out std_logic`
- `u_pll` port map gains `c3 => clk_lr`
- a re-timing register drives the pad:

```vhdl
process(clk_lr)
begin
    if rising_edge(clk_lr) then
        lrclk_pin_r <= lrclk_int;
    end if;
end process;

lrclk_out <= lrclk_test when C_LRCLK_TEST_50PCT else lrclk_pin_r;
```

**Only the pin moves.** `lrclk_int` stays in the `clk_18m` domain and stays wired to
`u_rx_A`/`u_rx_B` as their frame reference. This is deliberate — moving `tdm8_master` into
the shifted domain instead would create an internal clock crossing where there is currently
none, which is exactly the kind of new intermittent bug this is trying to remove.

`C_LRCLK_PHASE_PS` in `top_system.vhd` is a **mirror of the MegaWizard value, not a
control.** Editing it alone changes nothing. Keep the two in sync by hand.

---

## 4. Set C_BIT_ADJ to match the phase

`rtl/tdm8_rx.vhd`. Which value depends on where the capture edge falls relative to
`lrclk_int` changing at 20.345 ns:

| phase | capture edge | carries | added latency | C_BIT_ADJ |
|---|---|---|---|---|
| 225° (25431 ps) | 25.431 ns, **after** the change | same cycle | none | **−1** (unchanged) |
| 105° (11870 ps) | 11.870 ns, **before** the change | previous cycle | one BCLK | **−2** |
| 180° (20345 ps) | 20.345 ns, control | previous cycle | one BCLK | **−2** |

Legal range is −8..+8, from the k=0 and k=7 slice bounds at `tdm8_rx.vhd:140`. If the
channels read as noise after flashing, this constant is the first thing to move — one step
either way — and that outcome does **not** invalidate the phase change.

---

## 5. Compile, then check the report BEFORE programming

`TDM_UATR.sdc` needed no new constraint. `derive_pll_clocks` picks up c3, and the
`clk[*]` wildcard in `set_clock_groups` already declares c2 and c3 synchronous, which they
are — same PLL.

The existing two lines are now the verification:

```tcl
set_output_delay -clock bclk_pin -max  10.0 [get_ports {lrclk_out}]
set_output_delay -clock bclk_pin -min  -5.0 [get_ports {lrclk_out}]
```

### Both images are built, and the check has been run

`quartus_sh --flow compile` + `quartus_cpf -c -d EPCS16 -s EP4CE6E22C8`, Quartus 25.1std.
Both are in `output_files/`:

| image | phase | C_BIT_ADJ | `lrclk_out` setup | `lrclk_out` hold |
|---|---|---|---|---|
| `96K_LRPHASE_105.jic` | 105° | −2 | **+16.522** | **+7.928** |
| `96K_LRPHASE_225.jic` | 225° | −1 | **+4.489** | **+20.397** |
| `96K_LRPHASE_240.jic` | 240° | −1 | **+2.787** | **+22.127** |
| *(prior baseline, 180°)* | 180° | −1 | +8.382 | +16.520 |

### Bench result, 2026-08-21: 225° slightly better than 105°

**The sign is LATER, not earlier.** The failure is hold-limited — LRCLK arriving *early*
relative to BCLK at ADC3/ADC4 — which is the opposite of the setup-limited premise section 0
was originally built on. 105° was the wrong direction.

240° was then built as the last safe step. **The knob is now exhausted**: `lrclk_out` setup
slack *is* the margin for channels 1–8, and it reads +2.787 ns at 240°. 255° computes to
about +1 ns and 270° goes negative, i.e. it breaks the parts that work.

```
phase   launch     ch1-8 setup headroom
180 deg  20.35 ns      9.34 ns
225 deg  25.43 ns      4.26 ns
240 deg  27.13 ns      2.56 ns    <- last safe step, measured +2.787
255 deg  28.82 ns      0.87 ns    <- do not
270 deg  30.52 ns     -0.83 ns    <- breaks channels 1-8
```

### Two cautions on that result

**"Slightly" has not been shown to be reproducible.** This fault drifts within a session —
`LRCLK_HOLD_VIOLATION.md` lists "worsens over a session" as an observation, and the dropout
figures in `TDM2_NETLIST_FINDINGS.md` are ranges rather than values (U37 64–97 %, U38
9–39 %). Two single readings cannot separate a small real effect from that drift. **Run
225 → 105 → 225** and check the ordering reproduces before treating the gradient as real.

**No mechanism has been found for this sign.** The RC arithmetic predicts the opposite:

```
tau = 4.6 ns, half period 20.35 ns -> e^(T/2tau) = 81, BCLK settles to 3.26 V
    BCLK crosses 2.31 V at 5.5 ns     LRCLK crosses at 5.5 ns     no asymmetry
tau = 20 ns (badly slew limited)   -> BCLK swings only 0.88 to 2.43 V
    BCLK crosses at 17.9 ns           LRCLK crosses at 24 ns
    LRCLK LATER, i.e. setup-limited - the opposite of the measurement
```

Slew limiting gives setup-limited in both regimes, and nothing found so far produces the
~15 ns of *early* LRCLK that a hold violation at 180° would require. So the measured
gradient, if real, is not cable RC. Take the free margin at 240°, but **do not treat this
as the fix** — section 7 is still where the unexplored ground is.

**The edge-pair check passes on both.** Between the two builds setup moves 12.03 ns and hold
moves 12.47 ns, in opposite directions, against 13.56 ns of nominal phase difference — the
~1 ns shortfall is Cyclone IV's phase quantization (about an eighth of a VCO period) and is
consistent across both rows. TimeQuest picked the intended relationship; **no
`set_multicycle_path` is needed.**

`Design-wide TNS = 0.0` on setup, hold, recovery, removal and minimum pulse width for both
images. Nothing in the design fails. Worst-case slack in the 105° image is 2.879 ns on
`rmii_clk`, which is the pre-existing Ethernet path and unchanged by this work.

The hand arithmetic in section 0 was confirmed against the tool on the internal register
path, to three decimal places:

```
tdm8_master|lrclk_out -> lrclk_pin_r   (clk[2] -> clk[3], 105 deg)
    setup required   32.203 ns      hand-computed 32.22
    hold  required   -8.474 ns      hand-computed  8.47
```

### If you rebuild, re-run this check

Read setup and hold on `lrclk_out` against `bclk_pin`:

| phase | expect setup | expect hold |
|---|---|---|
| baseline (180°) | +8.382 | +16.520 |
| 105° | +16.5 | +7.9 |
| 225° | +4.5 | +20.4 |

**If setup and hold have not moved in opposite directions by about 8.5 ns, stop.**
With a phase-shifted launch clock TimeQuest picks whichever launch/capture edge pair gives
worst-case slack, and that is not always the intended one. A mismatch means it chose a
different pair and the design needs a `set_multicycle_path` — not that the phase is wrong.
Do not program the device until those numbers reconcile. This file has already shipped one
constraint that read plausibly and had its sign inverted.

Also confirm the three test flags are still false, since flashing with one set wastes the
session:

```
C_LRCLK_TEST_50PCT  false    top_system.vhd
C_BCLK_TEST_SLOW    false    top_system.vhd
C_TDM2_FROM_TDM1    false    top_system.vhd
```

---

## 6. On the bench

1. Flash. Run `python i2c_scan.py` first — all four parts should still verify 0x05 = `0x5B`
   and 0x06 = `0x08`, and hold PLL lock. Nothing here touches configuration, so anything
   different means something unrelated moved.
2. Run `python udp_monitor.py`. Read **channels 1–8 first, not 9–16.**

**Channels 1–8 are the control group.** This change is re-centering, not free margin —
every step away from 180° takes margin from the parts that already work:

```
window   [ 5.00 ................................. 30.69 ] ns
225 deg                                    ^ 25.43
180 deg                              ^ 20.35   (today)
105 deg              ^ 11.87
 90 deg        ^ 10.17
```

If channels 1–8 start dropping, you have gone too far and the previous value was the limit
— and that limit is itself the measurement, because it tells you how much differential
delay ADC3/ADC4 actually have.

3. If 9–16 improve but do not fully clear, step once further in the same direction (105° →
   90°, or 225° → 240°) and repeat.

---

## 7. When to abandon this

If **no phase between 90° and 240° gives all four parts clean at once**, the spread between
mainboard and daughterboard parts is wider than the 25.69 ns window and no launch point
exists. That is a real possible outcome and it is not a failure of the method — it rules
out timing and points at the two things this cannot fix:

- **amplitude at V_IH** — section 1b, and the LRCLK pulse width (`C_LR_PULSE_BCLKS`,
  `tdm8_master.vhd`, currently 4, `range 1 to 16`). Widening buys dwell above threshold.
  **Caveat: it is not established which LRCLK edge the part frames on.** The datasheet
  states it nowhere in text — searched all 44 pages — and it exists only in the Figure 25/26
  vector waveforms. p18 says the pulse "must be at least one BCLK wide" while Table 21 calls
  it "a single BCLK cycle wide pulse", and the one hardware observation in this project
  (2026-08-12, nonpulse mode, uniform +4 slot shift) points at the **falling** edge. If that
  carries into pulse mode, widening moves the frame boundary instead of adding margin. Test
  it as a test, with channels 1–8 as the oracle, not as a fix.
- **U1's Y0/Y1 outputs** — the R6/R7 cross-wire, still undone. Lift R6 and R7 and cross
  them so U19 runs off Y1 and U37 off Y2. U19 goes bad and U37 good → U1 is weak. Both stay
  as they are → U1 is cleared. This is the only test that separates a weak buffer output
  from a bad interconnect, and the two currently predict identical patterns.

## 8. Reverting

Set the MegaWizard phase back to `0` on c3 (or untick c3), set `C_BIT_ADJ` back to `−1`,
and change `lrclk_out` back to `lrclk_int`. The register and the c3 port can stay — with
zero phase shift `clk_lr` is `clk_18m` and the only residue is one BCLK of frame latency,
which `C_BIT_ADJ` absorbs.
