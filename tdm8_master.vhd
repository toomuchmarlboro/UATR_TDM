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
    signal bit_cnt : integer range 0 to 191 := 0;
begin

    bclk_out <= clk_in;

    process(clk_in, rst)
    begin
        if rst = '1' then
            bit_cnt <= 0;
            lrclk_out <= '0';
        elsif falling_edge(clk_in) then
            
            if bit_cnt = 191 then
                bit_cnt <= 0;
                lrclk_out <= '1';
            else
                bit_cnt <= bit_cnt + 1;
                lrclk_out <= '0';
            end if;
            
        end if;
    end process;

end architecture rtl;