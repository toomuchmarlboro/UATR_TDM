# Changing the array's IP addresses

The addressing is a **two-sided** edit: one constant in the RTL, one in the host
tools. Both sides are guarded, so getting it half-right fails loudly rather than
silently — which matters, because a wrong IP produces a board that transmits
flawlessly and delivers nothing.

Current state (moved 2026-09-07):

```
boards   192.168.3.101 - .104     C_FPGA_IP, derived from C_NODE
host     192.168.3.10             C_PC_IP
ports    5005 - 5008              one per board, deliberately
```

---

## The four things that must agree

```
1.  rtl/top_system.vhd     C_FPGA_IP  x"C0A803" & (100 + C_NODE)
2.  rtl/top_system.vhd     C_PC_IP    x"C0A8030A"
3.  rtl/top_system.vhd     the four ipv4_checksum assertions
4.  python/ctrl.py         SUBNET = "192.168.3"

    and the PC's adapter actually set to C_PC_IP.
```

Items 1–3 are in one file; item 4 is one line. `check_sync.py` compares 1, 2 and
4, and Quartus fails the build on 3. Nothing checks the adapter — that is on you.

---

## Procedure

### 1. Edit the RTL

`rtl/top_system.vhd`, two constants:

```vhdl
constant C_FPGA_IP : std_logic_vector(31 downto 0) :=
    x"C0A803" & std_logic_vector(to_unsigned(100 + C_NODE, 8));
--     ^^^^^^ third octet: C0A803 = 192.168.3

constant C_PC_IP : std_logic_vector(31 downto 0) := x"C0A8030A"; -- 192.168.3.10
```

**`C_PC_IP` must move with the boards.** A board cannot deliver to a host on a
different subnet, and `C_PC_IP` is also the filter deciding whose ARP the board
will learn from (`pc_mac_r`). Changing only the board addresses gives four
boards transmitting perfectly into nothing.

### 2. Recompute the checksum assertions

The IPv4 header checksum itself is computed at elaboration by
`work.net_pkg.ipv4_checksum`, so it follows automatically. But the **static
assertions that verify it** carry expected values, and they are pinned to the
old subnet:

```python
python - <<'EOF'
def ck(src, dst, ln=438):
    s = 0x4500 + ln + 0x0000 + 0x4000 + 0x4011
    s += (src >> 16) + (src & 0xFFFF) + (dst >> 16) + (dst & 0xFFFF)
    s = (s & 0xFFFF) + (s >> 16)
    s = (s & 0xFFFF) + (s >> 16)
    return (~s) & 0xFFFF

pc = 0xC0A8030A                      # <-- new C_PC_IP
for n in (1, 2, 3, 4):
    src = 0xC0A80300 | (100 + n)     # <-- new board subnet
    print("node %d  %08X  ->  %04X" % (n, src, ck(src, pc)))
EOF
```

Paste the four results into the assertion block near the bottom of
`top_system.vhd`. **If you skip this the build fails** — which is the intended
behaviour, not an obstacle.

Sanity check: moving the third octet by 2 (`.1` → `.3`) changes each checksum by
exactly `0x0400`. The old set was `B577/B576/B575/B574`; the new set is
`B177/B176/B175/B174`.

### 3. Edit the host side

`python/ctrl.py`, one line:

```python
SUBNET        = "192.168.3"
KNOWN_SUBNETS = ["192.168.3", "192.168.1"]
```

`SUBNET` is the default for outbound control. `KNOWN_SUBNETS` is what
`discover.py` sweeps — keep the old subnet listed while any board might still
carry an old image, and remove it once the migration is finished.

Everything else derives from these: `node_ip()`, `HOST_IP`, `FPGA_IP`, the GUI
tabs, and `make_gui_standalone.py`'s generated copy.

### 4. Verify before building

```
python python/check_sync.py
```

Must report **0 failed**. It checks:

- `board IP vs ctrl.py` — `C_NODE` and `SUBNET` produce the same address
- `host IP vs ctrl.py` — `C_PC_IP` equals `ctrl.HOST_IP`
- `host on board subnet` — the host and boards are on the same subnet
- `board subnet is known` — `KNOWN_SUBNETS` lists it, so discovery can find it

### 5. Rebuild all images

Both variants for all four boards, eight images. `C_NODE` and `C_DECIMATE` are
the only per-image edits:

```bash
export PATH="/c/altera_lite/25.1std/quartus/bin64:$PATH"
for MODE in true false; do
  TAG=$([ "$MODE" = "true" ] && echo 24K || echo 96K)
  for N in 1 2 3 4; do
    python - <<PY
import re
p = 'rtl/top_system.vhd'
s = open(p, encoding='utf-8').read()
s = re.sub(r'constant C_NODE : integer range 1 to 4 := \d+;',
           'constant C_NODE : integer range 1 to 4 := $N;', s)
s = re.sub(r'constant C_DECIMATE : boolean := (true|false);',
           'constant C_DECIMATE : boolean := $MODE;', s)
open(p, 'w', encoding='utf-8').write(s)
PY
    quartus_sh --flow compile TDM_UATR
    quartus_cpf -c -d EPCS16 -s EP4CE6E22C8 output_files/TDM_UATR.sof \
        "output_files/${TAG}_NODE${N}_192-168-3-10${N}.jic"
  done
done
```

Budget ~90 s per image, ~12 minutes for all eight.

### 6. Set the PC

```powershell
netsh interface ipv4 set address name="Ethernet" static 192.168.3.10 255.255.255.0
```

No gateway, no DNS. See `docs/NETWORK_SETUP.md` for the firewall rule and the
Wi-Fi route conflict.

### 7. Flash and confirm

**One board at a time**, checking the number in the filename against the board
actually connected. Four near-identical images per variant is exactly where the
wrong one lands on the wrong board, and the symptom looks like a network fault
rather than a flashing mistake.

```
quartus_pgm -m jtag -o "pi;output_files/24K_NODE2_192-168-3-102.jic"
ping 192.168.3.102
arp -a | findstr 192.168.3.102        # expect de-ad-be-ef-00-02
```

The MAC in the ARP table proves you flashed the image you meant to.

Then, once all four are done:

```
python python/discover.py
```

which reports each board's real address and measured rate, and names a mixed
subnet or a duplicate sender explicitly.

---

## Migration without downtime

`KNOWN_SUBNETS` exists so the array can be moved a board at a time. During the
move some boards answer on `192.168.3.x` and some on `192.168.1.x`, and
`discover.py` finds both and reports **MIXED SUBNETS**.

To capture from both at once the host needs an address on each subnet. Windows
allows a second address on one adapter:

```powershell
netsh interface ipv4 add address name="Ethernet" 192.168.1.10 255.255.255.0
```

⚠ **But the boards on the old subnet were built with the old `C_PC_IP`**, so
they will only send to `192.168.1.10` and only learn ARP from it. Both addresses
must be present, and both must be the ones compiled into the respective images.
This works, but it is a transitional state — finish the migration.

---

## Why the checksum matters so much

From `docs/MULTI_BOARD.md`, and worth repeating because it is the failure mode
that wastes the most time:

> A stale checksum does not produce an error anywhere: the board transmits
> flawlessly, the frames show up in Wireshark, and the **host kernel discards
> every one of them at the IP layer before any socket sees them.**

A board that looks alive on the wire and delivers nothing. That is why the
checksum is computed rather than hand-entered, why there are static assertions
that fail the build, and why step 2 is not optional.

Confirmed working: deliberately corrupting one expected value produces
`Error (10652): VHDL Assertion Statement ... assertion is false` and stops the
build.
