# LRCLK violated the ADAU1978's hold spec by ~4 ns

Written 2026-08-16, after the twisted-pair cable and the connector swap changed nothing
and U20 remained the only part at 0 % dropouts.

Companion to `TDM2_NETLIST_FINDINGS.md`. That document reads the symptom pattern as
pointing at U1, the LRCLK fan-out buffer. **This does not replace it - the two compose.**
The finding below is that the LRCLK the FPGA hands to U1 was already unusable by
datasheet, and that which parts survived it was then decided by U1 output delay and trace
length. Same evidence, one layer further back.

## The measurement

Table 5, page 5 of the ADAU1978 datasheet, ADC SERIAL PORT, verbatim:

| parameter | limit | description |
|---|---|---|
| tALS  | 10 ns min | LRCLK setup to BCLK **rising**, slave mode |
| tALH  | 5 ns min  | LRCLK hold from BCLK **rising**, slave mode |
| tABDD | 18 ns max | SDATAOUTx delay from BCLK **falling** |

Two different reference edges, and both are correct. The part **samples LRCLK on the
rising edge** and **launches SDATAOUT from the falling edge**. BCLKEDGE (0x04 bit 6) moves
the output launch edge - the one tABDD measures - and does not move the LRCLK input
sampling edge.

`tdm8_master.vhd` launched LRCLK on the **rising** edge of BCLK, from commit `927aac7`
until this change, on the reading that BCLKEDGE=0 made the falling edge the part's active
edge for everything. Under the correct reading that put the LRCLK transition **on the very
edge that samples it**.

From `output_files/TDM_UATR.sta.rpt`, the `lrclk_out` rows, as
`Data Delay - Clock Skew` - how much later LRCLK leaves its pad than BCLK leaves its:

| corner | data delay | clock skew | LRCLK after BCLK | tALH slack |
|---|---|---|---|---|
| Slow 1200mV 85C | 4.161 | 2.904 | **1.257 ns** | -3.853 |
| Slow 1200mV 0C  | 3.717 | 2.631 | **1.086 ns** | -4.024 |
| Fast 1200mV 0C  | 2.166 | 1.559 | **0.607 ns** | -4.503 |

Required: 5 ns. The pad-to-pad numbers need no sign convention and are read straight off
the report.

### The constraint was hiding it

`TDM_UATR.sdc` had `set_output_delay -clock bclk_pin -min 5.0`, with a comment reasoning
that a hold requirement means a positive `-min`. It is the opposite. `set_output_delay`
states delay *external* to the port and TimeQuest subtracts it in both checks:

```
required(setup) = latch_edge + T - output_delay_max
required(hold)  = latch_edge     - output_delay_min
```

so a positive `-min` makes hold *easier* by exactly that amount. A hold requirement is
entered as `-min -5.0`. The tool's own arithmetic confirms it - both rows reconcile to
within the same 0.110 ns of clock uncertainty:

```
setup   40.695 - 10.0 + 2.670 - 4.488 = 28.877    reported 28.767
hold             4.161 - 2.904 + 5.0  =  6.257    reported  6.147
```

The hold row only balances if the +5.0 is **added**. With the sign corrected the tool
reports -3.853 ns directly.

## Why this produces exactly the observed symptom set

A hold violation is not a failure, it is a race. Whether a given part latches the frame
sync at edge N or misses it and waits for N+1 is decided by U1's output delay versus U2's,
by trace length, and by temperature and supply - so it resolves **per part** and drifts.

| observation | explained |
|---|---|
| One part clean, three intermittent | the race resolves per part |
| Exact zeros, not bit errors | miss the frame sync, never enter the slot, DRV_HIZ=1 + pulldown |
| Every fault counter clean throughout | LRCLK is unmonitored; the PLL is MCLK-sourced and stays locked |
| New twisted-pair cable changed nothing | the margin was already negative at the FPGA pad |
| U19 bad with no cable in its path | same |
| 0.2 ohm contact resistance, still broken | contacts were never the issue |
| Worsens over a session | hold margin drifts with die temperature |

**Still not explained, by this or by anything else: why 48 kHz made every part uniformly
worse.** This theory predicts an *identical* violation at 12.288 MHz, not a worse one -
the skew and the 5 ns requirement are both unchanged by frequency. That remains open and
should not be smoothed over.

