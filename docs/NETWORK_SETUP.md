# Running four boards and four buoys on one PC

Written 2026-09-07, when the soundcards moved to `192.168.3.x` — the subnet the
buoy telemetry already occupies.

Short answer: **yes, one PC handles everything, and there is no collision.**
The capacity numbers are not close. But the *addressing* now needs care that it
did not before, because two systems that used to be on separate subnets are on
one.

---

## 1. What is on the network

| device | address | port | protocol | traffic |
|---|---|---|---|---|
| soundcard 1 | `192.168.3.101` | 5005 | UDP → host | 11.4 Mbit/s |
| soundcard 2 | `192.168.3.102` | 5006 | UDP → host | 11.4 Mbit/s |
| soundcard 3 | `192.168.3.103` | 5007 | UDP → host | 11.4 Mbit/s |
| soundcard 4 | `192.168.3.104` | 5008 | UDP → host | 11.4 Mbit/s |
| host PC | `192.168.3.10` | — | — | — |
| buoy 1 telemetry / IMU / altimeter | `.110` `.111` `.112` | 8080 | TCP ← host | ~0.2 Mbit/s |
| buoy 2 | `.120` `.121` `.122` | 8080 | TCP ← host | ~0.2 Mbit/s |
| buoy 3 | `.130` `.131` `.132` | 8080 | TCP ← host | ~0.2 Mbit/s |
| buoy 4 | `.140` `.141` `.142` | 8080 | TCP ← host | ~0.2 Mbit/s |

**No address collides.** Soundcards use `.101`–`.104`, buoys use `.110`–`.142`,
host is `.10`.

---

## 2. Capacity — the numbers, not an opinion

```
soundcards, 24 kHz    4 x 11.4 Mbit/s   =  45.7 Mbit/s
telemetry             4 x  0.2 Mbit/s   =   0.9 Mbit/s
                                           -----------
total offered                              46.6 Mbit/s
```

Against a **1 Gbit** host NIC that is **4.7% utilised**. Against 100 Mbit it is
47%, which also fits but with far less margin.

The telemetry is negligible — it is under 2% of the audio. It was never the
constraint and is not one now.

### At 96 kHz it does not fit 100 Mbit

```
soundcards, 96 kHz    4 x 45.7 Mbit/s   = 182.8 Mbit/s
telemetry                                   0.9 Mbit/s
                                           -----------
total                                     183.6 Mbit/s
```

**Gigabit is mandatory** for the 96K images on four boards. This is the single
biggest practical reason to run the decimating build: 4× decimation is what
takes the array from "needs gigabit end to end" to "fits in 100BASE-TX".

### Where the real bottleneck is

Not the wire. On a dedicated path with no competing traffic, 7 km of
single-mode fibre at BER 1e-12 drops roughly one frame per day, and the FPGA
side reports **zero sequence gaps**.

The bottleneck is **the host**: packets per second, not bits per second.

```
96 kHz:  4 boards x 12,000 pkt/s  =  48,000 pkt/s
24 kHz:  4 boards x  3,000 pkt/s  =  12,000 pkt/s
```

Every packet is a syscall, a kernel buffer copy and a Python loop iteration.
48,000/s across four Python processes is where drops actually appear, and they
appear as "packet loss" that looks like a network fault. Decimation cuts this
4×, which is the most effective loss-resilience change available.

---

## 2a. Measured, not assumed — Python's real capacity

Everything below was measured on this machine, because "Python is too slow" is
usually asserted and rarely tested. The answer is that Python is fine, **but
only if the app is written one particular way.**

### Receive capacity: not the problem

```
one socket, 64 MB SO_RCVBUF, blast test   59,650 pkt/s   0.00% loss
four sockets, four senders, 12,000 pkt/s   0.0000% loss
```

59,650 pkt/s on a single socket is above the **48,000 pkt/s** that four 96 kHz
boards produce, and 5× the 12,000 pkt/s of four decimating boards. Socket
receive is not the bottleneck.

