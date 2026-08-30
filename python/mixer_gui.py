#!/usr/bin/env python3
"""
UATR control station GUI. One tab per AFE, plus telemetry:

    AFE 1-4     16-channel meters and gain, over UDP to each FPGA soundcard.
                64 channels in total, four boards, one window.
    Telemetry   $GDAT2 sensor data from the aux_vcu, over TCP. See gdat2.py.

    python mixer_gui.py                       # all four AFEs
    python mixer_gui.py --nodes 1,3           # only the boards you have
    python mixer_gui.py --nodes 2 --port 5006
    python mixer_gui.py --gdat-buoy 2 --gdat-connect
    python mixer_gui.py --fullscreen          # or --maximized

Each AFE tab owns its own socket on that board's own stream port (5005-5008)
and its own control IP (192.168.1.101-.104), both derived from ctrl.py so they
cannot drift from C_NODE in top_system.vhd. Boards never share a port: the
receive loop uses recv(), which discards the sender, so two boards on one
socket would interleave their sequence numbers and the loss figure would be
meaningless for both.

ONLY THE VISIBLE TAB DECODES. A full decode runs at roughly 9,000 pkt/s against
one board's 12,000 pkt/s, so four tabs decoding at once would be far over
budget and every meter would lag. Background tabs still drain their sockets -
the receive threads never stop, or the kernel buffer overflows and the loss
numbers become fiction - they just skip the decode and the redraw.

The header on each tab names the board it is showing. With four identical
panels in one window, a fader moved on the wrong board is silent and
unrecoverable, so that is on screen rather than inferred from the tab you think
you clicked.

The window is resizable and every element scales with it - F11 toggles
fullscreen, Escape leaves it. It opens at a fraction of the actual screen, so
it is usable on a laptop and on the lab panel without a rebuild. The meters and
their faders derive all geometry from one channel width and the faders are
embedded in the meter canvas, so a fader is always under its own channel.

Test the telemetry tab with no aux_vcu present:

    python gdat2.py --sim                                  # in one terminal
    python mixer_gui.py --gdat-host 127.0.0.1 --gdat-connect

Every tab is independent - no device has to be present for any other to work,
which matters because they are separate pieces of hardware that will not arrive
on the bench at the same time. A missing board shows silent meters and
"board: ? (no packets)", not an error.

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

    This GUI does not own phantom power - the operator app does, and this is a
    debugger watching alongside it. So the checkbox FOLLOWS the board: it is
    driven by the readback the FPGA puts in every packet, and it tracks changes
    the app makes without this GUI being involved.

    That is also why gain commands from here are phantom-neutral. The FPGA
    parses one command format and every gain write carries the flags byte, so
    there is no way to change a fader without saying something about phantom
    power. flags() therefore sends back the board's OWN current state - "keep
    doing what you are doing" - and only a click on the checkbox sends anything
    different. Without that, moving a fader here would silently revert a
    phantom change the app had just made.

    A click is a request, not a result. The checkbox holds the requested value
    while the command is in flight and waits for the board to confirm it. If the
    FPGA refuses - C_ENABLE_48V false in the build, or the staged power-up not
    yet at 1000 ms - it snaps back and names the reason, rather than showing an
    ON that never happened.

    Asserted, not measured. The FPGA has no sense line back from the 48 V
    supply, so this reports what it is driving on EN_48V, not what reaches the
    hydrophones. Treat a dead supply as still possible when it reads ON.
"""

import argparse
import math
import os
import socket
import struct
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import udp_monitor as um
import ctrl
import gdat2
import ping1d
import witmotion
import imu_test          # AxisWindow: one implementation of "has this moved?"

# Which ADC owns which channels: matches get_i2c_addr in adau_sequencer.vhd and
# the B-part CMAP slot patch, cross-checked against the netlist address straps.
OWNER = ([("U19", "0x11")] * 4 + [("U20", "0x31")] * 4 +
         [("U37", "0x51")] * 4 + [("U38", "0x71")] * 4)

DB_LO   = -100.0
DECODE_MAX = 120        # packets decoded per redraw; see tick()
# How long a 48 V toggle may go unconfirmed before the checkbox snaps back to
# what the board reports. Generous: the command is one UDP datagram and the
# readback is in the very next packet, so anything past this is a refusal or a
# lost packet, not latency.
PH_TIMEOUT_S = 1.5

# Geometry is computed from the live canvas size in Mixer._metrics, not fixed.
# The meters and the faders under them derive every x from ONE ch_w, and the
# fader columns are embedded in the canvas rather than laid out in their own
# grid - two geometry sources that have to agree will eventually not, and a
# fader sitting under the wrong meter is the one misalignment nobody notices
# until they have turned down the wrong hydrophone.
# Deliberately modest. A 1366x768 or 1280x720 laptop is a real target, and a
# 620 px floor there leaves a window that cannot meaningfully be shrunk or put
# side by side with anything. The layout stays legible down to this size - it
# is tested at exactly these numbers.
MIN_W, MIN_H = 880, 560

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


def _clamp(lo, v, hi):
    return max(lo, min(hi, v))


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


