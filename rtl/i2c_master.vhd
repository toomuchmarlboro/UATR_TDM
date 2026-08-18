library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity i2c_master is
    generic (
        -- Quarter of an I2C bit period, in clk cycles. SCL is low on phases 0-1 and
    -- high on phases 2-3, i.e. a true 50% duty clock, so tLOW and tHIGH are each
    -- two quarter bits (5 us at 100 kHz) against standard-mode minimums of
    -- 4.7 us and 4.0 us.
        -- 50 MHz / 100 kHz = 500 per bit, / 4 phases = 125
        QUARTER_BIT_CYCLES : integer := 31
    );
    port (
        clk          : in  std_logic;
        rst_n        : in  std_logic;

        -- Sequencer Interface
        ena          : in  std_logic;
        rd_mode      : in  std_logic; -- '0' = write data_wr, '1' = read into data_rd
        -- Address-only probe: send START + address + R/W, sample the ACK, STOP.
        -- Touches no register, so it is safe to sweep across every address.
        probe_mode   : in  std_logic;
        addr         : in  std_logic_vector(6 downto 0);
        reg_addr     : in  std_logic_vector(7 downto 0);
        data_wr      : in  std_logic_vector(7 downto 0);
        data_rd      : out std_logic_vector(7 downto 0);
        busy         : out std_logic;

        -- '1' if any acknowledge slot in the last transaction was not pulled low
        -- by a slave. Valid once busy falls.
        ack_error    : out std_logic;
        -- ACK of the ADDRESS byte alone, which is what a bus scan cares about
        addr_nack    : out std_logic;

        -- Set if a line was found low while the master had BOTH released, and
        -- stayed that way. A stuck-low SDA makes every ACK read '0', so
        -- ack_error alone cannot tell a healthy bus from a jammed one.
        bus_stuck    : out std_logic;
        scl_stuck    : out std_logic;
        sda_stuck    : out std_logic;

        -- Power-on self test: each line is driven low and read straight back.
        -- Proves the FPGA's open-drain OUTPUT works, which the stuck detector
        -- (an input-only check) cannot tell us.
        scl_drv_ok   : out std_logic;
        sda_drv_ok   : out std_logic;
        selftest_done: out std_logic;
        -- '1' if the bus ever had to be clocked free of a jammed slave
        recovered    : out std_logic;

        -- I2C lines as open-drain intent plus readback. The tri-state buffers
        -- live in the top level so the two conductors can be crossed there
        -- without touching pin assignments.
        scl_o        : out std_logic;   -- '0' = pull low, '1' = release
        sda_o        : out std_logic;
        scl_i        : in  std_logic;   -- value read back off the wire
        sda_i        : in  std_logic
    );
end entity i2c_master;

architecture rtl of i2c_master is

    type state_type is (
        ST_ST1, ST_ST2, ST_ST3, ST_ST4,   -- output drive self test
        ST_RECOVER,                       -- free a slave jamming SDA
        ST_IDLE,
        ST_START,
        ST_WR_ADDR,   ST_ACK_ADDR,
        ST_WR_REG,    ST_ACK_REG,
        -- write path
        ST_WR_DATA,   ST_ACK_DATA,
        -- read path: repeated START, re-address with R, shift in, master NACK
        ST_RESTART,
        ST_WR_ADDR_R, ST_ACK_ADDR_R,
        ST_RD_DATA,   ST_NACK_DATA,
        ST_STOP
    );
    signal state : state_type;

    -- Internal signals for open-drain driving
    signal sda_int : std_logic;
    signal scl_int : std_logic;

    -- Timing and Phase counters
    signal clk_cnt : integer range 0 to QUARTER_BIT_CYCLES;
    signal phase   : integer range 0 to 3;
    signal bit_cnt : integer range 0 to 7 := 0;

    signal tx_shift : std_logic_vector(7 downto 0);
    signal rx_shift : std_logic_vector(7 downto 0) := (others => '0');
    signal is_read  : std_logic := '0';

    -- The sequencer raises ena for a SINGLE clk cycle, but the state machine
    -- below only advances once per quarter bit (126 clocks at 100 kHz). Sampling
    -- ena there would miss the pulse almost every time and the master would
    -- never leave ST_IDLE. Capture it at full clock rate instead.
    signal ena_latched : std_logic := '0';
    signal scl_drv, sda_drv, st_done : std_logic := '0';
    signal is_probe  : std_logic := '0';
    -- Bus recovery: a slave left mid-transfer can hold SDA low forever. Nine
    -- SCL pulses with SDA released walks it to the end of its byte, then a STOP
    -- returns it to idle. Standard I2C practice.
    signal rec_cnt   : integer range 0 to 9 := 0;
    signal rec_tries : integer range 0 to 15 := 0;
    signal recovered_i : std_logic := '0';
    signal anack     : std_logic := '0';

    -- Sticky for the duration of one transaction
    signal nack_flag : std_logic := '0';
    -- Sticky until reset
    signal stuck_flag : std_logic := '0';
    signal scl_low    : std_logic := '0';
    signal sda_low    : std_logic := '0';

    -- A single low sample is NOT enough to declare the bus jammed: during
    -- power-up either line can read low briefly. Require persistence. The idle
    -- check runs once per quarter bit, so 2000 consecutive samples is far
    -- longer than any settling transient.
    constant STUCK_PERSIST : integer := 200;
    signal scl_low_cnt : integer range 0 to STUCK_PERSIST := 0;
    signal sda_low_cnt : integer range 0 to STUCK_PERSIST := 0;

