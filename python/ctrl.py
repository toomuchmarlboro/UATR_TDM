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
    python ctrl.py --phantom status    what is 48 V actually doing right now
    python ctrl.py --phantom on

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

# ---------------------------------------------------------------- addressing
# THE SUBNET LIVES HERE, IN ONE PLACE.
#
# Changing the array's subnet is a two-sided edit: SUBNET below and C_FPGA_IP /
# C_PC_IP in rtl/top_system.vhd, which also feed the compile-time IPv4 checksum
# assertions. check_sync.py asserts the two sides agree, so they cannot drift
# silently. Full procedure: docs/CHANGING_IP.md
#
# Moved 192.168.1.x -> 192.168.3.x on 2026-09-07. Boards flashed with older
# images are still on 192.168.1.x, so BOTH are supported: SUBNET is the default
# for outbound control, and KNOWN_SUBNETS is what the discovery helpers sweep.
SUBNET        = "192.168.3"
KNOWN_SUBNETS = ["192.168.3", "192.168.1"]

HOST_IP   = SUBNET + ".10"       # C_PC_IP: where audio is sent, and the ARP filter

FPGA_IP   = SUBNET + ".101"      # C_FPGA_IP in top_system.vhd, node 1
FPGA_PORT = 5005                 # any port: udp_rx_core does not filter on it
STREAM_PORT = 5005


def node_ip(n, subnet=None):
    """Node number -> board IP. Mirrors C_NODE in top_system.vhd."""
    return "%s.%d" % (subnet or SUBNET, 100 + int(n))


def node_ips(n):
    """Every address node n could be at, across all known subnets.

    A board keeps whatever address its flashed image was built with, so during
    a subnet migration the array can legitimately be split across two. Callers
    that want to find a board rather than assume one should try these in order.
    """
    return ["%s.%d" % (sub, 100 + int(n)) for sub in KNOWN_SUBNETS]


def find_node(n, timeout=0.6):
    """Return the address node n is actually answering on, or None.

    Listens on that node's stream port and reads the source address of the
    first packet. That is authoritative - it is where the board really is -
    and needs no ARP, no ping, and no assumption about the host's own subnet.

    RECEIVING never needed this: capture() binds INADDR_ANY, so audio arrives
    from any subnet already. SENDING does - a gain or phantom command goes TO an
    address, so it has to be the right one. Use this when the board's subnet is
    not known, e.g. part-way through a migration.
    """
    import socket as _s
    sock = _s.socket(_s.AF_INET, _s.SOCK_DGRAM)
    sock.setsockopt(_s.SOL_SOCKET, _s.SO_REUSEADDR, 1)
    try:
        sock.bind(("", node_stream_port(n)))
        sock.settimeout(timeout)
        _, addr = sock.recvfrom(2048)
        return addr[0]
    except (OSError, _s.timeout):
        return None
    finally:
        sock.close()


def resolve_node(n, timeout=0.6):
    """Node number -> the address to SEND control commands to.

    Prefers the address the board is actually transmitting from; falls back to
    the configured SUBNET if it is silent (a board being configured before it
    streams, or one whose stream port is held by another process).

    This is what makes control work on 192.168.1.x and 192.168.3.x without a
    flag: a board built with an old image answers from its own address, and the
    command follows it there.
    """
    return find_node(n, timeout) or node_ip(n)


def node_stream_port(n):
    """Node number -> the port that board's audio arrives on.

    Each board transmits on its own port so the host can open one socket per
    board. udp_monitor.capture() uses recv(), not recvfrom(), so boards sharing
    a port would interleave their sequence numbers into a single socket and the
    loss report would be meaningless.
    """
    return 5004 + int(n)

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


# Frame 1's byte 0 is dbg_status2, which carries the 48 V phantom readback in
# bits 6:3. See the comment on dbg_status2_int in top_system.vhd.
#
# Deliberately the frame NUMBER and not the byte offset. Anything at module
# level here is extracted verbatim by make_gui_standalone.py and lands ABOVE
# the `um` stand-in it builds, so a module-level `um.HDR_LEN` would import
# cleanly in this file and raise NameError in the generated one. The offset is
# formed inside phantom_state, where `um` resolves at call time.
PHANTOM_FRAME = 1


def phantom_state(pkt):
    """Decode the 48 V readback out of one audio packet.

    -> dict, or None if the packet is unusable or the bitstream predates this.

    Phantom power is otherwise write-only, and the command path is not a record
    of the state: the FPGA clears udp_flags on any reset, and a restarted GUI
    starts with its checkbox off while the board may still be driving 48 V. So
    the only trustworthy answer comes from the board itself, in every packet.

    Keys:
        on          the en_48v pin as actually driven
        requested   the host asked for it (udp_flags bit 0)
        staged      the staged power-up passed 1000 ms
        permitted   C_ENABLE_48V is true in this build
    'on' is the AND of the other three, so which one is false names the cause.

    ASSERTED, NOT MEASURED. en_48v is an FPGA output with no sense line back, so
    a dead supply or an open enable trace still reports on.
    """
    if len(pkt) < um.PAYLOAD_LEN or pkt[:4] != um.MAGIC:
        return None
    b = pkt[um.HDR_LEN + PHANTOM_FRAME * um.FRAME_LEN]
    if not b & 0x80:            # marker bit: this byte is populated
        return None
    return {"on":        bool(b & 0x40),
            "requested": bool(b & 0x20),
            "staged":    bool(b & 0x10),
            "permitted": bool(b & 0x08)}


