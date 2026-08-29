library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity udp_rx_core is
    port (
        clk_50m      : in  std_logic;
        rst          : in  std_logic;
        fpga_mac     : in  std_logic_vector(47 downto 0);
        fpga_ip      : in  std_logic_vector(31 downto 0);
        
        -- MAC RX Interface
        rx_data      : in  std_logic_vector(7 downto 0);
        rx_valid     : in  std_logic;
        rx_end       : in  std_logic;
        rx_error     : in  std_logic;
        
        -- Sequencer Interface
        udp_req      : out std_logic;
        udp_ack      : in  std_logic;
        udp_adc_sel  : out std_logic_vector(1 downto 0);
        udp_ch_sel   : out std_logic_vector(1 downto 0);
        udp_gain     : out std_logic_vector(7 downto 0);
        -- Optional 3rd payload byte. bit 0 = 48V phantom enable. A 2-byte
        -- packet still works and simply leaves the flags unchanged, so the
        -- original gain-only protocol is preserved.
        udp_flags    : out std_logic_vector(7 downto 0);
        -- One-cycle pulse each time a packet actually CARRIED a flags byte and
        -- udp_flags was written from it. Not the same as udp_req: a 2-byte
        -- gain-only packet raises udp_req and never pulses this. The phantom
        -- watchdog in top_system uses it, and the distinction is the point -
        -- the watchdog must be fed by a host that is still stating what it
        -- wants phantom power to do, not merely by one still sending traffic.
        udp_flags_wr : out std_logic
    );
end entity udp_rx_core;

architecture rtl of udp_rx_core is

    type state_type is (IDLE, PARSE_HEADER, WAIT_END, TRIGGER_SEQ);
    signal state : state_type := IDLE;
    
    signal byte_cnt   : integer range 0 to 127 := 0;
    signal is_valid_pkt : std_logic := '0';
    
    -- Internal holding registers for payload data
    signal int_adc_sel : std_logic_vector(1 downto 0) := "00";
    signal int_ch_sel  : std_logic_vector(1 downto 0) := "00";
    signal int_gain    : std_logic_vector(7 downto 0) := x"00";
    signal int_flags   : std_logic_vector(7 downto 0) := x"00";
    signal have_flags  : std_logic := '0';

