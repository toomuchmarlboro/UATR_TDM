# Host configuration — the complete procedure

Everything the control-station PC needs to talk to all four soundcards and all
four buoys at once. Written 2026-09-08.

Start here if you are setting up a machine. For *why* it is arranged this way
see `docs/NETWORK_SETUP.md`; for changing the addressing see
`docs/CHANGING_IP.md`.

> ## THE HOST MUST SUPPORT BOTH SUBNETS
>
> Boards exist in two generations and **a board only ever talks to the address
> its own image was built with**:
>
> | board flashed with | sends audio to | learns ARP from |
> |---|---|---|
> | `*_192-168-3-*.jic` (current) | `192.168.3.10` | `192.168.3.10` only |
> | anything older | `192.168.1.10` | `192.168.1.10` only |
>
> `C_PC_IP` is a single constant compiled into each image — one value per
> image, never two. So the **host** is the side that must hold both addresses,
> and it must hold both **whenever any board on either subnet is in use**.
>
> This is not a migration-only workaround. Until every board in the array has
> been reflashed *and verified*, both addresses stay. A board on the wrong
> subnet does not error — it transmits perfectly and the host kernel discards
> every frame before any socket sees it.
>
> Both addresses live happily on one NIC. See §2.

---

## 0. The one-minute version

```powershell
# audio (UDP, boards -> host) - BOTH addresses, both subnets. Not optional.
netsh interface ipv4 set address name="Ethernet" static 192.168.3.10 255.255.255.0
netsh interface ipv4 add address name="Ethernet" 192.168.1.10 255.255.255.0
# let inbound audio through
New-NetFirewallRule -DisplayName "TDM_UATR audio" -Direction Inbound `
    -Protocol UDP -LocalPort 5005-5008 -Action Allow -Profile Private
