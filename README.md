# Gemini Briefing: 4× ADAU1978 — 16ch TDM Receiver on Cyclone IV FPGA
### Full project context + step-by-step test plan — paste this into Gemini

---

## Project Summary

| Parameter | Value |
|-----------|-------|
| ADC chip | Analog Devices ADAU1978 (quad, 24-bit) |
| Number of chips | **4** |
| Total channels | **16** |
| Sample rate | **96 kHz** |
| TDM architecture | **2× TDM8 streams** (pairs of chips per stream) |
| Slot width | **24 bits** (no zero padding, exact fit for 24-bit audio) |
| BCLK frequency | **18.432 MHz** |
| MCLK frequency | **12.288 MHz** (128 × 96kHz) |
| FPGA | Altera Cyclone IV E |
| Toolchain | Quartus Prime 18.1+ / ModelSim-Altera |
| Language | VHDL |

---

## Why These Choices — Architecture Decision Log

### Why NOT TDM16?

TDM16 puts all 16 channels on one wire. The BCLK cost is severe:

| Slot width | TDM16 BCLK at 96kHz |
|------------|---------------------|
| 32-bit | 96k × 16 × 32 = **49.152 MHz** — difficult PCB routing, tight FPGA I/O |
| 24-bit | 96k × 16 × 24 = **36.864 MHz** — still challenging |

These are usable but create unnecessary risk. We save one wire at the cost of 2× the BCLK frequency. Not worth it for a 4-chip system.

### Why NOT 4× TDM4?

4 separate TDM4 streams would work and give the lowest BCLK (9.216 MHz), but uses 4 SDATAOUT input pins on the FPGA. More pins, more routing, no real benefit over TDM8 pairing.

### Why 2× TDM8 with 24-bit slots?

```
BCLK = 96,000 × 8 slots × 24 bits = 18,432,000 Hz = 18.432 MHz
```

- BCLK is clean and well within Cyclone IV capability
- Only **2 SDATAOUT data wires** from ADC board to FPGA
- Each receiver handles 8 channels — simple, symmetric logic
- 24-bit slots eliminate 8 bits of zero-padding per slot vs 32-bit
- MCLK = 12.288 MHz — standard audio clock, easy to generate with PLL

### Chip pairing and slot assignment

```
Stream A:  Chip 0 (ch 1–4) → slots 1–4   }  shared SDATAOUT_A wire
           Chip 1 (ch 5–8) → slots 5–8   }

Stream B:  Chip 2 (ch 9–12)  → slots 1–4  }  shared SDATAOUT_B wire
           Chip 3 (ch 13–16) → slots 5–8  }
```

All 4 chips share the same BCLK and LRCLK driven from the FPGA.

---

## System Wiring Diagram

```
FPGA (master: generates BCLK + LRCLK)
  │
  ├──BCLK (18.432 MHz) ──────────────────────┬──► Chip 0 BCLK
  │                                           ├──► Chip 1 BCLK
  │                                           ├──► Chip 2 BCLK
  │                                           └──► Chip 3 BCLK
  │
  ├──LRCLK (96kHz, 1-cycle pulse) ───────────┬──► Chip 0 LRCLK
  │                                           ├──► Chip 1 LRCLK
  │                                           ├──► Chip 2 LRCLK
  │                                           └──► Chip 3 LRCLK
  │
FPGA PLL (50MHz → 12.288 MHz) ─────────────► MCLKIN on all 4 chips
  │
  ├──SDATAOUT_A ◄──── Chip 0 (slots 1–4) + Chip 1 (slots 5–8)
  └──SDATAOUT_B ◄──── Chip 2 (slots 1–4) + Chip 3 (slots 5–8)

Pull-down: 47kΩ to GND on SDATAOUT_A and SDATAOUT_B
           (prevents floating during HIGH-Z inactive slots)
```

---

## TDM Frame Structure at 96kHz / TDM8 / 24-bit slots

