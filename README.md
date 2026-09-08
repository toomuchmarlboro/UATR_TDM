# UATR_TDM

**16-channel 24-bit audio capture — 4× ADAU1978 → Cyclone IV FPGA → LAN8720A → Fiber → 7km Subsea → PC**

> **Status (2026-09-08):**
> - ✅ **All 16 channels stream clean.** The ADC3/ADC4 dropouts were traced to a
>   misplaced DVDD decoupling cap and a dead U37, both fixed in hardware. The LRCLK
>   phase-shift work is intact but out of the signal path (`C_LRCLK_RETIME = false`) —
>   see [docs/LRCLK_PHASE_SHIFT.md](docs/LRCLK_PHASE_SHIFT.md).
> - ✅ **Ethernet stack complete and verified on hardware** — ~11,950 packets/s, 0 FPGA-side
>   sequence gaps, FCS and IP checksum confirmed in Wireshark.
> - ✅ **ADAU1978 I2C bring-up complete** — all four parts answer, every register read back
>   byte-exact and cross-checked field-by-field against the datasheet.
> - ✅ **On-FPGA 96 kHz → 24 kHz decimation added.** Two cascaded halfband FIR stages,
>   0.00015 dB passband ripple to 11 kHz, −102.5 dB alias rejection. Cuts the uplink 4×,
>   which takes the four-board array from *needs gigabit* to *fits in 100BASE-TX*.
>   See [docs/DECIMATION.md](docs/DECIMATION.md).
> - ✅ **Array moved to `192.168.3.x`**, boards and host together. Host setup:
>   [docs/HOST_SETUP.md](docs/HOST_SETUP.md).
> - 🟡 **Active configuration is 2× TDM8 (16 ch, 24-bit) — not TDM16.** TDM16 was built and
>   tested (`output_files/96K_TDM16.jic`) but reverted: timing analysis showed the capture
>   path was never the fault, so merging all four parts onto one net would only have traded
>   24-bit samples for 16-bit. Procedure kept in
>   [docs/TDM16_BRINGUP.md](docs/TDM16_BRINGUP.md) in case it's revisited.
> - 🔴 **The decimating images have never run on hardware.** Verified numerically
>   (bit-exact against a scipy reference) and structurally (Quartus, TNS 0.0), but the
>   first capture is the real test. **Read the packet rate first: ~3,000/s is success,
>   ~12,000/s means `valid_out` is being ignored downstream.** Bugs found and design
>   decisions: [docs/DECIMATOR_FINDINGS.md](docs/DECIMATOR_FINDINGS.md).

---

## Full System Pipeline

```
SUBSEA ARRAY                   TOPSIDE FPGA BOARD              TOPSIDE NETWORK
────────────────               ─────────────────────           ───────────────
                               Altera Cyclone IV E
4× ADAU1978 ADC                (minimum system, IO pins only)
  Chip 0  ch  1– 4             ┌─────────────────────────┐
  Chip 1  ch  5– 8    TDM8─A──►│ tdm8_rx A → ch_data_A   │
  Chip 2  ch  9–12    TDM8─B──►│ tdm8_rx B → ch_data_B   │
  Chip 3  ch 13–16             │                         │
                               │ packet_formatter        │
  All chips:                   │ udp_tx_core             │
  BCLK  ◄────────────────────  │ crc32 / arp_responder   │
  LRCLK ◄────────────────────  │                         │
  MCLK  ◄────────────────────  │ rmii_tx ────────────────┼──► LAN8720A module
                               └─────────────────────────┘    (RMII, 100 Mbps)
                                                                    │ RJ45
                                                                    │
                                                            Media Converter 
                                                            (BiDi WDM, 1310/1550nm)
                                                                    │
                                                            Single SM fiber core
                                                            (from 8-fiber hybrid cable)
                                                                    │
                                                         ───────────┴───────────
                                                              7km Hybrid
                                                           Armored Subsea Cable
                                                         ───────────┬───────────
                                                                    │
                                                            Single SM fiber core
                                                                    │
                                                            Media Converter
                                                            (BiDi WDM, matched pair)
                                                                    │ RJ45
                                                                    ▼
                                                                 Host PC
                                                            (Python UDP receiver)
```

---

## System Parameters

| Parameter | Value |
|-----------|-------|
| ADC | Analog Devices ADAU1978, 40-lead LFCSP |
| Chips | 4 |
| Total channels | 16 (4 channels per chip) |
| Resolution | 24-bit |
| ADC sample rate | 96 kHz — always, both image sets |
| Output sample rate | 96 kHz (`96K_*`) or **24 kHz** (`24K_*`, on-FPGA 4× decimation) |
| TDM architecture | 2× TDM8 — chip pairs share one SDATAOUT wire |
| Slot width | **32 BCLK per slot**, 24-bit data left-justified, 8 pad bits |
| BCLK | **24.576 MHz** (96k × 8 slots × 32 BCLK) |
| MCLK to ADAU1978 | **24.576 MHz** (256 × 96 kHz, MCS=011) — same net as BCLK |
| LRCLK | 96 kHz, 1-BCLK-wide pulse (LR_MODE=1) |
| FPGA | Altera Cyclone IV E, minimum system board, IO pins only |
| Board oscillator | 50 MHz |
| Ethernet PHY module | LAN8720A breakout module (RMII, 100 Mbps) |
| Required throughput | 36.864 Mbps at 96 kHz, 9.216 Mbps at 24 kHz (16ch × 24b × fs) |
| Available throughput | 100 Mbps — 2.2× headroom at 96 kHz, 8.8× at 24 kHz (one board) |
| Fiber link | Single-mode, BiDi WDM, up to 20 km rated |
| Subsea cable | Hybrid (Power + 8× SM fiber), 7 km |
| Subsea power | 24V topside → 2.5mm² copper conductors → 9V buck subsea |
| Toolchain | Quartus Prime 18.1+ / ModelSim-Altera |
| Language | VHDL only |

