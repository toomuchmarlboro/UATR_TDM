library ieee;
use ieee.std_logic_1164.all;

-- Single-line TDM16 receiver.
--
-- Replaces the pair of tdm8_rx instances when all four ADAU1978s are jumpered
-- onto one SDATA net (R21 pin 1 to R122 pin 1). Sixteen slots of 16 BCLKs each
-- still totals 256 BCLKs per frame, so BCLK stays 24.576 MHz and tdm8_master is
-- unchanged - only the slot width and the decode differ from TDM8.
--
-- Outputs are split into the same two 192-bit halves tdm16_merge already expects,
-- so nothing downstream of here changes: merge, packet_formatter, the UDP layout
-- and every host script stay exactly as they are.
--
--   ch_data_A   slots 1-8    channels 1-8    U19 (slots 1-4) + U20 (slots 5-8)
--   ch_data_B   slots 9-16   channels 9-16   U37 (slots 9-12) + U38 (slots 13-16)
entity tdm16_rx is
    port (
        rst         : in  std_logic;
        bclk_in     : in  std_logic;
        lrclk_in    : in  std_logic;
        sdata_in    : in  std_logic;
        ch_data_A   : out std_logic_vector(191 downto 0);   -- ch 1-8
        ch_data_B   : out std_logic_vector(191 downto 0)    -- ch 9-16
    );
end entity tdm16_rx;

architecture rtl of tdm16_rx is

    -- Bit alignment, same meaning and same sign convention as tdm8_rx.
    --
    -- KEEP THIS EQUAL TO tdm8_rx's C_BIT_ADJ. The value describes the phase
    -- between the LRCLK the FPGA emits and the first data bit the ADC launches.
    -- That relationship is set by tdm8_master's launch edge and by the capture
    -- pipeline, and is completely independent of how wide a slot is - so the
    -- figure carries straight over from TDM8. It is -1 for the same reason
    -- recorded in tdm8_rx.vhd and docs/LRCLK_HOLD_VIOLATION.md: with LRCLK now
    -- launched on the falling edge of BCLK, every part deterministically frames
    -- one BCLK later than it did while it was winning the tALH race.
    --
    -- If the channels read as noise or "misaligned?", this is the one knob.
    constant C_BIT_ADJ : integer range -8 to 8 := -1;

    -- WHY THE CAPTURE IS DELAYED, AND WHY IT HAS TO BE FOR TDM16.
    --
    -- With 16-bit data in 16-BCLK slots there are NO pad bits. In TDM8 each
    -- 24-bit sample sat in a 32-BCLK slot, so eight spare bits per slot gave
    -- C_BIT_ADJ its room to move. Here the data fills the frame exactly: slot 15
    -- ends on the last bit of the frame.
    --
    -- Slicing at the same instant tdm8_rx does would put slot 15's bottom bit at
    -- index C_BIT_ADJ. At the current C_BIT_ADJ = -1 that is shift_reg(14 downto
    -- -1), which is not a legal range and will not compile - and the direction it
    -- fails in is exactly the one this design needs.
    --
    -- There are no bit positions below zero to borrow: at the moment the frame
    -- ends, index 0 holds the most recent bit and nothing newer exists yet. The
    -- only way to create room underneath is to let the shift register run on for
    -- a few more clocks before slicing, which moves the whole frame up by that
    -- many positions. Eight clocks restores the full -8..+8 range the 32-BCLK
    -- slots used to provide for free.
    --
    -- An error here is self-correcting rather than silent: getting the delay
    -- wrong by n bits shows up as every channel misaligned by n, which C_BIT_ADJ
    -- then corrects. Getting it wrong by a whole slot shows up as the channels
    -- being rotated, which is obvious in the channel table.
    constant C_CAP_EXTRA : integer := 8;

    -- 272 = 256 frame + 8 above (positive C_BIT_ADJ, reaching back into the tail
    -- of the previous frame) + 8 below (the capture delay above). Both margins
    -- are needed; trimming either one re-creates the illegal-range trap.
    signal shift_reg : std_logic_vector(271 downto 0) := (others => '0');

    -- Delay chain. lrclk_d/lrclk_d2 are the same two stages tdm8_rx uses, so the
    -- edge detection below is identical; lrclk_pipe simply inserts C_CAP_EXTRA
    -- clocks ahead of them. Counting register stages from lrclk_in:
    --   lrclk_pipe(0) = 1 ... lrclk_pipe(C_CAP_EXTRA-1) = C_CAP_EXTRA
    --   lrclk_d = C_CAP_EXTRA + 1        lrclk_d2 = C_CAP_EXTRA + 2
    -- against tdm8_rx's 1 and 2, i.e. exactly C_CAP_EXTRA clocks later.
    signal lrclk_pipe : std_logic_vector(C_CAP_EXTRA - 1 downto 0) := (others => '0');
    signal lrclk_d    : std_logic := '0';
    signal lrclk_d2   : std_logic := '0';

    -- SDATA registered on the FALLING edge of BCLK, exactly as tdm8_rx does, so
    -- the ADC's 18 ns tABDD gets a full BCLK period instead of half. See the
    -- sdata_f note in tdm8_rx.vhd - the reasoning is unchanged by slot width.
    signal sdata_f : std_logic := '0';

begin

    process(bclk_in)
    begin
        if falling_edge(bclk_in) then
            sdata_f <= sdata_in;
        end if;
    end process;

    process(bclk_in, rst)
        variable a_v : std_logic_vector(191 downto 0);
        variable b_v : std_logic_vector(191 downto 0);
    begin
        if rst = '1' then
            shift_reg  <= (others => '0');
            lrclk_pipe <= (others => '0');
            lrclk_d    <= '0';
            lrclk_d2   <= '0';
            ch_data_A  <= (others => '0');
            ch_data_B  <= (others => '0');

        elsif rising_edge(bclk_in) then

            shift_reg  <= shift_reg(270 downto 0) & sdata_f;

            lrclk_pipe <= lrclk_pipe(C_CAP_EXTRA - 2 downto 0) & lrclk_in;
            lrclk_d    <= lrclk_pipe(C_CAP_EXTRA - 1);
            lrclk_d2   <= lrclk_d;

            -- Rising edge of the delayed frame sync. Edge, not level: the pulse
            -- is C_LR_PULSE_BCLKS wide, and a level test would re-latch on every
            -- clock it stays high. Same rule as tdm8_rx and tdm16_merge.
            if lrclk_d = '1' and lrclk_d2 = '0' then

                -- Slot k occupies [263 + adj - 16k : 248 + adj - 16k]. Slot 0 is
                -- the OLDEST data in the register because it arrived first, so
                -- slot index counts downward through the register.
                --
                -- Each slot is 16 bits and the packet format is 24-bit signed, so
                -- the sample is left-justified with x"00" in the low byte. That
                -- keeps full scale identical to the TDM8 build, so dBFS readings
                -- in udp_monitor and timeline stay directly comparable and the
                -- exact-zero dropout test still works.
                for k in 0 to 7 loop
                    a_v(191 - 24*k downto 168 - 24*k) :=
                        shift_reg(263 + C_BIT_ADJ - 16*k
                                  downto 248 + C_BIT_ADJ - 16*k) & x"00";
                end loop;

                for k in 8 to 15 loop
                    b_v(191 - 24*(k-8) downto 168 - 24*(k-8)) :=
                        shift_reg(263 + C_BIT_ADJ - 16*k
                                  downto 248 + C_BIT_ADJ - 16*k) & x"00";
                end loop;

                ch_data_A <= a_v;
                ch_data_B <= b_v;

            end if;
        end if;
    end process;

end architecture rtl;