```

```
python python/discover.py          # does it see the boards?
python python/imu_test.py          # does it see the buoys?
```

If both report what you expect, you are done. The rest of this file is the
detail behind those four commands.

---

## 1. What is on the network

Two systems, two protocols. Audio and telemetry share `192.168.3.0/24` since
the 2026-09-07 migration — **plus `192.168.1.0/24` for any board still carrying
a pre-migration image**.

### Audio — UDP, boards push to the host

| device | address | UDP port | direction | rate |
|---|---|---|---|---|
| soundcard 1 | `192.168.3.101` | 5005 | board → host | 11.4 Mbit/s @ 24 kHz |
| soundcard 2 | `192.168.3.102` | 5006 | board → host | 11.4 Mbit/s |
| soundcard 3 | `192.168.3.103` | 5007 | board → host | 11.4 Mbit/s |
| soundcard 4 | `192.168.3.104` | 5008 | board → host | 11.4 Mbit/s |

Control (gain, 48 V phantom) goes the other way over the **same** UDP path —
`udp_rx_core` does not filter on port, so any port reaches it.

### Telemetry — TCP, host dials the buoys

All on **port 8080**, addressing is `192.168.3.1<buoy><role>`:

| role | | buoy 1 | buoy 2 | buoy 3 | buoy 4 | module |
|---|---|---|---|---|---|---|
| 0 | `$GDAT2` telemetry | `.110` | `.120` | `.130` | `.140` | `gdat2.py` |
| 1 | WitMotion IMU | `.111` | `.121` | `.131` | `.141` | `witmotion.py` |
| 2 | Ping1D altimeter | `.112` | `.122` | `.132` | `.142` | `ping1d.py` |

**The host is the TCP client** — the aux_vcu listens and we dial it (confirmed
on hardware 2026-08-19). `gdat2.Link` also has a `server` mode kept for a
future unit that dials in; you will not normally need it.

### Host

| | |
|---|---|
| audio + control, current boards | `192.168.3.10` — `C_PC_IP` in the `*_192-168-3-*` images |
| audio + control, older boards | `192.168.1.10` — `C_PC_IP` in anything older |
| telemetry | any address on `192.168.3.0/24`; `.10` serves both |

**Both audio addresses are required** while boards of both generations are in
use — see the box at the top of this file. They coexist on one NIC.

**No address collides.** Soundcards `.101`–`.104`, buoys `.110`–`.142`, host
`.10` on each subnet.

---

## 2. Configure the adapter

### Both required addresses

```powershell
netsh interface ipv4 set address name="Ethernet" static 192.168.3.10 255.255.255.0
netsh interface ipv4 add address name="Ethernet" 192.168.1.10 255.255.255.0
```

No gateway, no DNS. Check the adapter name first with `Get-NetAdapter` if it is
not called "Ethernet".

One NIC, two addresses, two subnets — Windows handles this natively and there
is no performance cost. Drop the second one only when **every** board has been
reflashed and verified on `192.168.3.x`.

`192.168.3.10` is load bearing **twice**: it is where the boards send audio,
*and* it is the filter deciding whose ARP the boards will learn from
(`pc_mac_r` in `top_system.vhd`). Get it wrong and nothing arrives.

> ⚠ **Unicast UDP is filtered by DESTINATION address.** A socket bound to
> `INADDR_ANY` still only receives packets addressed to an IP this host
> actually owns — the kernel drops the rest before any socket sees them.
> Measured on this machine:
>
> ```
> destination      host owns it?   received?
> 192.168.3.10     yes             YES
> 192.168.3.10     NO              NO      <- silently dropped
> ```
>
> This is why the address is not optional and why "the board is transmitting,
> Wireshark sees it, Python sees nothing" is a host configuration fault.

### Why the second address is not optional

Boards flashed before the migration were built with `C_PC_IP = 192.168.1.10`.
They send audio **only** to that address and learn ARP **only** from it. There
is no fallback and no negotiation — `C_PC_IP` is a compile-time constant.

So a `192.168.1.x` board on a host that holds only `192.168.3.10` is invisible:
it transmits flawlessly, the frames appear in Wireshark, and the host kernel
discards every one of them at the IP layer before any socket sees it. That is
indistinguishable from a dead board unless you know to look.

`discover.py` reports **MIXED SUBNETS** when it sees boards on both, so the
state is visible rather than silent — but only for boards it can actually
receive from, which is exactly why both addresses must be present first.

The host tools handle the mixed case throughout: `capture()` binds
`INADDR_ANY`, `discover.py` reads each board's real source address, and
`ctrl.resolve_node()` sends control to wherever the board actually is.

### Retiring the old subnet

Once every board is reflashed **and verified with `discover.py`**, drop the old
address and simplify the tooling:

```powershell
netsh interface ipv4 delete address name="Ethernet" 192.168.1.10
```

then edit `ctrl.KNOWN_SUBNETS` down to `["192.168.3"]`.

### Verify

```powershell
Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike '169.254.*' } |
    Select-Object InterfaceAlias, IPAddress | Format-Table -AutoSize
```

Expect **both** `192.168.3.10` and `192.168.1.10` on the wired adapter. If
`192.168.1.10` is missing, any board still carrying an older image will appear
completely dead.

---

## 3. Firewall

Windows Firewall silently drops inbound UDP. Without this rule the boards look
dead while transmitting perfectly.

```powershell
New-NetFirewallRule -DisplayName "TDM_UATR audio" -Direction Inbound `
    -Protocol UDP -LocalPort 5005-5008 -Action Allow -Profile Private
```

Telemetry needs **no rule** — the host opens those TCP connections outbound,
and the replies are part of an established connection.

If you prefer to allow the interpreter rather than the ports, allow `python.exe`
on the private profile. Either works.

---

## 4. Watch out for a second interface on the same subnet

Windows picks a route by interface metric, and two interfaces claiming
`192.168.3.0/24` is ambiguous. This has bitten this project before: the Wi-Fi
used to join a *different* `192.168.3.0/24` (the building network, ~29
unrelated hosts), so a reply from `192.168.3.x` proved nothing about which
segment answered.

Check:

```powershell
Get-NetIPAddress -AddressFamily IPv4 | Select-Object InterfaceAlias, IPAddress
route print -4 | Select-String "192.168.3"
```

If Wi-Fi also holds a `192.168.3.x` address, make the wired adapter win:

```powershell
Set-NetIPInterface -InterfaceAlias "Ethernet" -InterfaceMetric 5
```

Also remove any stray extra address on the same subnet (e.g. a leftover
`192.168.3.240`) — two addresses on one subnet can confuse *outbound* source
selection for control commands:

```powershell
netsh interface ipv4 delete address name="Ethernet" 192.168.3.240
```

---

## 5. Link speed