---

## Multi-AFE Deployment and Host DSP

The system above describes **one** AFE. The deployed array uses **4 AFEs = 64 channels**,
beamformed on a single host — 182.9 Mbps aggregate, 48,000 pkt/s, 70.8 GB/hr.

Host-side handling of that aggregate (decimate /4 to 24 kHz, then FLAC; ~9 GB/hr and 4×
less beamforming CPU) is specified in **[HOST_DSP_PIPELINE.md](HOST_DSP_PIPELINE.md)**,
including why in-FPGA GZIP compression was evaluated and rejected, and the inter-AFE
sample-alignment problem that is still open.

---

## Architecture Decisions Log

### Why 2× TDM8 and not TDM16 or 4× TDM4

- **TDM16 on one wire at 96kHz:** requires BCLK = 96k × 16 × 24 = 36.864 MHz, leaving only 3.5 ns timing margin at ADAU1978 input — too tight for a first PCB.
- **4× TDM4:** works and lowest BCLK (9.216 MHz) but wastes 4 SDATAOUT input pins.
- **2× TDM8:** 18.432 MHz BCLK with comfortable margins, only 2 data wires, symmetric 8-channel receivers. Best balance.

### Why LAN8720A and not W5100 or W5500

- W5100: SPI-based, max ~0.44 MB/s — 10× below the required 4.608 MB/s.
- W5500: SPI-based, max ~10 MB/s — adequate but adds SPI overhead and latency.
- LAN8720A: direct RMII interface to FPGA fabric, 100 Mbps line rate, no intermediate SPI bottleneck, minimal logic required.

### Why 100 Mbps and not Gigabit

36.864 Mbps required. 100 Mbps provides 2.7× headroom. Gigabit would require RGMII (more pins, more complex timing) and is unnecessary for this data rate.

### Why UDP and not TCP

Audio streaming is loss-tolerant and latency-sensitive. TCP retransmits cause variable delay. A dropped UDP packet means one frame of missing audio — the PC can detect and interpolate using sequence numbers. TCP overhead is also higher.

### Why fiber and not copper Ethernet at 7km

100 Mbps copper Ethernet (100BASE-TX) maximum reach is 100m. Fiber has no practical distance limit within the media converter spec (20 km rated). The subsea cable already includes singlemode fiber.

### Why BiDi WDM (single fiber) and not dual fiber

The client-supplied media converter uses WDM technology — TX and RX on one fiber at different wavelengths (1310nm and 1550nm). Only one fiber core is consumed from the 8-fiber cable, leaving 7 spares.

---

## Hardware Details

### FPGA Board

Altera Cyclone IV E minimum system. No onboard Ethernet, no onboard ADC interface, no onboard peripherals. All connections via IO pin header. IO banks are 3.3V.

### LAN8720A Module Wiring

| Module Pin | Signal | FPGA IO Pin | Direction | Notes |
|------------|--------|-------------|-----------|-------|
| VCC | 3.3V | — | — | Module power |
| GND | GND | — | — | |
| RST# | rmii_rst_n | any IO | FPGA → PHY | Assert LOW at startup, release HIGH |
| MDC | rmii_mdc | any IO | FPGA → PHY | ~2.5 MHz management clock |
| MDIO | rmii_mdio | any IO | Bidirectional | 10kΩ pull-up to 3.3V |
| REF_CLK | rmii_ref_clk | any IO | FPGA → PHY | 50 MHz — see note below |
| TXD0 | rmii_txd[0] | any IO | FPGA → PHY | |
| TXD1 | rmii_txd[1] | any IO | FPGA → PHY | |
| TX_EN | rmii_tx_en | any IO | FPGA → PHY | |
| RXD0 | rmii_rxd[0] | any IO | PHY → FPGA | Connect even if RX unused |
| RXD1 | rmii_rxd[1] | any IO | PHY → FPGA | |
| CRS_DV | rmii_crs_dv | any IO | PHY → FPGA | |

> **REF_CLK note:** Some LAN8720A modules have an onboard 50 MHz crystal. If yours does, REF_CLK is self-generated and the FPGA pin is not needed. Check your specific module before wiring.

### ADAU1978 Chip Pairing and Slot Assignment

```
Stream A wire:  Chip 0  ch  1– 4  → TDM slots 1–4
                Chip 1  ch  5– 8  → TDM slots 5–8

Stream B wire:  Chip 2  ch  9–12  → TDM slots 1–4
                Chip 3  ch 13–16  → TDM slots 5–8
```

```
FPGA output         Signal                Destination
───────────         ──────                ───────────
mclk_out            24.576 MHz            all 4× MCLKIN
bclk_out            24.576 MHz            all 4× BCLK
lrclk_out           96 kHz pulse          all 4× LRCLK

FPGA input          Source
──────────          ──────
sdata_in_A          Chip 0 SDATAOUT1 + Chip 1 SDATAOUT1  (47kΩ pull-down to GND)
sdata_in_B          Chip 2 SDATAOUT1 + Chip 3 SDATAOUT1  (47kΩ pull-down to GND)
```

### TDM Frame Structure

```
LRCLK:   |‾|__________________________________|‾|__
          1 BCLK wide pulse — marks start of slot 1

BCLK:    256 cycles per frame  (8 slots × 32 BCLK, 24-bit data + 8 pad bits)

sdata_in_A:
[Chip0 ch1:24b][Chip0 ch2:24b][Chip0 ch3:24b][Chip0 ch4:24b]  slots 1–4
[Chip1 ch1:24b][Chip1 ch2:24b][Chip1 ch3:24b][Chip1 ch4:24b]  slots 5–8

sdata_in_B: identical structure for Chips 2 and 3
```

