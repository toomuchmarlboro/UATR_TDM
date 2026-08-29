library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity arp_responder is
    port (
        clk_50m      : in  std_logic;
        rst          : in  std_logic;
        fpga_mac     : in  std_logic_vector(47 downto 0);
        fpga_ip      : in  std_logic_vector(31 downto 0);

        -- ARP learning, for udp_tx_core's destination MAC.
        --
        -- The sender MAC and sender IP of every request were already being
        -- captured for the reply path; this just carries them out. learn_valid
        -- is a one clock strobe, asserted with send_reply and additionally
        -- gated on the sender being pc_ip.
        pc_ip        : in  std_logic_vector(31 downto 0);
        learn_mac    : out std_logic_vector(47 downto 0);
        learn_valid  : out std_logic;

        -- MAC RX Interface
        rx_data      : in  std_logic_vector(7 downto 0);
        rx_valid     : in  std_logic;
        rx_end       : in  std_logic;
        rx_error     : in  std_logic;
        
        -- MAC TX Interface
        arp_tx_req   : out std_logic;
        arp_tx_data  : out std_logic_vector(7 downto 0);
        tx_ready     : in  std_logic
    );
end entity arp_responder;

architecture rtl of arp_responder is

    -- RX State Machine
    type rx_state_type is (RX_IDLE, RX_PARSE, RX_WAIT_END);
    signal rx_state : rx_state_type := RX_IDLE;
    
    signal rx_byte_cnt : integer range 0 to 127 := 0;
    signal is_arp_req  : std_logic := '1';
    
    -- Captured Data from Requester
    signal req_mac : std_logic_vector(47 downto 0) := (others => '0');
    signal req_ip  : std_logic_vector(31 downto 0) := (others => '0');
    
    -- TX State Machine
    type tx_state_type is (TX_IDLE, TX_SENDING);
    signal tx_state : tx_state_type := TX_IDLE;

    -- 14 byte Ethernet header + 28 byte ARP payload + 18 bytes of padding.
    -- rmii_tx appends the 4 byte FCS, giving the 64 byte Ethernet minimum.
    constant FRAME_BYTES : integer := 60;

    -- Index of the byte to present at the NEXT acknowledge from rmii_tx.
    -- Byte 0 is preloaded at request time (see the handshake contract in
    -- rmii_tx.vhd), so this always runs one ahead of what is on the wire.
    signal tx_byte_cnt : integer range 0 to 63 := 0;
    signal send_reply  : std_logic := '0';