class Mixer(tk.Frame):
    """The 16-channel mixer, as a frame so it can sit in a notebook tab.

    This was a tk.Tk in its own right until the telemetry tab arrived. Window
    concerns - title, geometry, close handling - moved up to App; everything
    below is unchanged apart from packing into self instead of into a root.
    """

    def __init__(self, master, rx, fps, hold, ip, label=""):
        super().__init__(master, bg=BG)
        self.rx, self.hold_s, self.ip = rx, hold, ip
        # Shown in the header. With four of these in one window, every panel
        # looks identical, and a fader moved on the wrong board is silent and
        # unrecoverable - so which board this is has to be on screen, not
        # inferred from which tab you think you clicked.
        self.label = label
        self.period = int(1000 / fps)

        # The checkbox FOLLOWS the board - see _sync_phantom. It starts False
        # only so the widget has a value before the first packet arrives.
        self.phantom = tk.BooleanVar(value=False)
        self.ph_actual = None           # last phantom_state dict, None = unknown
        self.ph_pending = None          # a user toggle awaiting confirmation
        self.ph_wait = 0.0              # how long it has been awaiting it
        self._ph_quiet = 0.0            # seconds since the last packet, for staleness
        self.gain_db = [tk.DoubleVar(value=0.0) for _ in range(um.CHANNELS)]
        self.muted = [tk.BooleanVar(value=False) for _ in range(um.CHANNELS)]

        self.bar = tk.Frame(self, bg=PANEL)
        self.bar.pack(side="bottom", fill="x")
        self._build_controls()

        self.cv = tk.Canvas(self, bg=BG, highlightthickness=0)
        self.cv.pack(side="top", fill="both", expand=True)

        self.m = None                   # layout metrics, set by _relayout
        self._rjob = None               # pending debounced relayout
        self._build_items()
        self.cv.bind("<Configure>", self._on_resize)

        self.held = np.full(um.CHANNELS, DB_LO - 40)
        self.held_age = np.zeros(um.CHANNELS)
        self._job = self.after(self.period, self.tick)

    # --------------------------------------------------------------- layout
    def _metrics(self, w, h):
        """Every coordinate on this tab, derived from the canvas size alone."""
        left  = _clamp(36, int(w * 0.055), 96)
        pad_r = _clamp(6,  int(w * 0.010), 24)
        ch_w  = max(16.0, float(w - left - pad_r) / um.CHANNELS)

        # Ceilings are set high enough that a 4K lab panel actually gets larger
        # text rather than 232 px meters labelled in 11 pt. The upper bounds
        # only exist to stop a very wide, very short window from producing text
        # taller than the meter it labels.
        f_hdr = _clamp(9, int(h * 0.021) + 5, 28)
        f_sub = _clamp(7, f_hdr - 3, 22)
        f_num = _clamp(7, int(ch_w * 0.20), 30)
        f_sml = _clamp(6, int(ch_w * 0.135), 20)

        head = int(f_hdr * 2.1 + f_sub * 2.2) + 8
        r_num = int(f_num * 1.9)                        # rows under the meter
        r_own = r_num + int(f_sml * 2.0)
        r_val = r_own + int(f_sml * 2.0)
        lab_h = r_val + int(f_sml * 1.5)

        # The faders get a share of the height, but the meters are the point of
        # this tab - so when the window is short the faders give ground first,
        # down to a floor where the scale is still draggable.
        fad_h = _clamp(88, int(h * 0.26), 280)
        mh = h - head - lab_h - fad_h - 6
        if mh < 90:
            fad_h = _clamp(58, fad_h + mh - 90, 280)
            mh = h - head - lab_h - fad_h - 6
        mh = max(36, mh)

        return {"w": w, "h": h, "left": left, "ch_w": ch_w, "top": head,
                "mh": mh, "r_num": r_num, "r_own": r_own, "r_val": r_val,
                "fad_y": head + mh + lab_h,
                "fad_h": fad_h,
                "sc_len": max(34, fad_h - int(f_sml * 2.3) * 2 - 6),
                "sc_wid": _clamp(7, int(ch_w * 0.20), 20),
                "inset": max(2, int(ch_w * 0.12)),
                "bar_in": max(3, int(ch_w * 0.17)),
                "f_hdr": f_hdr, "f_sub": f_sub, "f_num": f_num, "f_sml": f_sml}

    def cx(self, i):
        """Centre of channel i. The meter and its fader both use only this."""
        m = self.m
        return m["left"] + (i + 0.5) * m["ch_w"]

    def _on_resize(self, ev):
        if ev.width < 60 or ev.height < 60:
            return
        # Debounced: a drag fires Configure continuously, and relaying out on
        # every one of them makes the window crawl.
        if self._rjob:
            self.after_cancel(self._rjob)
        self._rjob = self.after(40, self._relayout)

    # ---------------------------------------------------------------- items
    def _build_items(self):
        """Create every canvas item and fader widget once; _relayout moves them.

        Rebuilding on each resize would churn 100+ items and destroy/recreate
        live Scale widgets, losing their drag state mid-gesture.
        """
        self.hdr = self.cv.create_text(0, 0, anchor="w", fill=TEXT, text="")
        self.sub = self.cv.create_text(0, 0, anchor="w", fill=DIM, text="")
        self.rules = []
        for db in range(0, int(DB_LO) - 1, -20):
            self.rules.append((db,
                               self.cv.create_line(0, 0, 0, 0, fill=GRID),
                               self.cv.create_text(0, 0, anchor="e", fill=DIM,
                                                   text="%d" % db)))
        self.gainlab = self.cv.create_text(0, 0, anchor="e", fill=DIM,
                                           text="gain dB")
        self.boxes, self.bars, self.peaks = [], [], []
        self.nums, self.owners, self.labels = [], [], []
        self.seps, self.fadwin = [], []
        for i in range(um.CHANNELS):
            self.boxes.append(self.cv.create_rectangle(0, 0, 0, 0,
                                                       outline=GRID, fill=PANEL))
            self.bars.append(self.cv.create_rectangle(0, 0, 0, 0,
                                                      outline="", fill=GREEN))
            self.peaks.append(self.cv.create_line(0, 0, 0, 0, fill="#ffffff"))
            self.nums.append(self.cv.create_text(0, 0, fill=TEXT,
                                                 text=str(i + 1)))
            who, addr = OWNER[i]
            self.owners.append(self.cv.create_text(0, 0, fill=DIM,
                                                   text="%s %s" % (who, addr)))
            self.labels.append(self.cv.create_text(0, 0, fill=DIM, text="-inf"))
            if i in (4, 8, 12):
                self.seps.append((i, self.cv.create_line(0, 0, 0, 0, fill=GRID)))

            col = tk.Frame(self.cv, bg=BG)
            s = tk.Scale(col, from_=60.0, to=-35.625, resolution=0.375,
                         orient="vertical", width=11, showvalue=False,
                         variable=self.gain_db[i],
                         bg=BG, fg=TEXT, troughcolor=PANEL, highlightthickness=0,
                         activebackground=GREEN, borderwidth=0,
                         command=lambda _v, ch=i: self.on_gain(ch))
            s.pack()
            lab = tk.Label(col, text="0.0", bg=BG, fg=TEXT)
            lab.pack()
            mt = tk.Checkbutton(col, text="M", variable=self.muted[i],
                                command=lambda ch=i: self.on_gain(ch),
                                bg=BG, fg=RED, selectcolor=PANEL,
                                activebackground=BG, activeforeground=RED,
                                borderwidth=0, highlightthickness=0)
            mt.pack()
            # Embedded in the canvas at the meter's own centre, so a fader can
            # never drift out from under the channel it controls.
            self.fadwin.append(self.cv.create_window(0, 0, window=col,
                                                     anchor="n"))
            setattr(self, "_glab%d" % i, lab)
            setattr(self, "_scale%d" % i, s)
            setattr(self, "_mute%d" % i, mt)

    def _relayout(self):
        self._rjob = None
        w, h = self.cv.winfo_width(), self.cv.winfo_height()
        if w < 60 or h < 60:
            return
        m = self.m = self._metrics(w, h)
        cvi, cvc = self.cv.itemconfigure, self.cv.coords
        hf, sf = ("Consolas", m["f_hdr"], "bold"), ("Consolas", m["f_sub"])
        nf, mf = ("Consolas", m["f_num"], "bold"), ("Consolas", m["f_sml"])

        cvc(self.hdr, 12, int(m["f_hdr"] * 1.3)); cvi(self.hdr, font=hf)
        cvc(self.sub, 12, int(m["f_hdr"] * 2.6)); cvi(self.sub, font=sf)
        right = m["left"] + um.CHANNELS * m["ch_w"] - m["inset"]
        for db, ln, tx in self.rules:
            y = self.y_of(db)
            cvc(ln, m["left"] - 6, y, right, y)      # ends at the last meter
            cvc(tx, m["left"] - 11, y); cvi(tx, font=mf)
        cvc(self.gainlab, m["left"] - 11, m["fad_y"] + m["sc_len"] * 0.5)
        cvi(self.gainlab, font=mf)

        bot = m["top"] + m["mh"]
        for i in range(um.CHANNELS):
            c = self.cx(i)
            ins, bin_ = m["inset"], m["bar_in"]
            cvc(self.boxes[i], c - m["ch_w"] / 2 + ins, m["top"],
                c + m["ch_w"] / 2 - ins, bot)
            cvc(self.peaks[i], c - m["ch_w"] / 2 + ins, bot,
                c + m["ch_w"] / 2 - ins, bot)
            cvc(self.bars[i], c - m["ch_w"] / 2 + bin_, bot,
                c + m["ch_w"] / 2 - bin_, bot)
            cvc(self.nums[i], c, bot + m["r_num"]);  cvi(self.nums[i], font=nf)
            cvc(self.owners[i], c, bot + m["r_own"])
            cvi(self.owners[i], font=("Consolas", max(6, m["f_sml"] - 1)))
            cvc(self.labels[i], c, bot + m["r_val"]); cvi(self.labels[i], font=mf)
            cvc(self.fadwin[i], c, m["fad_y"])
            getattr(self, "_scale%d" % i).config(length=m["sc_len"],
                                                 width=m["sc_wid"])
            getattr(self, "_glab%d" % i).config(font=mf)
            getattr(self, "_mute%d" % i).config(font=mf)
        for i, ln in self.seps:
            x = m["left"] + i * m["ch_w"]
            cvc(ln, x, m["top"] - 8, x, m["fad_y"] + m["fad_h"])

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
        self.ph.pack(side="left", padx=(18, 4))
        # What the board reports it is driving, from the readback in every
        # packet. Normally it agrees with the checkbox; it turns red while a
        # toggle is still in flight or has not taken effect.
        self.ph_lab = tk.Label(self.bar, text="board: ?", bg=PANEL, fg=DIM,
                               font=("Consolas", 9))
        self.ph_lab.pack(side="left", padx=(0, 14))
        self.status = tk.Label(self.bar, text="ready", bg=PANEL, fg=DIM,
                               font=("Consolas", 8), anchor="e")
        self.status.pack(side="right", padx=10)

    # ----------------------------------------------------------------- logic
    def flags(self):
        """The flags byte to attach to an outgoing command.

        This is the BOARD's current phantom state, not the checkbox - and that
        difference is the whole point of the method.

        This GUI is not the only thing driving the board. The operator app owns
        phantom power; this is a debugger watching alongside it. There is no
        flags-only packet - the FPGA parses one command format and every gain
        write carries the flags byte - so if this returned the checkbox, then
        any fader moved here would re-assert whatever phantom state this GUI
        last knew about and silently revert a change the app had made.

        Returning the readback makes a gain command phantom-NEUTRAL: it tells
        the board to keep doing what it is already doing. Only on_phantom, where
        the user actually clicked, sends a value that differs.

        Falls back to the checkbox when the board has not been heard from, which
        is the old single-controller behaviour and the best available guess.
        """
        if self.ph_pending is not None:
            return 0x01 if self.ph_pending else 0x00
        if self.ph_actual is not None:
            return 0x01 if self.ph_actual["on"] else 0x00
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
        """The ONE place this GUI deliberately changes phantom power.

        Everything else it sends is phantom-neutral - see flags(). A click here
        raises ph_pending, which flags() then sends in place of the readback
        until the board is seen to agree.
        """
        on = self.phantom.get()
        self.ph_pending = on
        self.ph_wait = 0.0
        self.ph.config(fg=RED if on else AMBER)
        self.send(0)            # any command carries the flags byte
        self.status.config(text="48 V %s requested" % ("ON" if on else "off"),
                           fg=RED if on else DIM)

    def _sync_phantom(self, pkt, dt):
        """Mirror the checkbox to whatever the board reports it is driving.

        This GUI FOLLOWS the board; it does not hold an opinion of its own. The
        operator app owns phantom power - it forces 48 V off at every start and
        reload, and from then on only a deliberate user toggle turns it on - so
        the truth lives in the FPGA, and this display exists to show it. An
        earlier version seeded the checkbox once at startup and then let the two
        drift apart, which was right when this GUI was the only controller and
        wrong now: the app can change phantom at any moment, and a debugger
        showing a stale toggle is worse than showing nothing.

        The one exception is a click the user just made. ph_pending holds it,
        the display stays on the requested value while the command is in flight,
        and the board's own readback is what confirms it. That is deliberately
        not a local assumption of success - if the FPGA refuses (C_ENABLE_48V
        false in the build, or the staged power-up not yet at 1000 ms) the
        checkbox snaps back and says so, rather than showing an ON that never
        happened.
        """
        st = ctrl.phantom_state(pkt)
        if st is None:
            return
        self.ph_actual = st

        if self.ph_pending is not None:
            if st["on"] == self.ph_pending:
                self.ph_pending = None          # the board agrees; done
            else:
                self.ph_wait += dt
                if self.ph_wait < PH_TIMEOUT_S:
                    self.ph_lab.config(
                        text="board: %s  (waiting)"
                             % ("ON" if st["on"] else "off"), fg=AMBER)
                    return
                # It has had long enough. Name the gate holding it off - "build"
                # and "power-up" are refusals the user cannot fix from here, and
                # saying which one beats a bare "it did not work".
                why = ("C_ENABLE_48V false in this build" if not st["permitted"]
                       else "staged power-up not at 1000 ms yet"
                       if not st["staged"] else
                       "the FPGA did not receive it" if not st["requested"]
                       else "watchdog has tripped - the FPGA is overriding")
                self.ph_pending = None
                self.phantom.set(st["on"])
                self.ph.config(fg=RED if st["on"] else AMBER)
                self.status.config(text="48 V refused: %s" % why, fg=RED)

        on = st["on"]
        if self.phantom.get() != on:
            # Display only. This writes the BooleanVar, not the hardware: Tk
            # does not fire the widget's command on a programmatic set, so
            # following the board here can never send a packet.
            self.phantom.set(on)
            self.ph.config(fg=RED if on else AMBER)
        self.ph_lab.config(text="board: %s" % ("ON" if on else "off"),
                           fg=RED if on else DIM)

    def set_all(self, db):
        for i in range(um.CHANNELS):
            self.muted[i].set(db is None)
            if db is not None:
                self.gain_db[i].set(db)
            self.send(i)
            self.update_idletasks()

    def y_of(self, db):
        m = self.m
        db = max(DB_LO, min(0.0, db))
        return m["top"] + m["mh"] - (db - DB_LO) / (-DB_LO) * m["mh"]

    def tick(self):
        # The first Configure may not have arrived yet. Reschedule rather than
        # return, or a late Configure would leave the meters never updating.
        if self.m is None:
            self._job = self.after(self.period, self.tick)
            return
        raw, npk, lost = self.rx.take()

        # HIDDEN TAB: drain and drop, do not decode.
        #
        # This is what makes four boards in one window affordable. Decoding is
        # the expensive half - a full decode runs at roughly 9,000 pkt/s against
        # a 12,000 pkt/s stream from ONE board - so four tabs all decoding would
        # be four times over budget and every meter would lag and flicker.
        # Only the tab you are looking at does that work.
        #
        # take() is still called, not skipped: it swaps the buffer out under the
        # lock, so the receive thread's backlog stays bounded and the packet and
        # loss counters keep advancing while the tab is in the background. The
        # thread itself never stops - the socket must keep being drained or the
        # kernel buffer overflows and the loss figures become fiction.
        if not self.winfo_viewable():
            self._job = self.after(self.period, self.tick)
            return

        # 48 V readback, from the newest packet in hand. One packet per tick is
        # enough - the state changes on human timescales - and it must be read
        # before the stride below, which is free to drop the newest one.
        if raw:
            self._ph_quiet = 0.0
            self._sync_phantom(raw[-1], self.period / 1000.0)
        else:
            self._ph_quiet += self.period / 1000.0
            if self._ph_quiet > 2.0 and self.ph_actual is not None:
                # Stop showing a reading the board is no longer confirming. The
                # pin has not necessarily changed - the link has - but an
                # indicator that keeps asserting "off" for an unplugged board is
                # exactly the kind of thing that gets trusted around live 48 V.
                self.ph_actual = None
                self.ph_lab.config(text="board: ? (no packets)", fg=AMBER)
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
        self.cv.itemconfigure(self.hdr, text="%s%d Hz   %5.0f pkt/s   lost %d"
                              % (self.label, um.SAMPLE_RATE, pps, lost))
        self.cv.itemconfigure(self.sub, text="bar = RMS   white = held peak   "
                                             "faders write ADAU1978 reg 0x0A-0x0D over I2C")

        step = self.period / 1000.0
        m = self.m
        bot, half = m["top"] + m["mh"], m["ch_w"] / 2
        for i in range(um.CHANNELS):
            rdb, pdb = dbfs(rms[i]), dbfs(pk[i])
            silent = rdb < -120
            clipped = pk[i] >= um.FULL_SCALE - 1
            self.held_age[i] += step
            if pdb >= self.held[i] or self.held_age[i] > self.hold_s:
                self.held[i], self.held_age[i] = pdb, 0.0

            c = self.cx(i)
            y = self.y_of(rdb)
            self.cv.coords(self.bars[i], c - half + m["bar_in"], y,
                           c + half - m["bar_in"], bot)
            self.cv.itemconfigure(self.bars[i], fill=(
                DIM if silent else RED if rdb > -6 else AMBER if rdb > -20 else GREEN))
            yp = self.y_of(self.held[i])
            self.cv.coords(self.peaks[i], c - half + m["inset"], yp,
                           c + half - m["inset"], yp)
            self.cv.itemconfigure(self.peaks[i], fill=RED if clipped else "#ffffff")
            self.cv.itemconfigure(
                self.labels[i],
                text="SILENT" if silent else ("CLIP" if clipped else "%.0f" % rdb),
                fill=DIM if silent else (RED if clipped else TEXT))

        self._job = self.after(self.period, self.tick)

    def close(self):
        """Release the socket. The window itself is App's to destroy."""
        # Cancel BOTH pending callbacks first. Destroying the window with one
        # still queued makes Tk fire it against a dead widget and print
        # "invalid command name ...tick" on every exit. The debounced relayout
        # is the same hazard on a resize-then-close, just harder to trip.
        for attr in ("_job", "_rjob"):
            if getattr(self, attr, None):
                self.after_cancel(getattr(self, attr))
                setattr(self, attr, None)
        self.rx.stop = True
        try:
            self.rx.sock.close()
        except OSError:
            pass


