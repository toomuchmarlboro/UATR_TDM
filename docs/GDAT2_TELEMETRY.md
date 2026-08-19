# $GDAT2 sensor telemetry — aux_vcu → Control Station

New protocol, separate hardware. This is **not** the FPGA soundcard: different
device, different transport (TCP, not UDP), different framing. Implemented in
`gdat2.py`, displayed in the **Telemetry** tab of `mixer_gui.py`.

One aux_vcu per buoy, all on **port 8080**:

| | address | |
|---|---|---|
| buoy 1 | `192.168.3.110` | |
| buoy 2 | `192.168.3.120` | |
| buoy 3 | `192.168.3.130` | **active unit** (2026-08-19) |
| buoy 4 | `192.168.3.140` | |

`gdat2.ACTIVE_BUOY` names the unit in service and `DEFAULT_HOST` follows it, so
a bare `python imu_test.py` dials the buoy that exists rather than whichever is
first in the table. Change it in that one place when the active unit changes.

> ### ⚠ `192.168.3.131` is not a buoy
>
> One digit from buoy 3, open on the same port 8080, and it **accepts the
> connection and then sends nothing** — which reads exactly like a silent
> aux_vcu. It is a different device: an `Embedthis-http` embedded web server.
>
> The discriminator is simple. **A GDAT2 source streams on connect without being
> asked.** A socket that opens and stays quiet is the wrong device, not a broken
> sensor. `imu_test.py --raw` settles it in seconds.

## OUTGOING PACKETS (aux_vcu → Control Station)

### `$GDAT2` (ID = 37) — General Data Telemetry, broadcast every ~20 ms (~50 Hz)

```
$GDAT2,<ulRaw[0]>,...,<ulRaw[9]>,<seq>,<cnt>*HH<CR><LF>
```

| Field | Type | Description | Decoded as |
|---|---|---|---|
| `ulRaw[0]` | u32 | Leak sensor | float, V |
| `ulRaw[1]` | u32 | Voltage monitor — main voltage | float, V |
| `ulRaw[2]` | u32 | Depth — water depth | float, m |
| `ulRaw[3]` | u32 | Depth temp — sensor temperature | float, °C |
| `ulRaw[4]` | u32 | AHRS Roll | float, deg |
| `ulRaw[5]` | u32 | AHRS Pitch | float, deg |
| `ulRaw[6]` | u32 | AHRS Yaw | float, deg |
| `ulRaw[7]` | u32 | Altimeter distance to seabed | integer, mm |
| `ulRaw[8]` | u32 | Altimeter confidence 0–100 | integer, % |
| `ulRaw[9]` | u32 | Digital I/O — bit0 = OPEN, bit1 = CLOSE | motor actuator state |
| `seq` | u32 | sequence | |
| `cnt` | u8 | packet counter, wraps at 256 | loss detection |

### Encoding

- `ulRaw[0..9]` are **8 hex digits each, no `0x` prefix**, even when carrying
  integer data. `"42280000"` is `0x42280000`.
- An f32 field is that u32 reinterpreted as an IEEE 754 32-bit float.
  `0x42280000` = `42.0`.
- `seq` and `cnt` are **unsigned decimal ASCII**, not hex.
- `*HH` is the XOR of every byte from the first `$` to the `*`, exclusive of
  both, as two hex chars.

**The mixed radix in one sentence is the thing to keep hold of.** The same
digits mean different numbers depending on which field they sit in: `"100"` is
256 as a `ulRaw` field and 100 as `cnt`.

A real captured sentence:

```
$GDAT2,3CC85BA9,41C0DBB2,41545BB3,419494F9,40AAE6D3,402149B0,41D23D71,00001258,0000005F,00000001,145,149*52
        0.024 V   24.107 V  13.272 m  18.573 C   5.341 d   2.520 d  26.280 d   4696 mm     95 %      OPEN  seq  cnt
```

### ⚠ One discrepancy in the makers' spec

Their encoding note reads **"42.5 °C = 0x42280000"**. That hex is **42.0**;
42.5 is `0x422A0000`. The hex is self-consistent with everything else in the
spec, so the decimal in the comment is almost certainly the typo. Worth
confirming, but it changes no code either way — the transform is hex → f32 bits
regardless.

## First real capture from buoy 3 (2026-08-19)

399 sentences in 8 s from `192.168.3.130:8080`, **0 checksum errors, 0 parse
errors, 0 counter gaps**. Framing, checksum and field layout are now confirmed
against hardware rather than against the makers' example.

```
$GDAT2,3FBFF666,0,0,0,3F8CCCCD,40466666,4331B333,0,0,0,0,222*5C
        1.4997V  0 0 0    1.1deg    3.1deg  177.7deg 0 0 0 seq cnt
```

Settled by this capture:

