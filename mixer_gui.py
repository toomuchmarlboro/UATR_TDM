#!/usr/bin/env python3
"""
Live 16-channel mixer GUI for the TDM_UATR hydrophone soundcard.

    python mixer_gui.py
    python mixer_gui.py --port 5005 --fps 25

Meters, per-channel gain faders, mute, and 48 V phantom power - all live over
UDP to the board. tkinter and numpy only.

Packet geometry comes from udp_monitor.py and the control protocol from
ctrl.py, so there is one definition of each. check_sync.py validates
udp_monitor against the RTL, so this inherits that.

Meters
    bar = RMS, white line = held peak.
    SILENT (grey) below -120 dBFS: LSB dither only. Normal on an open input;
    with a hydrophone connected and phantom on it means the analog path is
    not delivering.
    CLIP (red) at full scale. An open XLR with 48 V on it clips and means
    nothing - only trust it on a connected channel.

Faders
    Post-ADC gain, register 0x0A-0x0D of the owning part. +60 dB to -35.6 dB
    in 0.375 dB steps, which is the hardware's own resolution.

48 V
    Off at every reset. The FPGA gates phantom power on the build constant
    C_ENABLE_48V, the staged power-up timer, AND this flag - so it never comes
    up on its own after a power cycle.
"""

import argparse
import os
import socket
import struct
import sys
import threading
import tkinter as tk

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import udp_monitor as um
import ctrl

# Which ADC owns which channels: matches get_i2c_addr in adau_sequencer.vhd and
# the B-part CMAP slot patch, cross-checked against the netlist address straps.
OWNER = ([("U19", "0x11")] * 4 + [("U20", "0x31")] * 4 +
         [("U37", "0x51")] * 4 + [("U38", "0x71")] * 4)

DB_LO   = -100.0
DECODE_MAX = 120        # packets decoded per redraw; see tick()
METER_H = 300
CH_W    = 58
LEFT    = 74
TOP     = 56
BG      = "#16181d"
PANEL   = "#1c1f26"
GRID    = "#2c313a"
TEXT    = "#c8ccd4"
DIM     = "#6b7280"
GREEN   = "#3fb950"
AMBER   = "#d29922"
RED     = "#f85149"


def dbfs(v):
    return DB_LO - 40 if v <= 0 else max(DB_LO - 40, 20.0 * np.log10(v / um.FULL_SCALE))


class Receiver(threading.Thread):
    """UDP in its own thread so a slow redraw never costs packets."""

    def __init__(self, port, bind):
        super().__init__(daemon=True)
        self.lock = threading.Lock()
        self.raw, self.pkts, self.lost, self.seq_prev = [], 0, 0, 0
        self.stop = False
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 64 << 20)
        except OSError:
            pass
        self.sock.bind((bind, port))
        self.sock.settimeout(0.3)

    def run(self):
        # Keep this loop as cheap as possible. At 96 kHz the board sends 12,000
        # packets/s - 83 us each - and anything expensive here backs up the
        # socket buffer and drops packets. Decoding was originally done per
        # packet with numpy, which could not keep up: the meter showed half the
        # stream and channels near the threshold appeared to flicker. Raw bytes
        # go on a list, and the GUI thread decodes the whole batch at once.
        local = []
        while not self.stop:
            try:
                d = self.sock.recv(2048)
            except socket.timeout:
                if local:
                    self._flush(local)
                    local = []
                continue
            except OSError:
                break               # socket closed on shutdown
            if len(d) < um.PAYLOAD_LEN or d[:4] != um.MAGIC:
                continue
            local.append(d)
            if len(local) >= 64:            # one lock per 64 packets
                self._flush(local)
                local = []

    def _flush(self, batch):
        with self.lock:
            for d in batch:
                seq = struct.unpack(">I", d[4:8])[0]
                self.pkts += 1
                if self.seq_prev and seq > self.seq_prev + 1:
                    self.lost += seq - self.seq_prev - 1
                self.seq_prev = seq
            self.raw.extend(batch)
            if len(self.raw) > 2000:        # cap if the GUI stalls badly
                del self.raw[:-1000]

    def take(self):
        with self.lock:
            b, self.raw = self.raw, []
            n, self.pkts = self.pkts, 0
            return b, n, self.lost


