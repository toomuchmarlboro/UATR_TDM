# Buoy telemetry: how it is arranged, and how to lift it into the main app

Three sensors per buoy, three protocols, three modules. The decoders are
deliberately **GUI-agnostic** — standard library only, no tkinter, no Qt — so
moving them into the PyQt application means importing them and deleting code,
not porting it.

```
python/gdat2.py      $GDAT2 ASCII telemetry     aux_vcu
python/witmotion.py  WitMotion binary IMU       attitude
python/ping1d.py     Ping protocol              Blue Robotics Ping1D altimeter
python/mixer_gui.py  tkinter GUI                ← the only tk-specific file
```

Only `mixer_gui.py` knows what a widget is. Everything else is transport and
decode.

---

## 1. Addressing

`192.168.3.1<buoy><role>`, all on **port 8080**.

| role | | buoy 1 | buoy 2 | buoy 3 | buoy 4 |
|---|---|---|---|---|---|
| 0 | `$GDAT2` telemetry | `.110` | `.120` | `.130` | `.140` |
| 1 | WitMotion IMU | `.111` | `.121` | `.131` | `.141` |
| 2 | Ping1D altimeter | `.112` | `.122` | `.132` | `.142` |

```python
gdat2.buoy_ip(3, gdat2.ROLE_GDAT2)      # '192.168.3.130'
gdat2.buoy_ip(3, gdat2.ROLE_IMU)        # '192.168.3.131'
gdat2.buoy_ip(3, gdat2.ROLE_ALTIMETER)  # '192.168.3.132'
```

Verified against hardware on 2026-08-29. Use `buoy_ip()` rather than literals:
three roles one digit apart is the easiest kind of address to mistype, and a
wrong digit reaches a **real device that is simply not the one you meant** — so
the symptom is a decoder finding nothing, not a connection error.

> **The host needs an address on this subnet.** If your Ethernet adapter is
> configured for the FPGA soundcards (`192.168.1.x`) it cannot reach these at
> all, and traffic leaves via Wi-Fi instead. Windows allows a second address on
> one NIC:
> ```
> netsh interface ipv4 add address name="Ethernet" 192.168.3.240 255.255.255.0
> ```

---

## 2. The one interface all three share

Every module exposes a thread with the same four members. Learn it once.

```python
link = gdat2.Link("client", host, 8080)     # or witmotion.WitLink(host)
link.start()                                #    or ping1d.PingLink(host)
snap = link.snapshot()                      # thread-safe dict, never raises
link.close()
```

The threads **reconnect on their own and never raise into the caller**. A dead
sensor is a `state` string, not an exception — you do not need try/except
around any of this.

Common keys in every `snapshot()`:

| key | meaning |
|---|---|
| `state` | `"connected"`, `"connecting to …"`, `"reconnecting"`, `"peer closed"`, `"error: …"` |
| `peer` | `"host:port"` once connected |
| `rate` | packets or sentences per second, recomputed each 0.5 s |
| `good` | count decoded since the link started |

Then the per-protocol part:

| | extra keys |
|---|---|
| `gdat2.Link` | `last`, `lines`, `csum_err`, `parse_err`, `lost`, `tail` |
| `witmotion.WitLink` | `angle`, `accel`, `gyro`, `quat`, `t`, `bad` |
| `ping1d.PingLink` | `dist`, `conf`, `t`, `bad`, `timeouts`, `asked`, `answered_id`, `nacks`, `last_nack`, `applied` |

**One inconsistency to know about.** `gdat2.Link` has no top-level `t`; its
timestamp is on the decoded sentence, `snap["last"]["t"]`. The other two
timestamp the link itself. Normalise it if you want uniform staleness logic:

```python
t = snap["last"]["t"] if snap.get("last") else None
```

### Staleness is the check that matters

A socket can stay open while the far end stops talking. `state` still reads
`"connected"`, and the last decoded values sit there looking perfectly healthy.
Every display in this repo therefore treats **stale as worse than
disconnected**:

