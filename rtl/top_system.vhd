library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.net_pkg.all;

entity top_system is
    port (
        -- Board Hardware
        clk_50m_board : in  std_logic;

        -- Shared ~PD/~RST of all four ADAU1978s (U19/U20/U37/U38), FPGA pin 128.
        -- Active low, and driven by us: the net has no pull-up, so if this is
        -- left as an input the ADCs float in an undefined power-down state.
        adc_rst_n     : out std_logic;

        test_led      : out std_logic; -- Heartbeat LED
        
        -- NEW: Packet Debug LEDs
        debug_led_rx  : out std_logic; -- Flashes on incoming PHY data
        debug_led_tx  : out std_logic; -- Flashes on outgoing MAC data

        -- Power Enable Signals
        en_15v        : out std_logic;
        en_48v        : out std_logic;

        -- I2C Interface (Pins 76 & 84)
        i2c_scl       : inout std_logic;
        i2c_sda       : inout std_logic;

        -- ADAU1978 ADC Interface
        bclk_out      : out std_logic;
        lrclk_out     : out std_logic;
        sdata_in_A    : in  std_logic;
        sdata_in_B    : in  std_logic;

        -- LAN8720A RMII Interface
        phy_rst_n     : out std_logic;
        rmii_ref_clk  : in  std_logic;
        rmii_tx_en    : out std_logic;
        rmii_txd      : out std_logic_vector(1 downto 0);
        rmii_crs_dv   : in  std_logic;
        rmii_rxd      : in  std_logic_vector(1 downto 0);
        
        -- LAN8720A SMI (MDIO/MDC)
        eth_mdc       : out std_logic;
        eth_mdio      : inout std_logic;
        
        -- Miscellaneous PCB Signals
        buffer_state  : out std_logic
    );
end entity top_system;