| configuration | aggregate | needs |
|---|---|---|
| 4 boards @ 24 kHz + telemetry | 46.6 Mbit/s | 100 Mbit is enough |
| 4 boards @ 96 kHz + telemetry | 183.6 Mbit/s | **gigabit NIC and uplink** |

The four board links stay at 100 Mbit either way — each carries only its own
stream. It is the **switch uplink and the host NIC** that must be gigabit for
the 96 kHz images.

Telemetry is 0.9 Mbit/s total, under 2% of the audio. It has never been a
constraint.

---

## 6. Verify — audio

```
python python/discover.py
```

Passive: it binds the four stream ports and listens, transmits nothing, and
cannot disturb a capture in progress. It reports each board's **actual** source
address and **measured** sample rate, so it works without knowing anything in
advance.

Healthy four-board array on the decimating build:

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

It names three failure modes explicitly:

| message | meaning |
|---|---|
| **MIXED SUBNETS** | a board is still on `192.168.1.x` — wrong image, or migration incomplete |
| **MIXED SAMPLE RATES** | 24K and 96K images mixed. Each board is fine but they are **not** sample-aligned |
| **MORE THAN ONE SENDER ON THIS PORT** | two boards share an address or port; every capture on that port is meaningless |

Then capture — one process per board, each on its own port:

```
python python/udp_monitor.py -p 5005 -s 10
python python/udp_monitor.py -p 5006 -s 10
python python/udp_monitor.py -p 5007 -s 10
python python/udp_monitor.py -p 5008 -s 10
```

The sample rate is **detected from the packet rate**, so a 24K and a 96K board
are both read correctly with no flag. `--rate 96000` overrides if you need it.

⚠ With `--wav`, give each one its own prefix (`--wav node1`, `--wav node2`, …).
Filenames are `"%s_ch%02d.wav" % (prefix, channel)` and carry no port or
address, so four monitors sharing a prefix silently overwrite each other.

### Control

Use `resolve_node` so a command follows the board rather than assuming a
subnet:

```python
import ctrl
ip = ctrl.resolve_node(3)              # 192.168.3.103 or 192.168.1.103
ctrl.send_gain(ch, val, ip=ip)
```

From the shell:

```
python python/ctrl.py --node 3 --all 0x60      # +24 dB, see docs/DECIMATION.md
python python/ctrl.py --node 3 --phantom status
```

---

## 7. Verify — telemetry

```
python python/imu_test.py                 # dials the active buoy
python python/gdat2.py   --buoy 3         # $GDAT2 telemetry
python python/witmotion.py --buoy 3       # IMU / attitude
python python/ping1d.py  --buoy 3         # altimeter
```

`--buoy N` resolves the address through `buoy_ip()`, so it cannot be mistyped.
To dial something else explicitly, all three take `--connect HOST[:PORT]`:

```
python python/gdat2.py  --connect 192.168.3.130
python python/ping1d.py --connect 192.168.3.132:8080
```

Offline checks that need no hardware — worth running once on a new machine to
prove the decoders work before blaming the link:

```
python python/gdat2.py     --selftest
python python/witmotion.py --selftest
python python/ping1d.py    --selftest
python python/gdat2.py     --sim      # run a fake source to point a client at
python python/ping1d.py    --sim
```

`gdat2.ACTIVE_BUOY` names the unit in service (currently **buoy 3**) and
`DEFAULT_HOST` follows it, so a bare `python imu_test.py` dials a buoy that
exists rather than whichever is first in the table. Change it in that one place
when the active unit changes.

Always use `gdat2.buoy_ip(n, role)` rather than literals. Three roles one digit
apart is the easiest kind of address to mistype, and a wrong digit reaches a
**real device that is simply not the one you meant** — so the symptom is a
decoder finding nothing, not a connection error.

### The discriminator when a link connects but stays quiet

**A GDAT2 source streams on connect without being asked.** If `.1x0:8080`
accepts the connection and then sends nothing, you are probably talking to a
web config page on the wrong port, not a silent aux_vcu. Sweep for the real
port:

```
python python/altimeter_probe.py --buoy 3 --role 1
```

An `Embedthis-http` server was once found doing exactly this on what is now
buoy 3's IMU address.

### Two things that look like faults and are not

- **Attitude repeating exact values** — the firmware quantises attitude to
  0.1°, so a still buoy legitimately repeats one value. `imu_test.py` reports
  **UNPROVEN**, never a fault, and asks for motion instead of guessing.
