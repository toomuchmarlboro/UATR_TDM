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
    signal bit_cnt : integer range 0 to 255 := 0;
begin

    bclk_out <= clk_in;

    process(clk_in, rst)
    begin
        if rst = '1' then
            bit_cnt <= 0;
            lrclk_out <= '0';
        -- LRCLK transitions on the FALLING edge of BCLK, so it is stable well
        -- before the rising edge where an I2S/TDM slave latches it. This matters
        -- more now that U1 is bypassed with wire (~0 ns) while BCLK still goes
        -- through U2 (~3 ns): generating on the rising edge would leave only the
        -- buffer's propagation delay as setup time. Falling edge gives ~24 ns.
        elsif falling_edge(clk_in) then
            
            if bit_cnt = 255 then
                bit_cnt <= 0;
                lrclk_out <= '1';
            else
                bit_cnt <= bit_cnt + 1;
                lrclk_out <= '0';
            end if;
            
        end if;
    end process;

end architecture rtl;