def phantom_reason(st):
    """One line explaining a phantom_state dict, naming the gate that is off."""
    if st is None:
        return "unknown - no packet, or a bitstream older than the readback"
    if st["on"]:
        return "ON - the FPGA is asserting EN_48V"
    if not st["permitted"]:
        return "off - C_ENABLE_48V is false in this build, so it cannot come on"
    if not st["staged"]:
        return "off - the staged power-up has not reached 1000 ms yet"
    if not st["requested"]:
        return "off - not requested. An FPGA reset clears the request, so this " \
               "is also what you see after the board has rebooted under a " \
               "GUI that still shows phantom enabled"
    # All three gates set and the pin still low is the watchdog signature. It
    # needs no status bit of its own precisely because nothing else produces
    # this combination: the host asked for 48 V, the build allows it, the
    # power-up timer reached it, and the FPGA is overriding all three.
    return ("off - the phantom WATCHDOG has tripped. The FPGA has not heard a "
            "flags-carrying packet within C_PHANTOM_TIMEOUT_S and has dropped "
            "48 V on its own. Send any command with a flags byte to restore it")


def read_phantom(port=STREAM_PORT, bind="", timeout=3.0):
    """Wait for one audio packet and return its phantom_state, or None."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((bind, port))
    s.settimeout(timeout)
    t0 = time.time()
    try:
        while time.time() - t0 < timeout:
            try:
                d, _ = s.recvfrom(2048)
            except socket.timeout:
                return None
            st = phantom_state(d)
            if st is not None:
                return st
    finally:
        s.close()
    return None


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


def self_test(ch, ip=FPGA_IP, stream_port=STREAM_PORT):
    print("UDP RECEIVE PATH TEST   channel %d -> %s  (stream port %d)"
          % (ch, ip, stream_port))
    print("-" * 58)
    base = measure(ch, port=stream_port)
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

    send_gain(ch, MUTE, ip=ip)
    time.sleep(0.8)
    muted = measure(ch, port=stream_port)
    print("  after mute  (0xFF)  %10.1f" % (muted if muted is not None else -1))

    send_gain(ch, ZERO_DB, ip=ip)
    time.sleep(0.8)
    back = measure(ch, port=stream_port)
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
    print("    - is the PC on %s and the FPGA on %s?" % (HOST_IP, ip))
    print("    - arp -a should map %s to de-ad-be-ef-00-%02d"
          % (ip, int(ip.rsplit(".", 1)[1]) - 100))
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
    ap.add_argument("--phantom", choices=("on", "off", "status"),
                    help="48 V phantom power. 'status' reads it back from the "
                         "board and does not change anything.")
    ap.add_argument("--node", type=int, default=1, choices=(1, 2, 3, 4),
                    help="which board (1-4). Sets both the control IP and the "
                         "audio stream port. --ip overrides the address.")
    ap.add_argument("--ip", default=None,
                    help="override the board IP derived from --node")
    a = ap.parse_args()

    ip     = a.ip or node_ip(a.node)
    stream = node_stream_port(a.node)

    if a.phantom:
        if a.phantom != "status":
            # There is no flags-only packet: the FPGA parses one command format,
            # so carrying the flag means also writing a gain. send_flags picks
            # channel 1 at 0 dB, which is why that is called out here.
            send_flags(0x01 if a.phantom == "on" else 0x00, ip=ip)
            print("sent 48 V %s  (channel 1 also set to 0 dB - the flags byte "
                  "rides on a gain command)" % a.phantom)
            time.sleep(0.5)
        st = read_phantom(port=stream)
        print("48 V readback: %s" % phantom_reason(st))
        if st is None:
            # Do not let "no packet" be read as "old bitstream". On Windows two
            # sockets can both bind this port with SO_REUSEADDR while only ONE
            # of them receives, so a mixer GUI open on this node silently takes
            # the whole stream and this returns nothing at all.
            print("  nothing arrived on port %d in 3 s. Close any mixer_gui or"
                  % stream)
            print("  udp_monitor already listening on that port and re-run -")
            print("  two sockets can bind it but only one gets the packets.")
        if st is not None:
            print("  pin %s | requested %s | staged %s | build permits %s"
                  % tuple("yes" if st[k] else "no"
                          for k in ("on", "requested", "staged", "permitted")))
        return

    if a.test:
        sys.exit(self_test(a.channel, ip=ip, stream_port=stream))
    if a.set:
        ch, db = int(a.set[0]), parse_db(a.set[1])
        b = gain_byte(db)
        adc, sub = send_gain(ch, b, ip=ip)
        print("ch %d -> ADC %d ch %d, reg 0x%02X = 0x%02X (%s)"
              % (ch, adc, sub, 0x0A + sub, b,
                 "mute" if db is None else "%+.3f dB" % gain_db(b)))
        return
    if a.all is not None:
        db = parse_db(a.all)
        b = gain_byte(db)
        for ch in range(1, 17):
            send_gain(ch, b, ip=ip)
            time.sleep(0.02)
        print("all 16 channels -> 0x%02X (%s)"
              % (b, "mute" if db is None else "%+.3f dB" % gain_db(b)))
        return
    ap.print_help()


if __name__ == "__main__":
    main()
