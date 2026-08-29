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


class Telemetry(tk.Frame):
    """$GDAT2 sensor telemetry from the aux_vcu, over TCP.

    A different device on a different transport from everything else here, so
    it shares no state with the mixer beyond the window - if the aux_vcu is
    absent or the FPGA is unplugged, the other tab carries on regardless.

    ulRaw fields arrive as 8 hex digits; seq and cnt as decimal. The wire text
    is shown next to the decoded value for every field, so a decode that goes
    wrong can be checked against the bytes that produced it without a capture.
    """

    ROW_H = 26

    def __init__(self, master, mode, host, port, fps=10.0):
        super().__init__(master, bg=BG)
        self.period = int(1000 / fps)
        self.link = None
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
                if self.link:           # retarget an open link immediately
                    self.toggle()
                    self.toggle()
                break

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
        self.state_lab = tk.Label(bar, text="idle", bg=PANEL, fg=DIM,
                                  font=("Consolas", 8), anchor="e")
        self.state_lab.pack(side="right", padx=10)

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
        # A fresh link is a fresh session: carrying "it moved earlier" across a
        # reconnect would let a dead field inherit a previous unit's proof.
        for w in self.watch:
            w.__init__(w.name)
        self.last_t = None
        self.link = gdat2.Link(self.mode.get(), self.host.get().strip(), port)
        self.link.start()
        self.btn.config(text="disconnect", activebackground=RED)

    def tick(self):
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
