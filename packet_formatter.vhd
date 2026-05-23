library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity packet_formatter is
    port (
        clk_18m      : in  std_logic;
        rst          : in  std_logic;

        -- Audio Domain Inputs
        tdm16_valid  : in  std_logic;
        tdm16_data   : in  std_logic_vector(383 downto 0);

        -- Async FIFO Interface (Write Side)
        fifo_wr_en   : out std_logic;
        fifo_wr_data : out std_logic_vector(7 downto 0);

        -- Signal to 50MHz Domain
        packet_ready : out std_logic  -- Toggles when exactly 410 bytes are written
    );
end entity packet_formatter;

architecture rtl of packet_formatter is
    
    type state_type is (IDLE, WRITE_HEADER, WRITE_FRAME);
    signal state        : state_type := IDLE;

    signal latched_tdm  : std_logic_vector(383 downto 0) := (others => '0');
    signal byte_cnt     : integer range 0 to 63 := 0;
    signal frame_count  : integer range 0 to 7 := 0;
    signal seq_num      : unsigned(31 downto 0) := (others => '0');
    
    -- We use a toggle instead of a 1-clock pulse to cross clock domains safely
    signal ready_toggle : std_logic := '0';

begin
    
    packet_ready <= ready_toggle;

    process(clk_18m, rst)
    begin
        if rst = '1' then
            state        <= IDLE;
            fifo_wr_en   <= '0';
            fifo_wr_data <= (others => '0');
            byte_cnt     <= 0;
            frame_count  <= 0;
            seq_num      <= (others => '0');
            ready_toggle <= '0';
            
        elsif rising_edge(clk_18m) then

            -- Default: Do not write to FIFO unless explicitly commanded
            fifo_wr_en <= '0';

            case state is
                when IDLE =>
                    if tdm16_valid = '1' then
                        latched_tdm <= tdm16_data;
                        if frame_count = 0 then
                            state    <= WRITE_HEADER;
                            byte_cnt <= 0;
                        else
                            state    <= WRITE_FRAME;
                            byte_cnt <= 0;
                        end if;
                    end if;

                when WRITE_HEADER =>
                    fifo_wr_en <= '1';
                    
                    case byte_cnt is
                        when 0 => fifo_wr_data <= x"AD";
                        when 1 => fifo_wr_data <= x"A1";
                        when 2 => fifo_wr_data <= x"97";
                        when 3 => fifo_wr_data <= x"78";
                        when 4 => fifo_wr_data <= std_logic_vector(seq_num(31 downto 24));
                        when 5 => fifo_wr_data <= std_logic_vector(seq_num(23 downto 16));
                        when 6 => fifo_wr_data <= std_logic_vector(seq_num(15 downto 8));
                        when 7 => fifo_wr_data <= std_logic_vector(seq_num(7 downto 0));
                        when 8 => fifo_wr_data <= x"00"; -- Frame count MSB
                        when 9 => fifo_wr_data <= x"08"; -- Frame count LSB (8 frames)
                        when others => fifo_wr_data <= x"00";
                    end case;

                    if byte_cnt = 9 then
                        state    <= WRITE_FRAME;
                        byte_cnt <= 0;
                    else
                        byte_cnt <= byte_cnt + 1;
                    end if;

                when WRITE_FRAME =>
                    fifo_wr_en <= '1';

                    if byte_cnt = 0 then
                        fifo_wr_data <= x"00"; -- Frame Index MSB
                    elsif byte_cnt = 1 then
                        fifo_wr_data <= std_logic_vector(to_unsigned(frame_count, 8)); -- Frame Index LSB
                    else
                        -- Bytes 2 through 49 are the sliced audio payload
                        fifo_wr_data <= latched_tdm(383 downto 376);
                        
                        -- Shift the giant register left by 8 bits for the next clock cycle
                        latched_tdm <= latched_tdm(375 downto 0) & x"00";
                    end if;

                    if byte_cnt = 49 then
                        state <= IDLE;
                        
                        -- If we just finished the 8th frame, packet is fully in the FIFO!
                        if frame_count = 7 then
                            frame_count  <= 0;
                            seq_num      <= seq_num + 1;
                            ready_toggle <= not ready_toggle; -- Send signal to 50 MHz domain
                        else
                            frame_count  <= frame_count + 1;
                        end if;
                    else
                        byte_cnt <= byte_cnt + 1;
                    end if;

            end case;
        end if;
    end process;

end architecture rtl;