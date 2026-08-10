library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity adau1978_sequencer is
    generic (
        -- 50 MHz clock = 20 ns period. 
        -- Datasheet requires ~10 ms after DVDD > 1.2V and stable clocks for PLL lock.
        -- We wait 40 ms just to be absolutely safe (2,000,000 clock cycles).
        BOOT_DELAY_CYCLES : integer := 2000000 
    );
    port (
        clk         : in  std_logic;
        rst_n       : in  std_logic;
        
        -- Status Output
        boot_done   : out std_logic;

        -- ==========================================
        -- UDP / Runtime Interface (From Ethernet RX)
        -- ==========================================
        udp_req     : in  std_logic;
        udp_ack     : out std_logic;
        udp_adc_sel : in  std_logic_vector(1 downto 0); -- 00=ADC1, 01=ADC2, 10=ADC3, 11=ADC4
        udp_ch_sel  : in  std_logic_vector(1 downto 0); -- 00=Ch1, 01=Ch2, 10=Ch3, 11=Ch4
        udp_gain    : in  std_logic_vector(7 downto 0); -- 0x00 (+60dB) to 0xFF (Mute)

        -- ==========================================
        -- I2C Master Interface
        -- ==========================================
        i2c_ena      : out std_logic;
        i2c_addr     : out std_logic_vector(6 downto 0);
        i2c_reg_addr : out std_logic_vector(7 downto 0);
        i2c_data_wr  : out std_logic_vector(7 downto 0);
        i2c_busy     : in  std_logic;
        i2c_ack_error : in  std_logic;
        i2c_rd_mode  : out std_logic;
        i2c_probe    : out std_logic;
        i2c_addr_nack : in  std_logic;
        i2c_data_rd  : in  std_logic_vector(7 downto 0);

        -- Latches high if ANY boot write went unacknowledged, i.e. no ADAU1978
        -- answered on the bus. Sticky until reset.
        i2c_fault    : out std_logic;

        -- Post-boot readback of ADC 0, so we can see what actually took effect
        -- instead of assuming. Valid once boot_done is high.
        adc_pll_lock : out std_logic;  -- PLL_CONTROL bit 7 read back from 0x01
        adc_cfg_ok   : out std_logic;  -- SAI_CTRL0 (0x05) read back == written

        -- Raw readback bytes, published in the UDP header so the actual
        -- register contents are visible instead of a pass/fail bit.
        dbg_rd_pll   : out std_logic_vector(7 downto 0);  -- 0x01 PLL_CONTROL
        dbg_rd_sai   : out std_logic_vector(7 downto 0);  -- 0x05 SAI_CTRL0

        -- Results of the power-on bus scan across all 128 addresses
        dbg_scan_cnt  : out std_logic_vector(7 downto 0); -- how many answered
        dbg_scan_addr : out std_logic_vector(7 downto 0); -- first one that did
        dbg_scan_mask : out std_logic_vector(7 downto 0);
        dbg_ot        : out std_logic_vector(7 downto 0);
        dbg_health    : out std_logic_vector(7 downto 0); -- which of 11/31/51/71
        dbg_vfy_mask  : out std_logic_vector(7 downto 0)  -- which regs verified
    );
end entity adau1978_sequencer;

