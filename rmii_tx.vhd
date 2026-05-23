library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity rmii_tx is
    port (
        clk_50m      : in  std_logic;
        rst          : in  std_logic;
        
        -- Interface from udp_tx_core
        tx_start     : in  std_logic;
        tx_data      : in  std_logic_vector(7 downto 0);
        tx_ready     : out std_logic;
        
        -- Physical Pins to LAN8720A
        rmii_tx_en   : out std_logic;
        rmii_txd     : out std_logic_vector(1 downto 0)
    );
end entity rmii_tx;

architecture rtl of rmii_tx is
    
    component crc32 is
        port (
            clk      : in  std_logic;
            rst      : in  std_logic;
            en       : in  std_logic;
            data_in  : in  std_logic_vector(7 downto 0);
            crc_out  : out std_logic_vector(31 downto 0)
        );
    end component;

    type state_type is (IDLE, PREAMBLE, SFD, DATA_PAYLOAD, SEND_CRC, IFG);
    signal state : state_type := IDLE;
    
    signal byte_cnt   : integer range 0 to 1500 := 0;
    signal di_bit_cnt : integer range 0 to 3 := 0; -- Tracks the 2-bit slices
    
    signal current_byte : std_logic_vector(7 downto 0);
    
    signal crc_rst   : std_logic := '1';
    signal crc_en    : std_logic := '0';
    signal crc_data  : std_logic_vector(7 downto 0) := (others => '0');
    signal crc_value : std_logic_vector(31 downto 0);