- ADAU1978 outputs data on **falling BCLK edge** (max 18 ns delay)
- FPGA samples on **rising BCLK edge**
- LRCLK rising edge: latch completed 192-bit shift register, reset bit counter to 0
- Left Justified: first audio bit valid on BCLK cycle after LRCLK pulse

### Receiver Output Layout (per instance)

```
ch_data[191:168]  ch 1    ch_data[95:72]   ch 5
ch_data[167:144]  ch 2    ch_data[71:48]   ch 6
ch_data[143:120]  ch 3    ch_data[47:24]   ch 7
ch_data[119:96]   ch 4    ch_data[23:0]    ch 8
```

### Subsea Cable and Fiber Link

| Parameter | Value |
|-----------|-------|
| Cable type | Hybrid Power + Fiber, HDPE marine grade + Aramid yarn |
| Conductors | 2× 2.5mm² XLPE copper (power delivery) |
| Fiber count | 8× singlemode in stainless steel loose tube |
| Fiber used for data | 1 (BiDi WDM — single fiber full duplex) |
| Fiber spares | 7 |
| Cable OD | 18mm ±0.5mm |
| MBL | 1500 kg, working load 500 kg |
| Link budget at 7km | ~3.45 dB loss, ~15 dB margin — comfortable |

### Media Converter

| Parameter | Value |
|-----------|-------|
| Standards | IEEE 802.3, 802.3u, 802.3ab, 802.3z |
| Speed | 10/100/1000 Mbps Gigabit |
| Fiber | Single Core (BiDi WDM) |
| Max distance | 20 km |
| Technology | WDM — TX and RX on same fiber at different wavelengths |
| Power input | 9V DC, 80mA typical, 100mA peak |

> **BiDi pair requirement:** The two converters must be a matched pair — one TX at 1310nm, the other TX at 1550nm. Verify before deployment.

### Subsea Power Delivery

```
2.5mm² copper, 7km round trip resistance = ~96.3 Ω
At 100mA load: voltage drop = 9.63V

Supply 24V topside → ~14.4V arrives at subsea end
Subsea: 9V buck regulator (e.g. LM2596) powers media converter
```

---

## ADAU1978 Configuration

### Register settings

Written by `adau_sequencer.vhd`. Every field is checked against the datasheet
by `check_sync.py` on each build.

| Reg | Value | Description |
|-----|-------|-------------|
| 0x01 | `0x03` | PLL_MUTE=0, CLK_S=0 (MCLKIN), **MCS=011 = 256 × fS** (Table 9, fS=96 row) |
| 0x04 | `0x3F` | LR_POL=0, BCLKEDGE=0 (data on falling BCLK), LDO+VREF+all 4 ADCs enabled |
| 0x05 | `0x5B` | SDATA_FMT=01 (**left justified**), SAI=011 (TDM8), FS=011 (64–96 kHz) |
| 0x06 | `0x08` | SLOT_WIDTH=00 (**32 BCLK/slot**), DATA_WIDTH=0 (24b), LR_MODE=1 (pulse), SAI_MS=0 (slave) |
| 0x07 | `0x10` | Chips 0, 2: ch1→slot1, ch2→slot2 |
| 0x07 | `0x54` | Chips 1, 3: ch1→slot5, ch2→slot6 |
| 0x08 | `0x32` | Chips 0, 2: ch3→slot3, ch4→slot4 |
| 0x08 | `0x76` | Chips 1, 3: ch3→slot7, ch4→slot8 |
| 0x09 | `0xF8` | All 4ch drive enabled, DRV_HIZ=1 (unused slots HIGH-Z) |
| 0x00 | `0x01` | PWUP=1 — **write last, only after PLL_LOCK bit = 1** |

### I2C addresses

| Chip | ADDR1 | ADDR0 | Address |
|------|-------|-------|---------|
| 0 | 0 | 0 | 0x11 |
| 1 | 0 | 1 | 0x31 |
| 2 | 1 | 0 | 0x51 |
| 3 | 1 | 1 | 0x71 |

### Power-up sequence

```
1. Apply 3.3V AVDD. Hold PD/RST LOW.
2. Assert PD/RST HIGH → internal LDO charges DVDD.
3. Wait ~5 ms (DVDD > 1.2V, POR releases, safe margin).
4. Apply stable 18.432 MHz MCLK (FPGA must be running).
5. Wait 15 ms for PLL to lock.
6. Poll register 0x01 bit 7 (PLL_LOCK) until = 1.
7. Write registers: 0x04, 0x05, 0x06, 0x07, 0x08, 0x09.
8. Write register 0x00 = 0x01 (PWUP). LAST.
```

### Hardware requirements per chip

- **PLL_FILT (pin 3):** 1 kΩ + 5.6 nF + 390 pF to AVDD2 — mandatory
- **VREF (pin 2):** 100 nF + 10 µF to GND
- **DVDD (pin 10):** 100 nF + 10 µF MLCC X7R to GND
- **AVDD1/2/3:** 100 nF + 10 µF bulk per pin
- **Exposed pad (EP):** must be soldered to PCB ground plane
- **IOVDD:** match to FPGA IO bank voltage (3.3V)
- **47 kΩ pull-down** on each SDATAOUT line to GND

### ESP32 Role

The ESP32 is used **only for substitute while ADAU1978 is not available on site yet** it is only used to simulate 2x TDM8 lines to verify FPGA logic working as intended. One ESP32 represents 2x ADAU1978 chips. WE have a total of 4x ADAU1978 that is going to be on the final board. We have 2x ESP32s for testing purposes. (for claude, this step of making a ESP32 testbed is done)
To allow for immediate visual verification on the FPGA's 7-segment display and the PC USB receiver, the ESP32s output distinct, human-readable hexadecimal patterns rather than actual audio waveforms. Data is clocked out MSB-first, Left-Justified.

