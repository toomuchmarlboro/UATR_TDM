library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity tb_tdm16 is
end entity tb_tdm16;

architecture sim of tb_tdm16 is

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

    component tdm16_merge is
        port (
            clk         : in  std_logic;
            rst         : in  std_logic;
            lrclk_pulse : in  std_logic;
            ch_data_A   : in  std_logic_vector(191 downto 0);
            ch_data_B   : in  std_logic_vector(191 downto 0);
            tdm16_out   : out std_logic_vector(383 downto 0);
            tdm16_valid : out std_logic
        );
    end component;

    signal clk_18m432  : std_logic := '0';
    signal rst         : std_logic := '1';
    signal bclk        : std_logic;
    signal lrclk       : std_logic;
    
    signal sdata_A     : std_logic := '0';
    signal sdata_B     : std_logic := '0';
    
    signal ch_data_A   : std_logic_vector(191 downto 0);
    signal ch_data_B   : std_logic_vector(191 downto 0);
    
    signal tdm16_out   : std_logic_vector(383 downto 0);
    signal tdm16_valid : std_logic;

    -- VHDL-93 Strict: No underscores in hex bit-strings
    constant PAYLOAD_A : std_logic_vector(191 downto 0) := x"01AAAA02BBBB03CCCC04DDDD05EEEE06FFFF071111082222";
    constant PAYLOAD_B : std_logic_vector(191 downto 0) := x"0933330A44440B55550C66660D77770E88880F9999100000";

begin

    -- VHDL-93 Strict: Whole numbers for time only (27.126 ns -> 27126 ps)
    clk_18m432 <= not clk_18m432 after 27126 ps;
    rst <= '1', '0' after 100 ns;

    u_master : tdm8_master port map (
        rst        => rst,
        clk_in     => clk_18m432,
        bclk_out   => bclk,
        lrclk_out  => lrclk
    );

    u_rx_A : tdm8_rx port map (
        rst         => rst,
        bclk_in     => bclk,
        lrclk_in    => lrclk,
        sdata_in    => sdata_A,
        ch_data_out => ch_data_A
    );

    u_rx_B : tdm8_rx port map (
        rst         => rst,
        bclk_in     => bclk,
        lrclk_in    => lrclk,
        sdata_in    => sdata_B,
        ch_data_out => ch_data_B
    );

    u_merge : tdm16_merge port map (
        clk         => clk_18m432,
        rst         => rst,
        lrclk_pulse => lrclk,
        ch_data_A   => ch_data_A,
        ch_data_B   => ch_data_B,
        tdm16_out   => tdm16_out,
        tdm16_valid => tdm16_valid
    );

    -- Delta-Cycle-Proof ADAU1978 Emulator
    process(bclk, rst)
        variable bit_cnt : integer range 0 to 191 := 0;
    begin
        if rst = '1' then
            sdata_A <= '0';
            sdata_B <= '0';
            bit_cnt := 0;
        elsif falling_edge(bclk) then
            
            -- Master fires lrclk when its counter wraps from 191 to 0.
            -- We push the MSB at the exact same moment.
            if bit_cnt = 191 then
                bit_cnt := 0;
                sdata_A <= PAYLOAD_A(191);
                sdata_B <= PAYLOAD_B(191);
            else
                bit_cnt := bit_cnt + 1;
                sdata_A <= PAYLOAD_A(191 - bit_cnt);
                sdata_B <= PAYLOAD_B(191 - bit_cnt);
            end if;
            
        end if;
    end process;

end architecture sim;