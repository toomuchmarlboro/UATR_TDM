library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity seven_seg_monitor is
    port (
        clk      : in  std_logic;
        rst_n    : in  std_logic;
        data_in  : in  std_logic_vector(15 downto 0); -- Takes 4 Hex Characters
        
        dig_sel  : out std_logic_vector(3 downto 0);
        seg_out  : out std_logic_vector(7 downto 0)
    );
end entity seven_seg_monitor;

architecture rtl of seven_seg_monitor is
    signal refresh_clk : std_logic := '0';
    signal clk_div     : integer range 0 to 25000 := 0;
    signal scan_cnt    : integer range 0 to 3 := 0;
    signal current_nibble : std_logic_vector(3 downto 0);

    -- Standard 7-segment hex decoder (Active Low)
    function hex_to_7seg(hex : std_logic_vector(3 downto 0)) return std_logic_vector is
    begin
        case hex is
            when x"0" => return x"C0";
            when x"1" => return x"F9";
            when x"2" => return x"A4";
            when x"3" => return x"B0";
            when x"4" => return x"99";
            when x"5" => return x"92";
            when x"6" => return x"82";
            when x"7" => return x"F8";
            when x"8" => return x"80";
            when x"9" => return x"90";
            when x"A" => return x"88";
            when x"B" => return x"83";
            when x"C" => return x"C6";
            when x"D" => return x"A1";
            when x"E" => return x"86";
            when x"F" => return x"8E";
            when others => return x"FF";
        end case;
    end function;

begin
    -- Create slow refresh clock
    process(clk, rst_n) begin
        if rst_n = '0' then clk_div <= 0; refresh_clk <= '0';
        elsif rising_edge(clk) then
            if clk_div = 25000 then clk_div <= 0; refresh_clk <= not refresh_clk;
            else clk_div <= clk_div + 1; end if;
        end if;
    end process;

    -- Cycle through the 4 tubes
    process(refresh_clk, rst_n) begin
        if rst_n = '0' then scan_cnt <= 0;
        elsif rising_edge(refresh_clk) then
            if scan_cnt = 3 then scan_cnt <= 0; else scan_cnt <= scan_cnt + 1; end if;
        end if;
    end process;

    -- Map the 16-bit input to the 4 physical digits
    process(scan_cnt, data_in) begin
        dig_sel <= "1111";
        case scan_cnt is
            when 0 => 
                dig_sel <= "1110"; -- Leftmost digit
                current_nibble <= data_in(15 downto 12);
            when 1 => 
                dig_sel <= "1101"; 
                current_nibble <= data_in(11 downto 8);
            when 2 => 
                dig_sel <= "1011"; 
                current_nibble <= data_in(7 downto 4);
            when 3 => 
                dig_sel <= "0111"; -- Rightmost digit
                current_nibble <= data_in(3 downto 0);
        end case;
    end process;

    seg_out <= hex_to_7seg(current_nibble);

end architecture rtl;