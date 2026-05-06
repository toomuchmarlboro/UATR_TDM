library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

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
    signal shift_reg  : std_logic_vector(191 downto 0) := (others => '0');
    signal lrclk_prev : std_logic := '0';
begin

    -- Sample data on the RISING edge of BCLK
    process(bclk_in, rst)
    begin
        if rst = '1' then
            shift_reg <= (others => '0');
            ch_data_out <= (others => '0');
            lrclk_prev <= '0';
        elsif rising_edge(bclk_in) then
            lrclk_prev <= lrclk_in;

            -- Shift data in (MSB first, no zero padding)
            shift_reg <= shift_reg(190 downto 0) & sdata_in;

            -- Detect the rising edge of the LRCLK pulse
            -- When it hits, the PREVIOUS 192 bits form a complete frame
            if lrclk_in = '1' and lrclk_prev = '0' then
                ch_data_out <= shift_reg;
            end if;
        end if;
    end process;

end architecture rtl;