class Mixer(tk.Tk):
    def __init__(self, rx, fps, hold, ip):
        super().__init__()
        self.rx, self.hold_s, self.ip = rx, hold, ip
        self.period = int(1000 / fps)
        self.title("UATR 16-Channel Mixer")
        self.configure(bg=BG)
        self.resizable(False, False)

        self.phantom = tk.BooleanVar(value=False)
        self.gain_db = [tk.DoubleVar(value=0.0) for _ in range(um.CHANNELS)]
        self.muted = [tk.BooleanVar(value=False) for _ in range(um.CHANNELS)]

        w = LEFT + um.CHANNELS * CH_W + 24
        self.cv = tk.Canvas(self, width=w, height=TOP + METER_H + 54,
                            bg=BG, highlightthickness=0)
        self.cv.pack()
        self._build_meters(w)

        self.faders = tk.Frame(self, bg=BG)
        self.faders.pack(fill="x")
        self._build_faders()

        self.bar = tk.Frame(self, bg=PANEL)
        self.bar.pack(fill="x", pady=(6, 0))
        self._build_controls()

        self.held = np.full(um.CHANNELS, DB_LO - 40)
        self.held_age = np.zeros(um.CHANNELS)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.after(self.period, self.tick)

    # ---------------------------------------------------------------- meters
    def _build_meters(self, w):
        self.hdr = self.cv.create_text(14, 18, anchor="w", fill=TEXT,
                                       font=("Consolas", 11, "bold"), text="")
        self.sub = self.cv.create_text(14, 37, anchor="w", fill=DIM,
                                       font=("Consolas", 8), text="")
        for db in range(0, int(DB_LO) - 1, -20):
            y = self.y_of(db)
            self.cv.create_line(LEFT - 6, y, w - 14, y, fill=GRID)
            self.cv.create_text(LEFT - 12, y, anchor="e", fill=DIM,
                                font=("Consolas", 8), text="%d" % db)
        self.bars, self.peaks, self.labels = [], [], []
        for i in range(um.CHANNELS):
            x, cx = LEFT + i * CH_W, LEFT + i * CH_W + CH_W // 2
            self.cv.create_rectangle(x + 7, TOP, x + CH_W - 7, TOP + METER_H,
                                     outline=GRID, fill=PANEL)
            self.bars.append(self.cv.create_rectangle(
                x + 9, TOP + METER_H, x + CH_W - 9, TOP + METER_H,
                outline="", fill=GREEN))
            self.peaks.append(self.cv.create_line(
                x + 7, TOP + METER_H, x + CH_W - 7, TOP + METER_H, fill="#ffffff"))
            self.cv.create_text(cx, TOP + METER_H + 14, fill=TEXT,
                                font=("Consolas", 10, "bold"), text=str(i + 1))
            who, addr = OWNER[i]
            self.cv.create_text(cx, TOP + METER_H + 29, fill=DIM,
                                font=("Consolas", 7), text="%s %s" % (who, addr))
            self.labels.append(self.cv.create_text(
                cx, TOP + METER_H + 44, fill=DIM, font=("Consolas", 8), text="-inf"))
            if i in (4, 8, 12):
                self.cv.create_line(x + 1, TOP - 8, x + 1, TOP + METER_H + 36, fill=GRID)

    # ---------------------------------------------------------------- faders
    def _build_faders(self):
        self.faders.columnconfigure(0, minsize=LEFT)
        tk.Label(self.faders, text="gain\ndB", bg=BG, fg=DIM,
                 font=("Consolas", 8)).grid(row=0, column=0)
        for i in range(um.CHANNELS):
            self.faders.columnconfigure(i + 1, minsize=CH_W)
            col = tk.Frame(self.faders, bg=BG)
            col.grid(row=0, column=i + 1)
            s = tk.Scale(col, from_=60.0, to=-35.625, resolution=0.375,
                         orient="vertical", length=118, width=11,
                         showvalue=False, variable=self.gain_db[i],
                         bg=BG, fg=TEXT, troughcolor=PANEL, highlightthickness=0,
                         activebackground=GREEN, borderwidth=0,
                         command=lambda _v, ch=i: self.on_gain(ch))
            s.pack()
            lab = tk.Label(col, text="0.0", bg=BG, fg=TEXT, font=("Consolas", 7))
            lab.pack()
            m = tk.Checkbutton(col, text="M", variable=self.muted[i],
                               command=lambda ch=i: self.on_gain(ch),
                               bg=BG, fg=RED, selectcolor=PANEL,
                               activebackground=BG, activeforeground=RED,
                               font=("Consolas", 7), borderwidth=0,
                               highlightthickness=0)
            m.pack()
            setattr(self, "_glab%d" % i, lab)

    # -------------------------------------------------------------- controls
    def _build_controls(self):
        tk.Button(self.bar, text="all 0 dB", command=lambda: self.set_all(0.0),
                  bg=PANEL, fg=TEXT, font=("Consolas", 9), borderwidth=0,
                  activebackground=GRID, padx=10).pack(side="left", padx=6, pady=6)
        tk.Button(self.bar, text="all mute", command=lambda: self.set_all(None),
                  bg=PANEL, fg=TEXT, font=("Consolas", 9), borderwidth=0,
                  activebackground=GRID, padx=10).pack(side="left", padx=2)
        self.ph = tk.Checkbutton(
            self.bar, text=" 48 V PHANTOM ", variable=self.phantom,
            command=self.on_phantom, bg=PANEL, fg=AMBER, selectcolor="#3a1d1d",
            activebackground=PANEL, activeforeground=RED,
            font=("Consolas", 10, "bold"), borderwidth=0, highlightthickness=0)
        self.ph.pack(side="left", padx=18)
        self.status = tk.Label(self.bar, text="ready", bg=PANEL, fg=DIM,
                               font=("Consolas", 8), anchor="e")
        self.status.pack(side="right", padx=10)

    # ----------------------------------------------------------------- logic
    def flags(self):
        return 0x01 if self.phantom.get() else 0x00

    def send(self, ch):
        """ch is 0-based here; ctrl.send_gain takes 1-16."""
        db = None if self.muted[ch].get() else self.gain_db[ch].get()
        b = ctrl.gain_byte(db)
        try:
            ctrl.send_gain(ch + 1, b, flags=self.flags(), ip=self.ip)
        except OSError as e:
            self.status.config(text="send failed: %s" % e, fg=RED)
            return
        getattr(self, "_glab%d" % ch).config(
            text="mute" if db is None else "%.1f" % db,
            fg=RED if db is None else TEXT)
        self.status.config(
            text="ch %d -> 0x%02X  %s   48V %s"
                 % (ch + 1, b, "mute" if db is None else "%+.3f dB" % db,
                    "ON" if self.phantom.get() else "off"),
            fg=DIM)

    def on_gain(self, ch):
        self.send(ch)

    def on_phantom(self):
        on = self.phantom.get()
        self.ph.config(fg=RED if on else AMBER)
        self.send(0)            # any command carries the flags byte
        self.status.config(text="48 V %s" % ("ENABLED" if on else "disabled"),
                           fg=RED if on else DIM)

    def set_all(self, db):
        for i in range(um.CHANNELS):
            self.muted[i].set(db is None)
            if db is not None:
                self.gain_db[i].set(db)
            self.send(i)
            self.update_idletasks()

    def y_of(self, db):
        db = max(DB_LO, min(0.0, db))
        return TOP + METER_H - (db - DB_LO) / (-DB_LO) * METER_H

    def tick(self):
        raw, npk, lost = self.rx.take()
        # Decode a bounded, evenly-spread subset rather than everything. Full
        # decode runs at ~9,000 pkt/s against a 12,000 pkt/s stream, so the GUI
        # would fall further behind every frame and channels near the threshold
        # would flicker. 120 packets is 960 frames per channel per update -
        # far more than RMS and peak need - and the stride keeps it
        # representative of the whole window rather than just the oldest part.
        if len(raw) > DECODE_MAX:
            raw = raw[::max(1, len(raw) // DECODE_MAX)][:DECODE_MAX]
        blocks = [b for b in (ctrl.decode(d) for d in raw) if b is not None]
        if blocks:
            x = np.concatenate(blocks, axis=0).astype(np.float64)
            rms = np.sqrt(np.mean(x * x, axis=0))
            pk = np.max(np.abs(x), axis=0)
        else:
            rms = pk = np.zeros(um.CHANNELS)

        pps = npk * (1000.0 / self.period)
        self.cv.itemconfigure(self.hdr, text="%d Hz   %5.0f pkt/s   lost %d"
                              % (um.SAMPLE_RATE, pps, lost))
        self.cv.itemconfigure(self.sub, text="bar = RMS   white = held peak   "
                                             "faders write ADAU1978 reg 0x0A-0x0D over I2C")

        step = self.period / 1000.0
        for i in range(um.CHANNELS):
            rdb, pdb = dbfs(rms[i]), dbfs(pk[i])
            silent = rdb < -120
            clipped = pk[i] >= um.FULL_SCALE - 1
            self.held_age[i] += step
            if pdb >= self.held[i] or self.held_age[i] > self.hold_s:
                self.held[i], self.held_age[i] = pdb, 0.0

            y = self.y_of(rdb)
            self.cv.coords(self.bars[i], LEFT + i * CH_W + 9, y,
                           LEFT + i * CH_W + CH_W - 9, TOP + METER_H)
            self.cv.itemconfigure(self.bars[i], fill=(
                DIM if silent else RED if rdb > -6 else AMBER if rdb > -20 else GREEN))
            yp = self.y_of(self.held[i])
            self.cv.coords(self.peaks[i], LEFT + i * CH_W + 7, yp,
                           LEFT + i * CH_W + CH_W - 7, yp)
            self.cv.itemconfigure(self.peaks[i], fill=RED if clipped else "#ffffff")
            self.cv.itemconfigure(
                self.labels[i],
                text="SILENT" if silent else ("CLIP" if clipped else "%.0f" % rdb),
                fill=DIM if silent else (RED if clipped else TEXT))

        self.after(self.period, self.tick)

    def close(self):
        self.rx.stop = True
        try:
            self.rx.sock.close()
        except OSError:
            pass
        self.destroy()


def main():
    ap = argparse.ArgumentParser(description="live 16-channel mixer GUI")
    ap.add_argument("--port", type=int, default=5005)
    ap.add_argument("--bind", default="0.0.0.0")
    ap.add_argument("--fps", type=float, default=20.0)
    ap.add_argument("--peak-hold", type=float, default=2.0)
    ap.add_argument("--ip", default=ctrl.FPGA_IP, help="board IP for control")
    a = ap.parse_args()
    rx = Receiver(a.port, a.bind)
    rx.start()
    Mixer(rx, a.fps, a.peak_hold, a.ip).mainloop()


if __name__ == "__main__":
    main()