```python
live = t is not None and (time.time() - t) <= 1.0     # 3.0 for the altimeter
```

The altimeter gets a longer window because it answers on request and
legitimately goes quiet between polls; the other two stream continuously.

---

## 3. Calibration constants

Per buoy, because they describe **an installation, not a sensor** — how that
IMU is bolted into that hull, and what ferrous metal sits near it. Two units on
the same bench will not share values.

```python
witmotion.HEADING_OFFSET_DEG = {1: 0.0, 2: 0.0, 3: -12.4, 4: 0.0}
witmotion.LEVEL_OFFSET_DEG   = {1: (0.0, 0.0), ..., 3: (2.15, -4.66), ...}

hdg       = witmotion.heading(yaw, buoy=3)          # -> [0, 360)
roll, pit = witmotion.level(roll, pitch, buoy=3)    # -> zeroed when level
```

Always apply these before displaying attitude. Raw yaw uses ±180 and the
offset pushes readings across that seam, so a buoy near north flips between
−12 and +347 unless you go through `heading()`.

**To calibrate a buoy**

1. Point the bow at north, read raw yaw → `HEADING_OFFSET_DEG[n]`.
2. Sit it level, average a few seconds of raw roll and pitch →
   `LEVEL_OFFSET_DEG[n]`.

`python witmotion.py --buoy N` prints both raw. Note whether you sighted true
or magnetic north — the arithmetic is the same, but it decides what the
corrected heading means.

> Level correction is a **small-angle** approximation: strictly a mounting
> misalignment is a rotation, and undoing it means rotating the gravity vector
> rather than subtracting two numbers. Below ~10° the error is negligible. It
> breaks if a unit is ever mounted at a serious angle.

---

## 4. The altimeter needs its settings written

This is the one that will waste your afternoon otherwise.

**The Ping1D boots with `ping_interval = 250 ms`** — four measurements a second.
A host polling faster just re-reads the same stale result, and it reads
confidence 0 with the range wandering 54–92 m. Writing the vendor settings
(50 ms) took confidence to 22–51 % and settled the range.

`ping1d.PingLink` writes them on every connect by default:

```python
ping1d.VENDOR_DEFAULTS      # {'interval': 50, 'gain': 3, 'sos': 1500000, 'enable': 1}
link = ping1d.PingLink(host)                    # writes them
link = ping1d.PingLink(host, settings=None)     # connects without touching the sensor
```

`snapshot()["applied"]` reports what was actually written. Sound velocity is
`1500000` mm/s for water, ~`343000` for an air bench test.

Two more things about this sensor:

- **Confidence, not range, says whether it found anything.** ~90 m at 0 % is
  the sonar's ceiling — "no echo" — not a measurement. In air that is normal.
- **Its `distance` message is 5 bytes, not the documented 24**, and the
  confidence field is `u8` there rather than `u16`. `parse_distance()`
  dispatches on payload length for that reason. Checked against `brping`'s
  `get_distance()` on the real device: identical distances and confidences.

---

## 5. Dropping this into the PyQt app

The existing app has one thread per sensor emitting Qt signals. The simplest
integration keeps your widgets and replaces the transport.

**Replace these**

| existing class | use instead |
|---|---|
| `DataFetcherThread` (TCP mode) | `gdat2.Link` |
| `PingSensorThread` + `TCPSocketIO` + `brping` | `ping1d.PingLink` |
| — (no equivalent today) | `witmotion.WitLink` |

Because `snapshot()` is a cheap, thread-safe read, you do not need a QThread or
signals at all — a `QTimer` polling at display rate is enough, and it removes a
whole class of cross-thread bugs:

