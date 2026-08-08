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
    constant C_BIT_ADJ : integer := -1;
    signal shift_reg : std_logic_vector(263 downto 0) := (others => '0');
begin

    process(bclk_in, rst)
    begin
        if rst = '1' then
            shift_reg   <= (others => '0');
            ch_data_out <= (others => '0');
        elsif rising_edge(bclk_in) then
            
            -- 1. Always shift the new bit in (moving everything left)
            shift_reg <= shift_reg(262 downto 0) & sdata_in;
            
            -- 2. When the Sync pulse arrives, the PREVIOUS 192 bits 
            --    are perfectly aligned in the register. Take a snapshot!
            -- 32 BCLK per slot, 24-bit left-justified data: each slot holds
            -- 24 data bits followed by 8 pad bits, so take the top 24 of every
            -- 32. Slot width and data width are no longer the same number.
            if lrclk_in = '1' then
                for k in 0 to 7 loop
                    ch_data_out(191 - 24*k downto 168 - 24*k)
                        <= shift_reg(255 + C_BIT_ADJ - 32*k
                                     downto 232 + C_BIT_ADJ - 32*k);
                end loop;
            end if;
            
        end if;
    end process;

end architecture rtl;