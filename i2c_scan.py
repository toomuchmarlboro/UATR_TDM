#!/usr/bin/env python3
"""
TDM_UATR I2C diagnostics.

The FPGA performs the bus scan and register readback in hardware at boot and
publishes the results in spare bytes of every UDP audio packet. This tool reads
one packet and decodes just that: bus health, the address sweep, which ADCs
answered, and whether their configuration actually took effect.

    python i2c_scan.py              # decode and report
    python i2c_scan.py -v           # also dump the raw diagnostic bytes

Exit code is 0 if the scan was valid, 1 if the bus was jammed or no packets
arrived - so it can gate a script.

IMPORTANT: the scan is a ONE-SHOT taken at boot, roughly 150 ms after the FPGA
comes out of reset. Running this tool again re-reads the same latched result. To
genuinely re-scan the bus you must power-cycle or reprogram the FPGA.

Diagnostic byte layout, from packet_formatter.vhd:
    header byte  8      raw readback of ADAU 0x01  PLL_CONTROL
    header byte  9      raw readback of ADAU 0x09  SAI_OVERTEMP
    frame 0 byte 0      bus status bits
    frame 1 byte 0      output self-test bits
    frame 2 byte 0      count of addresses that answered
    frame 3 byte 0      first address that answered
    frame 4 byte 0      [7:4] PLL locked per part, [3:0] answered per part
    frame 7 byte 0      [7] scan invalid, [6] recovery ran, [5:0] register verify
"""

import argparse
import socket
import sys

MAGIC       = bytes([0xAD, 0xA1, 0x97, 0x78])
HDR_LEN     = 10
FRAME_LEN   = 50
FRAMES_PKT  = 8
PAYLOAD_LEN = HDR_LEN + FRAMES_PKT * FRAME_LEN      # 410

# 7-bit address, refdes, TDM line position, FPGA channels
DEVICES = [(0x11, "U19", "TDM1 slot 1-4", "ch  1-4"),
           (0x31, "U20", "TDM1 slot 5-8", "ch  5-8"),
           (0x51, "U37", "TDM2 slot 1-4", "ch  9-12"),
           (0x71, "U38", "TDM2 slot 5-8", "ch 13-16")]

# register, name, value written, datasheet reset value
VERIFY = [(0x00, "M_POWER",         0x01, 0x00),
          (0x01, "PLL_CONTROL",     0x01, 0x41),
          (0x04, "BLOCK_POWER_SAI", 0x3F, 0x3F),
          (0x05, "SAI_CTRL0",       0x5A, 0x02),
          (0x06, "SAI_CTRL1",       0x08, 0x00),
          (0x09, "SAI_OVERTEMP",    0xF8, 0xF0)]


def grab(port, bind, timeout):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((bind, port))
    s.settimeout(timeout)
    try:
        for _ in range(20):                 # skip any runt/partial datagram
            p = s.recv(2048)
            if len(p) == PAYLOAD_LEN and p[0:4] == MAGIC:
                return p
        return None
    except socket.timeout:
        return None
    finally:
        s.close()