begin

    process(clk_50m)
    begin
        if rising_edge(clk_50m) then
            if rst = '1' then
                state        <= IDLE;
                byte_cnt     <= 0;
                is_valid_pkt <= '0';
                udp_req      <= '0';
                udp_adc_sel  <= "00";
                udp_ch_sel   <= "00";
                udp_gain     <= x"A0"; -- Default gain
                udp_flags    <= x"00"; -- 48V off until commanded
                udp_flags_wr <= '0';
                have_flags   <= '0';
            else
                case state is
                    
                    when IDLE =>
                        udp_flags_wr <= '0';    -- one cycle only
                        byte_cnt <= 0;
                        is_valid_pkt <= '1'; -- Assume valid until a header check fails
                        if rx_valid = '1' then
                            state <= PARSE_HEADER;
                            
                            -- Verify Dest MAC (Bytes 0-5) matches FPGA MAC or Broadcast (0xFF)
                            if rx_data /= fpga_mac(47 downto 40) and rx_data /= x"FF" then 
                                is_valid_pkt <= '0'; 
                            end if;
                            
                            byte_cnt <= 1;
                        end if;
                        
                        -- Handle sequencer handshake
                        if udp_ack = '1' then
                            udp_req <= '0';
                        end if;

                    when PARSE_HEADER =>
                        if rx_end = '1' then
                            state <= IDLE;
                        elsif rx_valid = '1' then
                            
                            -- Check Dest MAC remaining bytes
                            if byte_cnt = 1 and rx_data /= fpga_mac(39 downto 32) and rx_data /= x"FF" then is_valid_pkt <= '0';
                            elsif byte_cnt = 2 and rx_data /= fpga_mac(31 downto 24) and rx_data /= x"FF" then is_valid_pkt <= '0';
                            elsif byte_cnt = 3 and rx_data /= fpga_mac(23 downto 16) and rx_data /= x"FF" then is_valid_pkt <= '0';
                            elsif byte_cnt = 4 and rx_data /= fpga_mac(15 downto 8)  and rx_data /= x"FF" then is_valid_pkt <= '0';
                            elsif byte_cnt = 5 and rx_data /= fpga_mac(7 downto 0)   and rx_data /= x"FF" then is_valid_pkt <= '0';
                            
                            -- Verify EtherType = 0x0800 (IPv4)
                            elsif byte_cnt = 12 and rx_data /= x"08" then is_valid_pkt <= '0';
                            elsif byte_cnt = 13 and rx_data /= x"00" then is_valid_pkt <= '0';
                            
                            -- Verify IPv4 Protocol = 0x11 (UDP)
                            elsif byte_cnt = 23 and rx_data /= x"11" then is_valid_pkt <= '0';
                            
                            -- Verify Target IP matches FPGA IP (Bytes 30 to 33)
                            elsif byte_cnt = 30 and rx_data /= fpga_ip(31 downto 24) then is_valid_pkt <= '0';
                            elsif byte_cnt = 31 and rx_data /= fpga_ip(23 downto 16) then is_valid_pkt <= '0';
                            elsif byte_cnt = 32 and rx_data /= fpga_ip(15 downto 8)  then is_valid_pkt <= '0';
                            elsif byte_cnt = 33 and rx_data /= fpga_ip(7 downto 0)   then is_valid_pkt <= '0';
                            
                            -- Extract UDP Payload (Starts at Byte 42)
                            -- Assuming Byte 42 contains ADC & Channel config: [3:2] ADC Sel, [1:0] CH Sel
                            elsif byte_cnt = 42 then
                                int_adc_sel <= rx_data(3 downto 2);
                                int_ch_sel  <= rx_data(1 downto 0);
                            -- Assuming Byte 43 contains Volume/Gain mapping
                            elsif byte_cnt = 43 then
                                int_gain <= rx_data;
                            -- Byte 44, if the sender supplies it: control flags.
                            elsif byte_cnt = 44 then
                                int_flags  <= rx_data;
                                have_flags <= '1';
                            end if;

                            -- Run to byte 44 rather than stopping at 43, so a
                            -- 3-byte payload is captured. rx_end in WAIT_END
                            -- still fires the trigger, so a 2-byte payload
                            -- behaves exactly as before - it just never sets
                            -- have_flags and the previous flag state persists.
                            if byte_cnt = 44 then
                                state <= WAIT_END;
                            else
                                byte_cnt <= byte_cnt + 1;
                            end if;
                        end if;

                        -- a 2-byte payload ends here, before byte 44
                        if rx_end = '1' then
                            state <= WAIT_END;
                        end if;

                    when WAIT_END =>
                        -- Wait for the packet to finish transmitting over the MAC
                        if rx_end = '1' then
                            if is_valid_pkt = '1' and rx_error = '0' then
                                state <= TRIGGER_SEQ;
                            else
                                state <= IDLE;
                            end if;
                        end if;
                        
                    when TRIGGER_SEQ =>
                        -- Push valid extracted data to the output ports
                        udp_adc_sel <= int_adc_sel;
                        udp_ch_sel  <= int_ch_sel;
                        udp_gain    <= int_gain;
                        if have_flags = '1' then
                            udp_flags    <= int_flags;
                            udp_flags_wr <= '1';
                        end if;
                        -- Clear it. have_flags used to latch for the lifetime
                        -- of the design: once ANY 3-byte packet had arrived,
                        -- every later 2-byte packet re-applied that stale
                        -- int_flags, which contradicts the comment above about
                        -- a 2-byte payload leaving the flag state alone. It
                        -- made no behavioural difference - int_flags and
                        -- udp_flags were equal by then, so the rewrite was a
                        -- no-op - but it made "this packet carried flags"
                        -- unusable as a signal, which the phantom watchdog
                        -- needs it to be.
                        have_flags  <= '0';
                        udp_req     <= '1';
                        state       <= IDLE;

                end case;
            end if;
        end if;
    end process;

end architecture rtl;