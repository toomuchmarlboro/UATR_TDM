library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

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
            udp_gain     : out std_logic_vector(7 downto 0)
        );
    end component;


    -- ==========================================
    -- INTERNAL SIGNALS
    -- ==========================================
    
    -- Clocks & Resets
    -- pll_audio generates BOTH audio clocks exactly from 50 MHz:
    --   c0 = 768/3125  = 12.288 MHz  -> 48 kHz  (256 BCLK/frame, MCS=001)
    --   c1 = 1152/3125 = 18.432 MHz  -> 72 kHz  (256 BCLK/frame, MCS=011)
    -- Both are exact, not approximations. MCLK and BCLK share a net on this
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

    -- TX Arbiter State Lock
    signal active_tx   : std_logic_vector(1 downto 0) := "00"; -- "00"=Idle, "01"=ARP, "10"=UDP

    -- Audio Domain (18.432 MHz)
    signal lrclk_int     : std_logic;
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
    signal sd_a_d, sd_b_d   : std_logic := '0';
    signal act_a, act_b     : unsigned(7 downto 0) := (others => '0');
    signal act_a_l, act_b_l : unsigned(7 downto 0) := (others => '0');
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
    -- HARDCODED NETWORK PARAMETERS (NODE 1)
    -- ==========================================
    constant C_FPGA_MAC : std_logic_vector(47 downto 0) := x"DEADBEEF0001";
    constant C_FPGA_IP  : std_logic_vector(31 downto 0) := x"C0A80165"; -- 192.168.1.101
    constant C_PC_MAC   : std_logic_vector(47 downto 0) := x"FFFFFFFFFFFF"; -- Broadcast until ARP resolves
    constant C_PC_IP    : std_logic_vector(31 downto 0) := x"C0A8010A"; -- 192.168.1.10

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
    constant C_ENABLE_48V : boolean := false;

    -- The schematic net named /SCL lands on ADAU pin 17, which the datasheet
    -- calls SDA, so the pin assignment was crossed to compensate. That relies on
    -- the KiCad symbol's pin numbers matching the real footprint, which cannot
    -- be verified from the netlist. Since I2C never once ran before the ena fix,
    -- there is no evidence for either mapping - flip this to test the other.
    --   false: i2c_scl port drives SCL (pin 76), i2c_sda drives SDA (pin 84)
    --   true : the two are crossed inside the FPGA
    constant C_I2C_SWAP : boolean := true;
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
    -- domain: 3.5 ms at 18.432 MHz, 5.3 ms at 12.288 MHz. The absolute
    -- duration does not matter - the counter saturates at 255 either way
    -- and it is only used as a live/static indicator.
    process(clk_18m)
    begin
        if rising_edge(clk_18m) then
            sd_a_d <= sdata_in_A;
            sd_b_d <= sdata_in_B;
            if act_win = 65535 then
                act_win <= (others => '0');
                act_a_l <= act_a;      -- publish
                act_b_l <= act_b;
                act_a   <= (others => '0');
                act_b   <= (others => '0');
            else
                act_win <= act_win + 1;
                if sdata_in_A /= sd_a_d and act_a /= 255 then
                    act_a <= act_a + 1;
                end if;
                if sdata_in_B /= sd_b_d and act_b /= 255 then
                    act_b <= act_b + 1;
                end if;
            end if;
        end if;
    end process;

    -- Second status byte: results of the I2C output drive self test.
    dbg_status2_int <= '1' & "0000"
                     & i2c_st_done          -- bit 2: self test ran
                     & i2c_sda_drv_ok       -- bit 1: SDA pulled low successfully
                     & i2c_scl_drv_ok;      -- bit 0: SCL pulled low successfully

    -- Everything we know about the I2C bus and the ADC, packed into one byte
    -- and shipped in every packet so it can be read without touching an LED.
    dbg_status_int <= '1'                 -- bit 7: marker, proves this is populated
                    & adc_cfg_ok_int      -- bit 6: 0x05 read back as written
                    & adc_pll_lock_int    -- bit 5: ADC PLL locked
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
    en_48v <= en_48v_int when C_ENABLE_48V else '0';
    
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

    lrclk_out    <= lrclk_test when C_LRCLK_TEST_50PCT else lrclk_int;

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
        c0     => open,         -- 12.288 MHz -> 48 kHz (breaks U37/U38)
        c1     => open,         -- 18.432 MHz -> 72 kHz
        c2     => clk_18m,      -- 24.576 MHz -> 96 kHz, MCS=011, 32-BCLK slots
        locked => pll_locked
    );

    u_master : tdm8_master port map (
        rst        => sys_rst,
        clk_in     => clk_18m,
        bclk_out   => open,
        lrclk_out  => lrclk_int
    );

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
        sdata_in    => sdata_in_B,
        ch_data_out => ch_data_B_int
    );

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
        dbg_byte0    => dbg0_sync,
        dbg_byte1    => dbg1_sync,
        dbg_status   => dbgs_sync,
        dbg_status2  => dbgt_sync,
        dbg_status3  => dbgu_sync,
        dbg_status4  => dbgv_sync,
        dbg_status5  => dbgw_sync,
        dbg_status6  => std_logic_vector(act_a_l),
        dbg_status7  => std_logic_vector(act_b_l),
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
        pc_mac       => C_PC_MAC,
        pc_ip        => C_PC_IP,
        packet_ready => packet_ready_int,
        fifo_rd_en   => fifo_rd_en_int,
        fifo_rd_data => fifo_rd_data_int,
        tx_start     => udp_tx_start_int,
        tx_data      => udp_tx_data_int, 
        tx_ready     => udp_tx_ready_int 
    );

    u_arp : arp_responder port map (
        clk_50m      => rmii_ref_clk,
        rst          => sys_rst,
        fpga_mac     => C_FPGA_MAC,
        fpga_ip      => C_FPGA_IP,
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
        dbg_vfy_mask  => dbg_vfy_mask_int
    );

    process(clk_18m)
    begin
        if rising_edge(clk_18m) then
            dbg0_meta <= dbg_rd_pll_int;  dbg0_sync <= dbg0_meta;
            dbg1_meta <= dbg_rd_sai_int;  dbg1_sync <= dbg1_meta;
            dbgs_meta <= dbg_status_int;  dbgs_sync <= dbgs_meta;
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
        udp_gain     => udp_gain_int
    );

end architecture rtl;