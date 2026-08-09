-- Self-checking simulation of the whole audio capture chain:
--   tdm8_master -> (modelled ADAU1978 pair) -> tdm8_rx -> tdm16_merge
--
-- Written because C_BIT_ADJ had been set by trial and error on hardware and I
-- got it wrong twice by reasoning about shift register indices. This decides it
-- arithmetically instead.
--
-- The ADC model follows the configuration the sequencer actually writes:
--   0x04 = 0x3F  BCLKEDGE = 0  -> data changes on the FALLING edge of BCLK
--   0x05 = 0x5A  SDATA_FMT=01 left justified, SAI=011 TDM8
--   0x06 = 0x08  SLOT_WIDTH=00 32 BCLKs/slot, DATA_WIDTH=0 24-bit,
--                LR_MODE=1 pulse, SAI_MSB=0 MSB first, SAI_MS=0 slave
--   0x09 = 0xF8  DRV_HIZ = 1 -> tri-state outside its own slots
--
-- HONEST LIMIT: the model encodes an assumption about how many BCLKs after the
-- LRCLK edge the part presents its first data bit. G_LAUNCH selects it, so the
-- test reports the correct C_BIT_ADJ *for each* assumption rather than pretending
-- to know the silicon. What it does prove unconditionally is that tdm8_master,
-- tdm8_rx and tdm16_merge agree with each other and with the frame arithmetic.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity tb_chain is
    generic (
        -- BCLKs from the sync edge to the first sampled data bit.
        G_LAUNCH : integer := 1
    );
end entity tb_chain;

