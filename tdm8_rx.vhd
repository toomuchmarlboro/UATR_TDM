library ieee;
use ieee.std_logic_1164.all;

entity tdm8_rx is
    port (
        rst         : in  std_logic;
        bclk_in     : in  std_logic;
        lrclk_in    : in  std_logic;
        sdata_in    : in  std_logic;
        ch_data_out : out std_logic_vector(191 downto 0)
    );
end entity tdm8_rx;

architecture rtl of tdm8_rx is
    -- BCLKs to shift the capture window, tunable -7..+8 (the register carries
    -- slack either side). NEGATIVE moves the window later in the frame.
    -- -1 was found empirically: at 0 channels 9-16 showed full-scale 8388607
    -- spikes and power-of-two minima; at -1 they read a clean -66..-78 dBFS
    -- noise floor. +1 made it worse, railing channels 1-4.
    --
    -- Judge this by the channel statistics, not by --align. With no phantom
    -- power and floating inputs there is no signal for a sample-to-sample
    -- correlation metric to work with, and the scan ties across many offsets.
    -- +7, derived from the raw capture rather than guessed. With the window at
    -- -1 the 8 pad BCLKs of slot 4 were active in 100% of frames while slot 4's
    -- 24 data BCLKs were active in only 10.7% - impossible if the part owning
    -- slot 4 drives both. Those pad BCLKs were carrying the next slot's data,
    -- i.e. the ADCs place data 8 BCLKs EARLIER than this window looked. Larger
    -- adj indexes older bits, so -1 + 8 = +7. Every one of the twelve
    -- data/pad activity figures on TDM1 is consistent with that offset and no
    -- other. Confirm with "udp_monitor.py --align": best offset should be 0.
    constant C_BIT_ADJ : integer := -1;

    -- RAW CAPTURE MODE. Instead of extracting 24 bits from each 32-BCLK slot,
    -- publish the first 192 BCLKs of the frame verbatim - slots 1 to 6, which
    -- covers both parts on this line (slots 1-4 and 5-6). The host then sees
    -- the actual bit pattern on SDATA rather than an interpretation of it, so
    -- "is the far part driving its slots at all" becomes something you look at
    -- rather than infer. Decode with rawview.py. Audio is meaningless here.
    constant C_RAW_CAPTURE : boolean := false;
    signal shift_reg : std_logic_vector(263 downto 0) := (others => '0');

    -- Capture on the RISING EDGE of LRCLK rather than on the level. With the
    -- old one-BCLK pulse the two were the same thing, so this changes nothing
    -- there; with a 50% duty LRCLK the level is true for 128 BCLKs and a level
    -- trigger would re-latch on every one of them. Edge detection is correct
    -- for both shapes, so the receiver no longer cares which the master sends.
    signal lrclk_d : std_logic := '0';
begin

    process(bclk_in, rst)
    begin
        if rst = '1' then
            shift_reg   <= (others => '0');
            ch_data_out <= (others => '0');
            lrclk_d     <= '0';
        elsif rising_edge(bclk_in) then

            lrclk_d <= lrclk_in;

            -- 1. Always shift the new bit in (moving everything left)
            shift_reg <= shift_reg(262 downto 0) & sdata_in;
            
            -- 2. When the Sync pulse arrives, the PREVIOUS 192 bits 
            --    are perfectly aligned in the register. Take a snapshot!
            -- 32 BCLK per slot, 24-bit left-justified data: each slot holds
            -- 24 data bits followed by 8 pad bits, so take the top 24 of every
            -- 32. Slot width and data width are no longer the same number.
            if lrclk_in = '1' and lrclk_d = '0' and C_RAW_CAPTURE then
                -- verbatim: frame bits 1..192, MSB = first bit after the sync
                ch_data_out <= shift_reg(255 + C_BIT_ADJ downto 64 + C_BIT_ADJ);
            elsif lrclk_in = '1' and lrclk_d = '0' then
                for k in 0 to 7 loop
                    ch_data_out(191 - 24*k downto 168 - 24*k)
                        <= shift_reg(255 + C_BIT_ADJ - 32*k
                                     downto 232 + C_BIT_ADJ - 32*k);
                end loop;
            end if;
            
        end if;
    end process;

end architecture rtl;