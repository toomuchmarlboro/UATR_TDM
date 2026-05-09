library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity seven_seg_driver is
    port (
        clk      : in  std_logic; -- 50 MHz
        rst_n    : in  std_logic;
        pass_in  : in  std_logic;
        fail_in  : in  std_logic;
        
        dig_sel  : out std_logic_vector(3 downto 0); -- DIG1 to DIG4
        seg_out  : out std_logic_vector(7 downto 0)  -- SEG0 to SEG7
    );
end entity seven_seg_driver;

architecture rtl of seven_seg_driver is

    signal refresh_clk : std_logic := '0';
    signal clk_div     : integer range 0 to 25000 := 0; -- 50MHz to ~1kHz
    signal scan_cnt    : integer range 0 to 3 := 0;

    -- Standard 7-Segment Active-Low Hex Codes (DP, G, F, E, D, C, B, A)
    constant CHAR_P : std_logic_vector(7 downto 0) := x"8C";
    constant CHAR_A : std_logic_vector(7 downto 0) := x"88";
    constant CHAR_S : std_logic_vector(7 downto 0) := x"92";
    constant CHAR_F : std_logic_vector(7 downto 0) := x"8E";
    constant CHAR_I : std_logic_vector(7 downto 0) := x"F9";
    constant CHAR_L : std_logic_vector(7 downto 0) := x"C7";
    constant CHAR_DASH : std_logic_vector(7 downto 0) := x"BF";

begin

    -- 1. Create a slow 1kHz refresh clock for the multiplexer
    process(clk, rst_n)
    begin
        if rst_n = '0' then
            clk_div <= 0;
            refresh_clk <= '0';
        elsif rising_edge(clk) then
            if clk_div = 25000 then
                clk_div <= 0;
                refresh_clk <= not refresh_clk;
            else
                clk_div <= clk_div + 1;
            end if;
        end if;
    end process;

    -- 2. Scan through the 4 digits 
    process(refresh_clk, rst_n)
    begin
        if rst_n = '0' then
            scan_cnt <= 0;
        elsif rising_edge(refresh_clk) then
            if scan_cnt = 3 then
                scan_cnt <= 0;
            else
                scan_cnt <= scan_cnt + 1;
            end if;
        end if;
    end process;

    -- 3. Output the correct character to the correct digit
    process(scan_cnt, pass_in, fail_in)
    begin
        -- Default to everything OFF (Active Low)
        dig_sel <= "1111";
        seg_out <= x"FF";
        
        case scan_cnt is
            when 0 => 
                dig_sel <= "0111"; -- Activate DIG1 (Leftmost)
                if pass_in = '1' then seg_out <= CHAR_P;
                elsif fail_in = '1' then seg_out <= CHAR_F;
                else seg_out <= CHAR_DASH; end if;
                
            when 1 => 
                dig_sel <= "1011"; -- Activate DIG2
                if pass_in = '1' then seg_out <= CHAR_A;
                elsif fail_in = '1' then seg_out <= CHAR_A;
                else seg_out <= CHAR_DASH; end if;
                
            when 2 => 
                dig_sel <= "1101"; -- Activate DIG3
                if pass_in = '1' then seg_out <= CHAR_S;
                elsif fail_in = '1' then seg_out <= CHAR_I;
                else seg_out <= CHAR_DASH; end if;
                
            when 3 => 
                dig_sel <= "1110"; -- Activate DIG4 (Rightmost)
                if pass_in = '1' then seg_out <= CHAR_S;
                elsif fail_in = '1' then seg_out <= CHAR_L;
                else seg_out <= CHAR_DASH; end if;
        end case;
    end process;

end architecture rtl;