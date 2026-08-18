library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity tb_tdm8_rx is
end entity tb_tdm8_rx;

architecture sim of tb_tdm8_rx is

    component tdm8_master is
        port (
            rst        : in  std_logic;
            clk_in     : in  std_logic;
            bclk_out   : out std_logic;
            lrclk_out  : out std_logic
        );
    end component;

    component tdm8_rx is
        port (
            rst         : in  std_logic;
            bclk_in     : in  std_logic;
            lrclk_in    : in  std_logic;
            sdata_in    : in  std_logic;
            ch_data_out : out std_logic_vector(191 downto 0)
        );
    end component;

    signal rst         : std_logic := '1';
    signal clk_18m432  : std_logic := '0';
    signal bclk        : std_logic;
    signal lrclk       : std_logic;
    signal sdata_in    : std_logic := '0';
    signal ch_data_out : std_logic_vector(191 downto 0);

    -- 18.432 MHz period is ~54.25 ns
    constant CLK_PERIOD : time := 54.25 ns; 

    -- 8 channels, 24-bit slots (NO zero padding)
    type frame_data_type is array (0 to 7) of std_logic_vector(23 downto 0);
    constant TEST_FRAME : frame_data_type := (
        x"A1A1A1", -- Ch 1
        x"B2B2B2", -- Ch 2
        x"C3C3C3", -- Ch 3
        x"D4D4D4", -- Ch 4
        x"E5E5E5", -- Ch 5
        x"F6F6F6", -- Ch 6
        x"070707", -- Ch 7
        x"181818"  -- Ch 8
    );

begin

    uut_master: tdm8_master
        port map (
            rst        => rst,
            clk_in     => clk_18m432,
            bclk_out   => bclk,
            lrclk_out  => lrclk
        );

    uut_rx: tdm8_rx
        port map (
            rst         => rst,
            bclk_in     => bclk,
            lrclk_in    => lrclk,
            sdata_in    => sdata_in,
            ch_data_out => ch_data_out
        );

    -- Generate 18.432 MHz system clock
    clk_gen: process
    begin
        clk_18m432 <= '0';
        wait for CLK_PERIOD / 2;
        clk_18m432 <= '1';
        wait for CLK_PERIOD / 2;
    end process clk_gen;

    -- Mimic the ADAU1978 pair sending data on the shared SDATAOUT wire
    stimulus: process
    begin
        rst <= '1';
        sdata_in <= '0';
        wait for 200 ns;
        
        wait until falling_edge(clk_18m432);
        rst <= '0';

        -- Send 3 complete frames
        for frame_idx in 1 to 3 loop
            
            -- Wait for the FPGA Master to pulse LRCLK high
            wait until lrclk = '1';
            
            -- ADAU1978 shifts data out on the FALLING edge of BCLK
            for ch_idx in 0 to 7 loop
                for bit_idx in 23 downto 0 loop
                    sdata_in <= TEST_FRAME(ch_idx)(bit_idx);
                    wait until falling_edge(bclk);
                end loop;
            end loop;
            
        end loop;

        wait for 300 ns;
        std.env.stop;
    end process stimulus;

end architecture sim;