library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity udp_tx_core is
    port (
        clk_50m      : in  std_logic;
        rst          : in  std_logic;
        
        -- IP Configuration (Hardcoded per FPGA node)
        fpga_mac     : in  std_logic_vector(47 downto 0);
        fpga_ip      : in  std_logic_vector(31 downto 0);
        pc_mac       : in  std_logic_vector(47 downto 0);
        pc_ip        : in  std_logic_vector(31 downto 0);

        -- Handshake from 18MHz Domain (packet_formatter)
        packet_ready : in  std_logic;
        
        -- Async FIFO Read Interface
        fifo_rd_en   : out std_logic;
        fifo_rd_data : in  std_logic_vector(7 downto 0);
        
        -- Output to RMII Transmitter
        tx_start     : out std_logic;
        tx_data      : out std_logic_vector(7 downto 0);
        tx_ready     : in  std_logic  -- High when RMII is ready for next byte
    );
end entity udp_tx_core;

architecture rtl of udp_tx_core is
    
    -- Two-Stage Synchronizer for the packet_ready toggle
    signal sync_ready_1 : std_logic := '0';
    signal sync_ready_2 : std_logic := '0';
    signal sync_ready_3 : std_logic := '0';
    signal trigger      : std_logic := '0';

    type state_type is (IDLE, SEND_MAC_HDR, SEND_IP_HDR, SEND_UDP_HDR, SEND_PAYLOAD, WAIT_RMII);
    signal state : state_type := IDLE;
    
    signal byte_cnt : integer range 0 to 511 := 0;
    
    -- Pre-calculated IP Checksum (Static for hardcoded IPs & Length)
    -- Length = 20(IP) + 8(UDP) + 410(Payload) = 438 bytes (x01B6)
    constant IP_CHECKSUM : std_logic_vector(15 downto 0) := x"B4E1"; -- Placeholder, needs calculation based on IPs
    