class CompassWidget(tk.Canvas):
    """Heading rose, ported from the manufacturer's CompassWidget.

    Theirs is QPainter: a circle, N/S/E/W, then painter.rotate(yaw) and a red
    needle drawn "up" with a white tail. Same geometry here, with the rotation
    done in the coordinate arithmetic because a tk Canvas has no transform.

    Screen convention throughout: y grows DOWNWARD, so a positive angle turns
    clockwise and "up" is negative y. Yaw 0 puts the needle on N, yaw 90 on E,
    which is what their rotate(yaw) produces.
    """

    def __init__(self, master, size=150):
        super().__init__(master, width=size, height=size, bg=BG,
                         highlightthickness=0, bd=0)
        self.size = size
        self.yaw = None                 # corrected heading, degrees
        self.raw_yaw = None             # what the IMU reported, for recalibration
        self.bind("<Configure>", lambda _e: self._redraw())
        self._redraw()

    def set_yaw(self, yaw, raw=None):
        if (yaw, raw) != (self.yaw, self.raw_yaw):
            self.yaw, self.raw_yaw = yaw, raw
            self._redraw()

    def _redraw(self):
        self.delete("all")
        w = max(self.winfo_width(), self.size)
        h = max(self.winfo_height(), self.size)
        cx, cy = w / 2.0, h / 2.0
        r = min(cx, cy) - 15
        if r < 10:
            return

        self.create_oval(cx - r, cy - r, cx + r, cy + r, outline=TEXT, width=2)
        for txt, dx, dy in (("N", 0, -1), ("S", 0, 1), ("E", 1, 0), ("W", -1, 0)):
            self.create_text(cx + dx * (r - 12), cy + dy * (r - 12), text=txt,
                             fill=TEXT, font=("Consolas", 9, "bold"))

        if self.yaw is None:
            self.create_text(cx, cy + r + 8, text="hdg --", fill=DIM,
                             font=("Consolas", 9))
            return

        a = math.radians(self.yaw)
        sa, ca = math.sin(a), math.cos(a)

        def rot(x, y):
            """Rotate clockwise by yaw, screen coords."""
            return cx + x * ca - y * sa, cy + x * sa + y * ca

        tip = r - 20
        # Red half points to the heading, white half trails it - theirs.
        self.create_polygon(*rot(-5, 0), *rot(5, 0), *rot(0, -tip),
                            fill=RED, outline="")
        self.create_polygon(*rot(-5, 0), *rot(5, 0), *rot(0, tip),
                            fill="#e6e6e6", outline="")
        cap = "hdg %.1f" % self.yaw
        if self.raw_yaw is not None and abs(self.raw_yaw - self.yaw) > 0.05:
            # The uncorrected number stays on screen: it is what you read off
            # to recalibrate, and it makes an applied offset visible rather
            # than silently baked in.
            cap += "   (raw %+.1f)" % self.raw_yaw
        self.create_text(cx, cy + r + 8, text=cap,
                         fill=AMBER, font=("Consolas", 9))


class AttitudeWidget(tk.Canvas):
    """Artificial horizon, ported from the manufacturer's AttitudeWidget.

    Theirs clips to a circle with QPainterPath, rotates by -roll, translates by
    pitch*2, then fills a blue rectangle above the horizon and a brown one
    below. A tk Canvas cannot clip, so the ground is computed instead: the
    horizon is a chord of the circle, and the ground is the circular segment on
    its far side.

    The geometry, once set up, is small. With the ground normal n at angle phi
    and the horizon offset d = pitch * PITCH_PX from centre, a point at angle t
    on the rim is ground when cos(t - phi) > d/r. So the segment runs from
    phi - acos(d/r) to phi + acos(d/r), and |d| >= r means the view is entirely
    sky or entirely ground - which is what a buoy past 45 degrees would show.
    """

    PITCH_PX = 2.0          # pixels per degree of pitch, as in their code

    def __init__(self, master, size=150):
        super().__init__(master, width=size, height=size, bg=BG,
                         highlightthickness=0, bd=0)
        self.size = size
        self.roll = None                # levelled
        self.pitch = None
        self.raw = None                 # as reported, for recalibration
        self.bind("<Configure>", lambda _e: self._redraw())
        self._redraw()

    def set_attitude(self, roll, pitch, raw=None):
        if (roll, pitch, raw) != (self.roll, self.pitch, self.raw):
            self.roll, self.pitch, self.raw = roll, pitch, raw
            self._redraw()

    def _redraw(self):
        self.delete("all")
        w = max(self.winfo_width(), self.size)
        h = max(self.winfo_height(), self.size)
        cx, cy = w / 2.0, h / 2.0
        r = min(cx, cy) - 10
        if r < 10:
            return

        if self.roll is None:
            self.create_oval(cx - r, cy - r, cx + r, cy + r,
                             outline=GRID, width=2)
            self.create_text(cx, cy, text="--", fill=DIM,
                             font=("Consolas", 10))
            return

        # Whole disc is sky; the ground segment goes on top of it.
        self.create_oval(cx - r, cy - r, cx + r, cy + r,
                         fill="#1e5f9e", outline="")

        a = math.radians(-self.roll)             # their painter.rotate(-roll)
        # Ground normal = local +y rotated by a. Offset of the horizon from the
        # centre along that normal is the pitch translation.
        nx, ny = -math.sin(a), math.cos(a)
        d = self.pitch * self.PITCH_PX
        phi = math.atan2(ny, nx)

        if d >= r:
            pass                                  # all sky
        elif d <= -r:
            self.create_oval(cx - r, cy - r, cx + r, cy + r,
                             fill="#6b4423", outline="")
        else:
            alpha = math.acos(max(-1.0, min(1.0, d / r)))
            pts = []
            steps = 36
            for i in range(steps + 1):
                t = (phi - alpha) + (2 * alpha) * i / float(steps)
                pts += [cx + r * math.cos(t), cy + r * math.sin(t)]
            self.create_polygon(*pts, fill="#6b4423", outline="")
            # Horizon line: the chord itself.
            ux, uy = -ny, nx                      # along the horizon
            hx, hy = cx + d * nx, cy + d * ny     # midpoint of the chord
            half = math.sqrt(max(0.0, r * r - d * d))
            self.create_line(hx - ux * half, hy - uy * half,
                             hx + ux * half, hy + uy * half,
                             fill="#ffffff", width=2)

        self.create_oval(cx - r, cy - r, cx + r, cy + r, outline=GRID, width=2)
        # Fixed aircraft reference, theirs: two bars and a centre dot.
        self.create_line(cx - 30, cy, cx - 10, cy, fill=AMBER, width=3)
        self.create_line(cx + 10, cy, cx + 30, cy, fill=AMBER, width=3)
        self.create_oval(cx - 2, cy - 2, cx + 2, cy + 2, fill=AMBER,
                         outline="")
        cap = "R %+.1f  P %+.1f" % (self.roll, self.pitch)
        if self.raw is not None and (abs(self.raw[0] - self.roll) > 0.05 or
                                     abs(self.raw[1] - self.pitch) > 0.05):
            # Same rule as the compass: an applied offset stays visible, and
            # the uncorrected pair is what you read off to recalibrate.
            cap += "   (raw %+.1f / %+.1f)" % self.raw
        self.create_text(cx, cy + r + 8, text=cap,
                         fill=TEXT, font=("Consolas", 9))


