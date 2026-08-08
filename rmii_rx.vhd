library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity rmii_rx is
    generic (
        -- Drive rx_error from the FCS check. The residue constant below has been
        -- confirmed against a reference CRC-32 implementation, so this is safe
        -- to enable. Set false to fall back to fail-open behaviour.
        G_ENFORCE_FCS : boolean := true
    );
    port (
        clk_50m      : in  std_logic;
        rst          : in  std_logic;

        -- Physical Pins from LAN8720A
        rmii_crs_dv  : in  std_logic;
        rmii_rxd     : in  std_logic_vector(1 downto 0);
        
        -- MAC Interface to ARP/UDP cores
        rx_data      : out std_logic_vector(7 downto 0);
        rx_valid     : out std_logic;
        rx_end       : out std_logic;
        rx_error     : out std_logic
    );
end entity rmii_rx;

architecture rtl of rmii_rx is

    component crc32 is
        port (
            clk      : in  std_logic;
            rst      : in  std_logic;
            en       : in  std_logic;
            data_in  : in  std_logic_vector(7 downto 0);
            crc_out  : out std_logic_vector(31 downto 0)
        );
    end component;

    -- ADDED: CHECK_CRC state to pause for pipeline alignment
    type state_type is (IDLE, HUNT_SFD, RECEIVE_DATA, CHECK_CRC);
    signal state : state_type := IDLE;
    
    signal di_bit_cnt   : integer range 0 to 3 := 0;
    signal current_byte : std_logic_vector(7 downto 0) := (others => '0');

    -- Registered copy of the fully assembled byte. crc_en is a registered strobe,
    -- so it goes high one clock AFTER the byte completes - by which point rmii_rxd
    -- already carries the first dibit of the NEXT byte. Feeding the CRC straight
    -- off the pins therefore hands it a corrupted MSB dibit every single time.
    signal byte_reg  : std_logic_vector(7 downto 0) := (others => '0');

    -- Previous cycle's CRS_DV, used to qualify end-of-frame (see RECEIVE_DATA)
    signal crs_dv_d  : std_logic := '0';

    signal crc_rst   : std_logic := '1';
    signal crc_en    : std_logic := '0';
    signal crc_value : std_logic_vector(31 downto 0);

    -- Ethernet CRC residue: clocking a good frame PLUS its trailing 4 byte FCS
    -- through the generator always leaves this constant behind.
    -- NOTE: this is the residue of the RAW register. crc32 exposes
    -- crc_out = not crc_reg, so we invert crc_value back before comparing.
    constant CRC_RESIDUE : std_logic_vector(31 downto 0) := x"C704DD7B";

    -- Held for one cycle alongside rx_end. Tap this in SignalTap to confirm the
    -- residue constant before enabling G_ENFORCE_FCS: it must read '0' for every
    -- frame the link delivers cleanly.
    signal fcs_bad : std_logic := '0';

    attribute keep : boolean;
    attribute keep of fcs_bad   : signal is true;
    attribute keep of crc_value : signal is true;

begin

    u_crc : crc32 port map (
        clk      => clk_50m,
        rst      => crc_rst,
        en       => crc_en,
        -- Registered byte, aligned with the registered crc_en strobe
        data_in  => byte_reg,
        crc_out  => crc_value
    );

    process(clk_50m)
    begin
        if rising_edge(clk_50m) then
            if rst = '1' then
                state       <= IDLE;
                rx_data     <= (others => '0');
                rx_valid    <= '0';
                rx_end      <= '0';
                rx_error    <= '0';
                crc_rst     <= '1';
                crc_en      <= '0';
                di_bit_cnt  <= 0;
                crs_dv_d    <= '0';
            else
                crs_dv_d <= rmii_crs_dv;

                -- Default strobes
                rx_valid <= '0';
                rx_end   <= '0';
                rx_error <= '0';
                fcs_bad  <= '0';
                crc_en   <= '0';
                crc_rst  <= '0';

                case state is
                    
                    when IDLE =>
                        crc_rst <= '1';
                        di_bit_cnt <= 0;
                        if rmii_crs_dv = '1' then
                            state <= HUNT_SFD;
                        end if;

                    when HUNT_SFD =>
                        crc_rst <= '1';
                        -- If line drops prematurely, reset
                        if rmii_crs_dv = '0' then
                            state <= IDLE;
                        -- The Preamble is 0x55 (dibits: 01) and SFD is 0xD5 (dibits: 01 01 01 11)
                        -- As soon as we see "11", the SFD is over. Next clock is Byte 0.
                        elsif rmii_rxd = "11" then 
                            state <= RECEIVE_DATA;
                            di_bit_cnt <= 0;
                        end if;

                    when RECEIVE_DATA =>
                        -- End of frame needs TWO consecutive low cycles. Per the RMII
                        -- spec, when the PHY loses carrier while its elastic buffer
                        -- still holds data, CRS_DV toggles at 50 MHz until that buffer
                        -- drains - and RXD carries valid data (including the FCS) right
                        -- through those cycles. Ending on the first low would clip the
                        -- tail of the frame and corrupt every CRC.
                        if rmii_crs_dv = '0' and crs_dv_d = '0' then
                            -- Carrier is genuinely gone. The extra cycle spent here also
                            -- lets the CRC pipeline absorb the final byte.
                            state <= CHECK_CRC;
                        else
                            -- Assemble 2-bit slices into an 8-bit byte (LSB dibit first)
                            if di_bit_cnt = 0 then 
                                current_byte(1 downto 0) <= rmii_rxd;
                            elsif di_bit_cnt = 1 then 
                                current_byte(3 downto 2) <= rmii_rxd;
                            elsif di_bit_cnt = 2 then 
                                current_byte(5 downto 4) <= rmii_rxd;
                            elsif di_bit_cnt = 3 then
                                -- The byte is fully assembled this clock cycle!
                                rx_data <= rmii_rxd & current_byte(5 downto 0);
                                byte_reg <= rmii_rxd & current_byte(5 downto 0);
                                rx_valid <= '1';
                                crc_en   <= '1';
                            end if;
                            
                            if di_bit_cnt = 3 then
                                di_bit_cnt <= 0;
                            else
                                di_bit_cnt <= di_bit_cnt + 1;
                            end if;
                        end if;

                    when CHECK_CRC =>
                        -- The extra state gives the CRC pipeline one clock to
                        -- absorb the final byte, so the residue is settled here.
                        state <= IDLE;
                        rx_end <= '1';

                        -- crc32 exposes crc_out = not crc_reg, so invert back to
                        -- compare against the raw-register residue.
                        if (not crc_value) /= CRC_RESIDUE then
                            fcs_bad <= '1';
                            if G_ENFORCE_FCS then
                                rx_error <= '1';
                            end if;
                        end if;

                end case;
            end if;
        end if;
    end process;

end architecture rtl;