```
LRCLK: |‾|______________________________________________|‾|__
        1 BCLK wide pulse (HIGH for exactly one BCLK cycle)

BCLK:  192 cycles per frame  (8 slots × 24 bits = 192)

SDATAOUT_A:
  [Chip0-CH1: 24b][Chip0-CH2: 24b][Chip0-CH3: 24b][Chip0-CH4: 24b]
  [Chip1-CH1: 24b][Chip1-CH2: 24b][Chip1-CH3: 24b][Chip1-CH4: 24b]
   ←──── slot 1 ────►←── slot 2 ──►                ←──── slot 8 ──►

SDATAOUT_B:
  [Chip2-CH1][Chip2-CH2][Chip2-CH3][Chip2-CH4]
  [Chip3-CH1][Chip3-CH2][Chip3-CH3][Chip3-CH4]
```

- **Each slot = 24 bits** — MSB first, no zero padding
- **Frame = 192 BCLK cycles** (8 × 24)
- Data changes on **falling BCLK edge**, valid by rising BCLK edge
- LRCLK pulse marks the start of slot 1 — the ADAU1978 outputs first bit of slot 1 the cycle AFTER the LRCLK pulse in Left Justified mode
- **FPGA samples on rising BCLK edge**

---

## Clock Calculations (verified against datasheet Table 9 and Table 10)

### BCLK
```
BCLK = fs × slots × bits_per_slot
     = 96,000 × 8 × 24
     = 18,432,000 Hz = 18.432 MHz
```

### MCLK (from datasheet Table 9, MCS=001)
```
MCS bits = 001 → 128 × fs
MCLK = 128 × 96,000 = 12,288,000 Hz = 12.288 MHz
```

### LRCLK (= sample rate)
```
LRCLK = 96,000 Hz (pulse every 192 BCLK cycles)
```

### FPGA PLL targets
```
Input:  50 MHz (board oscillator)
Output c0: 12.288 MHz  → MCLKIN for all 4 chips
Output c1: 18.432 MHz  → FPGA internal BCLK generator source
```

> Verify these are achievable with your specific Cyclone IV PLL by checking
> the ALTPLL output in Quartus. Both 12.288 and 18.432 are standard audio
> frequencies and should be fine.

---

## The ADAU1978 ADC — Key Hardware Details

### Package and supply
- 40-lead LFCSP, 6mm × 6mm
- Single **3.3V analog supply** (AVDD pins)
- Internal LDO generates **1.8V DVDD** (decouple only, no external load)
- **IOVDD** (digital I/O level): 1.8V to 3.3V — must match FPGA I/O bank voltage
- **Exposed pad (EP)** must be soldered to PCB ground plane — do not leave floating

### Decoupling requirements (per chip)
| Pin | Cap |
|-----|-----|
| AVDD1, AVDD2, AVDD3 | 100nF ceramic + 10µF bulk each |
| DVDD (pin 10) | 100nF + 10µF MLCC X7R |
| IOVDD | 100nF ceramic |
| VREF (pin 2) | 100nF + 10µF in parallel |

### PLL external filter at PLL_FILT (pin 3) — REQUIRED

In **MCLK mode** (`CLK_S=0`, our config), connect to AVDD2 via:

```
AVDD2 ──┬── 5.6nF ──┬── PLL_FILT (pin 3)
         └── 1kΩ  ──┘
         └── 390pF to GND
```

Place filter components as close as possible to pin 3. Use NPO/C0G capacitors for temperature stability. Without this filter the PLL will not lock correctly.

### Key pin table
| Pin | Name | Dir | Description |
|-----|------|-----|-------------|
| 7 | MCLKIN | I | Master clock in — 12.288 MHz from FPGA PLL |
| 16 | BCLK | I | Bit clock in — 18.432 MHz from FPGA (slave mode) |
| 15 | LRCLK | I | Frame sync in — 96kHz pulse from FPGA (slave mode) |
| 13 | SDATAOUT1 | O | Serial audio output (used in TDM8 mode) |
| 14 | SDATAOUT2 | O | Not used as data output in TDM8 mode (see SDATA_SEL bit) |
| 6 | PD/RST | I | Active-low reset — hold LOW until supply stable |
| 9 | SA_MODE | I | Pull HIGH (10kΩ to IOVDD) for standalone mode |
| 3 | PLL_FILT | O | External PLL filter (see above) |
| 2 | VREF | O | 1.5V internal reference — decouple, do not load |

### Slot assignment configuration (registers 0x07 and 0x08)

Each chip's 4 channels must be assigned to the correct TDM slots:

