library ieee;
use ieee.std_logic_1164.all;

entity tdm16_merge is
    port (
        clk         : in  std_logic;                       -- BCLK, = clk_18m
        rst         : in  std_logic;
        lrclk_pulse : in  std_logic;                       -- frame sync, EITHER shape
        ch_data_A   : in  std_logic_vector(191 downto 0);  -- ch 1–8
        ch_data_B   : in  std_logic_vector(191 downto 0);  -- ch 9–16
        tdm16_out   : out std_logic_vector(383 downto 0);  -- ch 1–16 ordered
        tdm16_valid : out std_logic                        -- high for 1 cycle on latch
    );
end entity tdm16_merge;

architecture rtl of tdm16_merge is
    -- Edge detect, not a level test. This block was written when LRCLK was a
    -- single-BCLK-wide pulse, where "lrclk_pulse = '1'" was true for exactly
    -- one clock and a level test was the same thing as an edge. With the 50%
    -- duty LRCLK the level is true for 128 clocks, so the level test latched
    -- and asserted tdm16_valid 128 times per frame - 128x the real sample
    -- rate into the FIFO. Symptoms were a packet rate several times higher
    -- than fS/8 and channels that appeared and vanished between runs.
    --
    -- Two stages, matching the lrclk_d/lrclk_d2 chain in tdm8_rx. Correct for
    -- either LRCLK shape.
    --
    -- Note what this does NOT do. tdm8_rx uses an identical two-stage chain off
    -- the same lrclk and the same clk, so its capture condition and the one
    -- below are true on exactly the SAME clock edge. tdm8_rx assigns
    -- ch_data_out on that edge, so the value visible here is still the previous
    -- frame's - this block is permanently one audio frame behind tdm8_rx.
    --
    -- That is harmless and deliberate: A and B are delayed identically, so all
    -- 16 channels stay mutually aligned and the only cost is 10.4 us of latency
    -- at 96 kHz. It is recorded because an earlier version of this comment
    -- claimed the two stages PREVENTED capturing the previous frame, which is
    -- not true and would mislead anyone retuning the delay. If tdm8_rx's chain
    -- is ever shortened, this one must shorten with it or the two will land on
    -- different frames and the A/B halves will skew by one sample.
    signal lrclk_d1 : std_logic := '0';
    signal lrclk_d2 : std_logic := '0';
begin
    process(clk, rst)
    begin
        if rst = '1' then
            tdm16_out   <= (others => '0');
            tdm16_valid <= '0';
            lrclk_d1    <= '0';
            lrclk_d2    <= '0';
        elsif rising_edge(clk) then

            lrclk_d1 <= lrclk_pulse;
            lrclk_d2 <= lrclk_d1;

            -- Default to 0 so valid only pulses for exactly 1 clock cycle
            tdm16_valid <= '0';

            -- One clock after the rising edge of the frame sync
            if lrclk_d1 = '1' and lrclk_d2 = '0' then

                -- Standard VHDL concatenation (&) perfectly aligns with your memory map.
                -- ch_data_A (191 downto 0) becomes tdm16_out(383 downto 192)
                -- ch_data_B (191 downto 0) becomes tdm16_out(191 downto 0)
                tdm16_out   <= ch_data_A & ch_data_B;
                
                -- Fire the trigger for the downstream packet_formatter
                tdm16_valid <= '1';
                
            end if;
            
        end if;
    end process;
end architecture rtl;