architecture rtl of adau1978_sequencer is

    -- State Machine Definitions
    type state_type is (
        ST_RESET, 
        ST_BOOT_DELAY,
        ST_SCAN_START, ST_SCAN_WAIT_HIGH, ST_SCAN_WAIT_LOW,
        ST_BOOT_START_TX, 
        ST_BOOT_WAIT_BUSY_HIGH,
        ST_BOOT_WAIT_BUSY_LOW,
        ST_PLL_SETTLE,
        ST_VERIFY_START,
        ST_VERIFY_WAIT_HIGH,
        ST_VERIFY_WAIT_LOW,
        ST_IDLE, 
        ST_RUNTIME_START_TX, 
        ST_RUNTIME_WAIT_BUSY_HIGH,
        ST_RUNTIME_WAIT_BUSY_LOW
    );
    signal state : state_type;

    -- Counters and Indices
    signal delay_cnt : integer range 0 to BOOT_DELAY_CYCLES;
    signal adc_idx   : unsigned(1 downto 0);
    signal reg_idx   : unsigned(3 downto 0);
    signal vfy_idx   : unsigned(2 downto 0);

    -- Read back the registers that decide whether SDATAOUT1 is driven at all.
    -- reg in [15:8], expected value in [7:0].
    type vfy_list_t is array (0 to 5) of std_logic_vector(15 downto 0);
    constant VFY_LIST : vfy_list_t := (
        0 => x"0001",  -- M_POWER        PWUP
        1 => x"0103",  -- PLL_CONTROL    bit7 is PLL_LOCK status, masked below
        2 => x"043F",  -- BLOCK_POWER_SAI
        3 => x"055B",  -- SAI_CTRL0
        4 => x"0608",  -- SAI_CTRL1      SLOT_WIDTH=00 32 BCLK, LR_MODE=1
        5 => x"09F8"   -- SAI_OVERTEMP   bit0 is OT status, masked below
    );
    signal vfy_mask : std_logic_vector(5 downto 0) := (others => '0');
    signal cfg_ok_i  : std_logic;
    signal boot_done_i : std_logic;
    signal scan_addr : unsigned(6 downto 0);
    signal found_cnt : unsigned(7 downto 0);
    signal first_adr : std_logic_vector(7 downto 0);
    signal scanned   : std_logic;
    -- Bound the retries. A partially populated board must still settle into a
    -- steady state instead of re-writing PLL_CONTROL on the working parts every
    -- 165 ms, which the datasheet warns can disturb a locked PLL.
    constant MAX_BOOT_TRIES : integer := 8;
    signal try_cnt : integer range 0 to MAX_BOOT_TRIES := 0;
    signal adr_mask : std_logic_vector(3 downto 0) := "0000";
    -- The scan is only believable if the bus was actually idle. A stuck-low SDA
    -- makes EVERY address acknowledge, so a large count is proof of a broken bus
    -- rather than a populated one. Four parts is all this board can have.
    signal scan_bad : std_logic := '0';

    -- Soft-reset pass. The datasheet POR section warns that if the PLL locks
    -- after the state machine has been enabled, the part can initialise with an
    -- "incorrect initialization configuration" and shows "indeterminate ADC
    -- behavior" - it answers I2C, accepts and reports back every register, locks
    -- its PLL, and does not run. That is exactly the failure on this board.
    -- S_RST (bit 7 of 0x00) "resets all internal circuitry and all control
    -- registers to their respective default states", so issuing it once with the
    -- clocks already stable, then configuring, gives the state machine a clean
    -- start. Set false to boot the old way for comparison.
    -- DIAGNOSTIC: put U19 (adc_idx 0, address 0x11) into SAI master mode, so it
    -- generates BCLK and LRCLK from its own PLL and drives SDATAOUT itself. This
    -- takes the entire external framing chain out of the loop. If SDATA activity
    -- appears, the converter and serial port work and the fault is in how we drive
    -- LRCLK/BCLK; if nothing appears, the SAI does not run on a part that is
    -- powered, referenced, PLL-locked and byte-exact configured.
    --
    -- REQUIRES R7 AND R14 LIFTED. U19 drives pins 15 and 16 as outputs; left
    -- connected it fights the FPGA and U2 at 3.3V/49.9ohm = 66 mA. Leave R13
    -- fitted - MCLK on pin 7 is still needed to run the PLL.
    --
    -- The FPGA's decode will be garbage in this mode (its LRCLK/BCLK are not
    -- synchronous to U19's). Ignore the channel table. The only meaningful
    -- number is the SDATA edge counter in udp_monitor.py.
    -- DIAGNOSTIC: force one part's four post-ADC gains to a chosen value at
    -- boot, leaving the other three at 0 dB. Used to answer "is this converter
    -- producing samples at all" without touching the board: at +60 dB (0x00) a
    -- working converter's noise floor lifts by three orders of magnitude, and a
    -- dead one does not move. Cleaner than master mode, which cannot avoid
    -- 66 mA of contention against the clock buffers through the 49.9 ohm
    -- series resistors unless those are lifted.
    --   -1 = off, 0=U19 1=U20 2=U37 3=U38
    -- Currently used as a SLOT IDENTITY tag, not a liveness probe. Two parts
    -- share each SDATA line and the decoded channel group they land in has been
    -- shown to shift by 4 slots when the LRCLK shape changed, so "ch 5-8 is
    -- U20" is an assumption, not a measurement. Raising one part's gain by a
    -- known amount labels its four channels unambiguously: whichever group
    -- moves is that part. +30 dB (0x50) rather than +60 dB (0x00) so the hotter
    -- group cannot clip and become unreadable - gain = 60 - 0.375*N.
    constant C_GAIN_PROBE_IDX  : integer range -1 to 3 := -1;
    constant C_GAIN_PROBE_BYTE : std_logic_vector(7 downto 0) := x"50";  -- +30 dB

    constant C_MASTER_TEST : boolean := false;
    -- Which part gets master mode: 0=U19 1=U20 2=U37 3=U38.
    -- U20 is the control: its PLL loop filter was reworked to return to AVDD2 as
    -- Table 8 requires, while U19/U37/U38 still return to GND. If U20 generates
    -- 96 kHz in master mode and U19 gives ~10 kHz, the loop filter is the fault.
    constant C_MASTER_IDX  : integer range 0 to 3 := 0;

    -- Delay after S_RST before the configuration writes. Deliberately SHORT.
    -- The datasheet says the PLL is enabled a fixed time after POR is released,
    -- and separately that it "be disabled, reprogrammed with the new setting, and
    -- then reenabled". Waiting the full 30 ms PLL_SETTLE here let the PLL come up
    -- on its reset default (MCS=001) first, so writing MCS=010 afterwards
    -- retuned a running PLL - which is how you get a lock that succeeds on some
    -- power-ups and not others. 1 ms is well past the 200 us DVDD charge time
    -- (tC = ROUT x CEXT) but lands the PLL settings before the PLL is running.
    constant SRST_SETTLE_CYCLES : integer := 50000;   -- 1 ms at 50 MHz

    constant C_SOFT_RESET_FIRST : boolean := true;
    constant SOFT_RESET_WORD : std_logic_vector(15 downto 0) := x"0080";
    signal srst_pass : std_logic := '1';

    -- Which ADC the post-boot register verify reads back from.
    --   0 = U19 (0x11)   1 = U20 (0x31)   2 = U37 (0x51)   3 = U38 (0x71)
    constant C_VERIFY_IDX : integer range 0 to 3 := 0;

    -- Datasheet, POWER-ON RESET SEQUENCE: "the software configuration needs to
    -- ensure that the ADAU1978 is not software-powered up until the PLL lock
    -- stabilizes... the PWUP bit can only be asserted at least 10 mS after
    -- DVDD > 1.2 V and the input clocks are stable." Table 5 gives the PLL a
    -- 10 ms maximum lock time in MCLK mode.
    --
    -- So the boot runs in two passes: everything EXCEPT PWUP is written first to
    -- all four parts, then we wait out the PLL, then PWUP is written. Asserting
    -- PWUP inside the lock window lets the state machine initialise against an
    -- unlocked PLL, which the datasheet warns gives indeterminate ADC behaviour.
    constant PLL_SETTLE_CYCLES : integer := 1500000;   -- 30 ms at 50 MHz
    signal settle_cnt : integer range 0 to PLL_SETTLE_CYCLES := 0;
    signal pwup_pass  : std_logic := '0';
    -- Re-read PLL_CONTROL every ~100 ms. A single sample taken 14 ms after
    -- configuring the PLL can easily miss a lock that arrives later.
    signal poll_cnt : integer range 0 to 25000000 := 0;
    signal poll_idx : unsigned(1 downto 0) := "00";
    signal polling  : std_logic := '0';
    -- PLL_LOCK read back from each of the four parts in rotation
    signal pll_mask : std_logic_vector(3 downto 0) := "0000";

    -- Runtime overtemperature watch. 0x09 bit 0 is OT, "1 = Overtemperature
    -- Fault", and until now it was only read once at boot - so a part that
    -- heats up, trips OT, mutes and recovers was completely invisible. That is
    -- exactly the signature of the intermittent, worsening dropouts seen on
    -- 2026-08-09, and Table 8 warns the exposed pad is the part's only thermal
    -- path: "THE EXPOSED PAD MUST BE CONNECTED TO THE GROUND PLANE".
    -- ot_now  : OT bit as last read, per part
    -- ot_ever : sticky - set once and never cleared, so a brief trip between
    --           polls is still caught
    -- Runtime poll list. Every register was previously checked once at boot and
    -- never again, so a part that silently lost its configuration - glitch,
    -- brownout, stray S_RST - went quiet with nothing to notice. This walks all
    -- four parts across six registers continuously.
    --   0x01 PLL_LOCK      read-only status
    --   0x09 OT            read-only status
    --   0x19 ASDC_CLIP     read-only status, is the converter seeing signal
    --   0x00 / 0x05 / 0x06 configuration, compared against what was written
    type poll_t is array (0 to 5) of std_logic_vector(15 downto 0);
    constant POLL_LIST : poll_t := (
        0 => x"0100",   -- PLL_CONTROL, bit 7 captured, value ignored
        1 => x"0900",   -- SAI_OVERTEMP, bit 0 captured
        2 => x"1900",   -- ASDC_CLIP, bits 3:0 captured
        3 => x"0001",   -- M_POWER      expect 0x01
        4 => x"055B",   -- SAI_CTRL0    expect as written
        5 => x"0608");  -- SAI_CTRL1    expect as written
    -- Entries 3..5 are compared against BOOT_ROM; 0..2 are read-only status and
    -- their expected byte is ignored. check_sync.py enforces that pairing, added
    -- after this list was left at 0x06 = 0x00 when BOOT_ROM moved to 0x08 - which
    -- made the runtime check report CONFIG DRIFTED on all four parts at once.
    -- A cry-wolf diagnostic is worse than none: it says the ADCs lost their
    -- configuration, which is exactly the symptom being chased.
    signal poll_reg : unsigned(2 downto 0) := "000";
    signal clip_ever : std_logic_vector(3 downto 0) := "0000";
    signal cfg_bad   : std_logic_vector(3 downto 0) := "0000";
    -- Sticky "this part's PLL has been unlocked at some point since boot".
    -- The instantaneous pll_mask is useless for catching brief events: with six
    -- registers in the poll list, any one part's 0x01 is only re-read every
    -- ~12 s, so a 250 ms unlock falls between samples. OT and config drift are
    -- already sticky; this makes lock loss sticky too.
    signal pll_lost  : std_logic_vector(3 downto 0) := "0000";
    signal poll_ot  : std_logic := '0';        -- retained, unused
    signal ot_now   : std_logic_vector(3 downto 0) := "0000";
    signal ot_ever  : std_logic_vector(3 downto 0) := "0000";

    constant LAST_REG : unsigned(3 downto 0) := to_unsigned(11, 4);

    -- ==========================================
    -- Boot Sequence ROM (Register Address, Data)
    --
    -- Clocking, per the ADAU1978 datasheet (Rev. B):
    --   BCLK  = 18.432 MHz = 192 x 96 kHz, which Table 10 gives as TDM8 with
    --           24 BCLKs per slot. Exactly what tdm8_master generates.
    --   MCLK  = 18.432 MHz, tied to the same net as BCLK. At fs = 96 kHz that
    --           is 192 x fS. Table 9 lists the MCS ratios PER SAMPLE RATE, and
    --           they are not the same above 48 kHz: at 96 kHz the options are
    --           64/128/192/256/384 x fS, so 192 x fS is MCS = 010. The PLL runs
    --           from MCLKIN (CLK_S = 0), which is also what the fitted loop
    --           filter expects - R118 1k / C119 5.6nF is the MCLK-mode network
    --           from Figure 15 (LRCLK mode would want 4.87k / 39nF / 2.2nF).
    --
    -- Slot sharing: two ADAU1978s sit on each SDATA line. They must occupy
    -- different TDM slots AND tri-state outside them, otherwise both parts
    -- drive the bus at once. Register 0x09 bit 3 (DRV_HIZ) defaults to 0,
    -- meaning "unused outputs driven low" - a hard conflict. See below.
    -- ==========================================
    type boot_rom_type is array (0 to 11) of std_logic_vector(15 downto 0);
    constant BOOT_ROM : boot_rom_type := (
        -- ORDER MATTERS. MCS is interpreted relative to FS, so both the PLL
        -- ratio (0x01) and the sample-rate range (0x05) must be in place BEFORE
        -- the core is powered up. Writing PWUP early makes the PLL start
        -- acquiring against FS's reset value (32-48 kHz, where MCS=010 means
        -- 384 x fS) and then moves the goalposts to 64-96 kHz underneath it.
        -- The datasheet: "the PLL be disabled, reprogrammed with the new
        -- setting, and then reenabled".
        0  => x"0103", -- 0x01 PLL_CONTROL:  CLK_S=0 MCLKIN, MCS=011 = 256 x fS,
                       -- i.e. 24.576 MHz at 96 kHz (Table 9). 256 is also what
                       -- the part assumes from its own reset defaults (MCS=001,
                       -- FS=010 -> 256 x fS), so the PLL locks on the ratio it
                       -- boots with and never has to re-acquire. 192 x fS would
                       -- change the ratio mid-configuration, which the datasheet
                       -- warns against and which left 3 of 4 PLLs unlocked.
        1  => x"055B", -- 0x05 SAI_CTRL0:    left-just, TDM8, FS=011 64-96 kHz
                       -- SDATA_FMT changed 00 (I2S) -> 01 (left justified).
                       -- I2S delays data one BCLK from the LRCLK edge, but with
                       -- SLOT_WIDTH=24 BCLK and DATA_WIDTH=24-bit the slot is
                       -- exactly full - the delay pushes the last bit outside its
                       -- slot. Left justified has no delay and is the correct
                       -- framing when slots exactly fit the data. Consistent with
                       -- the part working in master mode, where BCLKRATE=0 gives
                       -- 32-BCLK slots and the delay does fit.
                       --                    -> MCS=010 now means 192 x fS,
                       --                       i.e. 18.432 MHz at 96 kHz
        2  => x"0608", -- 0x06 SAI_CTRL1:    SDATAOUT1, 32 BCLK slots, 24-bit,
                       --                    LRCLK pulse, MSB first, slave
                       -- LR_MODE (bit 3) SET = "single BCLK cycle wide pulse"
                       -- (Table 21). 50% duty was tried instead, because an
                       -- 81 ns pulse averages 13 mV and no meter can see it
                       -- while a square averages 1.65 V. It cost channels: a
                       -- 256-BCLK frame puts the 50% falling edge at BCLK 128,
                       -- the slot 4 / slot 5 boundary, exactly where the part
                       -- owning slots 5-8 takes over the line. Both parts
                       -- holding slots 5-8 dropped out; both holding slots 1-4
                       -- did better. tdm8_master must match - C_LR_PULSE there.
        3  => x"0710", -- 0x07 SAI_CMAP12:   slots 1,2   (0x54 on the B parts)
        4  => x"0832", -- 0x08 SAI_CMAP34:   slots 3,4   (0x76 on the B parts)
        5  => x"09F8", -- 0x09 SAI_OVERTEMP: drive C1-C4, DRV_HIZ=1
        6  => x"043F", -- 0x04 BLOCK_POWER:  LDO + VREF + ADC1-4
        7  => x"0AA0", -- 0x0A POSTADC_GAIN1
                       -- DIAGNOSTIC GAIN: 0x50 = +30 dB, not the 0 dB 0xA0.
                       -- gain = 60 - 0.375*N, so N=0x50 gives +30 dB. This lifts
                       -- the converter's own noise floor ~30x above the LSBs, so
                       -- a part that is genuinely converting produces unmistakable
                       -- data. Zero activity at +30 dB means it is not converting
                       -- at all, which points at VREF or the analog supplies.
                       -- Set back to 0xA0 once audio is confirmed.
        8  => x"0BA0", -- 0x0B POSTADC_GAIN2
        9  => x"0CA0", -- 0x0C POSTADC_GAIN3
        10 => x"0DA0", -- 0x0D POSTADC_GAIN4
        11 => x"0001"  -- 0x00 M_POWER:      PWUP LAST, everything else settled
    );

    -- Slot map for the second ADC on each shared SDATA line
    constant CMAP12_SLOTS_5_6 : std_logic_vector(15 downto 0) := x"0754";
    constant CMAP34_SLOTS_7_8 : std_logic_vector(15 downto 0) := x"0876";

    -- DIAGNOSTIC: exchange which part of each pair owns the upper slots.
    --
    -- Normally adc_idx(0) = '1' takes slots 4-7, so U19 and U37 hold slots 0-3
    -- and U20/U38 hold 4-7. On both TDM lines the part holding slots 0-3 is the
    -- unreliable one and the part holding 4-7 is the good one - U19 ~30/40
    -- windows against U20 at 40/40, and the same ordering on TDM2 before its
    -- wiring fault took over. Slot 0 begins at the frame boundary, immediately
    -- after the LRCLK edge and at the instant the other part releases the line,
    -- so it has the least margin of any slot. That is a plausible reason for the
    -- ordering - but so is "U19 is simply the weaker part", and nothing measured
    -- so far separates them.
    --
    -- With this true, U19/U37 take slots 4-7 and U20/U38 take slots 0-3. The
    -- decoded channels follow the SLOTS, not the parts, so read the result as:
    --      channels 1-4  = slots 0-3 = U20 / U38
    --      channels 5-8  = slots 4-7 = U19 / U37
    --
    --   intermittency stays on channels 1-4 -> it follows the SLOT, so the frame
    --       boundary is the problem and it is ours to fix in firmware.
    --   intermittency moves to channels 5-8 -> it follows the PART, so it is U19
    --       itself or its LRCLK/BCLK wiring (R7, R14, pins 15/16) and firmware
    --       has nothing left to give.
    --
    -- Set back to false once answered.
    constant C_SWAP_SLOTS : boolean := false;   -- answered 2026-08-10: intermittency
    -- followed U19, not the slot. U20 held slots 0-3 and stayed 40/40 steady, so
    -- the frame boundary is fine and the fault is U19 or its LRCLK/BCLK wiring.

    -- Helper Function to resolve 7-bit I2C Address based on ADC index
    function get_i2c_addr(idx : unsigned(1 downto 0)) return std_logic_vector is
    begin
        case idx is
            when "00" => return "0010001"; -- 0x11
            when "01" => return "0110001"; -- 0x31
            when "10" => return "1010001"; -- 0x51
            when "11" => return "1110001"; -- 0x71
            when others => return "0000000";
        end case;
    end function;

