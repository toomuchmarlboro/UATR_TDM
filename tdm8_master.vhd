library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity tdm8_master is
    port (
        rst        : in  std_logic;
        clk_in     : in  std_logic; -- 18.432 MHz from PLL
        bclk_out   : out std_logic;
        lrclk_out  : out std_logic  -- 1-cycle HIGH pulse every 192 clocks
    );
end entity tdm8_master;

architecture rtl of tdm8_master is
    signal bit_cnt   : integer range 0 to 191 := 0;
    signal lrclk_reg : std_logic := '0';
begin

    -- Pass the 18.432 MHz clock directly to the output
    bclk_out <= clk_in;

    -- Generate LRCLK pulse on the FALLING edge of the clock
    -- This guarantees LRCLK is stable when the ADAU1978 reads it on the RISING edge
    process(clk_in, rst)
    begin
        if rst = '1' then
            bit_cnt <= 0;
            lrclk_reg <= '0';
        elsif falling_edge(clk_in) then
            if bit_cnt = 191 then
                bit_cnt <= 0;
                lrclk_reg <= '1'; -- Pulse HIGH for the first BCLK cycle
            else
                bit_cnt <= bit_cnt + 1;
                lrclk_reg <= '0';
            end if;
        end if;
    end process;

    lrclk_out <= lrclk_reg;

end architecture rtl;