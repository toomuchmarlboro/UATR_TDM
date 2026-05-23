library ieee;
use ieee.std_logic_1164.all;

entity tdm16_merge is
    port (
        clk         : in  std_logic;                       -- 18.432 MHz
        rst         : in  std_logic;
        lrclk_pulse : in  std_logic;                       -- 96 kHz, 1-cycle true sync
        ch_data_A   : in  std_logic_vector(191 downto 0);  -- ch 1–8
        ch_data_B   : in  std_logic_vector(191 downto 0);  -- ch 9–16
        tdm16_out   : out std_logic_vector(383 downto 0);  -- ch 1–16 ordered
        tdm16_valid : out std_logic                        -- high for 1 cycle on latch
    );
end entity tdm16_merge;

architecture rtl of tdm16_merge is
begin
    process(clk, rst)
    begin
        if rst = '1' then
            tdm16_out   <= (others => '0');
            tdm16_valid <= '0';
        elsif rising_edge(clk) then
            
            -- Default to 0 so valid only pulses for exactly 1 clock cycle
            tdm16_valid <= '0';

            -- Sample on the exact clock cycle the master fires the true sync
            if lrclk_pulse = '1' then
                
                -- Standard VHDL concatenation (&) perfectly aligns with your memory map.
                -- ch_data_A (191 downto 0) becomes tdm16_out(383 downto 192)
                -- ch_data_B (191 downto 0) becomes tdm16_out(191 downto 0)
                tdm16_out   <= ch_data_A & ch_data_B;
                
                -- Fire the trigger for the downstream packet_formatter
                tdm16_valid <= '1';
                
            end if;
            
        end if;
    end process;
end architecture rtl;