**Chips 0 and 2 (slots 1–4):**
```
Register 0x07 (SAI_CMAP12): CMAP_C2=0001 (slot 2), CMAP_C1=0000 (slot 1) → 0x10 (default)
Register 0x08 (SAI_CMAP34): CMAP_C4=0011 (slot 4), CMAP_C3=0010 (slot 3) → 0x32 (default)
```

**Chips 1 and 3 (slots 5–8):**
```
Register 0x07: CMAP_C2=0101 (slot 6), CMAP_C1=0100 (slot 5) → 0x54
Register 0x08: CMAP_C4=0111 (slot 8), CMAP_C3=0110 (slot 7) → 0x76
```

---

## ADAU1978 Configuration Registers

### For our exact setup: TDM8, Left Justified, 24-bit slots, 24-bit data, slave, pulse LRCLK, 96kHz

| Address | Register | Value | Bit breakdown |
|---------|----------|-------|---------------|
| 0x00 | M_POWER | `0x01` | PWUP=1 (write LAST, after PLL locks) |
| 0x01 | PLL_CONTROL | `0x41` | PLL_MUTE=1, CLK_S=0 (MCLK), MCS=001 (128×fs=12.288MHz) |
| 0x04 | BLOCK_POWER_SAI | `0x3F` | LR_POL=0, BCLKEDGE=0 (data changes on falling BCLK), LDO+VREF+all 4 ADCs enabled |
| 0x05 | SAI_CTRL0 | `0x5A` | SDATA_FMT=01 (Left Justified), SAI=011 (TDM8), FS=010 (32–96kHz range) |
| 0x06 | SAI_CTRL1 | `0x08` | SDATA_SEL=0 (SDATAOUT1), SLOT_WIDTH=01 (24 BCLKs/slot), DATA_WIDTH=0 (24-bit), LR_MODE=1 (pulse), SAI_MSB=0 (MSB first), SAI_MS=0 (slave) |
| 0x07 | SAI_CMAP12 | `0x10` | Chips 0,2: ch1→slot1, ch2→slot2 |
| 0x07 | SAI_CMAP12 | `0x54` | Chips 1,3: ch1→slot5, ch2→slot6 |
| 0x08 | SAI_CMAP34 | `0x32` | Chips 0,2: ch3→slot3, ch4→slot4 |
| 0x08 | SAI_CMAP34 | `0x76` | Chips 1,3: ch3→slot7, ch4→slot8 |
| 0x09 | SAI_OVERTEMP | `0xF8` | All 4 channels drive enabled, DRV_HIZ=1 (unused slots go HIGH-Z) |

> **Register 0x05 value `0x5A` decoded:**
> - Bits [7:6] SDATA_FMT = `01` (Left Justified)
> - Bits [5:3] SAI = `011` (TDM8)
> - Bits [2:0] FS = `010` (32kHz to 96kHz range — covers our 96kHz)

### I2C address per chip (set by ADDR1/ADDR0 pin strapping)

| Chip | ADDR1 | ADDR0 | 7-bit I2C Address |
|------|-------|-------|-------------------|
| 0 | 0 | 0 | 0x11 |
| 1 | 0 | 1 | 0x31 |
| 2 | 1 | 0 | 0x51 |
| 3 | 1 | 1 | 0x71 |

In standalone mode (`SA_MODE` HIGH), I2C is not used for audio config — but I2C is still recommended to verify PLL lock status at startup.

---

## Power-Up Sequence (CRITICAL — do not skip)

```
1. Apply 3.3V AVDD
2. Keep PD/RST LOW
3. Assert PD/RST HIGH
   → Internal LDO starts charging DVDD
   → DVDD rises toward 1.8V
4. Wait ~200 µs (DVDD reaches 1.2V with 10µF CEXT, 3kΩ REXT)
   → Internal POR releases
5. Apply stable 12.288 MHz MCLK to all MCLKIN pins
6. Wait 10 ms for PLL to lock
   → Poll PLL_LOCK bit (bit 7 of register 0x01) via I2C until = 1
   → OR simply wait 15 ms to be safe
7. Write all config registers (0x04, 0x05, 0x06, 0x07, 0x08, 0x09)
8. LAST: write PWUP=1 to register 0x00
   → ADC and serial port become active
9. Valid audio data appears within a few ms
```