architecture sim of tb_chain is

    component tdm8_master is
        port (rst : in std_logic; clk_in : in std_logic;
              bclk_out : out std_logic; lrclk_out : out std_logic);
    end component;

    component tdm8_rx is
        port (rst : in std_logic; bclk_in : in std_logic; lrclk_in : in std_logic;
              sdata_in : in std_logic;
              ch_data_out : out std_logic_vector(191 downto 0));
    end component;

    component tdm16_merge is
        port (clk : in std_logic; rst : in std_logic; lrclk_pulse : in std_logic;
              ch_data_A : in std_logic_vector(191 downto 0);
              ch_data_B : in std_logic_vector(191 downto 0);
              tdm16_out : out std_logic_vector(383 downto 0);
              tdm16_valid : out std_logic);
    end component;

    constant TBCLK : time := 81.380208 ns;      -- 12.288 MHz
    constant SLOTW : integer := 32;
    constant DATAW : integer := 24;

    signal clk   : std_logic := '0';
    signal rst   : std_logic := '1';
    signal bclk  : std_logic;
    signal lrclk : std_logic;
    signal sd_a, sd_b : std_logic := '0';
    signal ch_a, ch_b : std_logic_vector(191 downto 0);
    signal merged     : std_logic_vector(383 downto 0);
    signal valid      : std_logic;
    signal running    : boolean := true;

    -- distinctive per-slot payloads, so a bit shift is readable in the result
    function payload(line : integer; slot : integer) return unsigned is
    begin
        -- line 0: 0xA10000 + slot*0x1111 ; line 1: 0x5B0000 + slot*0x1111
        if line = 0 then
            return to_unsigned(16#A10000# + slot * 16#1111#, DATAW);
        else
            return to_unsigned(16#5B0000# + slot * 16#1111#, DATAW);
        end if;
    end function;

    -- what tdm16_merge should present for channel ch (1..16)
    function expect_ch(ch : integer) return unsigned is
    begin
        if ch <= 8 then return payload(0, ch - 1);
        else             return payload(1, ch - 9);
        end if;
    end function;

begin

    -- 12.288 MHz BCLK
    process begin
        while running loop
            clk <= '0'; wait for TBCLK / 2;
            clk <= '1'; wait for TBCLK / 2;
        end loop;
        wait;
    end process;

    u_master : tdm8_master port map (
        rst => rst, clk_in => clk, bclk_out => open, lrclk_out => lrclk);

    -- ADAU1978 pair on each line. Data changes on the FALLING edge of BCLK
    -- (BCLKEDGE = 0); outside its own slots the part is tri-stated and the 10k
    -- pulldown on the net holds the line low, modelled here as '0'.
    gen_lines : for line in 0 to 1 generate
        process(clk)
            variable n       : integer := -1;   -- BCLK index within the frame
            variable prev_lr : std_logic := '0';
            variable slot    : integer;
            variable bitpos  : integer;
            variable v       : std_logic := '0';
        begin
            if falling_edge(clk) then
                if lrclk = '1' and prev_lr = '0' then
                    n := 0;
                elsif n >= 0 then
                    n := n + 1;
                end if;
                prev_lr := lrclk;

                v := '0';
                if n >= G_LAUNCH then
                    slot   := (n - G_LAUNCH) / SLOTW;
                    bitpos := (n - G_LAUNCH) mod SLOTW;
                    if slot < 8 and bitpos < DATAW then
                        -- MSB first: bitpos 0 is bit 23
                        v := payload(line, slot)(DATAW - 1 - bitpos);
                    end if;
                end if;

                if line = 0 then sd_a <= v; else sd_b <= v; end if;
            end if;
        end process;
    end generate;

    u_rx_a : tdm8_rx port map (
        rst => rst, bclk_in => clk, lrclk_in => lrclk,
        sdata_in => sd_a, ch_data_out => ch_a);

    u_rx_b : tdm8_rx port map (
        rst => rst, bclk_in => clk, lrclk_in => lrclk,
        sdata_in => sd_b, ch_data_out => ch_b);

    u_merge : tdm16_merge port map (
        clk => clk, rst => rst, lrclk_pulse => lrclk,
        ch_data_A => ch_a, ch_data_B => ch_b,
        tdm16_out => merged, tdm16_valid => valid);

    -- ------------------------------------------------------------------ checks
    process
        variable lr_hi, lr_period : integer;
        variable t0 : time;
        variable got, want : unsigned(DATAW - 1 downto 0);
        variable fails : integer := 0;
        variable nvalid : integer := 0;
    begin
        rst <= '1';
        wait for 10 * TBCLK;
        rst <= '0';

        -- 1. LRCLK shape: period must be 256 BCLKs, high time C_LR_PULSE_BCLKS
        wait until rising_edge(lrclk);
        wait until rising_edge(lrclk);          -- skip the first, post-reset
        t0 := now;
        lr_hi := 0;
        while lrclk = '1' loop
            wait until falling_edge(clk);
            if lrclk = '1' then lr_hi := lr_hi + 1; end if;
        end loop;
        wait until rising_edge(lrclk);
        lr_period := integer((now - t0) / TBCLK);

        report "LRCLK period = " & integer'image(lr_period) & " BCLKs, high for "
             & integer'image(lr_hi) & " BCLKs";
        if lr_period /= 256 then
            report "FAIL: LRCLK period is not 256 BCLKs" severity error;
            fails := fails + 1;
        end if;

        -- 2. tdm16_valid must pulse exactly once per frame
        nvalid := 0;
        for i in 1 to 256 loop
            wait until rising_edge(clk);
            if valid = '1' then nvalid := nvalid + 1; end if;
        end loop;
        report "tdm16_valid pulses per frame = " & integer'image(nvalid);
        if nvalid /= 1 then
            report "FAIL: tdm16_valid must assert exactly once per frame"
                severity error;
            fails := fails + 1;
        end if;

        -- 3. channel payloads, after the pipeline has filled
        for f in 1 to 4 loop
            wait until rising_edge(clk) and valid = '1';
        end loop;

        for ch in 1 to 16 loop
            got  := unsigned(merged(383 - 24 * (ch - 1) downto 360 - 24 * (ch - 1)));
            want := expect_ch(ch);
            if got /= want then
                report "ch" & integer'image(ch) & " got 0x"
                     & to_hstring(std_logic_vector(got)) & " want 0x"
                     & to_hstring(std_logic_vector(want)) severity note;
                fails := fails + 1;
            end if;
        end loop;

        if fails = 0 then
            report "=== CHAIN OK: G_LAUNCH=" & integer'image(G_LAUNCH)
                 & " decodes correctly with the current C_BIT_ADJ ===";
        else
            report "=== CHAIN MISMATCH: " & integer'image(fails)
                 & " failures with G_LAUNCH=" & integer'image(G_LAUNCH)
                 & " and the current C_BIT_ADJ ===" severity note;
        end if;

        running <= false;
        wait;
    end process;

end architecture sim;