class Telemetry(tk.Frame):
    """$GDAT2 sensor telemetry from the aux_vcu, over TCP.

    A different device on a different transport from everything else here, so
    it shares no state with the mixer beyond the window - if the aux_vcu is
    absent or the FPGA is unplugged, the other tab carries on regardless.

    ulRaw fields arrive as 8 hex digits; seq and cnt as decimal. The wire text
    is shown next to the decoded value for every field, so a decode that goes
    wrong can be checked against the bytes that produced it without a capture.

    TWO VIEWS, ANSWERING DIFFERENT QUESTIONS.

    The ALL BUOYS strip at the top compares four units at once: link state,
    sentence rate, error and loss counts, seconds since the last good sentence,
    and the three values worth scanning across a fleet - leak, depth, altimeter.
    It exists because "which buoy is misbehaving" is not answerable by clicking
    through them one at a time. A link that drops every thirty seconds looks
    healthy in whichever moment you happen to be looking at it.

    The table below is the single-buoy detail: every field, its wire bytes, and
    whether it has ever been seen to change. That one asks "is this number
    believable", which the overview cannot.

    Links are keyed by address and SHARED between the two views. Plenty of
    embedded TCP servers accept a single client, so opening a second connection
    to a buoy the overview is already watching would either be refused or
    silently displace the first.
    """

    ROW_H = 26

    # The all-buoy overview. Link health first, because that is what decides
    # whether the numbers after it mean anything, then the three values you
    # would actually scan across four units: a leak, how deep it is, and how
    # far off the bottom.
    # THREE devices per buoy, each on its own address and its own protocol, so
    # each gets its own state column. They fail independently - the commonest
    # case in the water will be two of three alive - and a single "buoy OK"
    # light would hide exactly that.
    # ONE CELL PER DEVICE, then the values.
    #
    # This was thirteen columns: a state/rate/err/loss/age block for the
    # aux_vcu and a state cell each for the altimeter and IMU. Five columns to
    # say "is this link healthy" is four more than the question needs, and the
    # numbers that matter were pushed off to the right behind a wall of zeros.
    #
    # Each device cell now carries its own verdict - rate when healthy, the
    # fault when not - so a bad link is legible without reading four cells and
    # doing the arithmetic yourself. The detail table below still has the full
    # breakdown for whichever buoy is selected.
    OV_COLS = (("buoy", 62, "w"),
               ("gdat2", 108, "w"), ("imu", 96, "w"), ("altimeter", 104, "w"),
               ("leak V", 76, "e"), ("depth m", 84, "e"),
               ("alt m", 84, "e"), ("hdg", 74, "e"))

    C_GDAT2, C_IMU, C_ALT = 1, 2, 3
    C_LEAK, C_DEPTH, C_ALTMM, C_YAW = 4, 5, 6, 7

    def __init__(self, master, mode, host, port, fps=10.0):
        super().__init__(master, bg=BG)
        self.period = int(1000 / fps)
        # One Link per address, shared. Deliberately NOT one for the overview
        # and another for the detail table: plenty of embedded TCP servers
        # accept a single client, so a second connection to a buoy already
        # being watched would either be refused or would silently displace the
        # first. Whoever wants that buoy's data reads this same object.
        self.links = {}
        # Ping1D altimeters, keyed the same way. A separate dict rather than a
        # separate class: they are a different protocol on a different device,
        # and mixing them into self.links would put two incompatible snapshot()
        # shapes behind one lookup.
        self.alt_links = {}
        self.imu_links = {}
        self.mode = tk.StringVar(value=mode)
        self.host = tk.StringVar(value=host)
        self.port = tk.StringVar(value=str(port))
        self._rjob = None
        self._build()
        self.bind("<Configure>", self._on_resize)
        # A notebook tab that has never been shown is unmapped and 1x1, and
        # Configure does not fire on it - so a window resized while the Mixer
        # tab was in front would leave this one still at its build-time font
        # sizes. Map fires when it first becomes visible; rescale then.
        self.bind("<Map>", self._on_resize)
        self._job = self.after(self.period, self.tick)

    @property
    def link(self):
        """The link feeding the DETAIL table, i.e. whichever host is selected.

        A lookup rather than a field, so the detail view and the overview can
        never end up holding two different objects for one buoy. Returns None
        when that host is not being watched, which every reader already treats
        as "nothing to show".
        """
        return self.links.get(self.host.get().strip())

    def _ensure_link(self, host, port, mode="client"):
        """Open a link to host if there is not one already. -> the Link."""
        host = host.strip()
        if host not in self.links:
            lk = gdat2.Link(mode, host, port)
            lk.start()
            self.links[host] = lk
        return self.links[host]

    def _drop_link(self, host):
        lk = self.links.pop(host.strip(), None)
        if lk:
            lk.close()

    # Font sizes track the window so the table stays readable on a 4K panel and
    # still fits on a laptop. Column widths are weighted, so the table stretches
    # rather than stranding everything against the left edge in fullscreen.
    def _on_resize(self, _ev=None):
        # Deliberately does not read _ev: this handles <Map> too, whose width
        # and height are not the real geometry. _rescale asks the widget.
        if self._rjob:
            self.after_cancel(self._rjob)
        self._rjob = self.after(60, self._rescale)

    def _rescale(self):
        self._rjob = None
        w, h = self.winfo_width(), self.winfo_height()
        if w < 60 or h < 60:
            return
        base = _clamp(8, int(min(w / 105.0, h / 46.0)), 20)
        cell = ("Consolas", base)
        big = ("Consolas", base + 1)
        for row in self.cells:
            for i, lab in enumerate(row):
                lab.config(font=big if i == 3 else cell)
        self.stats.config(font=cell)
        for row in self.ov_rows:
            for lab in row:
                lab.config(font=cell)
        for lab in self.ov_heads:
            lab.config(font=("Consolas", max(7, base - 1)))
        for lab in self.heads:
            lab.config(font=("Consolas", max(7, base - 1)))
        self.rawbox.config(font=("Consolas", max(7, base - 1)))

    def pick_buoy(self, name):
        for nm, ip in gdat2.BUOYS:
            if nm == name:
                # Set the label too. The OptionMenu writes the variable itself
                # before calling this, but a programmatic call does not, and
                # then the label would name one buoy while the socket talked to
                # another - the one disagreement this selector must not allow.
                self.buoy.set(nm)
                self.host.set(ip)
                # No teardown any more. Links are keyed by address and shared
                # with the overview, so switching buoy just points the detail
                # table at a different one - and tearing down would have closed
                # a connection the overview is still using. tick() notices the
                # target changed and resets the liveness trackers, so buoy 2's
                # sentences can never be counted as proof that buoy 1 moved.
                self._sync_detail_button()
                break

    @staticmethod
    def _field_index(name):
        """Index of a gdat2 field BY NAME, or raise.

        Not a hardcoded number. The whole argument of gdat2.py's header is that
        a field map and a second array indexed in step with it drift apart
        silently, and the overview would be exactly that second array. If a
        field is renamed or reordered upstream, this fails at construction
        instead of quietly showing depth under the altimeter heading.
        """
        for i, (nm, _u, _k) in enumerate(gdat2.FIELDS):
            if nm == name:
                return i
        raise SystemExit("mixer_gui: gdat2.FIELDS has no %r - the telemetry "
                         "overview names it. Update OV_COLS." % name)

    def _build_overview(self):
        """All four buoys, one row each, above the single-buoy detail table.

        This answers a different question from the table below it. The detail
        table asks "is this field believable"; this asks "which of the four is
        misbehaving", which is not answerable by clicking through them one at a
        time - a link that drops every thirty seconds looks healthy in whichever
        moment you happen to be looking at it.

        Device health comes first because it qualifies everything after it: a
        depth reading from a link with a rising checksum-error count is not a
        depth reading. Each device cell shows its packet rate when healthy and
        names the fault when not - STALE for a link that is open but silent,
        which is the failure that otherwise presents as perfectly steady data.
        """
        # (overview column, gdat2 field index, format). Resolved by name here,
        # once, so a rename upstream is a startup error and not a mislabelled
        # number on screen.
        # Altimeter is NOT taken from gdat2 here any more: the manufacturer
        # moved it to its own Ping1D device, and their own reference parser
        # skips ulRaw[7:9] entirely. Those fields read hard zero on this
        # firmware, so showing them would be showing a number that is not a
        # measurement. The alt columns come from ping1d instead.
        self._OV_VALUE_COLS = (
            (self.C_LEAK,  self._field_index("Leak sensor"), "%.2f"),
            (self.C_DEPTH, self._field_index("Depth"),       "%.2f"),
        )

        wrap = tk.Frame(self, bg=BG)
        wrap.pack(fill="x", padx=12, pady=(8, 2))
        tk.Label(wrap, text="ALL BUOYS", bg=BG, fg=TEXT, anchor="w",
                 font=("Consolas", 9, "bold")).pack(fill="x")

        grid = tk.Frame(wrap, bg=BG)
        grid.pack(fill="x")
        self.ov_heads = []
        for c, (name, wid, _anc) in enumerate(self.OV_COLS):
            grid.grid_columnconfigure(c, weight=wid, minsize=44)
            lab = tk.Label(grid, text=name, bg=BG, fg=DIM, anchor="w",
                           font=("Consolas", 8))
            lab.grid(row=0, column=c, sticky="ew", padx=3)
            self.ov_heads.append(lab)

        self.ov_rows = []
        for r, (nm, ip) in enumerate(gdat2.BUOYS, start=1):
            row = []
            for c, (_n, _w, anc) in enumerate(self.OV_COLS):
                txt = nm if c == 0 else "-"
                lab = tk.Label(grid, text=txt, bg=BG, fg=DIM, anchor=anc,
                               font=("Consolas", 9))
                lab.grid(row=r, column=c, sticky="ew", padx=3)
                row.append(lab)
            self.ov_rows.append(row)

        tk.Frame(wrap, bg=GRID, height=1).pack(fill="x", pady=(6, 0))

    @staticmethod
    def _dev_cell(snap, now, fresh_s=1.0, errors=0):
        """One device's health as (text, colour). Shared by all three.

        The rule is the same whichever protocol is underneath, which is why it
        is written once: STALE outranks connected, because a socket that is
        open while the far end has stopped talking is the failure that a naive
        "connected" light hides. Errors are shown in the same cell rather than
        a column of their own - they are rare, and when they happen they are
        the most important thing about that link.
        """
        if snap is None:
            return "-", DIM
        st = snap["state"]
        age = None if snap["t"] is None else now - snap["t"]
        live = age is not None and age <= fresh_s
        if st == "connected" and not live:
            return ("STALE" if snap["t"] else "no data"), RED
        if st == "connected":
            txt = "%.0f/s" % snap["rate"]
            if errors:
                return "%s  %d err" % (txt, errors), RED
            return txt, GREEN
        if "connect" in st:
            return "connecting", AMBER
        return st[:14], RED

    @staticmethod
    def _is_live(snap, now, fresh_s=1.0):
        if snap is None or snap["t"] is None:
            return False
        return (now - snap["t"]) <= fresh_s

    def _update_instruments(self, now):
        """Point the compass and horizon at the SELECTED buoy.

        Preference is the IMU, because it is the origin of the number - the
        aux_vcu relays the same attitude into the sentence at a twentieth of
        the rate. Falling back to $GDAT2 means the instruments still work on a
        buoy whose IMU link is down, which is when you most want them.
        """
        try:
            n = [ip for _nm, ip in gdat2.BUOYS].index(
                self.host.get().strip()) + 1
        except ValueError:
            n = None

        roll = pitch = yaw = None
        src = ""
        if n is not None:
            im = self.imu_links.get(gdat2.buoy_ip(n, gdat2.ROLE_IMU))
            s = im.snapshot() if im else None
            if s and s["angle"] and self._is_live(s, now):
                a = s["angle"]
                roll, pitch, yaw = a["roll"], a["pitch"], a["yaw"]
                src = "from IMU  %.0f pkt/s" % s["rate"]

        if roll is None:
            lk = self.links.get(self.host.get().strip())
            g = lk.snapshot() if lk else None
            r = g["last"] if g else None
            if r is not None and (now - r["t"]) <= 1.0:
                i_r = self._field_index("AHRS Roll")
                vals = r["vals"]
                roll, pitch, yaw = vals[i_r], vals[i_r + 1], vals[i_r + 2]
                src = "from $GDAT2 relay"

        if roll is None or pitch is None or yaw is None:
            self.compass.set_yaw(None, None)
            self.horizon.set_attitude(None, None, None)
            self.att_src.config(text="attitude: no live source", fg=DIM)
            return
        # All three axes carry this buoy's installation offset. Gravity gives
        # roll and pitch an absolute reference, but that reference is to the
        # SENSOR's frame, not the hull's - so a unit bolted in a few degrees
        # off reads a steady tilt while floating perfectly level, and the
        # correction is what makes the horizon agree with the water.
        lr, lp = witmotion.level(roll, pitch, buoy=n)
        self.compass.set_yaw(witmotion.heading(yaw, buoy=n), raw=yaw)
        self.horizon.set_attitude(lr, lp, raw=(roll, pitch))
        self.att_src.config(text="attitude %s" % src, fg=DIM)

    def _update_overview(self):
        now = time.time()
        for r, (_nm, ip) in enumerate(gdat2.BUOYS):
            row = self.ov_rows[r]

            # ---- aux_vcu -----------------------------------------------
            lk = self.links.get(ip)
            g = lk.snapshot() if lk else None
            if g is not None:
                # gdat2.Link timestamps the sentence, not the socket read, so
                # normalise it to the shape _dev_cell expects.
                g = dict(g, t=None if g["last"] is None else g["last"]["t"])
                gerr = g["csum_err"] + g["parse_err"] + g["lost"]
            else:
                gerr = 0
            txt, fg = self._dev_cell(g, now, errors=gerr)
            row[self.C_GDAT2].config(text=txt, fg=fg)

            glive = self._is_live(g, now)
            rr = lk.snapshot()["last"] if lk else None
            vals = rr["vals"] if rr else [None] * len(gdat2.FIELDS)
            bad = set(i for i, _v, _lo, _hi in gdat2.implausible(vals)) if rr else set()
            for col, idx, fmt in self._OV_VALUE_COLS:
                v = vals[idx]
                row[col].config(
                    text="-" if v is None else fmt % v,
                    fg=DIM if not glive else (RED if idx in bad else TEXT))

            # ---- IMU ---------------------------------------------------
            im = self.imu_links.get(gdat2.buoy_ip(r + 1, gdat2.ROLE_IMU))
            i = im.snapshot() if im else None
            txt, fg = self._dev_cell(i, now, errors=(i["bad"] if i else 0))
            row[self.C_IMU].config(text=txt, fg=fg)
            ang = i["angle"] if i else None
            ilive = self._is_live(i, now)
            if ang is None:
                row[self.C_YAW].config(text="-", fg=DIM)
            else:
                # Corrected heading, not raw yaw - see witmotion.heading. The
                # column is titled "hdg" for that reason: comparing four buoys
                # is only meaningful once each one's own installation offset
                # has been taken out.
                hdg = witmotion.heading(ang["yaw"], buoy=r + 1)
                row[self.C_YAW].config(
                    text="%.1f" % hdg, fg=DIM if not ilive else TEXT)

            # ---- altimeter ---------------------------------------------
            al = self.alt_links.get(gdat2.buoy_ip(r + 1, gdat2.ROLE_ALTIMETER))
            a = al.snapshot() if al else None
            # A Ping1D answers on request, so "fresh" is looser than for the
            # two streaming devices - it legitimately goes quiet between polls.
            txt, fg = self._dev_cell(a, now, fresh_s=3.0,
                                     errors=(a["bad"] if a else 0))
            row[self.C_ALT].config(text=txt, fg=fg)
            alive = self._is_live(a, now, fresh_s=3.0)
            d = a["dist"] if a else None
            c = a["conf"] if a else None
            if d is None:
                row[self.C_ALTMM].config(text="-", fg=DIM)
            else:
                # Confidence, not range, is what says whether the sonar found
                # anything - so it colours the distance rather than occupying a
                # column of its own. Amber below 30 % means "this is a number,
                # not a measurement".
                # Metres, not millimetres. The sonar reports mm, but a range
                # to the seabed is read in metres by everyone who uses it, and
                # a five-digit millimetre count is harder to compare across
                # four buoys at a glance than 86.75.
                row[self.C_ALTMM].config(
                    text="%.2f" % (d / 1000.0),
                    fg=DIM if not alive else
                    (RED if d > ping1d.DIST_MAX_MM else
                     TEXT if (c or 0) >= 30 else AMBER))

    # ------------------------------------------------------------- layout --
    def _build(self):
        bar = tk.Frame(self, bg=PANEL)
        bar.pack(fill="x")
        tk.Label(bar, text=" aux_vcu ", bg=PANEL, fg=TEXT,
                 font=("Consolas", 10, "bold")).pack(side="left", padx=(8, 2), pady=7)
        # Start the selector on whichever buoy --gdat-host names, so the label
        # and the address can never disagree about what is being talked to.
        here = self.host.get().strip()
        self.buoy = tk.StringVar(
            value=next((n for n, ip in gdat2.BUOYS if ip == here), "custom"))
        om = tk.OptionMenu(bar, self.buoy, *[n for n, _ip in gdat2.BUOYS],
                           command=self.pick_buoy)
        om.config(bg=GRID, fg=TEXT, font=("Consolas", 9), borderwidth=0,
                  highlightthickness=0, activebackground=GREEN, width=7)
        om["menu"].config(bg=PANEL, fg=TEXT, font=("Consolas", 9))
        om.pack(side="left", padx=(4, 8))
        for txt, val in (("client", "client"), ("server", "server")):
            tk.Radiobutton(bar, text=txt, value=val, variable=self.mode,
                           bg=PANEL, fg=TEXT, selectcolor=GRID,
                           activebackground=PANEL, activeforeground=TEXT,
                           font=("Consolas", 8), borderwidth=0,
                           highlightthickness=0).pack(side="left")
        tk.Entry(bar, textvariable=self.host, width=15, bg=BG, fg=TEXT,
                 insertbackground=TEXT, font=("Consolas", 9),
                 borderwidth=0).pack(side="left", padx=(10, 2))
        tk.Label(bar, text=":", bg=PANEL, fg=DIM).pack(side="left")
        tk.Entry(bar, textvariable=self.port, width=6, bg=BG, fg=TEXT,
                 insertbackground=TEXT, font=("Consolas", 9),
                 borderwidth=0).pack(side="left", padx=2)
        self.btn = tk.Button(bar, text="connect", command=self.toggle,
                             bg=GRID, fg=TEXT, font=("Consolas", 9),
                             borderwidth=0, activebackground=GREEN, padx=12)
        self.btn.pack(side="left", padx=10)
        self.all_btn = tk.Button(bar, text="watch all", command=self.watch_all,
                                 bg=GRID, fg=TEXT, font=("Consolas", 9),
                                 borderwidth=0, activebackground=GREEN, padx=12)
        self.all_btn.pack(side="left")
        self.state_lab = tk.Label(bar, text="idle", bg=PANEL, fg=DIM,
                                  font=("Consolas", 8), anchor="e")
        self.state_lab.pack(side="right", padx=10)

        self._build_overview()

        inst = tk.Frame(self, bg=BG)
        inst.pack(fill="x", padx=12, pady=(6, 2))
        self.compass = CompassWidget(inst, size=132)
        self.compass.pack(side="left", padx=(0, 10))
        self.horizon = AttitudeWidget(inst, size=132)
        self.horizon.pack(side="left", padx=(0, 14))
        # Which unit the needles are actually following. The aux_vcu RELAYS the
        # IMU's attitude into $GDAT2 fields 4-6, so the two agree - but the IMU
        # is the direct source at ~1000 packets/s against the sentence's 50, and
        # saying which one is driving keeps "the compass is stuck" from turning
        # into a hunt across two devices.
        self.att_src = tk.Label(inst, text="", bg=BG, fg=DIM, anchor="w",
                                font=("Consolas", 8), justify="left")
        self.att_src.pack(side="left", anchor="s", pady=(0, 18))

        self.stats = tk.Label(self, text="", bg=BG, fg=DIM, anchor="w",
                              font=("Consolas", 9), justify="left")
        self.stats.pack(fill="x", padx=12, pady=(8, 4))

        # The "live" column is the one that stops a number being believed just
        # because it is well formatted. A field can frame, checksum, decode and
        # print a plausible value while never being updated at all - which is
        # what 1.1/3.1/177.7 deg of attitude did on buoy 3 until someone picked
        # the unit up. Tracking is imu_test's, imported rather than reimplemented.
        cols = (("field", 150, "w"), ("wire (hex)", 120, "e"),
                ("u32", 110, "e"), ("value", 130, "e"), ("unit", 60, "w"),
                ("live", 110, "w"))
        # weight per column, so the table uses the whole width when maximised
        wts = (3, 2, 2, 2, 1, 2)
        head = tk.Frame(self, bg=BG)
        head.pack(fill="x", padx=12)
        self.heads = []
        for i, (nm, _w, _a) in enumerate(cols):
            head.grid_columnconfigure(i, weight=wts[i], uniform="tel")
            lab = tk.Label(head, text=nm, bg=BG, fg=DIM, font=("Consolas", 8),
                           anchor="w")
            lab.grid(row=0, column=i, sticky="ew")
            self.heads.append(lab)

        self.grid_f = tk.Frame(self, bg=PANEL)
        self.grid_f.pack(fill="x", padx=12, pady=(2, 8))
        self.cells = []
        for i in range(len(cols)):
            self.grid_f.grid_columnconfigure(i, weight=wts[i], uniform="tel")
        # One tracker per field, session-wide. Reset on connect, not per frame:
        # "has this ever changed" is only meaningful over a whole session, and
        # is the only thing that separates a sensor sitting still from a field
        # nobody writes. See imu_test.AxisWindow.
        self.watch = [imu_test.AxisWindow(nm) for nm, _u, _k in gdat2.FIELDS]
        self.last_t = None

        for r, (nm, unit, _k) in enumerate(gdat2.FIELDS):
            row = []
            bgc = PANEL if r % 2 == 0 else BG
            for i, (_h, _w, anch) in enumerate(cols):
                txt = nm if i == 0 else (unit if i == 4 else "-")
                fg = TEXT if i in (0, 3) else DIM
                lab = tk.Label(self.grid_f, text=txt, bg=bgc, fg=fg,
                               font=("Consolas", 10 if i == 3 else 9),
                               anchor=anch, padx=4, pady=3)
                lab.grid(row=r, column=i, sticky="ew")
                row.append(lab)
            self.cells.append(row)

        tk.Label(self, text="last sentences", bg=BG, fg=DIM,
                 font=("Consolas", 8), anchor="w").pack(fill="x", padx=12)
        self.rawbox = tk.Text(self, height=6, bg=PANEL, fg=DIM,
                              font=("Consolas", 8), borderwidth=0,
                              highlightthickness=0, wrap="none")
        self.rawbox.pack(fill="both", expand=True, padx=12, pady=(2, 10))

    # -------------------------------------------------------------- logic --
    def toggle(self):
        """Connect or disconnect the selected host only."""
        if self.link:
            self._drop_link(self.host.get())
            self.btn.config(text="connect", activebackground=GREEN)
            self.state_lab.config(text="disconnected", fg=DIM)
            return
        try:
            port = int(self.port.get())
        except ValueError:
            self.state_lab.config(text="bad port", fg=RED)
            return
        # A fresh link is a fresh session: carrying "it moved earlier" across a
        # reconnect would let a dead field inherit a previous unit's proof.
        self._reset_watch()
        self._ensure_link(self.host.get(), port, self.mode.get())
        self.btn.config(text="disconnect", activebackground=RED)

    def watch_all(self):
        """Open a link to every buoy at once, so the overview is populated.

        The point of the overview is comparing four units, and a column that is
        blank because nobody dialled it looks exactly like a unit that is down.
        So this dials all of them, and the state column tells them apart.
        """
        try:
            port = int(self.port.get())
        except ValueError:
            self.state_lab.config(text="bad port", fg=RED)
            return
        ips = [ip for _n, ip in gdat2.BUOYS]
        alts = [gdat2.buoy_ip(n, 2) for n in (1, 2, 3, 4)]
        if all(ip in self.links for ip in ips):     # already up: take them down
            for ip in ips:
                self._drop_link(ip)
            for ip in alts:
                lk = self.alt_links.pop(ip, None)
                if lk:
                    lk.close()
            for n in (1, 2, 3, 4):
                lk = self.imu_links.pop(gdat2.buoy_ip(n, gdat2.ROLE_IMU), None)
                if lk:
                    lk.close()
            self.all_btn.config(text="watch all", activebackground=GREEN)
            return
        for ip in ips:
            self._ensure_link(ip, port, "client")
        for ip in alts:
            if ip not in self.alt_links:
                lk = ping1d.PingLink(ip, ping1d.PING_PORT)
                lk.start()
                self.alt_links[ip] = lk
        for n in (1, 2, 3, 4):
            ip = gdat2.buoy_ip(n, gdat2.ROLE_IMU)
            if ip not in self.imu_links:
                lk = witmotion.WitLink(ip, witmotion.WIT_PORT)
                lk.start()
                self.imu_links[ip] = lk
        self.all_btn.config(text="drop all", activebackground=RED)
        # The detail table follows whichever buoy is selected; if that is not
        # one of them (a custom host), leave it alone.
        self._sync_detail_button()

    def _reset_watch(self):
        for w in self.watch:
            w.__init__(w.name)
        self.last_t = None

    def _sync_detail_button(self):
        up = self.link is not None
        self.btn.config(text="disconnect" if up else "connect",
                        activebackground=RED if up else GREEN)

    def tick(self):
        self._update_overview()
        self._update_instruments(time.time())

        # The detail table follows the selected host, and the liveness trackers
        # below are per-field evidence about ONE unit. Switching buoy without
        # clearing them would let buoy 2's sentences stand as proof that buoy
        # 1's field had moved - a false "live" on a dead channel, which is the
        # exact claim this tab exists to make trustworthy. Detected here rather
        # than in pick_buoy so that typing an address by hand is covered too.
        key = self.host.get().strip()
        if key != getattr(self, "_detail_key", None):
            self._detail_key = key
            self._reset_watch()

        if self.link:
            s = self.link.snapshot()
            ok = s["state"] == "connected"
            self.state_lab.config(
                text="%s  %s" % (s["state"], s["peer"]),
                fg=GREEN if ok else AMBER if "connect" in s["state"] else RED)
            self.stats.config(
                text="%6.1f sentence/s   good %-7d checksum err %-5d "
                     "unparsable %-5d counter loss %-5d"
                     % (s["rate"], s["good"], s["csum_err"], s["parse_err"],
                        s["lost"]),
                fg=RED if (s["csum_err"] or s["parse_err"]) else DIM)

            r = s["last"]
            # Stale is its own state. A frozen connection shows the last good
            # reading forever otherwise, which is the one failure a telemetry
            # view must never present as live data.
            stale = r is None or (time.time() - r["t"]) > 1.0

            # Feed the liveness trackers, but only on a sentence we have not
            # already seen - snapshot() returns the same "last" between ticks,
            # and re-feeding it would pad the sample counts with duplicates.
            # This samples at the GUI tick rate rather than every frame, which
            # undercounts changes but cannot invent one: what matters is
            # whether a field EVER changes, and that survives sampling.
            if r is not None and r["t"] != self.last_t:
                self.last_t = r["t"]
                for i in range(len(gdat2.FIELDS)):
                    if r["raw"][i] is not None:
                        self.watch[i].feed(r["t"], r["raw"][i], r["vals"][i])

            # Out-of-range says the SENTENCE is suspect, most likely a shifted
            # field map, so it is flagged per field rather than as one banner.
            bad_range = set()
            if r is not None:
                bad_range = set(i for i, _v, _lo, _hi
                                in gdat2.implausible(r["vals"]))

            for i, (_nm, unit, kind) in enumerate(gdat2.FIELDS):
                raw = r["raw"][i] if r else None
                val = r["vals"][i] if r else None
                c = self.cells[i]
                c[1].config(text=(r["wire"][i] or "-") if r else "-",
                            fg=RED if (r and raw is None) else DIM)
                c[2].config(text="-" if raw is None else str(raw))
                if kind == "bits":
                    txt = gdat2.dio_text(raw)
                    fg = GREEN if txt in ("OPEN", "CLOSE") else \
                        RED if "invalid" in txt else DIM
                elif val is None:
                    # raw None = the token was not 8 hex digits at all.
                    # raw set but val None = bits that spell NaN/inf, i.e. not
                    # a float. Different faults, so they read differently.
                    txt, fg = ("not a float" if raw is not None
                               else "bad hex"), RED
                else:
                    txt = "%.3f" % val if kind == "f32" else "%d" % val
                    fg = RED if i in bad_range else TEXT
                c[3].config(text=txt, fg=DIM if stale else fg)

                # Liveness. "constant" is deliberately not red: on this firmware
                # attitude is quantised to 0.1 deg, so a still unit repeats one
                # value and that is healthy. Amber means unproven - move the
                # unit and watch it go green - not broken. Exact zero forever is
                # a different claim and does read as a fault.
                w = self.watch[i]
                if not w.session_raw:
                    lv, lfg = "-", DIM
                elif w.ever_moved:
                    lv, lfg = "live  %d" % w.changes, GREEN
                elif w.session_raw == {0}:
                    lv, lfg = "zero", RED
                else:
                    res = w.resolution()
                    lv = "constant ?" + (" %gd" % res if res else "")
                    lfg = AMBER
                c[5].config(text=lv, fg=DIM if stale else lfg)
            if stale and r is not None:
                self.state_lab.config(text="STALE - no sentence for >1 s",
                                      fg=RED)
            elif r is not None and r["csum_ok"] is False:
                # These numbers came off a sentence that failed its checksum, so
                # they are shown but not trusted. Saying so is the difference
                # between a reading and a guess.
                self.state_lab.config(text="CHECKSUM FAILED - values suspect",
                                      fg=RED)

            if s["tail"] != self.rawbox.get("1.0", "end-1c"):
                self.rawbox.delete("1.0", "end")
                self.rawbox.insert("1.0", s["tail"])
                self.rawbox.see("end")
        self._job = self.after(self.period, self.tick)

    def close(self):
        for attr in ("_job", "_rjob"):          # see Mixer.close
            if getattr(self, attr, None):
                self.after_cancel(getattr(self, attr))
                setattr(self, attr, None)
        for lk in (list(self.links.values()) + list(self.alt_links.values())
                   + list(self.imu_links.values())):
            lk.close()
        self.links.clear()
        self.alt_links.clear()
        self.imu_links.clear()