def main():
    ap = argparse.ArgumentParser(description="TDM_UATR I2C diagnostics")
    ap.add_argument("-p", "--port", type=int, default=5005)
    ap.add_argument("-b", "--bind", default="")
    ap.add_argument("-t", "--timeout", type=float, default=3.0)
    ap.add_argument("-v", "--verbose", action="store_true",
                    help="dump the raw diagnostic bytes")
    a = ap.parse_args()

    p = grab(a.port, a.bind, a.timeout)
    if p is None:
        print("No valid packet on %s:%d within %.1f s."
              % (a.bind or "0.0.0.0", a.port, a.timeout))
        print("  - is the FPGA powered and the link up?")
        print("  - is this PC on 192.168.1.0/24 at the address in C_PC_IP?")
        print("  - Windows Firewall silently drops inbound UDP; allow python.")
        return 1

    rd_pll   = p[8]
    rd_ot    = p[9]
    status   = p[HDR_LEN + 0 * FRAME_LEN]
    selftest = p[HDR_LEN + 1 * FRAME_LEN]
    count    = p[HDR_LEN + 2 * FRAME_LEN]
    first    = p[HDR_LEN + 3 * FRAME_LEN]
    masks    = p[HDR_LEN + 4 * FRAME_LEN]
    vbyte    = p[HDR_LEN + 7 * FRAME_LEN]

    answered = masks & 0x0F
    locked   = (masks >> 4) & 0x0F
    vmask    = vbyte & 0x3F
    recovered = bool(vbyte & 0x40)
    invalid   = bool(vbyte & 0x80) or count > 8

    if a.verbose:
        print("raw: rd_pll=%02X rd_ot=%02X status=%02X selftest=%02X "
              "count=%d first=%02X masks=%02X vbyte=%02X"
              % (rd_pll, rd_ot, status, selftest, count, first, masks, vbyte))
        print()

    bar = "=" * 66
    print(bar)
    print("I2C BUS SCAN AND DIAGNOSTICS")
    print(bar)

    # ---------------------------------------------------------------- verdict
    if invalid:
        print()
        print("  *** SCAN INVALID - THE BUS WAS NOT IDLE ***")
        print()
        print("  %d addresses appeared to answer. There are only four ADCs on" % count)
        print("  this board, so this cannot be real. A stuck-low SDA makes every")
        print("  acknowledge slot read as an ACK, so every address looks occupied")
        print("  and every read returns 0x00.")
        print()
        print("  Nothing else below can be trusted. Fix the bus and re-run:")
        print("    - is a 2.2k pull-up fitted on SDA and SCL near the ADCs?")
        print("      J19 pins 1 and 2 are the convenient tap. A pull-up only at")
        print("      the FPGA end leaves the ADCs seeing slow edges, and a slave")
        print("      that mis-samples a bit wedges holding SDA low.")
        print("    - power-cycle rather than reprogram, so the ADCs reset cleanly")
        print(bar)
        return 1

    # ---------------------------------------------------------- physical layer
    print()
    print("  BUS HEALTH")
    if not selftest & 0x80:
        print("    self test did not run (old bitstream?)")
    else:
        print("    FPGA drives SCL low   %s"
              % ("yes" if selftest & 0x01 else "*** NO ***"))
        print("    FPGA drives SDA low   %s"
              % ("yes" if selftest & 0x02 else "*** NO ***"))
    if status & 0x80:
        print("    line held low now     %s%s%s"
              % ("yes" if status & 0x02 else "no",
                 "  SCL" if status & 0x04 else "",
                 "  SDA" if status & 0x08 else ""))
        print("    any NACK seen         %s" % ("YES" if status & 0x01 else "no"))
        print("    boot sequence         %s"
              % ("completed" if status & 0x10 else "still running or retrying"))
        # bit 5: sticky, set if the FPGA's audio PLL has ever lost lock since
        # power-up. Everything downstream - MCLK, BCLK, LRCLK, the whole TDM
        # frame - is derived from that one PLL, so a drop here invalidates any
        # conclusion drawn about the ADCs. The design counted these internally
        # and published them nowhere until 2026-08-10.
        print("    audio PLL lock        %s"
              % ("*** HAS LOST LOCK since power-up ***" if status & 0x20
                 else "never lost since power-up"))
    if recovered:
        print("    NOTE: bus recovery had to clock a jammed slave free")

    # ------------------------------------------------------------- the sweep
    print()
    print("  ADDRESS SWEEP   (all 128 7-bit addresses probed)")
    print("    answered              %d" % count)
    if count:
        print("    lowest address        0x%02X" % first)
    print()
    print("    addr  part  position         channels   scan     PLL")
    print("    " + "-" * 56)
    for i, (addr, ref, pos, chs) in enumerate(DEVICES):
        alive = bool(answered & (1 << i))
        print("    0x%02X  %-4s  %-15s  %-9s  %-7s  %s"
              % (addr, ref, pos, chs,
                 "ALIVE" if alive else "silent",
                 ("locked" if locked & (1 << i) else "NOT LOCKED")
                 if alive else "-"))

    missing = [d[1] for i, d in enumerate(DEVICES) if not answered & (1 << i)]
    if missing:
        print()
        print("    %s did not answer. A part that is powered but silent on I2C"
              % ", ".join(missing))
        print("    usually has unbonded joints on pins 17/18 (SDA/SCL) - the")
        print("    0.5 mm pitch QFN is easy to get partially wetted.")

    # -------------------------------------------------------- register verify
    print()
    print("  REGISTER VERIFY   (read back from 0x%02X)" % first)
    print("    reg   name             wrote  reset  result")
    print("    " + "-" * 52)
    for i, (reg, name, wrote, rst) in enumerate(VERIFY):
        ok = bool(vmask & (1 << i))
        print("    0x%02X  %-15s  0x%02X   0x%02X   %s"
              % (reg, name, wrote, rst, "OK" if ok else "*** MISMATCH ***"))
    if vmask != 0x3F:
        print()
        print("    A mismatch means the value read back was not the value written.")
        print("    If it equals the reset column, the write never took effect.")

    # ------------------------------------------------------------- raw values
    print()
    print("  RAW READBACKS")
    print("    0x01 PLL_CONTROL   0x%02X   CLK_S=%d MCS=%s  PLL_LOCK=%s"
          % (rd_pll, (rd_pll >> 4) & 1, format(rd_pll & 0x07, "03b"),
             "set" if rd_pll & 0x80 else "clear"))
    print("    0x09 SAI_OVERTEMP  0x%02X   drive=%s DRV_HIZ=%d  OT=%s"
          % (rd_ot, format((rd_ot >> 4) & 0xF, "04b"), (rd_ot >> 3) & 1,
             "*** SHUTDOWN ***" if rd_ot & 1 else "normal"))

    print()
    print("  Reminder: this is the boot-time snapshot. Power-cycle to re-scan.")
    print(bar)
    return 0


if __name__ == "__main__":
    sys.exit(main())
