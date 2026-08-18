#!/usr/bin/env python3
"""
Control interface for the TDM_UATR board, and a self-test for the UDP receive
path.

The FPGA's udp_rx_core accepts a plain UDP datagram addressed to the board's
IP - there is no port filtering - carrying:

    payload[0]   bits [3:2] ADC select 0-3     (U19, U20, U37, U38)
                 bits [1:0] channel select 0-3 (that ADC's ch 1-4)
    payload[1]   gain byte, written to register 0x0A-0x0D of the selected part

adau_sequencer picks it up in ST_IDLE and writes it over I2C.

Gain encoding (ADAU1978 Table 25): 0x00 = +60 dB, steps of -0.375 dB,
0xA0 = 0 dB, 0xFE = -35.625 dB, 0xFF = mute.

Usage
    python ctrl.py --test              prove the receive path works
    python ctrl.py --set 1 -6          channel 1 to -6 dB
    python ctrl.py --set 5 mute
    python ctrl.py --all 0             every channel to 0 dB

--test is the important one. It measures a channel, mutes it, measures again,
restores it, and tells you whether the FPGA acted. Nothing else in the control
path is worth building until that passes.
"""

import argparse
import socket
import sys
import time

import numpy as np

sys.path.insert(0, __file__.rsplit("\\", 1)[0] if "\\" in __file__ else ".")
import udp_monitor as um

FPGA_IP   = "192.168.1.101"      # C_FPGA_IP in top_system.vhd
FPGA_PORT = 5005                 # any port: udp_rx_core does not filter on it
STREAM_PORT = 5005

MUTE = 0xFF
ZERO_DB = 0xA0


def gain_byte(db):
    """dB -> register value. +60 dB at 0x00, -0.375 dB per step."""
    if db is None:
        return MUTE
    v = int(round((60.0 - float(db)) / 0.375))
    return max(0, min(0xFE, v))          # 0xFF is mute, keep it out of range


def gain_db(b):
    return None if b == MUTE else 60.0 - b * 0.375


def send_gain(ch, byte_val, flags=None, ip=FPGA_IP, port=FPGA_PORT):
    """ch is 1-16 as printed by the monitor.

    flags is the optional 3rd payload byte; bit 0 enables 48 V phantom power.
    Pass None to send the original 2-byte packet, which leaves the FPGA's flag
    state untouched. The GUI passes it on every command so phantom state is
    carried explicitly and never depends on what the board happened to latch.
    """
    if not 1 <= ch <= 16:
        raise ValueError("channel must be 1-16")
    idx = ch - 1
    adc, sub = idx // 4, idx % 4
    pkt = [(adc << 2) | sub, byte_val]
    if flags is not None:
        pkt.append(flags & 0xFF)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.sendto(bytes(pkt), (ip, port))
    finally:
        s.close()
    return adc, sub


def send_flags(flags, ip=FPGA_IP, port=FPGA_PORT):
    """Set the control flags without changing a gain.

    Re-sends channel 1's current setting is not possible from here, so this
    addresses ADC 0 channel 0 with 0xA0 (0 dB). Harmless if channel 1 is
    already at 0 dB; the GUI uses its own slider value instead.
    """
    return send_gain(1, ZERO_DB, flags=flags, ip=ip, port=port)


def decode(payload):
    body = payload[um.HDR_LEN:]
    n = len(body) // um.FRAME_LEN
    if n == 0:
        return None
    raw = np.frombuffer(body[:n * um.FRAME_LEN], dtype=np.uint8)
    raw = raw.reshape(n, um.FRAME_LEN)[:, 2:]
    raw = raw.reshape(n, um.CHANNELS, um.SAMPLE_BYTES).astype(np.int32)
    v = (raw[:, :, 0] << 16) | (raw[:, :, 1] << 8) | raw[:, :, 2]
    return np.where(v & 0x800000, v - 0x1000000, v)


