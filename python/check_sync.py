#!/usr/bin/env python3
"""
Cross-check the Python decoders against the VHDL that produces the packets.

Every constant in udp_monitor.py / i2c_scan.py is derived from something in the
RTL: the packet layout from packet_formatter.vhd, the sample rate from
tdm8_master.vhd and the PLL, the register values from adau_sequencer.vhd, the
addresses from get_i2c_addr. If either side is edited, this catches the drift.

    python check_sync.py

Exit code 0 if everything agrees, 1 if not.
"""

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RTL  = ROOT / "rtl"

FAIL = []
OK = []


def chk(name, got, want, note=""):
    if got == want:
        OK.append((name, got, note))
    else:
        FAIL.append((name, got, want, note))


def rd(path):
    return open(path, encoding="utf-8", errors="replace").read()


# ------------------------------------------------------------------ sources ---
pf  = rd(RTL / "packet_formatter.vhd")
tm  = rd(RTL / "tdm8_master.vhd")
trx = rd(RTL / "tdm8_rx.vhd")
seq = rd(RTL / "adau_sequencer.vhd")
utx = rd(RTL / "udp_tx_core.vhd")
pll = rd(ROOT / "ip" / "pll_audio" / "pll_audio.vhd")
mon = rd(HERE / "udp_monitor.py")
scn = rd(HERE / "i2c_scan.py")


# Import the decoders and read their real values rather than regexing them -
# several are expressions (PAYLOAD_LEN = HDR_LEN + FRAMES_PKT * FRAME_LEN).
# Both modules guard their entry point, so importing is side-effect free.
import importlib
_mon = importlib.import_module("udp_monitor")
_scn = importlib.import_module("i2c_scan")


def pyconst(src, name, cast=int):
    mod = _mon if src is mon else _scn
    return getattr(mod, name, None)


# ------------------------------------------------------- 1. packet geometry ---
# packet_formatter writes a 10 byte header (byte_cnt 0..9), then 8 frames of
# 50 bytes (byte_cnt 0..49, frame_count 0..7).
hdr_last   = int(re.search(r'if byte_cnt = (\d+) then\s*\n\s*state\s*<= WRITE_FRAME', pf).group(1))
frame_last = int(re.search(r'if byte_cnt = (\d+) then\s*\n\s*state <= IDLE', pf).group(1))
# several 'if frame_count = N' exist (the IDLE check uses 0); the wrap is the
# largest, so take the max
frames     = max(int(x) for x in
                 re.findall(r'if frame_count = (\d+) then', pf)) + 1

chk("HDR_LEN",     pyconst(mon, "HDR_LEN"),   hdr_last + 1,   "packet_formatter WRITE_HEADER")
chk("FRAME_LEN",   pyconst(mon, "FRAME_LEN"), frame_last + 1, "packet_formatter WRITE_FRAME")
chk("FRAMES_PKT",  pyconst(mon, "FRAMES_PKT"), frames,        "packet_formatter frame_count")
chk("PAYLOAD_LEN", pyconst(mon, "PAYLOAD_LEN"),
    (hdr_last + 1) + frames * (frame_last + 1),               "derived")

# udp_tx_core must agree on the payload size
utx_payload = int(re.search(r'constant PAYLOAD_BYTES\s*:\s*integer\s*:=\s*(\d+)', utx).group(1))
chk("udp_tx_core PAYLOAD_BYTES", utx_payload, pyconst(mon, "PAYLOAD_LEN"), "must match")

utx_total = int(re.search(r'constant TOTAL_BYTES\s*:\s*integer\s*:=\s*([^\n;]+)', utx).group(1)
                .replace("HDR_BYTES", "42").replace("PAYLOAD_BYTES", str(utx_payload))
                .replace("+", "+")) if False else None
hdr_bytes = int(re.search(r'constant HDR_BYTES\s*:\s*integer\s*:=\s*(\d+)', utx).group(1))
chk("WIRE_LEN", pyconst(mon, "WIRE_LEN"), hdr_bytes + utx_payload,
    "eth+ip+udp header %d + payload %d" % (hdr_bytes, utx_payload))