begin

    u_crc : crc32 port map (
        clk     => clk_50m,
        rst     => crc_rst,
        en      => crc_en,
        data_in => crc_data,
        crc_out => crc_value
    );

    process(clk_50m, rst)
    begin
        if rst = '1' then
            state      <= IDLE;
            rmii_tx_en <= '0';
            rmii_txd   <= "00";
            tx_ready   <= '0';
            crc_rst    <= '1';
            crc_en     <= '0';
            di_bit_cnt <= 0;
            byte_cnt   <= 0;
            
        elsif rising_edge(clk_50m) then
            
            -- Defaults
            tx_ready <= '0';
            crc_en   <= '0';
            crc_rst  <= '0';
            
            case state is
                
                when IDLE =>
                    rmii_tx_en <= '0';
                    rmii_txd   <= "00";
                    crc_rst    <= '1'; -- Keep CRC cleared while idle
                    if tx_start = '1' then
                        state <= PREAMBLE;
                        byte_cnt <= 0;
                        di_bit_cnt <= 0;
                        current_byte <= x"55"; -- 0x55 is the standard Ethernet Preamble
                    end if;

                when PREAMBLE =>
                    rmii_tx_en <= '1';
                    
                    -- Slice the byte into 2-bit chunks (LSB first for Ethernet!)
                    if di_bit_cnt = 0 then rmii_txd <= current_byte(1 downto 0);
                    elsif di_bit_cnt = 1 then rmii_txd <= current_byte(3 downto 2);
                    elsif di_bit_cnt = 2 then rmii_txd <= current_byte(5 downto 4);
                    elsif di_bit_cnt = 3 then rmii_txd <= current_byte(7 downto 6);
                    end if;
                    
                    if di_bit_cnt = 3 then
                        di_bit_cnt <= 0;
                        if byte_cnt = 6 then 
                            -- After 7 bytes of 0x55, send the Start Frame Delimiter (SFD)
                            state <= SFD;
                            current_byte <= x"D5";
                        else
                            byte_cnt <= byte_cnt + 1;
                        end if;
                    else
                        di_bit_cnt <= di_bit_cnt + 1;
                    end if;

                when SFD =>
                    rmii_tx_en <= '1';
                    
                    if di_bit_cnt = 0 then rmii_txd <= current_byte(1 downto 0);
                    elsif di_bit_cnt = 1 then rmii_txd <= current_byte(3 downto 2);
                    elsif di_bit_cnt = 2 then rmii_txd <= current_byte(5 downto 4);
                    elsif di_bit_cnt = 3 then rmii_txd <= current_byte(7 downto 6);
                    end if;
                    
                    -- Trigger udp_tx_core to give us the first payload byte
                    if di_bit_cnt = 2 then
                        tx_ready <= '1';
                    end if;

                    if di_bit_cnt = 3 then
                        state <= DATA_PAYLOAD;
                        di_bit_cnt <= 0;
                        current_byte <= tx_data;
                        
                        -- Fire the CRC calculator for the incoming byte
                        crc_data <= tx_data;
                        crc_en   <= '1';
                    else
                        di_bit_cnt <= di_bit_cnt + 1;
                    end if;

                when DATA_PAYLOAD =>
                    rmii_tx_en <= '1';
                    
                    if di_bit_cnt = 0 then rmii_txd <= current_byte(1 downto 0);
                    elsif di_bit_cnt = 1 then rmii_txd <= current_byte(3 downto 2);
                    elsif di_bit_cnt = 2 then rmii_txd <= current_byte(5 downto 4);
                    elsif di_bit_cnt = 3 then rmii_txd <= current_byte(7 downto 6);
                    end if;
                    
                    -- Ask for the next byte just before we finish the current one
                    if di_bit_cnt = 2 then
                        tx_ready <= '1';
                    end if;
                    
                    if di_bit_cnt = 3 then
                        di_bit_cnt <= 0;
                        
                        if tx_start = '1' then
                            -- Still receiving data from udp_tx_core
                            current_byte <= tx_data;
                            crc_data     <= tx_data;
                            crc_en       <= '1';
                        else
                            -- udp_tx_core is done. Time to append the calculated CRC!
                            state <= SEND_CRC;
                            byte_cnt <= 0;
                            
                            -- CRC is sent MSB byte first, but still LSB bits out to the wire
                            -- Also, Ethernet requires bit-reversal of the CRC bytes.
                            current_byte <= crc_value(24) & crc_value(25) & crc_value(26) & crc_value(27) & 
                                            crc_value(28) & crc_value(29) & crc_value(30) & crc_value(31);
                        end if;
                    else
                        di_bit_cnt <= di_bit_cnt + 1;
                    end if;

                when SEND_CRC =>
                    rmii_tx_en <= '1';
                    
                    if di_bit_cnt = 0 then rmii_txd <= current_byte(1 downto 0);
                    elsif di_bit_cnt = 1 then rmii_txd <= current_byte(3 downto 2);
                    elsif di_bit_cnt = 2 then rmii_txd <= current_byte(5 downto 4);
                    elsif di_bit_cnt = 3 then rmii_txd <= current_byte(7 downto 6);
                    end if;
                    
                    if di_bit_cnt = 3 then
                        di_bit_cnt <= 0;
                        if byte_cnt = 3 then
                            -- CRC is 4 bytes. We are done! Enter Inter-Frame Gap.
                            state <= IFG;
                            byte_cnt <= 0;
                        else
                            byte_cnt <= byte_cnt + 1;
                            -- Load the next CRC byte (bit-reversed)
                            if byte_cnt = 0 then 
                                current_byte <= crc_value(16) & crc_value(17) & crc_value(18) & crc_value(19) & 
                                                crc_value(20) & crc_value(21) & crc_value(22) & crc_value(23);
                            elsif byte_cnt = 1 then
                                current_byte <= crc_value(8) & crc_value(9) & crc_value(10) & crc_value(11) & 
                                                crc_value(12) & crc_value(13) & crc_value(14) & crc_value(15);
                            elsif byte_cnt = 2 then
                                current_byte <= crc_value(0) & crc_value(1) & crc_value(2) & crc_value(3) & 
                                                crc_value(4) & crc_value(5) & crc_value(6) & crc_value(7);
                            end if;
                        end if;
                    else
                        di_bit_cnt <= di_bit_cnt + 1;
                    end if;
                    
                when IFG =>
                    -- Stop transmitting. Ethernet requires at least 96 bit times (48 clocks in RMII) between frames.
                    rmii_tx_en <= '0';
                    rmii_txd   <= "00";
                    
                    if byte_cnt = 48 then
                        state <= IDLE;
                    else
                        byte_cnt <= byte_cnt + 1;
                    end if;
                    
            end case;
            
        end if;
    end process;

end architecture rtl;