#!/usr/bin/env python3
"""
Cycle-accurate model of tdm8_master -> ADAU1978 -> tdm8_rx -> tdm16_merge,
transcribed line for line from the VHDL, used to settle C_BIT_ADJ arithmetically.

Questa is installed but unlicensed, so this stands in for a simulation. It is
only as good as the transcription, which is why each block below quotes the RTL
it mirrors. What it decides is the frame arithmetic - given an assumption about
how many BCLKs after the sync edge the ADC presents its first bit, which
C_BIT_ADJ decodes correctly. It cannot tell you the silicon's real launch phase.

    python sim_chain.py
"""

import re

# Read the frame length from the RTL instead of hardcoding it, so switching
# between 256 x fS (32-BCLK slots) and 192 x fS (24-BCLK slots) does not leave
# this model quietly describing the wrong design.
def _frame():
    import re as _re
    src = open("tdm8_master.vhd", encoding="utf-8", errors="replace").read()
    m = _re.search(r'C_FRAME_BCLKS\s*:\s*integer\s*:=\s*(\d+)', src)
    if m:
        return int(m.group(1))
    m = _re.search(r'if bit_cnt = (\d+) then', src)
    return int(m.group(1)) + 1 if m else 256

FRAME  = _frame()     # BCLKs per frame
SLOTW  = FRAME // 8   # 8 TDM slots
DATAW  = 24
SREG   = 264          # tdm8_rx shift_reg width


def rtl_const(path, name, cast=int):
    src = open(path, encoding="utf-8", errors="replace").read()
    m = re.search(name + r'\s*:\s*\w+(?:\s+range[^:]*)?\s*:=\s*(-?\w+)', src)
    return cast(m.group(1)) if m else None


class Master:
    """tdm8_master.vhd, rising_edge(clk_in):
         if bit_cnt = C_FRAME_BCLKS-1 then bit_cnt <= 0 else bit_cnt + 1
         if bit_cnt = C_FRAME_BCLKS-1   then lrclk <= '1'
         elsif bit_cnt = PULSE_BCLKS-1  then lrclk <= '0'

    The wrap value is FRAME-1, taken from the RTL. It was hardcoded 255 here,
    which silently kept modelling a 256-BCLK frame after the design moved to 192.
    """
    def __init__(self, pulse_bclks):
        self.bit_cnt = 0
        self.lrclk = 0
        self.pulse = pulse_bclks

    def rising(self):
        bc, lr = self.bit_cnt, self.lrclk       # read pre-edge
        self.bit_cnt = 0 if bc == FRAME - 1 else bc + 1
        if bc == FRAME - 1:
            self.lrclk = 1
        elif bc == self.pulse - 1:
            self.lrclk = 0
        else:
            self.lrclk = lr


class Adc:
    """ADAU1978, BCLKEDGE=0 so data changes on the FALLING edge of BCLK.
       Left justified: 24 data bits then 8 pad BCLKs in each 32-BCLK slot.
       DRV_HIZ=1 outside its own slots; the 10k pulldown gives 0.
    """
    def __init__(self, payloads, launch):
        self.n = -1
        self.prev_lr = 0
        self.sdata = 0
        self.payloads = payloads          # list of 8 ints, 24-bit
        self.launch = launch

    def falling(self, lrclk):
        if lrclk == 1 and self.prev_lr == 0:
            self.n = 0
        elif self.n >= 0:
            self.n += 1
        self.prev_lr = lrclk

        v = 0
        if self.n >= self.launch:
            k = self.n - self.launch
            slot, bitpos = k // SLOTW, k % SLOTW
            if slot < 8 and bitpos < DATAW:
                v = (self.payloads[slot] >> (DATAW - 1 - bitpos)) & 1
        self.sdata = v


class Rx:
    """tdm8_rx.vhd, rising_edge(bclk_in):
         lrclk_d   <= lrclk_in
         shift_reg <= shift_reg(262 downto 0) & sdata_in   -- index 0 = newest
         on lrclk_in='1' and lrclk_d='0':
             ch_data_out(191-24k downto 168-24k)
                 <= shift_reg(255+adj-32k downto 232+adj-32k)
    """
    def __init__(self, adj):
        self.sreg = 0
        self.lrclk_d = 0
        self.lrclk_d2 = 0
        self.sdata_f = 0        # falling-edge input register
        self.adj = adj
        self.ch = [0] * 8
        self.captured = False

    @staticmethod
    def adj_legal(adj):
        """The lowest slice index is (FRAME-1-DATAW+1) + adj - SLOTW*7, and with
        24-BCLK slots that reduces to adj itself - so a negative C_BIT_ADJ makes
        the VHDL slice shift_reg(22 downto -1), an illegal range. With 32-BCLK
        slots there were 8 spare bits per slot and adj could go to -8."""
        low  = (FRAME - DATAW) + adj - SLOTW * 7
        high = (FRAME - 1) + adj
        return low >= 0 and high <= SREG - 1

    def bit(self, i):
        if i < 0 or i >= SREG:
            return 0
        return (self.sreg >> i) & 1

    def rising(self, sdata, lrclk):
        # capture one clock AFTER the sync edge, matching tdm8_rx
        fire = (self.lrclk_d == 1 and self.lrclk_d2 == 0)
        if fire:
            for k in range(8):
                hi = (FRAME - 1) + self.adj - SLOTW * k
                v = 0
                for b in range(DATAW):          # hi down to hi-23, MSB first
                    v = (v << 1) | self.bit(hi - b)
                self.ch[k] = v
            self.captured = True
        self.lrclk_d2 = self.lrclk_d
        self.lrclk_d = lrclk
        self.sreg = ((self.sreg << 1) | self.sdata_f) & ((1 << SREG) - 1)


