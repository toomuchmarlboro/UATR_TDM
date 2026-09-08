#!/usr/bin/env python3
"""
Find every soundcard on the network and report what each one is doing.

    python discover.py                 listen on all four stream ports
    python discover.py -s 3            listen 3 s per board (default 2)
    python discover.py --nodes 1,3     only these

Answers, per board, without needing to know anything in advance:

    which SUBNET it is on      - read from the packet's source address
    which SAMPLE RATE it runs  - measured from the packet rate
    whether it is HEALTHY      - sequence gaps, magic word, payload length

WHY THIS EXISTS. A board's IP and sample rate are both baked into its flashed
image, and neither is announced in the packet - the payload is byte-identical
at 96 kHz and 24 kHz. So an array part-way through a migration, or a board
flashed with the wrong image, is invisible to any tool that assumes what it is
talking to. This measures instead of assuming, which is the only way to catch a
board that is working perfectly and is not the board you thought.

It is passive: it binds the stream ports and listens. Nothing is transmitted, so
it cannot disturb a capture in progress, and it works whether the boards are on
192.168.3.x, 192.168.1.x, or a mixture.
"""

import argparse
import socket
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ctrl
import udp_monitor as um


def probe(node, seconds=2.0):
    """Listen on one node's stream port. Returns a dict, or None if silent."""
    port = ctrl.node_stream_port(node)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 8 << 20)
    except OSError:
        pass
    try:
        s.bind(("", port))
    except OSError as e:
        s.close()
        return {"node": node, "port": port, "error": "cannot bind: %s" % e}
    s.settimeout(min(2.0, seconds))

    pkts, srcs = [], set()
    try:
        first, addr = s.recvfrom(2048)
    except (socket.timeout, OSError):
        s.close()
        return None
    pkts.append(first)
    srcs.add(addr[0])

    t0 = time.perf_counter()
    deadline = t0 + seconds
    while time.perf_counter() < deadline:
        try:
            p, addr = s.recvfrom(2048)
        except (socket.timeout, OSError):
            break
        pkts.append(p)
        srcs.add(addr[0])
    elapsed = time.perf_counter() - t0
    s.close()

    # Sequence health, read without disturbing udp_monitor's module state.
    seqs, bad_magic, bad_len = [], 0, 0
    for p in pkts:
        if len(p) != um.PAYLOAD_LEN:
            bad_len += 1
            continue
        if p[:4] != um.MAGIC:
            bad_magic += 1
            continue
        seqs.append(int.from_bytes(p[4:8], "big"))
    # Rate is detected AFTER the sequence numbers are available: heavy loss
    # would otherwise make a 96 kHz board read as a healthy 24 kHz one, since
    # the two rates are exactly 4x apart. See detect_rate's docstring.
    rate, confident = um.detect_rate(pkts, elapsed, seqs=seqs)

    lost = expected = 0
    if len(seqs) >= 2:
        for a, b in zip(seqs, seqs[1:]):
            d = (b - a) & 0xFFFFFFFF
            if 0 < d < 1000:
                expected += d
                lost += d - 1

    return {
        "node": node, "port": port, "srcs": sorted(srcs),
        "pkts": len(pkts), "elapsed": elapsed,
        "pps": len(pkts) / elapsed if elapsed else 0.0,
        "rate": rate, "confident": confident,
        "lost": lost, "expected": expected,
        "bad_magic": bad_magic, "bad_len": bad_len,
    }


def main():
    ap = argparse.ArgumentParser(description="find and identify every soundcard")
    ap.add_argument("-s", "--seconds", type=float, default=2.0,
                    help="listen time per board (default 2)")
    ap.add_argument("--nodes", default="1,2,3,4",
                    help="comma-separated node numbers (default all four)")
    args = ap.parse_args()
    nodes = [int(x) for x in args.nodes.split(",") if x.strip()]

    print("Listening %.1f s per board on ports %s ..."
          % (args.seconds, ", ".join(str(ctrl.node_stream_port(n)) for n in nodes)))
    print("(passive - nothing is transmitted)\n")

    found = []
    for n in nodes:
        r = probe(n, args.seconds)
        if r is None:
            print("  node %d  port %d   SILENT" % (n, ctrl.node_stream_port(n)))
            continue
        if r.get("error"):
            print("  node %d  port %d   %s" % (n, r["port"], r["error"]))
            print("           (another capture tool probably holds this port)")
            continue
        found.append(r)
        src = ", ".join(r["srcs"])
        rate = ("%d Hz" % r["rate"]) if r["confident"] else ("~%.0f Hz ?" % r["rate"])
        loss = (100.0 * r["lost"] / r["expected"]) if r["expected"] else 0.0
        print("  node %d  port %d   %-15s  %-10s  %5.0f pkt/s  loss %.3f%%"
              % (n, r["port"], src, rate, r["pps"], loss))
        if len(r["srcs"]) > 1:
            print("           ** MORE THAN ONE SENDER ON THIS PORT **")
            print("           Two boards share an address or a port. Their")
            print("           sequence numbers interleave and every capture on")
            print("           this port is meaningless until it is fixed.")
        if r["bad_magic"] or r["bad_len"]:
            print("           %d bad magic, %d wrong length"
                  % (r["bad_magic"], r["bad_len"]))

    if not found:
        print("\nNothing found.")
        print("  - are the boards powered and the link up?")
        print("  - is this PC on a subnet that can reach them? Known: %s"
              % ", ".join(ctrl.KNOWN_SUBNETS))
        print("  - Windows Firewall silently drops inbound UDP; allow python.")
        return 1

    # ------------------------------------------------------------- summary --
    print("\n" + "=" * 66)
    subnets = sorted({s.rsplit(".", 1)[0] for r in found for s in r["srcs"]})
    rates = sorted({r["rate"] for r in found if r["confident"]})

    print("%d board(s) answering." % len(found))

    if len(subnets) > 1:
        print("\n  MIXED SUBNETS: %s" % ", ".join(subnets))
        print("  The array is part-way through a migration, or a board was")
        print("  flashed with an image from the wrong set. The host needs an")
        print("  address on each subnet to reach them all - see")
        print("  docs/CHANGING_IP.md.")
    else:
        print("  subnet   %s.x" % subnets[0])

    if len(rates) > 1:
        print("\n  MIXED SAMPLE RATES: %s"
              % ", ".join("%d Hz" % r for r in rates))
        print("  Boards are running different images (24K_* vs 96K_*). Each")
        print("  board is individually fine, but they are NOT time-aligned in")
        print("  sample count, so nothing that compares channels ACROSS boards")
        print("  will be correct until they match.")
    elif rates:
        print("  rate     %d Hz  (%s)"
              % (rates[0], "decimating 24K_* image" if rates[0] == 24000
                 else "plain 96K_* image"))

    total = sum(r["pps"] * (um.WIRE_LEN + 8 + 4 + 12) * 8 for r in found) / 1e6
    print("  offered  %.1f Mbit/s aggregate to this host" % total)
    if total > 90:
        print("           ** over 90 Mbit/s: needs a gigabit NIC and uplink **")

    worst = max((100.0 * r["lost"] / r["expected"]) if r["expected"] else 0.0
                for r in found)
    if worst > 0.01:
        print("  worst loss %.3f%% - usually the host, not the wire; see"
              " docs/NETWORK_SETUP.md" % worst)
    return 0


if __name__ == "__main__":
    sys.exit(main())
