library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity top_tdm is
    port (
        clk_50m    : in  std_logic;
        rst_n      : in  std_logic;
        
        -- ADAU1978 / ESP32 External Interfaces (Unified Clock Architecture)
        bclk_out   : out std_logic;  -- 18.432 MHz (Wire this to both MCLK and BCLK)
        lrclk_out  : out std_logic;  -- 96 kHz
        sdata_in_A : in  std_logic;
        sdata_in_B : in  std_logic;
        
        -- Debug Display for ESP32 Verification
        dig        : out std_logic_vector(3 downto 0);
        seg        : out std_logic_vector(7 downto 0)
    );
end entity top_tdm;

architecture rtl of top_tdm is

    component pll_audio is
        port (
            inclk0 : in  std_logic;
            c0     : out std_logic;
            c1     : out std_logic;
            c2     : out std_logic;
            locked : out std_logic
        );
    end component;

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

    component seven_seg_monitor is
        port (
            clk      : in  std_logic;
            rst_n    : in  std_logic;
            data_in  : in  std_logic_vector(15 downto 0);
            dig_sel  : out std_logic_vector(3 downto 0);
            seg_out  : out std_logic_vector(7 downto 0)
        );
    end component;

    signal pll_locked  : std_logic;
    signal rst_int     : std_logic;
    
    signal clk_18m432  : std_logic;
    signal clk_50m_out : std_logic;
    
    signal bclk_int    : std_logic;
    signal lrclk_int   : std_logic;
    
    signal ch_data_A_int : std_logic_vector(191 downto 0);
    signal ch_data_B_int : std_logic_vector(191 downto 0);

begin

    -- Hold system in reset until PLL stabilizes
    rst_int <= (not rst_n) or (not pll_locked);
    
    -- Route internal clocks to external pins
    bclk_out  <= bclk_int;
    lrclk_out <= lrclk_int;

    u_pll : pll_audio port map (
        inclk0 => clk_50m,
        c0     => open,         -- 12.288 MHz is now disconnected and optimized away
        c1     => clk_18m432,   -- 18.432 MHz unified clock
        c2     => clk_50m_out,  -- 50 MHz for PHY (Step 5)
        locked => pll_locked
    );

    u_master : tdm8_master port map (
        rst       => rst_int,
        clk_in    => clk_18m432,
        bclk_out  => bclk_int,
        lrclk_out => lrclk_int
    );

    u_rx_A : tdm8_rx port map (
        rst         => rst_int,
        bclk_in     => bclk_int,
        lrclk_in    => lrclk_int,
        sdata_in    => sdata_in_A,
        ch_data_out => ch_data_A_int
    );

    u_rx_B : tdm8_rx port map (
        rst         => rst_int,
        bclk_in     => bclk_int,
        lrclk_in    => lrclk_int,
        sdata_in    => sdata_in_B,
        ch_data_out => ch_data_B_int
    );

    -- Route Channel 1 (Track A) to the Digital Tube
    u_display : seven_seg_monitor port map (
        clk      => clk_50m,
        rst_n    => rst_n,
        data_in  => ch_data_A_int(191 downto 176), 
        dig_sel  => dig,
        seg_out  => seg
    );

end architecture rtl;