# ------------------------------------------------------------ 2. audio rate ---
# which PLL output is wired to the audio clock in top_system's port map, and the
# frame length from tdm8_master. The two together fix fS, because MCLK and BCLK
# share a net on this board:
#   c0 12.288 MHz / 256 BCLK = 48 kHz      c1 18.432 MHz / 192 BCLK = 96 kHz
#   c1 18.432 MHz / 256 BCLK = 72 kHz      c2 24.576 MHz / 256 BCLK = 96 kHz
top = rd(RTL / "top_system.vhd")
m = re.search(r'c([012])\s*=>\s*clk_18m', top)
assert m, "cannot tell which PLL output drives clk_18m"
which = "clk%s" % m.group(1)
mult = int(re.search(which + r'_multiply_by\s*=>\s*(\d+)', pll).group(1))
divi = int(re.search(which + r'_divide_by\s*=>\s*(\d+)',   pll).group(1))
bclk = 50_000_000 * mult / divi
# The frame length is C_FRAME_BCLKS if tdm8_master declares one, otherwise the
# old hardcoded wrap value. Reading only the literal broke the moment the frame
# became a named constant.
_fr = re.search(r'C_FRAME_BCLKS\s*:\s*integer\s*:=\s*(\d+)', tm)
if _fr:
    div = int(_fr.group(1))
else:
    div = int(re.search(r'if bit_cnt = (\d+) then', tm).group(1)) + 1
fs   = bclk / div
# Not every rate is a round number of kHz: 44.1 kHz cannot be generated exactly
# from 50 MHz (needs 3528/15625) and the closest ALTPLL ratio lands +64 ppm off.
# Compare within 0.1% rather than rounding to the nearest kHz.
# C_DECIMATE divides the ADC rate by 4 on the way out, so the rate the HOST
# sees is not the rate the ADC runs at. The packet layout is byte-identical
# either way, so nothing downstream can notice a mismatch on its own - this is
# the only place the two sides are compared.
_decim = re.search(r'constant\s+C_DECIMATE\s*:\s*boolean\s*:=\s*(true|false)', top)
_dec_on = bool(_decim and _decim.group(1) == "true")
_ratio = 4 if _dec_on else 1
_host_fs = fs / _ratio

_want = pyconst(mon, "SAMPLE_RATE")
chk("SAMPLE_RATE", abs(_want - _host_fs) / _host_fs < 1e-3, True,
    "BCLK %.4f MHz / %d = %.1f Hz at the ADC, C_DECIMATE=%s -> /%d -> %.1f Hz "
    "on the wire, udp_monitor says %d (%+.0f ppm)"
    % (bclk / 1e6, div, fs, str(_dec_on).lower(), _ratio, _host_fs, _want,
       (_want - _host_fs) / _host_fs * 1e6))

# The decimator is only in the datapath when its files are in the project.
# C_DECIMATE = true without them is a build that cannot work; the reverse is
# harmless (the instance is stripped), so only one direction is an error.
if _dec_on:
    _qsf = rd(ROOT / "TDM_UATR.qsf")
    chk("decimator in QSF", ("decimator.vhd" in _qsf
                             and "decim_coef_pkg.vhd" in _qsf), True,
        "C_DECIMATE is true, so rtl/decimator.vhd and rtl/decim_coef_pkg.vhd "
        "must both be listed in TDM_UATR.qsf")

    # Coefficients are generated; the package must match what the design script
    # currently produces or the filter is not the one that was verified.
    _cf = rd(RTL / "decim_coef_pkg.vhd")
    _n1 = re.search(r'C_N1\s*:\s*integer\s*:=\s*(\d+)', _cf)
    _n2 = re.search(r'C_N2\s*:\s*integer\s*:=\s*(\d+)', _cf)
    chk("decim coefficients present", bool(_n1 and _n2), True,
        "decim_coef_pkg.vhd declares C_N1/C_N2 (regenerate with "
        "python/design_decimator.py)")

