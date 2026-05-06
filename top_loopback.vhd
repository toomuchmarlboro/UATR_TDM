library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity top_loopback is
    port (
        -- For this test, we assume you are routing the 18.432 MHz 
        -- clock from your PLL directly into this top level.
        clk_18m432 : in  std_logic; 
        rst_n      : in  std_logic; -- Active-low reset button on your board
        
        pass_led   : out std_logic; -- Solid green if 10 consecutive frames match
        fail_led   : out std_logic  -- Solid red if ANY mismatch happens
    );
end entity top_loopback;

architecture rtl of top_loopback is

    -- Component Declarations (from Step 1)
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

    -- Internal "Microscopic" Wires
    signal rst_int        : std_logic;
    signal bclk_int       : std_logic;
    signal lrclk_int      : std_logic;
    signal lrclk_prev     : std_logic := '0';
    signal sdata_internal : std_logic := '0';
    signal ch_data_out    : std_logic_vector(191 downto 0);

    -- Serializer (Fake ADAU1978) Signals
    signal tx_shift_reg   : std_logic_vector(191 downto 0) := (others => '0');
    signal frame_counter  : unsigned(23 downto 0) := (others => '0');

    -- Pass/Fail Checker Signals
    signal expected_count : unsigned(23 downto 0) := (others => '0');
    signal match_cnt      : integer range 0 to 15 := 0;
    signal startup_ignore : integer range 0 to 3 := 0;
    signal pass_reg       : std_logic := '0';
    signal fail_reg       : std_logic := '0';

begin

    -- Convert active-low board button to active-high internal reset
    rst_int <= not rst_n;
    
    -- Drive physical LEDs (assuming active-high LEDs, invert if active-low)
    pass_led <= pass_reg;
    fail_led <= fail_reg;

    -- 1. Instantiate the Clock Master
    u_tdm_master : tdm8_master
        port map (
            rst        => rst_int,
            clk_in     => clk_18m432,
            bclk_out   => bclk_int,
            lrclk_out  => lrclk_int
        );

    -- 2. Instantiate the Receiver
    u_tdm_rx : tdm8_rx
        port map (
            rst         => rst_int,
            bclk_in     => bclk_int,
            lrclk_in    => lrclk_int,
            sdata_in    => sdata_internal, -- Listening to our internal fake wire
            ch_data_out => ch_data_out
        );

    -- 3. The Pattern Serializer (The Fake ADC)
    -- Generates an incrementing counter for Ch1, and fixed values for Ch2-Ch8
    process(bclk_int, rst_int)
    begin
        if rst_int = '1' then
            tx_shift_reg <= (others => '0');
            frame_counter <= (others => '0');
        elsif falling_edge(bclk_int) then
            if lrclk_int = '1' then
                -- LRCLK pulsed! Load the new 192-bit frame into the shift register
                tx_shift_reg <= std_logic_vector(frame_counter) & x"B2B2B2C3C3C3D4D4D4E5E5E5F6F6F6070707181818";
                frame_counter <= frame_counter + 1;
            else
                -- Shift data out to the left (MSB first)
                tx_shift_reg <= tx_shift_reg(190 downto 0) & '0';
            end if;
        end if;
    end process;
    
    -- Continuously drive the internal wire with the Most Significant Bit of the shift register
    sdata_internal <= tx_shift_reg(191);

    -- 4. The Pass/Fail Checker
    -- Verifies the received data matches exactly what the Serializer sent
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
            
            -- Check the data exactly 1 clock cycle after the receiver latches it
            if lrclk_int = '0' and lrclk_prev = '1' then
                
                -- Skip the first two frames because the pipeline is still filling up
                if startup_ignore < 2 then
                    startup_ignore <= startup_ignore + 1;
                    -- Synchronize our expected checker to whatever channel 1 just received
                    expected_count <= unsigned(ch_data_out(191 downto 168)) + 1;
                else
                    -- Verify Channel 1 is the expected counter, and Ch2-8 are the exact fixed pattern
                    if unsigned(ch_data_out(191 downto 168)) = expected_count and 
                       ch_data_out(167 downto 0) = x"B2B2B2C3C3C3D4D4D4E5E5E5F6F6F6070707181818" then
                        
                        if match_cnt < 10 then
                            match_cnt <= match_cnt + 1;
                        else
                            pass_reg <= '1'; -- 10 perfect frames in a row! Turn on green LED.
                        end if;
                    else
                        fail_reg <= '1'; -- Mismatch detected! Turn on red LED.
                        pass_reg <= '0';
                    end if;
                    
                    expected_count <= expected_count + 1;
                end if;
            end if;
        end if;
    end process;

end architecture rtl;