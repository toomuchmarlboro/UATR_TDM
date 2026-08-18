library ieee;
use ieee.std_logic_1164.all;

entity crc32 is
    port (
        clk      : in  std_logic;
        rst      : in  std_logic;
        en       : in  std_logic;
        data_in  : in  std_logic_vector(7 downto 0);
        crc_out  : out std_logic_vector(31 downto 0)
    );
end entity crc32;

architecture rtl of crc32 is
    signal crc_reg : std_logic_vector(31 downto 0) := (others => '1');
begin

    crc_out <= not crc_reg; -- Ethernet requires the final CRC to be bit-inverted

    process(clk, rst)
        variable c : std_logic_vector(31 downto 0);
        variable d : std_logic_vector(7 downto 0);
    begin
        if rst = '1' then
            crc_reg <= (others => '1'); -- Ethernet CRC initializes to all 1s
        elsif rising_edge(clk) then
            if en = '1' then
                c := crc_reg;
                -- Ethernet transmits LSB first, so we reverse the byte for the calculation
                d := data_in(0) & data_in(1) & data_in(2) & data_in(3) & 
                     data_in(4) & data_in(5) & data_in(6) & data_in(7);

                -- Standard 8-bit parallel CRC32 XOR matrix for 0x04C11DB7
                crc_reg(0) <= c(24) xor c(30) xor d(0) xor d(6);
                crc_reg(1) <= c(24) xor c(25) xor c(30) xor c(31) xor d(0) xor d(1) xor d(6) xor d(7);
                crc_reg(2) <= c(24) xor c(25) xor c(26) xor c(30) xor c(31) xor d(0) xor d(1) xor d(2) xor d(6) xor d(7);
                crc_reg(3) <= c(25) xor c(26) xor c(27) xor c(31) xor d(1) xor d(2) xor d(3) xor d(7);
                crc_reg(4) <= c(24) xor c(26) xor c(27) xor c(28) xor c(30) xor d(0) xor d(2) xor d(3) xor d(4) xor d(6);
                crc_reg(5) <= c(24) xor c(25) xor c(27) xor c(28) xor c(29) xor c(30) xor c(31) xor d(0) xor d(1) xor d(3) xor d(4) xor d(5) xor d(6) xor d(7);
                crc_reg(6) <= c(25) xor c(26) xor c(28) xor c(29) xor c(30) xor c(31) xor d(1) xor d(2) xor d(4) xor d(5) xor d(6) xor d(7);
                crc_reg(7) <= c(24) xor c(26) xor c(27) xor c(29) xor c(31) xor d(0) xor d(2) xor d(3) xor d(5) xor d(7);
                crc_reg(8) <= c(0) xor c(24) xor c(25) xor c(27) xor c(28) xor d(0) xor d(1) xor d(3) xor d(4);
                crc_reg(9) <= c(1) xor c(25) xor c(26) xor c(28) xor c(29) xor d(1) xor d(2) xor d(4) xor d(5);
                crc_reg(10) <= c(2) xor c(24) xor c(26) xor c(27) xor c(29) xor d(0) xor d(2) xor d(3) xor d(5);
                crc_reg(11) <= c(3) xor c(24) xor c(25) xor c(27) xor c(28) xor d(0) xor d(1) xor d(3) xor d(4);
                crc_reg(12) <= c(4) xor c(24) xor c(25) xor c(26) xor c(28) xor c(29) xor c(30) xor d(0) xor d(1) xor d(2) xor d(4) xor d(5) xor d(6);
                crc_reg(13) <= c(5) xor c(25) xor c(26) xor c(27) xor c(29) xor c(30) xor c(31) xor d(1) xor d(2) xor d(3) xor d(5) xor d(6) xor d(7);
                crc_reg(14) <= c(6) xor c(26) xor c(27) xor c(28) xor c(30) xor c(31) xor d(2) xor d(3) xor d(4) xor d(6) xor d(7);
                crc_reg(15) <= c(7) xor c(27) xor c(28) xor c(29) xor c(31) xor d(3) xor d(4) xor d(5) xor d(7);
                crc_reg(16) <= c(8) xor c(24) xor c(28) xor c(29) xor d(0) xor d(4) xor d(5);
                crc_reg(17) <= c(9) xor c(25) xor c(29) xor c(30) xor d(1) xor d(5) xor d(6);
                crc_reg(18) <= c(10) xor c(26) xor c(30) xor c(31) xor d(2) xor d(6) xor d(7);
                crc_reg(19) <= c(11) xor c(27) xor c(31) xor d(3) xor d(7);
                crc_reg(20) <= c(12) xor c(28) xor d(4);
                crc_reg(21) <= c(13) xor c(29) xor d(5);
                crc_reg(22) <= c(14) xor c(24) xor d(0);
                crc_reg(23) <= c(15) xor c(24) xor c(25) xor c(30) xor d(0) xor d(1) xor d(6);
                crc_reg(24) <= c(16) xor c(25) xor c(26) xor c(31) xor d(1) xor d(2) xor d(7);
                crc_reg(25) <= c(17) xor c(26) xor c(27) xor d(2) xor d(3);
                crc_reg(26) <= c(18) xor c(24) xor c(27) xor c(28) xor c(30) xor d(0) xor d(3) xor d(4) xor d(6);
                crc_reg(27) <= c(19) xor c(25) xor c(28) xor c(29) xor c(31) xor d(1) xor d(4) xor d(5) xor d(7);
                crc_reg(28) <= c(20) xor c(26) xor c(29) xor c(30) xor d(2) xor d(5) xor d(6);
                crc_reg(29) <= c(21) xor c(27) xor c(30) xor c(31) xor d(3) xor d(6) xor d(7);
                crc_reg(30) <= c(22) xor c(28) xor c(31) xor d(4) xor d(7);
                crc_reg(31) <= c(23) xor c(29) xor d(5);
            end if;
        end if;
    end process;

end architecture rtl;