begin

    -- Clock Domain Crossing: Safely detect the toggle from the 18MHz clock
    process(clk_50m)
    begin
        if rising_edge(clk_50m) then
            sync_ready_1 <= packet_ready;
            sync_ready_2 <= sync_ready_1;
            sync_ready_3 <= sync_ready_2;
            
            -- Trigger fires for exactly 1 clock cycle when a toggle is detected
            if sync_ready_2 /= sync_ready_3 then
                trigger <= '1';
            else
                trigger <= '0';
            end if;
        end if;
    end process;

    -- The Network Wrapper State Machine
    process(clk_50m, rst)
    begin
        if rst = '1' then
            state      <= IDLE;
            tx_start   <= '0';
            tx_data    <= (others => '0');
            fifo_rd_en <= '0';
            byte_cnt   <= 0;
        elsif rising_edge(clk_50m) then
            
            -- Default states
            tx_start   <= '0';
            fifo_rd_en <= '0';
            
            case state is
                when IDLE =>
                    if trigger = '1' then
                        state    <= SEND_MAC_HDR;
                        byte_cnt <= 0;
                    end if;
                    
                when SEND_MAC_HDR =>
                    if tx_ready = '1' then
                        tx_start <= '1';
                        -- Destination MAC (PC)
                        if byte_cnt = 0 then tx_data <= pc_mac(47 downto 40);
                        elsif byte_cnt = 1 then tx_data <= pc_mac(39 downto 32);
                        elsif byte_cnt = 2 then tx_data <= pc_mac(31 downto 24);
                        elsif byte_cnt = 3 then tx_data <= pc_mac(23 downto 16);
                        elsif byte_cnt = 4 then tx_data <= pc_mac(15 downto 8);
                        elsif byte_cnt = 5 then tx_data <= pc_mac(7 downto 0);
                        -- Source MAC (FPGA)
                        elsif byte_cnt = 6 then tx_data <= fpga_mac(47 downto 40);
                        elsif byte_cnt = 7 then tx_data <= fpga_mac(39 downto 32);
                        elsif byte_cnt = 8 then tx_data <= fpga_mac(31 downto 24);
                        elsif byte_cnt = 9 then tx_data <= fpga_mac(23 downto 16);
                        elsif byte_cnt = 10 then tx_data <= fpga_mac(15 downto 8);
                        elsif byte_cnt = 11 then tx_data <= fpga_mac(7 downto 0);
                        -- EtherType (IPv4 = 0x0800)
                        elsif byte_cnt = 12 then tx_data <= x"08";
                        elsif byte_cnt = 13 then tx_data <= x"00";
                        end if;
                        
                        if byte_cnt = 13 then
                            state    <= SEND_IP_HDR;
                            byte_cnt <= 0;
                        else
                            byte_cnt <= byte_cnt + 1;
                        end if;
                    end if;
                    
                when SEND_IP_HDR =>
                    if tx_ready = '1' then
                        tx_start <= '1';
                        if byte_cnt = 0 then tx_data <= x"45"; -- Version/IHL
                        elsif byte_cnt = 1 then tx_data <= x"00"; -- DSCP/ECN
                        elsif byte_cnt = 2 then tx_data <= x"01"; -- Total Length MSB (438 = x01B6)
                        elsif byte_cnt = 3 then tx_data <= x"B6"; -- Total Length LSB
                        elsif byte_cnt = 4 then tx_data <= x"00"; -- Identification
                        elsif byte_cnt = 5 then tx_data <= x"00"; 
                        elsif byte_cnt = 6 then tx_data <= x"40"; -- Flags/Fragment Offset (Don't Fragment)
                        elsif byte_cnt = 7 then tx_data <= x"00"; 
                        elsif byte_cnt = 8 then tx_data <= x"40"; -- TTL (64)
                        elsif byte_cnt = 9 then tx_data <= x"11"; -- Protocol (UDP = 17)
                        elsif byte_cnt = 10 then tx_data <= IP_CHECKSUM(15 downto 8);
                        elsif byte_cnt = 11 then tx_data <= IP_CHECKSUM(7 downto 0);
                        elsif byte_cnt = 12 then tx_data <= fpga_ip(31 downto 24);
                        elsif byte_cnt = 13 then tx_data <= fpga_ip(23 downto 16);
                        elsif byte_cnt = 14 then tx_data <= fpga_ip(15 downto 8);
                        elsif byte_cnt = 15 then tx_data <= fpga_ip(7 downto 0);
                        elsif byte_cnt = 16 then tx_data <= pc_ip(31 downto 24);
                        elsif byte_cnt = 17 then tx_data <= pc_ip(23 downto 16);
                        elsif byte_cnt = 18 then tx_data <= pc_ip(15 downto 8);
                        elsif byte_cnt = 19 then tx_data <= pc_ip(7 downto 0);
                        end if;
                        
                        if byte_cnt = 19 then
                            state    <= SEND_UDP_HDR;
                            byte_cnt <= 0;
                        else
                            byte_cnt <= byte_cnt + 1;
                        end if;
                    end if;

                when SEND_UDP_HDR =>
                    if tx_ready = '1' then
                        tx_start <= '1';
                        if byte_cnt = 0 then tx_data <= x"13"; -- Source Port MSB (5005 = x138D)
                        elsif byte_cnt = 1 then tx_data <= x"8D"; -- Source Port LSB 
                        elsif byte_cnt = 2 then tx_data <= x"13"; -- Dest Port MSB (5005)
                        elsif byte_cnt = 3 then tx_data <= x"8D"; -- Dest Port LSB
                        elsif byte_cnt = 4 then tx_data <= x"01"; -- Length MSB (8 + 410 = 418 = x01A2)
                        elsif byte_cnt = 5 then tx_data <= x"A2"; -- Length LSB
                        elsif byte_cnt = 6 then tx_data <= x"00"; -- Checksum (0x0000 is allowed for UDP)
                        elsif byte_cnt = 7 then tx_data <= x"00";
                        end if;
                        
                        if byte_cnt = 7 then
                            state    <= SEND_PAYLOAD;
                            byte_cnt <= 0;
                            fifo_rd_en <= '1'; -- Pre-fetch first byte from FIFO
                        else
                            byte_cnt <= byte_cnt + 1;
                        end if;
                    end if;

                when SEND_PAYLOAD =>
                    if tx_ready = '1' then
                        tx_start <= '1';
                        tx_data  <= fifo_rd_data; -- Push the data we fetched last cycle
                        
                        if byte_cnt = 409 then
                            state    <= IDLE; -- Done!
                        else
                            byte_cnt <= byte_cnt + 1;
                            fifo_rd_en <= '1'; -- Fetch the next byte for the next cycle
                        end if;
                    end if;
                    
                when others =>
                    state <= IDLE;
            end case;
            
        end if;
    end process;

end architecture rtl;