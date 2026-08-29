# Running four boards

Four soundcards, 16 channels each, all streaming to one host.

Everything per-board derives from **one integer**, `C_NODE` in `rtl/top_system.vhd`.
Building the image for board 3 means changing that and nothing else.

| node | MAC | IP | UDP port | image |
|---|---|---|---|---|
| 1 | `DE:AD:BE:EF:00:01` | 192.168.1.101 | 5005 | `output_files/96K_NODE1_192-168-1-101.jic` |
| 2 | `DE:AD:BE:EF:00:02` | 192.168.1.102 | 5006 | `output_files/96K_NODE2_192-168-1-102.jic` |
| 3 | `DE:AD:BE:EF:00:03` | 192.168.1.103 | 5007 | `output_files/96K_NODE3_192-168-1-103.jic` |
| 4 | `DE:AD:BE:EF:00:04` | 192.168.1.104 | 5008 | `output_files/96K_NODE4_192-168-1-104.jic` |

Node 1 reproduces the values that were hardcoded before this change, exactly.

All four images carry LRCLK phase **225°** (`clk3_phase_shift = 25431`) and
`C_BIT_ADJ = -1`. One phase across the whole array — see "Phase" below.

---

## 1. Set up the host

The PC's **wired** adapter must be static `192.168.1.10 / 255.255.255.0`, no
gateway. That address is `C_PC_IP`, and it is load bearing twice over: it is
where the audio is sent, and it is the filter deciding whose ARP the boards are
willing to learn from. Get it wrong and nothing arrives.

Deployment PC, Realtek PCIe GbE, `A0-AD-9F-22-4B-6E` — this is compiled in as
`C_PC_MAC`. See "Moving to a different host" if that changes.

## 2. Flash

```
quartus_pgm -m jtag -o "pi;output_files/96K_NODE2_192-168-1-102.jic"
```

One board at a time, and **check the number in the filename against the board
you have connected**. Four near-identical images is exactly the situation where
the wrong one lands on the wrong board, and the symptom (two boards fighting
over one IP) looks like a network fault rather than a flashing mistake.

## 3. Verify each board before moving on

```
ping 192.168.1.102
arp -a | findstr 192.168.1.102        # expect de-ad-be-ef-00-02
python python/udp_monitor.py -p 5006 -s 5
```

`ping` proves ARP and the IP; the MAC in the ARP table proves you flashed the
image you meant to. Do all three per board, before connecting the next one.

### On the very first board, do this instead — ORDER MATTERS

The ARP learning in `pc_mac_r` is new logic that has never run on hardware, and
it decides where every audio frame goes. On the deployment PC it is invisible in
one direction: `C_PC_MAC` is *already* the correct MAC, so "learning never
fires" and "learning fires correctly" both look like success. The only failure
that shows is learning latching a **wrong** value — and that only happens after
the first ARP. So capture before you ping, once:

```
python python/udp_monitor.py -p 5005 -s 5     # 1. BEFORE any ping
ping 192.168.1.101                            # 2. provokes the ARP
python python/udp_monitor.py -p 5005 -s 5     # 3. after
```

- **alive in 1, dead in 3** → `learn_valid` latched garbage. Revert `pc_mac_r`
  to the constant in `top_system.vhd` and rebuild; everything else stands.
- **alive in both** → learning is correct or inert. `arp -a` plus one frame's
  destination MAC in Wireshark separates those, and either is fine to ship.
- **dead in 1** → not a learning problem. Normal bring-up fault, chase it first.

Once this passes on one board the logic is proven and the short procedure above
is enough for the other three.

## 4. Capture

One instance per board, each on its own port:

```
python python/udp_monitor.py -p 5005 -s 10
python python/udp_monitor.py -p 5006 -s 10
python python/udp_monitor.py -p 5007 -s 10
python python/udp_monitor.py -p 5008 -s 10
```

If you add `--wav`, **give each one its own prefix** — `--wav node1`, `--wav
node2` and so on, giving `node1_ch01.wav` … `node4_ch16.wav`. The filenames are
`"%s_ch%02d.wav" % (prefix, channel)` and carry no port or address, so four
monitors sharing a prefix silently overwrite each other's recordings.

Control likewise takes `--node`:

```
python python/ctrl.py --node 3 --all 0
python python/ctrl.py --node 3 --test --channel 5
```

---

## Why separate ports

`udp_monitor.capture()` uses `recv()`, not `recvfrom()`. Four boards sharing
port 5005 would interleave four independent sequence-number streams into one
socket, and `loss_report` would show enormous packet loss that isn't real. One
port per board means one socket per board and the existing tools work unchanged.

The UDP checksum is `0x0000` (legal for IPv4), so moving the port costs nothing —
no checksum depends on it.

## Network requirements

Each board sends 12000 packets/s (96 kHz ÷ 8 frames per packet). On the wire
that is 476 bytes each, including preamble, FCS and interframe gap:

```
476 x 8 x 12000  =  45.7 Mbit/s per board
             x4  = 182.8 Mbit/s aggregate
```

**That does not fit in 100BASE-TX.** The switch uplink and the PC NIC must be
gigabit. The four board links stay at 100 Mbit, which is fine — each carries
only its own stream.

That last sentence is only true because of the ARP fix below.

## The destination MAC, and why it mattered

