library ieee;
use ieee.std_logic_1164.all;

entity tdm8_rx is
    port (
        rst         : in  std_logic;
        bclk_in     : in  std_logic;
        lrclk_in    : in  std_logic;
        sdata_in    : in  std_logic;
        ch_data_out : out std_logic_vector(191 downto 0)
    );
end entity tdm8_rx;

architecture rtl of tdm8_rx is
    -- 96 kHz via 256 x fS: 8 slots x 32 BCLKs carrying 24-bit data, so 8 pad
    -- BCLKs per slot and C_BIT_ADJ has -8..+8 of room.
    --
    -- 0, not -1. SDATA_FMT=01 (left justified) starts the data ON the frame
    -- boundary with no delay, which is ADC launch offset 0, and sim_chain maps
    -- that to adj 0 given the falling-edge input register and the one-clock
    -- capture delay. -1 corresponds to launch 1, i.e. I2S, which is not what is
    -- configured. The 256 x fS builds before 2026-08-11 used -1 and U20's
    -- channels persistently reported "NOISE / misaligned?" in udp_monitor even
    -- though that part never dropped a sample - consistent with being one bit off.
    --
    -- 192 x fS was tried and abandoned: only U19 locked its PLL, the other three
    -- read PLL_LOCK=0 at 18.4332 MHz while all four lock at 24.576 MHz. The one
    -- known per-part difference is the PLL loop filter return (U20 reworked to
    -- AVDD2, the rest to GND), so locking at that VCO point looks marginal and
    -- filter dependent. Unproven.
    --
    -- Confirm on hardware by injecting a known tone: it must appear at full
    -- amplitude on exactly one channel.
    constant C_BIT_ADJ : integer := 0;

    -- RAW CAPTURE MODE. Instead of extracting 24 bits from each 32-BCLK slot,
    -- publish the first 192 BCLKs of the frame verbatim - slots 1 to 6, which
    -- covers both parts on this line (slots 1-4 and 5-6). The host then sees
    -- the actual bit pattern on SDATA rather than an interpretation of it, so
    -- "is the far part driving its slots at all" becomes something you look at
    -- rather than infer. Decode with rawview.py. Audio is meaningless here.
    constant C_RAW_CAPTURE : boolean := false;
    signal shift_reg : std_logic_vector(263 downto 0) := (others => '0');

    -- Capture on the RISING EDGE of LRCLK rather than on the level. With the
    -- old one-BCLK pulse the two were the same thing, so this changes nothing
    -- there; with a 50% duty LRCLK the level is true for 128 BCLKs and a level
    -- trigger would re-latch on every one of them. Edge detection is correct
    -- for both shapes, so the receiver no longer cares which the master sends.
    signal lrclk_d : std_logic := '0';

    -- Capture one clock AFTER the sync edge, not on it.
    --
    -- With 24-BCLK slots the 24-bit sample exactly fills the slot, so unlike the
    -- 32-BCLK case there are no pad bits to borrow and C_BIT_ADJ has no slack: at
    -- k=7 the slice bottom is C_BIT_ADJ itself, so any negative value asks for
    -- shift_reg(22 downto -1), an illegal range. The alignment the ADAU1978
    -- actually needs is one bit later than that bound allows, because slot 7's
    -- last bit is only sampled ON the next sync edge - at the instant the edge is
    -- detected it has not been shifted in yet.
    --
    -- Delaying the capture by one clock brings it in and moves the working
    -- C_BIT_ADJ from -1 to 0, inside the legal range. Same trick tdm16_merge uses.
    signal lrclk_d2 : std_logic := '0';

    -- SDATA is registered on the FALLING edge of BCLK before entering the shift
    -- register, which buys a full BCLK period for the round trip instead of half.
    --
    -- The ADAU1978 launches SDATA on the falling edge (BCLKEDGE = 0). Capturing on
    -- the rising edge gives only half a period: 20.35 ns at 24.576 MHz, against
    -- the part's 18 ns clock-to-out. Quartus measured 2.8-3.6 ns of slack, and
    -- that excludes the U2 buffer (1.5-2.5 ns) and the cable, which it cannot see
    -- - so the real margin is about zero. Capturing on the falling edge instead
    -- makes it falling-to-falling, a full 40.7 ns period, and the 18 ns fits with
    -- room to spare.
    --
    -- Only the DATA path moves. LRCLK edge detection stays on the rising edge, so
    -- the frame reference is unchanged. The extra register delays the stream by
    -- one bit, which sim_chain.py accounts for in C_BIT_ADJ.
    signal sdata_f : std_logic := '0';
begin

    -- Half-cycle input register. See sdata_f above.
    process(bclk_in)
    begin
        if falling_edge(bclk_in) then
            sdata_f <= sdata_in;
        end if;
    end process;

    process(bclk_in, rst)
    begin
        if rst = '1' then
            shift_reg   <= (others => '0');
            ch_data_out <= (others => '0');
            lrclk_d     <= '0';
            lrclk_d2    <= '0';
        elsif rising_edge(bclk_in) then

            lrclk_d  <= lrclk_in;
            lrclk_d2 <= lrclk_d;

            -- 1. Always shift the new bit in (moving everything left)
            shift_reg <= shift_reg(262 downto 0) & sdata_f;
            
            -- 2. One clock after the sync edge the previous frame's 192 bits are
            --    all in the register. Take a snapshot.
            -- 32 BCLKs per slot, 24-bit data: take the top 24 of every 32. The 8
            -- pad BCLKs are what give C_BIT_ADJ its range.
            if lrclk_d = '1' and lrclk_d2 = '0' and C_RAW_CAPTURE then
                -- verbatim: frame bits 1..192, MSB = first bit after the sync
                ch_data_out <= shift_reg(255 + C_BIT_ADJ downto 64 + C_BIT_ADJ);
            elsif lrclk_d = '1' and lrclk_d2 = '0' then
                for k in 0 to 7 loop
                    ch_data_out(191 - 24*k downto 168 - 24*k)
                        <= shift_reg(255 + C_BIT_ADJ - 32*k
                                     downto 232 + C_BIT_ADJ - 32*k);
                end loop;
            end if;
            
        end if;
    end process;

end architecture rtl;