architecture rtl of top_system is

    -- ==========================================
    -- COMPONENT DECLARATIONS
    -- ==========================================
    
    component pll_audio is
        port (
            areset : in  std_logic;
            inclk0 : in  std_logic;
            c0     : out std_logic;
            c1     : out std_logic;
            c2     : out std_logic;
            -- c3: 24.576 MHz like c2 but PHASE SHIFTED, used only to re-time
            -- lrclk_out at the pad. See C_LRCLK_PHASE_PS below and
            -- docs/LRCLK_PHASE_SHIFT.md. Must be added in the MegaWizard - the
            -- generated pll_audio.vhd currently has clk0/clk1/clk2 generics only.
            c3     : out std_logic;
            locked : out std_logic
        );
    end component;

    component tdm8_master is
        port (
            rst        : in  std_logic;
            clk_in     : in  std_logic;
            bclk_out   : out std_logic;
            lrclk_out  : out std_logic
        );
    end component;

    component tdm8_rx is
        port (
            rst         : in  std_logic;
            bclk_in     : in  std_logic;
            lrclk_in    : in  std_logic;
            sdata_in    : in  std_logic;
            ch_data_out : out std_logic_vector(191 downto 0)
        );
    end component;

    -- Single-line TDM16 receiver. Instantiated in place of the two tdm8_rx
    -- instances; tdm8_rx stays declared and in the project so reverting to the
    -- two-line TDM8 build is one instantiation swap away.
    component tdm16_rx is
        port (
            rst         : in  std_logic;
            bclk_in     : in  std_logic;
            lrclk_in    : in  std_logic;
            sdata_in    : in  std_logic;
            ch_data_A   : out std_logic_vector(191 downto 0);
            ch_data_B   : out std_logic_vector(191 downto 0)
        );
    end component;

    component tdm16_merge is
        port (
            clk         : in  std_logic;
            rst         : in  std_logic;
            lrclk_pulse : in  std_logic;
            ch_data_A   : in  std_logic_vector(191 downto 0);
            ch_data_B   : in  std_logic_vector(191 downto 0);
            tdm16_out   : out std_logic_vector(383 downto 0);
            tdm16_valid : out std_logic
        );
    end component;

    component packet_formatter is
        port (
            clk_18m      : in  std_logic;
            rst          : in  std_logic;
            tdm16_valid  : in  std_logic;
            tdm16_data   : in  std_logic_vector(383 downto 0);
            dbg_byte0    : in  std_logic_vector(7 downto 0);
            dbg_byte1    : in  std_logic_vector(7 downto 0);
            dbg_status   : in  std_logic_vector(7 downto 0);
            dbg_status2  : in  std_logic_vector(7 downto 0);
            dbg_status3  : in  std_logic_vector(7 downto 0);
            dbg_status4  : in  std_logic_vector(7 downto 0);
            dbg_status5  : in  std_logic_vector(7 downto 0);
            dbg_status6  : in  std_logic_vector(7 downto 0);
            dbg_status7  : in  std_logic_vector(7 downto 0);
            dbg_status8  : in  std_logic_vector(7 downto 0);
            fifo_wr_en   : out std_logic;
            fifo_wr_data : out std_logic_vector(7 downto 0);
            packet_ready : out std_logic
        );
    end component;

    component async_fifo is
        port (
            data    : in  std_logic_vector(7 downto 0);
            rdclk   : in  std_logic;
            rdreq   : in  std_logic;
            wrclk   : in  std_logic;
            wrreq   : in  std_logic;
            q       : out std_logic_vector(7 downto 0);
            rdempty : out std_logic;
            wrfull  : out std_logic
        );
    end component;

    component rmii_rx is
        generic (
            G_ENFORCE_FCS : boolean := false
        );
        port (
            clk_50m      : in  std_logic;
            rst          : in  std_logic;
            rmii_crs_dv  : in  std_logic;
            rmii_rxd     : in  std_logic_vector(1 downto 0);
            rx_data      : out std_logic_vector(7 downto 0);
            rx_valid     : out std_logic;
            rx_end       : out std_logic;
            rx_error     : out std_logic
        );
    end component;

    component udp_tx_core is
        port (
            clk_50m      : in  std_logic;
            rst          : in  std_logic;
            fpga_mac     : in  std_logic_vector(47 downto 0);
            fpga_ip      : in  std_logic_vector(31 downto 0);
            pc_mac       : in  std_logic_vector(47 downto 0);
            pc_ip        : in  std_logic_vector(31 downto 0);
            udp_port     : in  std_logic_vector(15 downto 0);
            packet_ready : in  std_logic;
            fifo_rd_en   : out std_logic;
            fifo_rd_data : in  std_logic_vector(7 downto 0);
            tx_start     : out std_logic;
            tx_data      : out std_logic_vector(7 downto 0);
            tx_ready     : in  std_logic
        );
    end component;

    component arp_responder is
        port (
            clk_50m      : in  std_logic;
            rst          : in  std_logic;
            fpga_mac     : in  std_logic_vector(47 downto 0);
            fpga_ip      : in  std_logic_vector(31 downto 0);
            pc_ip        : in  std_logic_vector(31 downto 0);
            learn_mac    : out std_logic_vector(47 downto 0);
            learn_valid  : out std_logic;
            rx_data      : in  std_logic_vector(7 downto 0);
            rx_valid     : in  std_logic;
            rx_end       : in  std_logic;
            rx_error     : in  std_logic;
            arp_tx_req   : out std_logic;
            arp_tx_data  : out std_logic_vector(7 downto 0);
            tx_ready     : in  std_logic
        );
    end component;

    component rmii_tx is
        port (
            clk_50m      : in  std_logic;
            rst          : in  std_logic;
            tx_start     : in  std_logic;
            tx_data      : in  std_logic_vector(7 downto 0);
            tx_ready     : out std_logic;
            tx_busy      : out std_logic;
            rmii_tx_en   : out std_logic;
            rmii_txd     : out std_logic_vector(1 downto 0)
        );
    end component;

    component i2c_master is
        generic (
            QUARTER_BIT_CYCLES : integer := 31
        );
        port (
            clk          : in  std_logic;
            rst_n        : in  std_logic;
            ena          : in  std_logic;
            addr         : in  std_logic_vector(6 downto 0);
            reg_addr     : in  std_logic_vector(7 downto 0);
            data_wr      : in  std_logic_vector(7 downto 0);
            rd_mode      : in  std_logic;
            probe_mode   : in  std_logic;
            data_rd      : out std_logic_vector(7 downto 0);
            busy         : out std_logic;
            ack_error    : out std_logic;
            addr_nack    : out std_logic;
            bus_stuck    : out std_logic;
            scl_stuck    : out std_logic;
            sda_stuck    : out std_logic;
            scl_drv_ok   : out std_logic;
            sda_drv_ok   : out std_logic;
            selftest_done: out std_logic;
            recovered    : out std_logic;
            scl_o        : out std_logic;
            sda_o        : out std_logic;
            scl_i        : in  std_logic;
            sda_i        : in  std_logic
        );
    end component;

    component adau1978_sequencer is
        generic (
            BOOT_DELAY_CYCLES : integer := 2000000 
        );
        port (
            clk          : in  std_logic;
            rst_n        : in  std_logic;
            boot_done    : out std_logic;
            udp_req      : in  std_logic;
            udp_ack      : out std_logic;
            udp_adc_sel  : in  std_logic_vector(1 downto 0);
            udp_ch_sel   : in  std_logic_vector(1 downto 0);
            udp_gain     : in  std_logic_vector(7 downto 0);
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
            i2c_fault    : out std_logic;
            adc_pll_lock : out std_logic;
            adc_cfg_ok   : out std_logic;
            dbg_rd_pll   : out std_logic_vector(7 downto 0);
            dbg_rd_sai   : out std_logic_vector(7 downto 0);
            dbg_scan_cnt  : out std_logic_vector(7 downto 0);
            dbg_scan_addr : out std_logic_vector(7 downto 0);
            dbg_scan_mask : out std_logic_vector(7 downto 0);
            dbg_ot        : out std_logic_vector(7 downto 0);
            dbg_health    : out std_logic_vector(7 downto 0);
            dbg_vfy_mask  : out std_logic_vector(7 downto 0)
        );
    end component;

    component udp_rx_core is
        port (
            clk_50m      : in  std_logic;
            rst          : in  std_logic;
            fpga_mac     : in  std_logic_vector(47 downto 0);
            fpga_ip      : in  std_logic_vector(31 downto 0);
            rx_data      : in  std_logic_vector(7 downto 0);
            rx_valid     : in  std_logic;
            rx_end       : in  std_logic;
            rx_error     : in  std_logic;
            udp_req      : out std_logic;
            udp_ack      : in  std_logic;
            udp_adc_sel  : out std_logic_vector(1 downto 0);
            udp_ch_sel   : out std_logic_vector(1 downto 0);
            udp_gain     : out std_logic_vector(7 downto 0);
            udp_flags    : out std_logic_vector(7 downto 0);
            udp_flags_wr : out std_logic
        );
    end component;


    -- ==========================================
    -- INTERNAL SIGNALS
    -- ==========================================
    
    -- Clocks & Resets
    -- pll_audio generates BOTH audio clocks exactly from 50 MHz:
    --   c0 = 768/3125  = 12.288 MHz  -> 48 kHz  (256 BCLK/frame, MCS=001)
    --   c1 = 1152/3125 = 18.432 MHz  -> 72 kHz  (256 BCLK/frame, MCS=011)
    -- NOT exact, despite what this comment said until 2026-08-10. The ALTPLL
    -- cannot realise 768/3125 - 3125 is 5^5 and gcd(768,3125)=1, so M would have
    -- to be 768 or a multiple, past the counter limit. Quartus approximates it as
    -- 73/297 = 12.289562 MHz, +127 ppm, which makes fS 48006.1 Hz and not 48000.
    -- The board measures 48010 Hz, which agrees with 48006 rather than 48000.
    -- Harmless for audio and for channel-to-channel timing, since all 16 channels
    -- come off this one clock. It matters only against an EXTERNAL time reference:
    -- 127 ppm is 127 us per second of drift, so time-of-arrival work referenced to
    -- GPS needs either the correction applied or an audio-rate oscillator instead
    -- of deriving from 50 MHz. Note check_sync validates the REQUESTED ratio, so
    -- it reports 48000 and cannot see this.
    -- MCLK and BCLK share a net on this
    -- board, so fS is fixed by whichever of these feeds the TDM logic.
    -- Switching rate is this constant plus MCS/FS in adau_sequencer.
    -- To switch rate, change WHICH PLL OUTPUT is mapped to clk_18m below:
    --   c0 -> 48 kHz    c1 -> 72 kHz
    -- Driving clk_18m from a mux instead cost dedicated PLL routing to
    -- bclk_out and its jitter guarantee, so the port map is the switch.
    -- Also update MCS (0x01) and FS (0x05) in adau_sequencer to match.
    signal clk_18m      : std_logic;
    signal pll_locked   : std_logic;
    signal sys_rst      : std_logic;
    signal sys_rst_n    : std_logic; 
    
    -- Heartbeat & Debug Counters
    signal clk_div          : unsigned(25 downto 0) := (others => '0');
    signal rx_flash_counter : integer range 0 to 25000000 := 0;
    signal tx_flash_counter : integer range 0 to 25000000 := 0;

    -- PHY Reset Delay Counter
    signal phy_rst_cnt   : unsigned(21 downto 0) := (others => '0');
    signal phy_rst_n_int : std_logic := '0';

    -- ADAU1978 Reset Release Counter
    signal adc_rst_cnt   : unsigned(26 downto 0) := (others => '0');
    signal adc_rst_n_int : std_logic := '0';

    -- Staged rail enables
    signal pwr_cnt    : unsigned(26 downto 0) := (others => '0');
    signal en_15v_int : std_logic := '0';
    signal en_48v_int : std_logic := '0';
    signal udp_flags_int : std_logic_vector(7 downto 0) := (others => '0');
    -- What actually goes out on the en_48v pin. A separate signal because an
    -- `out` port cannot be read back in VHDL-93, and the phantom readback in
    -- dbg_status2_int has to publish the driven value, not re-derive it.
    signal en_48v_drv  : std_logic := '0';
    signal en48_permit : std_logic;         -- C_ENABLE_48V as a bit

    -- Phantom watchdog. See C_PHANTOM_WATCHDOG.
    signal udp_flags_wr_int : std_logic;
    signal ph_wd_tick : unsigned(25 downto 0) := (others => '0'); -- 1 s prescaler
    signal ph_wd_secs : unsigned(7 downto 0)  := (others => '0'); -- seconds idle
    signal ph_wd_trip : std_logic := '0';
    signal ph_wd_gate : std_logic;

    -- TX Arbiter State Lock
    signal active_tx   : std_logic_vector(1 downto 0) := "00"; -- "00"=Idle, "01"=ARP, "10"=UDP

    -- ------------------------------------------------------------------
    -- LRCLK output phase, and the ONE constant that sets it.
    --
    -- The ADAU1978 samples LRCLK on the BCLK RISING edge (Table 5, tALS/tALH,
    -- slave mode). At 24.576 MHz the legal window for the LRCLK transition,
    -- measured from that edge, is
    --
    --     [ tALH , T - tALS ] = [ 5.00 , 30.69 ] ns        T = 40.690 ns
    --
    -- tdm8_master launches LRCLK on the FALLING edge of clk_18m, which is
    -- exactly T/2 = 20.345 ns - the only value a falling-edge launch can
    -- produce. That leaves 15.35 ns of hold margin and 10.34 ns of setup
    -- margin, and it is the value every image up to now has shipped.
    --
    -- Registering lrclk_int onto a PHASE SHIFTED copy of the same PLL clock
    -- puts the transition anywhere in the period instead. c3 is that copy.
    --
    -- WHICH WAY TO MOVE IT IS NOT KNOWN YET. ADC3/ADC4 drop out intermittently
    -- and the failure is at one end of the window or the other:
    --
    --   setup-limited (LRCLK arriving LATE at the part)  -> shift EARLIER, 105 deg
    --   hold-limited  (LRCLK arriving EARLY at the part) -> shift LATER,   225 deg
    --
    -- Guessing costs a bench session. docs/LRCLK_PHASE_SHIFT.md step 0 is a
    -- resistor test that determines the sign before anything is recompiled.
    --
    --   deg    ps      launch    hold margin   setup margin   C_BIT_ADJ
    --   180  20345     20.345 ns    15.35         10.34          -1   (today)
    --   105  11870     11.870 ns     7.87         18.82          -2
    --   225  25431     25.431 ns    20.43          5.26          -1
    --
    -- C_BIT_ADJ (tdm8_rx.vhd) differs between the two because of where the
    -- capture edge falls relative to lrclk_int's transition at 20.345 ns:
    --   105 deg - clk_lr rises at 11.870, BEFORE lrclk_int changes, so it
    --             carries the PREVIOUS cycle's value. One BCLK of added frame
    --             latency. C_BIT_ADJ must go -1 -> -2.
    --   225 deg - clk_lr rises at 25.431, AFTER lrclk_int changes, so it
    --             carries the SAME cycle's value. No added latency.
    --             C_BIT_ADJ stays at -1.
    --
    -- Setting this to 20345 reproduces today's timing through the new register
    -- (one BCLK later, so C_BIT_ADJ = -2) and is the control build.
    --
    -- *** THIS CONSTANT DOES NOT SET THE PHASE. ***
    -- The phase lives in the ALTPLL megafunction (ip/pll_audio), as
    -- clk3_phase_shift, and can only be changed in the MegaWizard. Editing the
    -- line below alone changes NOTHING about the built image. It exists so the
    -- intended value is recorded in the source next to the reasoning, and so a
    -- reader can tell at a glance which image they are looking at. Nothing in
    -- the toolchain enforces that the two agree - if you change one, change the
    -- other, and confirm against the fitter report as in step 5 of the doc.
    constant C_LRCLK_PHASE_PS : integer := 25431;   -- 225 deg. MIRROR OF THE PLL.

    -- ------------------------------------------------------------------
    -- ...AND THE SWITCH THAT DECIDES WHETHER ANY OF THE ABOVE IS USED.
    --
    --   false - lrclk_out comes straight from tdm8_master, launched on the
    --           FALLING edge of clk_18m at T/2 = 20.345 ns. This is what every
    --           image up to and including 96K_ACT shipped, and 96K_ACT is the
    --           build on which all 16 channels are known to work on real
    --           hardware. c3 is still generated by the PLL and simply goes
    --           unused; the LRCLK path itself is identical to ACT's.
    --   true  - lrclk_out is re-timed onto c3 at C_LRCLK_PHASE_PS.
    --
    -- SET FALSE ON PURPOSE. The phase shift was built to chase intermittent
    -- ADC3/ADC4 dropouts, and docs/LRCLK_PHASE_SHIFT.md step 0 is explicit that
    -- the SIGN of the required shift is still unknown - 105 deg and 225 deg move
    -- it opposite ways and only a bench measurement can say which is right.
    -- Meanwhile the dropouts were traced to a misplaced DVDD decoupling cap and
    -- a dead U37, both fixed in hardware, and all 16 channels now run clean.
    --
    -- So there is no longer a fault for this to fix, and turning it on would
    -- change LRCLK timing at the same moment as the phantom readback goes in -
    -- two variables in one flash, on four boards, with the known-good reference
    -- image retired. If the dropouts ever return, the work is intact: flip this
    -- to true, set the MegaWizard phase to match C_LRCLK_PHASE_PS, and follow
    -- the doc. Until then it stays out of the signal path.
    -- ------------------------------------------------------------------
    constant C_LRCLK_RETIME : boolean := false;

    -- Audio Domain (18.432 MHz)
    signal lrclk_int     : std_logic;
    signal clk_lr        : std_logic;               -- u_pll c3, phase shifted
    signal lrclk_pin_r   : std_logic := '0';        -- re-timed, drives the pad
    signal ch_data_A_int : std_logic_vector(191 downto 0);
    signal ch_data_B_int : std_logic_vector(191 downto 0);
    signal tdm16_out_int : std_logic_vector(383 downto 0);
    signal tdm16_val_int : std_logic;
    
    -- Bridge / FIFO Signals
    signal packet_ready_int : std_logic;
    signal fifo_wr_en_int   : std_logic;
    signal fifo_wr_data_int : std_logic_vector(7 downto 0);
    signal fifo_rd_en_int   : std_logic;
    signal fifo_rd_data_int : std_logic_vector(7 downto 0);
    
    -- MAC RX Bus Signals
    signal rx_data_int  : std_logic_vector(7 downto 0);
    signal rx_valid_int : std_logic;
    signal rx_end_int   : std_logic;
    signal rx_error_int : std_logic;

    -- UDP TX Core Signals
    signal udp_tx_start_int : std_logic;
    signal udp_tx_data_int  : std_logic_vector(7 downto 0);
    signal udp_tx_ready_int : std_logic;

    -- ARP Responder Signals
    signal arp_tx_req_int   : std_logic;
    signal arp_tx_data_int  : std_logic_vector(7 downto 0);
    signal arp_tx_ready_int : std_logic;

    -- Master RMII TX Signals (Output of Arbiter)
    signal tx_start_int : std_logic;
    signal tx_data_int  : std_logic_vector(7 downto 0);
    signal tx_ready_int : std_logic;
    signal tx_busy_int  : std_logic;

    -- I2C & Sequencer Interconnects
    signal i2c_ena_int      : std_logic;
    signal i2c_addr_int     : std_logic_vector(6 downto 0);
    signal i2c_reg_addr_int : std_logic_vector(7 downto 0);
    signal i2c_data_wr_int  : std_logic_vector(7 downto 0);
    signal i2c_busy_int     : std_logic;
    signal i2c_ack_err_int  : std_logic;
    signal i2c_stuck_int    : std_logic;
    signal i2c_scl_stuck    : std_logic;
    signal i2c_sda_stuck    : std_logic;
    signal i2c_rd_mode_int  : std_logic;
    signal m_scl_o, m_sda_o, m_scl_i, m_sda_i : std_logic;
    signal i2c_scl_drv_ok, i2c_sda_drv_ok, i2c_st_done : std_logic;
    signal i2c_recovered : std_logic;
    signal dbg_status2_int : std_logic_vector(7 downto 0);
    signal dbgt_meta, dbgt_sync : std_logic_vector(7 downto 0) := (others => '0');
    signal dbgu_meta, dbgu_sync : std_logic_vector(7 downto 0) := (others => '0');
    signal dbgv_meta, dbgv_sync : std_logic_vector(7 downto 0) := (others => '0');
    signal i2c_probe_int, i2c_addr_nack_int : std_logic;
    signal dbg_scan_cnt_int, dbg_scan_addr_int : std_logic_vector(7 downto 0);
    signal dbg_scan_mask_int : std_logic_vector(7 downto 0);
    signal dbg_vfy_mask_int  : std_logic_vector(7 downto 0);
    signal dbgx_meta, dbgx_sync : std_logic_vector(7 downto 0) := (others => '0');
    signal dbgw_meta, dbgw_sync : std_logic_vector(7 downto 0) := (others => '0');

    -- Raw SDATA edge counters. Answers "is the ADC driving the data line at
    -- all", independent of whether our framing happens to line up. Exact zeros
    -- in the channel table could be a silent bus OR a mis-snapshot; this tells
    -- the two apart.
    -- SDATA registered on the FALLING edge of clk_18m, for the activity
    -- counters below. They used to compare the raw pin on the rising edge, which
    -- is a half-period path against tABDD = 18 ns plus the clock-forwarding and
    -- buffer delay - it cannot be met, and once the SDC referenced the input
    -- delay to bclk_pin rather than to the internal PLL node the analyser said so
    -- (-7.275 ns, and -122 ns of TNS swamping the whole clk[2] domain summary).
    -- tdm8_rx already registers SDATA on the falling edge for exactly this
    -- reason; these two do the same so the diagnostic is sampled the same way the
    -- audio is. See the note on sdata_f in tdm8_rx.vhd.
    signal sd_a_f, sd_b_f   : std_logic := '0';
    signal sd_a_d, sd_b_d   : std_logic := '0';
    -- PER-SLOT activity bitmaps, not edge counts. Bit k is set if slot k saw at
    -- least one SDATA transition during the window. See the process below.
    signal act_a, act_b     : std_logic_vector(7 downto 0) := (others => '0');
    signal act_a_l, act_b_l : std_logic_vector(7 downto 0) := (others => '0');
    -- Local BCLK-within-frame counter, used only to attribute an edge to a slot.
    signal slot_cnt         : unsigned(7 downto 0) := (others => '0');
    signal lr_d             : std_logic := '0';

    -- Fault counters, in the 50 MHz board-clock domain so they survive anything
    -- that happens to the audio PLL. Both saturate at 255.
    --   pll_drop : times the FPGA PLL lost lock after first achieving it
    --   rst_drop : times adc_rst_n was re-asserted after the initial release,
    --              i.e. how often all four ADCs were reset at runtime
    -- The timeline showed U19 and U20 going dead in exactly the same windows,
    -- which is a shared cause, and both of these are gated on pll_locked.
    -- Two-stage synchroniser for pll_locked before the edge detector below.
    -- The ALTPLL lock output is asynchronous to clk_50m_board, so the detector
    -- used to compare a registered copy against the RAW pin: one metastable
    -- sample, or a glitch on an unsynchronised input, could latch pll_ever_lost
    -- and declare the audio PLL unstable when it was not. That flag is exactly
    -- what a day of framing debug rested on, so it must not be able to lie.
    -- Edge detection now happens entirely between two synchronised stages.
    signal pll_lock_s1 : std_logic := '0';
    signal pll_lock_s2 : std_logic := '0';
    signal pll_lock_d : std_logic := '0';
    signal pll_drop   : unsigned(7 downto 0) := (others => '0');
    -- Sticky "the audio PLL has lost lock at least once since power-up",
    -- published in status bit 5. Raised in the clk_50m_board domain and read in
    -- clk_18m, so it goes through the 2-FF chain below like every other
    -- cross-domain byte.
    signal pll_ever_lost : std_logic := '0';
    -- Sticky "adc_rst_n was re-asserted after its initial release". rst_drop
    -- counted exactly this and was read by nothing, so a spurious hardware reset
    -- of all four ADCs was invisible. It matters because the reset is 100 ms and
    -- reconfiguration follows, which lands in the same 110-170 ms band every
    -- observed dropout falls into. Published in status bit 6.
    signal rst_ever      : std_logic := '0';
    signal rst_meta, rst_sync : std_logic := '0';
    signal pll_lost_meta, pll_lost_sync : std_logic := '0';
    -- dbg_health/dbg_ot come from the sequencer in the rmii_ref_clk domain and
    -- were wired STRAIGHT into packet_formatter, which runs on clk_18m, while
    -- the other eight debug bytes went through synchronisers. Two independent
    -- 50 MHz oscillators and a 12.288 MHz PLL output, three unrelated domains.
    signal dbgy_meta, dbgy_sync : std_logic_vector(7 downto 0) := (others => '0');
    signal dbgz_meta, dbgz_sync : std_logic_vector(7 downto 0) := (others => '0');
    signal rst_n_d    : std_logic := '0';
    signal rst_seen   : std_logic := '0';
    signal rst_drop   : unsigned(7 downto 0) := (others => '0');
    signal dbg_ot_int : std_logic_vector(7 downto 0);
    signal dbg_health_int : std_logic_vector(7 downto 0);
    signal act_win          : unsigned(15 downto 0) := (others => '0');
    signal i2c_data_rd_int  : std_logic_vector(7 downto 0);
    signal adc_pll_lock_int : std_logic;
    signal adc_cfg_ok_int   : std_logic;
    signal dbg_rd_pll_int   : std_logic_vector(7 downto 0);
    signal dbg_rd_sai_int   : std_logic_vector(7 downto 0);
    -- 2-FF sync into the 18 MHz domain. These bytes are static once the ADC
    -- boot sequence finishes, so per-bit synchronisers are sufficient.
    signal dbg0_meta, dbg0_sync : std_logic_vector(7 downto 0) := (others => '0');
    signal dbg1_meta, dbg1_sync : std_logic_vector(7 downto 0) := (others => '0');
    signal dbgs_meta, dbgs_sync : std_logic_vector(7 downto 0) := (others => '0');
    signal boot_done_int : std_logic;
    signal dbg_status_int : std_logic_vector(7 downto 0);
    signal i2c_fault_int    : std_logic;
    
    -- UDP RX to Sequencer Interconnects
    signal udp_rx_req_int   : std_logic := '0';
    signal udp_rx_ack_int   : std_logic;
    signal udp_adc_sel_int  : std_logic_vector(1 downto 0) := "00";
    signal udp_ch_sel_int   : std_logic_vector(1 downto 0) := "00";
    signal udp_gain_int     : std_logic_vector(7 downto 0) := x"A0";

    -- ==========================================
    -- NETWORK PARAMETERS
    --
    -- *** C_NODE IS THE ONLY PER-BOARD EDIT. ***
    --
    -- Everything else on the network side derives from it, so building the
    -- image for board 3 means changing this one integer and nothing else.
    -- That is deliberate: the previous arrangement had the MAC, the IP, the
    -- UDP port and a hand-computed IP header checksum as four independent
    -- literals in two files, and getting three of the four right produces a
    -- board that transmits perfectly and delivers nothing.
    --
    --   node   MAC             IP               UDP port
    --     1    DEADBEEF0001    192.168.1.101    5005
    --     2    DEADBEEF0002    192.168.1.102    5006
    --     3    DEADBEEF0003    192.168.1.103    5007
    --     4    DEADBEEF0004    192.168.1.104    5008
    --
    -- ONE PORT PER BOARD, deliberately. Putting all four on 5005 was tried and
    -- reverted: the RTL side is a one-line change, but the port is what the host
    -- uses to tell the boards apart. Every tool here calls recv(), which
    -- discards the sender, so four boards on one port would merge four
    -- independent sequence-number streams into one socket. And on Windows two
    -- sockets may both BIND the same UDP port with SO_REUSEADDR while only ONE
    -- receives - measured on this machine, the second binds without error and
    -- then sits silent - so a shared port also means only one capture process
    -- can run at a time. Separate ports cost nothing and avoid both.
    --
    -- Node 1 reproduces the previous hardcoded values exactly.
    -- ==========================================
    constant C_NODE : integer range 1 to 4 := 1;

    constant C_FPGA_MAC : std_logic_vector(47 downto 0) :=
        x"DEADBEEF00" & std_logic_vector(to_unsigned(C_NODE, 8));
    constant C_FPGA_IP  : std_logic_vector(31 downto 0) :=
        x"C0A801" & std_logic_vector(to_unsigned(100 + C_NODE, 8));
    constant C_UDP_PORT : std_logic_vector(15 downto 0) :=
        std_logic_vector(to_unsigned(5004 + C_NODE, 16));

    -- The capture host. Same on every board.
    --
    -- C_PC_IP must match the static address set on the PC's wired adapter, and
    -- it is load bearing twice over: the ADCs' destination, and the filter that
    -- decides whose ARP we are willing to learn from.
    constant C_PC_IP  : std_logic_vector(31 downto 0) := x"C0A8010A"; -- 192.168.1.10

    -- Deployment PC, Realtek PCIe GbE, A0-AD-9F-22-4B-6E.
    --
    -- This is the RESET DEFAULT, not a fixed value - pc_mac_r below starts here
    -- and is overwritten by whatever ARPs us from C_PC_IP. Two things follow:
    -- the deployment PC works from the first packet with no ARP round trip, and
    -- moving the array to a different host needs no reflash, just one packet in
    -- our direction (a ping is enough) to teach us the new MAC.
    --
    -- It was x"FFFFFFFFFFFF" with the comment "Broadcast until ARP resolves",
    -- but nothing ever resolved it - see pc_mac_r. Broadcast is flooded to every
    -- switch port and is never suppressed by MAC learning, so with four boards
    -- each 100 Mbit port would have seen all four streams, 183 Mbit/s offered
    -- into a 100 Mbit link, and the I2C control path would have starved.
    constant C_PC_MAC : std_logic_vector(47 downto 0) := x"A0AD9F224B6E";

    -- The live destination MAC for audio frames. Starts at C_PC_MAC and tracks
    -- whoever ARPs us from C_PC_IP. arp_responder already captured both the
    -- sender MAC and the sender IP for its own reply path; all that was missing
    -- was carrying them out to here.
    signal pc_mac_r       : std_logic_vector(47 downto 0) := C_PC_MAC;
    signal arp_learn_mac  : std_logic_vector(47 downto 0);
    signal arp_learn_val  : std_logic;

    -- ==========================================
    -- LMK1C1104 OUTPUT ENABLE POLARITY
    -- Pin 2 of U1/U2 is drawn as "1G" (active high) in the KiCad symbol, but
    -- SnapEDA symbols frequently drop the inversion bubble. If BCLK measured at
    -- J18 pin 5 is flat instead of ~1.65 V DC, the buffers are being disabled by
    -- PLL lock - set this to false and the whole clock tree comes alive.
    -- ==========================================
    -- Confirmed active high in the LMK1C1104 datasheet. Kept as a constant only
    -- so the assumption is visible rather than buried in a signal assignment.
    constant C_BUFFER_EN_ACTIVE_HIGH : boolean := true;

    -- ==========================================
    -- LRCLK PATH CONTINUITY TEST
    -- The real LRCLK is a 1-in-192 pulse, so it averages to ~17 mV and a
    -- multimeter cannot tell it from a dead net. Set this true to drive
    -- lrclk_out with a 50% duty square instead: every point on the LRCLK tree
    -- (U1 pin 1, U1 outputs, the LRCLK_n nets, ADAU pin 15) then reads ~1.65 V
    -- DC and a break is obvious. Audio is meaningless in this mode - it is a
    -- continuity test only. Set back to false afterwards.
    -- ==========================================
    constant C_LRCLK_TEST_50PCT : boolean := false;

    -- Drives bclk_out (FPGA pin 113 -> U2 -> every MCLK and BCLK pin) with a
    -- ~0.27 Hz square instead of 18.432 MHz. A handheld scope cannot measure the
    -- amplitude of an 18 MHz square - it is at or past the front-end cutoff, and
    -- reports a reduced height for a perfectly healthy clock. That made every
    -- MCLK reading in this bring-up ambiguous (1.7 V, 2.0 V, 2.7 V, 800 mV).
    -- At 0.27 Hz the levels are pure DC: every point on the MCLK/BCLK tree must
    -- read a clean 0.0 V / 3.3 V, and a real amplitude problem becomes obvious.
    -- The ADCs cannot run in this mode - it is a level test only.
    constant C_BCLK_TEST_SLOW : boolean := false;

    -- DIAGNOSTIC: false holds 48V phantom power off entirely, to test whether
    -- the +/-15V rail collapse originates in the phantom path.
    -- 48 V phantom power for the hydrophones. Held off through the whole
    -- bring-up while the +/-15V rail was suspect; that turned out to be the
    -- OPA1671s on a 15 V rail, not the phantom path, which is current-limited
    -- to ~7 mA per pin by 32 x 6k81 feed resistors and could never have loaded
    -- the rail. Enabled 1000 ms after PLL lock, 500 ms after +/-15V.
    constant C_ENABLE_48V : boolean := true;

    -- ------------------------------------------------------------------
    -- PHANTOM WATCHDOG - a fail-safe, not a convention.
    --
    -- The host is supposed to turn 48 V off when it shuts down. That covers an
    -- orderly app restart and nothing else: if the operator app CRASHES, if the
    -- Ethernet cable is pulled, or if the PC loses power, then udp_flags bit 0
    -- is still set inside the FPGA and 48 V stays live on the XLRs forever.
    -- Nothing on the board notices, because nothing on the board was ever told
    -- the host is gone.
    --
    -- With this true, the FPGA stops taking the host's word for it. Phantom
    -- power is gated on having heard a flags-carrying packet within
    -- C_PHANTOM_TIMEOUT_S, so the host must keep saying "yes, still on" or 48 V
    -- drops on its own.
    --
    -- DEFAULT FALSE, deliberately. Turning it on makes a keepalive MANDATORY:
    -- any host that sets phantom and then goes quiet will see 48 V drop
    -- mid-capture, which during a real deployment is worse than the hazard it
    -- prevents. Enable it only once the host actually sends keepalives, and
    -- flash all four boards together - a board with the watchdog on and a board
    -- with it off behave differently under exactly the conditions you would be
    -- least able to diagnose in the water.
    --
    -- The gate is not latching. A keepalive that arrives after a trip restores
    -- phantom power on the spot, because the flags byte it carries says what the
    -- host wants. That is the right behaviour for a link that merely hiccupped;
    -- a host that has genuinely restarted sends flags = 0x00 and phantom stays
    -- off, which is the same thing arriving at the same answer from the other
    -- side.
    --
    -- A trip is visible on the host with no new status bit: it is the only
    -- state where dbg_status2 bits 5, 4 and 3 are all set while bit 6 is clear.
    -- ------------------------------------------------------------------
    constant C_PHANTOM_WATCHDOG  : boolean := false;
    constant C_PHANTOM_TIMEOUT_S : integer := 120;

    -- The schematic net named /SCL lands on ADAU pin 17, which the datasheet
    -- calls SDA, so the pin assignment was crossed to compensate. That relies on
    -- the KiCad symbol's pin numbers matching the real footprint, which cannot
    -- be verified from the netlist. Since I2C never once ran before the ena fix,
    -- there is no evidence for either mapping - flip this to test the other.
    --   false: i2c_scl port drives SCL (pin 76), i2c_sda drives SDA (pin 84)
    --   true : the two are crossed inside the FPGA
    constant C_I2C_SWAP : boolean := true;

    -- DIAGNOSTIC: point the TDM2 receiver at the TDM1 pin.
    --
    -- The firmware is symmetric across the two lines - one entity instantiated
    -- twice, same BCLK, same LRCLK, same register writes, same A/B slot split -
    -- and TDM1 has a part running at 100%, so the logic demonstrably works. So
    -- nothing in this file can single out TDM2 unless the FPGA's own input path
    -- for PIN_119 is at fault. This separates those two cases with no soldering.
    --
    --   channels 9-16 mirror channels 1-8 -> PIN_119's input path and instance
    --       u_rx_B are both fine, so nothing is arriving on the /TDM2 net. That
    --       is copper: J19.4/J21.4, R122, U37.13, U38.13, U43.67.
    --   channels 9-16 still dead          -> the fault is inside the FPGA - the
    --       pin, the bank, or the instance - and it really is firmware.
    --
    -- Set back to false once answered. While true, channels 9-16 are a copy of
    -- TDM1 and say nothing whatever about U37/U38.
    constant C_TDM2_FROM_TDM1 : boolean := false;   -- answered 2026-08-10: ch9-16 mirrored ch1-8, so PIN_119 and u_rx_B are good and /TDM2 carries nothing
    signal   sdata_b_sel      : std_logic;
    signal   lrclk_test : std_logic := '0';
    signal   lrclk_div  : unsigned(25 downto 0) := (others => '0');


    -- ==========================================
    -- SIGNAL PRESERVATION FOR SIGNALTAP
    -- ==========================================
    attribute keep : boolean;
    attribute keep of rx_data_int  : signal is true;
    attribute keep of rx_valid_int : signal is true;
    attribute keep of rx_error_int : signal is true;

