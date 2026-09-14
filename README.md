# UATR_TDM

**16-channel 24-bit underwater acoustic acquisition — 4× ADAU1978 → Cyclone IV E → LAN8720A → fiber → 7 km subsea → host PC**

Four of these boards form the deployed array: **64 channels**, beamformed on a
single host.

---

## Status — final

The design is complete and the firmware is frozen. `rtl/top_system.vhd` as
committed is the shipping configuration, and the eight flashable images in
`output_files/` were built from it by `build_all.sh`.

| | |
|---|---|
| **Shipping build** | `C_DECIMATE = true` — **24 kHz** output, 4× on-FPGA decimation |
| **Array addressing** | `192.168.3.101–104`, host `192.168.3.10`, ports 5005–5008 |
| **Phantom power** | `C_ENABLE_48V = true`, host-gated, watchdog available but off |
| **Fit** | 3,429 / 6,272 LE (55%), 2,610 registers, 8,290 memory bits, 0 multipliers |
| **Timing** | **TNS 0.000 on every corner**; worst setup +3.528 ns (`rmii_clk`), worst hold +0.439 ns |
| **Build consistency** | `python/check_sync.py` — **58 checks passed, 0 failed** |
| **Toolchain** | Quartus Prime 25.1std Lite, EP4CE6E22C8 |

**What is proven on hardware:** all 16 channels stream clean at 96 kHz/24-bit;
the Ethernet stack in both directions (~11,950 pkt/s, zero FPGA-side sequence
gaps, FCS and IP checksum confirmed in Wireshark); ADAU1978 I²C bring-up with
every register read back byte-exact; gain and 48 V control over UDP.

**What is proven numerically:** the 24 kHz decimator — bit-exact against a
scipy reference (`sim/decim_ref_vectors.txt`), 0.00015 dB passband ripple to
11 kHz, −102.5 dB worst alias band, and structurally clean through the fitter.
Per `docs/DECIMATOR_FINDINGS.md` §5 the decimating image had not yet been
captured on the bench at the time that record was written. **On the first
capture, read the packet rate first: ~3,000/s is success, ~12,000/s means
`valid_out` is being ignored downstream.**

---

## Quick start

```powershell
# 1. Host adapter — BOTH subnets, both required while any older board is in use
netsh interface ipv4 set address name="Ethernet" static 192.168.3.10 255.255.255.0
netsh interface ipv4 add address name="Ethernet" 192.168.1.10 255.255.255.0

# 2. Let the audio in
New-NetFirewallRule -DisplayName "TDM_UATR audio" -Direction Inbound `
    -Protocol UDP -LocalPort 5005-5008 -Action Allow -Profile Private
```

```
# 3. Flash each board with its own image — the IP is baked into the bitstream
output_files/24K_NODE1_192-168-3-101.jic   ->  board 1
output_files/24K_NODE2_192-168-3-102.jic   ->  board 2
output_files/24K_NODE3_192-168-3-103.jic   ->  board 3
output_files/24K_NODE4_192-168-3-104.jic   ->  board 4

# 4. Verify
python python/discover.py     # which boards, which subnet, which rate, loss
python python/imu_test.py     # the buoy telemetry side
python python/mixer_gui.py    # live meters, faders, 48 V
```

Full procedure, including the failure modes and what each message means:
**[docs/HOST_SETUP.md](docs/HOST_SETUP.md)**.

---

## Full system pipeline

```
SUBSEA ARRAY                   TOPSIDE FPGA BOARD              TOPSIDE NETWORK
────────────────               ─────────────────────           ───────────────
                               Altera Cyclone IV E
4× ADAU1978 ADC                (minimum system, IO pins only)
  Chip 0  ch  1– 4             ┌─────────────────────────┐
  Chip 1  ch  5– 8    TDM8─A──►│ tdm8_rx A → ch_data_A   │
  Chip 2  ch  9–12    TDM8─B──►│ tdm8_rx B → ch_data_B   │
  Chip 3  ch 13–16             │ tdm16_merge             │
                               │ decimator  (96k → 24k)  │
  All chips:                   │ packet_formatter        │
  BCLK  ◄────────────────────  │ udp_tx_core             │
  LRCLK ◄────────────────────  │ crc32 / arp_responder   │
  MCLK  ◄────────────────────  │ rmii_tx ────────────────┼──► LAN8720A module
                               └─────────────────────────┘    (RMII, 100 Mbps)
                                                                    │ RJ45
                                                            Media Converter
                                                            (BiDi WDM, 1310/1550 nm)
                                                                    │
                                                         ───────────┴───────────
                                                              7 km Hybrid
                                                           Armored Subsea Cable
                                                         ───────────┬───────────
                                                                    │
                                                            Media Converter
                                                            (matched BiDi pair)
                                                                    │ RJ45
                                                                    ▼
                                                                 Host PC
                                                          (Python UDP receiver)