`C_PC_MAC` used to be `FF:FF:FF:FF:FF:FF`, commented *"Broadcast until ARP
resolves"* — but nothing ever resolved it. `arp_responder` captured the sender
MAC for its own reply path and never passed it anywhere else, so every audio
frame shipped with a broadcast destination, permanently.

On one board that is untidy and harmless. On four it is fatal: broadcast is
flooded to every switch port unconditionally and is **never** suppressed by MAC
learning. Each board's 100 Mbit port would have received its own 45.7 Mbit/s
plus the other three boards' 137 Mbit/s, and the I²C control path would have
starved inside a failure mode that reads as anything but a MAC problem.

Now: `C_PC_MAC` is the **reset default**, and `pc_mac_r` in `top_system` tracks
whoever ARPs from `C_PC_IP`. The learning strobe reuses every check
`arp_responder` already made — EtherType, hardware and protocol type, opcode,
target IP is ours, clean CRC — plus sender IP equals `C_PC_IP`, so a stray host
on the segment cannot redirect the audio stream at itself.

### Moving to a different host

No reflash. Set the new machine's wired adapter to 192.168.1.10 and send each
board one packet — a `ping` is enough. The ARP that provokes teaches the board
the new MAC. Until that happens the board uses the compiled-in deployment PC
address, so the deployment PC needs no round trip at all.

## The IP header checksum

This used to be the literal `x"B577"` in `udp_tx_core.vhd`, correct for
192.168.1.101 → 192.168.1.10 and for nothing else. It is now computed from the
addresses by `work.net_pkg.ipv4_checksum`.

This was the single most dangerous thing about a four-board rollout. A stale
checksum does not produce an error anywhere: the board transmits flawlessly, the
frames show up in Wireshark, and the **host kernel discards every one of them at
the IP layer before any socket sees them.** A board that looks alive on the wire
and delivers nothing.

Since `fpga_ip` and `pc_ip` are constants at the top level, synthesis folds the
whole computation back to two literal bytes. It costs nothing.

### How it is verified

There is no simulator licence on this machine, so `top_system.vhd` carries five
static concurrent assertions calling the same function on known values. Quartus
evaluates these during Analysis & Elaboration and **fails the build** if any is
wrong — confirmed by deliberately corrupting one and watching
`Error (10652): VHDL Assertion Statement ... assertion is false`.

Expected values were derived independently by one's-complement sum in Python;
node 1 additionally reproduces the hand-computed `B577` that was already proven
on hardware. The fifth assertion is an all-ones case whose inner sum overflows
16 bits more than once, exercising the carry fold that the four node addresses
do not reach.

## Phase

All four images are 225°. Do not tune phase per board.

The phase result is "slightly better than 105°" on a single board and the A–B–A
reproducibility test is still outstanding. Bringing up four-node networking and
per-board phase tuning simultaneously makes both unreadable. 225° also has more
setup margin than the 240° that was in the PLL before this build (+4.489 ns
against +2.787 ns), so it is the safer default as well as the measured one.

See `LRCLK_PHASE_SHIFT.md`.

---

## Cross-board timing — read before doing anything coherent

**Each board free-runs off its own 50 MHz crystal.** The four LRCLKs are
independent time bases. At a typical ±50 ppm the relative drift reaches
100 ppm — **9.6 samples per second at 96 kHz**, and one sample is 15.6 mm of
acoustic path at 1500 m/s. The sequence numbers cannot fix this because each
board counts only its own frames.

What that does and doesn't rule out:

| processing | free-running OK? |
|---|---|
| 16-channel standalone | yes — one PLL, one LRCLK |
| four bearings → cross-fix | **yes** — each bearing is computed inside one board |
| TDOA / multilateration between boards | **no** |
| one coherent 64-element aperture | **no** |

For bearing intersection, cross-board phase never enters the calculation. The
four bearings only need to refer to the same moment, and "the same moment" for a
cross-fix means tens of milliseconds — host packet arrival timestamps are
already better than that. Nothing to do.

For the bottom two rows, the cheap option is **not** to distribute a frequency
reference. A board deployed standalone has no reference cable, so moving the PLL
input to an external clock leaves it with a dead audio domain; fixing that needs
a runtime clock mux and two build variants, which is eight images.

Instead distribute one **slow** signal (1 Hz), latch `seq_num` on its edge, and
report the latched value in the packet header. The host then knows exactly how
many samples each board took between edges, so drift becomes a measured number
to resample against rather than an unknown. A board with no SYNC wire reports
nothing and runs standalone. There is room already — the frame-count field in
`packet_formatter.vhd` is noted as "a constant 0x0008 that nothing reads", and
bytes past 9 fall through to `x"00"`. A slow single-ended pulse also survives
long separated cable runs in a way 24.576 MHz will not.

Not implemented. Decide the processing first.

---

## Hardware note

`U43` pin P34 → FPGA pin 25 is unconnected on the soundcard and is the obvious
landing spot for a SYNC input. It is **not confirmed as a dedicated clock
input** — `GND+` in the Quartus pin report only means Quartus tied an unused pin
to ground. For a slow SYNC pulse that does not matter; any free GPIO works. If a
PLL input there ever matters, assign one and run the Fitter — Quartus errors if
it is illegal.

Related: the QSF has `set_location_assignment PIN_31 -to phy_rst_n`, but the
netlist shows FPGA pin 31 unconnected on the soundcard. That output drives
nothing. Harmless, but it means **QSF assignments in this project do not imply
board connectivity** — check the netlist before wiring anything new.
