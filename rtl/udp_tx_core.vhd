library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.net_pkg.all;

entity udp_tx_core is
    port (
        clk_50m      : in  std_logic;
        rst          : in  std_logic;

        -- IP Configuration. All driven from C_NODE at the top level.
        fpga_mac     : in  std_logic_vector(47 downto 0);
        fpga_ip      : in  std_logic_vector(31 downto 0);
        pc_mac       : in  std_logic_vector(47 downto 0);
        pc_ip        : in  std_logic_vector(31 downto 0);

        -- Used for BOTH source and destination UDP port. One port per board so
        -- the host can open one socket per board: udp_monitor.py calls recv(),
        -- not recvfrom(), so four boards sharing a port would interleave four
        -- sequence-number streams into one socket and loss_report would show
        -- enormous losses that are not real.
        udp_port     : in  std_logic_vector(15 downto 0);

        -- Handshake from 18MHz Domain (packet_formatter)
        packet_ready : in  std_logic;

        -- Async FIFO Read Interface
        fifo_rd_en   : out std_logic;
        fifo_rd_data : in  std_logic_vector(7 downto 0);

        -- Output to RMII Transmitter (see handshake contract in rmii_tx.vhd)
        tx_start     : out std_logic; -- LEVEL: held high for the whole frame
        tx_data      : out std_logic_vector(7 downto 0);
        tx_ready     : in  std_logic  -- ACKNOWLEDGE: byte on tx_data was taken
    );
end entity udp_tx_core;

architecture rtl of udp_tx_core is

    -- Two-Stage Synchronizer for the packet_ready toggle
    signal sync_ready_1 : std_logic := '0';
    signal sync_ready_2 : std_logic := '0';
    signal sync_ready_3 : std_logic := '0';
    signal trigger      : std_logic := '0';

    type state_type is (IDLE, SENDING);
    signal state : state_type := IDLE;

    -- Frame layout: 14 byte Ethernet header + 20 byte IP header
    --             +  8 byte UDP header + 410 byte payload = 452 bytes.
    -- rmii_tx appends the 4 byte FCS.
    constant HDR_BYTES     : integer := 42;
    constant PAYLOAD_BYTES : integer := 410;
    constant TOTAL_BYTES   : integer := HDR_BYTES + PAYLOAD_BYTES;

    -- Index of the byte to present at the NEXT acknowledge from rmii_tx. Byte 0
    -- is preloaded at request time, so this always runs one ahead of the wire.
    signal byte_cnt  : integer range 0 to 511 := 0;
    signal tx_req    : std_logic := '0';
    signal next_byte : std_logic_vector(7 downto 0);

    -- IPv4 header total length, and the UDP length that shadows it.
    constant IP_TOTAL_LEN : integer := 20 + 8 + PAYLOAD_BYTES;  -- 438
    constant IP_LEN_V  : std_logic_vector(15 downto 0) :=
        std_logic_vector(to_unsigned(IP_TOTAL_LEN, 16));
    constant UDP_LEN_V : std_logic_vector(15 downto 0) :=
        std_logic_vector(to_unsigned(8 + PAYLOAD_BYTES, 16));

    -- IPv4 header checksum, COMPUTED (work.net_pkg) rather than hand-entered.
    --
    -- This was the literal x"B577", correct for 192.168.1.101 -> 192.168.1.10
    -- and for nothing else. That is a trap as soon as there is more than one
    -- node: change fpga_ip and forget the checksum, and the board transmits
    -- perfectly, the frames appear in Wireshark, and the host kernel discards
    -- every one of them at the IP layer before any socket sees them. You get a
    -- board that looks alive on the wire and delivers nothing.
    --
    -- fpga_ip and pc_ip are driven by constants at the top level, so synthesis
    -- constant-folds all of this back down to two literal bytes. It costs
    -- nothing and it can never go stale. top_system asserts the same function
    -- against known-good values for all four nodes at elaboration.
    signal ip_checksum : std_logic_vector(15 downto 0);

