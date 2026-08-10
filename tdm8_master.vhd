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
    -- the 81 ns pulse averages 13 mV and no meter can see it - but with 8 slots
    -- of 32 BCLKs the frame is 256 BCLKs and a 50% duty LRCLK falls at BCLK
    -- 128, which is exactly the slot 4 / slot 5 boundary. That is the BCLK
    -- where the part holding slots 5-8 has to take over the line. Measured:
    -- with 50% duty the slots 1-4 part ran 40/40 windows clean while the
    -- slots 5-8 part on the same line managed 30/40, and the same ordering
    -- held on the other TDM line. A pulse puts the only edge at BCLK 0 and
    -- leaves the rest of the frame quiet, which is what Table 21 intends for
    -- TDM; 50% duty is the I2S convention.
    --
    -- Both shapes are safe downstream: tdm8_rx and tdm16_merge edge-detect the
    -- sync rather than testing its level, so neither cares which is sent.
    -- Must match LR_MODE, register 0x06 bit 3, in the adau_sequencer BOOT_ROM.
    constant C_LR_PULSE : boolean := true;

    -- How many BCLKs wide the pulse is. The datasheet requires "at least one
    -- BCLK wide" (Figure 26) and sets no maximum, and one BCLK is what this
    -- generated before - the bare minimum, with no margin at all.
    --
    -- One BCLK is 81.4 ns at 12.288 MHz. Measured rise time on LRCLK at the ADC
    -- pin is ~20 ns, so with a comparable fall the signal is above the
    -- ADAU1978's VIH (0.7 x IOVDD = 2.31 V) for appreciably less than one BCLK
    -- even though the driver holds it high for a full one. The part then sees a
    -- sub-minimum pulse, and because each of the four LRCLK nets has its own
    -- rise time it fails per part rather than everywhere: one ADC framed
    -- reliably, one intermittently, two almost never.
    --
    -- 4 BCLKs = 326 ns gives 4x margin and still lands entirely inside slot 1's
    -- 32-BCLK window on a separate wire, so it cannot collide with data. The
    -- frame boundary is unchanged - it is the RISING edge, and that still
    -- occurs on the transition into bit_cnt = 0.
    constant C_LR_PULSE_BCLKS : integer range 1 to 16 := 4;

    -- 96 kHz via 192 x fS: 8 slots x 24 BCLKs. BCLK = MCLK = 18.432 MHz.
    -- 256 x fS was the old 96 kHz config but needs 24.576 MHz, which leaves
    -- only a 20.3 ns capture window against the ADAU1978's 18 ns clock-to-out
    -- plus the U2 buffer and cable - negative margin. 192 x fS gives 27.1 ns.
    constant C_FRAME_BCLKS : integer := 256;
    signal bit_cnt : integer range 0 to 255 := 0;
begin

    bclk_out <= clk_in;

    process(clk_in, rst)
    begin
        if rst = '1' then
            bit_cnt <= 0;
            lrclk_out <= '0';
        -- LRCLK transitions on the RISING edge of BCLK.
        --
        -- This was on the falling edge, on the assumption that "a TDM slave
        -- latches on the rising edge". The ADAU1978 does not: BCLKEDGE, bit 6 of
        -- register 0x04, selects which BCLK edge the serial port acts on, and we
        -- write 0x04 = 0x3F, so BCLKEDGE = 0 = "Data Changes on Falling Edge"
        -- (Table 19). The falling edge IS the part's active edge, so launching
        -- LRCLK there changed it at the instant the part sampled it - zero setup.
        -- A zero-setup path fails per part according to trace and buffer delay,
        -- is indifferent to the pulse's width and shape, drifts with temperature,
        -- and leaves I2C and the PLL untouched: the whole symptom set.
        --
        -- Launching on the rising edge gives half a BCLK, 40.7 ns at 12.288 MHz,
        -- before the part's falling-edge sample. The data direction stays correct
        -- too: the part launches SDATA on the falling edge and tdm8_rx samples on
        -- the rising edge, the same half period. Skew between the LRCLK path
        -- through U1 and the BCLK path through U2 is a few ns against that 40.7.
        --
        -- If BCLKEDGE is ever set to 1 this must move back to the falling edge.
        -- check_sync.py enforces the pairing.
        elsif rising_edge(clk_in) then
            
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