**Why the order matters:** If PWUP is asserted before PLL locks, the state machine initialises with the wrong clock and ADC behaviour is indeterminate. This is explicitly warned in the datasheet.

---

## FPGA Logic Required

Since FPGA is the serial port master, it needs two modules:

### Module 1: TDM8 Master (generates BCLK + LRCLK)
```
Inputs:  clk_18m432 (from PLL)
Outputs: bclk_out, lrclk_out

- Toggle bclk_out at half the input clock rate (or use clk_18m432 directly)
- lrclk_out: goes HIGH for exactly 1 BCLK period every 192 BCLK cycles
- Counter: 0 to 191, wraps. lrclk_out = '1' when counter = 0.
```

### Module 2: TDM8 Receiver (one instance per SDATAOUT line)
```
Inputs:  bclk_in, lrclk_in, sdata_in
Outputs: ch_data_out (8 × 24 bits = 192 bits total)

- Sample sdata_in on rising bclk_in edge
- Shift into 192-bit shift register
- When lrclk_in rising edge detected: latch shift_reg → ch_data_out
- bit_cnt counts 0 to 191

Extracted audio:
ch1 = ch_data_out[191:168]   (slot 1, bits 23:0 of 24)
ch2 = ch_data_out[167:144]   (slot 2)
ch3 = ch_data_out[143:120]   (slot 3)
ch4 = ch_data_out[119:96]    (slot 4)
ch5 = ch_data_out[95:72]     (slot 5, from second chip on this wire)
ch6 = ch_data_out[71:48]     (slot 6)
ch7 = ch_data_out[47:24]     (slot 7)
ch8 = ch_data_out[23:0]      (slot 8)
```

### Top-level connections
```
FPGA top level:
  ├── u_pll         → generates 12.288 MHz (MCLK) and 18.432 MHz (BCLK source)
  ├── u_tdm_master  → generates bclk_out, lrclk_out (shared to all 4 chips)
  ├── u_rx_A        → receives SDATAOUT_A (chips 0+1, ch 1–8)
  └── u_rx_B        → receives SDATAOUT_B (chips 2+3, ch 9–16)
```

---

## Voltage Compatibility

| Signal | ADAU1978 (IOVDD) | Cyclone IV (3.3V bank) | Compatible? |
|--------|------------------|------------------------|-------------|
| BCLK FPGA→ADC | VIH = 0.7×IOVDD | VOH ≥ 2.4V | ✅ yes (at 3.3V IOVDD) |
| LRCLK FPGA→ADC | VIH = 0.7×IOVDD | VOH ≥ 2.4V | ✅ yes |
| SDATAOUT ADC→FPGA | VOH = IOVDD−0.6V | VIH = 1.7V min | ✅ yes |
| MCLK FPGA→ADC | VIH = 0.7×IOVDD | VOH ≥ 2.4V | ✅ yes |

> **If your FPGA board uses 1.8V I/O banks:** Set ADAU1978 IOVDD = 1.8V.
> The ADAU1978 supports IOVDD from 1.8V to 3.3V. Match it to your FPGA bank.

---

## Project File Structure

```
tdm_adau1978_16ch/
├── top_tdm.vhd              ← top-level entity
├── tdm8_master.vhd          ← generates BCLK + LRCLK (master mode)
├── tdm8_rx.vhd              ← TDM8 receiver, 192-bit shift register
├── pll_audio.vhd            ← Quartus IP: 50MHz → 12.288MHz + 18.432MHz
├── tb_tdm8_rx.vhd           ← ModelSim testbench
├── tb_loopback.vhd          ← loopback test (master feeds into receiver)
├── tdm_adau1978.sdc         ← timing constraints
├── tdm_adau1978.qpf         ← Quartus project
└── tdm_adau1978.qsf         ← pin assignments
```

---

## Step-by-Step Tests (no ADC hardware needed)

---

### STEP 1 — ModelSim Simulation

**Goal:** Prove TDM8 master and receiver are functionally correct.

**What I need:**
- Complete VHDL for `tdm8_master.vhd`:
  - Input: `clk_in` (18.432 MHz from PLL)
  - Outputs: `bclk_out`, `lrclk_out`
  - `lrclk_out` = HIGH for 1 BCLK cycle every 192 BCLK cycles (counter = 0)
  - `bclk_out` = directly passes `clk_in` OR uses a divided version — clarify which