class Altimeter(tk.Frame):
    """Ping1D altimeter panel, modelled on the manufacturer's Ping1DPanel.

    Their GUI is the reference for this sensor and it exposes four settings -
    ping enable, gain, ping interval, speed of sound - behind an "Apply
    Settings" button. Those are not decoration. Measured on buoy 3, the device
    powers up at ping_interval = 250 ms, which reads confidence 0 and a range
    wandering 54-92 m; writing their defaults (50 ms) took confidence to
    22-51 % and settled the range. So the controls are reproduced here, with
    their ranges and their defaults.

    The transport underneath is ping1d.PingLink rather than brping. That was
    checked against their code on the real device, not assumed: brping's
    get_distance() and this decoder return the same distances and the same
    confidences. brping is also not safe to depend on here - the version
    installed on this machine has no connect_tcp(), which is exactly why their
    own code carries a TCPSocketIO fallback, and the standalone GUI must run
    with nothing installed but numpy.
    """

    # Their combo, verbatim: the index is the gain setting written to the
    # device, the number in brackets is the amplifier gain it selects.
    GAINS = ("0 (0.6)", "1 (1.8)", "2 (5.5)", "3 (12.9)",
             "4 (30.2)", "5 (66.1)", "6 (144.0)")

    def __init__(self, master, fps=10.0):
        super().__init__(master, bg=BG)
        self.period = int(1000 / fps)
        self.link = None
        self.buoy = tk.StringVar(value="buoy %d" % gdat2.ACTIVE_BUOY)
        self.host = tk.StringVar(
            value=gdat2.buoy_ip(gdat2.ACTIVE_BUOY, gdat2.ROLE_ALTIMETER))
        self.port = tk.StringVar(value=str(ping1d.PING_PORT))
        self.enable = tk.BooleanVar(value=bool(ping1d.VENDOR_DEFAULTS["enable"]))
        self.gain = tk.StringVar(value=self.GAINS[ping1d.VENDOR_DEFAULTS["gain"]])
        self.interval = tk.IntVar(value=ping1d.VENDOR_DEFAULTS["interval"])
        self.sos = tk.IntVar(value=ping1d.VENDOR_DEFAULTS["sos"])
        self._build()
        self._job = self.after(self.period, self.tick)

    # ------------------------------------------------------------ layout --
    def _build(self):
        bar = tk.Frame(self, bg=PANEL)
        bar.pack(fill="x")
        tk.Label(bar, text=" Ping1D ", bg=PANEL, fg=TEXT,
                 font=("Consolas", 10, "bold")).pack(side="left",
                                                     padx=(8, 2), pady=7)
        om = tk.OptionMenu(bar, self.buoy, *[n for n, _ip in gdat2.ALTIMETERS],
                           command=self.pick_buoy)
        om.config(bg=GRID, fg=TEXT, font=("Consolas", 9), borderwidth=0,
                  highlightthickness=0, activebackground=GREEN, width=7)
        om["menu"].config(bg=PANEL, fg=TEXT, font=("Consolas", 9))
        om.pack(side="left", padx=(4, 8))
        tk.Entry(bar, textvariable=self.host, width=15, bg=BG, fg=TEXT,
                 insertbackground=TEXT, font=("Consolas", 9),
                 borderwidth=0).pack(side="left", padx=(6, 2))
        tk.Label(bar, text=":", bg=PANEL, fg=DIM).pack(side="left")
        tk.Entry(bar, textvariable=self.port, width=6, bg=BG, fg=TEXT,
                 insertbackground=TEXT, font=("Consolas", 9),
                 borderwidth=0).pack(side="left", padx=2)
        self.btn = tk.Button(bar, text="connect", command=self.toggle,
                             bg=GRID, fg=TEXT, font=("Consolas", 9),
                             borderwidth=0, activebackground=GREEN, padx=12)
        self.btn.pack(side="left", padx=10)
        self.state_lab = tk.Label(bar, text="idle", bg=PANEL, fg=DIM,
                                  font=("Consolas", 8), anchor="e")
        self.state_lab.pack(side="right", padx=10)

        # ---- readout, their layout: distance large, confidence beneath it
        read = tk.Frame(self, bg=BG)
        read.pack(fill="x", pady=(26, 8))
        self.lbl_dist = tk.Label(read, text="--- m", bg=BG, fg=DIM,
                                 font=("Consolas", 40, "bold"))
        self.lbl_dist.pack()
        self.lbl_conf = tk.Label(read, text="confidence --", bg=BG, fg=DIM,
                                 font=("Consolas", 16))
        self.lbl_conf.pack(pady=(2, 0))
        # Their GUI shows a bare percentage. This adds what the percentage
        # MEANS, because 90 m at 0 % is not a reading and the number alone
        # does not say so.
        self.lbl_note = tk.Label(read, text="", bg=BG, fg=DIM,
                                 font=("Consolas", 9))
        self.lbl_note.pack(pady=(6, 0))

        # ---- settings: their controls, their ranges, their defaults
        box = tk.LabelFrame(self, text=" sensor settings ", bg=BG, fg=DIM,
                            font=("Consolas", 9), borderwidth=1,
                            relief="solid")
        box.pack(fill="x", padx=40, pady=(18, 10))
        grid = tk.Frame(box, bg=BG)
        grid.pack(padx=14, pady=10)

        def label(txt, r):
            tk.Label(grid, text=txt, bg=BG, fg=TEXT, anchor="w",
                     font=("Consolas", 9)).grid(row=r, column=0, sticky="w",
                                                padx=(0, 12), pady=3)

        label("ping", 0)
        self.cb_en = tk.Checkbutton(
            grid, text=" enabled", variable=self.enable, bg=BG, fg=TEXT,
            selectcolor=GRID, activebackground=BG, activeforeground=TEXT,
            font=("Consolas", 9), borderwidth=0, highlightthickness=0)
        self.cb_en.grid(row=0, column=1, sticky="w")

        label("gain", 1)
        gm = tk.OptionMenu(grid, self.gain, *self.GAINS)
        gm.config(bg=GRID, fg=TEXT, font=("Consolas", 9), borderwidth=0,
                  highlightthickness=0, width=10, anchor="w")
        gm["menu"].config(bg=PANEL, fg=TEXT, font=("Consolas", 9))
        gm.grid(row=1, column=1, sticky="w", pady=3)

        label("interval", 2)
        tk.Spinbox(grid, from_=10, to=5000, textvariable=self.interval,
                   width=8, bg=BG, fg=TEXT, buttonbackground=GRID,
                   insertbackground=TEXT, font=("Consolas", 9),
                   borderwidth=0, highlightthickness=0).grid(
                       row=2, column=1, sticky="w", pady=3)
        tk.Label(grid, text="ms   (device boots at 250 - that reads conf 0)",
                 bg=BG, fg=DIM, font=("Consolas", 8)).grid(row=2, column=2,
                                                           sticky="w", padx=8)

        label("sound velocity", 3)
        tk.Spinbox(grid, from_=300000, to=2000000, increment=1000,
                   textvariable=self.sos, width=8, bg=BG, fg=TEXT,
                   buttonbackground=GRID, insertbackground=TEXT,
                   font=("Consolas", 9), borderwidth=0,
                   highlightthickness=0).grid(row=3, column=1, sticky="w",
                                              pady=3)
        tk.Label(grid, text="mm/s  (1500000 water, ~343000 air)",
                 bg=BG, fg=DIM, font=("Consolas", 8)).grid(row=3, column=2,
                                                           sticky="w", padx=8)

        self.apply_btn = tk.Button(grid, text="apply settings",
                                   command=self.apply_settings, bg=GRID,
                                   fg=TEXT, font=("Consolas", 9),
                                   borderwidth=0, activebackground=GREEN,
                                   padx=14)
        self.apply_btn.grid(row=4, column=1, sticky="w", pady=(10, 2))
        self.applied_lab = tk.Label(grid, text="", bg=BG, fg=DIM,
                                    font=("Consolas", 8))
        self.applied_lab.grid(row=4, column=2, sticky="w", padx=8)

        self.info_lab = tk.Label(self, text="", bg=BG, fg=DIM, anchor="w",
                                 font=("Consolas", 9), justify="left")
        self.info_lab.pack(fill="x", padx=40, pady=(4, 12))

    # ------------------------------------------------------------- logic --
    def pick_buoy(self, name):
        for nm, ip in gdat2.ALTIMETERS:
            if nm == name:
                self.host.set(ip)
                if self.link:           # retarget an open link
                    self.toggle()
                    self.toggle()
                break

    def settings_dict(self):
        return {"enable": 1 if self.enable.get() else 0,
                "gain": self.GAINS.index(self.gain.get()),
                "interval": int(self.interval.get()),
                "sos": int(self.sos.get())}

    def toggle(self):
        if self.link:
            self.link.close()
            self.link = None
            self.btn.config(text="connect", activebackground=GREEN)
            self.state_lab.config(text="disconnected", fg=DIM)
            return
        try:
            port = int(self.port.get())
        except ValueError:
            self.state_lab.config(text="bad port", fg=RED)
            return
        self.link = ping1d.PingLink(self.host.get().strip(), port,
                                    settings=self.settings_dict())
        self.link.start()
        self.btn.config(text="disconnect", activebackground=RED)

    def apply_settings(self):
        """Write the settings to a live sensor, as their Apply button does."""
        if not self.link or not self.link.sock:
            self.applied_lab.config(text="not connected", fg=AMBER)
            return
        st = self.settings_dict()
        try:
            for key in ("enable", "gain", "interval", "sos"):
                self.link.sock.sendall(ping1d.set_message(key, st[key]))
                time.sleep(0.25)
        except OSError as e:
            self.applied_lab.config(text="send failed: %s" % e, fg=RED)
            return
        with self.link.lock:
            self.link.applied = dict(st)
        self.applied_lab.config(
            text="sent: interval %d ms, gain %d, sos %d, ping %s"
                 % (st["interval"], st["gain"], st["sos"],
                    "on" if st["enable"] else "off"), fg=GREEN)

    def tick(self):
        if self.link:
            s = self.link.snapshot()
            live = s["t"] is not None and (time.time() - s["t"]) <= 3.0
            ok = s["state"] == "connected"
            self.state_lab.config(
                text="%s   %.0f/s   good %d   csum %d   timeouts %d"
                     % (s["state"], s["rate"], s["good"], s["bad"],
                        s["timeouts"]),
                fg=GREEN if (ok and live) else
                AMBER if "connect" in s["state"] else RED)

            d, c = s["dist"], s["conf"]
            if d is None:
                self.lbl_dist.config(text="--- m", fg=DIM)
                self.lbl_conf.config(text="confidence --", fg=DIM)
                self.lbl_note.config(text="")
            else:
                # Confidence decides how the range is PRESENTED. A number the
                # sonar has no faith in is shown dimmed and captioned rather
                # than in the same weight as a real fix - the difference
                # between a reading and a shrug, which their bare percentage
                # leaves the operator to work out.
                conf = c or 0
                strong = conf >= 30
                # Metres. The wire value is millimetres - see ping1d - and
                # the raw count stays in the caption so a decode can still be
                # checked against the bytes without converting in your head.
                self.lbl_dist.config(
                    text="%.2f m" % (d / 1000.0),
                    fg=DIM if not live else (TEXT if strong else AMBER))
                self.lbl_conf.config(
                    text="confidence %d %%" % conf,
                    fg=DIM if not live else (GREEN if strong else AMBER))
                if not live:
                    note = "stale - no reply within 3 s"
                elif conf == 0:
                    note = ("no echo. In air this is normal; the range shown "
                            "is the sonar's ceiling, not a measurement.")
                elif not strong:
                    note = "weak echo - treat the range as approximate"
                else:
                    note = "%d mm" % d
                self.lbl_note.config(
                    text=note, fg=DIM if (conf < 30 or not live) else TEXT)

            ap = s["applied"]
            self.info_lab.config(
                text=("answering on msg %s   |   settings written: %s"
                      % (s["answered_id"],
                         ", ".join("%s=%s" % kv for kv in sorted(ap.items()))
                         if ap else "none")))
        self._job = self.after(self.period, self.tick)

    def close(self):
        if getattr(self, "_job", None):
            self.after_cancel(self._job)
            self._job = None
        if self.link:
            self.link.close()
            self.link = None


