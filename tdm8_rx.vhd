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
    signal shift_reg : std_logic_vector(191 downto 0) := (others => '0');
begin

    process(bclk_in, rst)
    begin
        if rst = '1' then
            shift_reg   <= (others => '0');
            ch_data_out <= (others => '0');
        elsif rising_edge(bclk_in) then
            
            -- 1. Always shift the new bit in (moving everything left)
            shift_reg <= shift_reg(190 downto 0) & sdata_in;
            
            -- 2. When the Sync pulse arrives, the PREVIOUS 192 bits 
            --    are perfectly aligned in the register. Take a snapshot!
            if lrclk_in = '1' then
                ch_data_out <= shift_reg;
            end if;
            
        end if;
    end process;

end architecture rtl;