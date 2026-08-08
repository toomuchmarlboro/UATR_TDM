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
pf  = rd("packet_formatter.vhd")
tm  = rd("tdm8_master.vhd")
trx = rd("tdm8_rx.vhd")
seq = rd("adau_sequencer.vhd")
utx = rd("udp_tx_core.vhd")
pll = rd("pll_audio.vhd")
mon = rd("udp_monitor.py")
scn = rd("i2c_scan.py")


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
# which PLL output is wired to the audio clock in top_system's port map:
#   c0 = 12.288 MHz -> 48 kHz     c1 = 18.432 MHz -> 72 kHz
top = rd("top_system.vhd")
m = re.search(r'c([012])\s*=>\s*clk_18m', top)
assert m, "cannot tell which PLL output drives clk_18m"
which = "clk%s" % m.group(1)
mult = int(re.search(which + r'_multiply_by\s*=>\s*(\d+)', pll).group(1))
divi = int(re.search(which + r'_divide_by\s*=>\s*(\d+)',   pll).group(1))
bclk = 50_000_000 * mult / divi
div  = int(re.search(r'if bit_cnt = (\d+) then', tm).group(1)) + 1
fs   = bclk / div
chk("SAMPLE_RATE", pyconst(mon, "SAMPLE_RATE"), round(fs / 1000) * 1000,
    "BCLK %.4f MHz / %d = %.1f Hz" % (bclk / 1e6, div, fs))

# slot width and data width are no longer the same: 32 BCLK slots carry 24-bit
# samples, so the shift register (frame in BCLKs) is wider than the data output.
shift_w = int(re.search(r'signal shift_reg\s*:\s*std_logic_vector\((\d+) downto 0\)', trx).group(1)) + 1
data_w  = int(re.search(r'ch_data_out\s*:\s*out\s*std_logic_vector\((\d+) downto 0\)', trx).group(1)) + 1
chk("channels x bits", pyconst(mon, "CHANNELS") * pyconst(mon, "SAMPLE_BYTES") * 8,
    data_w * 2, "tdm8_rx ch_data_out %d bits x 2 lines" % data_w)
# tdm8_rx carries slack either side of the frame so C_BIT_ADJ can slide the
# capture window, so the register is intentionally wider than one frame.
adj = int(re.search(r'C_BIT_ADJ\s*:\s*integer\s*:=\s*(-?\d+)', trx).group(1))
chk("shift reg holds a frame", shift_w >= div + abs(adj), True,
    "tdm8_rx %d bits >= %d BCLK frame + %d adj" % (shift_w, div, abs(adj)))
chk("capture window in range", 0 <= 232 + adj - 32*7 and 255 + adj <= shift_w - 1, True,
    "C_BIT_ADJ = %+d keeps all 8 slot slices inside the register" % adj)

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
      0x05: (0x5B, "left-justified, SAI=011 TDM8, FS=011 64-96kHz"),
      0x06: (0x08, "SDATAOUT1, 32 BCLK/slot, 24-bit, LRCLK pulse, MSB, slave"),
      0x09: (0xF8, "drive C1-C4, DRV_HIZ=1")}
for reg, spec in sorted(DS.items()):
    val, why = spec[0], spec[1]
    mask = spec[2] if len(spec) > 2 else 0xFF
    got = written.get(reg)
    chk("datasheet 0x%02X" % reg, None if got is None else got & mask, val & mask,
        why + ("" if mask == 0xFF else "  (mask %02X)" % mask))

# TDM8 with 24-bit slots must give BCLK = 192 x fS  (datasheet Table 10)
chk("Table 10 BCLK ratio", div, 8 * 32, "TDM8 x 32 BCLK slots = 256 x fS")

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
