# What the netlist says about the dropouts

> **SUPERSEDED AS THE HEADLINE, 2026-08-16 - read `LRCLK_HOLD_VIOLATION.md` first.**
> The FPGA was violating the ADAU1978's tALH = 5 ns hold spec on LRCLK by ~4 ns, measured
> at the pads by Quartus across all three corners. The two findings **compose** rather than
> compete: this document's reasoning - that the parts sort by U1 output and that LRCLK is
> the one clock with no monitor - is what a ~1 ns margin being resolved per part by buffer
> and trace delay looks like from the outside. Section 0's suspicion of U1 is not wrong, it
> was one layer downstream of the cause. **The scope test in section 0 is still worth
> doing** (the two faults could stack), and sections 2 and 4 are unaffected.

Source: `Souncard_Robomarine 1.0.net` (KiCad 9.0.7 export, 2026-08-05). Every net below
was read out of that file. The schematic PDF has **not** been opened; anything about which
physical board a part sits on is inferred from connector pairing, not confirmed.

Written 2026-08-16, after the cable was replaced with twisted-pair-plus-ground (no change)
and header contact resistance measured at 0.2 ohm (i.e. fine).

## 0. Headline: the suspect is U1, the LRCLK fan-out buffer

Two `LMK1C1104PWR` 1:4 clock buffers feed all four ADCs, both enabled by `/Buffer_State`
(U43.57):

| buffer | source | Y0 | Y1 | Y2 | Y3 |
|---|---|---|---|---|---|
| **U1** LRCLK | `/FPGA_LRCLK` U43.65 | R5 -> **U38** | R6 -> **U37** | R7 -> **U19** | R8 -> **U20** |
| **U2** MCLK+BCLK | `/FPGA_CLK` U43.66 | R19,R20 -> U38 | R15,R16 -> U37 | R13,R14 -> U19 | R17,R18 -> U20 |

Measured behaviour: U38 9-39 % zero, U37 64-97 %, U19 17-35 %, **U20 0 %**.

**U20 is the only part on Y3, and the only part that works.**

### Why this is not just a coincidence in the pin ordering

The firmware's own instrumentation is what makes LRCLK the *only* clock that can fail
silently.

* The PLL is **MCLK-sourced**. Datasheet: *"The CLK_S bit (Bit 4) of Register 0x01 is used
  for setting the clock source for the PLL. The clock source can be either the MCLKIN pin
  or the LRCLK pin (slave mode)."* The boot ROM writes `0x01 = 0x03`, so bit 4 = 0 =
  MCLKIN.
* Therefore `PLL_LOCK` (0x01 bit 7), which `POLL_LIST(0)` reads continuously and latches
  into `pll_lost`, **is a live monitor of MCLK and says nothing whatever about LRCLK.**
* All four parts hold lock continuously. That is positive evidence that **U2 is good on all
  four outputs** - MCLK, and therefore BCLK, which is the same buffer output split by two
  49.9 ohm resistors.
* Nothing in the design monitors LRCLK.

So: the one clock proven good is the one from U2. The one clock with no monitor at all is
the one from U1. And the parts sort exactly by U1 output.

### Why LRCLK loss produces *exactly zero*, not corrupted audio

The boot ROM writes `0x09 = 0xF8`. Bit 3 is **DRV_HIZ = 1**, which the datasheet defines as
*"1: Unused outputs High-Z."* In slave TDM mode the part has no frame reference except
LRCLK, so with no LRCLK edge it never enters its slot and never drives.

High-Z, plus the 10 k pulldowns at the FPGA end (R21 on `/TDM1`, R122 on `/TDM2`), reads out
as **exact zeros** - which is the logged symptom.

Meanwhile the part is not reset, so its register map stays valid (`cfg_bad` clean), its PLL
stays locked (`pll_lost` clean), no overtemperature, no clip. **Every fault counter in the
design stays clean while the channel is dead.** That is the observation nothing else has
explained, and this explains it exactly.

### What it also explains

| observation | explained |
|---|---|
| Exact zeros rather than bit errors | DRV_HIZ=1 + pulldown |
| All fault counters clean during a dropout | LRCLK is unmonitored; PLL is MCLK-fed |
| **U19 bad with no cable anywhere in its path** | U1 is on the mainboard |
| New twisted-pair cable changed nothing | U1 is on the mainboard |
| 0.2 ohm contact resistance, yet still broken | contacts were never the issue |
| U20 perfect, the other three not | U20 is the only part on Y3 |
| Board survived a rail collapse that killed four op-amps | collateral damage to a 3V3 buffer is unremarkable |

**Still not explained by this or anything else: why 48 kHz made every part uniformly
worse.** That remains open and should not be smoothed over.

### How to test it

1. **Scope U1 pins 3 (Y0), 5 (Y2), 7 (Y3), 8 (Y1).** Four probe points, no rework, no
   rebuild. Y3 feeds the working part - it is the reference. Compare amplitude, edge rate,
   and whether the pulse is continuously present. Watch during a dropout.
2. **Without a scope:** lift R7 and R8 and cross-wire, so U19 takes Y3 and U20 takes Y2.
   If the fault follows the buffer output, **U20 goes bad and U19 goes good**. If U20 stays
   perfect on Y2, U1 is exonerated and this section is wrong.
