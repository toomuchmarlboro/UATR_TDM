library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity top_loopback is
    port (
        clk_18m432 : in  std_logic; 
        rst_n      : in  std_logic; 
        pass_led   : out std_logic; 
        fail_led   : out std_logic;
        
        -- Digital Tube Pins
        dig        : out std_logic_vector(3 downto 0);
        seg        : out std_logic_vector(7 downto 0)
    );
end entity top_loopback;

architecture rtl of top_loopback is

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

    component seven_seg_driver is
        port (
            clk      : in  std_logic;
            rst_n    : in  std_logic;
            pass_in  : in  std_logic;
            fail_in  : in  std_logic;
            dig_sel  : out std_logic_vector(3 downto 0);
            seg_out  : out std_logic_vector(7 downto 0)
        );
    end component;

    -- ==========================================
    -- DECLARATIVE REGION: All signals MUST go here
    -- ==========================================
    signal rst_int        : std_logic;
    signal bclk_int       : std_logic;
    signal lrclk_int      : std_logic;
    signal lrclk_prev     : std_logic := '0';
    signal sdata_internal : std_logic := '0';
    signal ch_data_out    : std_logic_vector(191 downto 0);
    signal tx_shift_reg   : std_logic_vector(191 downto 0) := (others => '0');
    signal frame_counter  : unsigned(23 downto 0) := (others => '0');
    signal expected_count : unsigned(23 downto 0) := (others => '0');
    signal match_cnt      : integer range 0 to 15 := 0;
    signal startup_ignore : integer range 0 to 3 := 0;
    signal pass_reg       : std_logic := '0';
    signal fail_reg       : std_logic := '0';
    signal tx_bit_cnt     : integer range 0 to 191 := 0;
	 
	 attribute keep : boolean;
	 attribute keep of sdata_internal : signal is true;
	 attribute keep of bclk_int       : signal is true;
	 attribute keep of lrclk_int      : signal is true;	

begin
    -- ==========================================
    -- EXECUTION REGION: Processes and Logic go here
    -- ==========================================

    rst_int <= not rst_n;
    pass_led <= not pass_reg;
    fail_led <= not fail_reg;

    u_tdm_master : tdm8_master port map (rst_int, clk_18m432, bclk_int, lrclk_int);
    u_tdm_rx : tdm8_rx port map (rst_int, bclk_int, lrclk_int, sdata_internal, ch_data_out);
    
    u_display : seven_seg_driver port map (
        clk      => clk_18m432,
        rst_n    => rst_n,
        pass_in  => pass_reg,
        fail_in  => fail_reg,
        dig_sel  => dig,
        seg_out  => seg
    );

    -- Pattern Serializer (Now immune to the LRCLK edge race condition)
    process(bclk_int, rst_int)
    begin
        if rst_int = '1' then
            tx_shift_reg <= (others => '0');
            frame_counter <= (others => '0');
            tx_bit_cnt <= 0;
        elsif falling_edge(bclk_int) then
            if tx_bit_cnt = 191 then
                tx_shift_reg <= std_logic_vector(frame_counter) & x"B2B2B2C3C3C3D4D4D4E5E5E5F6F6F6070707181818";
                frame_counter <= frame_counter + 1;
                tx_bit_cnt <= 0;
            else
                tx_shift_reg <= tx_shift_reg(190 downto 0) & '0';
                tx_bit_cnt <= tx_bit_cnt + 1;
            end if;
        end if;
    end process;
    
    sdata_internal <= tx_shift_reg(191);

    -- Pass/Fail Checker
    process(bclk_int, rst_int)
    begin
        if rst_int = '1' then
            expected_count <= (others => '0');
            match_cnt <= 0;
            startup_ignore <= 0;
            pass_reg <= '0';
            fail_reg <= '0';
        elsif rising_edge(bclk_int) then
            lrclk_prev <= lrclk_int;
            
            if lrclk_int = '0' and lrclk_prev = '1' then
                if startup_ignore < 2 then
                    startup_ignore <= startup_ignore + 1;
                    expected_count <= unsigned(ch_data_out(191 downto 168)) + 1;
                else
                    if unsigned(ch_data_out(191 downto 168)) = expected_count and 
                       ch_data_out(167 downto 0) = x"B2B2B2C3C3C3D4D4D4E5E5E5F6F6F6070707181818" then
                        
                        if match_cnt < 10 then match_cnt <= match_cnt + 1;
                        else pass_reg <= '1'; end if;
                    else
                        fail_reg <= '1'; pass_reg <= '0';
                    end if;
                    expected_count <= expected_count + 1;
                end if;
            end if;
        end if;
    end process;

end architecture rtl;