**Stream A (`sdata_in_A`)**
* Ch 1: `0x01AAAA`
* Ch 2: `0x02BBBB`
* Ch 3: `0x03CCCC`
* Ch 4: `0x04DDDD`
* Ch 5: `0x05EEEE`
* Ch 6: `0x06FFFF`
* Ch 7: `0x071111`
* Ch 8: `0x082222`

**Stream B (`sdata_in_B`)**
* Ch 9: `0x093333`
* Ch 10: `0x0A4444`
* Ch 11: `0x0B5555`
* Ch 12: `0x0C6666`
* Ch 13: `0x0D7777`
* Ch 14: `0x0E8888`
* Ch 15: `0x0F9999`
* Ch 16: `0x100000`
---

## PLL Configuration

Single ALTPLL instance `pll_audio.vhd`, all three outputs exact from 50 MHz
(3125 = 5⁵ divides cleanly, so there is no rounding anywhere):

| Output | Ratio | Frequency | Gives |
|--------|-------|-----------|-------|
| c0 | 768/3125 | 12.288 MHz | 48 kHz — **do not use**, kills U37/U38 |
| c1 | 1152/3125 | 18.432 MHz | 72 kHz — working fallback |
| **c2** | **1536/3125** | **24.576 MHz** | **96 kHz — current** |

`top_system.vhd` selects the rate by which output it maps to `clk_18m` in the
`u_pll` port map. Changing it also means changing MCS (`0x01`) and FS (`0x05`)
to match — see the calculation below.

The Ethernet side is independent: `rmii_ref_clk` comes from the PHY at 50 MHz
and the two domains only meet through `async_fifo`, which the SDC declares
asynchronous. Lowering the audio rate reduces FIFO load, never increases it.

---

---

## Clock and Framing Calculation

The single most important constraint on this board, and the thing that cost the
most time to find.

### MCLK and BCLK are the same net

Each LMK1C1104 output feeds one ADC's **MCLKIN (pin 7)** *and* its **BCLK
(pin 16)** through two separate 49.9 Ω resistors:

```
U2-Y2 --+-- R13 --> MCLK_1 --> U19 pin 7
        +-- R14 --> BCLK_1 --> U19 pin 16
```

So MCLK and BCLK are physically one signal. That fixes the whole configuration,
because the MCS ratio must equal the BCLK ratio:

```
BCLK = 8 slots x SLOT_WIDTH x fS        (Table 10, TDM8)
MCLK = MCS_ratio x fS                   (Table 9)
MCLK = BCLK   =>   MCS_ratio = 8 x SLOT_WIDTH
```

### Which combinations are legal

Table 10 gives TDM8 three slot widths; Table 9 gives the MCS ratios available
at each standard rate. Only where they meet is a valid configuration:

| fS | 16-bit slots (128×) | 24-bit slots (192×) | 32-bit slots (256×) |
|---|---|---|---|
| 32 kHz | 4.096 MHz | — | 8.192 MHz |
| 44.1 kHz | 5.6448 MHz | — | 11.2896 MHz |
| 48 kHz | 6.144 MHz | — | 12.288 MHz |
| **96 kHz** | 12.288 MHz | 18.432 MHz | **24.576 MHz ← used** |
| 192 kHz | 24.576 MHz | 36.864 MHz | — |

**192 × fS exists only at 96 kHz and 192 kHz.** That matters because:

### 24-BCLK slots do not work on this part

`SLOT_WIDTH=01` (24 BCLK) is listed as legal in Table 21, and at 96 kHz it gives
exactly 18.432 MHz — which is what the board was originally designed around.
**The ADAU1978 refuses it.** Correctly configured, PLL locked, every register
reading back byte-exact, and SDATAOUT never driven.