# slot width and data width are no longer the same: 32 BCLK slots carry 24-bit
# samples, so the shift register (frame in BCLKs) is wider than the data output.
# TDM mode comes from the ADC configuration, not from an assumption here.
# 0x05 SAI_CTRL0 bits [5:3] SAI: 011 = TDM8, 100 = TDM16   (Table 20)
# 0x06 SAI_CTRL1 bits [6:5] SLOT_WIDTH: 00 = 32, 01 = 24, 10 = 16 BCLKs
# 0x06 SAI_CTRL1 bit  4    DATA_WIDTH: 0 = 24-bit, 1 = 16-bit   (Table 21)
_rom_pairs = dict((int(v[:2], 16), int(v[2:], 16)) for v in
                  re.findall(r'=>\s*x"([0-9A-Fa-f]{4})"', seq))
v05, v06 = _rom_pairs.get(0x05, 0), _rom_pairs.get(0x06, 0)
nslots = {3: 8, 4: 16}.get((v05 >> 3) & 7)
slotw  = {0: 32, 1: 24, 2: 16}.get((v06 >> 5) & 3)
dataw  = 16 if (v06 >> 4) & 1 else 24
# The receiver that is actually instantiated in top_system, not whichever file
# happens to exist - both are kept in the project so a revert is one swap.
rx_name = "tdm16_rx" if re.search(r'^\s*u_rx\s*:\s*tdm16_rx', top, re.M) else "tdm8_rx"
trx = rd(RTL / (rx_name + ".vhd"))
shift_w = int(re.search(r'signal shift_reg\s*:\s*std_logic_vector\((\d+) downto 0\)', trx).group(1)) + 1
cap_extra = int(re.search(r'C_CAP_EXTRA\s*:\s*integer\s*:=\s*(\d+)', trx).group(1))             if "C_CAP_EXTRA" in trx else 0
# The receivers do not agree on port shape: tdm8_rx exposes one ch_data_out and
# is instantiated twice (one per SDATA line), tdm16_rx exposes ch_data_A and
# ch_data_B from a single instance. Count what is actually there rather than
# assuming either shape - total audio bits per frame is what has to match the
# host, and both arrangements have to reach the same number.
_ports = [int(w) + 1 for w in re.findall(
    r'ch_data_\w+\s*:\s*out\s*std_logic_vector\((\d+) downto 0\)', trx)]
n_inst  = len(re.findall(r':\s*' + rx_name + r'\s+port map', top))
data_w  = sum(_ports)
chk("channels x bits", pyconst(mon, "CHANNELS") * pyconst(mon, "SAMPLE_BYTES") * 8,
    data_w * n_inst, "%s: %d output port(s) totalling %d bits x %d instance(s)"
    % (rx_name, len(_ports), data_w, n_inst))
# The receiver carries slack either side of the frame so C_BIT_ADJ can slide the
# capture window, so the register is intentionally wider than one frame.
# tdm16_rx constrains the type ("integer range -8 to 8 := -1") to catch a typo at
# elaboration, so the range clause has to be optional here or this stops matching.
adj = int(re.search(r'C_BIT_ADJ\s*:\s*integer\s*(?:range\s+[^:]*?)?:=\s*(-?\d+)',
                    trx).group(1))
chk("shift reg holds a frame", shift_w >= div + abs(adj), True,
    "%s %d bits >= %d BCLK frame + %d adj" % (rx_name, shift_w, div, abs(adj)))
# The slice must land inside the register for EVERY slot, at the configured
# slot width and data width. When the data exactly fills the slot there are no
# pad bits and no slack at all, so the lowest index reduces to the capture
# offset itself and a negative C_BIT_ADJ becomes an illegal VHDL range. That is
# what C_CAP_EXTRA buys back: it delays the capture so the frame sits higher in
# the register, creating room underneath.
base = (div - 1) + cap_extra
hi   = base + adj
lo   = base + adj - slotw * (nslots - 1) - dataw + 1
chk("capture window in range", 0 <= lo and hi <= shift_w - 1, True,
    "%s C_BIT_ADJ = %+d, C_CAP_EXTRA = %d -> slice %d..%d inside 0..%d; "
    "%d slots x %d BCLK carrying %d-bit data leaves %d pad bits per slot"
    % (rx_name, adj, cap_extra, lo, hi, shift_w - 1,
       nslots, slotw, dataw, slotw - dataw))