3. **Firmware-only, with a caveat:** setting CLK_S (0x01 bit 4) = 1 moves the PLL onto
   LRCLK, which would turn the existing `pll_lost` latch into a live LRCLK monitor.
   Caveat: LRCLK here is a 4-BCLK-wide pulse, not a square wave, so the PLL may fail to
   lock for entirely benign reasons and give a false positive. Rank this below 1 and 2.

## 1. The two signal connectors to the daughterboard

Both `Conn_01x10`, JST XH 2.50 mm, horizontal. `J18 <-> J20` and `J19 <-> J21`.

| pin | J18 / J20 | J19 / J21 |
|-----|-----------|-----------|
| 1  | `/MCLK_3`  | `/SCL`  (crossed, see 4) |
| 2  | GND        | `/SDA`  (crossed, see 4) |
| 3  | `/LRCLK_3` | GND |
| 4  | GND        | `/TDM2`  (SDATA, the only return signal) |
| 5  | `/BCLK_3`  | GND |
| 6  | GND        | `/MCLK_4` |
| 7  | `/PD/RST`  | GND |
| 8  | GND        | `/LRCLK_4` |
| 9  | `/EN_15V`  | GND |
| 10 | `/EN_48V`  | `/BCLK_4` |

Ground alternates with signal on both. The pinout is sound.

**U37 and U38 do not share a connector.** U37's three clocks all arrive on J18; U38's all
arrive on J19, the same connector its SDATA leaves on. U37 is the worse of the two. That is
consistent with an interconnect story *and* with the U1 story (U37 is on Y1, U38 on Y0), so
it does not discriminate between them by itself.

## 2. `/PD/RST` has no pull-up or pull-down anywhere

Full node list: `J18.7, J20.7, U19.6, U20.6, U37.6, U38.6, U43.78`. Seven nodes, **no
resistor**. The only thing holding it is the FPGA output on the far side of the connector.

This is *not* the current fault - a PD/RST glitch resets the part, which would clear its
register map and drop its PLL, and neither `cfg_bad` nor `pll_lost` has ever latched. But
it fails unsafe, and it is worth fixing on any rework: **10 k from `/PD/RST` to +3V3 on the
daughterboard side**, after the connector. On the mainboard side it does nothing.

Note this is a pull-*up* on PD/RST, not a pull-down on the data line - R122 is already
correctly placed.

## 3. No power crosses J18/J19

Every net touching J18/J19/J20/J21: `MCLK_3/4`, `LRCLK_3/4`, `BCLK_3/4`, `PD/RST`,
`EN_15V`, `EN_48V`, `SCL`, `SDA`, `TDM2`, `GND`. **No +3V3, no ±15V, no +48V.**

The rails have their own connector pairs (inferred from pairing, not confirmed against
layout): J28<->J29 +3V3; J26<->J27 +5V and +3V3; J24<->J25 ±15V; J22<->J23 +48V.

So replacing the signal cable never touched the supply or its ground return. A +3V3 sag
would however reset the parts and show up in `cfg_bad` / `pll_lost`, which it has not - so
this is a robustness concern, not the present fault.

`EN_15V` (U39.3 REMOTE) and `EN_48V` (U41.1 EN/UVLO) crossing J18 means an intermittent J18
can drop the analog rails. That kills audio content but does not stop SDATAOUT, so it is a
distinct fault mode.

## 4. Other defects visible in the netlist

* **I2C swapped at every ADC**: pin 17 (SDA) sits on net `/SCL`, pin 18 (SCL) on `/SDA`, on
  all four parts. Already compensated in firmware by `C_I2C_SWAP`.
* **VREF loaded by the OPA1671s**: U19->U44.3, U20->U46.3, U37->U45.3, U38->U47.3. These
  are the parts wired V+ to +15 V against a 6 V absolute maximum and destroyed. If any is
  still fitted it is a damaged input sitting on that ADC's VREF node. **Confirm U45 and U47
  are off the daughterboard.**
* `SDATAOUT2` (pin 14) unconnected on all four parts, so the two ADCs sharing a line can
  never be split onto separate data wires without rework.
* Series termination is 49.9 ohm everywhere. Right for a short mainboard trace,
  under-terminated into a ~100-120 ohm twisted pair, so J18/J19 clocks do see reflections.
  Degrades edges; does not stop a part driving.

## 5. Ruled out

| hypothesis | status |
|---|---|
| Connector pinout / missing grounds | ruled out - grounds interleave correctly |
| Contact resistance | ruled out - 0.2 ohm, and these are CMOS inputs drawing microamps |
| Cable conductors | ruled out - replaced with twisted pair plus ground, no change |
| MCLK or BCLK delivery | ruled out - continuous PLL lock on all four parts proves U2 good |
| PD/RST glitching | ruled out - would clear config and drop PLL; neither ever latched |
| +3V3 brownout | ruled out - same reason |
| Interconnect as the single cause | ruled out by U19, which has no interconnect |
| Clock fan-out **asymmetry** as a design error | ruled out - U19 and U20 paths are structurally identical |
