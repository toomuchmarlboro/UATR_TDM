library ieee;
use ieee.std_logic_1164.all;

entity tdm8_master is
    port (
        rst        : in  std_logic;
        clk_in     : in  std_logic;
        bclk_out   : out std_logic;
        lrclk_out  : out std_logic   -- The one and only true 96 kHz sync
    );
end entity tdm8_master;

architecture rtl of tdm8_master is
    -- LRCLK shape. Must agree with LR_MODE, bit 3 of the ADAU1978's SAI_CTRL1
    -- (register 0x06) - see the BOOT_ROM in adau_sequencer.
    --
    --   false -> 50% duty: high for 128 BCLKs, low for 128.  LR_MODE = 0
    --   true  -> one BCLK wide pulse per frame.              LR_MODE = 1
    --
    -- PULSE is the right choice here, despite being the harder signal to
    -- measure. 50% duty was tried for measurability - it averages 1.65 V where
    -- the 40 ns pulse averages 13 mV and no meter can see it. It does not work,
    -- and the reason is now established rather than guessed:
    --
    -- With a 256-BCLK frame a 50% duty LRCLK falls at BCLK 128, and in nonpulse
    -- mode the ADAU1978 frames on that FALLING edge. It therefore starts its
    -- slot 0 at BCLK 128 instead of BCLK 0, so every slot lands exactly 4
    -- positions late in tdm8_rx's decode (4 slots x 32 BCLKs = 128). Observed
    -- on hardware 2026-08-12: channel 5 carried channel 1's audio and channel
    -- 16 carried channel 12's - a uniform +4 shift, which wraps the two halves
    -- of each line into each other.
    --
    -- BEWARE when reading any older 50%-duty measurement. Because the halves
    -- swap, per-part conclusions from those runs are MISLABELLED: what looked
    -- like "the slots 1-4 part ran clean while slots 5-8 managed 30/40" was the
    -- two parts reported under each other's names. An earlier version of this
    -- comment recorded that swapped reading as though it were a real per-part
    -- difference, and it was used on 2026-08-12 to justify re-enabling 50% duty.
    -- It is not evidence about either part.
    --
    -- A pulse puts the only edge at BCLK 0 and leaves the rest of the frame
    -- quiet, which is what Table 21 intends for TDM; 50% duty is the I2S
    -- convention. LR_POL (0x04 bit 7, currently 0) inverts which edge the part
    -- frames on, so 50% duty could in principle be made to align - but pulse
    -- mode is the validated configuration and the only thing 50% duty ever
    -- bought was being visible on a handheld meter. Not worth revisiting.
    --
    -- Both shapes are safe downstream: tdm8_rx and tdm16_merge edge-detect the
    -- sync rather than testing its level, so neither cares which is sent.
    -- Must match LR_MODE, register 0x06 bit 3, in the adau_sequencer BOOT_ROM.
    constant C_LR_PULSE : boolean := true;

    -- How many BCLKs wide the pulse is. The datasheet requires "at least one
    -- BCLK wide" (Figure 26) and sets no maximum, and one BCLK is what this
    -- generated before - the bare minimum, with no margin at all.
    --
    -- One BCLK is 40.7 ns at 24.576 MHz. Measured rise time on LRCLK at the ADC
    -- pin is ~20 ns, so with a comparable fall the signal is above the
    -- ADAU1978's VIH (0.7 x IOVDD = 2.31 V) for appreciably less than one BCLK
    -- even though the driver holds it high for a full one. The part then sees a
    -- sub-minimum pulse, and because each of the four LRCLK nets has its own
    -- rise time it fails per part rather than everywhere: one ADC framed
    -- reliably, one intermittently, two almost never.
    --
    -- 4 BCLKs = 163 ns gives 4x margin and still lands entirely inside slot 1's
    -- 32-BCLK window on a separate wire, so it cannot collide with data. The
    -- frame boundary is unchanged - it is the RISING edge, and that still
    -- occurs on the transition into bit_cnt = 0.
    constant C_LR_PULSE_BCLKS : integer range 1 to 16 := 4;

    -- 96 kHz via 256 x fS: 8 slots x 32 BCLKs. BCLK = MCLK = 24.576 MHz, from
    -- PLL output c2. The 32-BCLK slot carries 24-bit data with 8 pad BCLKs,
    -- which is what gives C_BIT_ADJ its -8..+8 of room in tdm8_rx.
    --
    -- 192 x fS (8 x 24 BCLKs, 18.432 MHz) was tried for its wider capture
    -- window and abandoned: only U19 locked its PLL, the other three read
    -- PLL_LOCK=0 at 18.432 MHz while all four lock at 24.576 MHz. See the note
    -- in tdm8_rx.vhd. The capture margin that 192 x fS was meant to buy is
    -- obtained instead by registering SDATA on the FALLING edge of BCLK, which
    -- makes the path falling-to-falling - a full 40.7 ns period. Quartus
    -- reports 19.8 ns of setup slack on sdata_in_A with that in place.
    constant C_FRAME_BCLKS : integer := 256;

    -- Range tracks C_FRAME_BCLKS. This was hardcoded "range 0 to 255", which is
    -- wide enough for 256 and 192 but silently breaks the design for any longer
    -- frame: at C_FRAME_BCLKS = 320 the counter wraps at 256 and never equals
    -- C_FRAME_BCLKS - 1, so the frame boundary below never fires and LRCLK stops
    -- toggling altogether. Deriving the range makes that a compile error instead.
    signal bit_cnt : integer range 0 to C_FRAME_BCLKS - 1 := 0;