- **Fields reading zero** — Altimeter dist/conf (use the Altimeter tab, it is
  its own device), Voltage monitor, and Depth are known dead or unreliable on
  this firmware.

---

## 8. The GUI

```
python python/mixer_gui.py                 # everything, four AFE tabs + buoys
python python/mixer_gui.py --nodes 1,3     # only the boards you have
python python/mixer_gui_standalone.py      # single file, no local imports
```

Each AFE tab owns its own socket on that board's own stream port and its own
control IP, both derived from `ctrl.py`. Hidden tabs keep draining their
sockets so the loss counters stay honest. Each tab shows **that board's**
measured rate, so a mixed array displays correctly.

⚠ `mixer_gui_standalone.py` is **generated**. Never edit it — edit the real
modules and re-run:

```
python python/make_gui_standalone.py           # rebuild
python python/make_gui_standalone.py --check   # fail if stale
```

---

## 9. If you are writing the deployment app

Measured on this machine, and it decides the architecture:

```
socket receive, 64 MB SO_RCVBUF           59,650 pkt/s   0.00% loss
full 24-bit unpack, ONE packet at a time  30,800 pkt/s   <-- below 48,000
batched numpy (1000 packets at once)     161,000 pkt/s
```

**A naive loop that unpacks each datagram as it arrives drops packets at
96 kHz**, and it looks exactly like a network fault.

> Receive into a list. Never unpack inside the receive loop. Unpack in
> vectorised batches on another thread or after capture.

That is what `udp_monitor.capture()` already does. Preserve the structure.

Also:

- **`SO_RCVBUF` to 64 MB** on every socket. The default is ~64 kB and overflows
  in milliseconds at these rates.
- **One socket per board**, one thread each. Do not multiplex four boards onto
  one socket — `recv()` discards the sender, so four sequence-number streams
  would interleave and the loss report would be meaningless.
- **Never block the receive thread** on disk, GUI or DSP. Queue it.
- The GIL is not a problem: `recv()` releases it, and numpy releases it during
  vectorised work. Threads suffice; multiprocessing is not needed.
- **Replace lost packets, never skip them.** At 24 kHz one lost 8-frame packet
  shifts everything after it by 333 µs = **50 cm of acoustic path**,
  permanently and cumulatively. Zero-fill with a short fade preserves timing;
  hold-last-value does not. Better still, flag the window so GCC-PHAT can
  exclude it rather than correlate on invented data.

---

## 10. Troubleshooting

| symptom | first thing to check |
|---|---|
| `discover.py` finds nothing | are **both** `192.168.3.10` and `192.168.1.10` on the wired adapter? Firewall rule present? |
| some boards found, others silent | the silent ones are on the subnet whose host address is missing — §2 |
| board pings but no packets arrive | host does not own the address the image sends to — §2 |
| packets arrive, host sees none | firewall, or another process already holds the port |
| `--phantom status` reports nothing | a mixer GUI or `udp_monitor` holds that port. On Windows two sockets can both bind with `SO_REUSEADDR` while only one receives |
| packet rate 4× too high | `valid_out` ignored downstream — the decimator integration bug, not a network fault |
| enormous packet loss | check `discover.py` for **MORE THAN ONE SENDER**; otherwise host-side, see §9 |
| telemetry connects, sends nothing | wrong port or a web config page — §7 |
| works on Wi-Fi, not Ethernet | two interfaces on `192.168.3.0/24`; fix the metric — §4 |

---

## 11. Cross-board timing — read before anything coherent

**Each board free-runs off its own 50 MHz crystal.** The four sample clocks are
independent. At ±50 ppm the relative drift reaches 100 ppm — at 24 kHz that is
**2.4 samples per second**, and one sample is 6.25 cm of acoustic path at
1500 m/s.

| processing | free-running OK? |
|---|---|
| 16-channel standalone | yes — one PLL per board |
| four bearings → cross-fix | **yes** — each bearing is computed inside one board |
| TDOA / multilateration between boards | **no** |
| one coherent 64-element aperture | **no** |

No host configuration changes this. Networking makes four streams arrive at one
machine; it does not make them share a clock. See `docs/MULTI_BOARD.md` for the
1 Hz SYNC-pulse proposal that would.