class App(tk.Tk):
    """Window shell. Owns the notebook and shuts both tabs down cleanly."""

    def __init__(self, a):
        super().__init__()
        self.title("UATR Control Station")
        self.configure(bg=BG)
        self.minsize(MIN_W, MIN_H)

        # Open at a sensible fraction of the actual screen rather than a fixed
        # size - this runs on both a laptop and the lab's big panel, and a
        # hardcoded geometry is wrong on one of them.
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h = max(MIN_W, int(sw * 0.78)), max(MIN_H, int(sh * 0.82))
        self.geometry("%dx%d+%d+%d" % (w, h, (sw - w) // 2, max(0, (sh - h) // 3)))
        if getattr(a, "fullscreen", False):
            self.attributes("-fullscreen", True)
        elif getattr(a, "maximized", False):
            self._zoom()

        self._fs = bool(getattr(a, "fullscreen", False))
        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<Escape>", self.exit_fullscreen)

        style = ttk.Style(self)
        try:
            style.theme_use("clam")          # the only stock theme that lets
        except tk.TclError:                  # tab colours be set on Windows
            pass
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=PANEL, foreground=DIM,
                        padding=(16, 7), font=("Consolas", 10), borderwidth=0)
        style.map("TNotebook.Tab", background=[("selected", GRID)],
                  foreground=[("selected", TEXT)])

        nb = self.nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)

        # One tab per AFE. Each board streams on its OWN UDP port, so each tab
        # gets its own socket and its own receive thread - they never share a
        # port and cannot interleave. That separation is not a style choice: the
        # receive loop uses recv(), which discards the sender, so two boards on
        # one port would merge their sequence numbers into a single stream and
        # the loss figure would be meaningless for both.
        #
        # --port / --ip still override, for pointing one window at one board.
        self.rxs, self.mixers = [], []
        for n in a.nodes:
            port = a.port if a.port else ctrl.node_stream_port(n)
            ip   = a.ip   if a.ip   else ctrl.node_ip(n)
            rx = Receiver(port, a.bind)
            rx.start()
            mx = Mixer(nb, rx, a.fps, a.peak_hold, ip,
                       label="AFE %d  %s:%d   " % (n, ip, port))
            self.rxs.append(rx)
            self.mixers.append(mx)
            nb.add(mx, text="AFE %d" % n)

        self.tel = Telemetry(nb, a.gdat_mode, a.gdat_host, a.gdat_port)
        nb.add(self.tel, text="Telemetry")
        self.alt = Altimeter(nb)
        nb.add(self.alt, text="Altimeter")

        if a.gdat_connect:
            self.tel.toggle()
        self.protocol("WM_DELETE_WINDOW", self.close)

    def _zoom(self):
        """Maximise. 'zoomed' is Windows/macOS; X11 wants the WM hint."""
        try:
            self.state("zoomed")
        except tk.TclError:
            try:
                self.attributes("-zoomed", True)
            except tk.TclError:
                pass

    def toggle_fullscreen(self, _ev=None):
        self._fs = not self._fs
        self.attributes("-fullscreen", self._fs)
        return "break"

    def exit_fullscreen(self, _ev=None):
        # Escape only leaves fullscreen; it must not close the window, which is
        # what an unguarded Escape binding on the root would end up doing.
        if self._fs:
            self._fs = False
            self.attributes("-fullscreen", False)
        return "break"

    def close(self):
        for mx in self.mixers:
            mx.close()
        self.tel.close()
        self.alt.close()
        self.destroy()