def measure(ch, secs=1.5, port=STREAM_PORT):
    """RMS of one channel (1-16), or None if no packets arrived."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 16 << 20)
    except OSError:
        pass
    s.bind(("0.0.0.0", port))
    s.settimeout(0.6)
    acc, t0 = [], time.time()
    while time.time() - t0 < secs:
        try:
            d, _ = s.recvfrom(2048)
        except socket.timeout:
            break
        if len(d) >= um.PAYLOAD_LEN and d[:4] == um.MAGIC:
            b = decode(d)
            if b is not None:
                acc.append(b)
    s.close()
    if not acc:
        return None
    x = np.concatenate(acc, 0).astype(float)
    return float(np.sqrt(np.mean(x[:, ch - 1] ** 2)))


def self_test(ch):
    print("UDP RECEIVE PATH TEST   channel %d -> %s" % (ch, FPGA_IP))
    print("-" * 58)
    base = measure(ch)
    if base is None:
        print("  no packets received.")
        print("  The board is not streaming - power it up and confirm")
        print("  udp_monitor.py sees traffic before running this.")
        return 2
    print("  baseline RMS        %10.1f" % base)

    if base < 2.0:
        print()
        print("  channel %d is essentially silent (RMS %.1f), so muting it" % (ch, base))
        print("  cannot show a difference. Pick a channel that is carrying")
        print("  signal:  python ctrl.py --test --channel 3")
        return 2

    send_gain(ch, MUTE)
    time.sleep(0.8)
    muted = measure(ch)
    print("  after mute  (0xFF)  %10.1f" % (muted if muted is not None else -1))

    send_gain(ch, ZERO_DB)
    time.sleep(0.8)
    back = measure(ch)
    print("  after restore(0xA0) %10.1f" % (back if back is not None else -1))
    print()

    if muted is not None and muted < base * 0.2:
        print("  *** RECEIVE PATH WORKS ***")
        print("  The FPGA parsed the packet and wrote the gain register over I2C.")
        if back is not None and back < base * 0.2:
            print("  NOTE: the channel did not come back. Gain is left at 0 dB;")
            print("        re-run or send --set %d 0 to restore." % ch)
        return 0

    print("  no change - the FPGA did not act on the packet.")
    print("  Things to check, in order:")
    print("    - is the PC on 192.168.1.10 and the FPGA on 192.168.1.101?")
    print("    - arp -a should map 192.168.1.101 to de-ad-be-ef-00-01")
    print("    - rmii_rx / udp_rx_core have never been proven on hardware;")
    print("      this is the first thing that would exercise them.")
    return 1


def parse_db(tok):
    return None if str(tok).lower() in ("mute", "off") else float(tok)


def main():
    ap = argparse.ArgumentParser(description="TDM_UATR control interface")
    ap.add_argument("--test", action="store_true", help="prove the receive path")
    ap.add_argument("--channel", type=int, default=1, help="channel for --test")
    ap.add_argument("--set", nargs=2, metavar=("CH", "DB"),
                    help="set one channel, e.g. --set 3 -6  or  --set 5 mute")
    ap.add_argument("--all", metavar="DB", help="set every channel")
    ap.add_argument("--ip", default=FPGA_IP)
    a = ap.parse_args()

    if a.test:
        sys.exit(self_test(a.channel))
    if a.set:
        ch, db = int(a.set[0]), parse_db(a.set[1])
        b = gain_byte(db)
        adc, sub = send_gain(ch, b, ip=a.ip)
        print("ch %d -> ADC %d ch %d, reg 0x%02X = 0x%02X (%s)"
              % (ch, adc, sub, 0x0A + sub, b,
                 "mute" if db is None else "%+.3f dB" % gain_db(b)))
        return
    if a.all is not None:
        db = parse_db(a.all)
        b = gain_byte(db)
        for ch in range(1, 17):
            send_gain(ch, b, ip=a.ip)
            time.sleep(0.02)
        print("all 16 channels -> 0x%02X (%s)"
              % (b, "mute" if db is None else "%+.3f dB" % gain_db(b)))
        return
    ap.print_help()


if __name__ == "__main__":
    main()