### Per-packet processing: this IS the bottleneck

```
header parse only                     539,000 pkt/s
numpy reshape                         502,000 pkt/s
full 24-bit unpack, ONE packet at a time  30,800 pkt/s   <-- the trap
```

**30,800 pkt/s is below the 48,000 needed for four 96 kHz boards.** A naive
loop that unpacks each datagram as it arrives will drop packets at 96 kHz, and
it will look exactly like a network fault.

### The fix: batch the unpack

Accumulate raw datagrams, unpack many at once with one vectorised numpy call:

```
batch  100 packets    168,000 pkt/s
batch 1000 packets    161,000 pkt/s
batch 3000 packets    190,000 pkt/s
```

**~6× headroom even at 96 kHz.** The rule for the deployment app:

> Receive into a list. Never unpack inside the receive loop. Unpack in
> vectorised batches on a separate thread or after capture.

That is what `udp_monitor.capture()` already does — it appends raw bytes and
parses afterwards — and it is why it keeps up. Preserve that structure when
lifting the code into the PyQt application.

### What this means per configuration

| configuration | pkt/s | naive per-packet | batched |
|---|---|---|---|
| 4 boards @ 24 kHz | 12,000 | ✅ 2.5× margin | ✅ 16× margin |
| 4 boards @ 96 kHz | 48,000 | ❌ **0.64× — drops** | ✅ 4× margin |

Decimation makes even the naive approach viable. Batching makes both viable.
Do both.

### Also required in the app

- **`SO_RCVBUF` to 64 MB** on every socket (`udp_monitor.py:46` does this). The
  default is ~64 kB and overflows in milliseconds at these rates.
- **One socket per board**, one thread each. Do not multiplex four boards onto
  one socket — see the port discussion below.
- **Never block the receive thread** on disk, GUI, or DSP work. Queue it.
- The GIL is not a problem here: socket `recv()` releases it, and numpy releases
  it during vectorised work. Threads are sufficient; multiprocessing is not
  needed at these rates.

---

## 3. Why there is no collision

Four mechanisms, each doing a different job:

**Separate IP addresses** — every device is individually addressed. Unicast
UDP, so a switch forwards each board's stream only to the host port.

**Separate UDP ports per board** (5005–5008). This is deliberate and load
bearing: `udp_monitor.capture()` uses `recv()`, not `recvfrom()`, so it
discards the sender address. Four boards on one port would interleave four
independent sequence-number streams into one socket and `loss_report` would
report enormous loss that is not real. `discover.py` detects this case
explicitly and says **"MORE THAN ONE SENDER ON THIS PORT"**.

**Unicast, not broadcast.** `C_PC_MAC` was once `FF:FF:FF:FF:FF:FF` with the
comment *"Broadcast until ARP resolves"* — and nothing ever resolved it. On one
board that is untidy; on four it is fatal, because broadcast is flooded to
every switch port and is never suppressed by MAC learning. Each board's 100
Mbit port would have received all four streams. `pc_mac_r` now learns the real
MAC from any ARP originating at `C_PC_IP`.

**Different transports.** Audio is UDP push from the boards; telemetry is TCP
that the host opens outbound. They do not contend for the same sockets or the
same code path.

### The one real contention risk

**Two capture processes binding the same port.** On Windows two sockets can
both `bind()` the same UDP port with `SO_REUSEADDR` while **only one receives** —
measured on this machine; the second binds without error and then sits silent.

So if `ctrl.py --phantom status` reports nothing arrived, check whether a mixer
GUI or `udp_monitor` already holds that port. This is a host-side problem that
looks exactly like a dead board.

---

## 3a. Both subnets work, at the same time

The host tools support `192.168.1.x` and `192.168.3.x` simultaneously. This is
not a mode to select — it is how they are built:

| path | mechanism | subnet-dependent? |
|---|---|---|
| **receiving audio** | `capture()` binds `INADDR_ANY` | **no** — any subnet, always |
| **identifying a board** | `discover.py` reads the source address via `recvfrom` | **no** — the board reports itself |
| **sending control** | `ctrl.resolve_node(n)` | **no** — follows the board's live address |
| **default when silent** | `ctrl.SUBNET` | falls back to `192.168.3` |

`ctrl.resolve_node(n)` is the one to use in the app. It listens on the node's
stream port, takes the source address of the first packet, and sends the command
there — so a board still running an old `192.168.1.x` image is controlled
correctly with no flag and no configuration. If the board is silent it falls
back to `SUBNET`, which is right for a board being configured before it streams.

```python
ip = ctrl.resolve_node(2)          # wherever node 2 actually is
ctrl.send_gain(ch, val, ip=ip)
```

Verified: with a live sender on the port, `resolve_node` returns the sender's
real address rather than the configured one.

⚠ **The host still needs an address on each subnet it wants to reach.** Being
able to *identify* a board on `192.168.1.x` does not mean packets can *reach*
it. During a migration add the second address:

```powershell
netsh interface ipv4 add address name="Ethernet" 192.168.1.10 255.255.255.0
```

And note that boards built with the old image have the old `C_PC_IP` compiled
in — they will only send to, and learn ARP from, `192.168.1.10`. Both addresses
must be present and both must match what those images expect.

---

## 4. Configuring the PC

### The one required setting

Set the **wired** adapter to a static address on the array's subnet:

```
IP address    192.168.3.10
Subnet mask   255.255.255.0
Gateway       (leave empty)
DNS           (leave empty)
```

```powershell
netsh interface ipv4 set address name="Ethernet" static 192.168.3.10 255.255.255.0
```

`192.168.3.10` is `C_PC_IP`, compiled into every image. It is load bearing
twice: it is where audio is sent, **and** it is the filter deciding whose ARP
the boards will learn from. Get it wrong and nothing arrives.

`check_sync.py` asserts the RTL and `ctrl.py` agree on this — but it cannot
check what the adapter is actually set to. That part is on you.

### Firewall

Windows Firewall silently drops inbound UDP. Allow Python on the private
profile, or the boards look dead while transmitting perfectly:

```powershell
New-NetFirewallRule -DisplayName "TDM_UATR audio" -Direction Inbound `
    -Protocol UDP -LocalPort 5005-5008 -Action Allow -Profile Private
```

### Gigabit if running 96 kHz

The four board links stay at 100 Mbit — each carries only its own stream. The
**switch uplink and the host NIC** must be gigabit for the 96K images. For the
24K images 100 Mbit is sufficient throughout.

### Wi-Fi: the trap worth knowing

This laptop's Wi-Fi also joins a `192.168.3.0/24` network — the building
network, with ~29 unrelated hosts on it. **A matching subnet is not the same
network.** Getting a reply from `192.168.3.x` proves nothing about which segment
answered.

With the soundcards now also on `192.168.3.x`, Windows has two interfaces
claiming the same subnet, and route metrics decide which one is used. If
captures fail while `ping` works, this is the first thing to check:

```powershell
route print -4 | Select-String "192.168.3"
Get-NetIPAddress -AddressFamily IPv4 | Format-Table InterfaceAlias, IPAddress
```

The wired interface must own the `192.168.3.0/24` route for the array. The
cleanest fix is to lower the wired adapter's `InterfaceMetric` so it wins:

```powershell
Set-NetIPInterface -InterfaceAlias "Ethernet" -InterfaceMetric 5
```

If the buoys are reached over Wi-Fi and the soundcards over Ethernet, and both
are `192.168.3.0/24`, **that ambiguity is unavoidable and will bite.** The
robust answer is to put them on genuinely different subnets — see
`docs/CHANGING_IP.md`, which is a ten-minute change now that the subnet is a
single constant on each side.

---

## 5. Verifying it works

```
python python/discover.py
```

Passive — binds the four stream ports, transmits nothing, and reports each
board's **actual** address, **measured** sample rate, and packet loss. It needs
no configuration and makes no assumption about what is out there, which is the
point: a board flashed with the wrong image is working perfectly and is not the
board you think it is.

Expected, all four healthy on the decimating build:

```
  node 1  port 5005   192.168.3.101    24000 Hz     3000 pkt/s  loss 0.000%
  node 2  port 5006   192.168.3.102    24000 Hz     3000 pkt/s  loss 0.000%
  node 3  port 5007   192.168.3.103    24000 Hz     3000 pkt/s  loss 0.000%
  node 4  port 5008   192.168.3.104    24000 Hz     3000 pkt/s  loss 0.000%

  4 board(s) answering.
  subnet   192.168.3.x
  rate     24000 Hz  (decimating 24K_* image)
  offered  45.7 Mbit/s aggregate to this host