begin

    ack_error <= nack_flag;
    addr_nack <= anack;
    bus_stuck <= stuck_flag;
    scl_stuck <= scl_low;
    sda_stuck <= sda_low;
    scl_drv_ok    <= scl_drv;
    sda_drv_ok    <= sda_drv;
    selftest_done <= st_done;
    recovered     <= recovered_i;

    scl_o <= scl_int;
    sda_o <= sda_int;

    process(clk, rst_n)
    begin
        if rst_n = '0' then
            state       <= ST_ST1;
            scl_drv     <= '0';
            sda_drv     <= '0';
            st_done     <= '0';
            busy        <= '0';
            sda_int     <= '1';
            scl_int     <= '1';
            clk_cnt     <= 0;
            phase       <= 0;
            bit_cnt     <= 7;
            tx_shift    <= (others => '0');
            rx_shift    <= (others => '0');
            data_rd     <= (others => '0');
            is_read     <= '0';
            nack_flag   <= '0';
            stuck_flag  <= '0';
            scl_low     <= '0';
            sda_low     <= '0';
            scl_low_cnt <= 0;
            sda_low_cnt <= 0;
            ena_latched <= '0';
            rec_cnt     <= 0;
            rec_tries   <= 0;
            recovered_i <= '0';

        elsif rising_edge(clk) then

            -- Full-rate capture, independent of the quarter-bit divider
            if ena = '1' then
                ena_latched <= '1';
            end if;

            if clk_cnt < QUARTER_BIT_CYCLES then
                clk_cnt <= clk_cnt + 1;
            else
                clk_cnt <= 0;

                if phase = 3 then
                    phase <= 0;
                else
                    phase <= phase + 1;
                end if;

                case state is

                    -- ---------------- output drive self test ----------------
                    when ST_ST1 =>
                        scl_int <= '0';          -- pull SCL down
                        sda_int <= '1';
                        state   <= ST_ST2;

                    when ST_ST2 =>
                        -- SCL has been driven low for a full quarter bit; the
                        -- pull-up cannot win against a working output driver.
                        if scl_i = '0' then
                            scl_drv <= '1';
                        end if;
                        scl_int <= '1';
                        sda_int <= '0';          -- now pull SDA down
                        state   <= ST_ST3;

                    when ST_ST3 =>
                        if sda_i = '0' then
                            sda_drv <= '1';
                        end if;
                        sda_int <= '1';
                        state   <= ST_ST4;

                    when ST_ST4 =>
                        st_done <= '1';
                        -- Always clock the bus free at power-up, before any
                        -- transaction. A slave left wedged by a previous session
                        -- holds SDA low, and the 128-probe scan starts too soon
                        -- for the idle-timeout detector to ever catch it - the
                        -- scan would just read 128 false acknowledges.
                        rec_cnt <= 0;
                        state   <= ST_RECOVER;

                    when ST_IDLE =>
                        sda_int <= '1';
                        scl_int <= '1';
                        phase   <= 0;

                        -- Driving neither line, so with pull-ups both must read
                        -- high. Anything else means the bus is being held down.
                        if sda_int = '1' and scl_int = '1' then
                            -- Self-clearing rather than sticky: a latched flag
                            -- from a power-up transient looks identical to a
                            -- genuinely jammed bus, which is actively misleading.
                            -- Report what the bus is doing NOW.
                            if sda_i = '0' then
                                if sda_low_cnt = STUCK_PERSIST then
                                    sda_low <= '1';
                                else
                                    sda_low_cnt <= sda_low_cnt + 1;
                                end if;
                            else
                                sda_low_cnt <= 0;
                                sda_low     <= '0';   -- recovered
                            end if;

                            if scl_i = '0' then
                                if scl_low_cnt = STUCK_PERSIST then
                                    scl_low <= '1';
                                else
                                    scl_low_cnt <= scl_low_cnt + 1;
                                end if;
                            else
                                scl_low_cnt <= 0;
                                scl_low     <= '0';
                            end if;

                            stuck_flag <= scl_low or sda_low;
                        end if;

                        if (sda_i = '0' or scl_i = '0') and rec_tries < 15 then
                            -- Test the wire RIGHT NOW rather than the debounced
                            -- flag. We are about to issue a START, which is only
                            -- meaningful from a genuinely idle bus. sda_low needs
                            -- STUCK_PERSIST consecutive idle samples, and
                            -- back-to-back transactions - the 128 address probes
                            -- above all - never leave that much idle time. A
                            -- wedged slave therefore sailed straight through and
                            -- every probe read as a false acknowledge.
                            rec_cnt     <= 0;
                            rec_tries   <= rec_tries + 1;
                            recovered_i <= '1';
                            state       <= ST_RECOVER;

                        elsif ena_latched = '1' then
                            ena_latched <= '0';   -- consume the request
                            busy      <= '1';
                            nack_flag <= '0';
                            is_read   <= rd_mode;
                            is_probe  <= probe_mode;
                            anack     <= '0';
                            -- Invalidate the read register up front. data_rd is
                            -- only written at ST_NACK_DATA, so an aborted read
                            -- would otherwise report the PREVIOUS transaction's
                            -- byte as if it were fresh - which is how a stale
                            -- 0x05 value got reported as register 0x09.
                            if rd_mode = '1' then
                                data_rd <= (others => '1');
                            end if;
                            -- First byte is always a WRITE: the register pointer
                            -- must be sent before any read can happen.
                            tx_shift  <= addr & '0';
                            state     <= ST_START;
                        else
                            busy <= '0';
                        end if;

                    when ST_RECOVER =>
                        sda_int <= '1';           -- released throughout
                        if phase = 1 then
                            scl_int <= '1';
                        elsif phase = 3 then
                            scl_int <= '0';
                            if rec_cnt = 9 then
                                state <= ST_STOP; -- finish with a real STOP
                            else
                                rec_cnt <= rec_cnt + 1;
                            end if;
                        end if;

                    when ST_START =>
                        -- START: SDA falls while SCL is high.
                        -- Standard mode (100 kHz) needs tHD;STA >= 4.0 us before
                        -- SCL may fall. One quarter bit is only 2.5 us, so hold
                        -- through phase 2 and drop SCL at phase 3 instead: that
                        -- gives 5 us. (At the old 400 kHz setting a single
                        -- quarter bit was 0.625 us against a 0.6 us minimum,
                        -- which is why this only became a violation when the bus
                        -- was slowed down.)
                        if phase = 0 then
                            sda_int <= '1';
                            scl_int <= '1';
                        elsif phase = 1 then
                            sda_int <= '0';
                        elsif phase = 2 then
                            null;                 -- hold tHD;STA
                        elsif phase = 3 then
                            scl_int <= '0';
                            bit_cnt <= 7;
                            state   <= ST_WR_ADDR;
                        end if;

                    when ST_WR_ADDR =>
                        if phase = 0 then
                            sda_int <= tx_shift(bit_cnt);
                        elsif phase = 1 then
                            scl_int <= '1';       -- high through phases 2 and 3
                        elsif phase = 3 then
                            scl_int <= '0';
                            if bit_cnt = 0 then
                                state <= ST_ACK_ADDR;
                            else
                                bit_cnt <= bit_cnt - 1;
                            end if;
                        end if;

                    when ST_ACK_ADDR =>
                        if phase = 0 then
                            sda_int <= '1';
                        elsif phase = 1 then
                            scl_int <= '1';
                        elsif phase = 2 then
                            if sda_i /= '0' then  -- SCL is high here
                                nack_flag <= '1';
                                anack     <= '1';
                            end if;
                        elsif phase = 3 then
                            scl_int <= '0';
                            if is_probe = '1' then
                                state <= ST_STOP;     -- scan: nothing more to do
                            else
                                tx_shift <= reg_addr;
                                bit_cnt  <= 7;
                                state    <= ST_WR_REG;
                            end if;
                        end if;

                    when ST_WR_REG =>
                        if phase = 0 then
                            sda_int <= tx_shift(bit_cnt);
                        elsif phase = 1 then
                            scl_int <= '1';       -- high through phases 2 and 3
                        elsif phase = 3 then
                            scl_int <= '0';
                            if bit_cnt = 0 then
                                state <= ST_ACK_REG;
                            else
                                bit_cnt <= bit_cnt - 1;
                            end if;
                        end if;

                    when ST_ACK_REG =>
                        if phase = 0 then
                            sda_int <= '1';
                        elsif phase = 1 then
                            scl_int <= '1';
                        elsif phase = 2 then
                            if sda_i /= '0' then  -- SCL is high here
                                nack_flag <= '1';
                            end if;
                        elsif phase = 3 then
                            scl_int <= '0';
                            if is_read = '1' then
                                state <= ST_RESTART;
                            else
                                tx_shift <= data_wr;
                                bit_cnt  <= 7;
                                state    <= ST_WR_DATA;
                            end if;
                        end if;

                    -- ---------------- write path ----------------
                    when ST_WR_DATA =>
                        if phase = 0 then
                            sda_int <= tx_shift(bit_cnt);
                        elsif phase = 1 then
                            scl_int <= '1';       -- high through phases 2 and 3
                        elsif phase = 3 then
                            scl_int <= '0';
                            if bit_cnt = 0 then
                                state <= ST_ACK_DATA;
                            else
                                bit_cnt <= bit_cnt - 1;
                            end if;
                        end if;

                    when ST_ACK_DATA =>
                        if phase = 0 then
                            sda_int <= '1';
                        elsif phase = 1 then
                            scl_int <= '1';
                        elsif phase = 2 then
                            if sda_i /= '0' then  -- SCL is high here
                                nack_flag <= '1';
                            end if;
                        elsif phase = 3 then
                            scl_int <= '0';
                            state <= ST_STOP;
                        end if;

                    -- ---------------- read path ----------------
                    when ST_RESTART =>
                        -- Repeated START. tSU;STA >= 4.7 us from SCL rising to
                        -- SDA falling, so raise SCL at phase 0 and drop SDA at
                        -- phase 2: 5 us.
                        if phase = 0 then
                            sda_int <= '1';
                            scl_int <= '1';
                        elsif phase = 1 then
                            null;                 -- hold tSU;STA
                        elsif phase = 2 then
                            sda_int <= '0';
                        elsif phase = 3 then
                            scl_int  <= '0';
                            tx_shift <= addr & '1';   -- same device, READ
                            bit_cnt  <= 7;
                            state    <= ST_WR_ADDR_R;
                        end if;

                    when ST_WR_ADDR_R =>
                        if phase = 0 then
                            sda_int <= tx_shift(bit_cnt);
                        elsif phase = 1 then
                            scl_int <= '1';       -- high through phases 2 and 3
                        elsif phase = 3 then
                            scl_int <= '0';
                            if bit_cnt = 0 then
                                state <= ST_ACK_ADDR_R;
                            else
                                bit_cnt <= bit_cnt - 1;
                            end if;
                        end if;

                    when ST_ACK_ADDR_R =>
                        if phase = 0 then
                            sda_int <= '1';
                        elsif phase = 1 then
                            scl_int <= '1';
                        elsif phase = 2 then
                            if sda_i /= '0' then  -- SCL is high here
                                nack_flag <= '1';
                            end if;
                        elsif phase = 3 then
                            scl_int <= '0';
                            bit_cnt <= 7;
                            state   <= ST_RD_DATA;
                        end if;

                    when ST_RD_DATA =>
                        -- SDA stays released; the slave drives it.
                        if phase = 0 then
                            sda_int <= '1';
                        elsif phase = 1 then
                            scl_int <= '1';
                        elsif phase = 2 then
                            if sda_i = '0' then   -- SCL is high here
                                rx_shift(bit_cnt) <= '0';
                            else
                                rx_shift(bit_cnt) <= '1';
                            end if;
                        elsif phase = 3 then
                            scl_int <= '0';
                            if bit_cnt = 0 then
                                state <= ST_NACK_DATA;
                            else
                                bit_cnt <= bit_cnt - 1;
                            end if;
                        end if;

                    when ST_NACK_DATA =>
                        -- Only one byte wanted, so NACK it: leave SDA high.
                        if phase = 0 then
                            sda_int <= '1';
                        elsif phase = 1 then
                            scl_int <= '1';
                        elsif phase = 3 then
                            scl_int <= '0';
                            data_rd <= rx_shift;
                            state   <= ST_STOP;
                        end if;

                    when ST_STOP =>
                        -- STOP: SDA rises while SCL is high. tSU;STO >= 4.0 us in
                        -- standard mode, so hold SCL high through phase 2 and
                        -- release SDA at phase 3 for 5 us of setup.
                        if phase = 0 then
                            sda_int <= '0';
                        elsif phase = 1 then
                            scl_int <= '1';
                        elsif phase = 2 then
                            null;                 -- hold tSU;STO
                        elsif phase = 3 then
                            sda_int <= '1';
                            busy    <= '0';
                            state   <= ST_IDLE;
                        end if;

                    when others =>
                        state <= ST_IDLE;

                end case;
            end if;
        end if;
    end process;

end architecture rtl;