begin

    bclk_out <= clk_in;

    process(clk_in, rst)
    begin
        if rst = '1' then
            bit_cnt <= 0;
            lrclk_out <= '0';
        -- LRCLK transitions on the FALLING edge of BCLK.
        --
        -- CORRECTION 2026-08-16, from the datasheet rather than from inference.
        -- Table 5, page 5, ADC SERIAL PORT, quoted verbatim:
        --
        --   tALS   10 ns min   "LRCLK setup to BCLK rising, slave mode"
        --   tALH    5 ns min   "LRCLK hold from BCLK rising, slave mode"
        --   tABDD  18 ns max   "SDATAOUTx delay from BCLK falling"
        --
        -- The part samples LRCLK on the BCLK RISING edge. It launches SDATAOUT
        -- from the falling edge. Those are different edges and both are correct;
        -- BCLKEDGE = 0 sets the OUTPUT launch edge only, which is what tABDD
        -- measures. The previous comment here read BCLKEDGE as also moving the
        -- LRCLK sampling edge, and that was wrong.
        --
        -- Under the correct reading, launching LRCLK on the RISING edge - which
        -- is what this did from 927aac7 until now - puts the LRCLK transition on
        -- the very edge the part samples it. Not half a period away from it, ON
        -- it. Quartus measures the residual as a hold violation at the pads:
        --
        --   Slow 85C   hold slack -3.853 ns    LRCLK trails BCLK by 1.257 ns
        --   Slow  0C   hold slack -4.024 ns                        1.086 ns
        --   Fast  0C   hold slack -4.503 ns                        0.607 ns
        --
        -- against tALH = 5 ns. (Read straight off TDM_UATR.sta.rpt as data delay
        -- minus clock skew: 4.161 - 2.904, 3.717 - 2.631, 2.166 - 1.559. No sign
        -- convention needed - that is simply how much later LRCLK leaves its pad
        -- than BCLK leaves its.) Whether any given part latches the frame sync at
        -- edge N or misses it and waits for N+1 is then decided by U1's output
        -- delay versus U2's and by trace length, i.e. PER PART, and it drifts
        -- with temperature and supply. One part clean, three intermittent, no
        -- fault counter touched, and a new cable changing nothing, all follow.
        --
        -- Launching on the FALLING edge puts the transition 20.35 ns after the
        -- sampling edge at 24.576 MHz. Required window, relative to the BCLK
        -- rising edge at the part: [tALH, T - tALS] = [5.0, 30.695] ns. Delivered
        -- across all three corners: 20.35 + 0.607..1.257 = 20.96..21.61 ns.
        -- Margin 16 ns on the hold side and 9 ns on the setup side, against a few
        -- ns of U1-versus-U2 buffer skew and cable delay. The old arrangement had
        -- 0.6 ns of the wrong sign.
        --
        -- CONSEQUENCE FOR C_BIT_ADJ. The part now frames one BCLK later than it
        -- did when it won the race, so tdm8_rx's C_BIT_ADJ moves 0 -> -1. It is
        -- changed there, and the reasoning and the fallback are recorded in that
        -- file. The dropout percentages, which are what tests THIS change, do not
        -- depend on C_BIT_ADJ.
        --
        -- If BCLKEDGE (0x04 bit 6) is ever set to 1, re-read Table 5 before
        -- touching this: BCLKEDGE moves the part's output launch edge, and on the
        -- evidence above it does not move the LRCLK input sampling edge at all.
        -- check_sync.py enforces the pairing.
        elsif falling_edge(clk_in) then
            
            if bit_cnt = C_FRAME_BCLKS - 1 then
                bit_cnt <= 0;
            else
                bit_cnt <= bit_cnt + 1;
            end if;

            -- Either shape puts the frame boundary on the same BCLK: LRCLK is
            -- driven high on the transition into bit_cnt = 0. Only the falling
            -- edge differs - after one BCLK, or after 128.
            if bit_cnt = C_FRAME_BCLKS - 1 then
                lrclk_out <= '1';
            elsif C_LR_PULSE then
                -- falls on the transition into bit_cnt = C_LR_PULSE_BCLKS, so
                -- the high time is exactly that many BCLKs. With the constant
                -- at 1 this is the old one-BCLK pulse, bit for bit.
                if bit_cnt = C_LR_PULSE_BCLKS - 1 then
                    lrclk_out <= '0';
                end if;
            elsif bit_cnt = C_FRAME_BCLKS/2 - 1 then
                lrclk_out <= '0';
            end if;
            
        end if;
    end process;

end architecture rtl;