```

### How the rate is detected, and the trap it avoids

`fs = packets/second × 8`, because every packet carries exactly 8 audio frames
at both rates. No configuration, no help from the bitstream.

⚠ **Loss only ever lowers the measured rate, and the two rates are exactly 4×
apart.** A 96 kHz board losing 75% of its packets measures 24,000 — and would
be reported as a perfectly healthy 24 kHz board.

`detect_rate()` closes this by using the **sequence numbers** when they are
available: the FPGA increments them per packet *sent*, so the span between the
first and last received tells you how many it sent regardless of how many
arrived. Both `udp_monitor.py` and `discover.py` pass them.

```
96 kHz board, 75% loss:
   without sequence numbers  ->  24000 Hz, "confident"   (wrong)
   with sequence numbers     ->  96000 Hz, "confident"   (right)
```

Below ~15% loss the raw packet rate is enough on its own; the sequence-number
path is what makes the pathological case safe.

`discover.py` calls out three failure modes by name:

| it says | meaning |
|---|---|
| **MIXED SUBNETS** | a board is on the old `192.168.1.x` — wrong image flashed, or migration incomplete |
| **MIXED SAMPLE RATES** | 24K and 96K images are mixed. Each board is individually fine but they are not sample-aligned |
| **MORE THAN ONE SENDER ON THIS PORT** | two boards share an address or port. Every capture on that port is meaningless |

Then capture all four at once — one process per board, each on its own port:

```
python python/udp_monitor.py -p 5005 -s 10
python python/udp_monitor.py -p 5006 -s 10
python python/udp_monitor.py -p 5007 -s 10
python python/udp_monitor.py -p 5008 -s 10
```

`udp_monitor` now **detects the rate from the packet rate** and follows the
board, so no flag is needed whichever image is loaded. `--rate` overrides.

⚠ With `--wav`, give each one its own prefix (`--wav node1`, `--wav node2`, …).
The filenames are `"%s_ch%02d.wav" % (prefix, channel)` and carry no port or
address, so four monitors sharing a prefix silently overwrite each other.

---

## 6. Cross-board timing — unchanged by any of this

**Each board free-runs off its own 50 MHz crystal.** The four sample clocks are
independent time bases. At ±50 ppm the relative drift reaches 100 ppm — at
24 kHz that is **2.4 samples per second**, and one sample is 6.25 cm of acoustic
path at 1500 m/s.

| processing | OK free-running? |
|---|---|
| 16-channel standalone | yes — one PLL per board |
| four bearings → cross-fix | **yes** — each bearing is computed inside one board |
| TDOA / multilateration between boards | **no** |
| one coherent 64-element aperture | **no** |

Nothing in this document changes that. Networking makes the four streams arrive
at one host; it does not make them share a clock. See `docs/MULTI_BOARD.md` for
the 1 Hz SYNC-pulse proposal that would.