# --------------------------------------------------------------- 3. magic ----
mg = re.findall(r'when [0-3] => fifo_wr_data <= x"([0-9A-Fa-f]{2})"', pf)[:4]
chk("MAGIC", list(pyconst(mon, "MAGIC", lambda s, b: bytes.fromhex(
        re.sub(r'[^0-9A-Fa-fx,\s\[\]()]', '', s)))) if False else
    [int(x, 16) for x in re.findall(r'0x([0-9A-Fa-f]{2})', re.search(
        r'MAGIC\s*=\s*bytes\(\[(.*?)\]\)', mon, re.S).group(1))],
    [int(x, 16) for x in mg], "packet_formatter WRITE_HEADER bytes 0-3")

# ------------------------------------------- 4. diagnostic byte positions ----
# packet_formatter maps frame_count -> which debug byte sits in frame byte 0
fmap = dict((int(a), b) for a, b in
            re.findall(r'when (\d+) => fifo_wr_data <= (dbg_status\d?)', pf))
expect_slots = {0: "dbg_status", 1: "dbg_status2", 2: "dbg_status3",
                3: "dbg_status4", 4: "dbg_status5", 5: "dbg_status6",
                6: "dbg_status7", 7: "dbg_status8"}
for f in range(1, 8):
    chk("frame %d debug byte" % f, fmap.get(f), expect_slots[f],
        "i2c_scan reads frame %d byte 0" % f)

# ------------------------------------------------- 5. ADC register values ----
rom = dict((int(a), int(b, 16)) for a, b in
           re.findall(r'^\s*(\d+)\s*=>\s*x"([0-9A-Fa-f]{4})"', seq, re.M))
written = dict((v >> 8, v & 0xFF) for v in rom.values())
vfy = dict((int(a, 16), int(b, 16)) for a, b in
           re.findall(r'\(0x([0-9A-Fa-f]{2}),\s*"[A-Z0-9_]+",\s*0x([0-9A-Fa-f]{2})',
                      scn))
for reg, want in sorted(vfy.items()):
    chk("i2c_scan expects 0x%02X" % reg, want, written.get(reg),
        "adau_sequencer BOOT_ROM")

# ----------------------------------------------------- 6. device addresses ---
addrs = [int(m, 2) for m in re.findall(r'return "([01]{7})";', seq)][:4]
scn_addrs = [int(a, 16) for a in re.findall(r'\(0x([0-9A-Fa-f]{2}),\s*"U\d+"', scn)]
chk("device addresses", scn_addrs, addrs, "get_i2c_addr vs i2c_scan DEVICES")

# -------------------------------------------------------------- 7. datasheet -
# values that must match the ADAU1978 datasheet, not the RTL
DS = {0x00: (0x01, "PWUP=1"),
      0x01: (0x03, "CLK_S=0 MCLKIN, MCS=011 = 256 x fS at 96 kHz"),
      # bit 7 LR_POL and bit 6 BCLKEDGE are design choices tied to how the FPGA
      # drives LRCLK/BCLK, not datasheet-mandated values, so mask them here.
      # Bits [5:0] (LDO_EN, VREF_EN, ADC_EN4..1) are the ones that must be set.
      0x04: (0x3F, "LDO+VREF+ADC1-4 enabled", 0x3F),
      # SAI (0x05 [5:3]) and SLOT_WIDTH/DATA_WIDTH (0x06 [6:5], [4]) are the
      # TDM mode itself and are checked below against Table 10 rather than
      # pinned here - otherwise switching TDM8 <-> TDM16 means editing the
      # "datasheet" table, which is exactly how a check turns into a rubber
      # stamp. What is pinned is everything the mode must NOT change.
      0x05: (0x43, "left-justified (fmt=01), FS=011 64-96kHz", 0xC7),
      0x06: (0x08, "SDATAOUT1, LRCLK pulse, MSB first, slave", 0x8F),
      0x09: (0xF8, "drive C1-C4, DRV_HIZ=1")}
for reg, spec in sorted(DS.items()):
    val, why = spec[0], spec[1]
    mask = spec[2] if len(spec) > 2 else 0xFF
    got = written.get(reg)
    chk("datasheet 0x%02X" % reg, None if got is None else got & mask, val & mask,
        why + ("" if mask == 0xFF else "  (mask %02X)" % mask))