- **The aux_vcu is the TCP server.** We dialled it and it streamed unprompted, so
  `client` mode is correct and the "client or server" question below is closed.
- **~50 Hz confirmed** — 399 sentences in 8 s.
- **12-field form confirmed**, `cnt` increments and wraps through all 256 values.
- **`seq` is stuck at 0.** Loss detection must rely on `cnt`, which works. Do not
  build anything on `seq`.
- **Fields are NOT always 8 hex digits.** The spec says they are, "even when
  carrying integer data". The real device sends a bare `0`. The decoder
  left-pads, so this costs nothing — but a strict 8-digit parser would have
  rejected every sentence this device has ever sent.

### The AHRS is live, and quantised to 0.1°

Over 399 frames the three attitude fields held **one bit pattern each**. The
first reading of that was that they were hardcoded placeholders — the values are
`0x3F8CCCCD`, `0x40466666`, `0x4331B333`, i.e. **exactly 1.1, 3.1 and 177.7**,
and three one-decimal round numbers held bit-identical looked typed rather than
measured.

**That was wrong.** The operator shook the unit and the values moved. A second
capture read **1.2 / 3.2 / 152.3** — same one-decimal pattern, different
numbers.

The real explanation covers every observation: **the firmware quantises attitude
to 0.1°**. Every value seen across both captures is an exact multiple of 0.1. A
stationary unit therefore repeats one bit pattern indefinitely, and that is
healthy, not frozen.

The lesson is about the *inference*, not the arithmetic. "A live AHRS always
dithers in its low bits" is true of a raw fusion output and false of a quantised
one, and nothing in the stream distinguishes a still quantised sensor from a
field nobody updates — they are bit-identical. Only motion separates them.
`imu_test.py` now reports a constant axis as **UNPROVEN** and asks for the unit
to be moved, rather than asserting a fault. Once an axis has been seen to change
even once it is known alive, and later constant stretches read as stillness.

The map is confirmed: attitudes landed in the attitude slots and no field
violated its plausible range.

### What is genuinely not populated

Distinct values seen in 8 s, which is the measurement that matters:

| field | distinct | reading |
|---|---|---|
| Leak sensor | **172** | ~1.50 V, dithering — live |
| AHRS Roll / Pitch / Yaw | 1 per capture, **changes when moved** | live, 0.1° steps |
| Voltage monitor | 3 | ~0.00 V |
| Depth, Depth temp, Altimeter ×2, Digital I/O | 1 | exactly `0` |

So the module and its ADC path are running. The all-zero fields are the open
question — `Voltage monitor` reading 0.00 V on a powered unit is the one worth
asking the firmware owner about.

## Still open: client or server

> **Closed 2026-08-19** by the capture above — the aux_vcu listens, we dial it.
> `server` mode is kept for the case where a future unit dials in.

Unknown which end listens, so `Link` does either — `client` mode dials the
aux_vcu, `server` mode listens. Switchable live from the tab. Does not block
bring-up.

Also tolerated: sentences with 11 fields (no `seq`) as well as the documented
12, since the spec's field table lists `cnt` but not `seq`.

## Using it

```sh
python gdat2.py --selftest              # decoder round-trip, no hardware
python gdat2.py --sim                   # fake aux_vcu on :8080
python gdat2.py --buoy 2                # CLI readout from 192.168.3.120:8080
python gdat2.py --connect 192.168.3.110:8080
python gdat2.py --listen 8080

python mixer_gui.py --gdat-buoy 2 --gdat-connect
```

To exercise the tab with no aux_vcu present, run `python gdat2.py --sim` in one
terminal and `python mixer_gui.py --gdat-host 127.0.0.1 --gdat-connect` in
another. The simulator injects a corrupt sentence about every 2 s and skips a
counter about every 1 s, so the checksum and loss counters are exercised too — a
telemetry view that has only ever seen clean data has not been tested.

The buoy selector in the tab retargets a live link immediately; picking a buoy
drops the current connection and dials the new one.

### Window

Resizable and fully scalable — **F11** toggles fullscreen, **Escape** leaves it;
`--fullscreen` and `--maximized` set the startup state. The window opens at a
fraction of the actual screen rather than a fixed size, so it suits both a
laptop and the lab panel. Font sizes and column widths on this tab track the
window.

One subtlety worth keeping: a notebook tab that has never been shown is unmapped
and 1×1, and gets no `<Configure>`. Resizing the window while the Mixer tab was
in front therefore left this tab at its build-time font sizes. It rescales on
`<Map>` as well, i.e. the first time it becomes visible.

## IMU / AHRS — `imu_test.py`

The only IMU in this system is the AHRS inside the aux_vcu. It is **not** on the
FPGA's I2C bus and not on a serial port here — its attitude arrives already
fused, as `ulRaw[4..6]` in the sentence above. Connecting to the IMU is exactly
connecting to this link; there is no separate handshake or register map.