```python
class BuoyPanel(QWidget):
    def __init__(self, buoy):
        super().__init__()
        self.tel = gdat2.Link("client", gdat2.buoy_ip(buoy, gdat2.ROLE_GDAT2), 8080)
        self.imu = witmotion.WitLink(gdat2.buoy_ip(buoy, gdat2.ROLE_IMU))
        self.alt = ping1d.PingLink(gdat2.buoy_ip(buoy, gdat2.ROLE_ALTIMETER))
        for lk in (self.tel, self.imu, self.alt):
            lk.start()
        self.buoy = buoy
        t = QTimer(self); t.setInterval(100)
        t.timeout.connect(self.refresh); t.start()

    def refresh(self):
        now = time.time()

        s = self.imu.snapshot()
        live = s["t"] is not None and (now - s["t"]) <= 1.0
        if live and s["angle"]:
            a = s["angle"]
            r, p = witmotion.level(a["roll"], a["pitch"], buoy=self.buoy)
            self.compass.setYaw(witmotion.heading(a["yaw"], buoy=self.buoy))
            self.attitude.setAttitude(r, p)

        a = self.alt.snapshot()
        if a["dist"] is not None:
            self.lbl_distance.setText("%.2f m" % (a["dist"] / 1000.0))
            self.lbl_confidence.setText("%d %%" % (a["conf"] or 0))

        g = self.tel.snapshot()["last"]
        if g and g["ok"]:
            leak = g["vals"][0]          # see gdat2.FIELDS for the order
            ...

    def closeEvent(self, ev):
        for lk in (self.tel, self.imu, self.alt):
            lk.close()
        ev.accept()
```

**Index `gdat2.FIELDS` by name, never by number.** The field map and its
plausibility bounds are two arrays kept in step; hardcoding `vals[7]` is how a
shifted map ends up printing believable numbers under the wrong headings:

```python
I_DEPTH = [i for i, (nm, _u, _k) in enumerate(gdat2.FIELDS) if nm == "Depth"][0]
```

`gdat2.implausible(vals)` returns `[(index, value, lo, hi)]` for anything out
of range — worth colouring rather than hiding, since it is the signal that a
field map has shifted.

### Attitude has two sources, and they are not independent

The aux_vcu **relays the IMU's attitude** into `$GDAT2` fields 4–6. Measured
simultaneously: GDAT2 roll `2.1000`, IMU roll `+2.10`. Prefer the IMU (~1000
packets/s against the sentence's 50) and fall back to `$GDAT2` when its link is
down — but do not treat agreement between them as corroboration.

### Fields that are not populated on this firmware

- `Altimeter dist` / `Altimeter conf` — hard zero. The sensor is a separate
  device at role 2. The manufacturer's own parser skips these two fields.
- `Voltage monitor` — flat zero.
- `Depth` — has been seen at `−222`, `−403` and `+236695` m as well as
  plausible values. Treat with suspicion and check `implausible()`.

---

## 6. Verifying without hardware

Every module runs its decoder against known-good bytes, including frames
captured from the real devices:

```
python gdat2.py --selftest
python witmotion.py --selftest       # real captured frame + both calibrations
python ping1d.py --selftest          # includes the 5-byte distance case
```

And each has a simulator, so the display path can be exercised with nothing
plugged in:

```
python gdat2.py --sim                # then --connect 127.0.0.1:8080
python ping1d.py --sim
python ping1d.py --sim --no-sim-simple   # firmware that refuses msg 1212
```

**When a link connects and decodes nothing, dump the bytes before suspecting
the sensor.** That is how the IMU at role 1 was found: it was being read as
`$GDAT2`, reported ~300 unparsable sentences a second, and looked identical to
a dead device.

```
python altimeter_probe.py 192.168.3.131      # works on any of these hosts
```

---

## 7. Regenerating the standalone GUI

`mixer_gui_standalone.py` is **generated** — one file, no local imports, for
copying onto a machine that has only numpy.

```
python make_gui_standalone.py           # rebuild
python make_gui_standalone.py --check   # fail if stale
```

Never edit it directly; edit the modules and regenerate. It inlines the
decoders by name, and the generator fails the build rather than emitting a file
that dies on the target: it catches a name read but never defined, a definition
renamed upstream, and a name inlined from two modules at once (which is why
`ping1d` and `witmotion` prefix everything — both would otherwise want `Link`,
`Sim`, `build` and `checksum`).