- Complete VHDL for `tdm8_rx.vhd`:
  - Inputs: `bclk_in`, `lrclk_in`, `sdata_in`
  - Output: `ch_data_out` (192 bits = 8 channels × 24 bits)
  - Samples on rising `bclk_in`
  - Latches on rising `lrclk_in`
- Testbench `tb_tdm8_rx.vhd`:
  - Instantiates `tdm8_master` — uses its BCLK/LRCLK
  - Generates fake SDATAOUT with known 8-channel pattern:
    - Ch1=0xA1A1A1, Ch2=0xB2B2B2, Ch3=0xC3C3C3, Ch4=0xD4D4D4
    - Ch5=0xE5E5E5, Ch6=0xF6F6F6, Ch7=0x070707, Ch8=0x181818
    - Pattern serialised MSB-first, 24 bits per slot, left justified, 8 slots per frame
  - After 3 complete frames, asserts that `ch_data_out` contains expected values
- ModelSim TCL commands to compile and run
- Waveform checklist

**What correct behaviour looks like:**
- `lrclk_out` pulses exactly once every 192 BCLK cycles
- `ch_data_out[191:168]` = 0xA1A1A1 after first complete frame
- All 8 channels decode correctly
- `bit_cnt` counts 0–191 and wraps without glitches

---

### STEP 2 — FPGA Internal Loopback

**Goal:** Prove TDM8 master + receiver work on real Cyclone IV silicon.

**What I need:**
- `top_loopback.vhd` that:
  - Instantiates `tdm8_master`, `tdm8_rx`
  - Instantiates a **pattern serialiser**: takes a known 192-bit parallel pattern and shifts it out MSB-first, clocked by `bclk_out` from the master, triggered by `lrclk_out`
  - Pattern: ch1 = frame counter (increments each frame), ch2–ch8 = fixed values
  - Connects serialiser output directly (internal wire) to `sdata_in` of receiver
- Pass/fail checker: drives `pass_led` HIGH after 10 consecutive correct frames, `fail_led` HIGH on any mismatch
- Must compile and meet timing in Quartus

---

### STEP 3 — SignalTap II Logic Analyser

**Goal:** Observe internal signals in real time on hardware.

**What I need:**
- Instructions to add SignalTap II to Quartus project
- Signals to probe: `bclk_out`, `lrclk_out`, `sdata_in_A`, `bit_cnt`, `shift_reg[191:168]` (ch1 slice), `ch_data_out_A`, `pass_flag`
- Trigger: rising edge of `lrclk_out`
- Sample depth: 256 minimum to capture at least one full frame
- How to read a 24-bit audio value from the waveform in hex
- Common SignalTap mistakes to avoid

---

### STEP 4 — Arduino as Fake ADAU1978

**Goal:** Verify FPGA input pins and PCB/cable wiring before chips are connected.

**What I need:**
- Arduino (Uno or Mega) code that bit-bangs TDM8 at slow speed (~50 kHz BCLK):
  - LRCLK: 1-cycle HIGH pulse every 192 BCLK cycles
  - SDATAOUT: serialises known 8-channel 24-bit pattern, MSB first, left justified
  - Repeats continuously
- Voltage warning: Arduino = 5V, FPGA/ADAU1978 IOVDD = 3.3V — I need confirmation whether a resistor divider (e.g. 1kΩ + 2kΩ) or level shifter is required on each Arduino output line
- FPGA-side verification via LEDs or UART: received ch1 value matches expected
- What this proves (pin connectivity, gross logic) vs what it does NOT prove (18.432 MHz timing)

---

### STEP 5 — ADAU1978 Integration Checklist

**Goal:** Systematic verification when real chips are connected.

**What I need:**

**Before powering up:**
- [ ] Exposed pad soldered to PCB ground plane on all 4 chips
- [ ] PLL_FILT RC filter populated on all 4 chips (1kΩ, 5.6nF, 390pF)
- [ ] 47kΩ pull-down on SDATAOUT_A and SDATAOUT_B lines
- [ ] IOVDD matches FPGA I/O bank voltage on all chips
- [ ] ADDR1/ADDR0 strapped correctly for unique I2C addresses (0x11, 0x31, 0x51, 0x71)
- [ ] SA_MODE tied HIGH via 10kΩ (if standalone) or LOW (if I2C full control)

