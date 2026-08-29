library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

-- Shared network helpers.
--
-- The IPv4 header checksum lives here rather than inside udp_tx_core so that
-- top_system can call the SAME function on its own compile-time constants and
-- assert the result. There is no simulator licence on this machine, so those
-- static assertions in top_system are the regression test for this file - if
-- the arithmetic below is ever broken, Analysis & Synthesis fails loudly
-- instead of producing an image that transmits undeliverable packets.
package net_pkg is

    function ipv4_checksum (src : std_logic_vector(31 downto 0);
                            dst : std_logic_vector(31 downto 0);
                            len : std_logic_vector(15 downto 0))
                            return std_logic_vector;

end package net_pkg;


package body net_pkg is

    -- One's complement sum over the ten 16-bit words of a fixed IPv4 header:
    --
    --   4500  <len>  0000  4000  4011  0000  <src hi> <src lo> <dst hi> <dst lo>
    --
    -- with the checksum field itself counted as zero, then complemented. The
    -- constants match the bytes udp_tx_core emits at positions 14..33: version
    -- and IHL 0x45, no DSCP/ECN, identification 0, Don't Fragment, TTL 64,
    -- protocol 17 (UDP). Change any of those bytes and this must change too.
    function ipv4_checksum (src : std_logic_vector(31 downto 0);
                            dst : std_logic_vector(31 downto 0);
                            len : std_logic_vector(15 downto 0))
                            return std_logic_vector is
        variable s : unsigned(31 downto 0) := (others => '0');
    begin
        s := s + 16#4500#;                      -- version / IHL, DSCP / ECN
        s := s + unsigned(len);                 -- total length
        s := s + 16#0000#;                      -- identification
        s := s + 16#4000#;                      -- flags (DF) / fragment offset
        s := s + 16#4011#;                      -- TTL 64, protocol UDP (17)
        s := s + unsigned(src(31 downto 16));
        s := s + unsigned(src(15 downto 0));
        s := s + unsigned(dst(31 downto 16));
        s := s + unsigned(dst(15 downto 0));

        -- Fold the carries back in. Two passes is provably enough: nine terms
        -- each below 2**16 cannot exceed 0x8FFF7, so the first fold lands under
        -- 0x1FFFE and the second clears the last carry.
        s := (s and x"0000FFFF") + (s srl 16);
        s := (s and x"0000FFFF") + (s srl 16);

        return std_logic_vector(not s(15 downto 0));
    end function;

end package body net_pkg;