# Table 10: slots x BCLKs-per-slot IS the frame, and the frame is what
# tdm8_master counts out. Previously this read slotw = div // 8, which made it
# div == 8 * (div // 8) - true for any div, and blind to the slot COUNT. It now
# derives both numbers from the ADC registers, so a TDM16 config against a
# TDM8-length frame fails here instead of on the bench.
chk("Table 10 BCLK ratio", nslots * slotw, div,
    "TDM%d x %d BCLK slots = %d BCLK frame = %d x fS" % (nslots, slotw, div, div))
chk("data fits its slot", dataw <= slotw, True,
    "%d-bit data in a %d-BCLK slot" % (dataw, slotw))
# Channels are slots x LINES, not slots. TDM8 runs two independent SDATA lines
# whose slot numbering restarts on each, so 8 slots x 2 receivers = 16 channels;
# TDM16 runs one line of 16. n_inst is how many receivers top_system actually
# instantiates, which is the only place that distinction is recorded.
chk("host channel count", pyconst(mon, "CHANNELS"), nslots * n_inst,
    "TDM%d x %d line(s) = %d channels, udp_monitor decodes %d"
    % (nslots, n_inst, nslots * n_inst, pyconst(mon, "CHANNELS")))

# The FPGA's LRCLK shape and the ADC's LR_MODE must agree. Nothing checked this
# before, and they drifted apart: tdm8_master sent 50% duty while tdm16_merge
# still level-tested a signal it expected to be one clock wide, so it latched
# 128 times per frame. Table 21 bit 3: 0 = 50% duty, 1 = one-BCLK pulse.
lr_pulse = re.search(r'C_LR_PULSE\s*:\s*boolean\s*:=\s*(true|false)', tm).group(1) == "true"
chk("LRCLK shape agrees", (written.get(0x06, 0) >> 3) & 1, 1 if lr_pulse else 0,
    "tdm8_master C_LR_PULSE=%s vs 0x06 bit 3 LR_MODE" % lr_pulse)

# The sequencer's own VFY_LIST is what the boot verify compares the readback
# against, so it must agree with BOOT_ROM register for register. Nothing checked
# this, and when 0x06 changed from 0x00 to 0x08 the BOOT_ROM, i2c_scan and the
# datasheet table were all updated while VFY_LIST was left stale - so the verify
# reported a false mismatch on a register that was written correctly.
pairs = re.findall(r'\d\s*=>\s*x"([0-9A-Fa-f]{2})([0-9A-Fa-f]{2})"', seq)
vfy = {int(r, 16): int(v, 16) for r, v in pairs[:6]}
for reg, want in sorted(vfy.items()):
    chk("VFY_LIST 0x%02X" % reg, want, written.get(reg),
        "adau_sequencer VFY_LIST vs BOOT_ROM")

# POLL_LIST is the RUNTIME check and has its own copy of the expected values.
# Entries 0..2 are read-only status registers whose expected byte is ignored;
# 3..5 are configuration compared against what was written. VFY_LIST was fixed
# when 0x06 changed and this one was missed, so the runtime check reported
# CONFIG DRIFTED on all four parts - a false alarm indistinguishable from the
# real fault being chased.
poll = [(int(r, 16), int(v, 16)) for r, v in pairs[6:12]]
for idx, (reg, want) in enumerate(poll):
    if idx < 3:
        continue                     # status register, value not compared
    chk("POLL_LIST 0x%02X" % reg, want, written.get(reg),
        "adau_sequencer POLL_LIST vs BOOT_ROM (runtime check)")

# cfg_ok_i decides whether the boot verify PASSES. If it is gated on a literal
# rather than on VFY_LIST, changing a register value makes the verify fail
# forever: the sequencer retries the whole boot MAX_BOOT_TRIES times, each pass
# rewriting 0x01 PLL_CONTROL to all four parts and knocking their PLLs off
# framing for ~167 ms. That is exactly what happened when 0x05 went 0x5A -> 0x5B
# for 96 kHz, and it presented as a hardware dropout for hours.
_lit = re.search(r'if i2c_data_rd = x"([0-9A-Fa-f]{2})" then\s*\n\s*cfg_ok_i', seq)
chk("cfg_ok_i not gated on a literal", _lit is None, True,
    "adau_sequencer must compare against VFY_LIST, found x\"%s\""
    % (_lit.group(1) if _lit else "-"))