```

---

## System parameters

| Parameter | Value |
|-----------|-------|
| ADC | Analog Devices ADAU1978, 40-lead LFCSP |
| Chips | 4 |
| Total channels | 16 per board (4 per chip), 64 across the array |
| Resolution | 24-bit |
| **ADC sample rate** | **96 kHz — always, both image sets** |
| **Output sample rate** | **24 kHz** (`24K_*`, shipping) or 96 kHz (`96K_*`, fallback) |
| TDM architecture | 2× TDM8 — chip pairs share one SDATAOUT wire |
| Slot width | **32 BCLK per slot**, 24-bit data left-justified, 8 pad bits |
| BCLK | **24.576 MHz** (96k × 8 slots × 32 BCLK) |
| MCLK to ADAU1978 | **24.576 MHz** (256 × 96 kHz, MCS=011) — *same net as BCLK* |
| LRCLK | 96 kHz, 1-BCLK-wide pulse (LR_MODE=1) |
| FPGA | Altera Cyclone IV E, EP4CE6E22C8, minimum system board, IO pins only |
| Board oscillator | 50 MHz |
| Ethernet PHY | LAN8720A breakout module (RMII, 100 Mbps) |
| Payload rate | 9.216 Mbps at 24 kHz, 36.864 Mbps at 96 kHz (16 ch × 24 b × fs) |
| On the wire | 11.4 Mbps at 24 kHz, 45.7 Mbps at 96 kHz — one board |
| Fiber link | Single-mode, BiDi WDM, 20 km rated |
| Subsea cable | Hybrid (power + 8× SM fiber), 7 km |
| Subsea power | 24 V topside → 2.5 mm² copper → 9 V buck subsea |
| Language | VHDL only |

---

## Shipping firmware configuration

Compile-time constants in `rtl/top_system.vhd`, as committed. Every one is
documented in place with its reasoning — this table is the index, not the
explanation.

| Constant | Value | Effect |
|----------|-------|--------|
| `C_NODE` | `1` | Board identity. Drives MAC, IP and UDP port together. `build_all.sh` sweeps it 1–4 |
| `C_DECIMATE` | **`true`** | 96 → 24 kHz decimator in the signal path. Wire format unchanged; only the rate |
| `C_ENABLE_48V` | **`true`** | Permits 48 V phantom. Still gated on the staged power-up timer *and* the host's runtime flag |
| `C_PHANTOM_WATCHDOG` | `false` | Off on purpose — enabling it makes a host keepalive mandatory. See below |
| `C_PHANTOM_TIMEOUT_S` | `120` | Watchdog period, if ever enabled |
| `C_I2C_SWAP` | `true` | Compensates a **schematic error** — net `SCL` lands on ADAU pin 17, which is SDA. Do not "fix" without fixing the copper |
| `C_LRCLK_RETIME` | `false` | LRCLK phase-shift path built but out of the signal path — the fault it chased was hardware |
| `C_LRCLK_PHASE_PS` | `25431` | Mirror of the PLL's `clk3_phase_shift`. **Does not set the phase** — the MegaWizard does |
| `C_BUFFER_EN_ACTIVE_HIGH` | `true` | LMK1C1104 `1G` polarity, confirmed against the datasheet |
| `C_LRCLK_TEST_50PCT` | `false` | Diagnostic: drives LRCLK as a slow square so a DMM can see it |
| `C_BCLK_TEST_SLOW` | `false` | Diagnostic: drives BCLK at ~0.27 Hz so clock-tree levels read as pure DC |
| `C_TDM2_FROM_TDM1` | `false` | Diagnostic, answered 2026-08-10 — PIN_119 and `u_rx_B` are good |

`rtl/adau_sequencer.vhd`

| Constant | Value | Effect |
|----------|-------|--------|
| `C_SOFT_RESET_FIRST` | `true` | S_RST before configuring, so the FSM initialises with clocks already stable |
| `C_VERIFY_IDX` | `0` | Which ADC the register verify reads back (0=U19, 1=U20, 2=U37, 3=U38). One part per boot |

`rtl/tdm8_rx.vhd` / `rtl/tdm16_rx.vhd`

| Constant | Value | Effect |
|----------|-------|--------|
| `C_BIT_ADJ` | `-1` | Capture-window offset in BCLK. **Found by measurement** (`udp_monitor.py --align`), not derived. Keep both files equal |
| `C_RAW_CAPTURE` | `false` | Ships raw TDM bits instead of audio, for `rawview.py` |

### The phantom-power watchdog

`C_PHANTOM_WATCHDOG` is a fail-safe, not a convention. The host is supposed to
turn 48 V off when it shuts down, which covers an orderly restart and nothing
else — if the app crashes, the cable is pulled, or the PC loses power, the
enable flag stays set inside the FPGA and 48 V stays live on the XLRs.

It is **off by default** because turning it on makes a host keepalive
mandatory: any host that sets phantom and then goes quiet sees 48 V drop
mid-capture, which during a real deployment is worse than the hazard it
prevents. Enable it only once the host actually sends keepalives, and flash all
four boards together. Details: [docs/PHANTOM_POWER.md](docs/PHANTOM_POWER.md).

---

## Building

```bash
./build_all.sh      # 8 images: 4 nodes x {24K decimating, 96K plain}
```

The script rewrites `C_NODE` and `C_DECIMATE` in `top_system.vhd`, compiles,
converts to `.jic`, and reports LE count and TNS per build. It takes a lock:
two concurrent runs corrupt each other, because both edit the same source file
and both write `output_files/TDM_UATR.sof` — which would produce an image
labelled for one board carrying another board's IP, the exact failure the
filename convention exists to prevent.

Images are named `{rate}_NODE{n}_{ip}.jic` so a board can never be flashed with
the wrong identity by accident.

> **A `.sof` is volatile.** Power-cycling boots the `.jic` in flash instead —
> usually an older build. Power-sequencing changes cannot be tested with a
> `.sof` at all.

---

## Clock and framing

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

### 24-BCLK slots do not work on this part

`SLOT_WIDTH=01` (24 BCLK) is listed as legal in Table 21, and at 96 kHz it gives
exactly 18.432 MHz — which is what the board was originally designed around.
**The ADAU1978 refuses it.** Correctly configured, PLL locked, every register
reading back byte-exact, and SDATAOUT never driven.

This is not documented anywhere in the datasheet. It was found by putting one
part into **master mode** (`SAI_MS=1`, with its BCLK and LRCLK resistors lifted
so it wasn't fighting the FPGA): given free rein, the part generated **32-BCLK
slots** and drove data immediately. Switching the FPGA to match fixed it.

Contributing reasons it cannot work:

- 24-bit data in a 24-BCLK slot leaves **no room** for the I²S one-BCLK delay,
  so `SDATA_FMT` must be left-justified (`01`) rather than I²S (`00`).
- Even with left-justified framing it still refuses. The slot width itself is
  the problem.

192 × fS was retested on hardware on 2026-08-11 and rejected again. 256 × fS
stands.

### The final numbers

```
PLL c2       = 50 MHz x 1536/3125 = 24.576000 MHz   exact
frame        = 8 slots x 32 BCLK  = 256 BCLK
fS           = 24.576 MHz / 256   = 96000.0 Hz
MCS=011      = 256 x fS           = 24.576 MHz      matches MCLK
data         = 24 bit, left-justified, 8 pad bits per slot
LRCLK        = 1 BCLK wide pulse, 40.7 ns, once per 10.42 us
```

`tdm8_rx.vhd` shifts 256 bits per frame and takes the **top 24 of every 32**,
discarding the pad bits.

### PLL configuration

Single ALTPLL instance (`ip/pll_audio`), all outputs exact from 50 MHz
(3125 = 5⁵ divides cleanly, so there is no rounding anywhere):

| Output | Ratio | Frequency | Gives |
|--------|-------|-----------|-------|
| c0 | 768/3125 | 12.288 MHz | 48 kHz — **do not use**, kills U37/U38 |
| c1 | 1152/3125 | 18.432 MHz | 72 kHz — working fallback |
| **c2** | **1536/3125** | **24.576 MHz** | **96 kHz — shipping** |
| c3 | — | phase-shifted LRCLK | unused (`C_LRCLK_RETIME = false`) |

Changing the rate also means changing MCS (`0x01`) and FS (`0x05`) to match.

The Ethernet side is independent: `rmii_ref_clk` comes from the PHY at 50 MHz
and the two domains meet only through `async_fifo`, which the SDC declares
asynchronous. Lowering the audio rate reduces FIFO load, never increases it.

---

## Decimation and throughput

Two builds exist from the same source, differing only in `C_DECIMATE`.

**The packet never changes size — only how often one is sent.** Every packet
carries exactly 8 audio frames at either rate:

```
                          24 kHz (24K_*)   96 kHz (96K_*)