`gdat2.py` already prints those three fields, which proves the *link*. It does
not prove the *IMU*, because all three ways an attitude source fails produce
sentences that frame, checksum and format perfectly:

| Failure | What you see | How `imu_test.py` catches it |
|---|---|---|
| **Constant** | plausible attitude, unchanging | identical raw u32 across the window → reported **UNPROVEN**, never as a fault. On buoy 3 this is normal: attitude is quantised to 0.1°, so a still unit repeats one value. Only motion separates "sitting still" from "nobody updates this field", so the tool asks for motion instead of guessing. One observed change proves the axis alive for the rest of the session |
| **Zero** | `0.00 / 0.00 / 0.00` | all-zero for the whole window, and never yet seen to change. Quantisation explains a repeated *plausible* value, not an exact zero forever |
| **Shifted map** | *plausible* attitude, from the wrong slot | plausible-range guard on **every** field. Roll read out of the depth-temp slot is still a legal roll — the giveaway is a leak sensor reading 18 V and a confidence of 4696 % |

That last row is the one worth internalising. With the field map shifted one
place, a test run reads roll 18.50°, pitch 5.30°, yaw 2.50° — three entirely
believable numbers, correctly formatted, correct units. Nothing about the
attitude fields themselves says anything is wrong. Ranges live in
`gdat2.PLAUSIBLE` and the field map is **imported**, never copied — two copies
of a field map drifting apart is the cause of this failure, not the cure.

Yaw is unwrapped before any span or drift is computed. A plain max−min calls
`359.5 → 0.5` a 359° swing, which inverts every motion verdict at the one
heading a buoy is most likely to sit at.

```sh
python imu_test.py --selftest              # decoder + every verdict branch
python imu_test.py --buoy 1                # report only
python imu_test.py --buoy 1 --expect still   # bench: warn if something moves it
python imu_test.py --buoy 1 --expect moving  # in water: warn if it is dither only
python imu_test.py --connect 127.0.0.1 --raw # bytes only — any device, any framing
```

`--expect` is deliberately optional, and it is what turns an UNPROVEN constant
into a verdict: with `--expect moving`, an axis that does not change *is* a
fault, because something should have moved it. Without it the tool will not
guess, since whether the buoy should be moving is something only the operator
knows.

**The bench procedure that actually settles it:** run `python imu_test.py`, pick
the unit up and shake it. The axes flip from `??` to `ok ... live, moved N times
this session` the moment they change, and stay that way. That is the whole test.

With no hardware, `python gdat2.py --sim` in one terminal and
`python imu_test.py --connect 127.0.0.1` in another exercises the whole path,
including the injected checksum failures — a bad-checksum sentence is counted
but never fed to the motion window, since one corrupted float is a spike that
reads as motion.

**For a different IMU** — a part wired to a USB-serial adapter or onto the
FPGA's I2C bus — nothing in this repo names one yet. Start with `--raw`, read
the actual bytes, and write the decoder from those. A register map written from
memory produces a decoder that looks like it works and is for the wrong device.

## Notes for the reader

- **Hex is parsed as hex, with no sniffing.** An earlier decimal-first reading
  of the spec got two things silently wrong, and both are now regression-tested:
  `"42280000"` read as decimal is 42,280,000, whose bits spell `1.96e-37`; and
  because hex digits include `E`, any "looks like a float exponent" heuristic
  turns `"3E000000"` (= 0.125) into a plausible-but-wrong `3.0`. Fields are
  all-digits often enough that the first would have looked like a working link
  producing absurd numbers.
- **`seq`/`cnt` parse as base 10 explicitly.** Python's base-0 rejects a leading
  zero, so a zero-padded `"08"` would have returned `None` and silently disabled
  loss counting.
- **TCP is a byte stream, not a message stream.** At 20 ms two sentences
  routinely land in one `recv()` and a third splits across two. Sentences are
  recovered by buffering and splitting on newlines; treating each `recv()` as one
  message would corrupt roughly every other reading.
- **A checksum failure does not discard the sentence.** If the fields still
  decode, the values are shown and the tab states `CHECKSUM FAILED - values
  suspect`. During bring-up it is usually the checksum *convention* that differs,
  not the data, and discarding the evidence hides that.
- **Stale is its own state.** No sentence for >1 s greys every value and says so.
  A frozen link showing the last good reading forever is the one failure a
  telemetry view must never present as live data.
- **The error buckets are disjoint.** A corrupted sentence typically fails both
  the checksum and the field parse; counting it twice would make one fault read
  as two independent problems.
- **`bad hex` and `not a float` are different faults.** The first means the token
  was not 8 hex digits; the second means it was, but the bits spell NaN/inf —
  i.e. an integer sent where a float was documented.
- The two GUI tabs are independent. Neither device has to be present for the
  other to work — they are separate hardware and will not arrive on the bench at
  the same time.