## The fix

`tdm8_master.vhd`, one line: launch LRCLK on the **falling** edge of BCLK. That puts the
transition 20.35 ns after the sampling edge at 24.576 MHz.

Required window relative to the BCLK rising edge at the part is `[tALH, T - tALS]` =
`[5.0, 30.695]` ns. Delivered, across all three corners: `20.35 + 0.607..1.257` =
**20.96 to 21.61 ns**. Margin 16 ns on the hold side, 9 ns on the setup side, against a few
ns of U1-versus-U2 skew and cable delay.

Measured after the change:

| check | before | after |
|---|---|---|
| Hold `bclk_pin` (lrclk_out), Slow 85C | **-3.853** | **+16.520** |
| Hold `bclk_pin`, Slow 0C | -4.024 | +16.331 |
| Hold `bclk_pin`, Fast 0C | -4.503 | +15.902 |
| Setup `bclk_pin`, worst corner | 28.767 | +8.382 |

## Two other defects found and fixed alongside

**SDATA input delay was referenced to the wrong clock.** `set_input_delay -clock $bclk_net`
used the internal PLL output. The ADC is not clocked by that - it is clocked by the copy
that left the FPGA on `bclk_out` and went through U2. The reference is now `bclk_pin`, plus
declared board delays for U2 and the cable. This recovers 5-7 ns the analysis had been
crediting the design with. Note this affects both lines equally and produces bit errors
rather than exact zeros, so **it does not explain U20 versus the rest.**

With the honest constraint the audio capture path still passes comfortably -
`sdata_in_A -> u_rx_A|sdata_f` has **+11.48 ns** of setup slack on a full-period path,
which validates the falling-edge SDATA capture from `f72d2f3`.

**The debug SDATA edge counters sampled the raw pin on the rising edge.** `act_a`/`act_b`
in `top_system.vhd` compared `sdata_in_A/B` directly on a half-period path against 21.5 ns
of input delay: -7.275 ns, and -122 ns of TNS swamping the whole `clk[2]` domain summary.
They now use falling-edge registers like `tdm8_rx` does. `clk[2]` setup went from **-7.275
to +10.966**. This is a diagnostic-integrity fix, not an audio fix - but `act_a`/`act_b`
are exactly the counters used to decide whether a line is alive, so they need to be sound.

## What to expect on the next build, and how to read it

**C_BIT_ADJ moved 0 -> -1 in `tdm8_rx.vhd`, and this is a prediction.** C_BIT_ADJ = 0 maps
to `sim_chain` launch offset 0, which is the ADC framing on the same edge N the FPGA
launched on - reachable only by *winning* the tALH violation, which is why only some parts
managed it. With LRCLK now arriving 21 ns after edge N, every part deterministically frames
on N+1: launch offset +1, which `sim_chain.py` maps to C_BIT_ADJ = -1.

If the channels read as noise or "misaligned?", **put C_BIT_ADJ back to 0 and rebuild.**
That single constant is the only knob, and that outcome would not invalidate the LRCLK
change.

Do not read a misalignment as the LRCLK fix having failed. Two independent measurements:

* **Dropouts** - exact-zero percentage per channel, in `udp_monitor.py` and `timeline.py` -
  test the LRCLK timing. Success is all four parts at or near 0 % zeros.
* **Bit alignment** - a known tone at full amplitude on exactly one channel - tests
  C_BIT_ADJ.

`check_sync.py` check 50 was rewritten. It used to *demand* the rising edge, deriving the
rule from BCLKEDGE; it now requires the falling edge unconditionally and cites Table 5. If
BCLKEDGE is ever set to 1 this stays falling - do not re-derive it from BCLKEDGE.

## Still worth doing

Scoping U1 pins 3/5/7/8 (`TDM2_NETLIST_FINDINGS.md` section 0, test 1) is **still worth
the time**. A ~1 ns margin was being resolved per part by U1's output-to-output delay, so
if U1 is also genuinely weak on one output the two faults stack. If the dropouts clear with
this build, the U1 rework becomes unnecessary.

The unconditional recommendations from the netlist findings stand regardless: fit the 10 k
pull-up on `/PD/RST` on the daughterboard side, and confirm U45 and U47 are off the board.