def run(launch, adj, pulse_bclks, frames=10):
    pay_a = [0xA10000 + s * 0x1111 for s in range(8)]
    m   = Master(pulse_bclks)
    adc = Adc(pay_a, launch)
    rx  = Rx(adj)
    caps = []
    for _ in range(frames * FRAME):
        rx.rising(adc.sdata, m.lrclk)           # both read pre-edge values
        m.rising()
        if rx.captured:
            caps.append(list(rx.ch))
            rx.captured = False
        # both the ADC and the FPGA's half-cycle register act on this edge, and
        # both read pre-edge values, so sdata_f takes the bit the ADC drove last
        rx.sdata_f = adc.sdata
        adc.falling(m.lrclk)                    # ADC acts on the falling edge
    return pay_a, caps


def main():
    pulse = rtl_const("tdm8_master.vhd", "C_LR_PULSE_BCLKS") or 1
    adj_rtl = rtl_const("tdm8_rx.vhd", "C_BIT_ADJ")
    print("from the RTL: frame = %d BCLKs, %d BCLKs/slot, "
          "C_LR_PULSE_BCLKS = %d, C_BIT_ADJ = %+d"
          % (FRAME, SLOTW, pulse, adj_rtl))
    print()

    # 1. LRCLK shape
    m = Master(pulse)
    edges, hi = [], 0
    prev = 0
    for i in range(3 * FRAME):
        if m.lrclk == 1 and prev == 0:
            edges.append(i)
        if m.lrclk == 1:
            hi += 1
        prev = m.lrclk
        m.rising()
    period = edges[1] - edges[0] if len(edges) > 1 else 0
    hi_per_frame = hi / max(1, len(edges))
    print("LRCLK: period %d BCLKs, high %.0f BCLKs per frame  -> %s"
          % (period, hi_per_frame,
             "OK" if period == FRAME and hi_per_frame == pulse else "WRONG"))
    if SLOTW == DATAW:
        print("      %d-BCLK slots hold %d-bit data exactly, so there are no pad"
              % (SLOTW, DATAW))
        print("      bits and left justified is mandatory - I2S delays data one")
        print("      BCLK from LRCLK, which would push the LSB out of the slot.")
    print()

    # 2. which (launch, adj) pairs decode correctly
    print("decode matrix: ADC launch offset vs C_BIT_ADJ")
    print("  launch |  " + "  ".join("%+3d" % a for a in range(-4, 9)))
    print("  -------+" + "-" * (5 * 13))
    good = []
    for launch in range(0, 3):
        row = []
        for adj in range(-4, 9):
            if not Rx.adj_legal(adj):
                row.append(" xx ")          # illegal slice range in the VHDL
                continue
            pay, caps = run(launch, adj, pulse)
            ok = len(caps) >= 3 and caps[-1] == pay
            row.append(" OK " if ok else "  . ")
            if ok:
                good.append((launch, adj))
        print("    %+3d  |  %s" % (launch, " ".join(row)))
    print()
    if good:
        for launch, adj in good:
            print("  ADC presents its first bit %d BCLK(s) after the sync edge"
                  " -> C_BIT_ADJ = %+d" % (launch, adj))
    else:
        print("  no combination decoded correctly - the chain is broken"
              " independently of alignment")
    print()

    # 3. what the RTL's own C_BIT_ADJ actually produces
    print("with C_BIT_ADJ = %+d as currently set in tdm8_rx.vhd:" % adj_rtl)
    for launch in range(0, 3):
        pay, caps = run(launch, adj_rtl, pulse)
        got = caps[-1] if caps else [0] * 8
        print("  launch %+d: ch1 got 0x%06X want 0x%06X   %s"
              % (launch, got[0], pay[0],
                 "OK" if got == pay else "MISMATCH"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