begin

    -- ==========================================
    -- DUMMY ASSIGNMENTS FOR UNUSED PCB PINS
    -- ==========================================
    eth_mdc      <= '0';
    eth_mdio     <= 'Z'; -- High impedance (safe for bidirectional)
    
    -- Buffer State waits for PLL lock before engaging the LMK1C1104PWR clock
    -- buffers. Polarity is selectable because the KiCad symbol's "1G" pin may or
    -- may not actually be active high - see C_BUFFER_EN_ACTIVE_HIGH.
    buffer_state <= pll_locked when C_BUFFER_EN_ACTIVE_HIGH else not pll_locked;

    -- ==========================================
    -- HEARTBEAT CLOCK TEST (blinking = clock healthy)
    -- ==========================================
    process(clk_50m_board)
    begin
        if rising_edge(clk_50m_board) then
            clk_div <= clk_div + 1;
        end if;
    end process;
    
    -- Heartbeat doubles as the I2C verdict. Three distinguishable rates:
    --   VERY FAST (~12 Hz)  a line was low while we drove neither. The bus is
    --                       jammed - missing pull-up, or a device holding it.
    --                       NOTE this outranks the others, because a stuck-low
    --                       SDA also makes every ACK read as a success.
    --   FAST      (~3 Hz)   transfers ran but nothing acknowledged: no ADAU1978
    --                       responding at 0x11/0x31/0x51/0x71.
    --   SLOW      (~0.75 Hz) boot writes were acknowledged on a healthy bus.
    test_led <= std_logic(clk_div(21)) when i2c_stuck_int = '1'
           else std_logic(clk_div(23)) when i2c_fault_int = '1'
           else std_logic(clk_div(25));

    -- ==========================================
    -- PACKET VISUALIZATION (Pulse Stretchers)
    -- ==========================================
    process(rmii_ref_clk)
    begin
        if rising_edge(rmii_ref_clk) then
            -- 1. Catch incoming data from the PHY (RX)
            if rmii_crs_dv = '1' then
                rx_flash_counter <= 25000000; -- Reset counter to 500ms
            elsif rx_flash_counter > 0 then
                rx_flash_counter <= rx_flash_counter - 1;
            end if;

            -- 2. Catch outgoing data from the FPGA MAC (TX)
            -- Note: We check our internal tx_start/tx_en signal before it hits the PHY
            if tx_start_int = '1' or active_tx /= "00" then
                tx_flash_counter <= 25000000; -- Reset counter to 500ms
            elsif tx_flash_counter > 0 then
                tx_flash_counter <= tx_flash_counter - 1;
            end if;
        end if;
    end process;

    -- Note: This assumes Active-Low LEDs (standard for Altera/Intel dev boards). 
    -- It outputs '0' (ON) when the counter > 0, and '1' (OFF) when idle.
    -- If your board uses Active-High LEDs, swap the '0' and '1' below!
    -- BRING-UP OVERRIDE: the Ethernet path is proven, so these two LEDs are
    -- more useful reporting which I2C conductor is being held low. LED ON = that
    -- line was found low while the FPGA was driving neither, i.e. that is the
    -- jammed one. Revert the two lines below to restore packet activity display:
    --     debug_led_rx <= '0' when (rx_flash_counter > 0) else '1';
    --     debug_led_tx <= '0' when (tx_flash_counter > 0) else '1';
    debug_led_rx <= '0' when i2c_scl_stuck = '1' else '1';  -- ON = SCL held low
    debug_led_tx <= '0' when i2c_sda_stuck = '1' else '1';  -- ON = SDA held low


    -- ==========================================
    -- I2C OPEN-DRAIN BUFFERS
    -- The schematic net named /SCL lands on ADAU pin 17, which the datasheet
    -- calls SDA, so the pin assignment was crossed to compensate. That relies
    -- on the KiCad symbol's pin numbers matching the real footprint, which
    -- cannot be checked from the netlist. Flip C_I2C_SWAP to test the other
    -- mapping without touching the QSF.
    -- ==========================================
    i2c_scl <= '0' when ((not C_I2C_SWAP) and m_scl_o = '0')
                     or (C_I2C_SWAP and m_sda_o = '0') else 'Z';
    i2c_sda <= '0' when ((not C_I2C_SWAP) and m_sda_o = '0')
                     or (C_I2C_SWAP and m_scl_o = '0') else 'Z';
    m_scl_i <= i2c_sda when C_I2C_SWAP else i2c_scl;
    m_sda_i <= i2c_scl when C_I2C_SWAP else i2c_sda;

    -- Count SDATA transitions over a 65536-cycle window in the audio clock
    -- domain: 2.7 ms at 24.576 MHz, 3.5 ms at 18.432 MHz, 5.3 ms at 12.288 MHz.
    -- The absolute duration does not matter - the counter saturates at 255
    -- either way and it is only used as a live/static indicator.
    --
    -- How to read it. A healthy line saturates almost immediately: one window
    -- holds ~250 audio frames of 256 bits each, so tens of thousands of edges.
    -- So 255 means "driven", and anything near 0 means "nobody is driving".
    -- There is no useful information in between.
    --
    -- 2026-08-18: this used to be a saturating EDGE COUNT per line, and its
    -- recorded limitation was that both parts on a line shared one number, so it
    -- could not say WHICH of the two went quiet. It is now a PER-SLOT ACTIVITY
    -- BITMAP, which answers exactly that at no cost in packet bytes:
    --
    --   bit k = 1  slot k saw at least one SDATA transition during the window
    --
    --   0xFF  all eight slots driven          - healthy, same as the old 255
    --   0x0F  only slots 0-3                  - the upper part went quiet
    --                                           (U20 on line A, U38 on line B)
    --   0xF0  only slots 4-7                  - the lower part went quiet
    --                                           (U19 on line A, U37 on line B)
    --   0x00  nothing at all                  - whole line dead, same as old 0
    --
    -- This is the measurement that localizes a dropout to ONE PART without
    -- depending on our decode being correct, which no other diagnostic here can
    -- do. The channel table cannot: if the slot alignment is wrong, every
    -- channel reads wrong and the table looks the same as a dead part.
    --
    -- THREE LIMITATIONS, all real:
    --
    -- 1. NOT BIT-EXACT AT THE PART BOUNDARY. slot_cnt is reset by the LRCLK
    --    rising edge we generate, but the ADC's data for slot 0 arrives about one
    --    BCLK later - that offset is what C_BIT_ADJ = -1 encodes. So the two
    --    nibbles bleed into each other by 1 BCLK out of 128. Irrelevant for "did
    --    this part drive at all", wrong if read as bit-exact slot framing.
    --
    -- 2. DIGITAL SILENCE READS AS ABSENCE. A part driving exact 0x000000 makes no
    --    transitions and its bits read 0. This is a genuine regression against
    --    the old count, where one live part masked a silent one. Cross-check
    --    against the channel levels: 0x0F with ch 5-8 at exact zero means U20 is
    --    not driving; 0x0F with ch 5-8 carrying real audio is impossible and
    --    means the slot phase is off, not that U20 died.
    --
    -- 3. IT DETECTS SUSTAINED LOSS, NOT FLICKER. The bits are OR'd over 65536
    --    BCLKs (~256 frames), so a slot driven even once in that 2.7 ms reads 1.
    --    A part dropping 200 of 256 frames still shows healthy. OR is kept
    --    deliberately because it preserves the 0xFF = healthy convention; if
    --    frame-granularity flicker needs catching, AND these instead.
    --
    -- The slot index is 32 BCLKs wide here because TDM8 slots are 32 BCLKs. For
    -- TDM16 (16-BCLK slots) it becomes slot_cnt(7 downto 4).
    --
    -- Sample the line in the same capture as the audio, not separately - and on
    -- the same EDGE as the audio too. See sd_a_f/sd_b_f above.
    process(clk_18m)
    begin
        if falling_edge(clk_18m) then
            sd_a_f <= sdata_in_A;
            sd_b_f <= sdata_in_B;
        end if;
    end process;

    process(clk_18m)
    begin
        if rising_edge(clk_18m) then
            sd_a_d <= sd_a_f;
            sd_b_d <= sd_b_f;
            lr_d   <= lrclk_int;

            -- BCLKs since the frame start. Derived locally from lrclk_int rather
            -- than exported out of tdm8_master, so this diagnostic cannot perturb
            -- the audio path. The counter wraps at 256 on its own, which is the
            -- frame length, so a missed LRCLK edge self-corrects on the next one.
            -- Reset to 1, not 0. lr_d is registered in this same process, so the
            -- edge is detected on the cycle AFTER the LRCLK rise; writing 0 here
            -- would make slot_cnt read 0 on the cycle whose true frame index is
            -- already 1, leaving the counter permanently one BCLK behind on top
            -- of the data-arrival offset noted above. Loading 1 cancels it.
            if lrclk_int = '1' and lr_d = '0' then
                slot_cnt <= to_unsigned(1, slot_cnt'length);
            else
                slot_cnt <= slot_cnt + 1;
            end if;

            if act_win = 65535 then
                act_win <= (others => '0');
                act_a_l <= act_a;      -- publish
                act_b_l <= act_b;
                act_a   <= (others => '0');
                act_b   <= (others => '0');
            else
                act_win <= act_win + 1;
                -- Top three bits of the BCLK counter = the 32-BCLK slot index.
                if sd_a_f /= sd_a_d then
                    act_a(to_integer(slot_cnt(7 downto 5))) <= '1';
                end if;
                if sd_b_f /= sd_b_d then
                    act_b(to_integer(slot_cnt(7 downto 5))) <= '1';
                end if;
            end if;
        end if;
    end process;

    -- Second status byte: the I2C output drive self test, plus the 48 V
    -- phantom power READBACK in bits 6:3.
    --
    -- Phantom power used to be write-only: the host could command it and had no
    -- way to ask what the board was actually doing. That leaves two divergences
    -- nothing could detect, and they push the state opposite ways:
    --
    --   FPGA resets, GUI does not. udp_rx_core clears udp_flags to 0x00 on
    --   sys_rst, which follows pll_locked, so phantom drops to off while the
    --   checkbox still reads ON.
    --
    --   GUI restarts, FPGA does not. Nothing clears udp_flags, so 48 V stays
    --   LIVE on the XLRs while a freshly started GUI shows off - and because
    --   every gain command carries the flags byte, the next fader move sends
    --   flags = 0x00 and switches phantom off without anyone asking it to.
    --
    -- All four gating terms are published, not just the pin, because "off" has
    -- three causes that need different responses:
    --   bit 6  en_48v as actually driven on the pin
    --   bit 5  the host asked for it        (udp_flags bit 0)
    --   bit 4  staged power-up reached 1000 ms
    --   bit 3  this build permits it at all (C_ENABLE_48V)
    -- bit 6 is the AND of the other three, so any disagreement names the cause.
    --
    -- This is what the FPGA ASSERTS, not what reaches the hydrophones. EN_48V
    -- is an output and there is no sense line back from the 48 V supply, so a
    -- dead DC-DC, a blown fuse or an open enable trace still reads here as on.
    --
    -- Bits 6:3 were the "0000" pad. i2c_scan.py decodes only 0x80, 0x02 and
    -- 0x01 out of this byte, and check_sync.py only checks WHICH byte lands in
    -- which frame, so filling the pad breaks no existing reader.
    dbg_status2_int <= '1'
                     & en_48v_drv           -- bit 6: EN_48V pin as driven
                     & udp_flags_int(0)     -- bit 5: host requested it
                     & en_48v_int           -- bit 4: staged power-up reached it
                     & en48_permit          -- bit 3: build permits it
                     & i2c_st_done          -- bit 2: self test ran
                     & i2c_sda_drv_ok       -- bit 1: SDA pulled low successfully
                     & i2c_scl_drv_ok;      -- bit 0: SCL pulled low successfully

    -- Everything we know about the I2C bus and the ADC, packed into one byte
    -- and shipped in every packet so it can be read without touching an LED.
    --
    -- WARNING: bits 6 and 5 below are DEAD. The synchroniser that publishes this
    -- byte (see dbgs_meta, further down) forwards only bit 7 and bits 4:0, and
    -- substitutes rst_ever into bit 6 and pll_ever_lost into bit 5. Quartus
    -- reports both source terms as unread. What i2c_scan.py decodes for those two
    -- positions is "ADC hardware reset" and "audio PLL lock", NOT the two signals
    -- named here. Kept assigned rather than deleted so the intent stays visible,
    -- but do not add a reader of bit 6 or 5 of this signal expecting these.
    dbg_status_int <= '1'                 -- bit 7: marker, proves this is populated
                    & adc_cfg_ok_int      -- bit 6: DEAD, replaced by rst_ever
                    & adc_pll_lock_int    -- bit 5: DEAD, replaced by pll_ever_lost
                    & boot_done_int       -- bit 4: boot + verify sequence finished
                    & i2c_sda_stuck       -- bit 3
                    & i2c_scl_stuck       -- bit 2
                    & i2c_stuck_int       -- bit 1
                    & i2c_fault_int;      -- bit 0: a NACK was seen

    -- Resets
    sys_rst   <= not pll_locked;
    sys_rst_n <= not sys_rst;

    -- ==========================================
    -- PHY DELAYED BOOT RESET
    -- ==========================================
    process(clk_50m_board)
    begin
        if rising_edge(clk_50m_board) then
            if pll_locked = '0' then
                phy_rst_cnt <= (others => '0');
                phy_rst_n_int <= '0';
            else
                -- 50 MHz clock = 20ns per cycle.
                -- The LAN8720A needs nRST asserted for at least 100us; hold it
                -- for 10ms (500_000 cycles) so the PHY's internal regulator and
                -- strap latching are comfortably settled before release.
                if phy_rst_cnt < 500000 then
                    phy_rst_cnt <= phy_rst_cnt + 1;
                    phy_rst_n_int <= '0';
                else
                    phy_rst_n_int <= '1'; -- Release reset
                end if;
            end if;
        end if;
    end process;

    -- Drive the PHY reset port. Without this the port has no driver at all and
    -- Quartus ties it to GND (Warning 13410).
    --
    -- NOTE: on the Robomarine 1.0 board this does nothing. FPGA pin 31 is not
    -- routed anywhere, and the LAN8720A ~RST (U42 pin 15) is hardwired to +3V3,
    -- so the PHY only ever sees its own power-on reset. Kept because the port
    -- must be driven, and so a respin that routes the net works unchanged.
    phy_rst_n <= phy_rst_n_int;

    -- ==========================================
    -- ADAU1978 DELAYED BOOT RESET
    -- The ADCs must come out of reset with their clocks already running, so this
    -- keys off pll_locked - the same condition that enables the LMK1C1104 buffers
    -- via buffer_state, which is what actually gates MCLK/BCLK/LRCLK to the parts.
    -- ==========================================
    process(clk_50m_board)
    begin
        if rising_edge(clk_50m_board) then
            if pll_locked = '0' then
                adc_rst_cnt   <= (others => '0');
                adc_rst_n_int <= '0'; -- Hold the ADCs in reset until clocks exist
            else
                -- The ADAU1978 requires ~PD/~RST held low for tD, the time DVDD
                -- needs to bleed down before the core will re-initialise:
                --     REQ = RINT || REXT = 64k || 3k = 2.866k   (R119 = 3k)
                --     tD  = 1.32 * REQ * CEXT = 1.32 * 2.866k * 10uF = 37.8 ms
                -- CEXT is C123/C134/C257/C268 (10uF). Hold for 100 ms, a 2.6x
                -- margin. Anything near or below tD leaves the core half
                -- initialised, which presents as a part that is powered and
                -- correctly addressed but NACKs every transaction.
                -- 100 ms / 20 ns = 5,000,000.
                if adc_rst_cnt < 5000000 then
                    adc_rst_cnt   <= adc_rst_cnt + 1;
                    adc_rst_n_int <= '0';
                else
                    adc_rst_n_int <= '1'; -- Release reset
                end if;
            end if;
        end if;
    end process;

    -- Fault counters
    process(clk_50m_board)
    begin
        if rising_edge(clk_50m_board) then
            -- 2-FF synchronise, THEN edge detect between synchronised stages.
            pll_lock_s1 <= pll_locked;
            pll_lock_s2 <= pll_lock_s1;
            pll_lock_d  <= pll_lock_s2;
            if pll_lock_d = '1' and pll_lock_s2 = '0' and pll_drop /= 255 then
                pll_drop <= pll_drop + 1;
                -- Sticky, and unlike pll_drop this one is actually published.
                -- pll_drop counted lock losses and was read by nothing, so the
                -- design had no visibility into audio PLL stability at all -
                -- the one clock everything else is derived from. A whole day of
                -- framing debug rested on "the PLL is stable", inferred from a
                -- steady packet rate rather than measured.
                pll_ever_lost <= '1';
            end if;

            rst_n_d <= adc_rst_n_int;
            if adc_rst_n_int = '1' then
                rst_seen <= '1';                  -- initial release happened
            elsif rst_seen = '1' and rst_n_d = '1' and rst_drop /= 255 then
                rst_drop <= rst_drop + 1;         -- a later re-assertion
                rst_ever <= '1';
            end if;
        end if;
    end process;

    adc_rst_n <= adc_rst_n_int;


    -- ==========================================
    -- STAGED POWER-UP
    -- Previously both of these were just "<= pll_locked", so the +/-15V analog
    -- rails and the 48V phantom supply switched on in the same clock cycle,
    -- before the ADAU1978s had been configured. Now they are staggered:
    --      500 ms   +/-15V   (ADC boot needs ~250 ms: 150 ms BOOT_DELAY,
    --                         128 address probes, the register writes and two
    --                         30 ms PLL settles)
    --     1000 ms   48V phantom
    -- Timed off pll_locked rather than gated on boot_done on purpose: if the
    -- I2C boot ever failed, gating would leave the analog rails permanently
    -- dead and turn a recoverable fault into a board that looks unpowered.
    --
    -- C_ENABLE_48V is a diagnostic switch. The +/-15V rail collapses on power-up,
    -- randomly on either polarity, and the phantom path is the prime suspect: the
    -- 47 uF coupling caps feed the THAT1512 inputs, which run on +/-15V, so a
    -- failed or reversed cap injects 48V into +/-15V circuitry and which rail
    -- goes depends on the injection polarity. Set false to bring up +/-15V with
    -- phantom power off and see whether the rail is then stable.
    -- ==========================================
    process(clk_50m_board)
    begin
        if rising_edge(clk_50m_board) then
            if pll_locked = '0' then
                pwr_cnt    <= (others => '0');
                en_15v_int <= '0';
                en_48v_int <= '0';
            else
                if pwr_cnt < 50000000 then
                    pwr_cnt <= pwr_cnt + 1;
                end if;
                if pwr_cnt >= 25000000 then   -- 500 ms
                    en_15v_int <= '1';
                end if;
                if pwr_cnt >= 50000000 then   -- 1000 ms
                    en_48v_int <= '1';
                end if;
            end if;
        end if;
    end process;

    en_15v <= en_15v_int;
    -- 48V needs the staged power-up to have reached it, the build to permit it,
    -- and the host to have asked for it (udp_flags bit 0). The runtime flag
    -- defaults to 0, so phantom power never comes up on its own after a reset -
    -- it always takes a deliberate command from the GUI.
    en48_permit <= '1' when C_ENABLE_48V else '0';

    -- Phantom watchdog counter. Prescaled to 1 Hz rather than counting cycles:
    -- 120 s at 50 MHz is 6e9, which needs 33 bits, while 26 + 8 bits of
    -- prescaler and seconds cost a third of that and are far easier to read in
    -- a timing report.
    --
    -- Runs in rmii_ref_clk, the same domain udp_flags_wr_int and udp_flags_int
    -- come from, so the kick needs no synchroniser. It runs even when
    -- C_PHANTOM_WATCHDOG is false - a few hundred idle LUTs - so that enabling
    -- the feature is a one-constant change with no untested logic behind it.
    process(rmii_ref_clk)
    begin
        if rising_edge(rmii_ref_clk) then
            if sys_rst = '1' or udp_flags_wr_int = '1' then
                -- Reset on a flags-carrying packet, NOT on udp_req. A 2-byte
                -- gain command proves the link is up but says nothing about
                -- what the host wants phantom power to do, and feeding the
                -- watchdog from it would let a stray `ctrl.py --set` re-arm
                -- 48 V minutes after the app that asked for it had died.
                ph_wd_tick <= (others => '0');
                ph_wd_secs <= (others => '0');
                ph_wd_trip <= '0';
            elsif ph_wd_tick = 49999999 then        -- 1 s at 50 MHz
                ph_wd_tick <= (others => '0');
                if ph_wd_secs < C_PHANTOM_TIMEOUT_S then
                    ph_wd_secs <= ph_wd_secs + 1;
                else
                    ph_wd_trip <= '1';              -- holds until the next kick
                end if;
            else
                ph_wd_tick <= ph_wd_tick + 1;
            end if;
        end if;
    end process;

    ph_wd_gate <= '0' when (C_PHANTOM_WATCHDOG and ph_wd_trip = '1') else '1';

    en_48v_drv  <= en_48v_int and udp_flags_int(0) and en48_permit and ph_wd_gate;
    en_48v      <= en_48v_drv;
    
    -- Output physical clocks to the outside world
    bclk_out     <= lrclk_test when C_BCLK_TEST_SLOW else clk_18m;

    -- ~1.1 Hz square, used only by the LRCLK continuity test above.
    -- Deliberately SLOW. The first version toggled every clk_18m edge, giving
    -- 9.216 MHz - which a handheld DMM cannot average reliably, the same reason
    -- an 18 MHz BCLK reads as a meaningless fraction of a volt. The LMK1C1104
    -- is specified "DC to 250 MHz" and is DC-coupled, so a 1 Hz square passes
    -- through U1 exactly like a real clock. On a meter it visibly flips between
    -- 0 V and 3.3 V about twice a second: unambiguous, and no bandwidth involved.
    -- 0.27 Hz (3.6 s period). 1.1 Hz was still too fast: a handheld DMM updating
    -- 2-3 times a second partially averages it and reports ~1.65 V for a high,
    -- which reads as a degraded logic level when nothing is wrong. At 3.6 s the
    -- meter fully settles on 0.0 V and 3.3 V.
    process(clk_18m)
    begin
        if rising_edge(clk_18m) then
            lrclk_div <= lrclk_div + 1;
        end if;
    end process;
    lrclk_test <= std_logic(lrclk_div(25));   -- 18.432 MHz / 2^26 = 0.27 Hz, 3.6 s period

    -- Re-time LRCLK onto the phase shifted clock, immediately before the pad.
    --
    -- INACTIVE unless C_LRCLK_RETIME is true. With it false this register is
    -- built and then stripped, because lrclk_pin_r drives nothing - the pad
    -- takes lrclk_int directly, exactly as 96K_ACT did.
    --
    -- ONLY the pin moves. lrclk_int stays in the clk_18m domain and stays wired
    -- to u_rx_A / u_rx_B as their frame reference, so no new clock crossing is
    -- created inside the FPGA - which is the whole reason tdm8_master is NOT
    -- moved into the clk_lr domain instead. clk_lr and clk_18m come from the
    -- same PLL and derive_pll_clocks puts them in one synchronous group, so
    -- this register is a normal, fully analysable synchronous path.
    --
    -- At 105 deg (11.870 ns) against lrclk_int changing at 20.345 ns:
    --     setup  11.870 - (20.345 - 40.690) = 32.22 ns
    --     hold   20.345 - 11.870            =  8.47 ns
    -- At 225 deg (25.431 ns) the capture edge falls AFTER the data changes:
    --     setup  25.431 - 20.345            =  5.09 ns
    --     hold   (20.345 + 40.690) - 25.431 = 35.60 ns
    -- Both directions are comfortable; the tool will confirm on the real paths.
    process(clk_lr)
    begin
        if rising_edge(clk_lr) then
            lrclk_pin_r <= lrclk_int;
        end if;
    end process;

    -- The test mux stays on the RAW divider, not the re-timed copy: the 0.27 Hz
    -- continuity square has nothing to do with frame timing and must not be
    -- delayed by a register the test is not exercising.
    lrclk_out    <= lrclk_test  when C_LRCLK_TEST_50PCT
               else lrclk_pin_r when C_LRCLK_RETIME
               else lrclk_int;

    -- ==========================================
    -- TX ARBITER (Collision-Free State Lock)
    -- ==========================================
    process(rmii_ref_clk)
    begin
        if rising_edge(rmii_ref_clk) then
            if sys_rst = '1' then
                active_tx <= "00";
            else
                if active_tx = "00" then
                    -- Only hand out the line when rmii_tx is genuinely idle.
                    -- After a client drops its request rmii_tx still has the FCS
                    -- and the inter-frame gap to emit; granting during that window
                    -- would leave the new client waiting on an acknowledge that
                    -- belongs to the previous frame.
                    if tx_busy_int = '0' then
                        if arp_tx_req_int = '1' then
                            active_tx <= "01";
                        elsif udp_tx_start_int = '1' then
                            active_tx <= "10";
                        end if;
                    end if;
                else
                    if active_tx = "01" and arp_tx_req_int = '0' then
                        active_tx <= "00";
                    elsif active_tx = "10" and udp_tx_start_int = '0' then
                        active_tx <= "00";
                    end if;
                end if;
            end if;
        end if;
    end process;

    tx_start_int <= arp_tx_req_int  when active_tx = "01" else
                    udp_tx_start_int  when active_tx = "10" else
                    '0';

    tx_data_int  <= arp_tx_data_int   when active_tx = "01" else
                    udp_tx_data_int   when active_tx = "10" else
                    x"00";
    
    arp_tx_ready_int <= tx_ready_int when active_tx = "01" else '0';
    udp_tx_ready_int <= tx_ready_int when active_tx = "10" else '0';


    -- ==========================================
    -- INSTANTIATIONS
    -- ==========================================

    u_pll : pll_audio port map (
        areset => '0',    
        inclk0 => clk_50m_board,
        c0     => open,         -- 12.288 MHz -> 48 kHz, MCS=001, 32-BCLK slots
        c1     => open,         -- 18.432 MHz -> 96 kHz at 192 BCLK/frame, MCS=010
        c2     => clk_18m,      -- 24.576 MHz -> 96 kHz at 256 BCLK/frame, MCS=011
        c3     => clk_lr,       -- 24.576 MHz phase shifted, LRCLK pad re-timing
        locked => pll_locked
    );

    u_master : tdm8_master port map (
        rst        => sys_rst,
        clk_in     => clk_18m,
        bclk_out   => open,
        lrclk_out  => lrclk_int
    );

    -- TDM16: ONE receiver on ONE line, replacing the two tdm8_rx instances.
    --
    -- All four parts are jumpered onto a single SDATA net (R21 pin 1 to R122
    -- pin 1) and hold four slots each out of sixteen. Sixteen 16-BCLK slots is
    -- still 256 BCLKs per frame, so BCLK, LRCLK and tdm8_master are unchanged.
    --
    -- Both FPGA SDATA pins now see the same wire, so which one is read is
    -- arbitrary; sdata_in_A is used and sdata_in_B is left connected but
    -- unread. Keeping the port avoids a QSF pin change, and if the jumper is
    -- ever removed the pin is already there.
    --
    -- tdm16_rx splits its output into the same two 192-bit halves the old pair
    -- produced, so tdm16_merge, packet_formatter, the UDP layout and every host
    -- script are untouched.
    sdata_b_sel <= sdata_in_A when C_TDM2_FROM_TDM1 else sdata_in_B;

    u_rx_A : tdm8_rx port map (
        rst         => sys_rst,
        bclk_in     => clk_18m,
        lrclk_in    => lrclk_int,
        sdata_in    => sdata_in_A,
        ch_data_out => ch_data_A_int
    );

    u_rx_B : tdm8_rx port map (
        rst         => sys_rst,
        bclk_in     => clk_18m,
        lrclk_in    => lrclk_int,
        sdata_in    => sdata_b_sel,
        ch_data_out => ch_data_B_int
    );

    -- ================= SWITCHING THIS FILE TO TDM16 =================
    -- Delete the two instances above, uncomment the one below, and fit the board
    -- jumper (R21 pin 1 to R122 pin 1, or devboard header pins 32 and 119).
    -- tdm16_rx.vhd stays in the project either way, so nothing else moves here.
    -- adau_sequencer.vhd has its own note covering the four register values.
    -- Board procedure and failure signatures: docs/TDM16_BRINGUP.md
    --
    -- u_rx : tdm16_rx port map (
    --     rst => sys_rst, bclk_in => clk_18m, lrclk_in => lrclk_int,
    --     sdata_in => sdata_in_A,
    --     ch_data_A => ch_data_A_int, ch_data_B => ch_data_B_int);
    -- ================================================================

    u_merge : tdm16_merge port map (
        clk         => clk_18m,
        rst         => sys_rst,
        lrclk_pulse => lrclk_int,
        ch_data_A   => ch_data_A_int,
        ch_data_B   => ch_data_B_int,
        tdm16_out   => tdm16_out_int,
        tdm16_valid => tdm16_val_int
    );

    u_fmt : packet_formatter port map (
        clk_18m      => clk_18m,
        rst          => sys_rst,
        tdm16_valid  => tdm16_val_int,
        tdm16_data   => tdm16_out_int,
        -- Raw SDATA edge counters, NOT the ADC register readbacks any more.
        --
        -- act_a_l/act_b_l were computed every 2.7 ms and then read by nothing:
        -- when the debug bytes were reshuffled to carry cfg_bad/clip and
        -- ot_ever/pll_lost, these lost their slot and became dead code that
        -- Quartus stripped. That removed the only measurement in the design
        -- that can tell "the ADC stopped driving the line" apart from "the ADC
        -- is driving and our decode is wrong" - which is precisely the question
        -- every dropout investigation has had to guess at since.
        --
        -- The readbacks they displace (ADAU 0x01 and 0x05 from C_VERIFY_IDX)
        -- are static after boot, cover ONE part, and their live per-part
        -- equivalents are already in dbg_status6/7 as cfg_bad and pll_lost.
        -- i2c_scan.py can read the raw registers from any part at any time.
        -- A live liveness bit on both SDATA lines is worth more than that.
        --
        -- Already in the clk_18m domain, same as packet_formatter, so unlike
        -- dbg0_sync/dbg1_sync these need no synchroniser.
        dbg_byte0    => act_a_l,
        dbg_byte1    => act_b_l,
        dbg_status   => dbgs_sync,
        dbg_status2  => dbgt_sync,
        dbg_status3  => dbgu_sync,
        dbg_status4  => dbgv_sync,
        dbg_status5  => dbgw_sync,
        dbg_status6  => dbgy_sync,
        dbg_status7  => dbgz_sync,
        dbg_status8  => dbgx_sync,
        fifo_wr_en   => fifo_wr_en_int,
        fifo_wr_data => fifo_wr_data_int,
        packet_ready => packet_ready_int
    );

    u_fifo : async_fifo port map (
        data    => fifo_wr_data_int,
        rdclk   => rmii_ref_clk,
        rdreq   => fifo_rd_en_int,
        wrclk   => clk_18m,
        wrreq   => fifo_wr_en_int,
        q       => fifo_rd_data_int,
        rdempty => open, 
        wrfull  => open  
    );

    u_rmii_rx : rmii_rx
    generic map (
        -- The residue constant is verified, but enforcement stays OFF until the
        -- link is known good: dropping frames on a bad FCS is indistinguishable
        -- from a dead link, and rmii_rx can still clip the tail of a frame (see
        -- the CRS_DV note there). Turn on once ARP and UDP are confirmed working.
        G_ENFORCE_FCS => false
    )
    port map (
        clk_50m      => rmii_ref_clk,
        rst          => sys_rst,
        rmii_crs_dv  => rmii_crs_dv,
        rmii_rxd     => rmii_rxd,
        rx_data      => rx_data_int,
        rx_valid     => rx_valid_int,
        rx_end       => rx_end_int,
        rx_error     => rx_error_int
    );

    u_udp : udp_tx_core port map (
        clk_50m      => rmii_ref_clk,
        rst          => sys_rst,
        fpga_mac     => C_FPGA_MAC,
        fpga_ip      => C_FPGA_IP,
        pc_mac       => pc_mac_r,
        pc_ip        => C_PC_IP,
        udp_port     => C_UDP_PORT,
        packet_ready => packet_ready_int,
        fifo_rd_en   => fifo_rd_en_int,
        fifo_rd_data => fifo_rd_data_int,
        tx_start     => udp_tx_start_int,
        tx_data      => udp_tx_data_int, 
        tx_ready     => udp_tx_ready_int 
    );

    -- ==========================================
    -- COMPILE TIME SELF TEST of work.net_pkg.ipv4_checksum
    --
    -- There is no simulator licence on this machine, so this is the regression
    -- test for the checksum arithmetic. Every condition is static, so Analysis
    -- & Synthesis evaluates it and the build FAILS if any node's checksum comes
    -- out wrong - which is the only outcome that is safe, because a bad
    -- checksum produces a board that transmits flawlessly and delivers nothing.
    --
    -- Expected values were derived independently (one's complement sum in
    -- Python) and node 1 additionally reproduces the x"B577" literal that was
    -- hand-computed in udp_tx_core and proven on hardware.
    --
    -- x"01B6" = 438 = 20 byte IP header + 8 byte UDP header + 410 byte payload.
    -- ==========================================
    assert ipv4_checksum(x"C0A80165", x"C0A8010A", x"01B6") = x"B577"
        report "net_pkg.ipv4_checksum WRONG for node 1 (192.168.1.101), expected B577"
        severity failure;
    assert ipv4_checksum(x"C0A80166", x"C0A8010A", x"01B6") = x"B576"
        report "net_pkg.ipv4_checksum WRONG for node 2 (192.168.1.102), expected B576"
        severity failure;
    assert ipv4_checksum(x"C0A80167", x"C0A8010A", x"01B6") = x"B575"
        report "net_pkg.ipv4_checksum WRONG for node 3 (192.168.1.103), expected B575"
        severity failure;
    assert ipv4_checksum(x"C0A80168", x"C0A8010A", x"01B6") = x"B574"
        report "net_pkg.ipv4_checksum WRONG for node 4 (192.168.1.104), expected B574"
        severity failure;

    -- A carry-fold case the four node addresses above do not exercise: this
    -- one's inner sum overflows 16 bits more than once.
    assert ipv4_checksum(x"FFFFFFFF", x"FFFFFFFF", x"FFFF") = x"3AEE"
        report "net_pkg.ipv4_checksum WRONG on the all-ones carry-fold case"
        severity failure;

    -- Destination MAC tracking. arp_learn_val strobes only for an ARP request
    -- that passed every check arp_responder already makes (EtherType, hardware
    -- and protocol type, opcode, target IP = ours, clean CRC) AND whose sender
    -- IP is C_PC_IP - so a stray host on the segment cannot redirect the audio
    -- stream at us. Same clock domain as the responder, so no crossing.
    process(rmii_ref_clk)
    begin
        if rising_edge(rmii_ref_clk) then
            if sys_rst = '1' then
                pc_mac_r <= C_PC_MAC;
            elsif arp_learn_val = '1' then
                pc_mac_r <= arp_learn_mac;
            end if;
        end if;
    end process;

    u_arp : arp_responder port map (
        clk_50m      => rmii_ref_clk,
        rst          => sys_rst,
        fpga_mac     => C_FPGA_MAC,
        fpga_ip      => C_FPGA_IP,
        pc_ip        => C_PC_IP,
        learn_mac    => arp_learn_mac,
        learn_valid  => arp_learn_val,
        rx_data      => rx_data_int,
        rx_valid     => rx_valid_int,
        rx_end       => rx_end_int,
        rx_error     => rx_error_int,
        arp_tx_req   => arp_tx_req_int, 
        arp_tx_data  => arp_tx_data_int,
        tx_ready     => arp_tx_ready_int
    );

    u_rmii : rmii_tx port map (
        clk_50m      => rmii_ref_clk,
        rst          => sys_rst,
        tx_start     => tx_start_int,
        tx_data      => tx_data_int,
        tx_ready     => tx_ready_int,
        tx_busy      => tx_busy_int,
        rmii_tx_en   => rmii_tx_en,
        rmii_txd     => rmii_txd
    );

    u_i2c_master : i2c_master
    generic map (
        -- 100 kHz rather than the 400 kHz default. Four ADAU1978s plus the J19
        -- and J21 header stubs put real capacitance on this bus, and the
        -- datasheet's rise-time budget assumes under 236 pF. Slower is free.
        -- Dropped to 50 kHz. The pull-up sits at the FPGA end while four QFN
        -- inputs and two header stubs hang off the far end, so rise time at the
        -- ADCs is the weak link. Halving the bit rate doubles the time each edge
        -- has to get there. This is mitigation, not a cure - a 2.2k pull-up near
        -- the ADC cluster is the real fix.
        --   50 MHz / 50 kHz = 1000 clocks per bit, / 4 phases = 250
        QUARTER_BIT_CYCLES => 250
    )
    port map (
        clk          => rmii_ref_clk,
        rst_n        => sys_rst_n,
        ena          => i2c_ena_int,
        addr         => i2c_addr_int,
        reg_addr     => i2c_reg_addr_int,
        data_wr      => i2c_data_wr_int,
        rd_mode      => i2c_rd_mode_int,
        probe_mode   => i2c_probe_int,
        data_rd      => i2c_data_rd_int,
        busy         => i2c_busy_int,
        ack_error    => i2c_ack_err_int,
        addr_nack    => i2c_addr_nack_int,
        bus_stuck    => i2c_stuck_int,
        scl_stuck    => i2c_scl_stuck,
        sda_stuck    => i2c_sda_stuck,
        scl_drv_ok   => i2c_scl_drv_ok,
        sda_drv_ok   => i2c_sda_drv_ok,
        selftest_done=> i2c_st_done,
        recovered    => i2c_recovered,
        scl_o        => m_scl_o,
        sda_o        => m_sda_o,
        scl_i        => m_scl_i,
        sda_i        => m_sda_i
    );

    u_adau_sequencer : adau1978_sequencer
    generic map (
        -- Must expire AFTER adc_rst_n releases at 100 ms, or the first pass
        -- talks to parts still held in reset. 150 ms = 7,500,000 cycles at 20 ns,
        -- which also covers the datasheet's ~10 ms PLL settling recommendation.
        BOOT_DELAY_CYCLES => 7500000
    )
    port map (
        clk          => rmii_ref_clk,
        rst_n        => sys_rst_n,
        boot_done    => boot_done_int,
        udp_req      => udp_rx_req_int,
        udp_ack      => udp_rx_ack_int,
        udp_adc_sel  => udp_adc_sel_int,
        udp_ch_sel   => udp_ch_sel_int,
        udp_gain     => udp_gain_int,
        i2c_ena      => i2c_ena_int,
        i2c_addr     => i2c_addr_int,
        i2c_reg_addr => i2c_reg_addr_int,
        i2c_data_wr  => i2c_data_wr_int,
        i2c_busy     => i2c_busy_int,
        i2c_ack_error => i2c_ack_err_int,
        i2c_rd_mode  => i2c_rd_mode_int,
        i2c_probe    => i2c_probe_int,
        i2c_addr_nack => i2c_addr_nack_int,
        i2c_data_rd  => i2c_data_rd_int,
        i2c_fault    => i2c_fault_int,
        adc_pll_lock => adc_pll_lock_int,
        adc_cfg_ok   => adc_cfg_ok_int,
        dbg_rd_pll   => dbg_rd_pll_int,
        dbg_rd_sai   => dbg_rd_sai_int,
        dbg_scan_cnt  => dbg_scan_cnt_int,
        dbg_scan_addr => dbg_scan_addr_int,
        dbg_scan_mask => dbg_scan_mask_int,
        dbg_ot        => dbg_ot_int,
        dbg_health    => dbg_health_int,
        dbg_vfy_mask  => dbg_vfy_mask_int
    );

    process(clk_18m)
    begin
        if rising_edge(clk_18m) then
            dbg0_meta <= dbg_rd_pll_int;  dbg0_sync <= dbg0_meta;
            dbg1_meta <= dbg_rd_sai_int;  dbg1_sync <= dbg1_meta;
            -- status bit 5 was unused by i2c_scan (it decodes 0x80, 0x10, 0x08,
            -- 0x04, 0x02, 0x01), so the audio PLL flag goes there.
            pll_lost_meta <= pll_ever_lost; pll_lost_sync <= pll_lost_meta;
            rst_meta      <= rst_ever;       rst_sync      <= rst_meta;
            -- bit 7 kept, bit 6 = adc_rst_n re-asserted, bit 5 = audio PLL lost
            dbgs_meta <= dbg_status_int(7) & rst_sync & pll_lost_sync
                       & dbg_status_int(4 downto 0);
            dbgs_sync <= dbgs_meta;
            dbgy_meta <= dbg_health_int; dbgy_sync <= dbgy_meta;
            dbgz_meta <= dbg_ot_int;     dbgz_sync <= dbgz_meta;
            dbgt_meta <= dbg_status2_int; dbgt_sync <= dbgt_meta;
            dbgu_meta <= dbg_scan_cnt_int;  dbgu_sync <= dbgu_meta;
            dbgv_meta <= dbg_scan_addr_int; dbgv_sync <= dbgv_meta;
            dbgw_meta <= dbg_scan_mask_int; dbgw_sync <= dbgw_meta;
            -- bit7 = scan invalid (from the sequencer), bit6 = recovery ran
            dbgx_meta <= dbg_vfy_mask_int(7) & i2c_recovered
                       & dbg_vfy_mask_int(5 downto 0);
            dbgx_sync <= dbgx_meta;
        end if;
    end process;

    u_udp_rx : udp_rx_core port map (
        clk_50m      => rmii_ref_clk,
        rst          => sys_rst,
        fpga_mac     => C_FPGA_MAC,
        fpga_ip      => C_FPGA_IP,
        rx_data      => rx_data_int,
        rx_valid     => rx_valid_int,
        rx_end       => rx_end_int,
        rx_error     => rx_error_int,
        udp_req      => udp_rx_req_int,
        udp_ack      => udp_rx_ack_int,
        udp_adc_sel  => udp_adc_sel_int,
        udp_ch_sel   => udp_ch_sel_int,
        udp_gain     => udp_gain_int,
        udp_flags    => udp_flags_int,
        udp_flags_wr => udp_flags_wr_int
    );

end architecture rtl;