# TDM16 bring-up — what to do with the board

Image: `output_files/96K_TDM16.jic`
Fallback: `output_files/96K_LRCLK_FIX.jic` (TDM8, keep this — see "If it goes wrong")

---

## 1. What changed and why it fits

All four ADAU1978s move onto **one** SDATA net and take four slots each out of
sixteen, instead of two nets carrying eight slots each.

| | TDM8 (before) | TDM16 (now) |
|---|---|---|
| slots per frame | 8 | 16 |
| BCLKs per slot | 32 | 16 |
| **BCLKs per frame** | **256** | **256** |
| BCLK | 24.576 MHz | 24.576 MHz |
| data width | 24-bit | **16-bit** |
| SDATA nets used | 2 | 1 |

The frame is the same 256 BCLKs either way, so **BCLK, LRCLK, the PLL and
`tdm8_master` are all unchanged**. That is the whole reason this configuration was
chosen: it is the only TDM16 option that does not raise the clock. Per ADAU1978
Table 10, TDM16 runs at 256/384/512 × fS for 16/24/32-bit slots — 24-bit would
need 384 × fS = 36.864 MHz, which the audio clock domain has no margin for.

**The cost is real: samples are 16-bit, not 24-bit.** That is 8 bits of dynamic
range given up, roughly 48 dB of noise floor. The packet format still carries
24-bit words — each sample is left-justified with a zero low byte — so full scale,
every dBFS reading and every host script stay exactly as they were. The low byte
just always reads zero.

---

## 2. The board change

**Fit one jumper: `R21` pin 1 ↔ `R122` pin 1.**

That joins net `/TDM1` to net `/TDM2`. From the netlist those two nets are:

- `/TDM1` — `R21.1, U19.13, U20.13, U43.10` (FPGA `sdata_in_A`, PIN_32)
- `/TDM2` — `J19.4, J21.4, R122.1, U37.13, U38.13, U43.67` (FPGA `sdata_in_B`, PIN_119)

Pin 1 of each resistor is the signal end, so the two pads are the tidiest place to
bridge. Both FPGA pins then see the same wire; the design reads `sdata_in_A` and
leaves `sdata_in_B` connected but unread, so no QSF or pin change is needed and
removing the jumper later restores the second line immediately.

### The pulldowns: leave both fitted

You asked whether to remove one. **No — leave `R21` and `R122` both in place.**

They are 10 kΩ each. Jumpered together they sit in parallel and become 5 kΩ, which
is still a trivial load for a CMOS output (the ADAU1978 sources milliamps; 3.3 V
across 5 kΩ is 0.66 mA). Their job is to hold the net at a defined level when no
part is driving it, and with four parts sharing one net that job matters *more*
than it did before, not less. Removing one only weakens it.

---

## 3. Why sharing one net is safe — and the one way it isn't

Only one part may drive the net at a time. Two things enforce that:

1. **`DRV_HIZ = 1`** (register 0x09 = 0xF8). The datasheet is explicit: *"1: Unused
   outputs High-Z."* Each part tri-states outside the four slots it owns.
2. **`SAI_CMAP12`/`SAI_CMAP34`** (0x07/0x08) give every part a different four slots:

   | part | addr | slots | 0x07 | 0x08 |
   |---|---|---|---|---|
   | U19 | 0x11 | 1–4 | `0x10` | `0x32` |
   | U20 | 0x31 | 5–8 | `0x54` | `0x76` |
   | U37 | 0x51 | 9–12 | `0x98` | `0xBA` |
   | U38 | 0x71 | 13–16 | `0xDC` | `0xFE` |

**The failure mode to watch for:** both of those depend on the part being
*configured*. This matters here specifically because `/TDM2` has been showing
**zero transitions**, so U37/U38's state is exactly what is not yet established.

Note that `DRV_HIZ`'s **reset default is 0**, not 1 — the datasheet reads *"0:
Unused outputs driven low."* (`i2c_scan.py`'s VERIFY table lists 0x09 reset as
`0xF0`, bit 3 clear.) So a part that powers up but never completes configuration
does **not** sit High-Z; it drives low continuously. Under the jumper that pulls
**all 16 channels to exact zero**, which is a different signature from contention
and easy to misread. This is not new risk: U19 and U20 have shared `/TDM1` through
the same boot window for weeks without damage — it is four parties now instead of
two.

Check the `REGISTER VERIFY` block from `i2c_scan.py` before fitting the jumper. If
U37/U38 verify clean there, they are configured and High-Z, and the jumper is safe.

### What TDM16 can and cannot fix

This is the expectation that matters, and it follows straight from the netlist:

```
/TDM2:  U43.67 -> R122 -> J19.4 ->[cable]-> J21.4 -> U37.13, U38.13
```

The jumper joins `/TDM1` and `/TDM2` **at the FPGA end**. U37/U38's data still has
to cross J19 → cable → J21 to reach the shared net. Therefore:

- **Fault on the FPGA-side `/TDM2` path** (PIN_119, U43.67, that trace) → TDM16
  **recovers** channels 9–16, because their data now arrives via the `/TDM1` trace
  and PIN_32 instead.
- **Fault in the cable, J19/J21, or U37/U38 themselves** → TDM16 changes nothing
  for channels 9–16.

After two cable rebuilds and 0.2 Ω contact measurements, the second is the likelier
of the two. So be clear about what a partial result means: **channels 9–16 still
dead, with byte 9 ≈ byte 8, is a result, not a failure.** It rules out the entire
FPGA-side path and localizes the fault to cable-or-daughterboard — which is more
than three weeks of swapping has produced.

---

## 4. Order of operations

1. Flash `96K_TDM16.jic`.
2. **Before fitting the jumper**, run `python i2c_scan.py`. All four parts should
   verify 0x05 = `0x63` and 0x06 = `0x58`. This confirms the new mode took, and
   confirms U37/U38 are configured (hence High-Z) before you bridge the nets.
3. Fit the jumper `R21.1 ↔ R122.1`.
4. Run `python udp_monitor.py` and read the **SDATA LINE LIVENESS** section first
   (see below), then `python timeline.py` for the per-channel picture.

### Read byte 9 first — it is a direct continuity test on the jumper

Header bytes 8 and 9 carry the raw SDATA edge counters for line A and line B
(`sdata_in_A` on PIN_32, `sdata_in_B` on PIN_119). They count pin transitions
*before* any decoding, so they are independent of alignment, CMAP and slot width.

Line B currently reads **0 across an entire capture**. Once the jumper is fitted,
both FPGA pins are on the same wire, so **byte 9 must jump to roughly byte 8
(~255)**. That single number separates failures that would otherwise look alike:

| byte 9 | ch 1–8 | ch 9–16 | meaning |
|---|---|---|---|
| still 0 | alive | dead | **the jumper is not conducting.** Resolder it. Nothing else is diagnostic yet. |
| ≈ byte 8 | alive | alive | **success.** |
| ≈ byte 8 | alive | dead | jumper good; fault is *not* on the FPGA-side net — see section 3. |
| ≈ byte 8 | **dead** | dead | contention on the shared net. **Jumper off.** |
| ≈ byte 8 | all 16 exact zero | | an unconfigured part is driving low (`DRV_HIZ` = 0 at reset). Check `i2c_scan.py` REGISTER VERIFY. |

Do not skip to the channel table — a dead jumper and a dead daughterboard look
identical there, and byte 9 is the only thing that tells them apart.

---

## 5. If it goes wrong

This image carries three changes at once, so if it misbehaves, separate them in
this order:

1. **Channels 1–8 died when the jumper went on** → contention. Jumper off. This is
   a board/configuration question, not a firmware one.
2. **All channels read as noise, or "misaligned?"** → bit alignment. `C_BIT_ADJ`
   in `tdm16_rx.vhd` is currently `-1`, which is a *prediction* following the LRCLK
   launch-edge fix, not a measured value. Set it back to `0`, rebuild. This is the
   single most likely thing to need adjusting.
3. **Channels appear rotated** (ch 5 carries ch 1's signal, etc.) → `C_CAP_EXTRA`
   off by a whole slot, or a CMAP value wrong. Check the table in section 3.
4. **Channels 9–16 still dead, byte 9 healthy** → not a failure of this build; see
   section 3. Keep the jumper on, keep the image, and move the investigation to the
   cable and daughterboard. The FPGA-side path is now excluded.
5. **Nothing works at all** → flash `96K_LRCLK_FIX.jic` and remove the jumper. That
   is the last image known to give eight good channels.

Also note this is the **first image ever run** with the LRCLK falling-edge launch
fix (see `LRCLK_HOLD_VIOLATION.md`). Hold slack against the ADAU1978's 5 ns tALH
went from −3.853 ns to **+17.077 ns** worst corner. It is the right fix on paper
and has never been on hardware.

---

## 6. Going back to TDM8

No files need reverting — both receivers stay in the project and both are still
compiled in. The switch is:

- `top_system.vhd` — swap the `u_rx : tdm16_rx` instance for the two commented
  `tdm8_rx` instances directly beneath it.
- `adau_sequencer.vhd` — four values, listed in the `REVERTING THIS FILE TO TDM8`
  comment block next to `CMAP12_BY_IDX`.
- Remove the jumper.
- Run `python check_sync.py`. It reads the TDM mode out of the boot ROM and out of
  whichever receiver `top_system` instantiates, so it re-checks itself against the
  new mode automatically and will name anything left inconsistent.

The host scripts (`udp_monitor.py`, `timeline.py`, `i2c_scan.py`) need no changes
in either direction — the wire format is 16 channels × 24-bit big-endian either
way. The only mode-dependent value in them is `i2c_scan.py`'s `VERIFY` table for
0x05/0x06, and `check_sync.py` cross-checks that against the boot ROM, so it cannot
drift silently.
