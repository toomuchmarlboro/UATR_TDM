# 48 V phantom power: control, readback, and the watchdog

> **LRCLK note.** The four deployment images are built with
> `C_LRCLK_RETIME = false`, i.e. the LRCLK output timing of `96K_ACT` — the
> build all 16 channels are known to work on. The 225 deg phase-shift work is
> intact but out of the signal path; see `docs/LRCLK_PHASE_SHIFT.md`. This means
> flashing them changes only phantom power behaviour, nothing about clocking.

Phantom power used to be write-only. The host could command it and had no way
to ask what the board was doing, which left two divergences that nothing could
detect and that push the state opposite ways:

- **The FPGA resets, the host does not.** `udp_rx_core` clears `udp_flags` to
  `0x00` on `sys_rst`, which follows `pll_locked`. 48 V drops while the host UI
  still shows it on.
- **The host restarts, the FPGA does not.** Nothing clears `udp_flags`, so 48 V
  stays **live on the XLRs** while a freshly started app shows off. Worse: every
  gain command carries the flags byte, so the first fader the operator moved
  would send `flags = 0x00` and switch phantom off without anyone asking.

The readback closes both. The FPGA now publishes what it is actually driving.

---

## Control: what the host sends

One UDP datagram to the board's IP. `udp_rx_core` does not filter on port.

| byte | meaning |
|------|---------|
| 0 | `[3:2]` ADC select 0-3 (U19, U20, U37, U38), `[1:0]` channel 0-3 |
| 1 | gain, written to register `0x0A`-`0x0D` of that part |
| 2 | *optional* flags. **bit 0 = 48 V phantom enable** |

```python
sock.sendto(bytes([0x00, 0xA0, 0x00]), (fpga_ip, 5005))   # ch 1 @ 0 dB, 48 V off
```

A 2-byte packet is still valid and leaves the flag state untouched. A 3-byte
packet always writes it.

**There is no flags-only packet.** The FPGA parses one command format, so every
gain write says something about phantom power. This is the single most important
consequence for host code:

> Whatever your app attaches to routine gain commands *is* what phantom power
> becomes. Attach the current state, not a default.

`mixer_gui.py` handles this in `flags()`, which returns the **board's own
readback** — "keep doing what you're doing" — so a fader move is phantom-neutral.
Only a deliberate click sends something different.

---

## Readback: what the FPGA reports

**Byte 60 of every audio packet** (`HDR_LEN 10 + 1 x FRAME_LEN 50`). This is
frame 1's byte 0, which carries `dbg_status2`. `frame_count` cycles 0-7 *within*
each packet, so the offset is fixed in every packet, not just some.

| bit | mask | meaning |
|-----|------|---------|
| 7 | `0x80` | marker — byte is populated. **Clear = bitstream predates this; ignore the rest.** |
| 6 | `0x40` | `en_48v` as actually driven on the pin |
| 5 | `0x20` | the host asked for it (`udp_flags` bit 0) |
| 4 | `0x10` | staged power-up passed 1000 ms |
| 3 | `0x08` | this build permits it (`C_ENABLE_48V`) |
| 2:0 | | I2C self-test, unrelated |

```python
b = pkt[60]
if b & 0x80:
    on = bool(b & 0x40)
```

Bit 6 is the AND of bits 5, 4, 3 **and the watchdog gate**. All four are
published rather than just the pin because "off" has several causes needing
different responses — see the table under *Diagnosing* below.

`ctrl.phantom_state()` decodes it; `ctrl.phantom_reason()` turns it into a
sentence. `python ctrl.py --phantom status` prints it.

### Asserted, not measured

`EN_48V` is an FPGA **output**. There is no sense line back from the 48 V supply.
A dead DC-DC, a blown fuse or an open enable trace still reads as ON. Real
presence sensing would need a hardware change. Do not treat this as a rail
measurement.

---

## Ownership

The operator app owns phantom power. `mixer_gui.py` is a debugger watching
alongside it.

**App policy:** 48 V off at every startup and reload; only a user toggle turns
it on. Implemented by sending `flags = 0x00` once at startup — free if the app
initialises gains then anyway.

Verify, don't assume: if the app starts while the FPGA is unreachable, the off
command never lands and 48 V stays live. "Sent" and "off" are different facts.
Read byte 60 back and retry until it agrees.

**`mixer_gui.py`** therefore follows the board rather than holding its own
opinion — its checkbox is driven by the readback and tracks changes the app
makes. A click is a request that waits for the board to confirm; if the FPGA
refuses, the checkbox snaps back and names why.

Because the FPGA is the single source of truth, any number of UIs reading the
readback stay consistent automatically, whichever one the user touches.

---

## The watchdog

The app policy above is a **convention**, and it only covers an orderly restart.
An app *crash*, a pulled cable, or PC power loss all leave 48 V live
indefinitely, because nothing ever tells the FPGA the host is gone.

`C_PHANTOM_WATCHDOG` in `top_system.vhd` makes it a **fail-safe** instead: the
FPGA drops 48 V unless it has heard a flags-carrying packet within
`C_PHANTOM_TIMEOUT_S`.

```vhdl
constant C_PHANTOM_WATCHDOG  : boolean := false;   -- default
constant C_PHANTOM_TIMEOUT_S : integer := 120;
```

**Default false, deliberately.** Enabling it makes a keepalive *mandatory*: any
host that sets phantom and then goes quiet sees 48 V drop mid-capture, which
during a real deployment is worse than the hazard it prevents.

### Contract, once enabled

| | |
|---|---|
| host must send | a **3-byte** packet (one carrying flags) every ~20 s |
| tolerates | 5 consecutive lost keepalives |
| detects a dead host in | <= 120 s |

The kick is `udp_flags_wr`, which pulses only when a packet actually carried a
flags byte — **not** `udp_req`. A 2-byte gain command proves the link is up but
says nothing about intent, and feeding the watchdog from it would let a stray
`ctrl.py --set` re-arm 48 V minutes after the app that asked for it had died.

**The gate does not latch.** A keepalive arriving after a trip restores phantom
on the spot, because the flags byte it carries states what the host wants. That
is right for a link that merely hiccupped; a host that genuinely restarted sends
`flags = 0x00` and phantom stays off — the same answer from the other side.

Flash all four boards together when changing this. A board with the watchdog on
and a board with it off behave differently under exactly the conditions you
would be least able to diagnose in the water.

---

## Diagnosing

Read byte 60 and work down. Only one row can be true at a time.

| bits 6/5/4/3 | meaning | fix |
|---|---|---|
| `1 x x x` | 48 V is being asserted | — |
| `0 x x 0` | build forbids it | `C_ENABLE_48V := true`, rebuild |
| `0 x 0 1` | staged power-up not at 1000 ms | wait; if persistent, the PLL is not locking |
| `0 0 1 1` | host never asked, or an FPGA reset cleared the request | send a flags packet |
| `0 1 1 1` | **watchdog tripped** | send a flags packet; check why the host went quiet |

The watchdog needs no status bit of its own precisely because nothing else
produces "all three gates set, pin low".

Tools: `python ctrl.py --phantom status` for the sentence, `python i2c_scan.py`
for it inside the bus-health block, `mixer_gui.py` for it live.

If `--phantom status` reports nothing arrived, check whether a mixer GUI or
`udp_monitor` already holds the stream port — on Windows two sockets can both
bind it with `SO_REUSEADDR` while only one receives.
