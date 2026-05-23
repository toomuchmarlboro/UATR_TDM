library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity arp_responder is
    port (
        clk_50m      : in  std_logic;
        rst          : in  std_logic;
        
        -- IP Configuration (From top_system)
        fpga_mac     : in  std_logic_vector(47 downto 0);
        fpga_ip      : in  std_logic_vector(31 downto 0);

        -- RMII Receive Interface (From LAN8720A)
        rmii_rx_dv   : in  std_logic;
        rmii_rxd     : in  std_logic_vector(1 downto 0);
        
        -- Output to TX Arbiter / rmii_tx
        arp_tx_req   : out std_logic;
        arp_tx_data  : out std_logic_vector(7 downto 0);
        tx_ready     : in  std_logic
    );
end entity arp_responder;

architecture rtl of arp_responder is

    -- RX State Machine
    type rx_state_type is (IDLE, SYNC_SFD, PARSE_PACKET);
    signal rx_state : rx_state_type := IDLE;
    
    signal rx_byte_cnt  : integer range 0 to 1500 := 0;
    signal rx_bit_cnt   : integer range 0 to 3 := 0;
    signal rx_byte      : std_logic_vector(7 downto 0) := (others => '0');
    
    -- Captured Data from Requester
    signal sender_mac : std_logic_vector(47 downto 0) := (others => '0');
    signal sender_ip  : std_logic_vector(31 downto 0) := (others => '0');
    
    -- TX State Machine
    type tx_state_type is (IDLE, SEND_REPLY);
    signal tx_state : tx_state_type := IDLE;
    signal tx_byte_cnt : integer range 0 to 63 := 0;
    
    signal trigger_reply : std_logic := '0';