# tdm8_master must launch LRCLK on the FALLING edge of BCLK. Fixed, not derived
# from BCLKEDGE.
#
# This check used to key off 0x04 bit 6 BCLKEDGE, on the reading that BCLKEDGE
# selects "the edge the serial port acts on" for everything. It does not, and
# Table 5 on page 5 of the ADAU1978 datasheet settles it - the ADC SERIAL PORT
# block gives three separate parameters with two different reference edges:
#
#   tALS   10 ns min   "LRCLK setup to BCLK rising, slave mode"
#   tALH    5 ns min   "LRCLK hold from BCLK rising, slave mode"
#   tABDD  18 ns max   "SDATAOUTx delay from BCLK falling"
#
# LRCLK is sampled on the RISING edge whatever BCLKEDGE is; BCLKEDGE moves the
# OUTPUT launch edge, which is the one tABDD measures. So the FPGA must launch
# LRCLK on the falling edge, unconditionally, to sit half a period away from the
# sampling edge.
#
# Launching on the rising edge is what this check used to demand, and it put the
# LRCLK transition on the very edge that samples it. Quartus scored the residual
# at -3.853 ns of hold against tALH on 2026-08-16, i.e. LRCLK left its pad only
# 1.257 ns after BCLK left its. Which parts then framed correctly was decided by
# U1-versus-U2 buffer delay and trace length - per part, drifting with
# temperature. Moving to the falling edge took that to +16.5 ns.
#
# If BCLKEDGE is ever set to 1, this stays FALLING. Re-read Table 5 before
# changing it, and do not re-derive it from BCLKEDGE.
bclkedge = (written.get(0x04, 0) >> 6) & 1
launch_rising = bool(re.search(r'elsif\s+rising_edge\(clk_in\)', tm))
chk("LRCLK launches on BCLK falling edge", launch_rising, False,
    "Table 5: LRCLK is sampled on BCLK RISING (tALS/tALH) regardless of "
    "BCLKEDGE=%d, so tdm8_master must launch on falling; it launches on %s"
    % (bclkedge, "rising" if launch_rising else "falling"))

# Whatever the shape, both consumers must edge-detect it rather than test the
# level - a level test is only correct for the one-BCLK pulse.
for name, src in (("tdm8_rx", trx), ("tdm16_merge", rd(RTL / "tdm16_merge.vhd"))):
    chk("%s edge-detects sync" % name,
        bool(re.search(r"=\s*'1'\s+and\s+\w+\s*=\s*'0'", src)), True,
        "must not level-test LRCLK")

# ------------------------------------------------- 8. IP/UDP header fields ---
# The IPv4 header checksum used to be the literal IP_CHECKSUM in udp_tx_core,
# and this block recomputed it. It is now work.net_pkg.ipv4_checksum, evaluated
# at elaboration from C_FPGA_IP and C_PC_IP, with static assertions in
# top_system that FAIL THE BUILD on a wrong value - a stronger guard than this
# script can offer, and one that cannot be skipped.
#
# What is checked here instead is the part Quartus cannot see: that the
# addresses compiled into the RTL are the ones the host tools will talk to.
# C_FPGA_IP is an expression (x"C0A803" & C_NODE), so it is reconstructed from
# its parts rather than read as a literal - the old regex expected a literal and
# silently stopped matching when the expression was introduced, which is exactly
# the kind of drift this file exists to catch.
_sub = re.search(r'x"C0A8([0-9A-Fa-f]{2})"\s*&\s*std_logic_vector\(to_unsigned\(100 \+ C_NODE', top)
_node = re.search(r'constant\s+C_NODE\s*:\s*integer\s+range 1 to 4\s*:=\s*(\d+)', top)
_pc = re.search(r'C_PC_IP\s*:\s*std_logic_vector\(31 downto 0\)\s*:=\s*x"([0-9A-Fa-f]{8})"', top)