def main():
    ap = argparse.ArgumentParser(description="UATR control station GUI")
    ap.add_argument("--nodes", default="1,2,3,4",
                    help="which AFEs to open tabs for, e.g. --nodes 1,3. "
                         "Each gets its own IP and stream port from ctrl.py, "
                         "mirroring C_NODE in top_system.vhd.")
    ap.add_argument("--port", type=int, default=None,
                    help="override the stream port for ALL tabs. Only useful "
                         "with a single node; two tabs on one port would fight "
                         "over the socket and one would receive nothing.")
    ap.add_argument("--bind", default="0.0.0.0")
    ap.add_argument("--fps", type=float, default=20.0)
    ap.add_argument("--peak-hold", type=float, default=2.0)
    ap.add_argument("--ip", default=None,
                    help="override the control IP for ALL tabs")
    ap.add_argument("--gdat-host", default=gdat2.DEFAULT_HOST,
                    help="aux_vcu address (client mode)")
    ap.add_argument("--gdat-buoy", type=int, choices=(1, 2, 3, 4),
                    help="pick the buoy by number instead of --gdat-host (%s)"
                         % ", ".join("%d=%s" % (i + 1, ip)
                                     for i, (_n, ip) in enumerate(gdat2.BUOYS)))
    ap.add_argument("--gdat-port", type=int, default=gdat2.DEFAULT_PORT)
    ap.add_argument("--gdat-mode", choices=("client", "server"),
                    default="client",
                    help="client dials the aux_vcu, server waits for it")
    ap.add_argument("--gdat-connect", action="store_true",
                    help="open the telemetry link at startup")
    ap.add_argument("--fullscreen", action="store_true",
                    help="start fullscreen (F11 toggles, Escape leaves)")
    ap.add_argument("--maximized", action="store_true",
                    help="start maximised")
    a = ap.parse_args()
    if a.gdat_buoy:
        a.gdat_host = gdat2.BUOYS[a.gdat_buoy - 1][1]

    try:
        a.nodes = [int(t) for t in a.nodes.replace(",", " ").split()]
    except ValueError:
        ap.error("--nodes wants a list of numbers, e.g. --nodes 1,2,3,4")
    if not a.nodes or any(n < 1 or n > 4 for n in a.nodes):
        ap.error("--nodes must be between 1 and 4")
    if len(set(a.nodes)) != len(a.nodes):
        ap.error("--nodes has a repeat. Two tabs on one board would open two "
                 "sockets on the same port, and only one of them receives.")
    # Fail here rather than opening four tabs that all watch one board and
    # silently show three dead panels.
    if a.port and len(a.nodes) > 1:
        ap.error("--port overrides every tab, so it only makes sense with a "
                 "single node: --nodes 2 --port 5006")

    App(a).mainloop()


if __name__ == "__main__":
    main()