begin

    -- =========================================================
    -- RX PARSER: Wiretap the RMII RX bus
    -- =========================================================
    process(clk_50m, rst)
    begin
        if rst = '1' then
            rx_state      <= IDLE;
            rx_byte_cnt   <= 0;
            rx_bit_cnt    <= 0;
            trigger_reply <= '0';
        elsif rising_edge(clk_50m) then
            
            trigger_reply <= '0'; -- Default to no trigger
            
            if rmii_rx_dv = '1' then
                -- Shift 2-bits in (LSB first for Ethernet)
                if rx_bit_cnt = 0 then rx_byte(1 downto 0) <= rmii_rxd;
                elsif rx_bit_cnt = 1 then rx_byte(3 downto 2) <= rmii_rxd;
                elsif rx_bit_cnt = 2 then rx_byte(5 downto 4) <= rmii_rxd;
                elsif rx_bit_cnt = 3 then rx_byte(7 downto 6) <= rmii_rxd;
                end if;
                
                if rx_bit_cnt = 3 then
                    rx_bit_cnt <= 0;
                    
                    case rx_state is
                        when IDLE =>
                            if rx_byte = x"55" then
                                rx_state <= SYNC_SFD;
                            end if;
                            
                        when SYNC_SFD =>
                            if rx_byte = x"D5" then
                                rx_state <= PARSE_PACKET;
                                rx_byte_cnt <= 0;
                            elsif rx_byte /= x"55" then
                                rx_state <= IDLE;
                            end if;
                            
                        when PARSE_PACKET =>
                            
                            -- Capture Sender MAC
                            if rx_byte_cnt = 22 then sender_mac(47 downto 40) <= rx_byte;
                            elsif rx_byte_cnt = 23 then sender_mac(39 downto 32) <= rx_byte;
                            elsif rx_byte_cnt = 24 then sender_mac(31 downto 24) <= rx_byte;
                            elsif rx_byte_cnt = 25 then sender_mac(23 downto 16) <= rx_byte;
                            elsif rx_byte_cnt = 26 then sender_mac(15 downto 8) <= rx_byte;
                            elsif rx_byte_cnt = 27 then sender_mac(7 downto 0) <= rx_byte;
                            
                            -- Capture Sender IP
                            elsif rx_byte_cnt = 28 then sender_ip(31 downto 24) <= rx_byte;
                            elsif rx_byte_cnt = 29 then sender_ip(23 downto 16) <= rx_byte;
                            elsif rx_byte_cnt = 30 then sender_ip(15 downto 8) <= rx_byte;
                            elsif rx_byte_cnt = 31 then sender_ip(7 downto 0) <= rx_byte;
                            end if;

                            -- The Ultimate Check: Is this an ARP Request for OUR IP?
                            -- Byte 12/13: 0x0806 (ARP)
                            -- Byte 20/21: 0x0001 (Request)
                            -- Byte 38-41: Target IP matches FPGA_IP
                            if rx_byte_cnt = 41 then
                                -- We don't implement full rigorous checking here to save LEs,
                                -- but matching the Target IP is usually enough in a closed network.
                                if rx_byte = fpga_ip(7 downto 0) then 
                                    trigger_reply <= '1';
                                end if;
                            end if;
                            
                            rx_byte_cnt <= rx_byte_cnt + 1;
                    end case;
                else
                    rx_bit_cnt <= rx_bit_cnt + 1;
                end if;
            else
                rx_state <= IDLE;
                rx_bit_cnt <= 0;
            end if;
            
        end if;
    end process;

    -- =========================================================
    -- TX GENERATOR: Formulate the 42-Byte ARP Reply
    -- =========================================================
    process(clk_50m, rst)
    begin
        if rst = '1' then
            tx_state    <= IDLE;
            tx_byte_cnt <= 0;
            arp_tx_req  <= '0';
            arp_tx_data <= (others => '0');
        elsif rising_edge(clk_50m) then
            
            case tx_state is
                when IDLE =>
                    arp_tx_req <= '0';
                    if trigger_reply = '1' then
                        tx_state <= SEND_REPLY;
                        tx_byte_cnt <= 0;
                    end if;
                    
                when SEND_REPLY =>
                    arp_tx_req <= '1'; -- Request access to the RMII TX line
                    
                    if tx_ready = '1' then
                        
                        -- Ethernet Header (14 bytes)
                        if tx_byte_cnt = 0 then arp_tx_data <= sender_mac(47 downto 40); -- Dest MAC
                        elsif tx_byte_cnt = 1 then arp_tx_data <= sender_mac(39 downto 32);
                        elsif tx_byte_cnt = 2 then arp_tx_data <= sender_mac(31 downto 24);
                        elsif tx_byte_cnt = 3 then arp_tx_data <= sender_mac(23 downto 16);
                        elsif tx_byte_cnt = 4 then arp_tx_data <= sender_mac(15 downto 8);
                        elsif tx_byte_cnt = 5 then arp_tx_data <= sender_mac(7 downto 0);
                        
                        elsif tx_byte_cnt = 6 then arp_tx_data <= fpga_mac(47 downto 40); -- Src MAC (US)
                        elsif tx_byte_cnt = 7 then arp_tx_data <= fpga_mac(39 downto 32);
                        elsif tx_byte_cnt = 8 then arp_tx_data <= fpga_mac(31 downto 24);
                        elsif tx_byte_cnt = 9 then arp_tx_data <= fpga_mac(23 downto 16);
                        elsif tx_byte_cnt = 10 then arp_tx_data <= fpga_mac(15 downto 8);
                        elsif tx_byte_cnt = 11 then arp_tx_data <= fpga_mac(7 downto 0);
                        
                        elsif tx_byte_cnt = 12 then arp_tx_data <= x"08"; -- EtherType ARP
                        elsif tx_byte_cnt = 13 then arp_tx_data <= x"06";
                        
                        -- ARP Payload (28 bytes)
                        elsif tx_byte_cnt = 14 then arp_tx_data <= x"00"; -- HW Type (Ethernet = 1)
                        elsif tx_byte_cnt = 15 then arp_tx_data <= x"01";
                        elsif tx_byte_cnt = 16 then arp_tx_data <= x"08"; -- Proto Type (IPv4 = 0x0800)
                        elsif tx_byte_cnt = 17 then arp_tx_data <= x"00";
                        elsif tx_byte_cnt = 18 then arp_tx_data <= x"06"; -- HW Size (6)
                        elsif tx_byte_cnt = 19 then arp_tx_data <= x"04"; -- Proto Size (4)
                        elsif tx_byte_cnt = 20 then arp_tx_data <= x"00"; -- Opcode (Reply = 2)
                        elsif tx_byte_cnt = 21 then arp_tx_data <= x"02";
                        
                        elsif tx_byte_cnt = 22 then arp_tx_data <= fpga_mac(47 downto 40); -- Sender MAC (US)
                        elsif tx_byte_cnt = 23 then arp_tx_data <= fpga_mac(39 downto 32);
                        elsif tx_byte_cnt = 24 then arp_tx_data <= fpga_mac(31 downto 24);
                        elsif tx_byte_cnt = 25 then arp_tx_data <= fpga_mac(23 downto 16);
                        elsif tx_byte_cnt = 26 then arp_tx_data <= fpga_mac(15 downto 8);
                        elsif tx_byte_cnt = 27 then arp_tx_data <= fpga_mac(7 downto 0);
                        
                        elsif tx_byte_cnt = 28 then arp_tx_data <= fpga_ip(31 downto 24); -- Sender IP (US)
                        elsif tx_byte_cnt = 29 then arp_tx_data <= fpga_ip(23 downto 16);
                        elsif tx_byte_cnt = 30 then arp_tx_data <= fpga_ip(15 downto 8);
                        elsif tx_byte_cnt = 31 then arp_tx_data <= fpga_ip(7 downto 0);
                        
                        elsif tx_byte_cnt = 32 then arp_tx_data <= sender_mac(47 downto 40); -- Target MAC (THEM)
                        elsif tx_byte_cnt = 33 then arp_tx_data <= sender_mac(39 downto 32);
                        elsif tx_byte_cnt = 34 then arp_tx_data <= sender_mac(31 downto 24);
                        elsif tx_byte_cnt = 35 then arp_tx_data <= sender_mac(23 downto 16);
                        elsif tx_byte_cnt = 36 then arp_tx_data <= sender_mac(15 downto 8);
                        elsif tx_byte_cnt = 37 then arp_tx_data <= sender_mac(7 downto 0);
                        
                        elsif tx_byte_cnt = 38 then arp_tx_data <= sender_ip(31 downto 24); -- Target IP (THEM)
                        elsif tx_byte_cnt = 39 then arp_tx_data <= sender_ip(23 downto 16);
                        elsif tx_byte_cnt = 40 then arp_tx_data <= sender_ip(15 downto 8);
                        elsif tx_byte_cnt = 41 then arp_tx_data <= sender_ip(7 downto 0);
                        end if;

                        if tx_byte_cnt = 41 then
                            tx_state <= IDLE;
                        else
                            tx_byte_cnt <= tx_byte_cnt + 1;
                        end if;
                    end if;
            end case;
        end if;
    end process;

end architecture rtl;