packets per second            3,000           12,000
bytes on the wire               476              476
```

Per board:

```
payload  16 ch x 24 bit x fs         9.216 Mbit/s    36.864 Mbit/s
+ 10 B packet header                 9.840           39.360
+ eth/IP/UDP + preamble/FCS/IFG     11.424          45.696     <- on the wire
of 100BASE-TX                         11.4%           45.7%
disk  16 x fs x 3 B                  1.15 MB/s        4.6 MB/s
                                      4.1 GB/hour    16.6 GB/hour
```

Four boards:

```
aggregate                           45.696 Mbit/s  182.784 Mbit/s
                                  fits 100BASE-TX  needs GIGABIT
```

The wire figure exceeds the audio because 66 bytes of framing ride on every
packet — 410 B payload inside 476 B on the link, 86% efficiency:

```
410 B payload + 8 UDP + 20 IPv4 + 14 Ethernet = 452 B frame body
      + 4 B FCS                               = 456 B transmitted
      + 8 B preamble/SFD + 12 B inter-frame gap = 476 B of link time
```

Because that overhead is **per packet**, sending 4× fewer packets saves it 4×
over too, so the wire rate scales by exactly 4.00.

### The filter

Two cascaded halfband FIR stages, 96k → 48k → 24k. Halfband because every even
tap except the centre is exactly zero (halves the multiplies), and linear phase
because the coefficients are symmetric (halves them again).

| | Stage 1 | Stage 2 |
|---|---|---|
| Length | 27 taps | 171 taps |
| Non-zero taps | 15 | 87 |
| Rate | 96k → 48k | 48k → 24k |

20-bit coefficients, 24-bit data, 45-bit accumulator. Measured on the quantised
cascade by `python/design_decimator.py`:

```
passband ripple 0-11 kHz   0.00015 dB
worst alias band          -102.5   dB   (below the ADC's 103 dB range)
group delay                 1.91   ms
```

**Why not a CIC**, which was the original brief: the band of interest is
10 Hz – 11 kHz, which is 92% of the 12 kHz Nyquist after a ÷4 — a brick-wall
requirement. A CIC N=3 droops **−9.2 dB** at 11 kHz and puts a 13 kHz folding
tone only 4.1 dB below the signal. Raising the order makes it *worse*, because
the first null is pinned at 24 kHz. Full reasoning:
[docs/DECIMATOR_FINDINGS.md](docs/DECIMATOR_FINDINGS.md).

**Which image to use:** `24K_*` unless you need content above 11 kHz. Inside
that band it costs nothing measurable and it removes the gigabit requirement,
cuts host CPU 4× and quarters the disk rate. `96K_*` for the full 0–42 kHz the
ADC passes, or as the fallback with the longer hardware history.

> The payload is **byte-identical** at both rates and nothing in the packet
> announces which it is, so a mismatch is **silent**: WAVs play at the wrong
> pitch and every duration is out by 4×. `discover.py` measures the rate from
> the packet rate rather than assuming it; `check_sync.py` asserts the host
> constant against the RTL.

---

## Network and packet format

### Addressing (static — no DHCP)

Everything derives from `C_NODE` in `top_system.vhd`:

```vhdl
FPGA_MAC  : x"DEADBEEF00" & C_NODE      -- DE:AD:BE:EF:00:0n
FPGA_IP   : 192.168.3.(100 + C_NODE)    -- .101 .102 .103 .104
PC_IP     : 192.168.3.10                -- C_PC_IP
UDP_PORT  : 5004 + C_NODE               -- 5005 5006 5007 5008
```

`C_PC_IP` is load-bearing twice over: it is the audio destination *and* the
filter deciding whose ARP the board will learn from. Changing only the board
addresses gives four boards transmitting into nothing.

**One port per board, deliberately.** Every host tool calls `recv()`, which
discards the sender, so four boards on one port would merge four independent
sequence-number streams into one socket. And on Windows two sockets may both
bind the same UDP port with `SO_REUSEADDR` while only **one** receives.

`C_PC_MAC` is a reset default, not a fixed value — it is overwritten by
whatever ARPs the board from `C_PC_IP`. So the deployment PC works from the
first packet with no ARP round trip, and moving the array to a different host
needs no reflash, just one packet in the board's direction.

> ⚠ **The host must hold BOTH `192.168.3.10` and `192.168.1.10`** while boards
> of either generation are in use. `C_PC_IP` is one value per image, so the host
> is the side that carries both. A board on the wrong subnet does not error —
> it transmits perfectly and the host kernel discards every frame before any
> socket sees it. See [docs/HOST_SETUP.md](docs/HOST_SETUP.md) and
> [docs/CHANGING_IP.md](docs/CHANGING_IP.md).

### UDP payload — 410 bytes

Produced by `packet_formatter.vhd`. `udp_monitor.py` is the single host-side
definition of this geometry; the other tools import it.

```
Bytes  0– 3   Magic  AD A1 97 78
Bytes  4– 7   Sequence number (uint32, big-endian)
Byte      8   dbg_byte0 — SDATA_A edge count per window
Byte      9   dbg_byte1 — SDATA_B edge count per window

then 8 frames of 50 bytes each:
  Byte  0     diagnostic status byte  (frame 0 -> dbg_status,
                                       frame 1 -> dbg_status2, ... frame 7 -> dbg_status8)
  Byte  1     frame index, 0-7
  Bytes 2–49  16 channels x 24-bit signed big-endian, channel 1 first

Total payload   10 + (8 x 50)                    = 410 bytes
IPv4 total len  20 IP + 8 UDP + 410              = 438
Ethernet frame  14 + 438 + 4 FCS                 = 456 bytes transmitted
```

> **Bytes 8–9 are not a frame count.** They once carried a constant `0x0008`
> that nothing read, then ADC register readbacks that were static after boot
> and covered one part only. They now carry the raw SDATA edge counters, which
> are live and cover both TDM lines. Likewise each frame's byte 0 was the
> frame-index MSB, always zero because the index never exceeds 7; it now
> carries the I²C and power status bits.

**Byte 60** — frame 1's byte 0, `dbg_status2` — is the phantom-power readback,
at a fixed offset in every packet:

| bit | mask | meaning |
|-----|------|---------|
| 7 | `0x80` | marker — byte is populated. Clear = older bitstream, ignore the rest |
| 6 | `0x40` | `en_48v` as actually driven on the pin |
| 5 | `0x20` | the host asked for it (`udp_flags` bit 0) |
| 4 | `0x10` | staged power-up passed 1000 ms |
| 3 | `0x08` | this build permits it (`C_ENABLE_48V`) |
| 2:0 | | I²C self-test, unrelated |

`EN_48V` is an FPGA **output**. There is no sense line back from the 48 V
supply — a dead DC-DC, a blown fuse or an open enable trace still reads as ON.
Do not treat it as a rail measurement.

### Control protocol (host → FPGA)

`udp_rx_core.vhd` accepts a plain UDP datagram addressed to the board's IP.
**There is no port filtering** — any port works.

| Payload byte | Meaning |
|---|---|
| `[0]` | bits [3:2] ADC select 0–3, bits [1:0] channel select 0–3 |
| `[1]` | gain byte → register `0x0A`–`0x0D` of the selected part |
| `[2]` | *optional* control flags. **bit 0 = 48 V phantom enable** |

Gain encoding (Table 25): `0x00` = +60 dB, −0.375 dB per step, `0xA0` = 0 dB,
`0xFE` = −35.625 dB, `0xFF` = mute.

> **There is no flags-only packet.** The FPGA parses one command format, so
> every gain write also says something about phantom power. Whatever your app
> attaches to routine gain commands *is* what phantom power becomes — attach
> the board's own readback, not a default. `mixer_gui.py` does this in
> `flags()`, so a fader move is phantom-neutral.

```
python python/ctrl.py --test --channel 3     prove the receive path
python python/ctrl.py --set 3 -6             one channel to -6 dB
python python/ctrl.py --all 0                every channel to 0 dB
python python/ctrl.py --phantom status       decode byte 60
python python/mixer_gui.py                   live meters + faders + phantom
```

✅ **Verified on hardware 2026-08-09.** `ctrl.py --test --channel 1`: baseline
RMS 373 → mute 0.0 → restore 466. The FPGA parsed a UDP datagram from the PC
and wrote the gain register over I²C. Ethernet is proven in both directions.

---

## ADAU1978 configuration

### Register settings

Written by `adau_sequencer.vhd`. Every field is checked against the datasheet
by `check_sync.py` on each build.

| Reg | Value | Description |
|-----|-------|-------------|
| 0x01 | `0x03` | PLL_MUTE=0, CLK_S=0 (MCLKIN), **MCS=011 = 256 × fS** (Table 9, fS=96 row) |
| 0x04 | `0x3F` | LR_POL=0, BCLKEDGE=0 (data on falling BCLK), LDO+VREF+all 4 ADCs enabled |
| 0x05 | `0x5B` | SDATA_FMT=01 (**left justified**), SAI=011 (TDM8), FS=011 (64–96 kHz) |
| 0x06 | `0x08` | SLOT_WIDTH=00 (**32 BCLK/slot**), DATA_WIDTH=0 (24 b), LR_MODE=1 (pulse), SAI_MS=0 (slave) |
| 0x07 | `0x10` | Chips 0, 2: ch1→slot1, ch2→slot2 |
| 0x07 | `0x54` | Chips 1, 3: ch1→slot5, ch2→slot6 |
| 0x08 | `0x32` | Chips 0, 2: ch3→slot3, ch4→slot4 |
| 0x08 | `0x76` | Chips 1, 3: ch3→slot7, ch4→slot8 |
| 0x09 | `0xF8` | All 4 ch drive enabled, DRV_HIZ=1 (unused slots high-Z) |
| 0x00 | `0x01` | PWUP=1 — **write last, only after PLL_LOCK bit = 1** |

### I²C addresses

| Chip | ADDR1 | ADDR0 | Address |
|------|-------|-------|---------|
| 0 (U19) | 0 | 0 | 0x11 |
| 1 (U20) | 0 | 1 | 0x31 |
| 2 (U37) | 1 | 0 | 0x51 |
| 3 (U38) | 1 | 1 | 0x71 |

### Power-up sequence

```
1. Apply 3.3V AVDD. Hold PD/RST LOW.
2. Assert PD/RST HIGH -> internal LDO charges DVDD.
3. Wait ~5 ms (DVDD > 1.2V, POR releases, safe margin).
4. Apply stable 24.576 MHz MCLK (FPGA must be running).
5. Wait 15 ms for PLL to lock.
6. Poll register 0x01 bit 7 (PLL_LOCK) until = 1.
7. Write registers: 0x04, 0x05, 0x06, 0x07, 0x08, 0x09.
8. Settle 30 ms, then write register 0x00 = 0x01 (PWUP). LAST.
```

Boot is two-pass: configure everything, settle, then PWUP. The datasheet
requires PWUP be asserted ≥10 ms after DVDD > 1.2 V with stable clocks.

### Per-chip hardware requirements

- **PLL_FILT (pin 3):** 1 kΩ + 5.6 nF + 390 pF — mandatory
- **VREF (pin 2):** 100 nF + 10 µF to GND
- **DVDD (pin 10):** 100 nF + 10 µF MLCC X7R to GND
- **AVDD1/2/3:** 100 nF + 10 µF bulk per pin
- **Exposed pad (EP):** must be soldered to the PCB ground plane
- **IOVDD:** match to FPGA IO bank voltage (3.3 V)
- **47 kΩ pull-down** on each SDATAOUT line to GND

---

## Hardware details

### ADAU1978 chip pairing and slot assignment

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
sdata_in_A          Chip 0 SDATAOUT1 + Chip 1 SDATAOUT1  (47 kΩ pull-down)
sdata_in_B          Chip 2 SDATAOUT1 + Chip 3 SDATAOUT1  (47 kΩ pull-down)
```

### TDM frame structure

```
LRCLK:   |‾|__________________________________|‾|__
          1 BCLK wide pulse — marks start of slot 1

BCLK:    256 cycles per frame  (8 slots × 32 BCLK, 24-bit data + 8 pad bits)

sdata_in_A:
[Chip0 ch1:24b][Chip0 ch2:24b][Chip0 ch3:24b][Chip0 ch4:24b]  slots 1–4
[Chip1 ch1:24b][Chip1 ch2:24b][Chip1 ch3:24b][Chip1 ch4:24b]  slots 5–8

sdata_in_B: identical structure for Chips 2 and 3
```

- ADAU1978 outputs data on the **falling BCLK edge** (max 18 ns delay)
- FPGA samples on the **rising BCLK edge**
- LRCLK is *sampled* on the BCLK **rising** edge regardless of BCLKEDGE, so
  `tdm8_master` must **launch** it on the falling edge — asserted by `check_sync.py`
- Left-justified: first audio bit valid on the BCLK cycle after the LRCLK pulse

### Receiver output layout (per instance)

```
ch_data[191:168]  ch 1    ch_data[95:72]   ch 5
ch_data[167:144]  ch 2    ch_data[71:48]   ch 6
ch_data[143:120]  ch 3    ch_data[47:24]   ch 7
ch_data[119:96]   ch 4    ch_data[23:0]    ch 8
```

### LAN8720A module wiring

| Module Pin | Signal | Direction | Notes |
|------------|--------|-----------|-------|
| VCC / GND | 3.3 V | — | Module power |
| RST# | `rmii_rst_n` | FPGA → PHY | Assert LOW at startup, release HIGH |
| MDC | `rmii_mdc` | FPGA → PHY | ~2.5 MHz management clock |
| MDIO | `rmii_mdio` | Bidirectional | 10 kΩ pull-up to 3.3 V |
| REF_CLK | `rmii_ref_clk` | PHY → FPGA | 50 MHz — see note |
| TXD0/TXD1 | `rmii_txd[1:0]` | FPGA → PHY | |
| TX_EN | `rmii_tx_en` | FPGA → PHY | |
| RXD0/RXD1 | `rmii_rxd[1:0]` | PHY → FPGA | Required — the control path uses them |
| CRS_DV | `rmii_crs_dv` | PHY → FPGA | |

> **REF_CLK note:** these modules carry an onboard 50 MHz crystal, and that is
> the clock the RMII domain runs on here. Check your specific module before
> wiring.

### Subsea cable and fiber link

| Parameter | Value |
|-----------|-------|
| Cable type | Hybrid power + fiber, HDPE marine grade + aramid yarn |
| Conductors | 2× 2.5 mm² XLPE copper |
| Fiber count | 8× singlemode in stainless steel loose tube |
| Fiber used for data | 1 (BiDi WDM — single fiber, full duplex) |
| Cable OD | 18 mm ±0.5 mm |
| MBL | 1500 kg, working load 500 kg |
| Link budget at 7 km | ~3.45 dB loss, ~15 dB margin |

> **BiDi pair requirement:** the two converters must be a matched pair — one TX
> at 1310 nm, the other TX at 1550 nm. Verify before deployment.

### Subsea power delivery

```
2.5 mm² copper, 7 km round trip resistance = ~96.3 Ω
At 100 mA load: voltage drop = 9.63 V

Supply 24 V topside -> ~14.4 V arrives at the subsea end
Subsea: 9 V buck regulator (e.g. LM2596) powers the media converter
```

---

## Architecture decisions

**2× TDM8 rather than TDM16 or 4× TDM4.** TDM8 needs only two data wires and
gives symmetric 8-channel receivers. 4× TDM4 works and has the lowest BCLK but
wastes four input pins. TDM16 on one wire was built and tested
(`output_files/96K_TDM16.jic`) and **reverted**: timing analysis showed the
capture path was never the fault, so merging all four parts onto one net would
only have traded 24-bit samples for 16-bit. The procedure is kept in
[docs/TDM16_BRINGUP.md](docs/TDM16_BRINGUP.md) in case it is revisited.

**LAN8720A rather than W5100/W5500.** W5100 is SPI-based at max ~0.44 MB/s —
10× below what is needed. W5500 at ~10 MB/s is adequate but adds SPI overhead
and latency. LAN8720A speaks RMII directly to fabric with no intermediate
bottleneck.

**100 Mbps rather than gigabit.** With the decimator, one board offers
11.4 Mbit/s and the whole four-board array 45.7 Mbit/s — comfortably inside
100BASE-TX. Gigabit would require RGMII: more pins, harder timing, no benefit.

**UDP rather than TCP.** Audio is loss-tolerant and latency-sensitive. TCP
retransmits cause variable delay; a dropped UDP packet is one frame of missing
audio that the host detects from the sequence number.

**Fiber rather than copper at 7 km.** 100BASE-TX reaches 100 m. The subsea
cable already carries singlemode fiber and the converters are rated to 20 km.

**BiDi WDM rather than dual fiber.** TX and RX share one fiber at different
wavelengths, consuming one core of eight and leaving seven spare.

**GZIP compression in the FPGA was evaluated and rejected** — see
[HOST_DSP_PIPELINE.md](HOST_DSP_PIPELINE.md).

---

## Multi-board deployment and host DSP

The deployed array is **4 boards = 64 channels**, beamformed on a single host.
With the decimating build that is 45.7 Mbit/s aggregate and 12,000 pkt/s, which
fits 100BASE-TX; the 96 kHz build's 182.9 Mbit/s does not.

Host-side handling of the aggregate is specified in
**[HOST_DSP_PIPELINE.md](HOST_DSP_PIPELINE.md)**, including the
FLAC storage path and the **inter-board sample-alignment problem, which remains
open** — the four boards free-run from their own oscillators and nothing
currently disciplines them to a common timebase. `discover.py` flags mixed
sample rates for the same reason: each board is fine on its own and they are
not aligned to each other.

---

## Repository layout

```
rtl/        Synthesizable VHDL — everything in TDM_UATR.qsf's VHDL_FILE list
ip/         ALTPLL / FIFO IP cores, one directory per .qip (self-contained)
sim/        Testbenches, modelsim.ini, wave.do, decimator reference vectors
python/     Host-side tools (Python 3)
hardware/   Schematic PDF and KiCad netlist export
docs/       Findings and procedures, referenced from this README
db/, incremental_db/, output_files/   Quartus build output — gitignored
```

`TDM_UATR.qpf` / `.qsf` / `.sdc` stay at the repository root so the project
opens in Quartus by double-clicking the `.qpf`. Every source reference is a path
relative to the project root — no fixed drive letters.

### RTL

| File | Description |
|------|-------------|
| `top_system.vhd` | Top level. Clock/reset, staged power-up, I²C open-drain buffers, TX arbiter, all build-option constants |
| `tdm8_master.vhd` | Generates LRCLK (1 BCLK pulse @ 96 kHz) from 24.576 MHz |
| `tdm8_rx.vhd` | TDM8 receiver — 264-bit shift register (256-BCLK frame + `C_BIT_ADJ` slack), latch on LRCLK. Instantiated twice |
| `tdm16_merge.vhd` | Merges the two TDM8 streams into 16 channels |
| `tdm16_rx.vhd` | Single-net 16-slot receiver, built for the TDM16 experiment — not in the active path |
| `decimator.vhd` | Two-stage halfband FIR, 96 → 24 kHz, 16 channels time-multiplexed |
| `decim_coef_pkg.vhd` | Generated coefficients and tap indices — regenerate with `design_decimator.py` |
| `i2c_master.vhd` | I²C master. Bus recovery, probe mode, repeated-START reads |
| `adau_sequencer.vhd` | 128-address scan, soft reset, register boot, two-pass PWUP, live PLL poll, runtime gain writes |
| `crc32.vhd` | Ethernet FCS (0x04C11DB7) |
| `rmii_tx.vhd` / `rmii_rx.vhd` | RMII MAC — preamble, data, FCS, IFG |
| `udp_tx_core.vhd` | Ethernet + IP + UDP headers, 452-byte frame body |
| `udp_rx_core.vhd` | UDP receive path — gain and flags control |
| `arp_responder.vhd` | ARP replies, and learns the host MAC |
| `packet_formatter.vhd` | 10-byte header + 8 × 50-byte frames = 410-byte payload |
| `net_pkg.vhd` | Shared network constants |
| `ip/pll_audio` | ALTPLL: 50 MHz → 24.576 MHz |
| `ip/async_fifo` | Clock-domain crossing, 24.576 MHz → 50 MHz |

### Host tools (`python/`)

**Audio**

| File | Description |
|------|-------------|
| `discover.py` | **Start here.** Passive — finds every board, reports its real subnet, measured rate, and loss. Transmits nothing |
| `udp_monitor.py` | One-shot capture: link rate, loss, per-channel statistics, `--wav`, `--align`. The single definition of the packet geometry |
| `mixer_gui.py` | **Live tkinter mixer** — 16 meters, gain faders, mute, 48 V, telemetry tab, follows each board's real address |
| `mixer_gui_standalone.py` | The whole GUI in one file. **Generated — do not edit** |
| `make_gui_standalone.py` | Generates the above with `ast`. `--check` fails if it is stale |
| `mixer.py` | The same meters in the terminal |
| `ctrl.py` | Control protocol, phantom decode, and `--test` |
| `timeline.py` | Reports channel dropout windows over a capture |
| `rawview.py` | Decodes `tdm8_rx`'s raw-capture debug mode, bit for bit |

**Verification**

| File | Description |
|------|-------------|
| `check_sync.py` | Cross-checks the host constants against the RTL **and** the datasheet tables. 58 assertions — run on every build |
| `design_decimator.py` | Designs the filter, generates `decim_coef_pkg.vhd` and `sim/decim_ref_vectors.txt`, and reports ripple and alias rejection |
| `sim_chain.py` | Cycle-accurate model of the TDM chain, used to settle `C_BIT_ADJ` without a licensed simulator |
| `i2c_scan.py` | Decodes the boot-time I²C diagnostics: bus health, 128-address sweep, per-part table, register verify |

**Buoy telemetry**

| File | Description |
|------|-------------|
| `gdat2.py` | `$GDAT2` serial telemetry — see [docs/GDAT2_TELEMETRY.md](docs/GDAT2_TELEMETRY.md) |
| `witmotion.py` | WitMotion IMU/AHRS client |
| `ping1d.py` | Ping1D altimeter client |
| `altimeter_probe.py` | Altimeter bring-up probe |
| `imu_test.py` | Proves the AHRS is *live*, not merely present — catches an unchanging-constant or all-zero field map |
| `imu_standalone.py` | The same check as one self-contained stdlib file |
| `test_RMI.py` | Buoy integration test |

### Testbenches (`sim/`, not in the synthesis hierarchy)

| File | Description |
|------|-------------|
| `tb_tdm8_rx.vhd` | Known pattern, frame assertions |
| `tb_tdm16.vhd` | 16-channel merge |
| `tb_chain.vhd` | Full chain |
| `decim_ref_vectors.txt` | Bit-exact decimator reference output |

```
vlib work
vcom -modelsimini sim/modelsim.ini -work work -2002 rtl/tdm8_master.vhd rtl/tdm8_rx.vhd rtl/tdm16_merge.vhd sim/tb_tdm16.vhd
vsim -modelsimini sim/modelsim.ini -do sim/wave.do work.tb_tdm16
```

`-modelsimini sim/modelsim.ini` points at the tracked library mapping —
ModelSim otherwise resolves `modelsim.ini` from the current directory and
silently falls back to the install default.

![ModelSim TDM16 waveform](docs/modelsim_tdm16.png)

### Documentation (`docs/`)

**Procedures**

| File | Description |
|------|-------------|
| `HOST_SETUP.md` | **The complete host procedure** — adapter, firewall, which `.jic` to flash, verifying audio and telemetry |
| `DECIMATION.md` | The 96→24 kHz decimator, and the ADC gain budget that goes with it |
| `CHANGING_IP.md` | Changing the array's addressing — the four things that must agree |
| `NETWORK_SETUP.md` | Why the network is arranged this way: capacity, collisions, Python limits |

**Reference**

| File | Description |
|------|-------------|
| `ETHERNET_TRANSMISSION.md` | The UDP/IP/Ethernet transmit path end to end |
| `MULTI_BOARD.md` | Four-board deployment |
| `PHANTOM_POWER.md` | 48 V control, readback and the optional watchdog |
| `TELEMETRY_INTEGRATION.md` | The three buoy sensors and how to lift them into an app |
| `GDAT2_TELEMETRY.md` | `$GDAT2` field map, and the AHRS quantisation trap |

**Findings**

| File | Description |
|------|-------------|
| `DECIMATOR_FINDINGS.md` | Design decisions, and every bug found building the decimator |
| `TDM16_BRINGUP.md` | TDM16 procedure and why it was reverted |
| `LRCLK_HOLD_VIOLATION.md` | The ~4 ns LRCLK hold-spec violation |
| `LRCLK_PHASE_SHIFT.md` | The phase-shift investigation — intact but out of the signal path |
| `TDM2_NETLIST_FINDINGS.md` | Netlist trace of the LMK1C1104 buffer fan-out |

---

## Hardware bring-up log

Findings from bringing up the Souncard_Robomarine 1.0 PCB. Recorded because
none of it is derivable from the RTL. **All are resolved**; they are kept
because the next board revision needs them.

### Schematic errors

| Error | Impact | Resolution |
|-------|--------|------------|
| **SDA/SCL crossed** — net `SCL` wires to ADAU pin 17 (really SDA), net `SDA` to pin 18 (really SCL). The KiCad symbol is correct; the wiring is not | I²C could never work as drawn | Compensated in firmware by `C_I2C_SWAP = true`. **Fix the copper in the next revision** |
| **OPA1671 on +15 V** — U44–U47 (VREF→VCOM buffers) have V+ on +15 V against a **6 V absolute maximum** | Destroyed all four. Their damaged inputs clamped VREF to 0–0.8 V on every ADC and loaded the ±15 V rail | **Removed, not replaced.** OPA1632 `VOCM` self-biases to mid-rail, which is correct on ±15 V, and the ADC inputs are AC-coupled — the buffers were never needed. **Delete them in the next revision** |
| **PLL loop filter returns to GND**, not AVDD2 as Table 8 requires | None observed | Disproven as a fault — U19/U37 lock with the GND return. Component values are correct |
| **Both LMK1C1104 clock buffers (U1, U2) damaged** | Their inputs loaded the FPGA's 3.3 V outputs to 2.0 V and their outputs produced 0.9 V and millivolts. The ADAU1978 needs VIH = 0.7 × IOVDD = 2.31 V, so the ADCs never saw a valid clock and left SDATAOUT high-Z | Replaced. Can also be bypassed by bridging pin 1 to pins 3/5/7/8 on each footprint — the FPGA drives these loads directly; the 49.9 Ω series resistors stay |
| **Misplaced DVDD decoupling cap, and a dead U37** | The intermittent ADC3/ADC4 channel dropouts | Fixed in hardware. All 16 channels now run clean |

### Firmware bugs

- **`i2c_master.vhd`** — `ena` was sampled only on quarter-bit boundaries while
  the sequencer pulsed it for one cycle, so the pulse was missed ~99% of the
  time. **No I²C transaction had ever run.**
- **`crc32.vhd`** — 7 of the 32 XOR equations (bits 10, 11, 12, 16, 17, 22, 23)
  carried spurious terms, so every frame left with a garbage FCS and the host
  NIC discarded all of it silently. **Root cause of the original "Ethernet
  dead" fault.** Verified after the fix: `"123456789"` → `0x649C2FD3`, RX
  residue `0xC704DD7B`.
- **False PLL-lock reporting** — `i2c_master` pre-loads `data_rd` with `0xFF`
  to invalidate aborted reads. The live poll took bit 7 of that blindly, so a
  *failed* read reported `PLL_LOCK = 1`. It reported four locked PLLs on a
  board whose MCLK never arrived.
- **TDM framing** — the merge fired 128×/frame, and LRCLK was launched on the
  ADC's own sampling edge.
- **Scan abort** — the address sweep stopped at 9 answers, collapsing "hard
  stuck-low SDA" (128 answers) and "a few glitched bits" (9) onto one number.
  It now always sweeps all 128.
- **Decimator pipeline misalignment** — survived one round of "bit-exact"
  verification because the model encoded the *intent* rather than the written
  VHDL. Caught only by a cycle-accurate model following VHDL signal semantics.

### Measurement traps

- **LRCLK is a 54 ns pulse at 96 kHz** — 0.5% duty, so a *working* LRCLK reads
  **~17 mV** on a multimeter. Use `C_LRCLK_TEST_50PCT`, or a scope.
- **24 MHz on a handheld DMM** reads as a meaningless fraction of a volt.
  MCLK/BCLK cannot be checked with a meter at all. Use `C_BCLK_TEST_SLOW`.
- **Scope frequency counters quantise.** An 18.432 MHz clock (54.25 ns) on a
  100 MSa/s timebase alternates between "20 MHz" and "16.6 MHz". Both readings
  are the same correct clock.
- **Resistance to GND across bulk capacitance is meaningless** — the meter
  charges the cap and the reading climbs. A rail also reads "shorted" on a
  continuity beeper because of the substrate diodes in every IC on it; reverse
  the probes and the asymmetry gives it away.

### Standing lessons

1. **Model what you wrote, not what you meant.**
2. **A passing check may be checking nothing** — two `check_sync.py` guards had
   been green for weeks while matching no text at all.
3. **Cheap in one resource is expensive in another** — padding a RAM depth cost
   zero LEs and broke the fit on memory blocks.
4. **Generated files must be executed, not just generated.**
5. **Never `git checkout` a file mid-session to reset unrelated state.**

---

## Minimal host receiver

```python
import socket, struct

MAGIC = b'\xAD\xA1\x97\x78'
sock  = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", 5005))                 # 5004 + C_NODE
sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 * 1024 * 1024)

prev_seq = None
while True:
    data, _ = sock.recvfrom(65535)
    if len(data) != 410 or data[0:4] != MAGIC:
        continue
    seq = struct.unpack(">I", data[4:8])[0]
    if prev_seq is not None and seq != prev_seq + 1:
        print("WARNING: %d packet(s) dropped" % (seq - prev_seq - 1))
    prev_seq = seq

    phantom_on = bool(data[60] & 0x40) if data[60] & 0x80 else None

    offset = 10
    for f in range(8):                        # 8 frames per packet, both rates
        samples = [int.from_bytes(data[offset+2+i*3 : offset+5+i*3],
                                  'big', signed=True) for i in range(16)]
        offset += 50
        # samples[0..15] = ch1..ch16
```

---

## Constraints

- VHDL only — no Verilog or SystemVerilog
- Cyclone IV E only — no Cyclone V or later features
- `rtl/top_system.vhd` is the only top level
- `rtl/tdm8_rx.vhd` is complete and instantiated twice — do not rewrite
- All FPGA IO pins are 3.3 V — the LAN8720A IOVCC must also be 3.3 V
- UDP checksum is 0x0000 (valid per RFC 768)
- The sample rate is **not** announced in the packet. Any tool that assumes it
  must be told, and `check_sync.py` must be run after flashing a different image

---

## License

MIT — see [LICENSE](LICENSE). Copyright (c) 2026 Faiz Akbar Parinduri, S.T.

This covers the VHDL in `rtl/`, the host tools in `python/`, the testbenches in
`sim/`, and the documentation. It does **not** cover third-party material
redistributed here for convenience:

- `ip/pll_audio` and `ip/async_fifo` are Altera/Intel megafunction output,
  governed by the Quartus Prime license under which they were generated
- `docs/adau1978.pdf` is the Analog Devices datasheet, © Analog Devices
- `hardware/` contains the Souncard_Robomarine 1.0 schematic and netlist

---

*Analog Devices ADAU1978 Rev B. Microchip LAN8720A. Altera Cyclone IV E
EP4CE6E22C8. Built with Quartus Prime 25.1std Lite.*