**Power-up verification:**
- How to confirm DVDD reaches 1.8V on each chip with a multimeter
- How to confirm MCLK is reaching all MCLKIN pins before PD/RST goes HIGH
- Exact I2C byte sequence to read PLL_LOCK bit from register 0x01
- Exact I2C byte sequence to write all config registers in order, then PWUP last

**I2C initialisation sequence (complete, for one chip at address 0x11):**
- Write register 0x04 = 0x3F
- Write register 0x05 = 0x5A
- Write register 0x06 = 0x08
- Write register 0x07 per chip (0x10 for chips 0,2 or 0x54 for chips 1,3)
- Write register 0x08 per chip (0x32 for chips 0,2 or 0x76 for chips 1,3)
- Write register 0x09 = 0xF8
- Poll register 0x01 bit 7 until PLL_LOCK = 1
- Write register 0x00 = 0x01 (PWUP)

**SignalTap integration verification:**
- What valid SDATAOUT looks like on a scope vs misconfigured (flat line, wrong frequency, no transitions)
- How to compare live chip output against loopback pattern to confirm FPGA receiver is working

**Common ADAU1978-specific failure modes:**
- PWUP asserted before PLL locks → indeterminate ADC behaviour, output is garbage
- PLL_FILT filter missing or wrong values → PLL never locks (PLL_LOCK bit stays 0)
- DRV_HIZ=0 on chips 1,3 → inactive slots are driven LOW instead of HIGH-Z, corrupts other chip's data on shared wire
- SLOT_WIDTH and DATA_WIDTH mismatch → frame sync drifts after a few frames
- LRCLK polarity (LR_POL) wrong → channels appear in wrong order
- Chip 1/3 slot mapping not updated (left at default 0x10/0x32) → all chips fight over slots 1–4

---

## Key Rules — Always Apply

1. **4× ADAU1978 = 16 channels total.** Each chip = 4 channels. 3 chips would be 12.

2. **FPGA is serial port MASTER** — FPGA generates BCLK (18.432 MHz) and LRCLK (96kHz pulse). All 4 ADAU1978 chips are serial port slaves (`SAI_MS=0`).

3. **FPGA still supplies MCLK** — 12.288 MHz to all 4 MCLKIN pins. The ADAU1978 PLL runs from this.

4. **TDM8 mode, NOT TDM16** — each chip outputs 4 channels in 8-slot frame. Two chips per wire. Frame = 192 BCLK cycles (8 × 24).

5. **24-bit slots** — `SLOT_WIDTH=01` in register 0x06. Each slot is exactly 24 bits. No zero padding. Frame = 192 bits, not 256.

6. **Left Justified format** — audio MSB appears on first BCLK after LRCLK pulse (`SDATA_FMT=01`).

7. **FPGA samples SDATAOUT on rising BCLK edge** — ADAU1978 outputs data on falling edge (max 18ns later), stable by the next rising edge.

8. **LRCLK = pulse mode** — single BCLK-wide HIGH pulse (`LR_MODE=1`). NOT 50% duty cycle.

9. **Chips 1 and 3 use different slot mapping** — registers 0x07=0x54 and 0x08=0x76, not the default. If left at default both chips try to output to slots 1–4 and corrupt each other.

10. **DRV_HIZ must be 1** — register 0x09 bit 3. Unused TDM slots must go HIGH-Z, not driven low, so chips can share the wire.

11. **47kΩ pull-down on shared SDATAOUT lines** — prevents floating when both chips are in HIGH-Z simultaneously (between frames).

12. **PLL_FILT RC filter is mandatory hardware** — not optional. Wrong values = PLL never locks.

13. **PWUP is the last register you write** — after all other config and after PLL_LOCK = 1.

14. **VHDL only.** **Cyclone IV E only.** **Quartus 18.1+.**

15. **Give exact register hex values** — not descriptions. Always include the full I2C write sequence with device address, register address, and data byte.

---

*ADAU1978 Rev B datasheet. 4 chips, 16 channels, 96kHz, TDM8, 24-bit slots, 18.432 MHz BCLK. Start from Step 1 unless told otherwise.*