begin

    -- Held continuously; only meaningful in the cycle learn_valid strobes.
    learn_mac <= req_mac;

    -- ==========================================
    -- RX PROCESS: Parse incoming packets
    -- ==========================================
    process(clk_50m)
    begin
        if rising_edge(clk_50m) then
            if rst = '1' then
                rx_state    <= RX_IDLE;
                rx_byte_cnt <= 0;
                is_arp_req  <= '0';
                send_reply  <= '0';
                learn_valid <= '0';
            else
                send_reply  <= '0'; -- Default strobe
                learn_valid <= '0'; -- Default strobe
                
                case rx_state is
                    when RX_IDLE =>
                        rx_byte_cnt <= 0;
                        is_arp_req  <= '1'; -- Assume valid until proven otherwise
                        if rx_valid = '1' then
                            rx_state <= RX_PARSE;
                            -- Byte 0 is Destination MAC. 
                            -- An ARP is usually a broadcast (0xFF). We'll skip validating MAC 
                            -- here and focus on the EtherType and Target IP.
                            rx_byte_cnt <= 1;
                        end if;
                        
                    when RX_PARSE =>
                        if rx_end = '1' then
                            rx_state <= RX_IDLE;
                        elsif rx_valid = '1' then
                            
                            -- Capture Sender MAC (Bytes 6 to 11)
                            if rx_byte_cnt = 6 then req_mac(47 downto 40) <= rx_data;
                            elsif rx_byte_cnt = 7 then req_mac(39 downto 32) <= rx_data;
                            elsif rx_byte_cnt = 8 then req_mac(31 downto 24) <= rx_data;
                            elsif rx_byte_cnt = 9 then req_mac(23 downto 16) <= rx_data;
                            elsif rx_byte_cnt = 10 then req_mac(15 downto 8)  <= rx_data;
                            elsif rx_byte_cnt = 11 then req_mac(7 downto 0)   <= rx_data;
                            
                            -- Verify EtherType = 0x0806 (ARP)
                            elsif rx_byte_cnt = 12 and rx_data /= x"08" then is_arp_req <= '0';
                            elsif rx_byte_cnt = 13 and rx_data /= x"06" then is_arp_req <= '0';
                            
                            -- Verify Hardware Type = 0x0001 (Ethernet)
                            elsif rx_byte_cnt = 14 and rx_data /= x"00" then is_arp_req <= '0';
                            elsif rx_byte_cnt = 15 and rx_data /= x"01" then is_arp_req <= '0';
                            
                            -- Verify Protocol Type = 0x0800 (IPv4)
                            elsif rx_byte_cnt = 16 and rx_data /= x"08" then is_arp_req <= '0';
                            elsif rx_byte_cnt = 17 and rx_data /= x"00" then is_arp_req <= '0';
                            
                            -- Verify Opcode = 0x0001 (Request)
                            elsif rx_byte_cnt = 20 and rx_data /= x"00" then is_arp_req <= '0';
                            elsif rx_byte_cnt = 21 and rx_data /= x"01" then is_arp_req <= '0';
                            
                            -- Capture Sender IP (Bytes 28 to 31)
                            elsif rx_byte_cnt = 28 then req_ip(31 downto 24) <= rx_data;
                            elsif rx_byte_cnt = 29 then req_ip(23 downto 16) <= rx_data;
                            elsif rx_byte_cnt = 30 then req_ip(15 downto 8)  <= rx_data;
                            elsif rx_byte_cnt = 31 then req_ip(7 downto 0)   <= rx_data;
                            
                            -- Verify Target IP matches FPGA IP (Bytes 38 to 41)
                            elsif rx_byte_cnt = 38 and rx_data /= fpga_ip(31 downto 24) then is_arp_req <= '0';
                            elsif rx_byte_cnt = 39 and rx_data /= fpga_ip(23 downto 16) then is_arp_req <= '0';
                            elsif rx_byte_cnt = 40 and rx_data /= fpga_ip(15 downto 8)  then is_arp_req <= '0';
                            elsif rx_byte_cnt = 41 and rx_data /= fpga_ip(7 downto 0)   then is_arp_req <= '0';
                            end if;

                            -- Move to next state after checking target IP or just keep counting
                            if rx_byte_cnt = 41 then
                                rx_state <= RX_WAIT_END;
                            else
                                rx_byte_cnt <= rx_byte_cnt + 1;
                            end if;
                        end if;
                        
                    when RX_WAIT_END =>
                        if rx_end = '1' then
                            rx_state <= RX_IDLE;
                            -- Only reply if it was a valid ARP request AND the CRC was clean
                            if is_arp_req = '1' and rx_error = '0' then
                                send_reply <= '1';

                                -- Same gate, plus "the sender really is the
                                -- capture host". req_mac has been stable since
                                -- byte 11 and req_ip since byte 31, both long
                                -- before this state is reached.
                                if req_ip = pc_ip then
                                    learn_valid <= '1';
                                end if;
                            end if;
                        end if;
                        
                end case;
            end if;
        end if;
    end process;


    -- ==========================================
    -- TX PROCESS: Generate ARP Reply
    -- ==========================================
    process(clk_50m)
    begin
        if rising_edge(clk_50m) then
            if rst = '1' then
                tx_state    <= TX_IDLE;
                arp_tx_req  <= '0';
                arp_tx_data <= (others => '0');
                tx_byte_cnt <= 0;
            else
                case tx_state is
                    when TX_IDLE =>
                        arp_tx_req  <= '0';
                        if send_reply = '1' then
                            -- Raise the request as a LEVEL and present byte 0
                            -- immediately: rmii_tx latches tx_data in the same
                            -- cycle it first raises tx_ready, so the byte has to
                            -- already be on the bus before that acknowledge.
                            arp_tx_req  <= '1';
                            arp_tx_data <= req_mac(47 downto 40); -- Dest MAC MSB
                            tx_byte_cnt <= 1;
                            tx_state    <= TX_SENDING;
                        end if;

                    when TX_SENDING =>
                        if tx_ready = '1' and tx_byte_cnt = FRAME_BYTES then
                            -- rmii_tx just consumed the final byte on this same
                            -- acknowledge. Drop the request so the next
                            -- acknowledge terminates the frame and appends the FCS.
                            arp_tx_req  <= '0';
                            tx_byte_cnt <= 0;
                            tx_state    <= TX_IDLE;

                        elsif tx_ready = '1' then

                            -- Construct the Ethernet Frame + ARP Payload (42 bytes total)
                            case tx_byte_cnt is
                                -- ETHERNET HEADER
                                when 1 => arp_tx_data <= req_mac(39 downto 32);     -- Dest MAC
                                when 2 => arp_tx_data <= req_mac(31 downto 24);
                                when 3 => arp_tx_data <= req_mac(23 downto 16);
                                when 4 => arp_tx_data <= req_mac(15 downto 8);
                                when 5 => arp_tx_data <= req_mac(7 downto 0);
                                
                                when 6 => arp_tx_data <= fpga_mac(47 downto 40);    -- Source MAC
                                when 7 => arp_tx_data <= fpga_mac(39 downto 32);
                                when 8 => arp_tx_data <= fpga_mac(31 downto 24);
                                when 9 => arp_tx_data <= fpga_mac(23 downto 16);
                                when 10=> arp_tx_data <= fpga_mac(15 downto 8);
                                when 11=> arp_tx_data <= fpga_mac(7 downto 0);
                                
                                when 12=> arp_tx_data <= x"08";                     -- EtherType (ARP = 0x0806)
                                when 13=> arp_tx_data <= x"06";
                                
                                -- ARP PAYLOAD
                                when 14=> arp_tx_data <= x"00";                     -- Hardware Type (Ethernet = 1)
                                when 15=> arp_tx_data <= x"01";
                                when 16=> arp_tx_data <= x"08";                     -- Protocol Type (IPv4 = 0x0800)
                                when 17=> arp_tx_data <= x"00";
                                when 18=> arp_tx_data <= x"06";                     -- Hardware Size (6)
                                when 19=> arp_tx_data <= x"04";                     -- Protocol Size (4)
                                when 20=> arp_tx_data <= x"00";                     -- Opcode (Reply = 2)
                                when 21=> arp_tx_data <= x"02";
                                
                                when 22=> arp_tx_data <= fpga_mac(47 downto 40);    -- Sender MAC (FPGA)
                                when 23=> arp_tx_data <= fpga_mac(39 downto 32);
                                when 24=> arp_tx_data <= fpga_mac(31 downto 24);
                                when 25=> arp_tx_data <= fpga_mac(23 downto 16);
                                when 26=> arp_tx_data <= fpga_mac(15 downto 8);
                                when 27=> arp_tx_data <= fpga_mac(7 downto 0);
                                
                                when 28=> arp_tx_data <= fpga_ip(31 downto 24);     -- Sender IP (FPGA)
                                when 29=> arp_tx_data <= fpga_ip(23 downto 16);
                                when 30=> arp_tx_data <= fpga_ip(15 downto 8);
                                when 31=> arp_tx_data <= fpga_ip(7 downto 0);
                                
                                when 32=> arp_tx_data <= req_mac(47 downto 40);     -- Target MAC (PC)
                                when 33=> arp_tx_data <= req_mac(39 downto 32);
                                when 34=> arp_tx_data <= req_mac(31 downto 24);
                                when 35=> arp_tx_data <= req_mac(23 downto 16);
                                when 36=> arp_tx_data <= req_mac(15 downto 8);
                                when 37=> arp_tx_data <= req_mac(7 downto 0);
                                
                                when 38=> arp_tx_data <= req_ip(31 downto 24);      -- Target IP (PC)
                                when 39=> arp_tx_data <= req_ip(23 downto 16);
                                when 40=> arp_tx_data <= req_ip(15 downto 8);
                                when 41=> arp_tx_data <= req_ip(7 downto 0);
                                
                                -- PAD TO 60 BYTES MINIMUM ETHERNET FRAME (excluding FCS/CRC)
                                -- 14 byte header + 28 byte ARP = 42 bytes. Need 18 bytes of padding.
                                when 42 to 59 => 
                                    arp_tx_data <= x"00";
                                
                                when others =>
                                    arp_tx_data <= x"00";
                            end case;

                            tx_byte_cnt <= tx_byte_cnt + 1;
                        end if;
                end case;
            end if;
        end if;
    end process;

end architecture rtl;