if _sub and _node and _pc:
    _third = int(_sub.group(1), 16)
    _n = int(_node.group(1))
    rtl_board = "192.168.%d.%d" % (_third, 100 + _n)
    _pcv = int(_pc.group(1), 16)
    rtl_host = "%d.%d.%d.%d" % (_pcv >> 24, (_pcv >> 16) & 0xFF,
                                (_pcv >> 8) & 0xFF, _pcv & 0xFF)

    import ctrl as _ctrl
    chk("board IP vs ctrl.py", _ctrl.node_ip(_n), rtl_board,
        "C_NODE=%d in top_system -> %s; ctrl.node_ip(%d) must agree "
        "(docs/CHANGING_IP.md)" % (_n, rtl_board, _n))
    chk("host IP vs ctrl.py", _ctrl.HOST_IP, rtl_host,
        "C_PC_IP in top_system is %s; ctrl.HOST_IP must agree, and the PC's "
        "adapter must actually be set to it" % rtl_host)
    chk("board subnet is known", rtl_board.rsplit(".", 1)[0] in _ctrl.KNOWN_SUBNETS,
        True, "ctrl.KNOWN_SUBNETS must list %s or discovery cannot find this "
        "board" % rtl_board.rsplit(".", 1)[0])
    chk("host on board subnet", rtl_host.rsplit(".", 1)[0],
        rtl_board.rsplit(".", 1)[0],
        "a board cannot deliver to a host on another subnet, and C_PC_IP is "
        "also the ARP filter")
else:
    FAIL.append(("IP address extraction", "no match", "regex matches",
                 "C_FPGA_IP / C_PC_IP / C_NODE not in the expected form"))


# IP/UDP total length used to be literal bytes in the byte_cnt case statement
# and is now derived from PAYLOAD_BYTES, so read the expression's inputs rather
# than the emitted bytes. Same drift as the checksum above: the old regex
# matched literals that no longer exist and the check quietly did nothing.
_pb = re.search(r'PAYLOAD_BYTES\s*:\s*integer\s*:=\s*(\d+)', utx)
if not _pb:
    _pb = re.search(r'PAYLOAD_BYTES\s*:\s*integer\s*:=\s*(\d+)', top)
_payload_rtl = int(_pb.group(1)) if _pb else None

chk("PAYLOAD_BYTES vs host", _payload_rtl, pyconst(mon, "PAYLOAD_LEN"),
    "udp_tx_core PAYLOAD_BYTES drives IP and UDP length; udp_monitor "
    "PAYLOAD_LEN must match or the host rejects every packet")

ip_total  = 20 + 8 + (_payload_rtl or 0)
udp_total = 8 + (_payload_rtl or 0)
chk("IPv4 total length", ip_total, 20 + 8 + pyconst(mon, "PAYLOAD_LEN"),
    "20 IP + 8 UDP + payload")
chk("UDP length", udp_total, 8 + pyconst(mon, "PAYLOAD_LEN"), "8 UDP + payload")

# ------------------------------------------------- 9. frame counter range ----
# bit_cnt must be able to REACH C_FRAME_BCLKS - 1, or the frame boundary never
# fires and LRCLK stops toggling with no other symptom. A hardcoded "range 0 to
# 255" survives 192 and 256 and dies silently at anything longer.
_bc = re.search(r'signal bit_cnt\s*:\s*integer range 0 to ([^:=]+?)\s*:=', tm)
_bc_txt = _bc.group(1).strip() if _bc else "?"
if _bc_txt == "C_FRAME_BCLKS - 1":
    _top = div - 1
else:
    try:
        _top = int(_bc_txt)
    except ValueError:
        _top = -1
chk("bit_cnt reaches frame end", _top >= div - 1, True,
    "tdm8_master bit_cnt range 0 to %s, needs to reach %d" % (_bc_txt, div - 1))

# --------------------------------------------------------------- report ------
w = max(len(n) for n, *_ in OK + [(f[0],) for f in FAIL])
print("=" * 78)
print("VHDL <-> PYTHON <-> DATASHEET CONSISTENCY")
print("=" * 78)
for n, got, note in OK:
    print("  OK    %-*s = %-22s %s" % (w, n, got, note))
if FAIL:
    print()
    for n, got, want, note in FAIL:
        print("  FAIL  %-*s = %-22s want %s   %s" % (w, n, got, want, note))
print("=" * 78)
print("%d checks passed, %d failed" % (len(OK), len(FAIL)))
sys.exit(1 if FAIL else 0)