begin

    adc_cfg_ok    <= cfg_ok_i;
    dbg_scan_cnt  <= std_logic_vector(found_cnt);
    -- upper nibble = PLL locked per part, lower nibble = answered the scan
    dbg_scan_mask <= pll_mask & adr_mask;
    -- ot_now dropped in favour of the sticky lock-loss flag: an
    -- instantaneous reading cannot catch a 250 ms event.
    dbg_ot        <= ot_ever & pll_lost;
    dbg_health    <= cfg_bad & clip_ever;
    dbg_vfy_mask  <= scan_bad & '0' & vfy_mask;
    boot_done     <= boot_done_i;
    -- Report the address the verify actually targeted, so the readback table is
    -- never mislabelled. Which parts answered is already in adr_mask.
    dbg_scan_addr <= "0" & get_i2c_addr(to_unsigned(C_VERIFY_IDX, 2));

    process(clk, rst_n)
        variable current_boot_word : std_logic_vector(15 downto 0);
    begin
        if rst_n = '0' then
            state        <= ST_RESET;
            boot_done_i  <= '0';
            i2c_fault    <= '0';
            i2c_rd_mode  <= '0';
            adc_pll_lock <= '0';
            cfg_ok_i     <= '0';
            i2c_probe    <= '0';
            scan_addr    <= (others => '0');
            found_cnt    <= (others => '0');
            first_adr    <= x"FF";
            scanned      <= '0';
            try_cnt      <= 0;
            adr_mask     <= "0000";
            scan_bad     <= '0';
            if C_SOFT_RESET_FIRST then
                srst_pass <= '1';
            else
                srst_pass <= '0';
            end if;
            settle_cnt   <= 0;
            pwup_pass    <= '0';
            poll_cnt     <= 0;
            poll_idx     <= "00";
            poll_ot      <= '0';
            poll_reg     <= "000";
            clip_ever    <= "0000";
            cfg_bad      <= "0000";
            pll_lost     <= "0000";
            ot_now       <= "0000";
            ot_ever      <= "0000";
            polling      <= '0';
            pll_mask     <= "0000";
            dbg_rd_pll   <= (others => '0');
            dbg_rd_sai   <= (others => '0');
            vfy_idx      <= (others => '0');
            udp_ack      <= '0';
            i2c_ena      <= '0';
            i2c_addr     <= (others => '0');
            i2c_reg_addr <= (others => '0');
            i2c_data_wr  <= (others => '0');
            delay_cnt    <= 0;
            adc_idx      <= (others => '0');
            reg_idx      <= (others => '0');
            
        elsif rising_edge(clk) then
            
            -- Default pulse states
            i2c_ena <= '0';
            udp_ack <= '0';

            case state is
                
                -- ==========================================
                -- BOOT SEQUENCE
                -- ==========================================
                when ST_RESET =>
                    delay_cnt <= 0;
                    adc_idx   <= "00";
                    reg_idx   <= (others => '0');
                    boot_done_i <= '0';
                    state       <= ST_BOOT_DELAY;

                when ST_BOOT_DELAY =>
                    -- Wait for DVDD to stabilize and PLL to lock
                    if delay_cnt < BOOT_DELAY_CYCLES then
                        delay_cnt <= delay_cnt + 1;
                    elsif scanned = '0' then
                        state <= ST_SCAN_START;   -- sweep the bus once, first
                    else
                        state <= ST_BOOT_START_TX;
                    end if;

                -- ==========================================
                -- BUS SCAN
                -- Address-only probes across 0x00..0x7F. This is the one test
                -- that does not assume the address is 0x11/0x31/0x51/0x71: if
                -- anything at all is alive on the bus, it answers here.
                -- ==========================================
                when ST_SCAN_START =>
                    i2c_addr    <= std_logic_vector(scan_addr);
                    i2c_probe   <= '1';
                    i2c_rd_mode <= '0';
                    i2c_ena     <= '1';
                    state       <= ST_SCAN_WAIT_HIGH;

                when ST_SCAN_WAIT_HIGH =>
                    if i2c_busy = '1' then
                        state <= ST_SCAN_WAIT_LOW;
                    end if;

                when ST_SCAN_WAIT_LOW =>
                    if i2c_busy = '0' then
                        if i2c_addr_nack = '0' then
                            found_cnt <= found_cnt + 1;
                            case std_logic_vector(scan_addr) is
                                when "0010001" => adr_mask(0) <= '1';  -- 0x11 U19
                                when "0110001" => adr_mask(1) <= '1';  -- 0x31 U20
                                when "1010001" => adr_mask(2) <= '1';  -- 0x51 U37
                                when "1110001" => adr_mask(3) <= '1';  -- 0x71 U38
                                when others    => null;
                            end case;
                            if first_adr = x"FF" then
                                first_adr <= "0" & std_logic_vector(scan_addr);
                            end if;
                            -- >= 4 before the increment means this answer is the
                            -- fifth, and only four parts can exist. Tested here
                            -- rather than outside: found_cnt is registered, so a
                            -- test after the branch trails by one probe.
                            if found_cnt >= 4 then
                                scan_bad <= '1';
                            end if;
                        end if;
                        -- Always sweep all 128 now. Aborting early collapsed every
                        -- failure onto one number: a hard stuck-low SDA (128
                        -- answers) looked identical to a few glitched bits (9), and
                        -- those are different faults. 28 ms buys the distinction.
                        if scan_addr = 127 then
                            i2c_probe <= '0';
                            scanned   <= '1';
                            state     <= ST_BOOT_START_TX;
                        else
                            scan_addr <= scan_addr + 1;
                            state     <= ST_SCAN_START;
                        end if;
                    end if;

                when ST_BOOT_START_TX =>
                    -- Fetch configuration from ROM and start I2C transaction
                    current_boot_word := BOOT_ROM(to_integer(reg_idx));
                    if srst_pass = '1' then
                        current_boot_word := SOFT_RESET_WORD;   -- 0x00 <= 0x80
                    elsif pwup_pass = '1' then
                        current_boot_word := BOOT_ROM(to_integer(LAST_REG));
                    end if;

                    -- The address straps pair the parts up as
                    --   adc_idx 00 = 0x11 U19 (TDM1 A)   01 = 0x31 U20 (TDM1 B)
                    --   adc_idx 10 = 0x51 U37 (TDM2 A)   11 = 0x71 U38 (TDM2 B)
                    -- so bit 0 selects which half of the shared line this part
                    -- owns. The A part keeps slots 1-4 from the ROM; the B part
                    -- is moved up to slots 5-8.
                    -- master-mode diagnostic: force SAI_MS on U19 only
                    if C_MASTER_TEST
                       and adc_idx = to_unsigned(C_MASTER_IDX, 2)
                       and current_boot_word(15 downto 8) = x"06" then
                        current_boot_word(0) := '1';
                    end if;

                    -- gain probe: override 0x0A-0x0D on one part only
                    if C_GAIN_PROBE_IDX >= 0
                       and adc_idx = to_unsigned(C_GAIN_PROBE_IDX, 2)
                       and (current_boot_word(15 downto 8) = x"0A"
                         or current_boot_word(15 downto 8) = x"0B"
                         or current_boot_word(15 downto 8) = x"0C"
                         or current_boot_word(15 downto 8) = x"0D") then
                        current_boot_word := current_boot_word(15 downto 8)
                                           & C_GAIN_PROBE_BYTE;
                    end if;

                    -- C_SWAP_SLOTS inverts which of the pair takes slots 4-7.
                    if (adc_idx(0) = '1') /= C_SWAP_SLOTS then
                        -- keyed on the register address so ROM order can change
                        if current_boot_word(15 downto 8) = x"07" then
                            current_boot_word := CMAP12_SLOTS_5_6;
                        elsif current_boot_word(15 downto 8) = x"08" then
                            current_boot_word := CMAP34_SLOTS_7_8;
                        end if;
                    end if;

                    i2c_addr     <= get_i2c_addr(adc_idx);
                    i2c_reg_addr <= current_boot_word(15 downto 8);
                    i2c_data_wr  <= current_boot_word(7 downto 0);
                    
                    i2c_ena <= '1'; -- Trigger I2C Master
                    state   <= ST_BOOT_WAIT_BUSY_HIGH;

                when ST_BOOT_WAIT_BUSY_HIGH =>
                    -- Wait for I2C master to acknowledge the trigger
                    if i2c_busy = '1' then
                        state <= ST_BOOT_WAIT_BUSY_LOW;
                    end if;

                when ST_BOOT_WAIT_BUSY_LOW =>
                    -- Wait for I2C transaction to complete
                    if i2c_busy = '0' then
                        -- Record whether anything actually answered
                        if i2c_ack_error = '1' then
                            i2c_fault <= '1';
                        end if;

                        -- Pass 1 writes ROM entries 0..LAST_REG-1 (all the
                        -- configuration). Pass 2 writes only LAST_REG, which is
                        -- PWUP, and runs after the PLL has been given time to lock.
                        if srst_pass = '1' or pwup_pass = '1'
                           or reg_idx = LAST_REG - 1 then
                            reg_idx <= (others => '0');
                            if adc_idx = 3 then
                                adc_idx <= (others => '0');
                                -- Settle after BOTH passes: once to let the
                                -- PLLs lock before PWUP, once after PWUP before
                                -- PLL_LOCK is read back.
                                settle_cnt <= 0;
                                state      <= ST_PLL_SETTLE;
                            else
                                adc_idx <= adc_idx + 1;
                                state   <= ST_BOOT_START_TX;
                            end if;
                        else
                            reg_idx <= reg_idx + 1;
                            state   <= ST_BOOT_START_TX;
                        end if;
                    end if;

                when ST_PLL_SETTLE =>
                    -- Used twice. Before PWUP, so the parts are configured while
                    -- quiet. After PWUP, because M_POWER is what actually enables
                    -- the PLL ("enabling the boost regulator, microphone bias,
                    -- PLL, band gap reference, ADC, and LDO regulator") and
                    -- Table 5 allows it 10 ms to lock. Reading PLL_LOCK sooner
                    -- than that samples inside the acquisition window and reports
                    -- a meaningless 0.
                    if (srst_pass = '1' and settle_cnt < SRST_SETTLE_CYCLES)
                       or (srst_pass = '0' and settle_cnt < PLL_SETTLE_CYCLES) then
                        settle_cnt <= settle_cnt + 1;
                    elsif srst_pass = '1' then
                        -- soft reset done, now configure from a known state
                        srst_pass <= '0';
                        reg_idx   <= (others => '0');
                        adc_idx   <= (others => '0');
                        state     <= ST_BOOT_START_TX;
                    elsif pwup_pass = '0' then
                        pwup_pass <= '1';
                        reg_idx   <= LAST_REG;    -- pass 2: PWUP only
                        adc_idx   <= (others => '0');
                        state     <= ST_BOOT_START_TX;
                    else
                        vfy_idx <= "000";
                        state   <= ST_VERIFY_START;
                    end if;

                -- ==========================================
                -- POST-BOOT VERIFY
                -- Read two registers back from ADC 0 (0x11). This is the only
                -- way to distinguish "the writes landed and the part still will
                -- not run" from "the writes never took effect at all".
                -- ==========================================
                when ST_VERIFY_START =>
                    -- Target whichever part replied to the scan. Hardcoding 0x11
                    -- would loop forever if U19 is the dead one while the other
                    -- three are perfectly usable.
                    if polling = '1' then
                        i2c_addr <= get_i2c_addr(poll_idx);
                    else
                        -- C_VERIFY_IDX selects WHICH part gets read back. The
                        -- verify phase can only interrogate one part per boot, and
                        -- it used to always take first_adr (the lowest answering
                        -- address, i.e. U19). That left U20/U37/U38 configured but
                        -- never confirmed - so a write that failed on one of them
                        -- was invisible. Build once per index to check all four.
                        i2c_addr <= get_i2c_addr(
                            to_unsigned(C_VERIFY_IDX, 2));
                    end if;
                    i2c_rd_mode <= '1';
                    if polling = '1' then
                        i2c_reg_addr <= POLL_LIST(to_integer(poll_reg))(15 downto 8);
                    else
                        i2c_reg_addr <= VFY_LIST(to_integer(vfy_idx))(15 downto 8);
                    end if;
                    i2c_ena <= '1';
                    state   <= ST_VERIFY_WAIT_HIGH;

                when ST_VERIFY_WAIT_HIGH =>
                    if i2c_busy = '1' then
                        state <= ST_VERIFY_WAIT_LOW;
                    end if;

                when ST_VERIFY_WAIT_LOW =>
                    if i2c_busy = '0' then
                        if i2c_ack_error = '1' then
                            i2c_fault <= '1';
                        end if;
                        if polling = '1' then
                            -- Live poll: record this part's PLL_LOCK bit
                            -- 0xFF and 0x00 are the invalid-read sentinels:
                            -- i2c_master pre-loads data_rd with 0xFF so an
                            -- aborted read cannot report stale data. Taking
                            -- bit 7 of 0xFF blindly reports PLL_LOCK = 1, i.e.
                            -- a failed read looks like a locked PLL. The boot
                            -- verify path already guarded against this; this
                            -- poll did not, and reported four locked PLLs on a
                            -- board whose MCLK never reached the parts.
                            if i2c_addr_nack = '0'
                               and i2c_data_rd /= x"FF"
                               and i2c_data_rd /= x"00" then
                                case to_integer(poll_reg) is
                                    when 0 =>          -- 0x01 PLL_LOCK
                                        pll_mask(to_integer(poll_idx)) <= i2c_data_rd(7);
                                        if i2c_data_rd(7) = '0' and boot_done_i = '1' then
                                            pll_lost(to_integer(poll_idx)) <= '1';
                                        end if;
                                    when 1 =>          -- 0x09 OT
                                        ot_now(to_integer(poll_idx)) <= i2c_data_rd(0);
                                        if i2c_data_rd(0) = '1' then
                                            ot_ever(to_integer(poll_idx)) <= '1';
                                        end if;
                                    when 2 =>          -- 0x19 ASDC_CLIP
                                        if i2c_data_rd(3 downto 0) /= "0000" then
                                            clip_ever(to_integer(poll_idx)) <= '1';
                                        end if;
                                    when others =>     -- configuration readback
                                        if i2c_data_rd
                                           /= POLL_LIST(to_integer(poll_reg))(7 downto 0) then
                                            cfg_bad(to_integer(poll_idx)) <= '1';
                                        end if;
                                end case;
                            elsif poll_reg = 0 then
                                pll_mask(to_integer(poll_idx)) <= '0';
                            end if;
                            -- walk all four parts, then advance the register
                            if poll_idx = 3 then
                                if poll_reg = 5 then
                                    poll_reg <= "000";
                                else
                                    poll_reg <= poll_reg + 1;
                                end if;
                            end if;
                            poll_idx    <= poll_idx + 1;
                            polling     <= '0';
                            i2c_rd_mode <= '0';
                            state       <= ST_IDLE;
                        else
                            -- Boot verify: walk the whole list, masking the two
                            -- read-only status bits that will never match.
                            if i2c_addr_nack = '0' then
                                if vfy_idx = 1 then      -- 0x01, ignore PLL_LOCK
                                    if (i2c_data_rd and x"7F")
                                       = (VFY_LIST(1)(7 downto 0) and x"7F") then
                                        vfy_mask(1) <= '1';
                                    end if;
                                elsif vfy_idx = 5 then   -- 0x09, ignore OT
                                    if (i2c_data_rd and x"FE")
                                       = (VFY_LIST(5)(7 downto 0) and x"FE") then
                                        vfy_mask(5) <= '1';
                                    end if;
                                elsif i2c_data_rd = VFY_LIST(to_integer(vfy_idx))(7 downto 0) then
                                    vfy_mask(to_integer(vfy_idx)) <= '1';
                                end if;
                            end if;

                            if vfy_idx = 5 then
                                -- publish 0x09 RAW so bit 0 (OT, overtemperature
                                -- shutdown) is visible. 0x05 is already covered by
                                -- the verify mask, so this byte is better spent here.
                                dbg_rd_sai <= i2c_data_rd;
                            end if;
                            if vfy_idx = 3 then
                                if i2c_data_rd = x"5A" then
                                    cfg_ok_i <= '1';
                                end if;
                            elsif vfy_idx = 1 then
                                dbg_rd_pll <= i2c_data_rd;
                                if i2c_data_rd /= x"00" and i2c_data_rd /= x"FF" then
                                    adc_pll_lock <= i2c_data_rd(7);
                                else
                                    adc_pll_lock <= '0';
                                end if;
                            end if;

                            if vfy_idx = 5 then
                                i2c_rd_mode <= '0';
                                if cfg_ok_i = '1' or try_cnt = MAX_BOOT_TRIES then
                                    boot_done_i <= '1';
                                    state       <= ST_IDLE;
                                else
                                    try_cnt <= try_cnt + 1;
                                    state   <= ST_RESET;
                                end if;
                            else
                                vfy_idx <= vfy_idx + 1;
                                state   <= ST_VERIFY_START;
                            end if;
                        end if;
                    end if;

                -- ==========================================
                -- RUNTIME OPERATION
                -- ==========================================
                when ST_IDLE =>
                    -- Wait for a request from the Ethernet UDP Core
                    if udp_req = '1' then
                        state <= ST_RUNTIME_START_TX;
                    -- Re-read PLL_LOCK from each part every 500 ms. Enabled
                    -- 2026-08-07: VREF was observed reaching 1.5 V and then
                    -- collapsing later, so a boot-time-only snapshot cannot see
                    -- the fault. This makes the PLL column in i2c_scan.py live.
                    elsif boot_done_i = '1' then
                        -- Otherwise keep PLL_LOCK fresh
                        if poll_cnt = 25000000 then     -- ~500 ms, gentler on the bus
                            poll_cnt <= 0;
                            polling  <= '1';            -- rotate through all 4
                            vfy_idx  <= "001";          -- read 0x01 only
                            state    <= ST_VERIFY_START;
                        else
                            poll_cnt <= poll_cnt + 1;
                        end if;
                    end if;

                when ST_RUNTIME_START_TX =>
                    -- Map the requested target to the I2C transaction
                    i2c_addr    <= get_i2c_addr(unsigned(udp_adc_sel));
                    i2c_data_wr <= udp_gain;
                    
                    -- Channel registers map sequentially from 0x0A to 0x0D
                    case udp_ch_sel is
                        when "00"   => i2c_reg_addr <= x"0A";
                        when "01"   => i2c_reg_addr <= x"0B";
                        when "10"   => i2c_reg_addr <= x"0C";
                        when "11"   => i2c_reg_addr <= x"0D";
                        when others => i2c_reg_addr <= x"0A";
                    end case;

                    i2c_ena <= '1'; -- Trigger I2C Master
                    state   <= ST_RUNTIME_WAIT_BUSY_HIGH;

                when ST_RUNTIME_WAIT_BUSY_HIGH =>
                    if i2c_busy = '1' then
                        state <= ST_RUNTIME_WAIT_BUSY_LOW;
                    end if;

                when ST_RUNTIME_WAIT_BUSY_LOW =>
                    if i2c_busy = '0' then
                        udp_ack <= '1'; -- Signal to UDP core that gain is applied
                        state   <= ST_IDLE;
                    end if;

                when others =>
                    state <= ST_RESET;
                    
            end case;
        end if;
    end process;

end architecture rtl;