This is not documented anywhere in the datasheet. It was found by putting one
part into **master mode** (`SAI_MS=1`, with its BCLK and LRCLK resistors lifted
so it wasn't fighting the FPGA): given free rein, the part generated **32-BCLK
slots** and drove data immediately. Switching the FPGA to match fixed it.

Two contributing reasons it can't work:

- 24-bit data in a 24-BCLK slot leaves **no room** for the I²S one-BCLK delay,
  so `SDATA_FMT` must be left-justified (`01`) rather than I²S (`00`).
- Even with left-justified framing it still refuses. The slot width itself is
  the problem.

### The current numbers

```
PLL c2       = 50 MHz x 1536/3125 = 24.576000 MHz   exact
frame        = 8 slots x 32 BCLK  = 256 BCLK
fS           = 24.576 MHz / 256   = 96000.0 Hz
MCS=011      = 256 x fS           = 24.576 MHz      matches MCLK
data         = 24 bit, left-justified, 8 pad bits per slot
LRCLK        = 1 BCLK wide pulse, 40.7 ns, once per 10.42 us
```

`tdm8_rx.vhd` shifts 256 bits per frame and takes the **top 24 of every 32**,
discarding the pad bits. `C_BIT_ADJ = -1` shifts the capture window by one BCLK;
that offset was found by measurement (`udp_monitor.py --align`), not derived.

### Throughput — and why there are two image sets

Two builds exist from the same design, differing only in whether the on-FPGA
decimator is in the signal path (`C_DECIMATE` in `top_system.vhd`).

**The packet never changes size — only how often one is sent.** Every packet
carries exactly 8 audio frames at either rate:

```
                          96 kHz (96K_*)   24 kHz (24K_*)
packets per second            12,000           3,000
bytes on the wire                476             476
```

Per board:

```
payload  16 ch x 24 bit x fs        36.864 Mbit/s     9.216 Mbit/s
+ 10 B packet header                39.360            9.840
+ eth/IP/UDP + preamble/FCS/IFG     45.696           11.424   <- on the wire
of 100BASE-TX                          45.7%            11.4%
disk  16 x fs x 3 B                  4.6 MB/s         1.15 MB/s
                                    16.6 GB/hour      4.1 GB/hour
```

Four boards:

```
aggregate                          182.784 Mbit/s   45.696 Mbit/s
                                   needs GIGABIT    fits 100BASE-TX
```

The wire figure exceeds the audio because 66 bytes of framing ride on every
packet — 410 B payload inside 476 B on the link, 86% efficiency:

```
410 B payload + 8 UDP + 20 IPv4 + 14 Ethernet = 452 B frame body
      + 8 B preamble/SFD + 4 B FCS + 12 B inter-frame gap = 476 B
```

Because that overhead is **per packet**, sending 4x fewer packets saves it 4x
over too, so the wire rate scales by exactly 4.00.

**Which to use:** `24K_*` unless you need content above 11 kHz — inside that
band it costs nothing measurable (0.00015 dB ripple, −102.5 dB alias
rejection, below the converter's own noise floor) and it removes the gigabit
requirement, cuts host CPU 4x and quarters the disk rate. `96K_*` for the full
0–42 kHz the ADC passes, or as the fallback that has actually run on hardware.

See [docs/DECIMATION.md](docs/DECIMATION.md) and
[docs/HOST_SETUP.md](docs/HOST_SETUP.md).


## Ethernet / UDP Details

### Network configuration (static — no DHCP)

```vhdl
-- Everything derives from C_NODE (1-4) in top_system.vhd.
FPGA_MAC  : x"DEADBEEF00" & C_NODE      -- DE:AD:BE:EF:00:0n
FPGA_IP   : 192.168.3.(100 + C_NODE)    -- .101 .102 .103 .104
PC_IP     : 192.168.3.10                -- C_PC_IP
UDP_PORT  : 5004 + C_NODE               -- 5005 5006 5007 5008
```

Moved from `192.168.1.x` on 2026-09-07. `C_PC_IP` moved with the boards: it is
both the audio destination *and* the filter deciding whose ARP the board will
learn from, so changing only the board addresses gives four boards
transmitting into nothing.

⚠ **The host must hold BOTH `192.168.3.10` and `192.168.1.10`** while boards of
either generation are in use — `C_PC_IP` is one value per image, so the host is
the side that carries both. Full procedure:
[docs/HOST_SETUP.md](docs/HOST_SETUP.md), addressing changes:
[docs/CHANGING_IP.md](docs/CHANGING_IP.md).

### UDP packet format (sent every 8 audio frames = 83.3 µs at 96 kHz)

```
Ethernet frame
├── Dst MAC   6 bytes
├── Src MAC   6 bytes
├── EtherType 2 bytes   0x0800
├── IP header 20 bytes  proto=UDP, TTL=64
├── UDP header 8 bytes  checksum=0 (optional for UDP)
└── Payload:
      Bytes  0– 3   Magic:  0xAD 0xA1 0x97 0x78
      Bytes  4– 7   Sequence number (uint32, MSB first)
      Bytes  8– 9   Frame count in this packet (uint16)
      Per frame × 8  (50 bytes each):
        Bytes 0– 1   Frame index (uint16)
        Bytes 2– 4   Ch  1  (24-bit signed, MSB first)
        Bytes 5– 7   Ch  2
        ...
        Bytes 47–49  Ch 16
Total payload: 10 + (8 × 50) = 410 bytes
Total UDP frame: ~454 bytes
Transmission time at 100 Mbps: ~43 µs  < 83.3 µs frame window  ✅
```

### RMII transmit timing

```
REF_CLK = 50 MHz
2 bits per clock cycle
1 byte = 4 clock cycles
454-byte frame = 1816 cycles = 36.3 µs + preamble/IFG ≈ 43 µs total
Frame budget = 83.3 µs  →  comfortable margin
```

---

### Control protocol (PC → FPGA)

`udp_rx_core.vhd` accepts a plain UDP datagram addressed to the board's IP.
**There is no port filtering** — any port works.

| Payload byte | Meaning |
|---|---|
| `[0]` | bits [3:2] ADC select 0–3, bits [1:0] channel select 0–3 |
| `[1]` | gain byte → register `0x0A`–`0x0D` of the selected part |
| `[2]` | *optional* control flags. **bit 0 = 48 V phantom enable** |

`adau_sequencer` picks it up in `ST_IDLE` and writes it over I²C. A 2-byte
packet is still valid and simply leaves the flag state untouched.

Gain encoding (Table 25): `0x00` = +60 dB, −0.375 dB per step, `0xA0` = 0 dB,
`0xFE` = −35.625 dB, `0xFF` = mute.

48 V is gated on **three** things — the build constant `C_ENABLE_48V`, the
staged power-up timer, and this runtime flag, which defaults to 0. Phantom
power therefore never comes up on its own after a reset.

```
python python/ctrl.py --test --channel 3     prove the receive path
python python/ctrl.py --set 3 -6             one channel to -6 dB
python python/ctrl.py --all 0                every channel to 0 dB
python python/mixer_gui.py                   live meters + faders + phantom
```

✅ **Verified on hardware 2026-08-09.** `ctrl.py --test --channel 1`:
baseline RMS 373 → mute 0.0 → restore 466. The FPGA parsed a UDP datagram from
the PC and wrote the gain register over I²C. Ethernet is proven in both
directions.


## File Index

### Repository layout

```
rtl/        Synthesizable VHDL — everything in TDM_UATR.qsf's VHDL_FILE list
ip/         ALTPLL / FIFO IP cores, one directory per .qip (self-contained —
            Quartus resolves each .qip's files relative to itself)
sim/        Testbenches, modelsim.ini, wave.do — not in the synthesis hierarchy
python/     Host-side tools (Python 3)
hardware/   Schematic PDF and KiCad netlist export
docs/       Bring-up logs and findings, referenced from this README
db/, incremental_db/, output_files/   Quartus build output — gitignored, regenerable
```

`TDM_UATR.qpf` / `.qsf` / `.sdc` stay at the repository root so the project still
opens in Quartus by double-clicking the `.qpf`. Everything the source files reference
is a path relative to the project root — no fixed drive letters. **After pulling this
layout change, run Project → Clean Project (or delete `db/`) once** so Quartus drops
any cached references to the old flat paths.

The step-1/2 files superseded by `top_system.vhd` (`top_tdm.vhd`, `top_loopback.vhd`,
`seven_seg*.vhd`) were removed on 2026-08-08 — recover from git history if ever needed.

### RTL — top level

| File | Status | Description |
|------|--------|-------------|
| `rtl/top_system.vhd` | ✅ Verified | Top level. Clock/reset, staged power-up, I2C open-drain buffers, TX arbiter, build-option constants |

### RTL — audio path

| File | Status | Description |
|------|--------|-------------|
| `rtl/tdm8_master.vhd` | ✅ Verified | Generates LRCLK (1 BCLK pulse @ 96 kHz) from 24.576 MHz |
| `rtl/tdm8_rx.vhd` | ✅ Verified | TDM8 receiver — 264-bit shift reg (256-BCLK frame + `C_BIT_ADJ` slack), latch on LRCLK |
| `rtl/tdm16_rx.vhd` | 🟡 Built, not active | Single-net 16-slot receiver for the TDM16 experiment — see [docs/TDM16_BRINGUP.md](docs/TDM16_BRINGUP.md) |
| `rtl/tdm16_merge.vhd` | ✅ Verified | Merges the two TDM8 streams into 16 channels |
| `ip/pll_audio/pll_audio.vhd` | ✅ Verified | ALTPLL: 50 MHz → 24.576 MHz (c2, ×1536 / ÷3125) — see [PLL Configuration](#pll-configuration) |
| `ip/async_fifo/async_fifo.vhd` | ✅ Verified | Clock-domain crossing, 24.576 MHz → 50 MHz |

### RTL — ADC control

| File | Status | Description |
|------|--------|-------------|
| `rtl/i2c_master.vhd` | ✅ Verified | I2C master. Bus recovery, probe mode, repeated-START reads |
| `rtl/adau_sequencer.vhd` | ✅ Verified | 128-address scan, soft reset, register boot, two-pass PWUP, live PLL poll |

### RTL — Ethernet

| File | Status | Description |
|------|--------|-------------|
| `rtl/crc32.vhd` | ✅ Verified | Ethernet FCS (0x04C11DB7). **Root cause of the original "Ethernet dead" fault** |
| `rtl/rmii_tx.vhd` | ✅ Verified | RMII MAC TX — preamble, data, FCS, IFG |
| `rtl/rmii_rx.vhd` | ✅ Verified | RMII MAC RX. Proven by the control-path test |
| `rtl/udp_tx_core.vhd` | ✅ Verified | Ethernet + IP + UDP headers, 452-byte frame |
| `rtl/udp_rx_core.vhd` | ✅ Verified | UDP receive path, gain + flags control |
| `rtl/arp_responder.vhd` | ✅ Verified | ARP replies so the PC resolves the FPGA IP |
| `rtl/packet_formatter.vhd` | ✅ Verified | 10-byte header + 8 × 50-byte frames = 410-byte payload |

### Host tools (Python 3, in `python/`)

| File | Description |
|------|-------------|
| `udp_monitor.py` | One-shot capture: link rate, loss, per-channel statistics, `--wav`, `--align`. The single definition of the packet geometry — the others import it |
| `i2c_scan.py` | Decodes the boot-time I2C diagnostics: bus health, 128-address sweep, per-part table, register verify |
| `check_sync.py` | Cross-checks the Python decoders against the RTL (in `../rtl/`) **and** the datasheet tables. 52 assertions, run on every build |
| `sim_chain.py` | Cycle-accurate model of the TDM chain used to settle `C_BIT_ADJ` without a licensed simulator |
| `rawview.py` | Decodes `tdm8_rx`'s raw-capture debug mode, bit for bit |
| `mixer_gui.py` | **Live tkinter mixer** — 16 meters, gain faders, mute, 48 V toggle |
| `mixer.py` | Same meters in the terminal, no GUI |
| `ctrl.py` | Control protocol and `--test`, which proves the UDP receive path |
| `timeline.py` | Reports channel dropout windows over a capture |
| `gdat2.py` | Serial telemetry GUI tab — see [docs/GDAT2_TELEMETRY.md](docs/GDAT2_TELEMETRY.md) |
| `imu_test.py` | IMU/AHRS connection test over the same link — checks the attitude is *live*, not just present (unproven-constant / all-zero / shifted field map) |
| `imu_standalone.py` | The same check as a **single self-contained file** — stdlib only, no project imports. Copy it to any machine and run it. Snapshot; the two files above stay authoritative |
| `mixer_gui_standalone.py` | The **whole GUI in one file** — no imports from this directory (numpy and tkinter still used). **Generated, do not edit** |
| `make_gui_standalone.py` | Generates the above by extracting definitions from the real modules with `ast`. `--check` fails if the generated file is stale — a regenerated copy cannot drift, a hand-edited one silently does |

### Testbenches (`sim/`, not in the synthesis hierarchy)

| File | Description |
|------|-------------|
| `sim/tb_tdm8_rx.vhd` | ModelSim — known pattern, frame assertions |
| `sim/tb_tdm16.vhd` | ModelSim — 16-channel merge |
| `sim/tb_chain.vhd` | ModelSim — full chain |

Run from the repository root:

```
vlib work
vcom -modelsimini sim/modelsim.ini -work work -2002 rtl/tdm8_master.vhd rtl/tdm8_rx.vhd rtl/tdm16_merge.vhd sim/tb_tdm16.vhd
vsim -modelsimini sim/modelsim.ini -do sim/wave.do work.tb_tdm16
```

(`-modelsimini sim/modelsim.ini` points at the tracked library mapping — ModelSim
otherwise resolves `modelsim.ini` from the current directory and would silently fall
back to the install default. ModelSim's own `*.mpf` project cache is machine-specific
— it's gitignored and regenerates from the `vcom`/`vsim` lines above.)

### Documentation (`docs/`)

**Start here**

| File | Description |
|------|-------------|
| `HOST_SETUP.md` | **The complete host procedure** — adapter, firewall, which `.jic` to flash, verifying audio and telemetry |
| `DECIMATION.md` | The 96→24 kHz decimator, and the ADC gain budget that goes with it |
| `CHANGING_IP.md` | Changing the array's addressing — the four things that must agree |
| `NETWORK_SETUP.md` | Why the network is arranged this way: capacity, collisions, Python limits |
| `DECIMATOR_FINDINGS.md` | Design decisions, and every bug found building the decimator |

**Reference**

| File | Description |
|------|-------------|
| `ETHERNET_TRANSMISSION.md` | The UDP/IP/Ethernet transmit path end to end |
| `MULTI_BOARD.md` | Four-board deployment (address table pre-migration — see `HOST_SETUP.md`) |
| `PHANTOM_POWER.md` | 48 V control, readback and the optional watchdog |
| `TELEMETRY_INTEGRATION.md` | The three buoy sensors and how to lift them into an app |
| `GDAT2_TELEMETRY.md` | `$GDAT2` field map, and the AHRS quantisation trap |

**Bring-up history**

| File | Description |
|------|-------------|
| `TDM16_BRINGUP.md` | TDM16 procedure and why it was reverted |
| `LRCLK_HOLD_VIOLATION.md` | The ~4 ns LRCLK hold-spec violation; fixed, kept for the reasoning |
| `LRCLK_PHASE_SHIFT.md` | The phase-shift investigation — intact but out of the signal path |
| `TDM2_NETLIST_FINDINGS.md` | Netlist trace of the LMK1C1104 buffer fan-out; composes with the hold-violation finding |

---

## Build Options

Compile-time constants. All are documented in-place with the reasoning.

`top_system.vhd`

| Constant | Default | Effect |
|----------|---------|--------|
| `C_I2C_SWAP` | `true` | Compensates a **schematic error**: the net named `SCL` lands on ADAU pin 17, which is SDA. Do not "fix" without fixing the copper |
| `C_LRCLK_TEST_50PCT` | `false` | Drives LRCLK as a 0.27 Hz square for continuity testing. A real LRCLK is a 54 ns pulse that reads ~17 mV on a DMM |
| `C_ENABLE_48V` | `false` | Holds 48 V phantom power off |
| `C_BUFFER_EN_ACTIVE_HIGH` | `true` | LMK1C1104 `1G` polarity |

`adau_sequencer.vhd`

| Constant | Default | Effect |
|----------|---------|--------|
| `C_SOFT_RESET_FIRST` | `true` | Issues S_RST before configuring, so the state machine initialises with clocks already stable |
| `C_VERIFY_IDX` | `0` | Which ADC the register verify reads back (0=U19, 1=U20, 2=U37, 3=U38). Only one part can be verified per boot |

---

## Project History

Condensed. The detail that matters now lives in
[Clock and Framing Calculation](#clock-and-framing-calculation) and the
[Hardware Bring-Up Log](#hardware-bring-up-log).

**Simulation** — TDM8 master and receiver verified in ModelSim. `sim/tb_tdm8_rx.vhd`
drives a known 8-channel pattern and asserts `ch_data_out` after three complete
frames; `sim/tb_tdm16.vhd` covers the 16-channel merge. Both are still in the tree
and still the fastest way to check a framing change before it reaches hardware.

![ModelSim TDM16 waveform](docs/modelsim_tdm16.png)

**FPGA loopback and SignalTap** — an internal pattern generator drove `tdm8_rx`
on silicon and framing was confirmed over JTAG, before any ADC existed. The
loopback and 7-segment debug sources were removed on 2026-08-08; recover them
from git history if ever needed.

**Ethernet stack** — complete and verified on hardware: ~12,000 packets/s,
zero FPGA-side sequence gaps, correct FCS and IP checksum in Wireshark. It did
not work at first, and the cause was `crc32.vhd` — 7 of the 32 XOR equations
(bits 10, 11, 12, 16, 17, 22, 23) carried spurious terms, so every frame left
with a garbage FCS and the PC's NIC discarded all of it silently. Verified after
the fix: `"123456789"` → `0x649C2FD3`, RX residue `0xC704DD7B`.

**ADC bring-up** — see the log below. The short version: I²C had never once run
(an `ena` pulse the FSM could not see), four OPA1671 buffers were on a 15 V rail
against a 6 V maximum, both clock buffers were fitted rotated 180°, and the
ADAU1978 turned out to reject the 24-BCLK slot width the board was designed
around.

**Current state (2026-08-18)** — clock buffers fixed, all four ADAU1978s frame at
96 kHz / 24-bit on 2× TDM8. Three of the four (all but U20) show channel dropouts,
root-caused to the FPGA violating the ADAU1978's LRCLK hold spec by ~4 ns — see
[docs/LRCLK_HOLD_VIOLATION.md](docs/LRCLK_HOLD_VIOLATION.md); that is the open item.

---

## Hardware Bring-Up Log

Findings from bringing up the Souncard_Robomarine 1.0 PCB. Recorded because none of it
is derivable from the RTL.

### Schematic errors found

| Error | Impact | Resolution |
|-------|--------|------------|
| **SDA/SCL crossed** — net `SCL` wires to ADAU pin 17 (really SDA), net `SDA` to pin 18 (really SCL). The KiCad symbol is correct; the wiring is not | I2C could never work as drawn | Compensated in firmware by `C_I2C_SWAP = true`. Fix the copper in the next revision |
| **OPA1671 on +15 V** — U44–U47 (VREF→VCOM buffers) have V+ on +15 V against a **6 V absolute maximum** (recommended 1.7–5.5 V) | Destroyed all four. Their damaged inputs clamped VREF to 0–0.8 V on every ADC, and they loaded the ±15 V rail | **Removed, not replaced.** OPA1632 `VOCM` self-biases to mid-rail (0 V), which is correct on ±15 V, and the ADC inputs are AC-coupled — the buffers were never needed. Delete them in the next revision |
| **PLL loop filter returns to GND**, not AVDD2 as Table 8 requires | None observed | Disproven as a fault: U19/U37 lock with the GND return. Component values (1 kΩ / 390 pF / 5600 pF) are correct for the MCLK option |

### Firmware bugs found

- **`i2c_master.vhd`** — `ena` was sampled only on quarter-bit boundaries while the
  sequencer pulsed it for one cycle, so the pulse was missed ~99% of the time. **No I2C
  transaction had ever run.**
- **PWUP ordering** — the datasheet requires PWUP be asserted ≥10 ms after DVDD > 1.2 V
  with stable clocks. Boot is now two-pass: configure everything, settle 30 ms, then PWUP.
- **False PLL-lock reporting** — `i2c_master` pre-loads `data_rd` with `0xFF` to invalidate
  aborted reads. The live poll took bit 7 of that blindly, so a *failed* read reported
  `PLL_LOCK = 1`. Reported four locked PLLs on a board whose MCLK never arrived.
- **Scan abort** — the address sweep stopped at 9 answers, collapsing "hard stuck-low SDA"
  (128 answers) and "a few glitched bits" (9) onto one number. Now always sweeps all 128.

### Measurement traps hit (all cost real time)

- **LRCLK is a 54 ns pulse at 96 kHz** — 0.5% duty, so a *working* LRCLK reads **~17 mV**
  on a multimeter. Use `C_LRCLK_TEST_50PCT`, or a scope.
- **18 MHz on a handheld DMM** reads as a meaningless fraction of a volt. MCLK/BCLK cannot
  be checked with a meter at all.
- **Scope frequency counters quantise.** An 18.432 MHz clock (54.25 ns) on a 100 MSa/s
  timebase alternates between "20 MHz" (50 ns) and "16.6 MHz" (60 ns). Both are the same
  correct clock.
- **Resistance to GND across bulk capacitance is meaningless** — the meter charges the cap
  and the reading climbs. A rail also reads "shorted" on a continuity beeper because of the
  substrate diodes in every IC on it; reverse the probes and the asymmetry gives it away.
- **A `.sof` is volatile.** Power-cycling boots the `.jic` in flash instead — usually an
  older build. Power-sequencing changes cannot be tested with a `.sof` at all.

### Outstanding

✅ **RESOLVED, kept for the record — both LMK1C1104 clock buffers (U1, U2) were
damaged.** Confirmed with a 10× probe: their inputs loaded the FPGA's 3.3 V outputs
down to 2.0 V, and their outputs produced 0.9 V (U1) and millivolts (U2). The ADAU1978
needs **VIH = 0.7 × IOVDD = 2.31 V**, so the ADCs never saw a valid clock, never framed,
and left SDATAOUT high-Z. Everything upstream and downstream was verified good — the
FPGA drove a clean 3.3 V when jumpered directly.

Fix applied: replace both, or bypass in place by bridging pin 1 to pins 3/5/7/8 on each footprint
(the FPGA can drive these loads directly; the 49.9 Ω series resistors stay).

🔴 **Current open item: channel dropouts on 3 of 4 ADCs.** See
[docs/LRCLK_HOLD_VIOLATION.md](docs/LRCLK_HOLD_VIOLATION.md) and
[docs/TDM2_NETLIST_FINDINGS.md](docs/TDM2_NETLIST_FINDINGS.md) for the current
investigation — this is a different fault from the resolved buffer damage above.

---

## PC Receiver

```python
import socket, struct

MAGIC    = b'\xAD\xA1\x97\x78'
sock     = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", 5005))
sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 * 1024 * 1024)
print("Listening for UATR_TDM stream on UDP 5005...")

prev_seq = None
while True:
    data, _ = sock.recvfrom(65535)
    if data[0:4] != MAGIC:
        continue
    seq         = struct.unpack(">I", data[4:8])[0]
    frame_count = struct.unpack(">H", data[8:10])[0]
    if prev_seq is not None and seq != prev_seq + 1:
        print(f"WARNING: {seq - prev_seq - 1} packet(s) dropped")
    prev_seq = seq
    offset = 10
    for f in range(frame_count):
        frame_idx = struct.unpack(">H", data[offset:offset+2])[0]
        samples   = [int.from_bytes(data[offset+2+i*3:offset+5+i*3],
                                    'big', signed=True) for i in range(16)]
        offset   += 50
        # samples[0..15] = ch1..ch16
```

---

## Constraints

- VHDL only — no Verilog or SystemVerilog
- Cyclone IV E only — no Cyclone V or later features
- Quartus Prime 18.1+
- `rtl/tdm8_rx.vhd` is complete — instantiated twice in `rtl/top_system.vhd`, do not rewrite
- `rtl/top_system.vhd` is the only top-level; `top_tdm.vhd` / `top_loopback.vhd` were removed 2026-08-08
- All FPGA IO pins are 3.3V — LAN8720A IOVCC must also be 3.3V
- ESP32 only acts as a surrogate 2x ADAU1978 chip outputting TDM8
- UDP checksum may be set to 0x0000 (valid per RFC 768) to simplify implementation

---

*Analog Devices ADAU1978 Rev B. FTDI LAN8720A. Altera Cyclone IV E. Quartus Prime 18.1+.*
*Step 4 (TDM Acquisition) verified on hardware. Current tasks: ESP32 Integration (Step 6) and Ethernet Stack (Step 5).*