begin

    ip_checksum <= ipv4_checksum(fpga_ip, pc_ip, IP_LEN_V);

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

    -- ==========================================
    -- HEADER ROM
    -- Combinational lookup of the byte at position byte_cnt. Anything at or past
    -- HDR_BYTES is payload and comes straight off the FIFO output register.
    -- ==========================================
    process(byte_cnt, pc_mac, fpga_mac, fpga_ip, pc_ip,
            udp_port, ip_checksum, fifo_rd_data)
    begin
        case byte_cnt is
            -- ETHERNET HEADER
            when 0  => next_byte <= pc_mac(47 downto 40);   -- Destination MAC (PC)
            when 1  => next_byte <= pc_mac(39 downto 32);
            when 2  => next_byte <= pc_mac(31 downto 24);
            when 3  => next_byte <= pc_mac(23 downto 16);
            when 4  => next_byte <= pc_mac(15 downto 8);
            when 5  => next_byte <= pc_mac(7 downto 0);
            when 6  => next_byte <= fpga_mac(47 downto 40); -- Source MAC (FPGA)
            when 7  => next_byte <= fpga_mac(39 downto 32);
            when 8  => next_byte <= fpga_mac(31 downto 24);
            when 9  => next_byte <= fpga_mac(23 downto 16);
            when 10 => next_byte <= fpga_mac(15 downto 8);
            when 11 => next_byte <= fpga_mac(7 downto 0);
            when 12 => next_byte <= x"08";                  -- EtherType (IPv4 = 0x0800)
            when 13 => next_byte <= x"00";

            -- IPv4 HEADER
            when 14 => next_byte <= x"45";                  -- Version / IHL
            when 15 => next_byte <= x"00";                  -- DSCP / ECN
            when 16 => next_byte <= IP_LEN_V(15 downto 8);  -- Total Length MSB (438 = x01B6)
            when 17 => next_byte <= IP_LEN_V(7 downto 0);   -- Total Length LSB
            when 18 => next_byte <= x"00";                  -- Identification
            when 19 => next_byte <= x"00";
            when 20 => next_byte <= x"40";                  -- Flags (Don't Fragment)
            when 21 => next_byte <= x"00";                  -- Fragment Offset
            when 22 => next_byte <= x"40";                  -- TTL (64)
            when 23 => next_byte <= x"11";                  -- Protocol (UDP = 17)
            when 24 => next_byte <= ip_checksum(15 downto 8);
            when 25 => next_byte <= ip_checksum(7 downto 0);
            when 26 => next_byte <= fpga_ip(31 downto 24);  -- Source IP
            when 27 => next_byte <= fpga_ip(23 downto 16);
            when 28 => next_byte <= fpga_ip(15 downto 8);
            when 29 => next_byte <= fpga_ip(7 downto 0);
            when 30 => next_byte <= pc_ip(31 downto 24);    -- Destination IP
            when 31 => next_byte <= pc_ip(23 downto 16);
            when 32 => next_byte <= pc_ip(15 downto 8);
            when 33 => next_byte <= pc_ip(7 downto 0);

            -- UDP HEADER
            when 34 => next_byte <= udp_port(15 downto 8);  -- Source Port MSB (node 1 = 5005 = x138D)
            when 35 => next_byte <= udp_port(7 downto 0);   -- Source Port LSB
            when 36 => next_byte <= udp_port(15 downto 8);  -- Dest Port MSB
            when 37 => next_byte <= udp_port(7 downto 0);   -- Dest Port LSB
            when 38 => next_byte <= UDP_LEN_V(15 downto 8); -- Length MSB (8 + 410 = 418 = x01A2)
            when 39 => next_byte <= UDP_LEN_V(7 downto 0);  -- Length LSB
            when 40 => next_byte <= x"00";                  -- Checksum (0x0000 = unused, legal for IPv4/UDP)
            when 41 => next_byte <= x"00";

            -- PAYLOAD
            when others => next_byte <= fifo_rd_data;
        end case;
    end process;

    tx_start <= tx_req;

    -- ==========================================
    -- FRAME SEQUENCER
    -- ==========================================
    process(clk_50m, rst)
    begin
        if rst = '1' then
            state      <= IDLE;
            tx_req     <= '0';
            tx_data    <= (others => '0');
            fifo_rd_en <= '0';
            byte_cnt   <= 0;
        elsif rising_edge(clk_50m) then

            fifo_rd_en <= '0'; -- Default

            case state is
                when IDLE =>
                    if trigger = '1' then
                        -- Raise the request as a LEVEL and present byte 0 in the
                        -- same cycle. rmii_tx latches tx_data on the very first
                        -- tx_ready, so the byte must already be on the bus - it
                        -- cannot be produced in response to the acknowledge.
                        tx_req   <= '1';
                        tx_data  <= next_byte; -- byte_cnt is 0 here
                        byte_cnt <= 1;
                        state    <= SENDING;
                    end if;

                when SENDING =>
                    if tx_ready = '1' then
                        if byte_cnt = TOTAL_BYTES then
                            -- rmii_tx consumed the final byte on this same
                            -- acknowledge. Drop the request so the next
                            -- acknowledge terminates the frame and appends the FCS.
                            tx_req   <= '0';
                            byte_cnt <= 0;
                            state    <= IDLE;
                        else
                            tx_data  <= next_byte;
                            byte_cnt <= byte_cnt + 1;

                            -- Prefetch for position byte_cnt+1 when that position
                            -- is payload. The FIFO is in normal (not show-ahead)
                            -- mode so q settles one clock after rdreq, and the
                            -- acknowledges are four clocks apart - ample margin.
                            if byte_cnt >= HDR_BYTES - 1 and byte_cnt <= TOTAL_BYTES - 2 then
                                fifo_rd_en <= '1';
                            end if;
                        end if;
                    end if;
            end case;

        end if;
    end process;

end architecture rtl;
