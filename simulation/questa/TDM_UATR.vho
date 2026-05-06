-- Copyright (C) 2025  Altera Corporation. All rights reserved.
-- Your use of Altera Corporation's design tools, logic functions 
-- and other software and tools, and any partner logic 
-- functions, and any output files from any of the foregoing 
-- (including device programming or simulation files), and any 
-- associated documentation or information are expressly subject 
-- to the terms and conditions of the Altera Program License 
-- Subscription Agreement, the Altera Quartus Prime License Agreement,
-- the Altera IP License Agreement, or other applicable license
-- agreement, including, without limitation, that your use is for
-- the sole purpose of programming logic devices manufactured by
-- Altera and sold by Altera or its authorized distributors.  Please
-- refer to the Altera Software License Subscription Agreements 
-- on the Quartus Prime software download page.

-- VENDOR "Altera"
-- PROGRAM "Quartus Prime"
-- VERSION "Version 25.1std.0 Build 1129 10/21/2025 SC Lite Edition"

-- DATE "05/06/2026 20:25:46"

-- 
-- Device: Altera EP4CE6E22C8 Package TQFP144
-- 

-- 
-- This VHDL file should be used for Questa Altera FPGA (VHDL) only
-- 

LIBRARY CYCLONEIVE;
LIBRARY IEEE;
USE CYCLONEIVE.CYCLONEIVE_COMPONENTS.ALL;
USE IEEE.STD_LOGIC_1164.ALL;

ENTITY 	hard_block IS
    PORT (
	devoe : IN std_logic;
	devclrn : IN std_logic;
	devpor : IN std_logic
	);
END hard_block;

-- Design Ports Information
-- ~ALTERA_ASDO_DATA1~	=>  Location: PIN_6,	 I/O Standard: 3.3-V LVTTL,	 Current Strength: Default
-- ~ALTERA_FLASH_nCE_nCSO~	=>  Location: PIN_8,	 I/O Standard: 3.3-V LVTTL,	 Current Strength: Default
-- ~ALTERA_DCLK~	=>  Location: PIN_12,	 I/O Standard: 3.3-V LVTTL,	 Current Strength: Default
-- ~ALTERA_DATA0~	=>  Location: PIN_13,	 I/O Standard: 3.3-V LVTTL,	 Current Strength: Default
-- ~ALTERA_nCEO~	=>  Location: PIN_101,	 I/O Standard: 2.5 V,	 Current Strength: 8mA


ARCHITECTURE structure OF hard_block IS
SIGNAL gnd : std_logic := '0';
SIGNAL vcc : std_logic := '1';
SIGNAL unknown : std_logic := 'X';
SIGNAL ww_devoe : std_logic;
SIGNAL ww_devclrn : std_logic;
SIGNAL ww_devpor : std_logic;
SIGNAL \~ALTERA_ASDO_DATA1~~padout\ : std_logic;
SIGNAL \~ALTERA_FLASH_nCE_nCSO~~padout\ : std_logic;
SIGNAL \~ALTERA_DATA0~~padout\ : std_logic;
SIGNAL \~ALTERA_ASDO_DATA1~~ibuf_o\ : std_logic;
SIGNAL \~ALTERA_FLASH_nCE_nCSO~~ibuf_o\ : std_logic;
SIGNAL \~ALTERA_DATA0~~ibuf_o\ : std_logic;

BEGIN

ww_devoe <= devoe;
ww_devclrn <= devclrn;
ww_devpor <= devpor;
END structure;


LIBRARY ALTERA;
LIBRARY CYCLONEIVE;
LIBRARY IEEE;
USE ALTERA.ALTERA_PRIMITIVES_COMPONENTS.ALL;
USE CYCLONEIVE.CYCLONEIVE_COMPONENTS.ALL;
USE IEEE.STD_LOGIC_1164.ALL;

ENTITY 	top_loopback IS
    PORT (
	clk_18m432 : IN std_logic;
	rst_n : IN std_logic;
	pass_led : BUFFER std_logic;
	fail_led : BUFFER std_logic
	);
END top_loopback;

-- Design Ports Information
-- pass_led	=>  Location: PIN_135,	 I/O Standard: 3.3-V LVTTL,	 Current Strength: 8mA
-- fail_led	=>  Location: PIN_136,	 I/O Standard: 3.3-V LVTTL,	 Current Strength: 8mA
-- clk_18m432	=>  Location: PIN_23,	 I/O Standard: 3.3-V LVTTL,	 Current Strength: Default
-- rst_n	=>  Location: PIN_88,	 I/O Standard: 3.3-V LVTTL,	 Current Strength: Default


ARCHITECTURE structure OF top_loopback IS
SIGNAL gnd : std_logic := '0';
SIGNAL vcc : std_logic := '1';
SIGNAL unknown : std_logic := 'X';
SIGNAL devoe : std_logic := '1';
SIGNAL devclrn : std_logic := '1';
SIGNAL devpor : std_logic := '1';
SIGNAL ww_devoe : std_logic;
SIGNAL ww_devclrn : std_logic;
SIGNAL ww_devpor : std_logic;
SIGNAL ww_clk_18m432 : std_logic;
SIGNAL ww_rst_n : std_logic;
SIGNAL ww_pass_led : std_logic;
SIGNAL ww_fail_led : std_logic;
SIGNAL \clk_18m432~inputclkctrl_INCLK_bus\ : std_logic_vector(3 DOWNTO 0);
SIGNAL \rst_n~inputclkctrl_INCLK_bus\ : std_logic_vector(3 DOWNTO 0);
SIGNAL \pass_led~output_o\ : std_logic;
SIGNAL \fail_led~output_o\ : std_logic;
SIGNAL \clk_18m432~input_o\ : std_logic;
SIGNAL \clk_18m432~inputclkctrl_outclk\ : std_logic;
SIGNAL \u_tdm_master|Add0~0_combout\ : std_logic;
SIGNAL \rst_n~input_o\ : std_logic;
SIGNAL \rst_n~inputclkctrl_outclk\ : std_logic;
SIGNAL \u_tdm_master|Add0~1\ : std_logic;
SIGNAL \u_tdm_master|Add0~2_combout\ : std_logic;
SIGNAL \u_tdm_master|Add0~3\ : std_logic;
SIGNAL \u_tdm_master|Add0~4_combout\ : std_logic;
SIGNAL \u_tdm_master|Add0~5\ : std_logic;
SIGNAL \u_tdm_master|Add0~6_combout\ : std_logic;
SIGNAL \u_tdm_master|Equal0~1_combout\ : std_logic;
SIGNAL \u_tdm_master|Add0~7\ : std_logic;
SIGNAL \u_tdm_master|Add0~8_combout\ : std_logic;
SIGNAL \u_tdm_master|Add0~9\ : std_logic;
SIGNAL \u_tdm_master|Add0~10_combout\ : std_logic;
SIGNAL \u_tdm_master|Add0~11\ : std_logic;
SIGNAL \u_tdm_master|Add0~12_combout\ : std_logic;
SIGNAL \u_tdm_master|bit_cnt~1_combout\ : std_logic;
SIGNAL \u_tdm_master|Add0~13\ : std_logic;
SIGNAL \u_tdm_master|Add0~14_combout\ : std_logic;
SIGNAL \u_tdm_master|bit_cnt~0_combout\ : std_logic;
SIGNAL \u_tdm_master|Equal0~0_combout\ : std_logic;
SIGNAL \u_tdm_master|Equal0~2_combout\ : std_logic;
SIGNAL \u_tdm_master|lrclk_reg~q\ : std_logic;
SIGNAL \lrclk_prev~q\ : std_logic;
SIGNAL \startup_ignore[0]~1_combout\ : std_logic;
SIGNAL \startup_ignore[1]~0_combout\ : std_logic;
SIGNAL \fail_reg~0_combout\ : std_logic;
SIGNAL \frame_counter[0]~69_combout\ : std_logic;
SIGNAL \frame_counter[1]~23_combout\ : std_logic;
SIGNAL \frame_counter[1]~24\ : std_logic;
SIGNAL \frame_counter[2]~25_combout\ : std_logic;
SIGNAL \frame_counter[2]~26\ : std_logic;
SIGNAL \frame_counter[3]~27_combout\ : std_logic;
SIGNAL \frame_counter[3]~28\ : std_logic;
SIGNAL \frame_counter[4]~29_combout\ : std_logic;
SIGNAL \frame_counter[4]~30\ : std_logic;
SIGNAL \frame_counter[5]~31_combout\ : std_logic;
SIGNAL \frame_counter[5]~32\ : std_logic;
SIGNAL \frame_counter[6]~33_combout\ : std_logic;
SIGNAL \frame_counter[6]~34\ : std_logic;
SIGNAL \frame_counter[7]~35_combout\ : std_logic;
SIGNAL \frame_counter[7]~36\ : std_logic;
SIGNAL \frame_counter[8]~37_combout\ : std_logic;
SIGNAL \frame_counter[8]~38\ : std_logic;
SIGNAL \frame_counter[9]~39_combout\ : std_logic;
SIGNAL \frame_counter[9]~40\ : std_logic;
SIGNAL \frame_counter[10]~41_combout\ : std_logic;
SIGNAL \frame_counter[10]~42\ : std_logic;
SIGNAL \frame_counter[11]~43_combout\ : std_logic;
SIGNAL \frame_counter[11]~44\ : std_logic;
SIGNAL \frame_counter[12]~45_combout\ : std_logic;
SIGNAL \frame_counter[12]~46\ : std_logic;
SIGNAL \frame_counter[13]~47_combout\ : std_logic;
SIGNAL \frame_counter[13]~48\ : std_logic;
SIGNAL \frame_counter[14]~49_combout\ : std_logic;
SIGNAL \frame_counter[14]~50\ : std_logic;
SIGNAL \frame_counter[15]~51_combout\ : std_logic;
SIGNAL \frame_counter[15]~52\ : std_logic;
SIGNAL \frame_counter[16]~53_combout\ : std_logic;
SIGNAL \frame_counter[16]~54\ : std_logic;
SIGNAL \frame_counter[17]~55_combout\ : std_logic;
SIGNAL \frame_counter[17]~56\ : std_logic;
SIGNAL \frame_counter[18]~57_combout\ : std_logic;
SIGNAL \frame_counter[18]~58\ : std_logic;
SIGNAL \frame_counter[19]~59_combout\ : std_logic;
SIGNAL \frame_counter[19]~60\ : std_logic;
SIGNAL \frame_counter[20]~61_combout\ : std_logic;
SIGNAL \frame_counter[20]~62\ : std_logic;
SIGNAL \frame_counter[21]~63_combout\ : std_logic;
SIGNAL \frame_counter[21]~64\ : std_logic;
SIGNAL \frame_counter[22]~65_combout\ : std_logic;
SIGNAL \tx_shift_reg[3]~feeder_combout\ : std_logic;
SIGNAL \tx_shift_reg~187_combout\ : std_logic;
SIGNAL \tx_shift_reg~186_combout\ : std_logic;
SIGNAL \tx_shift_reg~185_combout\ : std_logic;
SIGNAL \tx_shift_reg~184_combout\ : std_logic;
SIGNAL \tx_shift_reg~183_combout\ : std_logic;
SIGNAL \tx_shift_reg~182_combout\ : std_logic;
SIGNAL \tx_shift_reg~181_combout\ : std_logic;
SIGNAL \tx_shift_reg~180_combout\ : std_logic;
SIGNAL \tx_shift_reg~179_combout\ : std_logic;
SIGNAL \tx_shift_reg~178_combout\ : std_logic;
SIGNAL \tx_shift_reg~177_combout\ : std_logic;
SIGNAL \tx_shift_reg~176_combout\ : std_logic;
SIGNAL \tx_shift_reg~175_combout\ : std_logic;
SIGNAL \tx_shift_reg~174_combout\ : std_logic;
SIGNAL \tx_shift_reg~173_combout\ : std_logic;
SIGNAL \tx_shift_reg~172_combout\ : std_logic;
SIGNAL \tx_shift_reg~171_combout\ : std_logic;
SIGNAL \tx_shift_reg~170_combout\ : std_logic;
SIGNAL \tx_shift_reg~169_combout\ : std_logic;
SIGNAL \tx_shift_reg~168_combout\ : std_logic;
SIGNAL \tx_shift_reg~167_combout\ : std_logic;
SIGNAL \tx_shift_reg~166_combout\ : std_logic;
SIGNAL \tx_shift_reg~165_combout\ : std_logic;
SIGNAL \tx_shift_reg~164_combout\ : std_logic;
SIGNAL \tx_shift_reg~163_combout\ : std_logic;
SIGNAL \tx_shift_reg~162_combout\ : std_logic;
SIGNAL \tx_shift_reg~161_combout\ : std_logic;
SIGNAL \tx_shift_reg~160_combout\ : std_logic;
SIGNAL \tx_shift_reg~159_combout\ : std_logic;
SIGNAL \tx_shift_reg~158_combout\ : std_logic;
SIGNAL \tx_shift_reg~157_combout\ : std_logic;
SIGNAL \tx_shift_reg~156_combout\ : std_logic;
SIGNAL \tx_shift_reg~155_combout\ : std_logic;
SIGNAL \tx_shift_reg~154_combout\ : std_logic;
SIGNAL \tx_shift_reg~153_combout\ : std_logic;
SIGNAL \tx_shift_reg~152_combout\ : std_logic;
SIGNAL \tx_shift_reg~151_combout\ : std_logic;
SIGNAL \tx_shift_reg~150_combout\ : std_logic;
SIGNAL \tx_shift_reg~149_combout\ : std_logic;
SIGNAL \tx_shift_reg~148_combout\ : std_logic;
SIGNAL \tx_shift_reg~147_combout\ : std_logic;
SIGNAL \tx_shift_reg~146_combout\ : std_logic;
SIGNAL \tx_shift_reg~145_combout\ : std_logic;
SIGNAL \tx_shift_reg~144_combout\ : std_logic;
SIGNAL \tx_shift_reg~143_combout\ : std_logic;
SIGNAL \tx_shift_reg~142_combout\ : std_logic;
SIGNAL \tx_shift_reg~141_combout\ : std_logic;
SIGNAL \tx_shift_reg~140_combout\ : std_logic;
SIGNAL \tx_shift_reg~139_combout\ : std_logic;
SIGNAL \tx_shift_reg~138_combout\ : std_logic;
SIGNAL \tx_shift_reg~137_combout\ : std_logic;
SIGNAL \tx_shift_reg~136_combout\ : std_logic;
SIGNAL \tx_shift_reg~135_combout\ : std_logic;
SIGNAL \tx_shift_reg~134_combout\ : std_logic;
SIGNAL \tx_shift_reg~133_combout\ : std_logic;
SIGNAL \tx_shift_reg~132_combout\ : std_logic;
SIGNAL \tx_shift_reg~131_combout\ : std_logic;
SIGNAL \tx_shift_reg~130_combout\ : std_logic;
SIGNAL \tx_shift_reg~129_combout\ : std_logic;
SIGNAL \tx_shift_reg~128_combout\ : std_logic;
SIGNAL \tx_shift_reg~127_combout\ : std_logic;
SIGNAL \tx_shift_reg~126_combout\ : std_logic;
SIGNAL \tx_shift_reg~125_combout\ : std_logic;
SIGNAL \tx_shift_reg~124_combout\ : std_logic;
SIGNAL \tx_shift_reg~123_combout\ : std_logic;
SIGNAL \tx_shift_reg~122_combout\ : std_logic;
SIGNAL \tx_shift_reg~121_combout\ : std_logic;
SIGNAL \tx_shift_reg~120_combout\ : std_logic;
SIGNAL \tx_shift_reg~119_combout\ : std_logic;
SIGNAL \tx_shift_reg~118_combout\ : std_logic;
SIGNAL \tx_shift_reg~117_combout\ : std_logic;
SIGNAL \tx_shift_reg~116_combout\ : std_logic;
SIGNAL \tx_shift_reg~115_combout\ : std_logic;
SIGNAL \tx_shift_reg~114_combout\ : std_logic;
SIGNAL \tx_shift_reg~113_combout\ : std_logic;
SIGNAL \tx_shift_reg~112_combout\ : std_logic;
SIGNAL \tx_shift_reg~111_combout\ : std_logic;
SIGNAL \tx_shift_reg~110_combout\ : std_logic;
SIGNAL \tx_shift_reg~109_combout\ : std_logic;
SIGNAL \tx_shift_reg~108_combout\ : std_logic;
SIGNAL \tx_shift_reg~107_combout\ : std_logic;
SIGNAL \tx_shift_reg~106_combout\ : std_logic;
SIGNAL \tx_shift_reg~105_combout\ : std_logic;
SIGNAL \tx_shift_reg~104_combout\ : std_logic;
SIGNAL \tx_shift_reg~103_combout\ : std_logic;
SIGNAL \tx_shift_reg~102_combout\ : std_logic;
SIGNAL \tx_shift_reg~101_combout\ : std_logic;
SIGNAL \tx_shift_reg~100_combout\ : std_logic;
SIGNAL \tx_shift_reg~99_combout\ : std_logic;
SIGNAL \tx_shift_reg~98_combout\ : std_logic;
SIGNAL \tx_shift_reg~97_combout\ : std_logic;
SIGNAL \tx_shift_reg~96_combout\ : std_logic;
SIGNAL \tx_shift_reg~95_combout\ : std_logic;
SIGNAL \tx_shift_reg~94_combout\ : std_logic;
SIGNAL \tx_shift_reg~93_combout\ : std_logic;
SIGNAL \tx_shift_reg~92_combout\ : std_logic;
SIGNAL \tx_shift_reg~91_combout\ : std_logic;
SIGNAL \tx_shift_reg~90_combout\ : std_logic;
SIGNAL \tx_shift_reg~89_combout\ : std_logic;
SIGNAL \tx_shift_reg~88_combout\ : std_logic;
SIGNAL \tx_shift_reg~87_combout\ : std_logic;
SIGNAL \tx_shift_reg~86_combout\ : std_logic;
SIGNAL \tx_shift_reg~85_combout\ : std_logic;
SIGNAL \tx_shift_reg~84_combout\ : std_logic;
SIGNAL \tx_shift_reg~83_combout\ : std_logic;
SIGNAL \tx_shift_reg~82_combout\ : std_logic;
SIGNAL \tx_shift_reg~81_combout\ : std_logic;
SIGNAL \tx_shift_reg~80_combout\ : std_logic;
SIGNAL \tx_shift_reg~79_combout\ : std_logic;
SIGNAL \tx_shift_reg~78_combout\ : std_logic;
SIGNAL \tx_shift_reg~77_combout\ : std_logic;
SIGNAL \tx_shift_reg~76_combout\ : std_logic;
SIGNAL \tx_shift_reg~75_combout\ : std_logic;
SIGNAL \tx_shift_reg~74_combout\ : std_logic;
SIGNAL \tx_shift_reg~73_combout\ : std_logic;
SIGNAL \tx_shift_reg~72_combout\ : std_logic;
SIGNAL \tx_shift_reg~71_combout\ : std_logic;
SIGNAL \tx_shift_reg~70_combout\ : std_logic;
SIGNAL \tx_shift_reg~69_combout\ : std_logic;
SIGNAL \tx_shift_reg~68_combout\ : std_logic;
SIGNAL \tx_shift_reg~67_combout\ : std_logic;
SIGNAL \tx_shift_reg~66_combout\ : std_logic;
SIGNAL \tx_shift_reg~65_combout\ : std_logic;
SIGNAL \tx_shift_reg~64_combout\ : std_logic;
SIGNAL \tx_shift_reg~63_combout\ : std_logic;
SIGNAL \tx_shift_reg~62_combout\ : std_logic;
SIGNAL \tx_shift_reg~61_combout\ : std_logic;
SIGNAL \tx_shift_reg~60_combout\ : std_logic;
SIGNAL \tx_shift_reg~59_combout\ : std_logic;
SIGNAL \tx_shift_reg~58_combout\ : std_logic;
SIGNAL \tx_shift_reg~57_combout\ : std_logic;
SIGNAL \tx_shift_reg~56_combout\ : std_logic;
SIGNAL \tx_shift_reg~55_combout\ : std_logic;
SIGNAL \tx_shift_reg~54_combout\ : std_logic;
SIGNAL \tx_shift_reg~53_combout\ : std_logic;
SIGNAL \tx_shift_reg~52_combout\ : std_logic;
SIGNAL \tx_shift_reg~51_combout\ : std_logic;
SIGNAL \tx_shift_reg~50_combout\ : std_logic;
SIGNAL \tx_shift_reg~49_combout\ : std_logic;
SIGNAL \tx_shift_reg~48_combout\ : std_logic;
SIGNAL \tx_shift_reg~47_combout\ : std_logic;
SIGNAL \tx_shift_reg~46_combout\ : std_logic;
SIGNAL \tx_shift_reg~45_combout\ : std_logic;
SIGNAL \tx_shift_reg~44_combout\ : std_logic;
SIGNAL \tx_shift_reg~43_combout\ : std_logic;
SIGNAL \tx_shift_reg~42_combout\ : std_logic;
SIGNAL \tx_shift_reg~41_combout\ : std_logic;
SIGNAL \tx_shift_reg~40_combout\ : std_logic;
SIGNAL \tx_shift_reg~39_combout\ : std_logic;
SIGNAL \tx_shift_reg~38_combout\ : std_logic;
SIGNAL \tx_shift_reg~37_combout\ : std_logic;
SIGNAL \tx_shift_reg~36_combout\ : std_logic;
SIGNAL \tx_shift_reg~35_combout\ : std_logic;
SIGNAL \tx_shift_reg~34_combout\ : std_logic;
SIGNAL \tx_shift_reg~33_combout\ : std_logic;
SIGNAL \tx_shift_reg~32_combout\ : std_logic;
SIGNAL \tx_shift_reg~31_combout\ : std_logic;
SIGNAL \tx_shift_reg~30_combout\ : std_logic;
SIGNAL \tx_shift_reg~29_combout\ : std_logic;
SIGNAL \tx_shift_reg~28_combout\ : std_logic;
SIGNAL \tx_shift_reg~27_combout\ : std_logic;
SIGNAL \tx_shift_reg~26_combout\ : std_logic;
SIGNAL \tx_shift_reg~25_combout\ : std_logic;
SIGNAL \tx_shift_reg~24_combout\ : std_logic;
SIGNAL \tx_shift_reg~23_combout\ : std_logic;
SIGNAL \tx_shift_reg~22_combout\ : std_logic;
SIGNAL \tx_shift_reg~21_combout\ : std_logic;
SIGNAL \tx_shift_reg~20_combout\ : std_logic;
SIGNAL \tx_shift_reg~19_combout\ : std_logic;
SIGNAL \tx_shift_reg~18_combout\ : std_logic;
SIGNAL \tx_shift_reg~17_combout\ : std_logic;
SIGNAL \tx_shift_reg~16_combout\ : std_logic;
SIGNAL \tx_shift_reg~15_combout\ : std_logic;
SIGNAL \tx_shift_reg~14_combout\ : std_logic;
SIGNAL \tx_shift_reg~13_combout\ : std_logic;
SIGNAL \tx_shift_reg~12_combout\ : std_logic;
SIGNAL \tx_shift_reg~11_combout\ : std_logic;
SIGNAL \tx_shift_reg~10_combout\ : std_logic;
SIGNAL \tx_shift_reg~9_combout\ : std_logic;
SIGNAL \tx_shift_reg~8_combout\ : std_logic;
SIGNAL \tx_shift_reg~7_combout\ : std_logic;
SIGNAL \tx_shift_reg~6_combout\ : std_logic;
SIGNAL \tx_shift_reg~5_combout\ : std_logic;
SIGNAL \tx_shift_reg~4_combout\ : std_logic;
SIGNAL \tx_shift_reg~3_combout\ : std_logic;
SIGNAL \tx_shift_reg~2_combout\ : std_logic;
SIGNAL \tx_shift_reg~1_combout\ : std_logic;
SIGNAL \frame_counter[22]~66\ : std_logic;
SIGNAL \frame_counter[23]~67_combout\ : std_logic;
SIGNAL \tx_shift_reg~0_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[0]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[1]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[2]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[4]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[6]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[7]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[8]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[9]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[13]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[14]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[15]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[22]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[23]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[25]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[26]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[27]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[28]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[29]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[30]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[31]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[32]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[33]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[35]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[38]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[39]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[40]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[41]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[42]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[43]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[44]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[47]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[48]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[49]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[52]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[53]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[54]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[55]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[58]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[59]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[60]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[62]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[63]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[65]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[66]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[67]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[68]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[69]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[70]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[71]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[74]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[75]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[76]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[77]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[79]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[80]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[81]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[82]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[83]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[84]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[85]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[86]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[87]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[89]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[90]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[91]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[96]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[99]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[102]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[103]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[104]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[105]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[106]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[107]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[108]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[110]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[111]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[112]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[113]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[116]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[118]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[119]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[120]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[121]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[122]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[123]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[124]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[126]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[128]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[129]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[130]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[132]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[135]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[136]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[137]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[140]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[142]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[143]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[144]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[145]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[146]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[147]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[151]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[154]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[155]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[156]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[157]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[158]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[159]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[160]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[161]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[162]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[163]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[164]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[165]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[166]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[171]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[172]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[173]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[174]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[175]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[179]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[180]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[181]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[183]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[185]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[187]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[188]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|lrclk_prev~q\ : std_logic;
SIGNAL \u_tdm_rx|process_0~0_combout\ : std_logic;
SIGNAL \Add2~21_combout\ : std_logic;
SIGNAL \expected_count[0]~24_combout\ : std_logic;
SIGNAL \process_1~72_combout\ : std_logic;
SIGNAL \Add2~1_combout\ : std_logic;
SIGNAL \expected_count[0]~25\ : std_logic;
SIGNAL \expected_count[1]~26_combout\ : std_logic;
SIGNAL \Add2~0_combout\ : std_logic;
SIGNAL \expected_count[1]~27\ : std_logic;
SIGNAL \expected_count[2]~28_combout\ : std_logic;
SIGNAL \Add2~3_combout\ : std_logic;
SIGNAL \expected_count[2]~29\ : std_logic;
SIGNAL \expected_count[3]~30_combout\ : std_logic;
SIGNAL \Add2~2_combout\ : std_logic;
SIGNAL \expected_count[3]~31\ : std_logic;
SIGNAL \expected_count[4]~32_combout\ : std_logic;
SIGNAL \Add2~5_combout\ : std_logic;
SIGNAL \expected_count[4]~33\ : std_logic;
SIGNAL \expected_count[5]~34_combout\ : std_logic;
SIGNAL \Add2~4_combout\ : std_logic;
SIGNAL \expected_count[5]~35\ : std_logic;
SIGNAL \expected_count[6]~36_combout\ : std_logic;
SIGNAL \Add2~7_combout\ : std_logic;
SIGNAL \expected_count[6]~37\ : std_logic;
SIGNAL \expected_count[7]~38_combout\ : std_logic;
SIGNAL \Add2~6_combout\ : std_logic;
SIGNAL \expected_count[7]~39\ : std_logic;
SIGNAL \expected_count[8]~40_combout\ : std_logic;
SIGNAL \Add2~9_combout\ : std_logic;
SIGNAL \expected_count[8]~41\ : std_logic;
SIGNAL \expected_count[9]~42_combout\ : std_logic;
SIGNAL \Add2~8_combout\ : std_logic;
SIGNAL \expected_count[9]~43\ : std_logic;
SIGNAL \expected_count[10]~44_combout\ : std_logic;
SIGNAL \Add2~11_combout\ : std_logic;
SIGNAL \expected_count[10]~45\ : std_logic;
SIGNAL \expected_count[11]~46_combout\ : std_logic;
SIGNAL \Add2~10_combout\ : std_logic;
SIGNAL \expected_count[11]~47\ : std_logic;
SIGNAL \expected_count[12]~48_combout\ : std_logic;
SIGNAL \Add2~13_combout\ : std_logic;
SIGNAL \expected_count[12]~49\ : std_logic;
SIGNAL \expected_count[13]~50_combout\ : std_logic;
SIGNAL \Add2~12_combout\ : std_logic;
SIGNAL \expected_count[13]~51\ : std_logic;
SIGNAL \expected_count[14]~52_combout\ : std_logic;
SIGNAL \Add2~15_combout\ : std_logic;
SIGNAL \expected_count[14]~53\ : std_logic;
SIGNAL \expected_count[15]~54_combout\ : std_logic;
SIGNAL \Add2~14_combout\ : std_logic;
SIGNAL \expected_count[15]~55\ : std_logic;
SIGNAL \expected_count[16]~56_combout\ : std_logic;
SIGNAL \Add2~17_combout\ : std_logic;
SIGNAL \expected_count[16]~57\ : std_logic;
SIGNAL \expected_count[17]~58_combout\ : std_logic;
SIGNAL \Add2~16_combout\ : std_logic;
SIGNAL \expected_count[17]~59\ : std_logic;
SIGNAL \expected_count[18]~60_combout\ : std_logic;
SIGNAL \Add2~19_combout\ : std_logic;
SIGNAL \expected_count[18]~61\ : std_logic;
SIGNAL \expected_count[19]~62_combout\ : std_logic;
SIGNAL \Add2~18_combout\ : std_logic;
SIGNAL \expected_count[19]~63\ : std_logic;
SIGNAL \expected_count[20]~64_combout\ : std_logic;
SIGNAL \Add2~20_combout\ : std_logic;
SIGNAL \expected_count[20]~65\ : std_logic;
SIGNAL \expected_count[21]~66_combout\ : std_logic;
SIGNAL \process_1~12_combout\ : std_logic;
SIGNAL \process_1~10_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[190]~feeder_combout\ : std_logic;
SIGNAL \Add2~23_combout\ : std_logic;
SIGNAL \expected_count[21]~67\ : std_logic;
SIGNAL \expected_count[22]~68_combout\ : std_logic;
SIGNAL \u_tdm_rx|shift_reg[191]~feeder_combout\ : std_logic;
SIGNAL \Add2~22_combout\ : std_logic;
SIGNAL \expected_count[22]~69\ : std_logic;
SIGNAL \expected_count[23]~70_combout\ : std_logic;
SIGNAL \process_1~13_combout\ : std_logic;
SIGNAL \process_1~11_combout\ : std_logic;
SIGNAL \process_1~14_combout\ : std_logic;
SIGNAL \process_1~3_combout\ : std_logic;
SIGNAL \process_1~2_combout\ : std_logic;
SIGNAL \process_1~0_combout\ : std_logic;
SIGNAL \process_1~1_combout\ : std_logic;
SIGNAL \process_1~4_combout\ : std_logic;
SIGNAL \process_1~7_combout\ : std_logic;
SIGNAL \process_1~6_combout\ : std_logic;
SIGNAL \process_1~8_combout\ : std_logic;
SIGNAL \process_1~5_combout\ : std_logic;
SIGNAL \process_1~9_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[160]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[162]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[161]~feeder_combout\ : std_logic;
SIGNAL \process_1~16_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[152]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[153]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[154]~feeder_combout\ : std_logic;
SIGNAL \process_1~18_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[157]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[158]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[159]~feeder_combout\ : std_logic;
SIGNAL \process_1~17_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[167]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[165]~feeder_combout\ : std_logic;
SIGNAL \process_1~15_combout\ : std_logic;
SIGNAL \process_1~19_combout\ : std_logic;
SIGNAL \process_1~20_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[13]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[14]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[12]~feeder_combout\ : std_logic;
SIGNAL \process_1~65_combout\ : std_logic;
SIGNAL \process_1~64_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[21]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[22]~feeder_combout\ : std_logic;
SIGNAL \process_1~63_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[8]~feeder_combout\ : std_logic;
SIGNAL \process_1~66_combout\ : std_logic;
SIGNAL \process_1~67_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[5]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[6]~feeder_combout\ : std_logic;
SIGNAL \process_1~68_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[0]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[3]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[1]~feeder_combout\ : std_logic;
SIGNAL \process_1~69_combout\ : std_logic;
SIGNAL \process_1~70_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[105]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[106]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[104]~feeder_combout\ : std_logic;
SIGNAL \process_1~34_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[118]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[117]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[119]~feeder_combout\ : std_logic;
SIGNAL \process_1~31_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[111]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[109]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[110]~feeder_combout\ : std_logic;
SIGNAL \process_1~33_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[112]~feeder_combout\ : std_logic;
SIGNAL \process_1~32_combout\ : std_logic;
SIGNAL \process_1~35_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[98]~feeder_combout\ : std_logic;
SIGNAL \process_1~37_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[88]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[90]~feeder_combout\ : std_logic;
SIGNAL \process_1~39_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[95]~feeder_combout\ : std_logic;
SIGNAL \process_1~38_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[102]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[103]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[101]~feeder_combout\ : std_logic;
SIGNAL \process_1~36_combout\ : std_logic;
SIGNAL \process_1~40_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[150]~feeder_combout\ : std_logic;
SIGNAL \process_1~21_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[141]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[142]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[143]~feeder_combout\ : std_logic;
SIGNAL \process_1~23_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[144]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[146]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[145]~feeder_combout\ : std_logic;
SIGNAL \process_1~22_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[136]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[139]~feeder_combout\ : std_logic;
SIGNAL \process_1~24_combout\ : std_logic;
SIGNAL \process_1~25_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[135]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[134]~feeder_combout\ : std_logic;
SIGNAL \process_1~26_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[120]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[123]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[121]~feeder_combout\ : std_logic;
SIGNAL \process_1~29_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[125]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[127]~feeder_combout\ : std_logic;
SIGNAL \process_1~28_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[129]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[131]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[128]~feeder_combout\ : std_logic;
SIGNAL \process_1~27_combout\ : std_logic;
SIGNAL \process_1~30_combout\ : std_logic;
SIGNAL \process_1~41_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[69]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[70]~feeder_combout\ : std_logic;
SIGNAL \process_1~47_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[61]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[62]~feeder_combout\ : std_logic;
SIGNAL \process_1~49_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[67]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[65]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[66]~feeder_combout\ : std_logic;
SIGNAL \process_1~48_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[57]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[59]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[58]~feeder_combout\ : std_logic;
SIGNAL \process_1~50_combout\ : std_logic;
SIGNAL \process_1~51_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[37]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[39]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[38]~feeder_combout\ : std_logic;
SIGNAL \process_1~57_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[30]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[29]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[31]~feeder_combout\ : std_logic;
SIGNAL \process_1~59_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[35]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[34]~feeder_combout\ : std_logic;
SIGNAL \process_1~58_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[26]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[25]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[27]~feeder_combout\ : std_logic;
SIGNAL \process_1~60_combout\ : std_logic;
SIGNAL \process_1~61_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[84]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[86]~feeder_combout\ : std_logic;
SIGNAL \process_1~42_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[75]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[74]~feeder_combout\ : std_logic;
SIGNAL \process_1~45_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[82]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[83]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[80]~feeder_combout\ : std_logic;
SIGNAL \process_1~43_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[76]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[79]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[78]~feeder_combout\ : std_logic;
SIGNAL \process_1~44_combout\ : std_logic;
SIGNAL \process_1~46_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[47]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[46]~feeder_combout\ : std_logic;
SIGNAL \process_1~54_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[43]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[41]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[42]~feeder_combout\ : std_logic;
SIGNAL \process_1~55_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[51]~feeder_combout\ : std_logic;
SIGNAL \process_1~53_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[54]~feeder_combout\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out[53]~feeder_combout\ : std_logic;
SIGNAL \process_1~52_combout\ : std_logic;
SIGNAL \process_1~56_combout\ : std_logic;
SIGNAL \process_1~62_combout\ : std_logic;
SIGNAL \process_1~71_combout\ : std_logic;
SIGNAL \match_cnt[0]~7_combout\ : std_logic;
SIGNAL \match_cnt[1]~3_combout\ : std_logic;
SIGNAL \match_cnt[1]~4_combout\ : std_logic;
SIGNAL \match_cnt[1]~6_combout\ : std_logic;
SIGNAL \match_cnt[2]~5_combout\ : std_logic;
SIGNAL \match_cnt[3]~1_combout\ : std_logic;
SIGNAL \match_cnt[3]~2_combout\ : std_logic;
SIGNAL \match_cnt[3]~0_combout\ : std_logic;
SIGNAL \pass_reg~0_combout\ : std_logic;
SIGNAL \pass_reg~q\ : std_logic;
SIGNAL \fail_reg~1_combout\ : std_logic;
SIGNAL \fail_reg~q\ : std_logic;
SIGNAL \u_tdm_rx|ch_data_out\ : std_logic_vector(191 DOWNTO 0);
SIGNAL expected_count : std_logic_vector(23 DOWNTO 0);
SIGNAL \u_tdm_rx|shift_reg\ : std_logic_vector(191 DOWNTO 0);
SIGNAL frame_counter : std_logic_vector(23 DOWNTO 0);
SIGNAL match_cnt : std_logic_vector(3 DOWNTO 0);
SIGNAL startup_ignore : std_logic_vector(1 DOWNTO 0);
SIGNAL tx_shift_reg : std_logic_vector(191 DOWNTO 0);
SIGNAL \u_tdm_master|bit_cnt\ : std_logic_vector(7 DOWNTO 0);
SIGNAL \ALT_INV_clk_18m432~inputclkctrl_outclk\ : std_logic;

COMPONENT hard_block
    PORT (
	devoe : IN std_logic;
	devclrn : IN std_logic;
	devpor : IN std_logic);
END COMPONENT;

BEGIN

ww_clk_18m432 <= clk_18m432;
ww_rst_n <= rst_n;
pass_led <= ww_pass_led;
fail_led <= ww_fail_led;
ww_devoe <= devoe;
ww_devclrn <= devclrn;
ww_devpor <= devpor;

\clk_18m432~inputclkctrl_INCLK_bus\ <= (vcc & vcc & vcc & \clk_18m432~input_o\);

\rst_n~inputclkctrl_INCLK_bus\ <= (vcc & vcc & vcc & \rst_n~input_o\);
\ALT_INV_clk_18m432~inputclkctrl_outclk\ <= NOT \clk_18m432~inputclkctrl_outclk\;
auto_generated_inst : hard_block
PORT MAP (
	devoe => ww_devoe,
	devclrn => ww_devclrn,
	devpor => ww_devpor);

-- Location: IOOBUF_X11_Y24_N16
\pass_led~output\ : cycloneive_io_obuf
-- pragma translate_off
GENERIC MAP (
	bus_hold => "false",
	open_drain_output => "false")
-- pragma translate_on
PORT MAP (
	i => \pass_reg~q\,
	devoe => ww_devoe,
	o => \pass_led~output_o\);

-- Location: IOOBUF_X9_Y24_N9
\fail_led~output\ : cycloneive_io_obuf
-- pragma translate_off
GENERIC MAP (
	bus_hold => "false",
	open_drain_output => "false")
-- pragma translate_on
PORT MAP (
	i => \fail_reg~q\,
	devoe => ww_devoe,
	o => \fail_led~output_o\);

-- Location: IOIBUF_X0_Y11_N8
\clk_18m432~input\ : cycloneive_io_ibuf
-- pragma translate_off
GENERIC MAP (
	bus_hold => "false",
	simulate_z_as => "z")
-- pragma translate_on
PORT MAP (
	i => ww_clk_18m432,
	o => \clk_18m432~input_o\);

-- Location: CLKCTRL_G2
\clk_18m432~inputclkctrl\ : cycloneive_clkctrl
-- pragma translate_off
GENERIC MAP (
	clock_type => "global clock",
	ena_register_mode => "none")
-- pragma translate_on
PORT MAP (
	inclk => \clk_18m432~inputclkctrl_INCLK_bus\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	outclk => \clk_18m432~inputclkctrl_outclk\);

-- Location: LCCOMB_X16_Y14_N12
\u_tdm_master|Add0~0\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_master|Add0~0_combout\ = \u_tdm_master|bit_cnt\(0) $ (VCC)
-- \u_tdm_master|Add0~1\ = CARRY(\u_tdm_master|bit_cnt\(0))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0101010110101010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|bit_cnt\(0),
	datad => VCC,
	combout => \u_tdm_master|Add0~0_combout\,
	cout => \u_tdm_master|Add0~1\);

-- Location: IOIBUF_X34_Y12_N22
\rst_n~input\ : cycloneive_io_ibuf
-- pragma translate_off
GENERIC MAP (
	bus_hold => "false",
	simulate_z_as => "z")
-- pragma translate_on
PORT MAP (
	i => ww_rst_n,
	o => \rst_n~input_o\);

-- Location: CLKCTRL_G8
\rst_n~inputclkctrl\ : cycloneive_clkctrl
-- pragma translate_off
GENERIC MAP (
	clock_type => "global clock",
	ena_register_mode => "none")
-- pragma translate_on
PORT MAP (
	inclk => \rst_n~inputclkctrl_INCLK_bus\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	outclk => \rst_n~inputclkctrl_outclk\);

-- Location: FF_X16_Y14_N13
\u_tdm_master|bit_cnt[0]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_master|Add0~0_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_master|bit_cnt\(0));

-- Location: LCCOMB_X16_Y14_N14
\u_tdm_master|Add0~2\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_master|Add0~2_combout\ = (\u_tdm_master|bit_cnt\(1) & (!\u_tdm_master|Add0~1\)) # (!\u_tdm_master|bit_cnt\(1) & ((\u_tdm_master|Add0~1\) # (GND)))
-- \u_tdm_master|Add0~3\ = CARRY((!\u_tdm_master|Add0~1\) # (!\u_tdm_master|bit_cnt\(1)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0011110000111111",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|bit_cnt\(1),
	datad => VCC,
	cin => \u_tdm_master|Add0~1\,
	combout => \u_tdm_master|Add0~2_combout\,
	cout => \u_tdm_master|Add0~3\);

-- Location: FF_X16_Y14_N15
\u_tdm_master|bit_cnt[1]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_master|Add0~2_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_master|bit_cnt\(1));

-- Location: LCCOMB_X16_Y14_N16
\u_tdm_master|Add0~4\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_master|Add0~4_combout\ = (\u_tdm_master|bit_cnt\(2) & (\u_tdm_master|Add0~3\ $ (GND))) # (!\u_tdm_master|bit_cnt\(2) & (!\u_tdm_master|Add0~3\ & VCC))
-- \u_tdm_master|Add0~5\ = CARRY((\u_tdm_master|bit_cnt\(2) & !\u_tdm_master|Add0~3\))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1100001100001100",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|bit_cnt\(2),
	datad => VCC,
	cin => \u_tdm_master|Add0~3\,
	combout => \u_tdm_master|Add0~4_combout\,
	cout => \u_tdm_master|Add0~5\);

-- Location: FF_X16_Y14_N17
\u_tdm_master|bit_cnt[2]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_master|Add0~4_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_master|bit_cnt\(2));

-- Location: LCCOMB_X16_Y14_N18
\u_tdm_master|Add0~6\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_master|Add0~6_combout\ = (\u_tdm_master|bit_cnt\(3) & (!\u_tdm_master|Add0~5\)) # (!\u_tdm_master|bit_cnt\(3) & ((\u_tdm_master|Add0~5\) # (GND)))
-- \u_tdm_master|Add0~7\ = CARRY((!\u_tdm_master|Add0~5\) # (!\u_tdm_master|bit_cnt\(3)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0011110000111111",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|bit_cnt\(3),
	datad => VCC,
	cin => \u_tdm_master|Add0~5\,
	combout => \u_tdm_master|Add0~6_combout\,
	cout => \u_tdm_master|Add0~7\);

-- Location: FF_X16_Y14_N19
\u_tdm_master|bit_cnt[3]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_master|Add0~6_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_master|bit_cnt\(3));

-- Location: LCCOMB_X16_Y14_N0
\u_tdm_master|Equal0~1\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_master|Equal0~1_combout\ = (\u_tdm_master|bit_cnt\(0) & (\u_tdm_master|bit_cnt\(2) & (\u_tdm_master|bit_cnt\(1) & \u_tdm_master|bit_cnt\(3))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1000000000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|bit_cnt\(0),
	datab => \u_tdm_master|bit_cnt\(2),
	datac => \u_tdm_master|bit_cnt\(1),
	datad => \u_tdm_master|bit_cnt\(3),
	combout => \u_tdm_master|Equal0~1_combout\);

-- Location: LCCOMB_X16_Y14_N20
\u_tdm_master|Add0~8\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_master|Add0~8_combout\ = (\u_tdm_master|bit_cnt\(4) & (\u_tdm_master|Add0~7\ $ (GND))) # (!\u_tdm_master|bit_cnt\(4) & (!\u_tdm_master|Add0~7\ & VCC))
-- \u_tdm_master|Add0~9\ = CARRY((\u_tdm_master|bit_cnt\(4) & !\u_tdm_master|Add0~7\))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1100001100001100",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|bit_cnt\(4),
	datad => VCC,
	cin => \u_tdm_master|Add0~7\,
	combout => \u_tdm_master|Add0~8_combout\,
	cout => \u_tdm_master|Add0~9\);

-- Location: FF_X16_Y14_N21
\u_tdm_master|bit_cnt[4]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_master|Add0~8_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_master|bit_cnt\(4));

-- Location: LCCOMB_X16_Y14_N22
\u_tdm_master|Add0~10\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_master|Add0~10_combout\ = (\u_tdm_master|bit_cnt\(5) & (!\u_tdm_master|Add0~9\)) # (!\u_tdm_master|bit_cnt\(5) & ((\u_tdm_master|Add0~9\) # (GND)))
-- \u_tdm_master|Add0~11\ = CARRY((!\u_tdm_master|Add0~9\) # (!\u_tdm_master|bit_cnt\(5)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0101101001011111",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|bit_cnt\(5),
	datad => VCC,
	cin => \u_tdm_master|Add0~9\,
	combout => \u_tdm_master|Add0~10_combout\,
	cout => \u_tdm_master|Add0~11\);

-- Location: FF_X16_Y14_N23
\u_tdm_master|bit_cnt[5]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_master|Add0~10_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_master|bit_cnt\(5));

-- Location: LCCOMB_X16_Y14_N24
\u_tdm_master|Add0~12\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_master|Add0~12_combout\ = (\u_tdm_master|bit_cnt\(6) & (\u_tdm_master|Add0~11\ $ (GND))) # (!\u_tdm_master|bit_cnt\(6) & (!\u_tdm_master|Add0~11\ & VCC))
-- \u_tdm_master|Add0~13\ = CARRY((\u_tdm_master|bit_cnt\(6) & !\u_tdm_master|Add0~11\))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1100001100001100",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|bit_cnt\(6),
	datad => VCC,
	cin => \u_tdm_master|Add0~11\,
	combout => \u_tdm_master|Add0~12_combout\,
	cout => \u_tdm_master|Add0~13\);

-- Location: LCCOMB_X16_Y14_N28
\u_tdm_master|bit_cnt~1\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_master|bit_cnt~1_combout\ = (\u_tdm_master|Add0~12_combout\ & ((!\u_tdm_master|Equal0~1_combout\) # (!\u_tdm_master|Equal0~0_combout\)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0111011100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|Equal0~0_combout\,
	datab => \u_tdm_master|Equal0~1_combout\,
	datad => \u_tdm_master|Add0~12_combout\,
	combout => \u_tdm_master|bit_cnt~1_combout\);

-- Location: FF_X16_Y14_N29
\u_tdm_master|bit_cnt[6]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_master|bit_cnt~1_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_master|bit_cnt\(6));

-- Location: LCCOMB_X16_Y14_N26
\u_tdm_master|Add0~14\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_master|Add0~14_combout\ = \u_tdm_master|Add0~13\ $ (\u_tdm_master|bit_cnt\(7))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000111111110000",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_master|bit_cnt\(7),
	cin => \u_tdm_master|Add0~13\,
	combout => \u_tdm_master|Add0~14_combout\);

-- Location: LCCOMB_X16_Y14_N10
\u_tdm_master|bit_cnt~0\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_master|bit_cnt~0_combout\ = (\u_tdm_master|Add0~14_combout\ & ((!\u_tdm_master|Equal0~1_combout\) # (!\u_tdm_master|Equal0~0_combout\)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0101000011110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|Equal0~0_combout\,
	datac => \u_tdm_master|Add0~14_combout\,
	datad => \u_tdm_master|Equal0~1_combout\,
	combout => \u_tdm_master|bit_cnt~0_combout\);

-- Location: FF_X16_Y14_N11
\u_tdm_master|bit_cnt[7]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_master|bit_cnt~0_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_master|bit_cnt\(7));

-- Location: LCCOMB_X16_Y14_N6
\u_tdm_master|Equal0~0\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_master|Equal0~0_combout\ = (\u_tdm_master|bit_cnt\(7) & (!\u_tdm_master|bit_cnt\(6) & (\u_tdm_master|bit_cnt\(5) & \u_tdm_master|bit_cnt\(4))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0010000000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|bit_cnt\(7),
	datab => \u_tdm_master|bit_cnt\(6),
	datac => \u_tdm_master|bit_cnt\(5),
	datad => \u_tdm_master|bit_cnt\(4),
	combout => \u_tdm_master|Equal0~0_combout\);

-- Location: LCCOMB_X16_Y14_N8
\u_tdm_master|Equal0~2\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_master|Equal0~2_combout\ = (\u_tdm_master|Equal0~0_combout\ & \u_tdm_master|Equal0~1_combout\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1010101000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|Equal0~0_combout\,
	datad => \u_tdm_master|Equal0~1_combout\,
	combout => \u_tdm_master|Equal0~2_combout\);

-- Location: FF_X16_Y14_N9
\u_tdm_master|lrclk_reg\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_master|Equal0~2_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_master|lrclk_reg~q\);

-- Location: FF_X18_Y12_N17
lrclk_prev : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_master|lrclk_reg~q\,
	sload => VCC,
	ena => \rst_n~input_o\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \lrclk_prev~q\);

-- Location: LCCOMB_X18_Y12_N30
\startup_ignore[0]~1\ : cycloneive_lcell_comb
-- Equation(s):
-- \startup_ignore[0]~1_combout\ = startup_ignore(0) $ (((!\u_tdm_master|lrclk_reg~q\ & (!startup_ignore(1) & \lrclk_prev~q\))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1110000111110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datab => startup_ignore(1),
	datac => startup_ignore(0),
	datad => \lrclk_prev~q\,
	combout => \startup_ignore[0]~1_combout\);

-- Location: FF_X18_Y12_N31
\startup_ignore[0]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \startup_ignore[0]~1_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => startup_ignore(0));

-- Location: LCCOMB_X18_Y12_N18
\startup_ignore[1]~0\ : cycloneive_lcell_comb
-- Equation(s):
-- \startup_ignore[1]~0_combout\ = (startup_ignore(1)) # ((startup_ignore(0) & (!\u_tdm_master|lrclk_reg~q\ & \lrclk_prev~q\)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111001011110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => startup_ignore(0),
	datab => \u_tdm_master|lrclk_reg~q\,
	datac => startup_ignore(1),
	datad => \lrclk_prev~q\,
	combout => \startup_ignore[1]~0_combout\);

-- Location: FF_X18_Y12_N19
\startup_ignore[1]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \startup_ignore[1]~0_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => startup_ignore(1));

-- Location: LCCOMB_X18_Y12_N4
\fail_reg~0\ : cycloneive_lcell_comb
-- Equation(s):
-- \fail_reg~0_combout\ = (startup_ignore(1) & (!\u_tdm_master|lrclk_reg~q\ & \lrclk_prev~q\))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000110000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => startup_ignore(1),
	datac => \u_tdm_master|lrclk_reg~q\,
	datad => \lrclk_prev~q\,
	combout => \fail_reg~0_combout\);

-- Location: LCCOMB_X23_Y11_N0
\frame_counter[0]~69\ : cycloneive_lcell_comb
-- Equation(s):
-- \frame_counter[0]~69_combout\ = frame_counter(0) $ (\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000111111110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => frame_counter(0),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \frame_counter[0]~69_combout\);

-- Location: FF_X23_Y11_N1
\frame_counter[0]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \frame_counter[0]~69_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => frame_counter(0));

-- Location: LCCOMB_X22_Y11_N10
\frame_counter[1]~23\ : cycloneive_lcell_comb
-- Equation(s):
-- \frame_counter[1]~23_combout\ = (frame_counter(1) & (frame_counter(0) $ (VCC))) # (!frame_counter(1) & (frame_counter(0) & VCC))
-- \frame_counter[1]~24\ = CARRY((frame_counter(1) & frame_counter(0)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0110011010001000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => frame_counter(1),
	datab => frame_counter(0),
	datad => VCC,
	combout => \frame_counter[1]~23_combout\,
	cout => \frame_counter[1]~24\);

-- Location: FF_X22_Y11_N11
\frame_counter[1]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \frame_counter[1]~23_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_master|lrclk_reg~q\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => frame_counter(1));

-- Location: LCCOMB_X22_Y11_N12
\frame_counter[2]~25\ : cycloneive_lcell_comb
-- Equation(s):
-- \frame_counter[2]~25_combout\ = (frame_counter(2) & (!\frame_counter[1]~24\)) # (!frame_counter(2) & ((\frame_counter[1]~24\) # (GND)))
-- \frame_counter[2]~26\ = CARRY((!\frame_counter[1]~24\) # (!frame_counter(2)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0101101001011111",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	dataa => frame_counter(2),
	datad => VCC,
	cin => \frame_counter[1]~24\,
	combout => \frame_counter[2]~25_combout\,
	cout => \frame_counter[2]~26\);

-- Location: FF_X22_Y11_N13
\frame_counter[2]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \frame_counter[2]~25_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_master|lrclk_reg~q\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => frame_counter(2));

-- Location: LCCOMB_X22_Y11_N14
\frame_counter[3]~27\ : cycloneive_lcell_comb
-- Equation(s):
-- \frame_counter[3]~27_combout\ = (frame_counter(3) & (\frame_counter[2]~26\ $ (GND))) # (!frame_counter(3) & (!\frame_counter[2]~26\ & VCC))
-- \frame_counter[3]~28\ = CARRY((frame_counter(3) & !\frame_counter[2]~26\))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1100001100001100",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	datab => frame_counter(3),
	datad => VCC,
	cin => \frame_counter[2]~26\,
	combout => \frame_counter[3]~27_combout\,
	cout => \frame_counter[3]~28\);

-- Location: FF_X22_Y11_N15
\frame_counter[3]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \frame_counter[3]~27_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_master|lrclk_reg~q\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => frame_counter(3));

-- Location: LCCOMB_X22_Y11_N16
\frame_counter[4]~29\ : cycloneive_lcell_comb
-- Equation(s):
-- \frame_counter[4]~29_combout\ = (frame_counter(4) & (!\frame_counter[3]~28\)) # (!frame_counter(4) & ((\frame_counter[3]~28\) # (GND)))
-- \frame_counter[4]~30\ = CARRY((!\frame_counter[3]~28\) # (!frame_counter(4)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0011110000111111",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	datab => frame_counter(4),
	datad => VCC,
	cin => \frame_counter[3]~28\,
	combout => \frame_counter[4]~29_combout\,
	cout => \frame_counter[4]~30\);

-- Location: FF_X22_Y11_N17
\frame_counter[4]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \frame_counter[4]~29_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_master|lrclk_reg~q\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => frame_counter(4));

-- Location: LCCOMB_X22_Y11_N18
\frame_counter[5]~31\ : cycloneive_lcell_comb
-- Equation(s):
-- \frame_counter[5]~31_combout\ = (frame_counter(5) & (\frame_counter[4]~30\ $ (GND))) # (!frame_counter(5) & (!\frame_counter[4]~30\ & VCC))
-- \frame_counter[5]~32\ = CARRY((frame_counter(5) & !\frame_counter[4]~30\))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1100001100001100",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	datab => frame_counter(5),
	datad => VCC,
	cin => \frame_counter[4]~30\,
	combout => \frame_counter[5]~31_combout\,
	cout => \frame_counter[5]~32\);

-- Location: FF_X22_Y11_N19
\frame_counter[5]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \frame_counter[5]~31_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_master|lrclk_reg~q\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => frame_counter(5));

-- Location: LCCOMB_X22_Y11_N20
\frame_counter[6]~33\ : cycloneive_lcell_comb
-- Equation(s):
-- \frame_counter[6]~33_combout\ = (frame_counter(6) & (!\frame_counter[5]~32\)) # (!frame_counter(6) & ((\frame_counter[5]~32\) # (GND)))
-- \frame_counter[6]~34\ = CARRY((!\frame_counter[5]~32\) # (!frame_counter(6)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0011110000111111",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	datab => frame_counter(6),
	datad => VCC,
	cin => \frame_counter[5]~32\,
	combout => \frame_counter[6]~33_combout\,
	cout => \frame_counter[6]~34\);

-- Location: FF_X22_Y11_N21
\frame_counter[6]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \frame_counter[6]~33_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_master|lrclk_reg~q\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => frame_counter(6));

-- Location: LCCOMB_X22_Y11_N22
\frame_counter[7]~35\ : cycloneive_lcell_comb
-- Equation(s):
-- \frame_counter[7]~35_combout\ = (frame_counter(7) & (\frame_counter[6]~34\ $ (GND))) # (!frame_counter(7) & (!\frame_counter[6]~34\ & VCC))
-- \frame_counter[7]~36\ = CARRY((frame_counter(7) & !\frame_counter[6]~34\))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1010010100001010",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	dataa => frame_counter(7),
	datad => VCC,
	cin => \frame_counter[6]~34\,
	combout => \frame_counter[7]~35_combout\,
	cout => \frame_counter[7]~36\);

-- Location: FF_X22_Y11_N23
\frame_counter[7]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \frame_counter[7]~35_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_master|lrclk_reg~q\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => frame_counter(7));

-- Location: LCCOMB_X22_Y11_N24
\frame_counter[8]~37\ : cycloneive_lcell_comb
-- Equation(s):
-- \frame_counter[8]~37_combout\ = (frame_counter(8) & (!\frame_counter[7]~36\)) # (!frame_counter(8) & ((\frame_counter[7]~36\) # (GND)))
-- \frame_counter[8]~38\ = CARRY((!\frame_counter[7]~36\) # (!frame_counter(8)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0011110000111111",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	datab => frame_counter(8),
	datad => VCC,
	cin => \frame_counter[7]~36\,
	combout => \frame_counter[8]~37_combout\,
	cout => \frame_counter[8]~38\);

-- Location: FF_X22_Y11_N25
\frame_counter[8]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \frame_counter[8]~37_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_master|lrclk_reg~q\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => frame_counter(8));

-- Location: LCCOMB_X22_Y11_N26
\frame_counter[9]~39\ : cycloneive_lcell_comb
-- Equation(s):
-- \frame_counter[9]~39_combout\ = (frame_counter(9) & (\frame_counter[8]~38\ $ (GND))) # (!frame_counter(9) & (!\frame_counter[8]~38\ & VCC))
-- \frame_counter[9]~40\ = CARRY((frame_counter(9) & !\frame_counter[8]~38\))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1010010100001010",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	dataa => frame_counter(9),
	datad => VCC,
	cin => \frame_counter[8]~38\,
	combout => \frame_counter[9]~39_combout\,
	cout => \frame_counter[9]~40\);

-- Location: FF_X22_Y11_N27
\frame_counter[9]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \frame_counter[9]~39_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_master|lrclk_reg~q\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => frame_counter(9));

-- Location: LCCOMB_X22_Y11_N28
\frame_counter[10]~41\ : cycloneive_lcell_comb
-- Equation(s):
-- \frame_counter[10]~41_combout\ = (frame_counter(10) & (!\frame_counter[9]~40\)) # (!frame_counter(10) & ((\frame_counter[9]~40\) # (GND)))
-- \frame_counter[10]~42\ = CARRY((!\frame_counter[9]~40\) # (!frame_counter(10)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0011110000111111",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	datab => frame_counter(10),
	datad => VCC,
	cin => \frame_counter[9]~40\,
	combout => \frame_counter[10]~41_combout\,
	cout => \frame_counter[10]~42\);

-- Location: FF_X22_Y11_N29
\frame_counter[10]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \frame_counter[10]~41_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_master|lrclk_reg~q\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => frame_counter(10));

-- Location: LCCOMB_X22_Y11_N30
\frame_counter[11]~43\ : cycloneive_lcell_comb
-- Equation(s):
-- \frame_counter[11]~43_combout\ = (frame_counter(11) & (\frame_counter[10]~42\ $ (GND))) # (!frame_counter(11) & (!\frame_counter[10]~42\ & VCC))
-- \frame_counter[11]~44\ = CARRY((frame_counter(11) & !\frame_counter[10]~42\))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1010010100001010",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	dataa => frame_counter(11),
	datad => VCC,
	cin => \frame_counter[10]~42\,
	combout => \frame_counter[11]~43_combout\,
	cout => \frame_counter[11]~44\);

-- Location: FF_X22_Y11_N31
\frame_counter[11]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \frame_counter[11]~43_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_master|lrclk_reg~q\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => frame_counter(11));

-- Location: LCCOMB_X22_Y10_N0
\frame_counter[12]~45\ : cycloneive_lcell_comb
-- Equation(s):
-- \frame_counter[12]~45_combout\ = (frame_counter(12) & (!\frame_counter[11]~44\)) # (!frame_counter(12) & ((\frame_counter[11]~44\) # (GND)))
-- \frame_counter[12]~46\ = CARRY((!\frame_counter[11]~44\) # (!frame_counter(12)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0011110000111111",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	datab => frame_counter(12),
	datad => VCC,
	cin => \frame_counter[11]~44\,
	combout => \frame_counter[12]~45_combout\,
	cout => \frame_counter[12]~46\);

-- Location: FF_X22_Y10_N1
\frame_counter[12]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \frame_counter[12]~45_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_master|lrclk_reg~q\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => frame_counter(12));

-- Location: LCCOMB_X22_Y10_N2
\frame_counter[13]~47\ : cycloneive_lcell_comb
-- Equation(s):
-- \frame_counter[13]~47_combout\ = (frame_counter(13) & (\frame_counter[12]~46\ $ (GND))) # (!frame_counter(13) & (!\frame_counter[12]~46\ & VCC))
-- \frame_counter[13]~48\ = CARRY((frame_counter(13) & !\frame_counter[12]~46\))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1100001100001100",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	datab => frame_counter(13),
	datad => VCC,
	cin => \frame_counter[12]~46\,
	combout => \frame_counter[13]~47_combout\,
	cout => \frame_counter[13]~48\);

-- Location: FF_X22_Y10_N3
\frame_counter[13]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \frame_counter[13]~47_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_master|lrclk_reg~q\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => frame_counter(13));

-- Location: LCCOMB_X22_Y10_N4
\frame_counter[14]~49\ : cycloneive_lcell_comb
-- Equation(s):
-- \frame_counter[14]~49_combout\ = (frame_counter(14) & (!\frame_counter[13]~48\)) # (!frame_counter(14) & ((\frame_counter[13]~48\) # (GND)))
-- \frame_counter[14]~50\ = CARRY((!\frame_counter[13]~48\) # (!frame_counter(14)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0011110000111111",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	datab => frame_counter(14),
	datad => VCC,
	cin => \frame_counter[13]~48\,
	combout => \frame_counter[14]~49_combout\,
	cout => \frame_counter[14]~50\);

-- Location: FF_X22_Y10_N5
\frame_counter[14]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \frame_counter[14]~49_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_master|lrclk_reg~q\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => frame_counter(14));

-- Location: LCCOMB_X22_Y10_N6
\frame_counter[15]~51\ : cycloneive_lcell_comb
-- Equation(s):
-- \frame_counter[15]~51_combout\ = (frame_counter(15) & (\frame_counter[14]~50\ $ (GND))) # (!frame_counter(15) & (!\frame_counter[14]~50\ & VCC))
-- \frame_counter[15]~52\ = CARRY((frame_counter(15) & !\frame_counter[14]~50\))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1010010100001010",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	dataa => frame_counter(15),
	datad => VCC,
	cin => \frame_counter[14]~50\,
	combout => \frame_counter[15]~51_combout\,
	cout => \frame_counter[15]~52\);

-- Location: FF_X22_Y10_N7
\frame_counter[15]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \frame_counter[15]~51_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_master|lrclk_reg~q\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => frame_counter(15));

-- Location: LCCOMB_X22_Y10_N8
\frame_counter[16]~53\ : cycloneive_lcell_comb
-- Equation(s):
-- \frame_counter[16]~53_combout\ = (frame_counter(16) & (!\frame_counter[15]~52\)) # (!frame_counter(16) & ((\frame_counter[15]~52\) # (GND)))
-- \frame_counter[16]~54\ = CARRY((!\frame_counter[15]~52\) # (!frame_counter(16)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0011110000111111",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	datab => frame_counter(16),
	datad => VCC,
	cin => \frame_counter[15]~52\,
	combout => \frame_counter[16]~53_combout\,
	cout => \frame_counter[16]~54\);

-- Location: FF_X22_Y10_N9
\frame_counter[16]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \frame_counter[16]~53_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_master|lrclk_reg~q\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => frame_counter(16));

-- Location: LCCOMB_X22_Y10_N10
\frame_counter[17]~55\ : cycloneive_lcell_comb
-- Equation(s):
-- \frame_counter[17]~55_combout\ = (frame_counter(17) & (\frame_counter[16]~54\ $ (GND))) # (!frame_counter(17) & (!\frame_counter[16]~54\ & VCC))
-- \frame_counter[17]~56\ = CARRY((frame_counter(17) & !\frame_counter[16]~54\))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1010010100001010",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	dataa => frame_counter(17),
	datad => VCC,
	cin => \frame_counter[16]~54\,
	combout => \frame_counter[17]~55_combout\,
	cout => \frame_counter[17]~56\);

-- Location: FF_X22_Y10_N11
\frame_counter[17]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \frame_counter[17]~55_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_master|lrclk_reg~q\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => frame_counter(17));

-- Location: LCCOMB_X22_Y10_N12
\frame_counter[18]~57\ : cycloneive_lcell_comb
-- Equation(s):
-- \frame_counter[18]~57_combout\ = (frame_counter(18) & (!\frame_counter[17]~56\)) # (!frame_counter(18) & ((\frame_counter[17]~56\) # (GND)))
-- \frame_counter[18]~58\ = CARRY((!\frame_counter[17]~56\) # (!frame_counter(18)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0101101001011111",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	dataa => frame_counter(18),
	datad => VCC,
	cin => \frame_counter[17]~56\,
	combout => \frame_counter[18]~57_combout\,
	cout => \frame_counter[18]~58\);

-- Location: FF_X22_Y10_N13
\frame_counter[18]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \frame_counter[18]~57_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_master|lrclk_reg~q\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => frame_counter(18));

-- Location: LCCOMB_X22_Y10_N14
\frame_counter[19]~59\ : cycloneive_lcell_comb
-- Equation(s):
-- \frame_counter[19]~59_combout\ = (frame_counter(19) & (\frame_counter[18]~58\ $ (GND))) # (!frame_counter(19) & (!\frame_counter[18]~58\ & VCC))
-- \frame_counter[19]~60\ = CARRY((frame_counter(19) & !\frame_counter[18]~58\))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1100001100001100",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	datab => frame_counter(19),
	datad => VCC,
	cin => \frame_counter[18]~58\,
	combout => \frame_counter[19]~59_combout\,
	cout => \frame_counter[19]~60\);

-- Location: FF_X22_Y10_N15
\frame_counter[19]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \frame_counter[19]~59_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_master|lrclk_reg~q\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => frame_counter(19));

-- Location: LCCOMB_X22_Y10_N16
\frame_counter[20]~61\ : cycloneive_lcell_comb
-- Equation(s):
-- \frame_counter[20]~61_combout\ = (frame_counter(20) & (!\frame_counter[19]~60\)) # (!frame_counter(20) & ((\frame_counter[19]~60\) # (GND)))
-- \frame_counter[20]~62\ = CARRY((!\frame_counter[19]~60\) # (!frame_counter(20)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0011110000111111",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	datab => frame_counter(20),
	datad => VCC,
	cin => \frame_counter[19]~60\,
	combout => \frame_counter[20]~61_combout\,
	cout => \frame_counter[20]~62\);

-- Location: FF_X22_Y10_N17
\frame_counter[20]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \frame_counter[20]~61_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_master|lrclk_reg~q\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => frame_counter(20));

-- Location: LCCOMB_X22_Y10_N18
\frame_counter[21]~63\ : cycloneive_lcell_comb
-- Equation(s):
-- \frame_counter[21]~63_combout\ = (frame_counter(21) & (\frame_counter[20]~62\ $ (GND))) # (!frame_counter(21) & (!\frame_counter[20]~62\ & VCC))
-- \frame_counter[21]~64\ = CARRY((frame_counter(21) & !\frame_counter[20]~62\))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1100001100001100",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	datab => frame_counter(21),
	datad => VCC,
	cin => \frame_counter[20]~62\,
	combout => \frame_counter[21]~63_combout\,
	cout => \frame_counter[21]~64\);

-- Location: FF_X22_Y10_N19
\frame_counter[21]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \frame_counter[21]~63_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_master|lrclk_reg~q\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => frame_counter(21));

-- Location: LCCOMB_X22_Y10_N20
\frame_counter[22]~65\ : cycloneive_lcell_comb
-- Equation(s):
-- \frame_counter[22]~65_combout\ = (frame_counter(22) & (!\frame_counter[21]~64\)) # (!frame_counter(22) & ((\frame_counter[21]~64\) # (GND)))
-- \frame_counter[22]~66\ = CARRY((!\frame_counter[21]~64\) # (!frame_counter(22)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0011110000111111",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	datab => frame_counter(22),
	datad => VCC,
	cin => \frame_counter[21]~64\,
	combout => \frame_counter[22]~65_combout\,
	cout => \frame_counter[22]~66\);

-- Location: FF_X22_Y10_N21
\frame_counter[22]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \frame_counter[22]~65_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_master|lrclk_reg~q\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => frame_counter(22));

-- Location: LCCOMB_X24_Y10_N30
\tx_shift_reg[3]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg[3]~feeder_combout\ = \u_tdm_master|lrclk_reg~q\

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg[3]~feeder_combout\);

-- Location: FF_X24_Y10_N31
\tx_shift_reg[3]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg[3]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(3));

-- Location: LCCOMB_X24_Y10_N20
\tx_shift_reg~187\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~187_combout\ = (tx_shift_reg(3)) # (\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(3),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~187_combout\);

-- Location: FF_X24_Y10_N21
\tx_shift_reg[4]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~187_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(4));

-- Location: LCCOMB_X24_Y10_N2
\tx_shift_reg~186\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~186_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(4))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0011001100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(4),
	combout => \tx_shift_reg~186_combout\);

-- Location: FF_X24_Y10_N3
\tx_shift_reg[5]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~186_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(5));

-- Location: LCCOMB_X24_Y10_N8
\tx_shift_reg~185\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~185_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(5))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0011001100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(5),
	combout => \tx_shift_reg~185_combout\);

-- Location: FF_X24_Y10_N9
\tx_shift_reg[6]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~185_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(6));

-- Location: LCCOMB_X24_Y10_N14
\tx_shift_reg~184\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~184_combout\ = (tx_shift_reg(6) & !\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000000011110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(6),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~184_combout\);

-- Location: FF_X24_Y10_N15
\tx_shift_reg[7]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~184_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(7));

-- Location: LCCOMB_X24_Y10_N4
\tx_shift_reg~183\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~183_combout\ = (tx_shift_reg(7) & !\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000000011110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(7),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~183_combout\);

-- Location: FF_X24_Y10_N5
\tx_shift_reg[8]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~183_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(8));

-- Location: LCCOMB_X24_Y10_N26
\tx_shift_reg~182\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~182_combout\ = (tx_shift_reg(8) & !\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000000011110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(8),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~182_combout\);

-- Location: FF_X24_Y10_N27
\tx_shift_reg[9]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~182_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(9));

-- Location: LCCOMB_X24_Y10_N16
\tx_shift_reg~181\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~181_combout\ = (tx_shift_reg(9) & !\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000000011110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(9),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~181_combout\);

-- Location: FF_X24_Y10_N17
\tx_shift_reg[10]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~181_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(10));

-- Location: LCCOMB_X24_Y10_N22
\tx_shift_reg~180\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~180_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(10))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111001100",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(10),
	combout => \tx_shift_reg~180_combout\);

-- Location: FF_X24_Y10_N23
\tx_shift_reg[11]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~180_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(11));

-- Location: LCCOMB_X23_Y10_N14
\tx_shift_reg~179\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~179_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(11))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111001100",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(11),
	combout => \tx_shift_reg~179_combout\);

-- Location: FF_X23_Y10_N15
\tx_shift_reg[12]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~179_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(12));

-- Location: LCCOMB_X23_Y12_N22
\tx_shift_reg~178\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~178_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(12))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0101010100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(12),
	combout => \tx_shift_reg~178_combout\);

-- Location: FF_X23_Y12_N23
\tx_shift_reg[13]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~178_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(13));

-- Location: LCCOMB_X22_Y12_N14
\tx_shift_reg~177\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~177_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(13))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0101010100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(13),
	combout => \tx_shift_reg~177_combout\);

-- Location: FF_X22_Y12_N15
\tx_shift_reg[14]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~177_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(14));

-- Location: LCCOMB_X22_Y12_N4
\tx_shift_reg~176\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~176_combout\ = (tx_shift_reg(14) & !\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000000011110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(14),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~176_combout\);

-- Location: FF_X22_Y12_N5
\tx_shift_reg[15]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~176_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(15));

-- Location: LCCOMB_X22_Y12_N18
\tx_shift_reg~175\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~175_combout\ = (tx_shift_reg(15) & !\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000000011110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(15),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~175_combout\);

-- Location: FF_X22_Y12_N19
\tx_shift_reg[16]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~175_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(16));

-- Location: LCCOMB_X22_Y12_N0
\tx_shift_reg~174\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~174_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(16))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0101010100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(16),
	combout => \tx_shift_reg~174_combout\);

-- Location: FF_X22_Y12_N1
\tx_shift_reg[17]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~174_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(17));

-- Location: LCCOMB_X22_Y12_N22
\tx_shift_reg~173\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~173_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(17))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0101010100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(17),
	combout => \tx_shift_reg~173_combout\);

-- Location: FF_X22_Y12_N23
\tx_shift_reg[18]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~173_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(18));

-- Location: LCCOMB_X22_Y12_N20
\tx_shift_reg~172\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~172_combout\ = (tx_shift_reg(18)) # (\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(18),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~172_combout\);

-- Location: FF_X22_Y12_N21
\tx_shift_reg[19]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~172_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(19));

-- Location: LCCOMB_X22_Y12_N10
\tx_shift_reg~171\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~171_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(19))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111110101010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(19),
	combout => \tx_shift_reg~171_combout\);

-- Location: FF_X22_Y12_N11
\tx_shift_reg[20]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~171_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(20));

-- Location: LCCOMB_X22_Y12_N24
\tx_shift_reg~170\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~170_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(20))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0101010100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(20),
	combout => \tx_shift_reg~170_combout\);

-- Location: FF_X22_Y12_N25
\tx_shift_reg[21]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~170_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(21));

-- Location: LCCOMB_X22_Y12_N30
\tx_shift_reg~169\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~169_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(21))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0101010100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(21),
	combout => \tx_shift_reg~169_combout\);

-- Location: FF_X22_Y12_N31
\tx_shift_reg[22]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~169_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(22));

-- Location: LCCOMB_X22_Y12_N28
\tx_shift_reg~168\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~168_combout\ = (tx_shift_reg(22) & !\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000000011110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(22),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~168_combout\);

-- Location: FF_X22_Y12_N29
\tx_shift_reg[23]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~168_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(23));

-- Location: LCCOMB_X22_Y12_N26
\tx_shift_reg~167\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~167_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(23))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111110101010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(23),
	combout => \tx_shift_reg~167_combout\);

-- Location: FF_X22_Y12_N27
\tx_shift_reg[24]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~167_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(24));

-- Location: LCCOMB_X22_Y12_N16
\tx_shift_reg~166\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~166_combout\ = (tx_shift_reg(24)) # (\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(24),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~166_combout\);

-- Location: FF_X22_Y12_N17
\tx_shift_reg[25]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~166_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(25));

-- Location: LCCOMB_X22_Y12_N6
\tx_shift_reg~165\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~165_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(25))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111110101010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(25),
	combout => \tx_shift_reg~165_combout\);

-- Location: FF_X22_Y12_N7
\tx_shift_reg[26]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~165_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(26));

-- Location: LCCOMB_X22_Y12_N12
\tx_shift_reg~164\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~164_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(26))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0101010100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(26),
	combout => \tx_shift_reg~164_combout\);

-- Location: FF_X22_Y12_N13
\tx_shift_reg[27]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~164_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(27));

-- Location: LCCOMB_X22_Y12_N2
\tx_shift_reg~163\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~163_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(27))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0101010100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(27),
	combout => \tx_shift_reg~163_combout\);

-- Location: FF_X22_Y12_N3
\tx_shift_reg[28]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~163_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(28));

-- Location: LCCOMB_X28_Y12_N14
\tx_shift_reg~162\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~162_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(28))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0101010100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(28),
	combout => \tx_shift_reg~162_combout\);

-- Location: FF_X28_Y12_N15
\tx_shift_reg[29]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~162_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(29));

-- Location: LCCOMB_X28_Y12_N28
\tx_shift_reg~161\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~161_combout\ = (tx_shift_reg(29) & !\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000000011110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(29),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~161_combout\);

-- Location: FF_X28_Y12_N29
\tx_shift_reg[30]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~161_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(30));

-- Location: LCCOMB_X28_Y12_N18
\tx_shift_reg~160\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~160_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(30))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0101010100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(30),
	combout => \tx_shift_reg~160_combout\);

-- Location: FF_X28_Y12_N19
\tx_shift_reg[31]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~160_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(31));

-- Location: LCCOMB_X28_Y12_N16
\tx_shift_reg~159\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~159_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(31))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111110101010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(31),
	combout => \tx_shift_reg~159_combout\);

-- Location: FF_X28_Y12_N17
\tx_shift_reg[32]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~159_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(32));

-- Location: LCCOMB_X28_Y12_N30
\tx_shift_reg~158\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~158_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(32))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111110101010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(32),
	combout => \tx_shift_reg~158_combout\);

-- Location: FF_X28_Y12_N31
\tx_shift_reg[33]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~158_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(33));

-- Location: LCCOMB_X28_Y12_N20
\tx_shift_reg~157\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~157_combout\ = (tx_shift_reg(33)) # (\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(33),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~157_combout\);

-- Location: FF_X28_Y12_N21
\tx_shift_reg[34]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~157_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(34));

-- Location: LCCOMB_X28_Y12_N2
\tx_shift_reg~156\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~156_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(34))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0101010100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(34),
	combout => \tx_shift_reg~156_combout\);

-- Location: FF_X28_Y12_N3
\tx_shift_reg[35]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~156_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(35));

-- Location: LCCOMB_X25_Y13_N14
\tx_shift_reg~155\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~155_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(35))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0101000001010000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datac => tx_shift_reg(35),
	combout => \tx_shift_reg~155_combout\);

-- Location: FF_X25_Y13_N15
\tx_shift_reg[36]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~155_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(36));

-- Location: LCCOMB_X25_Y13_N4
\tx_shift_reg~154\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~154_combout\ = (tx_shift_reg(36) & !\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000110000001100",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => tx_shift_reg(36),
	datac => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~154_combout\);

-- Location: FF_X25_Y13_N5
\tx_shift_reg[37]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~154_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(37));

-- Location: LCCOMB_X25_Y13_N10
\tx_shift_reg~153\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~153_combout\ = (tx_shift_reg(37) & !\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000110000001100",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => tx_shift_reg(37),
	datac => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~153_combout\);

-- Location: FF_X25_Y13_N11
\tx_shift_reg[38]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~153_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(38));

-- Location: LCCOMB_X25_Y13_N16
\tx_shift_reg~152\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~152_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(38))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(38),
	combout => \tx_shift_reg~152_combout\);

-- Location: FF_X25_Y13_N17
\tx_shift_reg[39]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~152_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(39));

-- Location: LCCOMB_X25_Y13_N30
\tx_shift_reg~151\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~151_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(39))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(39),
	combout => \tx_shift_reg~151_combout\);

-- Location: FF_X25_Y13_N31
\tx_shift_reg[40]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~151_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(40));

-- Location: LCCOMB_X25_Y13_N28
\tx_shift_reg~150\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~150_combout\ = (tx_shift_reg(40)) # (\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111101011111010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => tx_shift_reg(40),
	datac => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~150_combout\);

-- Location: FF_X25_Y13_N29
\tx_shift_reg[41]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~150_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(41));

-- Location: LCCOMB_X25_Y13_N18
\tx_shift_reg~149\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~149_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(41))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(41),
	combout => \tx_shift_reg~149_combout\);

-- Location: FF_X25_Y13_N19
\tx_shift_reg[42]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~149_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(42));

-- Location: LCCOMB_X25_Y13_N0
\tx_shift_reg~148\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~148_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(42))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(42),
	combout => \tx_shift_reg~148_combout\);

-- Location: FF_X25_Y13_N1
\tx_shift_reg[43]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~148_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(43));

-- Location: LCCOMB_X25_Y13_N6
\tx_shift_reg~147\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~147_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(43))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(43),
	combout => \tx_shift_reg~147_combout\);

-- Location: FF_X25_Y13_N7
\tx_shift_reg[44]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~147_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(44));

-- Location: LCCOMB_X25_Y13_N12
\tx_shift_reg~146\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~146_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(44))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(44),
	combout => \tx_shift_reg~146_combout\);

-- Location: FF_X25_Y13_N13
\tx_shift_reg[45]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~146_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(45));

-- Location: LCCOMB_X25_Y13_N2
\tx_shift_reg~145\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~145_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(45))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(45),
	combout => \tx_shift_reg~145_combout\);

-- Location: FF_X25_Y13_N3
\tx_shift_reg[46]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~145_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(46));

-- Location: LCCOMB_X25_Y13_N8
\tx_shift_reg~144\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~144_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(46))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(46),
	combout => \tx_shift_reg~144_combout\);

-- Location: FF_X25_Y13_N9
\tx_shift_reg[47]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~144_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(47));

-- Location: LCCOMB_X25_Y13_N22
\tx_shift_reg~143\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~143_combout\ = (tx_shift_reg(47) & !\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000110000001100",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => tx_shift_reg(47),
	datac => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~143_combout\);

-- Location: FF_X25_Y13_N23
\tx_shift_reg[48]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~143_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(48));

-- Location: LCCOMB_X25_Y13_N20
\tx_shift_reg~142\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~142_combout\ = (tx_shift_reg(48)) # (\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111101011111010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => tx_shift_reg(48),
	datac => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~142_combout\);

-- Location: FF_X25_Y13_N21
\tx_shift_reg[49]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~142_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(49));

-- Location: LCCOMB_X25_Y13_N26
\tx_shift_reg~141\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~141_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(49))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(49),
	combout => \tx_shift_reg~141_combout\);

-- Location: FF_X25_Y13_N27
\tx_shift_reg[50]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~141_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(50));

-- Location: LCCOMB_X25_Y13_N24
\tx_shift_reg~140\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~140_combout\ = (tx_shift_reg(50) & !\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000101000001010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => tx_shift_reg(50),
	datac => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~140_combout\);

-- Location: FF_X25_Y13_N25
\tx_shift_reg[51]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~140_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(51));

-- Location: LCCOMB_X24_Y13_N24
\tx_shift_reg~139\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~139_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(51))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111001100",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(51),
	combout => \tx_shift_reg~139_combout\);

-- Location: FF_X24_Y13_N25
\tx_shift_reg[52]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~139_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(52));

-- Location: LCCOMB_X24_Y13_N6
\tx_shift_reg~138\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~138_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(52))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111001100",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(52),
	combout => \tx_shift_reg~138_combout\);

-- Location: FF_X24_Y13_N7
\tx_shift_reg[53]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~138_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(53));

-- Location: LCCOMB_X24_Y13_N12
\tx_shift_reg~137\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~137_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(53))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111001100",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(53),
	combout => \tx_shift_reg~137_combout\);

-- Location: FF_X24_Y13_N13
\tx_shift_reg[54]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~137_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(54));

-- Location: LCCOMB_X24_Y13_N10
\tx_shift_reg~136\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~136_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(54))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111001100",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(54),
	combout => \tx_shift_reg~136_combout\);

-- Location: FF_X24_Y13_N11
\tx_shift_reg[55]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~136_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(55));

-- Location: LCCOMB_X24_Y13_N16
\tx_shift_reg~135\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~135_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(55))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0011001100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(55),
	combout => \tx_shift_reg~135_combout\);

-- Location: FF_X24_Y13_N17
\tx_shift_reg[56]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~135_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(56));

-- Location: LCCOMB_X23_Y12_N28
\tx_shift_reg~134\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~134_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(56))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111110101010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(56),
	combout => \tx_shift_reg~134_combout\);

-- Location: FF_X23_Y12_N29
\tx_shift_reg[57]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~134_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(57));

-- Location: LCCOMB_X23_Y12_N18
\tx_shift_reg~133\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~133_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(57))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111110101010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(57),
	combout => \tx_shift_reg~133_combout\);

-- Location: FF_X23_Y12_N19
\tx_shift_reg[58]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~133_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(58));

-- Location: LCCOMB_X23_Y12_N0
\tx_shift_reg~132\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~132_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(58))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0101010100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(58),
	combout => \tx_shift_reg~132_combout\);

-- Location: FF_X23_Y12_N1
\tx_shift_reg[59]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~132_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(59));

-- Location: LCCOMB_X23_Y12_N30
\tx_shift_reg~131\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~131_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(59))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111110101010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(59),
	combout => \tx_shift_reg~131_combout\);

-- Location: FF_X23_Y12_N31
\tx_shift_reg[60]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~131_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(60));

-- Location: LCCOMB_X23_Y12_N4
\tx_shift_reg~130\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~130_combout\ = (tx_shift_reg(60)) # (\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(60),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~130_combout\);

-- Location: FF_X23_Y12_N5
\tx_shift_reg[61]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~130_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(61));

-- Location: LCCOMB_X22_Y12_N8
\tx_shift_reg~129\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~129_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(61))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111110101010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(61),
	combout => \tx_shift_reg~129_combout\);

-- Location: FF_X22_Y12_N9
\tx_shift_reg[62]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~129_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(62));

-- Location: LCCOMB_X23_Y12_N2
\tx_shift_reg~128\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~128_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(62))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111110101010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(62),
	combout => \tx_shift_reg~128_combout\);

-- Location: FF_X23_Y12_N3
\tx_shift_reg[63]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~128_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(63));

-- Location: LCCOMB_X23_Y12_N8
\tx_shift_reg~127\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~127_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(63))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0101010100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(63),
	combout => \tx_shift_reg~127_combout\);

-- Location: FF_X23_Y12_N9
\tx_shift_reg[64]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~127_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(64));

-- Location: LCCOMB_X23_Y12_N14
\tx_shift_reg~126\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~126_combout\ = (tx_shift_reg(64)) # (\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(64),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~126_combout\);

-- Location: FF_X23_Y12_N15
\tx_shift_reg[65]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~126_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(65));

-- Location: LCCOMB_X23_Y12_N12
\tx_shift_reg~125\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~125_combout\ = (tx_shift_reg(65)) # (\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(65),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~125_combout\);

-- Location: FF_X23_Y12_N13
\tx_shift_reg[66]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~125_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(66));

-- Location: LCCOMB_X23_Y12_N10
\tx_shift_reg~124\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~124_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(66))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0101010100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(66),
	combout => \tx_shift_reg~124_combout\);

-- Location: FF_X23_Y12_N11
\tx_shift_reg[67]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~124_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(67));

-- Location: LCCOMB_X23_Y12_N24
\tx_shift_reg~123\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~123_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(67))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111110101010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(67),
	combout => \tx_shift_reg~123_combout\);

-- Location: FF_X23_Y12_N25
\tx_shift_reg[68]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~123_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(68));

-- Location: LCCOMB_X23_Y12_N6
\tx_shift_reg~122\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~122_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(68))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111110101010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(68),
	combout => \tx_shift_reg~122_combout\);

-- Location: FF_X23_Y12_N7
\tx_shift_reg[69]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~122_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(69));

-- Location: LCCOMB_X23_Y12_N20
\tx_shift_reg~121\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~121_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(69))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111110101010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(69),
	combout => \tx_shift_reg~121_combout\);

-- Location: FF_X23_Y12_N21
\tx_shift_reg[70]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~121_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(70));

-- Location: LCCOMB_X23_Y12_N26
\tx_shift_reg~120\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~120_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(70))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111110101010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(70),
	combout => \tx_shift_reg~120_combout\);

-- Location: FF_X23_Y12_N27
\tx_shift_reg[71]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~120_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(71));

-- Location: LCCOMB_X23_Y12_N16
\tx_shift_reg~119\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~119_combout\ = (tx_shift_reg(71)) # (\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(71),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~119_combout\);

-- Location: FF_X23_Y12_N17
\tx_shift_reg[72]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~119_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(72));

-- Location: LCCOMB_X24_Y11_N30
\tx_shift_reg~118\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~118_combout\ = (tx_shift_reg(72) & !\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000000011110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(72),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~118_combout\);

-- Location: FF_X24_Y11_N31
\tx_shift_reg[73]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~118_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(73));

-- Location: LCCOMB_X24_Y11_N4
\tx_shift_reg~117\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~117_combout\ = (tx_shift_reg(73)) # (\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(73),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~117_combout\);

-- Location: FF_X24_Y11_N5
\tx_shift_reg[74]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~117_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(74));

-- Location: LCCOMB_X24_Y11_N26
\tx_shift_reg~116\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~116_combout\ = (tx_shift_reg(74) & !\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000000011110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(74),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~116_combout\);

-- Location: FF_X24_Y11_N27
\tx_shift_reg[75]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~116_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(75));

-- Location: LCCOMB_X24_Y11_N0
\tx_shift_reg~115\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~115_combout\ = (tx_shift_reg(75) & !\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000000011110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(75),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~115_combout\);

-- Location: FF_X24_Y11_N1
\tx_shift_reg[76]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~115_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(76));

-- Location: LCCOMB_X24_Y11_N22
\tx_shift_reg~114\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~114_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(76))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111001100",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(76),
	combout => \tx_shift_reg~114_combout\);

-- Location: FF_X24_Y11_N23
\tx_shift_reg[77]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~114_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(77));

-- Location: LCCOMB_X24_Y11_N28
\tx_shift_reg~113\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~113_combout\ = (tx_shift_reg(77)) # (\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(77),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~113_combout\);

-- Location: FF_X24_Y11_N29
\tx_shift_reg[78]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~113_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(78));

-- Location: LCCOMB_X24_Y11_N18
\tx_shift_reg~112\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~112_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(78))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111001100",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(78),
	combout => \tx_shift_reg~112_combout\);

-- Location: FF_X24_Y11_N19
\tx_shift_reg[79]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~112_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(79));

-- Location: LCCOMB_X24_Y11_N24
\tx_shift_reg~111\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~111_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(79))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111001100",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(79),
	combout => \tx_shift_reg~111_combout\);

-- Location: FF_X24_Y11_N25
\tx_shift_reg[80]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~111_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(80));

-- Location: LCCOMB_X24_Y11_N14
\tx_shift_reg~110\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~110_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(80))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0011001100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(80),
	combout => \tx_shift_reg~110_combout\);

-- Location: FF_X24_Y11_N15
\tx_shift_reg[81]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~110_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(81));

-- Location: LCCOMB_X24_Y11_N12
\tx_shift_reg~109\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~109_combout\ = (tx_shift_reg(81)) # (\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(81),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~109_combout\);

-- Location: FF_X24_Y11_N13
\tx_shift_reg[82]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~109_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(82));

-- Location: LCCOMB_X24_Y11_N10
\tx_shift_reg~108\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~108_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(82))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0011001100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(82),
	combout => \tx_shift_reg~108_combout\);

-- Location: FF_X24_Y11_N11
\tx_shift_reg[83]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~108_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(83));

-- Location: LCCOMB_X24_Y11_N8
\tx_shift_reg~107\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~107_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(83))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0011001100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(83),
	combout => \tx_shift_reg~107_combout\);

-- Location: FF_X24_Y11_N9
\tx_shift_reg[84]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~107_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(84));

-- Location: LCCOMB_X24_Y11_N6
\tx_shift_reg~106\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~106_combout\ = (tx_shift_reg(84)) # (\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(84),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~106_combout\);

-- Location: FF_X24_Y11_N7
\tx_shift_reg[85]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~106_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(85));

-- Location: LCCOMB_X24_Y11_N20
\tx_shift_reg~105\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~105_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(85))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111001100",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(85),
	combout => \tx_shift_reg~105_combout\);

-- Location: FF_X24_Y11_N21
\tx_shift_reg[86]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~105_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(86));

-- Location: LCCOMB_X24_Y11_N2
\tx_shift_reg~104\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~104_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(86))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111001100",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(86),
	combout => \tx_shift_reg~104_combout\);

-- Location: FF_X24_Y11_N3
\tx_shift_reg[87]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~104_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(87));

-- Location: LCCOMB_X24_Y11_N16
\tx_shift_reg~103\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~103_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(87))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111001100",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(87),
	combout => \tx_shift_reg~103_combout\);

-- Location: FF_X24_Y11_N17
\tx_shift_reg[88]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~103_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(88));

-- Location: LCCOMB_X28_Y12_N0
\tx_shift_reg~102\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~102_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(88))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0101010100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(88),
	combout => \tx_shift_reg~102_combout\);

-- Location: FF_X28_Y12_N1
\tx_shift_reg[89]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~102_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(89));

-- Location: LCCOMB_X28_Y12_N6
\tx_shift_reg~101\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~101_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(89))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111110101010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(89),
	combout => \tx_shift_reg~101_combout\);

-- Location: FF_X28_Y12_N7
\tx_shift_reg[90]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~101_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(90));

-- Location: LCCOMB_X28_Y12_N4
\tx_shift_reg~100\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~100_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(90))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0101010100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(90),
	combout => \tx_shift_reg~100_combout\);

-- Location: FF_X28_Y12_N5
\tx_shift_reg[91]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~100_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(91));

-- Location: LCCOMB_X28_Y12_N26
\tx_shift_reg~99\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~99_combout\ = (tx_shift_reg(91) & !\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000000011110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(91),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~99_combout\);

-- Location: FF_X28_Y12_N27
\tx_shift_reg[92]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~99_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(92));

-- Location: LCCOMB_X28_Y12_N8
\tx_shift_reg~98\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~98_combout\ = (tx_shift_reg(92)) # (\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(92),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~98_combout\);

-- Location: FF_X28_Y12_N9
\tx_shift_reg[93]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~98_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(93));

-- Location: LCCOMB_X28_Y12_N22
\tx_shift_reg~97\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~97_combout\ = (tx_shift_reg(93)) # (\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(93),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~97_combout\);

-- Location: FF_X28_Y12_N23
\tx_shift_reg[94]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~97_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(94));

-- Location: LCCOMB_X28_Y12_N12
\tx_shift_reg~96\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~96_combout\ = (tx_shift_reg(94)) # (\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(94),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~96_combout\);

-- Location: FF_X28_Y12_N13
\tx_shift_reg[95]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~96_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(95));

-- Location: LCCOMB_X28_Y12_N10
\tx_shift_reg~95\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~95_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(95))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0101010100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(95),
	combout => \tx_shift_reg~95_combout\);

-- Location: FF_X28_Y12_N11
\tx_shift_reg[96]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~95_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(96));

-- Location: LCCOMB_X28_Y12_N24
\tx_shift_reg~94\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~94_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(96))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0101010100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(96),
	combout => \tx_shift_reg~94_combout\);

-- Location: FF_X28_Y12_N25
\tx_shift_reg[97]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~94_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(97));

-- Location: LCCOMB_X22_Y14_N30
\tx_shift_reg~93\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~93_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(97))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111110101010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(97),
	combout => \tx_shift_reg~93_combout\);

-- Location: FF_X22_Y14_N31
\tx_shift_reg[98]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~93_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(98));

-- Location: LCCOMB_X22_Y14_N28
\tx_shift_reg~92\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~92_combout\ = (tx_shift_reg(98) & !\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000000011110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(98),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~92_combout\);

-- Location: FF_X22_Y14_N29
\tx_shift_reg[99]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~92_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(99));

-- Location: LCCOMB_X22_Y14_N18
\tx_shift_reg~91\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~91_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(99))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111110101010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(99),
	combout => \tx_shift_reg~91_combout\);

-- Location: FF_X22_Y14_N19
\tx_shift_reg[100]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~91_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(100));

-- Location: LCCOMB_X22_Y14_N16
\tx_shift_reg~90\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~90_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(100))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0101010100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(100),
	combout => \tx_shift_reg~90_combout\);

-- Location: FF_X22_Y14_N17
\tx_shift_reg[101]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~90_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(101));

-- Location: LCCOMB_X22_Y14_N6
\tx_shift_reg~89\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~89_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(101))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111110101010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(101),
	combout => \tx_shift_reg~89_combout\);

-- Location: FF_X22_Y14_N7
\tx_shift_reg[102]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~89_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(102));

-- Location: LCCOMB_X22_Y14_N4
\tx_shift_reg~88\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~88_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(102))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111110101010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(102),
	combout => \tx_shift_reg~88_combout\);

-- Location: FF_X22_Y14_N5
\tx_shift_reg[103]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~88_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(103));

-- Location: LCCOMB_X22_Y14_N2
\tx_shift_reg~87\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~87_combout\ = (tx_shift_reg(103) & !\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000000011110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(103),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~87_combout\);

-- Location: FF_X22_Y14_N3
\tx_shift_reg[104]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~87_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(104));

-- Location: LCCOMB_X22_Y14_N8
\tx_shift_reg~86\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~86_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(104))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0101010100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(104),
	combout => \tx_shift_reg~86_combout\);

-- Location: FF_X22_Y14_N9
\tx_shift_reg[105]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~86_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(105));

-- Location: LCCOMB_X22_Y14_N22
\tx_shift_reg~85\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~85_combout\ = (tx_shift_reg(105)) # (\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(105),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~85_combout\);

-- Location: FF_X22_Y14_N23
\tx_shift_reg[106]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~85_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(106));

-- Location: LCCOMB_X22_Y14_N20
\tx_shift_reg~84\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~84_combout\ = (tx_shift_reg(106) & !\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000000011110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(106),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~84_combout\);

-- Location: FF_X22_Y14_N21
\tx_shift_reg[107]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~84_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(107));

-- Location: LCCOMB_X22_Y14_N26
\tx_shift_reg~83\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~83_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(107))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111110101010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(107),
	combout => \tx_shift_reg~83_combout\);

-- Location: FF_X22_Y14_N27
\tx_shift_reg[108]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~83_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(108));

-- Location: LCCOMB_X22_Y14_N24
\tx_shift_reg~82\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~82_combout\ = (tx_shift_reg(108) & !\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000000011110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(108),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~82_combout\);

-- Location: FF_X22_Y14_N25
\tx_shift_reg[109]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~82_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(109));

-- Location: LCCOMB_X22_Y14_N14
\tx_shift_reg~81\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~81_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(109))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111110101010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(109),
	combout => \tx_shift_reg~81_combout\);

-- Location: FF_X22_Y14_N15
\tx_shift_reg[110]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~81_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(110));

-- Location: LCCOMB_X22_Y14_N12
\tx_shift_reg~80\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~80_combout\ = (tx_shift_reg(110)) # (\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(110),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~80_combout\);

-- Location: FF_X22_Y14_N13
\tx_shift_reg[111]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~80_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(111));

-- Location: LCCOMB_X22_Y14_N10
\tx_shift_reg~79\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~79_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(111))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0101010100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(111),
	combout => \tx_shift_reg~79_combout\);

-- Location: FF_X22_Y14_N11
\tx_shift_reg[112]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~79_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(112));

-- Location: LCCOMB_X22_Y14_N0
\tx_shift_reg~78\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~78_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(112))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0101010100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(112),
	combout => \tx_shift_reg~78_combout\);

-- Location: FF_X22_Y14_N1
\tx_shift_reg[113]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~78_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(113));

-- Location: LCCOMB_X19_Y12_N30
\tx_shift_reg~77\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~77_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(113))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111110101010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(113),
	combout => \tx_shift_reg~77_combout\);

-- Location: FF_X19_Y12_N31
\tx_shift_reg[114]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~77_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(114));

-- Location: LCCOMB_X19_Y12_N28
\tx_shift_reg~76\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~76_combout\ = (tx_shift_reg(114) & !\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000000011110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(114),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~76_combout\);

-- Location: FF_X19_Y12_N29
\tx_shift_reg[115]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~76_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(115));

-- Location: LCCOMB_X19_Y12_N10
\tx_shift_reg~75\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~75_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(115))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111110101010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(115),
	combout => \tx_shift_reg~75_combout\);

-- Location: FF_X19_Y12_N11
\tx_shift_reg[116]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~75_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(116));

-- Location: LCCOMB_X19_Y12_N16
\tx_shift_reg~74\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~74_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(116))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0101010100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(116),
	combout => \tx_shift_reg~74_combout\);

-- Location: FF_X19_Y12_N17
\tx_shift_reg[117]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~74_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(117));

-- Location: LCCOMB_X19_Y12_N6
\tx_shift_reg~73\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~73_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(117))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111110101010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(117),
	combout => \tx_shift_reg~73_combout\);

-- Location: FF_X19_Y12_N7
\tx_shift_reg[118]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~73_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(118));

-- Location: LCCOMB_X19_Y12_N20
\tx_shift_reg~72\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~72_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(118))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111110101010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(118),
	combout => \tx_shift_reg~72_combout\);

-- Location: FF_X19_Y12_N21
\tx_shift_reg[119]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~72_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(119));

-- Location: LCCOMB_X19_Y12_N18
\tx_shift_reg~71\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~71_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(119))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111110101010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(119),
	combout => \tx_shift_reg~71_combout\);

-- Location: FF_X19_Y12_N19
\tx_shift_reg[120]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~71_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(120));

-- Location: LCCOMB_X19_Y12_N8
\tx_shift_reg~70\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~70_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(120))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111110101010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(120),
	combout => \tx_shift_reg~70_combout\);

-- Location: FF_X19_Y12_N9
\tx_shift_reg[121]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~70_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(121));

-- Location: LCCOMB_X19_Y12_N22
\tx_shift_reg~69\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~69_combout\ = (tx_shift_reg(121) & !\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000000011110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(121),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~69_combout\);

-- Location: FF_X19_Y12_N23
\tx_shift_reg[122]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~69_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(122));

-- Location: LCCOMB_X19_Y12_N12
\tx_shift_reg~68\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~68_combout\ = (tx_shift_reg(122) & !\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000000011110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(122),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~68_combout\);

-- Location: FF_X19_Y12_N13
\tx_shift_reg[123]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~68_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(123));

-- Location: LCCOMB_X19_Y12_N26
\tx_shift_reg~67\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~67_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(123))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0101010100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(123),
	combout => \tx_shift_reg~67_combout\);

-- Location: FF_X19_Y12_N27
\tx_shift_reg[124]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~67_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(124));

-- Location: LCCOMB_X19_Y12_N0
\tx_shift_reg~66\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~66_combout\ = (tx_shift_reg(124) & !\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000000011110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(124),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~66_combout\);

-- Location: FF_X19_Y12_N1
\tx_shift_reg[125]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~66_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(125));

-- Location: LCCOMB_X19_Y12_N14
\tx_shift_reg~65\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~65_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(125))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111110101010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(125),
	combout => \tx_shift_reg~65_combout\);

-- Location: FF_X19_Y12_N15
\tx_shift_reg[126]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~65_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(126));

-- Location: LCCOMB_X19_Y12_N4
\tx_shift_reg~64\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~64_combout\ = (tx_shift_reg(126)) # (\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(126),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~64_combout\);

-- Location: FF_X19_Y12_N5
\tx_shift_reg[127]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~64_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(127));

-- Location: LCCOMB_X19_Y12_N2
\tx_shift_reg~63\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~63_combout\ = (tx_shift_reg(127)) # (\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(127),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~63_combout\);

-- Location: FF_X19_Y12_N3
\tx_shift_reg[128]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~63_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(128));

-- Location: LCCOMB_X19_Y12_N24
\tx_shift_reg~62\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~62_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(128))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111110101010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(128),
	combout => \tx_shift_reg~62_combout\);

-- Location: FF_X19_Y12_N25
\tx_shift_reg[129]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~62_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(129));

-- Location: LCCOMB_X17_Y11_N14
\tx_shift_reg~61\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~61_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(129))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(129),
	combout => \tx_shift_reg~61_combout\);

-- Location: FF_X17_Y11_N15
\tx_shift_reg[130]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~61_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(130));

-- Location: LCCOMB_X17_Y11_N20
\tx_shift_reg~60\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~60_combout\ = (tx_shift_reg(130) & !\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000110000001100",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => tx_shift_reg(130),
	datac => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~60_combout\);

-- Location: FF_X17_Y11_N21
\tx_shift_reg[131]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~60_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(131));

-- Location: LCCOMB_X17_Y11_N2
\tx_shift_reg~59\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~59_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(131))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(131),
	combout => \tx_shift_reg~59_combout\);

-- Location: FF_X17_Y11_N3
\tx_shift_reg[132]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~59_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(132));

-- Location: LCCOMB_X17_Y11_N8
\tx_shift_reg~58\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~58_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(132))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(132),
	combout => \tx_shift_reg~58_combout\);

-- Location: FF_X17_Y11_N9
\tx_shift_reg[133]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~58_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(133));

-- Location: LCCOMB_X17_Y11_N30
\tx_shift_reg~57\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~57_combout\ = (tx_shift_reg(133)) # (\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111110011111100",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => tx_shift_reg(133),
	datac => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~57_combout\);

-- Location: FF_X17_Y11_N31
\tx_shift_reg[134]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~57_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(134));

-- Location: LCCOMB_X17_Y11_N28
\tx_shift_reg~56\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~56_combout\ = (tx_shift_reg(134)) # (\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111101011111010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => tx_shift_reg(134),
	datac => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~56_combout\);

-- Location: FF_X17_Y11_N29
\tx_shift_reg[135]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~56_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(135));

-- Location: LCCOMB_X17_Y11_N10
\tx_shift_reg~55\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~55_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(135))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(135),
	combout => \tx_shift_reg~55_combout\);

-- Location: FF_X17_Y11_N11
\tx_shift_reg[136]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~55_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(136));

-- Location: LCCOMB_X17_Y11_N16
\tx_shift_reg~54\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~54_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(136))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(136),
	combout => \tx_shift_reg~54_combout\);

-- Location: FF_X17_Y11_N17
\tx_shift_reg[137]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~54_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(137));

-- Location: LCCOMB_X17_Y11_N6
\tx_shift_reg~53\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~53_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(137))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(137),
	combout => \tx_shift_reg~53_combout\);

-- Location: FF_X17_Y11_N7
\tx_shift_reg[138]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~53_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(138));

-- Location: LCCOMB_X17_Y11_N4
\tx_shift_reg~52\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~52_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(138))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(138),
	combout => \tx_shift_reg~52_combout\);

-- Location: FF_X17_Y11_N5
\tx_shift_reg[139]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~52_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(139));

-- Location: LCCOMB_X17_Y11_N26
\tx_shift_reg~51\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~51_combout\ = (tx_shift_reg(139) & !\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000110000001100",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => tx_shift_reg(139),
	datac => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~51_combout\);

-- Location: FF_X17_Y11_N27
\tx_shift_reg[140]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~51_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(140));

-- Location: LCCOMB_X17_Y11_N24
\tx_shift_reg~50\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~50_combout\ = (tx_shift_reg(140) & !\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000101000001010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => tx_shift_reg(140),
	datac => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~50_combout\);

-- Location: FF_X17_Y11_N25
\tx_shift_reg[141]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~50_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(141));

-- Location: LCCOMB_X17_Y11_N22
\tx_shift_reg~49\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~49_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(141))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(141),
	combout => \tx_shift_reg~49_combout\);

-- Location: FF_X17_Y11_N23
\tx_shift_reg[142]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~49_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(142));

-- Location: LCCOMB_X17_Y11_N12
\tx_shift_reg~48\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~48_combout\ = (tx_shift_reg(142)) # (\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111101011111010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => tx_shift_reg(142),
	datac => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~48_combout\);

-- Location: FF_X17_Y11_N13
\tx_shift_reg[143]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~48_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(143));

-- Location: LCCOMB_X17_Y11_N18
\tx_shift_reg~47\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~47_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(143))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(143),
	combout => \tx_shift_reg~47_combout\);

-- Location: FF_X17_Y11_N19
\tx_shift_reg[144]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~47_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(144));

-- Location: LCCOMB_X17_Y11_N0
\tx_shift_reg~46\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~46_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(144))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(144),
	combout => \tx_shift_reg~46_combout\);

-- Location: FF_X17_Y11_N1
\tx_shift_reg[145]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~46_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(145));

-- Location: LCCOMB_X24_Y10_N12
\tx_shift_reg~45\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~45_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(145))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0011001100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(145),
	combout => \tx_shift_reg~45_combout\);

-- Location: FF_X24_Y10_N13
\tx_shift_reg[146]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~45_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(146));

-- Location: LCCOMB_X24_Y10_N18
\tx_shift_reg~44\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~44_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(146))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0011001100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(146),
	combout => \tx_shift_reg~44_combout\);

-- Location: FF_X24_Y10_N19
\tx_shift_reg[147]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~44_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(147));

-- Location: LCCOMB_X24_Y10_N0
\tx_shift_reg~43\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~43_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(147))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111001100",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(147),
	combout => \tx_shift_reg~43_combout\);

-- Location: FF_X24_Y10_N1
\tx_shift_reg[148]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~43_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(148));

-- Location: LCCOMB_X24_Y10_N6
\tx_shift_reg~42\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~42_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(148))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111001100",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(148),
	combout => \tx_shift_reg~42_combout\);

-- Location: FF_X24_Y10_N7
\tx_shift_reg[149]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~42_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(149));

-- Location: LCCOMB_X24_Y10_N28
\tx_shift_reg~41\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~41_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(149))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0011001100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(149),
	combout => \tx_shift_reg~41_combout\);

-- Location: FF_X24_Y10_N29
\tx_shift_reg[150]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~41_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(150));

-- Location: LCCOMB_X24_Y10_N10
\tx_shift_reg~40\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~40_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(150))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111001100",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(150),
	combout => \tx_shift_reg~40_combout\);

-- Location: FF_X24_Y10_N11
\tx_shift_reg[151]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~40_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(151));

-- Location: LCCOMB_X24_Y10_N24
\tx_shift_reg~39\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~39_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(151))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0011001100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(151),
	combout => \tx_shift_reg~39_combout\);

-- Location: FF_X24_Y10_N25
\tx_shift_reg[152]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~39_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(152));

-- Location: LCCOMB_X23_Y10_N4
\tx_shift_reg~38\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~38_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(152))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111001100",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(152),
	combout => \tx_shift_reg~38_combout\);

-- Location: FF_X23_Y10_N5
\tx_shift_reg[153]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~38_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(153));

-- Location: LCCOMB_X23_Y10_N10
\tx_shift_reg~37\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~37_combout\ = (tx_shift_reg(153) & !\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000000011110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(153),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~37_combout\);

-- Location: FF_X23_Y10_N11
\tx_shift_reg[154]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~37_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(154));

-- Location: LCCOMB_X23_Y10_N16
\tx_shift_reg~36\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~36_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(154))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0011001100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(154),
	combout => \tx_shift_reg~36_combout\);

-- Location: FF_X23_Y10_N17
\tx_shift_reg[155]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~36_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(155));

-- Location: LCCOMB_X23_Y10_N30
\tx_shift_reg~35\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~35_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(155))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111001100",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(155),
	combout => \tx_shift_reg~35_combout\);

-- Location: FF_X23_Y10_N31
\tx_shift_reg[156]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~35_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(156));

-- Location: LCCOMB_X23_Y10_N12
\tx_shift_reg~34\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~34_combout\ = (tx_shift_reg(156)) # (\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(156),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~34_combout\);

-- Location: FF_X23_Y10_N13
\tx_shift_reg[157]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~34_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(157));

-- Location: LCCOMB_X23_Y10_N18
\tx_shift_reg~33\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~33_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(157))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0011001100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(157),
	combout => \tx_shift_reg~33_combout\);

-- Location: FF_X23_Y10_N19
\tx_shift_reg[158]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~33_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(158));

-- Location: LCCOMB_X23_Y10_N0
\tx_shift_reg~32\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~32_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(158))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111001100",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(158),
	combout => \tx_shift_reg~32_combout\);

-- Location: FF_X23_Y10_N1
\tx_shift_reg[159]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~32_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(159));

-- Location: LCCOMB_X23_Y11_N30
\tx_shift_reg~31\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~31_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(159))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0011001100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(159),
	combout => \tx_shift_reg~31_combout\);

-- Location: FF_X23_Y11_N31
\tx_shift_reg[160]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~31_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(160));

-- Location: LCCOMB_X23_Y11_N12
\tx_shift_reg~30\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~30_combout\ = (tx_shift_reg(160)) # (\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(160),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~30_combout\);

-- Location: FF_X23_Y11_N13
\tx_shift_reg[161]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~30_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(161));

-- Location: LCCOMB_X23_Y11_N10
\tx_shift_reg~29\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~29_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(161))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0011001100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(161),
	combout => \tx_shift_reg~29_combout\);

-- Location: FF_X23_Y11_N11
\tx_shift_reg[162]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~29_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(162));

-- Location: LCCOMB_X23_Y11_N16
\tx_shift_reg~28\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~28_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(162))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0011001100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(162),
	combout => \tx_shift_reg~28_combout\);

-- Location: FF_X23_Y11_N17
\tx_shift_reg[163]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~28_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(163));

-- Location: LCCOMB_X23_Y11_N22
\tx_shift_reg~27\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~27_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(163))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111001100",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(163),
	combout => \tx_shift_reg~27_combout\);

-- Location: FF_X23_Y11_N23
\tx_shift_reg[164]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~27_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(164));

-- Location: LCCOMB_X23_Y11_N28
\tx_shift_reg~26\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~26_combout\ = (tx_shift_reg(164)) # (\u_tdm_master|lrclk_reg~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => tx_shift_reg(164),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~26_combout\);

-- Location: FF_X23_Y11_N29
\tx_shift_reg[165]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~26_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(165));

-- Location: LCCOMB_X23_Y11_N2
\tx_shift_reg~25\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~25_combout\ = (!\u_tdm_master|lrclk_reg~q\ & tx_shift_reg(165))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0011001100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(165),
	combout => \tx_shift_reg~25_combout\);

-- Location: FF_X23_Y11_N3
\tx_shift_reg[166]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~25_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(166));

-- Location: LCCOMB_X23_Y11_N8
\tx_shift_reg~24\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~24_combout\ = (\u_tdm_master|lrclk_reg~q\) # (tx_shift_reg(166))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111111001100",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(166),
	combout => \tx_shift_reg~24_combout\);

-- Location: FF_X23_Y11_N9
\tx_shift_reg[167]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~24_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(167));

-- Location: LCCOMB_X23_Y11_N14
\tx_shift_reg~23\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~23_combout\ = (\u_tdm_master|lrclk_reg~q\ & ((frame_counter(0)))) # (!\u_tdm_master|lrclk_reg~q\ & (tx_shift_reg(167)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111110000110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datac => tx_shift_reg(167),
	datad => frame_counter(0),
	combout => \tx_shift_reg~23_combout\);

-- Location: FF_X23_Y11_N15
\tx_shift_reg[168]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~23_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(168));

-- Location: LCCOMB_X23_Y11_N20
\tx_shift_reg~22\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~22_combout\ = (\u_tdm_master|lrclk_reg~q\ & (frame_counter(1))) # (!\u_tdm_master|lrclk_reg~q\ & ((tx_shift_reg(168))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1010101011110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => frame_counter(1),
	datac => tx_shift_reg(168),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~22_combout\);

-- Location: FF_X23_Y11_N21
\tx_shift_reg[169]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~22_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(169));

-- Location: LCCOMB_X23_Y11_N26
\tx_shift_reg~21\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~21_combout\ = (\u_tdm_master|lrclk_reg~q\ & (frame_counter(2))) # (!\u_tdm_master|lrclk_reg~q\ & ((tx_shift_reg(169))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1011101110001000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => frame_counter(2),
	datab => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(169),
	combout => \tx_shift_reg~21_combout\);

-- Location: FF_X23_Y11_N27
\tx_shift_reg[170]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~21_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(170));

-- Location: LCCOMB_X23_Y11_N24
\tx_shift_reg~20\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~20_combout\ = (\u_tdm_master|lrclk_reg~q\ & (frame_counter(3))) # (!\u_tdm_master|lrclk_reg~q\ & ((tx_shift_reg(170))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1010101011110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => frame_counter(3),
	datac => tx_shift_reg(170),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~20_combout\);

-- Location: FF_X23_Y11_N25
\tx_shift_reg[171]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~20_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(171));

-- Location: LCCOMB_X23_Y11_N6
\tx_shift_reg~19\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~19_combout\ = (\u_tdm_master|lrclk_reg~q\ & (frame_counter(4))) # (!\u_tdm_master|lrclk_reg~q\ & ((tx_shift_reg(171))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111001111000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datac => frame_counter(4),
	datad => tx_shift_reg(171),
	combout => \tx_shift_reg~19_combout\);

-- Location: FF_X23_Y11_N7
\tx_shift_reg[172]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~19_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(172));

-- Location: LCCOMB_X23_Y11_N4
\tx_shift_reg~18\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~18_combout\ = (\u_tdm_master|lrclk_reg~q\ & ((frame_counter(5)))) # (!\u_tdm_master|lrclk_reg~q\ & (tx_shift_reg(172)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1110111000100010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => tx_shift_reg(172),
	datab => \u_tdm_master|lrclk_reg~q\,
	datad => frame_counter(5),
	combout => \tx_shift_reg~18_combout\);

-- Location: FF_X23_Y11_N5
\tx_shift_reg[173]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~18_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(173));

-- Location: LCCOMB_X23_Y11_N18
\tx_shift_reg~17\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~17_combout\ = (\u_tdm_master|lrclk_reg~q\ & ((frame_counter(6)))) # (!\u_tdm_master|lrclk_reg~q\ & (tx_shift_reg(173)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111110000110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datac => tx_shift_reg(173),
	datad => frame_counter(6),
	combout => \tx_shift_reg~17_combout\);

-- Location: FF_X23_Y11_N19
\tx_shift_reg[174]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~17_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(174));

-- Location: LCCOMB_X22_Y11_N0
\tx_shift_reg~16\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~16_combout\ = (\u_tdm_master|lrclk_reg~q\ & (frame_counter(7))) # (!\u_tdm_master|lrclk_reg~q\ & ((tx_shift_reg(174))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111010110100000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datac => frame_counter(7),
	datad => tx_shift_reg(174),
	combout => \tx_shift_reg~16_combout\);

-- Location: FF_X22_Y11_N1
\tx_shift_reg[175]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~16_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(175));

-- Location: LCCOMB_X22_Y11_N6
\tx_shift_reg~15\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~15_combout\ = (\u_tdm_master|lrclk_reg~q\ & ((frame_counter(8)))) # (!\u_tdm_master|lrclk_reg~q\ & (tx_shift_reg(175)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111110000001100",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => tx_shift_reg(175),
	datac => \u_tdm_master|lrclk_reg~q\,
	datad => frame_counter(8),
	combout => \tx_shift_reg~15_combout\);

-- Location: FF_X22_Y11_N7
\tx_shift_reg[176]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~15_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(176));

-- Location: LCCOMB_X22_Y11_N4
\tx_shift_reg~14\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~14_combout\ = (\u_tdm_master|lrclk_reg~q\ & (frame_counter(9))) # (!\u_tdm_master|lrclk_reg~q\ & ((tx_shift_reg(176))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111010110100000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datac => frame_counter(9),
	datad => tx_shift_reg(176),
	combout => \tx_shift_reg~14_combout\);

-- Location: FF_X22_Y11_N5
\tx_shift_reg[177]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~14_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(177));

-- Location: LCCOMB_X22_Y11_N2
\tx_shift_reg~13\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~13_combout\ = (\u_tdm_master|lrclk_reg~q\ & ((frame_counter(10)))) # (!\u_tdm_master|lrclk_reg~q\ & (tx_shift_reg(177)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111110000001100",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => tx_shift_reg(177),
	datac => \u_tdm_master|lrclk_reg~q\,
	datad => frame_counter(10),
	combout => \tx_shift_reg~13_combout\);

-- Location: FF_X22_Y11_N3
\tx_shift_reg[178]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~13_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(178));

-- Location: LCCOMB_X22_Y11_N8
\tx_shift_reg~12\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~12_combout\ = (\u_tdm_master|lrclk_reg~q\ & (frame_counter(11))) # (!\u_tdm_master|lrclk_reg~q\ & ((tx_shift_reg(178))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111010110100000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datac => frame_counter(11),
	datad => tx_shift_reg(178),
	combout => \tx_shift_reg~12_combout\);

-- Location: FF_X22_Y11_N9
\tx_shift_reg[179]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~12_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(179));

-- Location: LCCOMB_X23_Y10_N22
\tx_shift_reg~11\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~11_combout\ = (\u_tdm_master|lrclk_reg~q\ & (frame_counter(12))) # (!\u_tdm_master|lrclk_reg~q\ & ((tx_shift_reg(179))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111001111000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datac => frame_counter(12),
	datad => tx_shift_reg(179),
	combout => \tx_shift_reg~11_combout\);

-- Location: FF_X23_Y10_N23
\tx_shift_reg[180]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~11_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(180));

-- Location: LCCOMB_X23_Y10_N28
\tx_shift_reg~10\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~10_combout\ = (\u_tdm_master|lrclk_reg~q\ & (frame_counter(13))) # (!\u_tdm_master|lrclk_reg~q\ & ((tx_shift_reg(180))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1010101011110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => frame_counter(13),
	datac => tx_shift_reg(180),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~10_combout\);

-- Location: FF_X23_Y10_N29
\tx_shift_reg[181]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~10_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(181));

-- Location: LCCOMB_X23_Y10_N2
\tx_shift_reg~9\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~9_combout\ = (\u_tdm_master|lrclk_reg~q\ & (frame_counter(14))) # (!\u_tdm_master|lrclk_reg~q\ & ((tx_shift_reg(181))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111001111000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datac => frame_counter(14),
	datad => tx_shift_reg(181),
	combout => \tx_shift_reg~9_combout\);

-- Location: FF_X23_Y10_N3
\tx_shift_reg[182]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~9_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(182));

-- Location: LCCOMB_X23_Y10_N8
\tx_shift_reg~8\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~8_combout\ = (\u_tdm_master|lrclk_reg~q\ & (frame_counter(15))) # (!\u_tdm_master|lrclk_reg~q\ & ((tx_shift_reg(182))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111001111000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datac => frame_counter(15),
	datad => tx_shift_reg(182),
	combout => \tx_shift_reg~8_combout\);

-- Location: FF_X23_Y10_N9
\tx_shift_reg[183]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~8_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(183));

-- Location: LCCOMB_X23_Y10_N6
\tx_shift_reg~7\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~7_combout\ = (\u_tdm_master|lrclk_reg~q\ & (frame_counter(16))) # (!\u_tdm_master|lrclk_reg~q\ & ((tx_shift_reg(183))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1010101011110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => frame_counter(16),
	datac => tx_shift_reg(183),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~7_combout\);

-- Location: FF_X23_Y10_N7
\tx_shift_reg[184]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~7_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(184));

-- Location: LCCOMB_X23_Y10_N20
\tx_shift_reg~6\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~6_combout\ = (\u_tdm_master|lrclk_reg~q\ & (frame_counter(17))) # (!\u_tdm_master|lrclk_reg~q\ & ((tx_shift_reg(184))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1011101110001000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => frame_counter(17),
	datab => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(184),
	combout => \tx_shift_reg~6_combout\);

-- Location: FF_X23_Y10_N21
\tx_shift_reg[185]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~6_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(185));

-- Location: LCCOMB_X23_Y10_N26
\tx_shift_reg~5\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~5_combout\ = (\u_tdm_master|lrclk_reg~q\ & (frame_counter(18))) # (!\u_tdm_master|lrclk_reg~q\ & ((tx_shift_reg(185))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1011101110001000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => frame_counter(18),
	datab => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(185),
	combout => \tx_shift_reg~5_combout\);

-- Location: FF_X23_Y10_N27
\tx_shift_reg[186]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~5_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(186));

-- Location: LCCOMB_X23_Y10_N24
\tx_shift_reg~4\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~4_combout\ = (\u_tdm_master|lrclk_reg~q\ & (frame_counter(19))) # (!\u_tdm_master|lrclk_reg~q\ & ((tx_shift_reg(186))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1010101011110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => frame_counter(19),
	datac => tx_shift_reg(186),
	datad => \u_tdm_master|lrclk_reg~q\,
	combout => \tx_shift_reg~4_combout\);

-- Location: FF_X23_Y10_N25
\tx_shift_reg[187]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~4_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(187));

-- Location: LCCOMB_X22_Y10_N30
\tx_shift_reg~3\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~3_combout\ = (\u_tdm_master|lrclk_reg~q\ & (frame_counter(20))) # (!\u_tdm_master|lrclk_reg~q\ & ((tx_shift_reg(187))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1100111111000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => frame_counter(20),
	datac => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(187),
	combout => \tx_shift_reg~3_combout\);

-- Location: FF_X22_Y10_N31
\tx_shift_reg[188]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~3_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(188));

-- Location: LCCOMB_X22_Y10_N28
\tx_shift_reg~2\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~2_combout\ = (\u_tdm_master|lrclk_reg~q\ & ((frame_counter(21)))) # (!\u_tdm_master|lrclk_reg~q\ & (tx_shift_reg(188)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111110000110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datac => tx_shift_reg(188),
	datad => frame_counter(21),
	combout => \tx_shift_reg~2_combout\);

-- Location: FF_X22_Y10_N29
\tx_shift_reg[189]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~2_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(189));

-- Location: LCCOMB_X22_Y10_N26
\tx_shift_reg~1\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~1_combout\ = (\u_tdm_master|lrclk_reg~q\ & (frame_counter(22))) # (!\u_tdm_master|lrclk_reg~q\ & ((tx_shift_reg(189))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1100111111000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => frame_counter(22),
	datac => \u_tdm_master|lrclk_reg~q\,
	datad => tx_shift_reg(189),
	combout => \tx_shift_reg~1_combout\);

-- Location: FF_X22_Y10_N27
\tx_shift_reg[190]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~1_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(190));

-- Location: LCCOMB_X22_Y10_N22
\frame_counter[23]~67\ : cycloneive_lcell_comb
-- Equation(s):
-- \frame_counter[23]~67_combout\ = frame_counter(23) $ (!\frame_counter[22]~66\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1010010110100101",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	dataa => frame_counter(23),
	cin => \frame_counter[22]~66\,
	combout => \frame_counter[23]~67_combout\);

-- Location: FF_X22_Y10_N23
\frame_counter[23]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \frame_counter[23]~67_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_master|lrclk_reg~q\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => frame_counter(23));

-- Location: LCCOMB_X22_Y10_N24
\tx_shift_reg~0\ : cycloneive_lcell_comb
-- Equation(s):
-- \tx_shift_reg~0_combout\ = (\u_tdm_master|lrclk_reg~q\ & ((frame_counter(23)))) # (!\u_tdm_master|lrclk_reg~q\ & (tx_shift_reg(190)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1110001011100010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => tx_shift_reg(190),
	datab => \u_tdm_master|lrclk_reg~q\,
	datac => frame_counter(23),
	combout => \tx_shift_reg~0_combout\);

-- Location: FF_X22_Y10_N25
\tx_shift_reg[191]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \ALT_INV_clk_18m432~inputclkctrl_outclk\,
	d => \tx_shift_reg~0_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => tx_shift_reg(191));

-- Location: LCCOMB_X21_Y13_N16
\u_tdm_rx|shift_reg[0]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[0]~feeder_combout\ = tx_shift_reg(191)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => tx_shift_reg(191),
	combout => \u_tdm_rx|shift_reg[0]~feeder_combout\);

-- Location: FF_X21_Y13_N17
\u_tdm_rx|shift_reg[0]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[0]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(0));

-- Location: LCCOMB_X21_Y13_N6
\u_tdm_rx|shift_reg[1]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[1]~feeder_combout\ = \u_tdm_rx|shift_reg\(0)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(0),
	combout => \u_tdm_rx|shift_reg[1]~feeder_combout\);

-- Location: FF_X21_Y13_N7
\u_tdm_rx|shift_reg[1]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[1]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(1));

-- Location: LCCOMB_X21_Y13_N4
\u_tdm_rx|shift_reg[2]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[2]~feeder_combout\ = \u_tdm_rx|shift_reg\(1)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(1),
	combout => \u_tdm_rx|shift_reg[2]~feeder_combout\);

-- Location: FF_X21_Y13_N5
\u_tdm_rx|shift_reg[2]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[2]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(2));

-- Location: FF_X21_Y13_N11
\u_tdm_rx|shift_reg[3]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(2),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(3));

-- Location: LCCOMB_X21_Y13_N0
\u_tdm_rx|shift_reg[4]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[4]~feeder_combout\ = \u_tdm_rx|shift_reg\(3)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(3),
	combout => \u_tdm_rx|shift_reg[4]~feeder_combout\);

-- Location: FF_X21_Y13_N1
\u_tdm_rx|shift_reg[4]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[4]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(4));

-- Location: FF_X19_Y11_N27
\u_tdm_rx|shift_reg[5]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(4),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(5));

-- Location: LCCOMB_X19_Y11_N10
\u_tdm_rx|shift_reg[6]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[6]~feeder_combout\ = \u_tdm_rx|shift_reg\(5)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(5),
	combout => \u_tdm_rx|shift_reg[6]~feeder_combout\);

-- Location: FF_X19_Y11_N11
\u_tdm_rx|shift_reg[6]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[6]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(6));

-- Location: LCCOMB_X19_Y11_N20
\u_tdm_rx|shift_reg[7]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[7]~feeder_combout\ = \u_tdm_rx|shift_reg\(6)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(6),
	combout => \u_tdm_rx|shift_reg[7]~feeder_combout\);

-- Location: FF_X19_Y11_N21
\u_tdm_rx|shift_reg[7]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[7]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(7));

-- Location: LCCOMB_X19_Y11_N0
\u_tdm_rx|shift_reg[8]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[8]~feeder_combout\ = \u_tdm_rx|shift_reg\(7)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(7),
	combout => \u_tdm_rx|shift_reg[8]~feeder_combout\);

-- Location: FF_X19_Y11_N1
\u_tdm_rx|shift_reg[8]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[8]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(8));

-- Location: LCCOMB_X19_Y11_N30
\u_tdm_rx|shift_reg[9]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[9]~feeder_combout\ = \u_tdm_rx|shift_reg\(8)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(8),
	combout => \u_tdm_rx|shift_reg[9]~feeder_combout\);

-- Location: FF_X19_Y11_N31
\u_tdm_rx|shift_reg[9]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[9]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(9));

-- Location: FF_X19_Y11_N5
\u_tdm_rx|shift_reg[10]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(9),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(10));

-- Location: FF_X19_Y11_N9
\u_tdm_rx|shift_reg[11]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(10),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(11));

-- Location: FF_X19_Y11_N7
\u_tdm_rx|shift_reg[12]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(11),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(12));

-- Location: LCCOMB_X18_Y11_N12
\u_tdm_rx|shift_reg[13]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[13]~feeder_combout\ = \u_tdm_rx|shift_reg\(12)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(12),
	combout => \u_tdm_rx|shift_reg[13]~feeder_combout\);

-- Location: FF_X18_Y11_N13
\u_tdm_rx|shift_reg[13]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[13]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(13));

-- Location: LCCOMB_X18_Y11_N18
\u_tdm_rx|shift_reg[14]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[14]~feeder_combout\ = \u_tdm_rx|shift_reg\(13)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(13),
	combout => \u_tdm_rx|shift_reg[14]~feeder_combout\);

-- Location: FF_X18_Y11_N19
\u_tdm_rx|shift_reg[14]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[14]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(14));

-- Location: LCCOMB_X18_Y11_N4
\u_tdm_rx|shift_reg[15]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[15]~feeder_combout\ = \u_tdm_rx|shift_reg\(14)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(14),
	combout => \u_tdm_rx|shift_reg[15]~feeder_combout\);

-- Location: FF_X18_Y11_N5
\u_tdm_rx|shift_reg[15]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[15]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(15));

-- Location: FF_X18_Y11_N15
\u_tdm_rx|shift_reg[16]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(15),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(16));

-- Location: FF_X18_Y11_N31
\u_tdm_rx|shift_reg[17]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(16),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(17));

-- Location: FF_X18_Y11_N23
\u_tdm_rx|shift_reg[18]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(17),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(18));

-- Location: FF_X18_Y11_N9
\u_tdm_rx|shift_reg[19]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(18),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(19));

-- Location: FF_X16_Y11_N1
\u_tdm_rx|shift_reg[20]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(19),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(20));

-- Location: FF_X16_Y10_N11
\u_tdm_rx|shift_reg[21]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(20),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(21));

-- Location: LCCOMB_X16_Y10_N2
\u_tdm_rx|shift_reg[22]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[22]~feeder_combout\ = \u_tdm_rx|shift_reg\(21)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(21),
	combout => \u_tdm_rx|shift_reg[22]~feeder_combout\);

-- Location: FF_X16_Y10_N3
\u_tdm_rx|shift_reg[22]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[22]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(22));

-- Location: LCCOMB_X16_Y10_N22
\u_tdm_rx|shift_reg[23]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[23]~feeder_combout\ = \u_tdm_rx|shift_reg\(22)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(22),
	combout => \u_tdm_rx|shift_reg[23]~feeder_combout\);

-- Location: FF_X16_Y10_N23
\u_tdm_rx|shift_reg[23]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[23]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(23));

-- Location: FF_X16_Y10_N21
\u_tdm_rx|shift_reg[24]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(23),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(24));

-- Location: LCCOMB_X16_Y10_N24
\u_tdm_rx|shift_reg[25]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[25]~feeder_combout\ = \u_tdm_rx|shift_reg\(24)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(24),
	combout => \u_tdm_rx|shift_reg[25]~feeder_combout\);

-- Location: FF_X16_Y10_N25
\u_tdm_rx|shift_reg[25]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[25]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(25));

-- Location: LCCOMB_X16_Y10_N16
\u_tdm_rx|shift_reg[26]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[26]~feeder_combout\ = \u_tdm_rx|shift_reg\(25)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(25),
	combout => \u_tdm_rx|shift_reg[26]~feeder_combout\);

-- Location: FF_X16_Y10_N17
\u_tdm_rx|shift_reg[26]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[26]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(26));

-- Location: LCCOMB_X16_Y10_N18
\u_tdm_rx|shift_reg[27]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[27]~feeder_combout\ = \u_tdm_rx|shift_reg\(26)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(26),
	combout => \u_tdm_rx|shift_reg[27]~feeder_combout\);

-- Location: FF_X16_Y10_N19
\u_tdm_rx|shift_reg[27]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[27]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(27));

-- Location: LCCOMB_X16_Y10_N14
\u_tdm_rx|shift_reg[28]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[28]~feeder_combout\ = \u_tdm_rx|shift_reg\(27)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(27),
	combout => \u_tdm_rx|shift_reg[28]~feeder_combout\);

-- Location: FF_X16_Y10_N15
\u_tdm_rx|shift_reg[28]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[28]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(28));

-- Location: LCCOMB_X14_Y10_N8
\u_tdm_rx|shift_reg[29]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[29]~feeder_combout\ = \u_tdm_rx|shift_reg\(28)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(28),
	combout => \u_tdm_rx|shift_reg[29]~feeder_combout\);

-- Location: FF_X14_Y10_N9
\u_tdm_rx|shift_reg[29]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[29]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(29));

-- Location: LCCOMB_X14_Y10_N26
\u_tdm_rx|shift_reg[30]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[30]~feeder_combout\ = \u_tdm_rx|shift_reg\(29)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(29),
	combout => \u_tdm_rx|shift_reg[30]~feeder_combout\);

-- Location: FF_X14_Y10_N27
\u_tdm_rx|shift_reg[30]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[30]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(30));

-- Location: LCCOMB_X14_Y10_N18
\u_tdm_rx|shift_reg[31]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[31]~feeder_combout\ = \u_tdm_rx|shift_reg\(30)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(30),
	combout => \u_tdm_rx|shift_reg[31]~feeder_combout\);

-- Location: FF_X14_Y10_N19
\u_tdm_rx|shift_reg[31]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[31]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(31));

-- Location: LCCOMB_X14_Y10_N12
\u_tdm_rx|shift_reg[32]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[32]~feeder_combout\ = \u_tdm_rx|shift_reg\(31)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(31),
	combout => \u_tdm_rx|shift_reg[32]~feeder_combout\);

-- Location: FF_X14_Y10_N13
\u_tdm_rx|shift_reg[32]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[32]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(32));

-- Location: LCCOMB_X14_Y10_N14
\u_tdm_rx|shift_reg[33]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[33]~feeder_combout\ = \u_tdm_rx|shift_reg\(32)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(32),
	combout => \u_tdm_rx|shift_reg[33]~feeder_combout\);

-- Location: FF_X14_Y10_N15
\u_tdm_rx|shift_reg[33]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[33]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(33));

-- Location: FF_X14_Y10_N29
\u_tdm_rx|shift_reg[34]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(33),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(34));

-- Location: LCCOMB_X14_Y10_N30
\u_tdm_rx|shift_reg[35]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[35]~feeder_combout\ = \u_tdm_rx|shift_reg\(34)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(34),
	combout => \u_tdm_rx|shift_reg[35]~feeder_combout\);

-- Location: FF_X14_Y10_N31
\u_tdm_rx|shift_reg[35]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[35]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(35));

-- Location: FF_X14_Y9_N23
\u_tdm_rx|shift_reg[36]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(35),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(36));

-- Location: FF_X14_Y9_N29
\u_tdm_rx|shift_reg[37]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(36),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(37));

-- Location: LCCOMB_X13_Y9_N8
\u_tdm_rx|shift_reg[38]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[38]~feeder_combout\ = \u_tdm_rx|shift_reg\(37)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(37),
	combout => \u_tdm_rx|shift_reg[38]~feeder_combout\);

-- Location: FF_X13_Y9_N9
\u_tdm_rx|shift_reg[38]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[38]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(38));

-- Location: LCCOMB_X14_Y9_N10
\u_tdm_rx|shift_reg[39]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[39]~feeder_combout\ = \u_tdm_rx|shift_reg\(38)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(38),
	combout => \u_tdm_rx|shift_reg[39]~feeder_combout\);

-- Location: FF_X14_Y9_N11
\u_tdm_rx|shift_reg[39]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[39]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(39));

-- Location: LCCOMB_X14_Y9_N2
\u_tdm_rx|shift_reg[40]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[40]~feeder_combout\ = \u_tdm_rx|shift_reg\(39)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(39),
	combout => \u_tdm_rx|shift_reg[40]~feeder_combout\);

-- Location: FF_X14_Y9_N3
\u_tdm_rx|shift_reg[40]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[40]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(40));

-- Location: LCCOMB_X14_Y9_N12
\u_tdm_rx|shift_reg[41]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[41]~feeder_combout\ = \u_tdm_rx|shift_reg\(40)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(40),
	combout => \u_tdm_rx|shift_reg[41]~feeder_combout\);

-- Location: FF_X14_Y9_N13
\u_tdm_rx|shift_reg[41]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[41]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(41));

-- Location: LCCOMB_X14_Y9_N4
\u_tdm_rx|shift_reg[42]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[42]~feeder_combout\ = \u_tdm_rx|shift_reg\(41)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(41),
	combout => \u_tdm_rx|shift_reg[42]~feeder_combout\);

-- Location: FF_X14_Y9_N5
\u_tdm_rx|shift_reg[42]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[42]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(42));

-- Location: LCCOMB_X14_Y9_N18
\u_tdm_rx|shift_reg[43]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[43]~feeder_combout\ = \u_tdm_rx|shift_reg\(42)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(42),
	combout => \u_tdm_rx|shift_reg[43]~feeder_combout\);

-- Location: FF_X14_Y9_N19
\u_tdm_rx|shift_reg[43]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[43]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(43));

-- Location: LCCOMB_X14_Y9_N24
\u_tdm_rx|shift_reg[44]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[44]~feeder_combout\ = \u_tdm_rx|shift_reg\(43)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(43),
	combout => \u_tdm_rx|shift_reg[44]~feeder_combout\);

-- Location: FF_X14_Y9_N25
\u_tdm_rx|shift_reg[44]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[44]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(44));

-- Location: FF_X14_Y11_N23
\u_tdm_rx|shift_reg[45]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(44),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(45));

-- Location: FF_X14_Y11_N5
\u_tdm_rx|shift_reg[46]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(45),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(46));

-- Location: LCCOMB_X14_Y11_N0
\u_tdm_rx|shift_reg[47]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[47]~feeder_combout\ = \u_tdm_rx|shift_reg\(46)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(46),
	combout => \u_tdm_rx|shift_reg[47]~feeder_combout\);

-- Location: FF_X14_Y11_N1
\u_tdm_rx|shift_reg[47]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[47]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(47));

-- Location: LCCOMB_X14_Y11_N2
\u_tdm_rx|shift_reg[48]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[48]~feeder_combout\ = \u_tdm_rx|shift_reg\(47)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(47),
	combout => \u_tdm_rx|shift_reg[48]~feeder_combout\);

-- Location: FF_X14_Y11_N3
\u_tdm_rx|shift_reg[48]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[48]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(48));

-- Location: LCCOMB_X14_Y11_N14
\u_tdm_rx|shift_reg[49]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[49]~feeder_combout\ = \u_tdm_rx|shift_reg\(48)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(48),
	combout => \u_tdm_rx|shift_reg[49]~feeder_combout\);

-- Location: FF_X14_Y11_N15
\u_tdm_rx|shift_reg[49]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[49]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(49));

-- Location: FF_X14_Y11_N31
\u_tdm_rx|shift_reg[50]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(49),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(50));

-- Location: FF_X14_Y11_N29
\u_tdm_rx|shift_reg[51]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(50),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(51));

-- Location: LCCOMB_X13_Y11_N0
\u_tdm_rx|shift_reg[52]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[52]~feeder_combout\ = \u_tdm_rx|shift_reg\(51)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(51),
	combout => \u_tdm_rx|shift_reg[52]~feeder_combout\);

-- Location: FF_X13_Y11_N1
\u_tdm_rx|shift_reg[52]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[52]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(52));

-- Location: LCCOMB_X13_Y11_N6
\u_tdm_rx|shift_reg[53]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[53]~feeder_combout\ = \u_tdm_rx|shift_reg\(52)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(52),
	combout => \u_tdm_rx|shift_reg[53]~feeder_combout\);

-- Location: FF_X13_Y11_N7
\u_tdm_rx|shift_reg[53]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[53]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(53));

-- Location: LCCOMB_X13_Y11_N2
\u_tdm_rx|shift_reg[54]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[54]~feeder_combout\ = \u_tdm_rx|shift_reg\(53)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(53),
	combout => \u_tdm_rx|shift_reg[54]~feeder_combout\);

-- Location: FF_X13_Y11_N3
\u_tdm_rx|shift_reg[54]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[54]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(54));

-- Location: LCCOMB_X13_Y11_N8
\u_tdm_rx|shift_reg[55]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[55]~feeder_combout\ = \u_tdm_rx|shift_reg\(54)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(54),
	combout => \u_tdm_rx|shift_reg[55]~feeder_combout\);

-- Location: FF_X13_Y11_N9
\u_tdm_rx|shift_reg[55]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[55]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(55));

-- Location: FF_X13_Y11_N23
\u_tdm_rx|shift_reg[56]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(55),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(56));

-- Location: FF_X13_Y11_N29
\u_tdm_rx|shift_reg[57]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(56),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(57));

-- Location: LCCOMB_X13_Y11_N10
\u_tdm_rx|shift_reg[58]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[58]~feeder_combout\ = \u_tdm_rx|shift_reg\(57)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(57),
	combout => \u_tdm_rx|shift_reg[58]~feeder_combout\);

-- Location: FF_X13_Y11_N11
\u_tdm_rx|shift_reg[58]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[58]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(58));

-- Location: LCCOMB_X13_Y11_N20
\u_tdm_rx|shift_reg[59]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[59]~feeder_combout\ = \u_tdm_rx|shift_reg\(58)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(58),
	combout => \u_tdm_rx|shift_reg[59]~feeder_combout\);

-- Location: FF_X13_Y11_N21
\u_tdm_rx|shift_reg[59]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[59]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(59));

-- Location: LCCOMB_X13_Y11_N14
\u_tdm_rx|shift_reg[60]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[60]~feeder_combout\ = \u_tdm_rx|shift_reg\(59)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(59),
	combout => \u_tdm_rx|shift_reg[60]~feeder_combout\);

-- Location: FF_X13_Y11_N15
\u_tdm_rx|shift_reg[60]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[60]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(60));

-- Location: FF_X13_Y12_N11
\u_tdm_rx|shift_reg[61]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(60),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(61));

-- Location: LCCOMB_X13_Y12_N2
\u_tdm_rx|shift_reg[62]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[62]~feeder_combout\ = \u_tdm_rx|shift_reg\(61)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(61),
	combout => \u_tdm_rx|shift_reg[62]~feeder_combout\);

-- Location: FF_X13_Y12_N3
\u_tdm_rx|shift_reg[62]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[62]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(62));

-- Location: LCCOMB_X13_Y12_N26
\u_tdm_rx|shift_reg[63]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[63]~feeder_combout\ = \u_tdm_rx|shift_reg\(62)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(62),
	combout => \u_tdm_rx|shift_reg[63]~feeder_combout\);

-- Location: FF_X13_Y12_N27
\u_tdm_rx|shift_reg[63]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[63]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(63));

-- Location: FF_X13_Y12_N13
\u_tdm_rx|shift_reg[64]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(63),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(64));

-- Location: LCCOMB_X13_Y12_N0
\u_tdm_rx|shift_reg[65]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[65]~feeder_combout\ = \u_tdm_rx|shift_reg\(64)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(64),
	combout => \u_tdm_rx|shift_reg[65]~feeder_combout\);

-- Location: FF_X13_Y12_N1
\u_tdm_rx|shift_reg[65]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[65]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(65));

-- Location: LCCOMB_X13_Y12_N30
\u_tdm_rx|shift_reg[66]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[66]~feeder_combout\ = \u_tdm_rx|shift_reg\(65)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(65),
	combout => \u_tdm_rx|shift_reg[66]~feeder_combout\);

-- Location: FF_X13_Y12_N31
\u_tdm_rx|shift_reg[66]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[66]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(66));

-- Location: LCCOMB_X13_Y12_N24
\u_tdm_rx|shift_reg[67]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[67]~feeder_combout\ = \u_tdm_rx|shift_reg\(66)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(66),
	combout => \u_tdm_rx|shift_reg[67]~feeder_combout\);

-- Location: FF_X13_Y12_N25
\u_tdm_rx|shift_reg[67]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[67]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(67));

-- Location: LCCOMB_X17_Y14_N20
\u_tdm_rx|shift_reg[68]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[68]~feeder_combout\ = \u_tdm_rx|shift_reg\(67)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(67),
	combout => \u_tdm_rx|shift_reg[68]~feeder_combout\);

-- Location: FF_X17_Y14_N21
\u_tdm_rx|shift_reg[68]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[68]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(68));

-- Location: LCCOMB_X17_Y14_N18
\u_tdm_rx|shift_reg[69]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[69]~feeder_combout\ = \u_tdm_rx|shift_reg\(68)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(68),
	combout => \u_tdm_rx|shift_reg[69]~feeder_combout\);

-- Location: FF_X17_Y14_N19
\u_tdm_rx|shift_reg[69]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[69]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(69));

-- Location: LCCOMB_X17_Y14_N24
\u_tdm_rx|shift_reg[70]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[70]~feeder_combout\ = \u_tdm_rx|shift_reg\(69)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(69),
	combout => \u_tdm_rx|shift_reg[70]~feeder_combout\);

-- Location: FF_X17_Y14_N25
\u_tdm_rx|shift_reg[70]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[70]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(70));

-- Location: LCCOMB_X17_Y14_N22
\u_tdm_rx|shift_reg[71]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[71]~feeder_combout\ = \u_tdm_rx|shift_reg\(70)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(70),
	combout => \u_tdm_rx|shift_reg[71]~feeder_combout\);

-- Location: FF_X17_Y14_N23
\u_tdm_rx|shift_reg[71]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[71]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(71));

-- Location: FF_X17_Y14_N27
\u_tdm_rx|shift_reg[72]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(71),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(72));

-- Location: FF_X17_Y14_N13
\u_tdm_rx|shift_reg[73]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(72),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(73));

-- Location: LCCOMB_X17_Y15_N18
\u_tdm_rx|shift_reg[74]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[74]~feeder_combout\ = \u_tdm_rx|shift_reg\(73)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(73),
	combout => \u_tdm_rx|shift_reg[74]~feeder_combout\);

-- Location: FF_X17_Y15_N19
\u_tdm_rx|shift_reg[74]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[74]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(74));

-- Location: LCCOMB_X17_Y15_N28
\u_tdm_rx|shift_reg[75]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[75]~feeder_combout\ = \u_tdm_rx|shift_reg\(74)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(74),
	combout => \u_tdm_rx|shift_reg[75]~feeder_combout\);

-- Location: FF_X17_Y15_N29
\u_tdm_rx|shift_reg[75]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[75]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(75));

-- Location: LCCOMB_X17_Y15_N16
\u_tdm_rx|shift_reg[76]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[76]~feeder_combout\ = \u_tdm_rx|shift_reg\(75)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(75),
	combout => \u_tdm_rx|shift_reg[76]~feeder_combout\);

-- Location: FF_X17_Y15_N17
\u_tdm_rx|shift_reg[76]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[76]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(76));

-- Location: LCCOMB_X17_Y15_N30
\u_tdm_rx|shift_reg[77]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[77]~feeder_combout\ = \u_tdm_rx|shift_reg\(76)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(76),
	combout => \u_tdm_rx|shift_reg[77]~feeder_combout\);

-- Location: FF_X17_Y15_N31
\u_tdm_rx|shift_reg[77]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[77]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(77));

-- Location: FF_X17_Y15_N21
\u_tdm_rx|shift_reg[78]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(77),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(78));

-- Location: LCCOMB_X17_Y15_N2
\u_tdm_rx|shift_reg[79]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[79]~feeder_combout\ = \u_tdm_rx|shift_reg\(78)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(78),
	combout => \u_tdm_rx|shift_reg[79]~feeder_combout\);

-- Location: FF_X17_Y15_N3
\u_tdm_rx|shift_reg[79]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[79]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(79));

-- Location: LCCOMB_X17_Y15_N24
\u_tdm_rx|shift_reg[80]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[80]~feeder_combout\ = \u_tdm_rx|shift_reg\(79)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(79),
	combout => \u_tdm_rx|shift_reg[80]~feeder_combout\);

-- Location: FF_X17_Y15_N25
\u_tdm_rx|shift_reg[80]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[80]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(80));

-- Location: LCCOMB_X16_Y15_N24
\u_tdm_rx|shift_reg[81]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[81]~feeder_combout\ = \u_tdm_rx|shift_reg\(80)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(80),
	combout => \u_tdm_rx|shift_reg[81]~feeder_combout\);

-- Location: FF_X16_Y15_N25
\u_tdm_rx|shift_reg[81]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[81]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(81));

-- Location: LCCOMB_X16_Y15_N4
\u_tdm_rx|shift_reg[82]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[82]~feeder_combout\ = \u_tdm_rx|shift_reg\(81)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(81),
	combout => \u_tdm_rx|shift_reg[82]~feeder_combout\);

-- Location: FF_X16_Y15_N5
\u_tdm_rx|shift_reg[82]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[82]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(82));

-- Location: LCCOMB_X16_Y15_N10
\u_tdm_rx|shift_reg[83]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[83]~feeder_combout\ = \u_tdm_rx|shift_reg\(82)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(82),
	combout => \u_tdm_rx|shift_reg[83]~feeder_combout\);

-- Location: FF_X16_Y15_N11
\u_tdm_rx|shift_reg[83]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[83]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(83));

-- Location: LCCOMB_X16_Y15_N0
\u_tdm_rx|shift_reg[84]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[84]~feeder_combout\ = \u_tdm_rx|shift_reg\(83)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(83),
	combout => \u_tdm_rx|shift_reg[84]~feeder_combout\);

-- Location: FF_X16_Y15_N1
\u_tdm_rx|shift_reg[84]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[84]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(84));

-- Location: LCCOMB_X16_Y15_N2
\u_tdm_rx|shift_reg[85]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[85]~feeder_combout\ = \u_tdm_rx|shift_reg\(84)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(84),
	combout => \u_tdm_rx|shift_reg[85]~feeder_combout\);

-- Location: FF_X16_Y15_N3
\u_tdm_rx|shift_reg[85]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[85]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(85));

-- Location: LCCOMB_X16_Y15_N18
\u_tdm_rx|shift_reg[86]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[86]~feeder_combout\ = \u_tdm_rx|shift_reg\(85)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(85),
	combout => \u_tdm_rx|shift_reg[86]~feeder_combout\);

-- Location: FF_X16_Y15_N19
\u_tdm_rx|shift_reg[86]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[86]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(86));

-- Location: LCCOMB_X16_Y15_N22
\u_tdm_rx|shift_reg[87]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[87]~feeder_combout\ = \u_tdm_rx|shift_reg\(86)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(86),
	combout => \u_tdm_rx|shift_reg[87]~feeder_combout\);

-- Location: FF_X16_Y15_N23
\u_tdm_rx|shift_reg[87]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[87]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(87));

-- Location: FF_X16_Y15_N31
\u_tdm_rx|shift_reg[88]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(87),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(88));

-- Location: LCCOMB_X13_Y10_N2
\u_tdm_rx|shift_reg[89]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[89]~feeder_combout\ = \u_tdm_rx|shift_reg\(88)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(88),
	combout => \u_tdm_rx|shift_reg[89]~feeder_combout\);

-- Location: FF_X13_Y10_N3
\u_tdm_rx|shift_reg[89]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[89]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(89));

-- Location: LCCOMB_X13_Y10_N24
\u_tdm_rx|shift_reg[90]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[90]~feeder_combout\ = \u_tdm_rx|shift_reg\(89)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(89),
	combout => \u_tdm_rx|shift_reg[90]~feeder_combout\);

-- Location: FF_X13_Y10_N25
\u_tdm_rx|shift_reg[90]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[90]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(90));

-- Location: LCCOMB_X13_Y10_N4
\u_tdm_rx|shift_reg[91]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[91]~feeder_combout\ = \u_tdm_rx|shift_reg\(90)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(90),
	combout => \u_tdm_rx|shift_reg[91]~feeder_combout\);

-- Location: FF_X13_Y10_N5
\u_tdm_rx|shift_reg[91]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[91]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(91));

-- Location: FF_X13_Y10_N27
\u_tdm_rx|shift_reg[92]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(91),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(92));

-- Location: FF_X13_Y10_N23
\u_tdm_rx|shift_reg[93]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(92),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(93));

-- Location: FF_X13_Y10_N31
\u_tdm_rx|shift_reg[94]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(93),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(94));

-- Location: FF_X13_Y10_N29
\u_tdm_rx|shift_reg[95]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(94),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(95));

-- Location: LCCOMB_X12_Y10_N24
\u_tdm_rx|shift_reg[96]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[96]~feeder_combout\ = \u_tdm_rx|shift_reg\(95)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(95),
	combout => \u_tdm_rx|shift_reg[96]~feeder_combout\);

-- Location: FF_X12_Y10_N25
\u_tdm_rx|shift_reg[96]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[96]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(96));

-- Location: FF_X12_Y10_N31
\u_tdm_rx|shift_reg[97]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(96),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(97));

-- Location: FF_X12_Y10_N17
\u_tdm_rx|shift_reg[98]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(97),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(98));

-- Location: LCCOMB_X12_Y10_N26
\u_tdm_rx|shift_reg[99]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[99]~feeder_combout\ = \u_tdm_rx|shift_reg\(98)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(98),
	combout => \u_tdm_rx|shift_reg[99]~feeder_combout\);

-- Location: FF_X12_Y10_N27
\u_tdm_rx|shift_reg[99]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[99]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(99));

-- Location: FF_X12_Y10_N5
\u_tdm_rx|shift_reg[100]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(99),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(100));

-- Location: FF_X12_Y10_N21
\u_tdm_rx|shift_reg[101]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(100),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(101));

-- Location: LCCOMB_X12_Y10_N18
\u_tdm_rx|shift_reg[102]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[102]~feeder_combout\ = \u_tdm_rx|shift_reg\(101)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(101),
	combout => \u_tdm_rx|shift_reg[102]~feeder_combout\);

-- Location: FF_X12_Y10_N19
\u_tdm_rx|shift_reg[102]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[102]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(102));

-- Location: LCCOMB_X12_Y10_N0
\u_tdm_rx|shift_reg[103]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[103]~feeder_combout\ = \u_tdm_rx|shift_reg\(102)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(102),
	combout => \u_tdm_rx|shift_reg[103]~feeder_combout\);

-- Location: FF_X12_Y10_N1
\u_tdm_rx|shift_reg[103]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[103]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(103));

-- Location: LCCOMB_X12_Y11_N10
\u_tdm_rx|shift_reg[104]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[104]~feeder_combout\ = \u_tdm_rx|shift_reg\(103)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(103),
	combout => \u_tdm_rx|shift_reg[104]~feeder_combout\);

-- Location: FF_X12_Y11_N11
\u_tdm_rx|shift_reg[104]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[104]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(104));

-- Location: LCCOMB_X13_Y13_N10
\u_tdm_rx|shift_reg[105]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[105]~feeder_combout\ = \u_tdm_rx|shift_reg\(104)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(104),
	combout => \u_tdm_rx|shift_reg[105]~feeder_combout\);

-- Location: FF_X13_Y13_N11
\u_tdm_rx|shift_reg[105]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[105]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(105));

-- Location: LCCOMB_X13_Y13_N0
\u_tdm_rx|shift_reg[106]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[106]~feeder_combout\ = \u_tdm_rx|shift_reg\(105)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(105),
	combout => \u_tdm_rx|shift_reg[106]~feeder_combout\);

-- Location: FF_X13_Y13_N1
\u_tdm_rx|shift_reg[106]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[106]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(106));

-- Location: LCCOMB_X13_Y13_N24
\u_tdm_rx|shift_reg[107]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[107]~feeder_combout\ = \u_tdm_rx|shift_reg\(106)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(106),
	combout => \u_tdm_rx|shift_reg[107]~feeder_combout\);

-- Location: FF_X13_Y13_N25
\u_tdm_rx|shift_reg[107]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[107]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(107));

-- Location: LCCOMB_X13_Y13_N8
\u_tdm_rx|shift_reg[108]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[108]~feeder_combout\ = \u_tdm_rx|shift_reg\(107)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(107),
	combout => \u_tdm_rx|shift_reg[108]~feeder_combout\);

-- Location: FF_X13_Y13_N9
\u_tdm_rx|shift_reg[108]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[108]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(108));

-- Location: FF_X13_Y13_N17
\u_tdm_rx|shift_reg[109]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(108),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(109));

-- Location: LCCOMB_X13_Y13_N20
\u_tdm_rx|shift_reg[110]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[110]~feeder_combout\ = \u_tdm_rx|shift_reg\(109)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(109),
	combout => \u_tdm_rx|shift_reg[110]~feeder_combout\);

-- Location: FF_X13_Y13_N21
\u_tdm_rx|shift_reg[110]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[110]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(110));

-- Location: LCCOMB_X13_Y13_N12
\u_tdm_rx|shift_reg[111]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[111]~feeder_combout\ = \u_tdm_rx|shift_reg\(110)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(110),
	combout => \u_tdm_rx|shift_reg[111]~feeder_combout\);

-- Location: FF_X13_Y13_N13
\u_tdm_rx|shift_reg[111]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[111]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(111));

-- Location: LCCOMB_X14_Y13_N18
\u_tdm_rx|shift_reg[112]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[112]~feeder_combout\ = \u_tdm_rx|shift_reg\(111)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(111),
	combout => \u_tdm_rx|shift_reg[112]~feeder_combout\);

-- Location: FF_X14_Y13_N19
\u_tdm_rx|shift_reg[112]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[112]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(112));

-- Location: LCCOMB_X14_Y13_N14
\u_tdm_rx|shift_reg[113]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[113]~feeder_combout\ = \u_tdm_rx|shift_reg\(112)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(112),
	combout => \u_tdm_rx|shift_reg[113]~feeder_combout\);

-- Location: FF_X14_Y13_N15
\u_tdm_rx|shift_reg[113]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[113]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(113));

-- Location: FF_X14_Y13_N5
\u_tdm_rx|shift_reg[114]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(113),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(114));

-- Location: FF_X14_Y13_N11
\u_tdm_rx|shift_reg[115]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(114),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(115));

-- Location: LCCOMB_X14_Y13_N22
\u_tdm_rx|shift_reg[116]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[116]~feeder_combout\ = \u_tdm_rx|shift_reg\(115)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(115),
	combout => \u_tdm_rx|shift_reg[116]~feeder_combout\);

-- Location: FF_X14_Y13_N23
\u_tdm_rx|shift_reg[116]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[116]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(116));

-- Location: FF_X14_Y13_N13
\u_tdm_rx|shift_reg[117]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(116),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(117));

-- Location: LCCOMB_X14_Y13_N24
\u_tdm_rx|shift_reg[118]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[118]~feeder_combout\ = \u_tdm_rx|shift_reg\(117)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(117),
	combout => \u_tdm_rx|shift_reg[118]~feeder_combout\);

-- Location: FF_X14_Y13_N25
\u_tdm_rx|shift_reg[118]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[118]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(118));

-- Location: LCCOMB_X14_Y13_N0
\u_tdm_rx|shift_reg[119]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[119]~feeder_combout\ = \u_tdm_rx|shift_reg\(118)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(118),
	combout => \u_tdm_rx|shift_reg[119]~feeder_combout\);

-- Location: FF_X14_Y13_N1
\u_tdm_rx|shift_reg[119]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[119]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(119));

-- Location: LCCOMB_X14_Y14_N24
\u_tdm_rx|shift_reg[120]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[120]~feeder_combout\ = \u_tdm_rx|shift_reg\(119)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(119),
	combout => \u_tdm_rx|shift_reg[120]~feeder_combout\);

-- Location: FF_X14_Y14_N25
\u_tdm_rx|shift_reg[120]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[120]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(120));

-- Location: LCCOMB_X13_Y14_N20
\u_tdm_rx|shift_reg[121]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[121]~feeder_combout\ = \u_tdm_rx|shift_reg\(120)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(120),
	combout => \u_tdm_rx|shift_reg[121]~feeder_combout\);

-- Location: FF_X13_Y14_N21
\u_tdm_rx|shift_reg[121]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[121]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(121));

-- Location: LCCOMB_X13_Y14_N12
\u_tdm_rx|shift_reg[122]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[122]~feeder_combout\ = \u_tdm_rx|shift_reg\(121)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(121),
	combout => \u_tdm_rx|shift_reg[122]~feeder_combout\);

-- Location: FF_X13_Y14_N13
\u_tdm_rx|shift_reg[122]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[122]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(122));

-- Location: LCCOMB_X13_Y14_N18
\u_tdm_rx|shift_reg[123]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[123]~feeder_combout\ = \u_tdm_rx|shift_reg\(122)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(122),
	combout => \u_tdm_rx|shift_reg[123]~feeder_combout\);

-- Location: FF_X13_Y14_N19
\u_tdm_rx|shift_reg[123]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[123]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(123));

-- Location: LCCOMB_X13_Y14_N22
\u_tdm_rx|shift_reg[124]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[124]~feeder_combout\ = \u_tdm_rx|shift_reg\(123)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(123),
	combout => \u_tdm_rx|shift_reg[124]~feeder_combout\);

-- Location: FF_X13_Y14_N23
\u_tdm_rx|shift_reg[124]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[124]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(124));

-- Location: FF_X13_Y14_N3
\u_tdm_rx|shift_reg[125]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(124),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(125));

-- Location: LCCOMB_X13_Y14_N8
\u_tdm_rx|shift_reg[126]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[126]~feeder_combout\ = \u_tdm_rx|shift_reg\(125)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(125),
	combout => \u_tdm_rx|shift_reg[126]~feeder_combout\);

-- Location: FF_X13_Y14_N9
\u_tdm_rx|shift_reg[126]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[126]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(126));

-- Location: FF_X13_Y14_N29
\u_tdm_rx|shift_reg[127]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(126),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(127));

-- Location: LCCOMB_X12_Y14_N6
\u_tdm_rx|shift_reg[128]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[128]~feeder_combout\ = \u_tdm_rx|shift_reg\(127)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(127),
	combout => \u_tdm_rx|shift_reg[128]~feeder_combout\);

-- Location: FF_X12_Y14_N7
\u_tdm_rx|shift_reg[128]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[128]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(128));

-- Location: LCCOMB_X12_Y14_N12
\u_tdm_rx|shift_reg[129]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[129]~feeder_combout\ = \u_tdm_rx|shift_reg\(128)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(128),
	combout => \u_tdm_rx|shift_reg[129]~feeder_combout\);

-- Location: FF_X12_Y14_N13
\u_tdm_rx|shift_reg[129]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[129]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(129));

-- Location: LCCOMB_X12_Y14_N26
\u_tdm_rx|shift_reg[130]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[130]~feeder_combout\ = \u_tdm_rx|shift_reg\(129)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(129),
	combout => \u_tdm_rx|shift_reg[130]~feeder_combout\);

-- Location: FF_X12_Y14_N27
\u_tdm_rx|shift_reg[130]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[130]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(130));

-- Location: FF_X12_Y14_N3
\u_tdm_rx|shift_reg[131]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(130),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(131));

-- Location: LCCOMB_X12_Y14_N4
\u_tdm_rx|shift_reg[132]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[132]~feeder_combout\ = \u_tdm_rx|shift_reg\(131)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(131),
	combout => \u_tdm_rx|shift_reg[132]~feeder_combout\);

-- Location: FF_X12_Y14_N5
\u_tdm_rx|shift_reg[132]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[132]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(132));

-- Location: FF_X12_Y14_N25
\u_tdm_rx|shift_reg[133]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(132),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(133));

-- Location: FF_X12_Y14_N19
\u_tdm_rx|shift_reg[134]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(133),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(134));

-- Location: LCCOMB_X12_Y14_N0
\u_tdm_rx|shift_reg[135]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[135]~feeder_combout\ = \u_tdm_rx|shift_reg\(134)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(134),
	combout => \u_tdm_rx|shift_reg[135]~feeder_combout\);

-- Location: FF_X12_Y14_N1
\u_tdm_rx|shift_reg[135]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[135]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(135));

-- Location: LCCOMB_X12_Y15_N12
\u_tdm_rx|shift_reg[136]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[136]~feeder_combout\ = \u_tdm_rx|shift_reg\(135)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(135),
	combout => \u_tdm_rx|shift_reg[136]~feeder_combout\);

-- Location: FF_X12_Y15_N13
\u_tdm_rx|shift_reg[136]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[136]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(136));

-- Location: LCCOMB_X12_Y15_N26
\u_tdm_rx|shift_reg[137]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[137]~feeder_combout\ = \u_tdm_rx|shift_reg\(136)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(136),
	combout => \u_tdm_rx|shift_reg[137]~feeder_combout\);

-- Location: FF_X12_Y15_N27
\u_tdm_rx|shift_reg[137]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[137]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(137));

-- Location: FF_X12_Y15_N9
\u_tdm_rx|shift_reg[138]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(137),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(138));

-- Location: FF_X12_Y15_N7
\u_tdm_rx|shift_reg[139]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(138),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(139));

-- Location: LCCOMB_X12_Y15_N0
\u_tdm_rx|shift_reg[140]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[140]~feeder_combout\ = \u_tdm_rx|shift_reg\(139)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(139),
	combout => \u_tdm_rx|shift_reg[140]~feeder_combout\);

-- Location: FF_X12_Y15_N1
\u_tdm_rx|shift_reg[140]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[140]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(140));

-- Location: FF_X19_Y13_N13
\u_tdm_rx|shift_reg[141]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(140),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(141));

-- Location: LCCOMB_X19_Y13_N28
\u_tdm_rx|shift_reg[142]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[142]~feeder_combout\ = \u_tdm_rx|shift_reg\(141)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(141),
	combout => \u_tdm_rx|shift_reg[142]~feeder_combout\);

-- Location: FF_X19_Y13_N29
\u_tdm_rx|shift_reg[142]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[142]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(142));

-- Location: LCCOMB_X19_Y13_N0
\u_tdm_rx|shift_reg[143]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[143]~feeder_combout\ = \u_tdm_rx|shift_reg\(142)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(142),
	combout => \u_tdm_rx|shift_reg[143]~feeder_combout\);

-- Location: FF_X19_Y13_N1
\u_tdm_rx|shift_reg[143]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[143]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(143));

-- Location: LCCOMB_X19_Y13_N2
\u_tdm_rx|shift_reg[144]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[144]~feeder_combout\ = \u_tdm_rx|shift_reg\(143)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(143),
	combout => \u_tdm_rx|shift_reg[144]~feeder_combout\);

-- Location: FF_X19_Y13_N3
\u_tdm_rx|shift_reg[144]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[144]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(144));

-- Location: LCCOMB_X19_Y13_N16
\u_tdm_rx|shift_reg[145]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[145]~feeder_combout\ = \u_tdm_rx|shift_reg\(144)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(144),
	combout => \u_tdm_rx|shift_reg[145]~feeder_combout\);

-- Location: FF_X19_Y13_N17
\u_tdm_rx|shift_reg[145]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[145]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(145));

-- Location: LCCOMB_X19_Y13_N6
\u_tdm_rx|shift_reg[146]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[146]~feeder_combout\ = \u_tdm_rx|shift_reg\(145)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(145),
	combout => \u_tdm_rx|shift_reg[146]~feeder_combout\);

-- Location: FF_X19_Y13_N7
\u_tdm_rx|shift_reg[146]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[146]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(146));

-- Location: LCCOMB_X19_Y13_N14
\u_tdm_rx|shift_reg[147]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[147]~feeder_combout\ = \u_tdm_rx|shift_reg\(146)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(146),
	combout => \u_tdm_rx|shift_reg[147]~feeder_combout\);

-- Location: FF_X19_Y13_N15
\u_tdm_rx|shift_reg[147]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[147]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(147));

-- Location: FF_X19_Y10_N27
\u_tdm_rx|shift_reg[148]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(147),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(148));

-- Location: FF_X19_Y10_N9
\u_tdm_rx|shift_reg[149]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(148),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(149));

-- Location: FF_X19_Y10_N29
\u_tdm_rx|shift_reg[150]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(149),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(150));

-- Location: LCCOMB_X19_Y10_N22
\u_tdm_rx|shift_reg[151]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[151]~feeder_combout\ = \u_tdm_rx|shift_reg\(150)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(150),
	combout => \u_tdm_rx|shift_reg[151]~feeder_combout\);

-- Location: FF_X19_Y10_N23
\u_tdm_rx|shift_reg[151]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[151]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(151));

-- Location: FF_X19_Y10_N5
\u_tdm_rx|shift_reg[152]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(151),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(152));

-- Location: FF_X19_Y10_N25
\u_tdm_rx|shift_reg[153]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(152),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(153));

-- Location: LCCOMB_X19_Y10_N18
\u_tdm_rx|shift_reg[154]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[154]~feeder_combout\ = \u_tdm_rx|shift_reg\(153)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(153),
	combout => \u_tdm_rx|shift_reg[154]~feeder_combout\);

-- Location: FF_X19_Y10_N19
\u_tdm_rx|shift_reg[154]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[154]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(154));

-- Location: LCCOMB_X18_Y10_N2
\u_tdm_rx|shift_reg[155]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[155]~feeder_combout\ = \u_tdm_rx|shift_reg\(154)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(154),
	combout => \u_tdm_rx|shift_reg[155]~feeder_combout\);

-- Location: FF_X18_Y10_N3
\u_tdm_rx|shift_reg[155]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[155]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(155));

-- Location: LCCOMB_X18_Y10_N16
\u_tdm_rx|shift_reg[156]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[156]~feeder_combout\ = \u_tdm_rx|shift_reg\(155)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(155),
	combout => \u_tdm_rx|shift_reg[156]~feeder_combout\);

-- Location: FF_X18_Y10_N17
\u_tdm_rx|shift_reg[156]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[156]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(156));

-- Location: LCCOMB_X17_Y10_N0
\u_tdm_rx|shift_reg[157]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[157]~feeder_combout\ = \u_tdm_rx|shift_reg\(156)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(156),
	combout => \u_tdm_rx|shift_reg[157]~feeder_combout\);

-- Location: FF_X17_Y10_N1
\u_tdm_rx|shift_reg[157]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[157]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(157));

-- Location: LCCOMB_X17_Y10_N10
\u_tdm_rx|shift_reg[158]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[158]~feeder_combout\ = \u_tdm_rx|shift_reg\(157)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(157),
	combout => \u_tdm_rx|shift_reg[158]~feeder_combout\);

-- Location: FF_X17_Y10_N11
\u_tdm_rx|shift_reg[158]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[158]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(158));

-- Location: LCCOMB_X17_Y10_N28
\u_tdm_rx|shift_reg[159]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[159]~feeder_combout\ = \u_tdm_rx|shift_reg\(158)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(158),
	combout => \u_tdm_rx|shift_reg[159]~feeder_combout\);

-- Location: FF_X17_Y10_N29
\u_tdm_rx|shift_reg[159]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[159]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(159));

-- Location: LCCOMB_X17_Y10_N2
\u_tdm_rx|shift_reg[160]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[160]~feeder_combout\ = \u_tdm_rx|shift_reg\(159)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(159),
	combout => \u_tdm_rx|shift_reg[160]~feeder_combout\);

-- Location: FF_X17_Y10_N3
\u_tdm_rx|shift_reg[160]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[160]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(160));

-- Location: LCCOMB_X17_Y10_N16
\u_tdm_rx|shift_reg[161]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[161]~feeder_combout\ = \u_tdm_rx|shift_reg\(160)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(160),
	combout => \u_tdm_rx|shift_reg[161]~feeder_combout\);

-- Location: FF_X17_Y10_N17
\u_tdm_rx|shift_reg[161]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[161]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(161));

-- Location: LCCOMB_X17_Y10_N6
\u_tdm_rx|shift_reg[162]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[162]~feeder_combout\ = \u_tdm_rx|shift_reg\(161)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(161),
	combout => \u_tdm_rx|shift_reg[162]~feeder_combout\);

-- Location: FF_X17_Y10_N7
\u_tdm_rx|shift_reg[162]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[162]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(162));

-- Location: LCCOMB_X17_Y10_N12
\u_tdm_rx|shift_reg[163]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[163]~feeder_combout\ = \u_tdm_rx|shift_reg\(162)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(162),
	combout => \u_tdm_rx|shift_reg[163]~feeder_combout\);

-- Location: FF_X17_Y10_N13
\u_tdm_rx|shift_reg[163]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[163]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(163));

-- Location: LCCOMB_X18_Y10_N20
\u_tdm_rx|shift_reg[164]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[164]~feeder_combout\ = \u_tdm_rx|shift_reg\(163)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(163),
	combout => \u_tdm_rx|shift_reg[164]~feeder_combout\);

-- Location: FF_X18_Y10_N21
\u_tdm_rx|shift_reg[164]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[164]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(164));

-- Location: LCCOMB_X18_Y10_N26
\u_tdm_rx|shift_reg[165]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[165]~feeder_combout\ = \u_tdm_rx|shift_reg\(164)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(164),
	combout => \u_tdm_rx|shift_reg[165]~feeder_combout\);

-- Location: FF_X18_Y10_N27
\u_tdm_rx|shift_reg[165]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[165]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(165));

-- Location: LCCOMB_X18_Y10_N30
\u_tdm_rx|shift_reg[166]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[166]~feeder_combout\ = \u_tdm_rx|shift_reg\(165)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(165),
	combout => \u_tdm_rx|shift_reg[166]~feeder_combout\);

-- Location: FF_X18_Y10_N31
\u_tdm_rx|shift_reg[166]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[166]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(166));

-- Location: FF_X18_Y10_N9
\u_tdm_rx|shift_reg[167]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(166),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(167));

-- Location: FF_X18_Y12_N15
\u_tdm_rx|shift_reg[168]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(167),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(168));

-- Location: FF_X14_Y12_N23
\u_tdm_rx|shift_reg[169]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(168),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(169));

-- Location: FF_X16_Y13_N17
\u_tdm_rx|shift_reg[170]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(169),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(170));

-- Location: LCCOMB_X16_Y13_N20
\u_tdm_rx|shift_reg[171]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[171]~feeder_combout\ = \u_tdm_rx|shift_reg\(170)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(170),
	combout => \u_tdm_rx|shift_reg[171]~feeder_combout\);

-- Location: FF_X16_Y13_N21
\u_tdm_rx|shift_reg[171]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[171]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(171));

-- Location: LCCOMB_X16_Y13_N2
\u_tdm_rx|shift_reg[172]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[172]~feeder_combout\ = \u_tdm_rx|shift_reg\(171)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(171),
	combout => \u_tdm_rx|shift_reg[172]~feeder_combout\);

-- Location: FF_X16_Y13_N3
\u_tdm_rx|shift_reg[172]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[172]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(172));

-- Location: LCCOMB_X16_Y13_N12
\u_tdm_rx|shift_reg[173]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[173]~feeder_combout\ = \u_tdm_rx|shift_reg\(172)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(172),
	combout => \u_tdm_rx|shift_reg[173]~feeder_combout\);

-- Location: FF_X16_Y13_N13
\u_tdm_rx|shift_reg[173]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[173]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(173));

-- Location: LCCOMB_X16_Y13_N24
\u_tdm_rx|shift_reg[174]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[174]~feeder_combout\ = \u_tdm_rx|shift_reg\(173)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(173),
	combout => \u_tdm_rx|shift_reg[174]~feeder_combout\);

-- Location: FF_X16_Y13_N25
\u_tdm_rx|shift_reg[174]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[174]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(174));

-- Location: LCCOMB_X16_Y13_N4
\u_tdm_rx|shift_reg[175]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[175]~feeder_combout\ = \u_tdm_rx|shift_reg\(174)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(174),
	combout => \u_tdm_rx|shift_reg[175]~feeder_combout\);

-- Location: FF_X16_Y13_N5
\u_tdm_rx|shift_reg[175]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[175]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(175));

-- Location: FF_X16_Y13_N7
\u_tdm_rx|shift_reg[176]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(175),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(176));

-- Location: FF_X18_Y13_N15
\u_tdm_rx|shift_reg[177]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(176),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(177));

-- Location: FF_X18_Y13_N13
\u_tdm_rx|shift_reg[178]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(177),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(178));

-- Location: LCCOMB_X18_Y13_N16
\u_tdm_rx|shift_reg[179]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[179]~feeder_combout\ = \u_tdm_rx|shift_reg\(178)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(178),
	combout => \u_tdm_rx|shift_reg[179]~feeder_combout\);

-- Location: FF_X18_Y13_N17
\u_tdm_rx|shift_reg[179]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[179]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(179));

-- Location: LCCOMB_X18_Y13_N18
\u_tdm_rx|shift_reg[180]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[180]~feeder_combout\ = \u_tdm_rx|shift_reg\(179)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(179),
	combout => \u_tdm_rx|shift_reg[180]~feeder_combout\);

-- Location: FF_X18_Y13_N19
\u_tdm_rx|shift_reg[180]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[180]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(180));

-- Location: LCCOMB_X18_Y13_N20
\u_tdm_rx|shift_reg[181]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[181]~feeder_combout\ = \u_tdm_rx|shift_reg\(180)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(180),
	combout => \u_tdm_rx|shift_reg[181]~feeder_combout\);

-- Location: FF_X18_Y13_N21
\u_tdm_rx|shift_reg[181]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[181]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(181));

-- Location: FF_X18_Y13_N25
\u_tdm_rx|shift_reg[182]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(181),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(182));

-- Location: LCCOMB_X14_Y12_N26
\u_tdm_rx|shift_reg[183]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[183]~feeder_combout\ = \u_tdm_rx|shift_reg\(182)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(182),
	combout => \u_tdm_rx|shift_reg[183]~feeder_combout\);

-- Location: FF_X14_Y12_N27
\u_tdm_rx|shift_reg[183]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[183]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(183));

-- Location: FF_X14_Y12_N25
\u_tdm_rx|shift_reg[184]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(183),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(184));

-- Location: LCCOMB_X14_Y12_N4
\u_tdm_rx|shift_reg[185]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[185]~feeder_combout\ = \u_tdm_rx|shift_reg\(184)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(184),
	combout => \u_tdm_rx|shift_reg[185]~feeder_combout\);

-- Location: FF_X14_Y12_N5
\u_tdm_rx|shift_reg[185]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[185]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(185));

-- Location: FF_X14_Y12_N31
\u_tdm_rx|shift_reg[186]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(185),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(186));

-- Location: LCCOMB_X16_Y12_N8
\u_tdm_rx|shift_reg[187]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[187]~feeder_combout\ = \u_tdm_rx|shift_reg\(186)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(186),
	combout => \u_tdm_rx|shift_reg[187]~feeder_combout\);

-- Location: FF_X16_Y12_N9
\u_tdm_rx|shift_reg[187]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[187]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(187));

-- Location: LCCOMB_X16_Y12_N30
\u_tdm_rx|shift_reg[188]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[188]~feeder_combout\ = \u_tdm_rx|shift_reg\(187)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(187),
	combout => \u_tdm_rx|shift_reg[188]~feeder_combout\);

-- Location: FF_X16_Y12_N31
\u_tdm_rx|shift_reg[188]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[188]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(188));

-- Location: FF_X14_Y12_N7
\u_tdm_rx|lrclk_prev\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_master|lrclk_reg~q\,
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|lrclk_prev~q\);

-- Location: LCCOMB_X14_Y12_N6
\u_tdm_rx|process_0~0\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|process_0~0_combout\ = (\u_tdm_master|lrclk_reg~q\ & !\u_tdm_rx|lrclk_prev~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000110000001100",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_master|lrclk_reg~q\,
	datac => \u_tdm_rx|lrclk_prev~q\,
	combout => \u_tdm_rx|process_0~0_combout\);

-- Location: FF_X16_Y12_N29
\u_tdm_rx|ch_data_out[188]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(188),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(188));

-- Location: LCCOMB_X16_Y12_N16
\Add2~21\ : cycloneive_lcell_comb
-- Equation(s):
-- \Add2~21_combout\ = (startup_ignore(1) & ((expected_count(20)))) # (!startup_ignore(1) & (\u_tdm_rx|ch_data_out\(188)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111110000001100",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \u_tdm_rx|ch_data_out\(188),
	datac => startup_ignore(1),
	datad => expected_count(20),
	combout => \Add2~21_combout\);

-- Location: FF_X16_Y12_N5
\u_tdm_rx|ch_data_out[186]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(186),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(186));

-- Location: FF_X14_Y12_N13
\u_tdm_rx|ch_data_out[183]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(183),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(183));

-- Location: FF_X18_Y13_N31
\u_tdm_rx|ch_data_out[181]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(181),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(181));

-- Location: FF_X18_Y13_N11
\u_tdm_rx|ch_data_out[179]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(179),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(179));

-- Location: FF_X18_Y13_N5
\u_tdm_rx|ch_data_out[178]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(178),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(178));

-- Location: FF_X16_Y13_N27
\u_tdm_rx|ch_data_out[175]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(175),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(175));

-- Location: FF_X16_Y13_N31
\u_tdm_rx|ch_data_out[173]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(173),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(173));

-- Location: FF_X16_Y13_N29
\u_tdm_rx|ch_data_out[172]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(172),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(172));

-- Location: FF_X14_Y12_N21
\u_tdm_rx|ch_data_out[169]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(169),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(169));

-- Location: LCCOMB_X17_Y13_N8
\expected_count[0]~24\ : cycloneive_lcell_comb
-- Equation(s):
-- \expected_count[0]~24_combout\ = \Add2~1_combout\ $ (VCC)
-- \expected_count[0]~25\ = CARRY(\Add2~1_combout\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0011001111001100",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \Add2~1_combout\,
	datad => VCC,
	combout => \expected_count[0]~24_combout\,
	cout => \expected_count[0]~25\);

-- Location: LCCOMB_X17_Y12_N26
\process_1~72\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~72_combout\ = (!\u_tdm_master|lrclk_reg~q\ & \lrclk_prev~q\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0101010100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_master|lrclk_reg~q\,
	datad => \lrclk_prev~q\,
	combout => \process_1~72_combout\);

-- Location: FF_X17_Y13_N9
\expected_count[0]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \expected_count[0]~24_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \process_1~72_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => expected_count(0));

-- Location: FF_X14_Y12_N17
\u_tdm_rx|ch_data_out[168]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(168),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(168));

-- Location: LCCOMB_X14_Y12_N10
\Add2~1\ : cycloneive_lcell_comb
-- Equation(s):
-- \Add2~1_combout\ = (startup_ignore(1) & (expected_count(0))) # (!startup_ignore(1) & ((\u_tdm_rx|ch_data_out\(168))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111010110100000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => startup_ignore(1),
	datac => expected_count(0),
	datad => \u_tdm_rx|ch_data_out\(168),
	combout => \Add2~1_combout\);

-- Location: LCCOMB_X17_Y13_N10
\expected_count[1]~26\ : cycloneive_lcell_comb
-- Equation(s):
-- \expected_count[1]~26_combout\ = (\Add2~0_combout\ & (!\expected_count[0]~25\)) # (!\Add2~0_combout\ & ((\expected_count[0]~25\) # (GND)))
-- \expected_count[1]~27\ = CARRY((!\expected_count[0]~25\) # (!\Add2~0_combout\))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0011110000111111",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	datab => \Add2~0_combout\,
	datad => VCC,
	cin => \expected_count[0]~25\,
	combout => \expected_count[1]~26_combout\,
	cout => \expected_count[1]~27\);

-- Location: FF_X17_Y13_N11
\expected_count[1]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \expected_count[1]~26_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \process_1~72_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => expected_count(1));

-- Location: LCCOMB_X14_Y12_N20
\Add2~0\ : cycloneive_lcell_comb
-- Equation(s):
-- \Add2~0_combout\ = (startup_ignore(1) & ((expected_count(1)))) # (!startup_ignore(1) & (\u_tdm_rx|ch_data_out\(169)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111101001010000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => startup_ignore(1),
	datac => \u_tdm_rx|ch_data_out\(169),
	datad => expected_count(1),
	combout => \Add2~0_combout\);

-- Location: LCCOMB_X17_Y13_N12
\expected_count[2]~28\ : cycloneive_lcell_comb
-- Equation(s):
-- \expected_count[2]~28_combout\ = (\Add2~3_combout\ & (\expected_count[1]~27\ $ (GND))) # (!\Add2~3_combout\ & (!\expected_count[1]~27\ & VCC))
-- \expected_count[2]~29\ = CARRY((\Add2~3_combout\ & !\expected_count[1]~27\))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1010010100001010",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	dataa => \Add2~3_combout\,
	datad => VCC,
	cin => \expected_count[1]~27\,
	combout => \expected_count[2]~28_combout\,
	cout => \expected_count[2]~29\);

-- Location: FF_X17_Y13_N13
\expected_count[2]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \expected_count[2]~28_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \process_1~72_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => expected_count(2));

-- Location: FF_X16_Y13_N11
\u_tdm_rx|ch_data_out[170]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(170),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(170));

-- Location: LCCOMB_X16_Y13_N16
\Add2~3\ : cycloneive_lcell_comb
-- Equation(s):
-- \Add2~3_combout\ = (startup_ignore(1) & (expected_count(2))) # (!startup_ignore(1) & ((\u_tdm_rx|ch_data_out\(170))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1101110110001000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => startup_ignore(1),
	datab => expected_count(2),
	datad => \u_tdm_rx|ch_data_out\(170),
	combout => \Add2~3_combout\);

-- Location: LCCOMB_X17_Y13_N14
\expected_count[3]~30\ : cycloneive_lcell_comb
-- Equation(s):
-- \expected_count[3]~30_combout\ = (\Add2~2_combout\ & (!\expected_count[2]~29\)) # (!\Add2~2_combout\ & ((\expected_count[2]~29\) # (GND)))
-- \expected_count[3]~31\ = CARRY((!\expected_count[2]~29\) # (!\Add2~2_combout\))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0101101001011111",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	dataa => \Add2~2_combout\,
	datad => VCC,
	cin => \expected_count[2]~29\,
	combout => \expected_count[3]~30_combout\,
	cout => \expected_count[3]~31\);

-- Location: FF_X17_Y13_N15
\expected_count[3]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \expected_count[3]~30_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \process_1~72_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => expected_count(3));

-- Location: FF_X16_Y13_N9
\u_tdm_rx|ch_data_out[171]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(171),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(171));

-- Location: LCCOMB_X16_Y13_N8
\Add2~2\ : cycloneive_lcell_comb
-- Equation(s):
-- \Add2~2_combout\ = (startup_ignore(1) & (expected_count(3))) # (!startup_ignore(1) & ((\u_tdm_rx|ch_data_out\(171))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1100110011110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => expected_count(3),
	datac => \u_tdm_rx|ch_data_out\(171),
	datad => startup_ignore(1),
	combout => \Add2~2_combout\);

-- Location: LCCOMB_X17_Y13_N16
\expected_count[4]~32\ : cycloneive_lcell_comb
-- Equation(s):
-- \expected_count[4]~32_combout\ = (\Add2~5_combout\ & (\expected_count[3]~31\ $ (GND))) # (!\Add2~5_combout\ & (!\expected_count[3]~31\ & VCC))
-- \expected_count[4]~33\ = CARRY((\Add2~5_combout\ & !\expected_count[3]~31\))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1100001100001100",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	datab => \Add2~5_combout\,
	datad => VCC,
	cin => \expected_count[3]~31\,
	combout => \expected_count[4]~32_combout\,
	cout => \expected_count[4]~33\);

-- Location: FF_X17_Y13_N17
\expected_count[4]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \expected_count[4]~32_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \process_1~72_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => expected_count(4));

-- Location: LCCOMB_X16_Y13_N6
\Add2~5\ : cycloneive_lcell_comb
-- Equation(s):
-- \Add2~5_combout\ = (startup_ignore(1) & ((expected_count(4)))) # (!startup_ignore(1) & (\u_tdm_rx|ch_data_out\(172)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1100110010101010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(172),
	datab => expected_count(4),
	datad => startup_ignore(1),
	combout => \Add2~5_combout\);

-- Location: LCCOMB_X17_Y13_N18
\expected_count[5]~34\ : cycloneive_lcell_comb
-- Equation(s):
-- \expected_count[5]~34_combout\ = (\Add2~4_combout\ & (!\expected_count[4]~33\)) # (!\Add2~4_combout\ & ((\expected_count[4]~33\) # (GND)))
-- \expected_count[5]~35\ = CARRY((!\expected_count[4]~33\) # (!\Add2~4_combout\))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0011110000111111",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	datab => \Add2~4_combout\,
	datad => VCC,
	cin => \expected_count[4]~33\,
	combout => \expected_count[5]~34_combout\,
	cout => \expected_count[5]~35\);

-- Location: FF_X17_Y13_N19
\expected_count[5]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \expected_count[5]~34_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \process_1~72_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => expected_count(5));

-- Location: LCCOMB_X16_Y13_N30
\Add2~4\ : cycloneive_lcell_comb
-- Equation(s):
-- \Add2~4_combout\ = (startup_ignore(1) & ((expected_count(5)))) # (!startup_ignore(1) & (\u_tdm_rx|ch_data_out\(173)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111101001010000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => startup_ignore(1),
	datac => \u_tdm_rx|ch_data_out\(173),
	datad => expected_count(5),
	combout => \Add2~4_combout\);

-- Location: LCCOMB_X17_Y13_N20
\expected_count[6]~36\ : cycloneive_lcell_comb
-- Equation(s):
-- \expected_count[6]~36_combout\ = (\Add2~7_combout\ & (\expected_count[5]~35\ $ (GND))) # (!\Add2~7_combout\ & (!\expected_count[5]~35\ & VCC))
-- \expected_count[6]~37\ = CARRY((\Add2~7_combout\ & !\expected_count[5]~35\))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1010010100001010",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	dataa => \Add2~7_combout\,
	datad => VCC,
	cin => \expected_count[5]~35\,
	combout => \expected_count[6]~36_combout\,
	cout => \expected_count[6]~37\);

-- Location: FF_X17_Y13_N21
\expected_count[6]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \expected_count[6]~36_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \process_1~72_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => expected_count(6));

-- Location: FF_X16_Y13_N19
\u_tdm_rx|ch_data_out[174]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(174),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(174));

-- Location: LCCOMB_X16_Y13_N14
\Add2~7\ : cycloneive_lcell_comb
-- Equation(s):
-- \Add2~7_combout\ = (startup_ignore(1) & (expected_count(6))) # (!startup_ignore(1) & ((\u_tdm_rx|ch_data_out\(174))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111010110100000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => startup_ignore(1),
	datac => expected_count(6),
	datad => \u_tdm_rx|ch_data_out\(174),
	combout => \Add2~7_combout\);

-- Location: LCCOMB_X17_Y13_N22
\expected_count[7]~38\ : cycloneive_lcell_comb
-- Equation(s):
-- \expected_count[7]~38_combout\ = (\Add2~6_combout\ & (!\expected_count[6]~37\)) # (!\Add2~6_combout\ & ((\expected_count[6]~37\) # (GND)))
-- \expected_count[7]~39\ = CARRY((!\expected_count[6]~37\) # (!\Add2~6_combout\))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0101101001011111",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	dataa => \Add2~6_combout\,
	datad => VCC,
	cin => \expected_count[6]~37\,
	combout => \expected_count[7]~38_combout\,
	cout => \expected_count[7]~39\);

-- Location: FF_X17_Y13_N23
\expected_count[7]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \expected_count[7]~38_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \process_1~72_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => expected_count(7));

-- Location: LCCOMB_X16_Y13_N26
\Add2~6\ : cycloneive_lcell_comb
-- Equation(s):
-- \Add2~6_combout\ = (startup_ignore(1) & ((expected_count(7)))) # (!startup_ignore(1) & (\u_tdm_rx|ch_data_out\(175)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111101001010000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => startup_ignore(1),
	datac => \u_tdm_rx|ch_data_out\(175),
	datad => expected_count(7),
	combout => \Add2~6_combout\);

-- Location: LCCOMB_X17_Y13_N24
\expected_count[8]~40\ : cycloneive_lcell_comb
-- Equation(s):
-- \expected_count[8]~40_combout\ = (\Add2~9_combout\ & (\expected_count[7]~39\ $ (GND))) # (!\Add2~9_combout\ & (!\expected_count[7]~39\ & VCC))
-- \expected_count[8]~41\ = CARRY((\Add2~9_combout\ & !\expected_count[7]~39\))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1100001100001100",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	datab => \Add2~9_combout\,
	datad => VCC,
	cin => \expected_count[7]~39\,
	combout => \expected_count[8]~40_combout\,
	cout => \expected_count[8]~41\);

-- Location: FF_X17_Y13_N25
\expected_count[8]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \expected_count[8]~40_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \process_1~72_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => expected_count(8));

-- Location: FF_X17_Y13_N1
\u_tdm_rx|ch_data_out[176]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(176),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(176));

-- Location: LCCOMB_X17_Y13_N2
\Add2~9\ : cycloneive_lcell_comb
-- Equation(s):
-- \Add2~9_combout\ = (startup_ignore(1) & (expected_count(8))) # (!startup_ignore(1) & ((\u_tdm_rx|ch_data_out\(176))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111001111000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => startup_ignore(1),
	datac => expected_count(8),
	datad => \u_tdm_rx|ch_data_out\(176),
	combout => \Add2~9_combout\);

-- Location: LCCOMB_X17_Y13_N26
\expected_count[9]~42\ : cycloneive_lcell_comb
-- Equation(s):
-- \expected_count[9]~42_combout\ = (\Add2~8_combout\ & (!\expected_count[8]~41\)) # (!\Add2~8_combout\ & ((\expected_count[8]~41\) # (GND)))
-- \expected_count[9]~43\ = CARRY((!\expected_count[8]~41\) # (!\Add2~8_combout\))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0101101001011111",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	dataa => \Add2~8_combout\,
	datad => VCC,
	cin => \expected_count[8]~41\,
	combout => \expected_count[9]~42_combout\,
	cout => \expected_count[9]~43\);

-- Location: FF_X17_Y13_N27
\expected_count[9]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \expected_count[9]~42_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \process_1~72_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => expected_count(9));

-- Location: FF_X18_Y13_N29
\u_tdm_rx|ch_data_out[177]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(177),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(177));

-- Location: LCCOMB_X18_Y13_N28
\Add2~8\ : cycloneive_lcell_comb
-- Equation(s):
-- \Add2~8_combout\ = (startup_ignore(1) & (expected_count(9))) # (!startup_ignore(1) & ((\u_tdm_rx|ch_data_out\(177))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1011100010111000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => expected_count(9),
	datab => startup_ignore(1),
	datac => \u_tdm_rx|ch_data_out\(177),
	combout => \Add2~8_combout\);

-- Location: LCCOMB_X17_Y13_N28
\expected_count[10]~44\ : cycloneive_lcell_comb
-- Equation(s):
-- \expected_count[10]~44_combout\ = (\Add2~11_combout\ & (\expected_count[9]~43\ $ (GND))) # (!\Add2~11_combout\ & (!\expected_count[9]~43\ & VCC))
-- \expected_count[10]~45\ = CARRY((\Add2~11_combout\ & !\expected_count[9]~43\))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1100001100001100",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	datab => \Add2~11_combout\,
	datad => VCC,
	cin => \expected_count[9]~43\,
	combout => \expected_count[10]~44_combout\,
	cout => \expected_count[10]~45\);

-- Location: FF_X17_Y13_N29
\expected_count[10]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \expected_count[10]~44_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \process_1~72_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => expected_count(10));

-- Location: LCCOMB_X18_Y13_N24
\Add2~11\ : cycloneive_lcell_comb
-- Equation(s):
-- \Add2~11_combout\ = (startup_ignore(1) & ((expected_count(10)))) # (!startup_ignore(1) & (\u_tdm_rx|ch_data_out\(178)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1110111000100010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(178),
	datab => startup_ignore(1),
	datad => expected_count(10),
	combout => \Add2~11_combout\);

-- Location: LCCOMB_X17_Y13_N30
\expected_count[11]~46\ : cycloneive_lcell_comb
-- Equation(s):
-- \expected_count[11]~46_combout\ = (\Add2~10_combout\ & (!\expected_count[10]~45\)) # (!\Add2~10_combout\ & ((\expected_count[10]~45\) # (GND)))
-- \expected_count[11]~47\ = CARRY((!\expected_count[10]~45\) # (!\Add2~10_combout\))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0011110000111111",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	datab => \Add2~10_combout\,
	datad => VCC,
	cin => \expected_count[10]~45\,
	combout => \expected_count[11]~46_combout\,
	cout => \expected_count[11]~47\);

-- Location: FF_X17_Y13_N31
\expected_count[11]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \expected_count[11]~46_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \process_1~72_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => expected_count(11));

-- Location: LCCOMB_X18_Y13_N10
\Add2~10\ : cycloneive_lcell_comb
-- Equation(s):
-- \Add2~10_combout\ = (startup_ignore(1) & ((expected_count(11)))) # (!startup_ignore(1) & (\u_tdm_rx|ch_data_out\(179)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111110000110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => startup_ignore(1),
	datac => \u_tdm_rx|ch_data_out\(179),
	datad => expected_count(11),
	combout => \Add2~10_combout\);

-- Location: LCCOMB_X17_Y12_N0
\expected_count[12]~48\ : cycloneive_lcell_comb
-- Equation(s):
-- \expected_count[12]~48_combout\ = (\Add2~13_combout\ & (\expected_count[11]~47\ $ (GND))) # (!\Add2~13_combout\ & (!\expected_count[11]~47\ & VCC))
-- \expected_count[12]~49\ = CARRY((\Add2~13_combout\ & !\expected_count[11]~47\))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1100001100001100",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	datab => \Add2~13_combout\,
	datad => VCC,
	cin => \expected_count[11]~47\,
	combout => \expected_count[12]~48_combout\,
	cout => \expected_count[12]~49\);

-- Location: FF_X17_Y12_N1
\expected_count[12]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \expected_count[12]~48_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \process_1~72_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => expected_count(12));

-- Location: FF_X18_Y13_N23
\u_tdm_rx|ch_data_out[180]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(180),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(180));

-- Location: LCCOMB_X18_Y13_N14
\Add2~13\ : cycloneive_lcell_comb
-- Equation(s):
-- \Add2~13_combout\ = (startup_ignore(1) & (expected_count(12))) # (!startup_ignore(1) & ((\u_tdm_rx|ch_data_out\(180))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1011101110001000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => expected_count(12),
	datab => startup_ignore(1),
	datad => \u_tdm_rx|ch_data_out\(180),
	combout => \Add2~13_combout\);

-- Location: LCCOMB_X17_Y12_N2
\expected_count[13]~50\ : cycloneive_lcell_comb
-- Equation(s):
-- \expected_count[13]~50_combout\ = (\Add2~12_combout\ & (!\expected_count[12]~49\)) # (!\Add2~12_combout\ & ((\expected_count[12]~49\) # (GND)))
-- \expected_count[13]~51\ = CARRY((!\expected_count[12]~49\) # (!\Add2~12_combout\))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0101101001011111",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	dataa => \Add2~12_combout\,
	datad => VCC,
	cin => \expected_count[12]~49\,
	combout => \expected_count[13]~50_combout\,
	cout => \expected_count[13]~51\);

-- Location: FF_X17_Y12_N3
\expected_count[13]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \expected_count[13]~50_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \process_1~72_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => expected_count(13));

-- Location: LCCOMB_X18_Y13_N30
\Add2~12\ : cycloneive_lcell_comb
-- Equation(s):
-- \Add2~12_combout\ = (startup_ignore(1) & ((expected_count(13)))) # (!startup_ignore(1) & (\u_tdm_rx|ch_data_out\(181)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111110000110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => startup_ignore(1),
	datac => \u_tdm_rx|ch_data_out\(181),
	datad => expected_count(13),
	combout => \Add2~12_combout\);

-- Location: LCCOMB_X17_Y12_N4
\expected_count[14]~52\ : cycloneive_lcell_comb
-- Equation(s):
-- \expected_count[14]~52_combout\ = (\Add2~15_combout\ & (\expected_count[13]~51\ $ (GND))) # (!\Add2~15_combout\ & (!\expected_count[13]~51\ & VCC))
-- \expected_count[14]~53\ = CARRY((\Add2~15_combout\ & !\expected_count[13]~51\))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1010010100001010",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	dataa => \Add2~15_combout\,
	datad => VCC,
	cin => \expected_count[13]~51\,
	combout => \expected_count[14]~52_combout\,
	cout => \expected_count[14]~53\);

-- Location: FF_X17_Y12_N5
\expected_count[14]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \expected_count[14]~52_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \process_1~72_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => expected_count(14));

-- Location: FF_X14_Y12_N9
\u_tdm_rx|ch_data_out[182]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(182),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(182));

-- Location: LCCOMB_X14_Y12_N30
\Add2~15\ : cycloneive_lcell_comb
-- Equation(s):
-- \Add2~15_combout\ = (startup_ignore(1) & (expected_count(14))) # (!startup_ignore(1) & ((\u_tdm_rx|ch_data_out\(182))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1101110110001000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => startup_ignore(1),
	datab => expected_count(14),
	datad => \u_tdm_rx|ch_data_out\(182),
	combout => \Add2~15_combout\);

-- Location: LCCOMB_X17_Y12_N6
\expected_count[15]~54\ : cycloneive_lcell_comb
-- Equation(s):
-- \expected_count[15]~54_combout\ = (\Add2~14_combout\ & (!\expected_count[14]~53\)) # (!\Add2~14_combout\ & ((\expected_count[14]~53\) # (GND)))
-- \expected_count[15]~55\ = CARRY((!\expected_count[14]~53\) # (!\Add2~14_combout\))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0101101001011111",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	dataa => \Add2~14_combout\,
	datad => VCC,
	cin => \expected_count[14]~53\,
	combout => \expected_count[15]~54_combout\,
	cout => \expected_count[15]~55\);

-- Location: FF_X17_Y12_N7
\expected_count[15]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \expected_count[15]~54_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \process_1~72_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => expected_count(15));

-- Location: LCCOMB_X14_Y12_N12
\Add2~14\ : cycloneive_lcell_comb
-- Equation(s):
-- \Add2~14_combout\ = (startup_ignore(1) & ((expected_count(15)))) # (!startup_ignore(1) & (\u_tdm_rx|ch_data_out\(183)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111101001010000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => startup_ignore(1),
	datac => \u_tdm_rx|ch_data_out\(183),
	datad => expected_count(15),
	combout => \Add2~14_combout\);

-- Location: LCCOMB_X17_Y12_N8
\expected_count[16]~56\ : cycloneive_lcell_comb
-- Equation(s):
-- \expected_count[16]~56_combout\ = (\Add2~17_combout\ & (\expected_count[15]~55\ $ (GND))) # (!\Add2~17_combout\ & (!\expected_count[15]~55\ & VCC))
-- \expected_count[16]~57\ = CARRY((\Add2~17_combout\ & !\expected_count[15]~55\))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1100001100001100",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	datab => \Add2~17_combout\,
	datad => VCC,
	cin => \expected_count[15]~55\,
	combout => \expected_count[16]~56_combout\,
	cout => \expected_count[16]~57\);

-- Location: FF_X17_Y12_N9
\expected_count[16]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \expected_count[16]~56_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \process_1~72_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => expected_count(16));

-- Location: FF_X14_Y12_N19
\u_tdm_rx|ch_data_out[184]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(184),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(184));

-- Location: LCCOMB_X14_Y12_N14
\Add2~17\ : cycloneive_lcell_comb
-- Equation(s):
-- \Add2~17_combout\ = (startup_ignore(1) & (expected_count(16))) # (!startup_ignore(1) & ((\u_tdm_rx|ch_data_out\(184))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1010101011001100",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => expected_count(16),
	datab => \u_tdm_rx|ch_data_out\(184),
	datad => startup_ignore(1),
	combout => \Add2~17_combout\);

-- Location: LCCOMB_X17_Y12_N10
\expected_count[17]~58\ : cycloneive_lcell_comb
-- Equation(s):
-- \expected_count[17]~58_combout\ = (\Add2~16_combout\ & (!\expected_count[16]~57\)) # (!\Add2~16_combout\ & ((\expected_count[16]~57\) # (GND)))
-- \expected_count[17]~59\ = CARRY((!\expected_count[16]~57\) # (!\Add2~16_combout\))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0011110000111111",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	datab => \Add2~16_combout\,
	datad => VCC,
	cin => \expected_count[16]~57\,
	combout => \expected_count[17]~58_combout\,
	cout => \expected_count[17]~59\);

-- Location: FF_X17_Y12_N11
\expected_count[17]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \expected_count[17]~58_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \process_1~72_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => expected_count(17));

-- Location: FF_X14_Y12_N29
\u_tdm_rx|ch_data_out[185]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(185),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(185));

-- Location: LCCOMB_X14_Y12_N28
\Add2~16\ : cycloneive_lcell_comb
-- Equation(s):
-- \Add2~16_combout\ = (startup_ignore(1) & (expected_count(17))) # (!startup_ignore(1) & ((\u_tdm_rx|ch_data_out\(185))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1101100011011000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => startup_ignore(1),
	datab => expected_count(17),
	datac => \u_tdm_rx|ch_data_out\(185),
	combout => \Add2~16_combout\);

-- Location: LCCOMB_X17_Y12_N12
\expected_count[18]~60\ : cycloneive_lcell_comb
-- Equation(s):
-- \expected_count[18]~60_combout\ = (\Add2~19_combout\ & (\expected_count[17]~59\ $ (GND))) # (!\Add2~19_combout\ & (!\expected_count[17]~59\ & VCC))
-- \expected_count[18]~61\ = CARRY((\Add2~19_combout\ & !\expected_count[17]~59\))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1010010100001010",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	dataa => \Add2~19_combout\,
	datad => VCC,
	cin => \expected_count[17]~59\,
	combout => \expected_count[18]~60_combout\,
	cout => \expected_count[18]~61\);

-- Location: FF_X17_Y12_N13
\expected_count[18]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \expected_count[18]~60_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \process_1~72_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => expected_count(18));

-- Location: LCCOMB_X16_Y12_N26
\Add2~19\ : cycloneive_lcell_comb
-- Equation(s):
-- \Add2~19_combout\ = (startup_ignore(1) & ((expected_count(18)))) # (!startup_ignore(1) & (\u_tdm_rx|ch_data_out\(186)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1110010011100100",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => startup_ignore(1),
	datab => \u_tdm_rx|ch_data_out\(186),
	datac => expected_count(18),
	combout => \Add2~19_combout\);

-- Location: LCCOMB_X17_Y12_N14
\expected_count[19]~62\ : cycloneive_lcell_comb
-- Equation(s):
-- \expected_count[19]~62_combout\ = (\Add2~18_combout\ & (!\expected_count[18]~61\)) # (!\Add2~18_combout\ & ((\expected_count[18]~61\) # (GND)))
-- \expected_count[19]~63\ = CARRY((!\expected_count[18]~61\) # (!\Add2~18_combout\))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0011110000111111",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	datab => \Add2~18_combout\,
	datad => VCC,
	cin => \expected_count[18]~61\,
	combout => \expected_count[19]~62_combout\,
	cout => \expected_count[19]~63\);

-- Location: FF_X17_Y12_N15
\expected_count[19]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \expected_count[19]~62_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \process_1~72_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => expected_count(19));

-- Location: FF_X16_Y12_N7
\u_tdm_rx|ch_data_out[187]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(187),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(187));

-- Location: LCCOMB_X16_Y12_N6
\Add2~18\ : cycloneive_lcell_comb
-- Equation(s):
-- \Add2~18_combout\ = (startup_ignore(1) & (expected_count(19))) # (!startup_ignore(1) & ((\u_tdm_rx|ch_data_out\(187))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1101100011011000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => startup_ignore(1),
	datab => expected_count(19),
	datac => \u_tdm_rx|ch_data_out\(187),
	combout => \Add2~18_combout\);

-- Location: LCCOMB_X17_Y12_N16
\expected_count[20]~64\ : cycloneive_lcell_comb
-- Equation(s):
-- \expected_count[20]~64_combout\ = (\Add2~21_combout\ & (\expected_count[19]~63\ $ (GND))) # (!\Add2~21_combout\ & (!\expected_count[19]~63\ & VCC))
-- \expected_count[20]~65\ = CARRY((\Add2~21_combout\ & !\expected_count[19]~63\))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1010010100001010",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	dataa => \Add2~21_combout\,
	datad => VCC,
	cin => \expected_count[19]~63\,
	combout => \expected_count[20]~64_combout\,
	cout => \expected_count[20]~65\);

-- Location: FF_X17_Y12_N17
\expected_count[20]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \expected_count[20]~64_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \process_1~72_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => expected_count(20));

-- Location: FF_X16_Y12_N25
\u_tdm_rx|shift_reg[189]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(188),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(189));

-- Location: FF_X16_Y12_N19
\u_tdm_rx|ch_data_out[189]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(189),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(189));

-- Location: LCCOMB_X16_Y12_N18
\Add2~20\ : cycloneive_lcell_comb
-- Equation(s):
-- \Add2~20_combout\ = (startup_ignore(1) & ((expected_count(21)))) # (!startup_ignore(1) & (\u_tdm_rx|ch_data_out\(189)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111101001010000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => startup_ignore(1),
	datac => \u_tdm_rx|ch_data_out\(189),
	datad => expected_count(21),
	combout => \Add2~20_combout\);

-- Location: LCCOMB_X17_Y12_N18
\expected_count[21]~66\ : cycloneive_lcell_comb
-- Equation(s):
-- \expected_count[21]~66_combout\ = (\Add2~20_combout\ & (!\expected_count[20]~65\)) # (!\Add2~20_combout\ & ((\expected_count[20]~65\) # (GND)))
-- \expected_count[21]~67\ = CARRY((!\expected_count[20]~65\) # (!\Add2~20_combout\))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0011110000111111",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	datab => \Add2~20_combout\,
	datad => VCC,
	cin => \expected_count[20]~65\,
	combout => \expected_count[21]~66_combout\,
	cout => \expected_count[21]~67\);

-- Location: FF_X17_Y12_N19
\expected_count[21]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \expected_count[21]~66_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \process_1~72_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => expected_count(21));

-- Location: LCCOMB_X16_Y12_N28
\process_1~12\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~12_combout\ = (expected_count(20) & (\u_tdm_rx|ch_data_out\(188) & (\u_tdm_rx|ch_data_out\(189) $ (!expected_count(21))))) # (!expected_count(20) & (!\u_tdm_rx|ch_data_out\(188) & (\u_tdm_rx|ch_data_out\(189) $ (!expected_count(21)))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1000010000100001",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => expected_count(20),
	datab => \u_tdm_rx|ch_data_out\(189),
	datac => \u_tdm_rx|ch_data_out\(188),
	datad => expected_count(21),
	combout => \process_1~12_combout\);

-- Location: LCCOMB_X14_Y12_N18
\process_1~10\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~10_combout\ = (expected_count(16) & (\u_tdm_rx|ch_data_out\(184) & (expected_count(17) $ (!\u_tdm_rx|ch_data_out\(185))))) # (!expected_count(16) & (!\u_tdm_rx|ch_data_out\(184) & (expected_count(17) $ (!\u_tdm_rx|ch_data_out\(185)))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1000010000100001",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => expected_count(16),
	datab => expected_count(17),
	datac => \u_tdm_rx|ch_data_out\(184),
	datad => \u_tdm_rx|ch_data_out\(185),
	combout => \process_1~10_combout\);

-- Location: LCCOMB_X16_Y12_N20
\u_tdm_rx|shift_reg[190]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[190]~feeder_combout\ = \u_tdm_rx|shift_reg\(189)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(189),
	combout => \u_tdm_rx|shift_reg[190]~feeder_combout\);

-- Location: FF_X16_Y12_N21
\u_tdm_rx|shift_reg[190]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[190]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(190));

-- Location: FF_X16_Y12_N23
\u_tdm_rx|ch_data_out[190]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(190),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(190));

-- Location: LCCOMB_X16_Y12_N0
\Add2~23\ : cycloneive_lcell_comb
-- Equation(s):
-- \Add2~23_combout\ = (startup_ignore(1) & (expected_count(22))) # (!startup_ignore(1) & ((\u_tdm_rx|ch_data_out\(190))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111010110100000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => startup_ignore(1),
	datac => expected_count(22),
	datad => \u_tdm_rx|ch_data_out\(190),
	combout => \Add2~23_combout\);

-- Location: LCCOMB_X17_Y12_N20
\expected_count[22]~68\ : cycloneive_lcell_comb
-- Equation(s):
-- \expected_count[22]~68_combout\ = (\Add2~23_combout\ & (\expected_count[21]~67\ $ (GND))) # (!\Add2~23_combout\ & (!\expected_count[21]~67\ & VCC))
-- \expected_count[22]~69\ = CARRY((\Add2~23_combout\ & !\expected_count[21]~67\))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1010010100001010",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	dataa => \Add2~23_combout\,
	datad => VCC,
	cin => \expected_count[21]~67\,
	combout => \expected_count[22]~68_combout\,
	cout => \expected_count[22]~69\);

-- Location: FF_X17_Y12_N21
\expected_count[22]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \expected_count[22]~68_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \process_1~72_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => expected_count(22));

-- Location: LCCOMB_X16_Y12_N10
\u_tdm_rx|shift_reg[191]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|shift_reg[191]~feeder_combout\ = \u_tdm_rx|shift_reg\(190)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(190),
	combout => \u_tdm_rx|shift_reg[191]~feeder_combout\);

-- Location: FF_X16_Y12_N11
\u_tdm_rx|shift_reg[191]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|shift_reg[191]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|shift_reg\(191));

-- Location: FF_X16_Y12_N15
\u_tdm_rx|ch_data_out[191]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(191),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(191));

-- Location: LCCOMB_X16_Y12_N14
\Add2~22\ : cycloneive_lcell_comb
-- Equation(s):
-- \Add2~22_combout\ = (startup_ignore(1) & ((expected_count(23)))) # (!startup_ignore(1) & (\u_tdm_rx|ch_data_out\(191)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111101001010000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => startup_ignore(1),
	datac => \u_tdm_rx|ch_data_out\(191),
	datad => expected_count(23),
	combout => \Add2~22_combout\);

-- Location: LCCOMB_X17_Y12_N22
\expected_count[23]~70\ : cycloneive_lcell_comb
-- Equation(s):
-- \expected_count[23]~70_combout\ = \expected_count[22]~69\ $ (\Add2~22_combout\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000111111110000",
	sum_lutc_input => "cin")
-- pragma translate_on
PORT MAP (
	datad => \Add2~22_combout\,
	cin => \expected_count[22]~69\,
	combout => \expected_count[23]~70_combout\);

-- Location: FF_X17_Y12_N23
\expected_count[23]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \expected_count[23]~70_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \process_1~72_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => expected_count(23));

-- Location: LCCOMB_X16_Y12_N22
\process_1~13\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~13_combout\ = (expected_count(22) & (\u_tdm_rx|ch_data_out\(190) & (\u_tdm_rx|ch_data_out\(191) $ (!expected_count(23))))) # (!expected_count(22) & (!\u_tdm_rx|ch_data_out\(190) & (\u_tdm_rx|ch_data_out\(191) $ (!expected_count(23)))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1000010000100001",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => expected_count(22),
	datab => \u_tdm_rx|ch_data_out\(191),
	datac => \u_tdm_rx|ch_data_out\(190),
	datad => expected_count(23),
	combout => \process_1~13_combout\);

-- Location: LCCOMB_X16_Y12_N4
\process_1~11\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~11_combout\ = (expected_count(19) & (\u_tdm_rx|ch_data_out\(187) & (expected_count(18) $ (!\u_tdm_rx|ch_data_out\(186))))) # (!expected_count(19) & (!\u_tdm_rx|ch_data_out\(187) & (expected_count(18) $ (!\u_tdm_rx|ch_data_out\(186)))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1000001001000001",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => expected_count(19),
	datab => expected_count(18),
	datac => \u_tdm_rx|ch_data_out\(186),
	datad => \u_tdm_rx|ch_data_out\(187),
	combout => \process_1~11_combout\);

-- Location: LCCOMB_X16_Y12_N12
\process_1~14\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~14_combout\ = (\process_1~12_combout\ & (\process_1~10_combout\ & (\process_1~13_combout\ & \process_1~11_combout\)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1000000000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \process_1~12_combout\,
	datab => \process_1~10_combout\,
	datac => \process_1~13_combout\,
	datad => \process_1~11_combout\,
	combout => \process_1~14_combout\);

-- Location: LCCOMB_X16_Y13_N18
\process_1~3\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~3_combout\ = (expected_count(6) & (\u_tdm_rx|ch_data_out\(174) & (\u_tdm_rx|ch_data_out\(175) $ (!expected_count(7))))) # (!expected_count(6) & (!\u_tdm_rx|ch_data_out\(174) & (\u_tdm_rx|ch_data_out\(175) $ (!expected_count(7)))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1000010000100001",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => expected_count(6),
	datab => \u_tdm_rx|ch_data_out\(175),
	datac => \u_tdm_rx|ch_data_out\(174),
	datad => expected_count(7),
	combout => \process_1~3_combout\);

-- Location: LCCOMB_X16_Y13_N28
\process_1~2\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~2_combout\ = (\u_tdm_rx|ch_data_out\(173) & (expected_count(5) & (\u_tdm_rx|ch_data_out\(172) $ (!expected_count(4))))) # (!\u_tdm_rx|ch_data_out\(173) & (!expected_count(5) & (\u_tdm_rx|ch_data_out\(172) $ (!expected_count(4)))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1001000000001001",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(173),
	datab => expected_count(5),
	datac => \u_tdm_rx|ch_data_out\(172),
	datad => expected_count(4),
	combout => \process_1~2_combout\);

-- Location: LCCOMB_X14_Y12_N16
\process_1~0\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~0_combout\ = (expected_count(0) & (\u_tdm_rx|ch_data_out\(168) & (expected_count(1) $ (!\u_tdm_rx|ch_data_out\(169))))) # (!expected_count(0) & (!\u_tdm_rx|ch_data_out\(168) & (expected_count(1) $ (!\u_tdm_rx|ch_data_out\(169)))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1000010000100001",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => expected_count(0),
	datab => expected_count(1),
	datac => \u_tdm_rx|ch_data_out\(168),
	datad => \u_tdm_rx|ch_data_out\(169),
	combout => \process_1~0_combout\);

-- Location: LCCOMB_X16_Y13_N10
\process_1~1\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~1_combout\ = (expected_count(2) & (\u_tdm_rx|ch_data_out\(170) & (expected_count(3) $ (!\u_tdm_rx|ch_data_out\(171))))) # (!expected_count(2) & (!\u_tdm_rx|ch_data_out\(170) & (expected_count(3) $ (!\u_tdm_rx|ch_data_out\(171)))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1000010000100001",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => expected_count(2),
	datab => expected_count(3),
	datac => \u_tdm_rx|ch_data_out\(170),
	datad => \u_tdm_rx|ch_data_out\(171),
	combout => \process_1~1_combout\);

-- Location: LCCOMB_X16_Y13_N22
\process_1~4\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~4_combout\ = (\process_1~3_combout\ & (\process_1~2_combout\ & (\process_1~0_combout\ & \process_1~1_combout\)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1000000000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \process_1~3_combout\,
	datab => \process_1~2_combout\,
	datac => \process_1~0_combout\,
	datad => \process_1~1_combout\,
	combout => \process_1~4_combout\);

-- Location: LCCOMB_X18_Y13_N22
\process_1~7\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~7_combout\ = (expected_count(12) & (\u_tdm_rx|ch_data_out\(180) & (\u_tdm_rx|ch_data_out\(181) $ (!expected_count(13))))) # (!expected_count(12) & (!\u_tdm_rx|ch_data_out\(180) & (\u_tdm_rx|ch_data_out\(181) $ (!expected_count(13)))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1000010000100001",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => expected_count(12),
	datab => \u_tdm_rx|ch_data_out\(181),
	datac => \u_tdm_rx|ch_data_out\(180),
	datad => expected_count(13),
	combout => \process_1~7_combout\);

-- Location: LCCOMB_X18_Y13_N4
\process_1~6\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~6_combout\ = (\u_tdm_rx|ch_data_out\(179) & (expected_count(11) & (expected_count(10) $ (!\u_tdm_rx|ch_data_out\(178))))) # (!\u_tdm_rx|ch_data_out\(179) & (!expected_count(11) & (expected_count(10) $ (!\u_tdm_rx|ch_data_out\(178)))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1000001001000001",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(179),
	datab => expected_count(10),
	datac => \u_tdm_rx|ch_data_out\(178),
	datad => expected_count(11),
	combout => \process_1~6_combout\);

-- Location: LCCOMB_X14_Y12_N8
\process_1~8\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~8_combout\ = (expected_count(15) & (\u_tdm_rx|ch_data_out\(183) & (expected_count(14) $ (!\u_tdm_rx|ch_data_out\(182))))) # (!expected_count(15) & (!\u_tdm_rx|ch_data_out\(183) & (expected_count(14) $ (!\u_tdm_rx|ch_data_out\(182)))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1000001001000001",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => expected_count(15),
	datab => expected_count(14),
	datac => \u_tdm_rx|ch_data_out\(182),
	datad => \u_tdm_rx|ch_data_out\(183),
	combout => \process_1~8_combout\);

-- Location: LCCOMB_X18_Y13_N26
\process_1~5\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~5_combout\ = (\u_tdm_rx|ch_data_out\(176) & (expected_count(8) & (expected_count(9) $ (!\u_tdm_rx|ch_data_out\(177))))) # (!\u_tdm_rx|ch_data_out\(176) & (!expected_count(8) & (expected_count(9) $ (!\u_tdm_rx|ch_data_out\(177)))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1001000000001001",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(176),
	datab => expected_count(8),
	datac => expected_count(9),
	datad => \u_tdm_rx|ch_data_out\(177),
	combout => \process_1~5_combout\);

-- Location: LCCOMB_X18_Y13_N6
\process_1~9\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~9_combout\ = (\process_1~7_combout\ & (\process_1~6_combout\ & (\process_1~8_combout\ & \process_1~5_combout\)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1000000000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \process_1~7_combout\,
	datab => \process_1~6_combout\,
	datac => \process_1~8_combout\,
	datad => \process_1~5_combout\,
	combout => \process_1~9_combout\);

-- Location: LCCOMB_X17_Y10_N30
\u_tdm_rx|ch_data_out[160]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[160]~feeder_combout\ = \u_tdm_rx|shift_reg\(160)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(160),
	combout => \u_tdm_rx|ch_data_out[160]~feeder_combout\);

-- Location: FF_X17_Y10_N31
\u_tdm_rx|ch_data_out[160]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[160]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(160));

-- Location: LCCOMB_X17_Y10_N14
\u_tdm_rx|ch_data_out[162]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[162]~feeder_combout\ = \u_tdm_rx|shift_reg\(162)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(162),
	combout => \u_tdm_rx|ch_data_out[162]~feeder_combout\);

-- Location: FF_X17_Y10_N15
\u_tdm_rx|ch_data_out[162]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[162]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(162));

-- Location: FF_X17_Y10_N23
\u_tdm_rx|ch_data_out[163]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(163),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(163));

-- Location: LCCOMB_X17_Y10_N18
\u_tdm_rx|ch_data_out[161]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[161]~feeder_combout\ = \u_tdm_rx|shift_reg\(161)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(161),
	combout => \u_tdm_rx|ch_data_out[161]~feeder_combout\);

-- Location: FF_X17_Y10_N19
\u_tdm_rx|ch_data_out[161]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[161]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(161));

-- Location: LCCOMB_X17_Y10_N22
\process_1~16\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~16_combout\ = (!\u_tdm_rx|ch_data_out\(160) & (!\u_tdm_rx|ch_data_out\(162) & (!\u_tdm_rx|ch_data_out\(163) & \u_tdm_rx|ch_data_out\(161))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000000100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(160),
	datab => \u_tdm_rx|ch_data_out\(162),
	datac => \u_tdm_rx|ch_data_out\(163),
	datad => \u_tdm_rx|ch_data_out\(161),
	combout => \process_1~16_combout\);

-- Location: LCCOMB_X18_Y10_N22
\u_tdm_rx|ch_data_out[152]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[152]~feeder_combout\ = \u_tdm_rx|shift_reg\(152)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(152),
	combout => \u_tdm_rx|ch_data_out[152]~feeder_combout\);

-- Location: FF_X18_Y10_N23
\u_tdm_rx|ch_data_out[152]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[152]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(152));

-- Location: LCCOMB_X18_Y10_N0
\u_tdm_rx|ch_data_out[153]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[153]~feeder_combout\ = \u_tdm_rx|shift_reg\(153)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(153),
	combout => \u_tdm_rx|ch_data_out[153]~feeder_combout\);

-- Location: FF_X18_Y10_N1
\u_tdm_rx|ch_data_out[153]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[153]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(153));

-- Location: FF_X18_Y10_N19
\u_tdm_rx|ch_data_out[155]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(155),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(155));

-- Location: LCCOMB_X18_Y10_N12
\u_tdm_rx|ch_data_out[154]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[154]~feeder_combout\ = \u_tdm_rx|shift_reg\(154)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(154),
	combout => \u_tdm_rx|ch_data_out[154]~feeder_combout\);

-- Location: FF_X18_Y10_N13
\u_tdm_rx|ch_data_out[154]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[154]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(154));

-- Location: LCCOMB_X18_Y10_N18
\process_1~18\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~18_combout\ = (!\u_tdm_rx|ch_data_out\(152) & (\u_tdm_rx|ch_data_out\(153) & (!\u_tdm_rx|ch_data_out\(155) & !\u_tdm_rx|ch_data_out\(154))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000000000000100",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(152),
	datab => \u_tdm_rx|ch_data_out\(153),
	datac => \u_tdm_rx|ch_data_out\(155),
	datad => \u_tdm_rx|ch_data_out\(154),
	combout => \process_1~18_combout\);

-- Location: LCCOMB_X17_Y10_N26
\u_tdm_rx|ch_data_out[157]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[157]~feeder_combout\ = \u_tdm_rx|shift_reg\(157)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(157),
	combout => \u_tdm_rx|ch_data_out[157]~feeder_combout\);

-- Location: FF_X17_Y10_N27
\u_tdm_rx|ch_data_out[157]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[157]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(157));

-- Location: LCCOMB_X17_Y10_N20
\u_tdm_rx|ch_data_out[158]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[158]~feeder_combout\ = \u_tdm_rx|shift_reg\(158)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(158),
	combout => \u_tdm_rx|ch_data_out[158]~feeder_combout\);

-- Location: FF_X17_Y10_N21
\u_tdm_rx|ch_data_out[158]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[158]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(158));

-- Location: FF_X17_Y10_N5
\u_tdm_rx|ch_data_out[156]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(156),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(156));

-- Location: LCCOMB_X17_Y10_N24
\u_tdm_rx|ch_data_out[159]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[159]~feeder_combout\ = \u_tdm_rx|shift_reg\(159)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(159),
	combout => \u_tdm_rx|ch_data_out[159]~feeder_combout\);

-- Location: FF_X17_Y10_N25
\u_tdm_rx|ch_data_out[159]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[159]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(159));

-- Location: LCCOMB_X17_Y10_N4
\process_1~17\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~17_combout\ = (\u_tdm_rx|ch_data_out\(157) & (!\u_tdm_rx|ch_data_out\(158) & (\u_tdm_rx|ch_data_out\(156) & \u_tdm_rx|ch_data_out\(159))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0010000000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(157),
	datab => \u_tdm_rx|ch_data_out\(158),
	datac => \u_tdm_rx|ch_data_out\(156),
	datad => \u_tdm_rx|ch_data_out\(159),
	combout => \process_1~17_combout\);

-- Location: FF_X18_Y10_N7
\u_tdm_rx|ch_data_out[166]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(166),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(166));

-- Location: LCCOMB_X18_Y10_N24
\u_tdm_rx|ch_data_out[167]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[167]~feeder_combout\ = \u_tdm_rx|shift_reg\(167)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(167),
	combout => \u_tdm_rx|ch_data_out[167]~feeder_combout\);

-- Location: FF_X18_Y10_N25
\u_tdm_rx|ch_data_out[167]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[167]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(167));

-- Location: FF_X18_Y10_N29
\u_tdm_rx|ch_data_out[164]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(164),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(164));

-- Location: LCCOMB_X18_Y10_N10
\u_tdm_rx|ch_data_out[165]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[165]~feeder_combout\ = \u_tdm_rx|shift_reg\(165)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(165),
	combout => \u_tdm_rx|ch_data_out[165]~feeder_combout\);

-- Location: FF_X18_Y10_N11
\u_tdm_rx|ch_data_out[165]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[165]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(165));

-- Location: LCCOMB_X18_Y10_N28
\process_1~15\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~15_combout\ = (!\u_tdm_rx|ch_data_out\(166) & (\u_tdm_rx|ch_data_out\(167) & (\u_tdm_rx|ch_data_out\(164) & \u_tdm_rx|ch_data_out\(165))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0100000000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(166),
	datab => \u_tdm_rx|ch_data_out\(167),
	datac => \u_tdm_rx|ch_data_out\(164),
	datad => \u_tdm_rx|ch_data_out\(165),
	combout => \process_1~15_combout\);

-- Location: LCCOMB_X17_Y10_N8
\process_1~19\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~19_combout\ = (\process_1~16_combout\ & (\process_1~18_combout\ & (\process_1~17_combout\ & \process_1~15_combout\)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1000000000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \process_1~16_combout\,
	datab => \process_1~18_combout\,
	datac => \process_1~17_combout\,
	datad => \process_1~15_combout\,
	combout => \process_1~19_combout\);

-- Location: LCCOMB_X17_Y12_N24
\process_1~20\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~20_combout\ = (\process_1~14_combout\ & (\process_1~4_combout\ & (\process_1~9_combout\ & \process_1~19_combout\)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1000000000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \process_1~14_combout\,
	datab => \process_1~4_combout\,
	datac => \process_1~9_combout\,
	datad => \process_1~19_combout\,
	combout => \process_1~20_combout\);

-- Location: LCCOMB_X18_Y11_N28
\u_tdm_rx|ch_data_out[13]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[13]~feeder_combout\ = \u_tdm_rx|shift_reg\(13)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(13),
	combout => \u_tdm_rx|ch_data_out[13]~feeder_combout\);

-- Location: FF_X18_Y11_N29
\u_tdm_rx|ch_data_out[13]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[13]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(13));

-- Location: LCCOMB_X18_Y11_N16
\u_tdm_rx|ch_data_out[14]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[14]~feeder_combout\ = \u_tdm_rx|shift_reg\(14)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(14),
	combout => \u_tdm_rx|ch_data_out[14]~feeder_combout\);

-- Location: FF_X18_Y11_N17
\u_tdm_rx|ch_data_out[14]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[14]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(14));

-- Location: FF_X18_Y11_N7
\u_tdm_rx|ch_data_out[15]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(15),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(15));

-- Location: LCCOMB_X18_Y11_N20
\u_tdm_rx|ch_data_out[12]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[12]~feeder_combout\ = \u_tdm_rx|shift_reg\(12)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(12),
	combout => \u_tdm_rx|ch_data_out[12]~feeder_combout\);

-- Location: FF_X18_Y11_N21
\u_tdm_rx|ch_data_out[12]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[12]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(12));

-- Location: LCCOMB_X18_Y11_N6
\process_1~65\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~65_combout\ = (!\u_tdm_rx|ch_data_out\(13) & (!\u_tdm_rx|ch_data_out\(14) & (!\u_tdm_rx|ch_data_out\(15) & \u_tdm_rx|ch_data_out\(12))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000000100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(13),
	datab => \u_tdm_rx|ch_data_out\(14),
	datac => \u_tdm_rx|ch_data_out\(15),
	datad => \u_tdm_rx|ch_data_out\(12),
	combout => \process_1~65_combout\);

-- Location: FF_X18_Y11_N27
\u_tdm_rx|ch_data_out[17]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(17),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(17));

-- Location: FF_X18_Y11_N3
\u_tdm_rx|ch_data_out[16]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(16),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(16));

-- Location: FF_X18_Y11_N1
\u_tdm_rx|ch_data_out[18]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(18),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(18));

-- Location: FF_X18_Y11_N25
\u_tdm_rx|ch_data_out[19]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(19),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(19));

-- Location: LCCOMB_X18_Y11_N0
\process_1~64\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~64_combout\ = (!\u_tdm_rx|ch_data_out\(17) & (!\u_tdm_rx|ch_data_out\(16) & (!\u_tdm_rx|ch_data_out\(18) & \u_tdm_rx|ch_data_out\(19))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000000100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(17),
	datab => \u_tdm_rx|ch_data_out\(16),
	datac => \u_tdm_rx|ch_data_out\(18),
	datad => \u_tdm_rx|ch_data_out\(19),
	combout => \process_1~64_combout\);

-- Location: LCCOMB_X16_Y10_N12
\u_tdm_rx|ch_data_out[21]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[21]~feeder_combout\ = \u_tdm_rx|shift_reg\(21)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(21),
	combout => \u_tdm_rx|ch_data_out[21]~feeder_combout\);

-- Location: FF_X16_Y10_N13
\u_tdm_rx|ch_data_out[21]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[21]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(21));

-- Location: LCCOMB_X16_Y10_N28
\u_tdm_rx|ch_data_out[22]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[22]~feeder_combout\ = \u_tdm_rx|shift_reg\(22)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(22),
	combout => \u_tdm_rx|ch_data_out[22]~feeder_combout\);

-- Location: FF_X16_Y10_N29
\u_tdm_rx|ch_data_out[22]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[22]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(22));

-- Location: FF_X16_Y10_N1
\u_tdm_rx|ch_data_out[23]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(23),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(23));

-- Location: FF_X16_Y10_N5
\u_tdm_rx|ch_data_out[20]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(20),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(20));

-- Location: LCCOMB_X16_Y10_N0
\process_1~63\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~63_combout\ = (!\u_tdm_rx|ch_data_out\(21) & (!\u_tdm_rx|ch_data_out\(22) & (!\u_tdm_rx|ch_data_out\(23) & \u_tdm_rx|ch_data_out\(20))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000000100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(21),
	datab => \u_tdm_rx|ch_data_out\(22),
	datac => \u_tdm_rx|ch_data_out\(23),
	datad => \u_tdm_rx|ch_data_out\(20),
	combout => \process_1~63_combout\);

-- Location: LCCOMB_X19_Y11_N22
\u_tdm_rx|ch_data_out[8]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[8]~feeder_combout\ = \u_tdm_rx|shift_reg\(8)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(8),
	combout => \u_tdm_rx|ch_data_out[8]~feeder_combout\);

-- Location: FF_X19_Y11_N23
\u_tdm_rx|ch_data_out[8]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[8]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(8));

-- Location: FF_X19_Y11_N17
\u_tdm_rx|ch_data_out[11]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(11),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(11));

-- Location: FF_X19_Y11_N3
\u_tdm_rx|ch_data_out[10]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(10),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(10));

-- Location: FF_X19_Y11_N13
\u_tdm_rx|ch_data_out[9]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(9),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(9));

-- Location: LCCOMB_X19_Y11_N2
\process_1~66\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~66_combout\ = (!\u_tdm_rx|ch_data_out\(8) & (\u_tdm_rx|ch_data_out\(11) & (!\u_tdm_rx|ch_data_out\(10) & !\u_tdm_rx|ch_data_out\(9))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000000000000100",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(8),
	datab => \u_tdm_rx|ch_data_out\(11),
	datac => \u_tdm_rx|ch_data_out\(10),
	datad => \u_tdm_rx|ch_data_out\(9),
	combout => \process_1~66_combout\);

-- Location: LCCOMB_X18_Y11_N10
\process_1~67\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~67_combout\ = (\process_1~65_combout\ & (\process_1~64_combout\ & (\process_1~63_combout\ & \process_1~66_combout\)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1000000000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \process_1~65_combout\,
	datab => \process_1~64_combout\,
	datac => \process_1~63_combout\,
	datad => \process_1~66_combout\,
	combout => \process_1~67_combout\);

-- Location: FF_X19_Y11_N25
\u_tdm_rx|ch_data_out[4]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(4),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(4));

-- Location: LCCOMB_X19_Y11_N14
\u_tdm_rx|ch_data_out[5]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[5]~feeder_combout\ = \u_tdm_rx|shift_reg\(5)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(5),
	combout => \u_tdm_rx|ch_data_out[5]~feeder_combout\);

-- Location: FF_X19_Y11_N15
\u_tdm_rx|ch_data_out[5]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[5]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(5));

-- Location: FF_X19_Y11_N29
\u_tdm_rx|ch_data_out[7]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(7),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(7));

-- Location: LCCOMB_X19_Y11_N18
\u_tdm_rx|ch_data_out[6]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[6]~feeder_combout\ = \u_tdm_rx|shift_reg\(6)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(6),
	combout => \u_tdm_rx|ch_data_out[6]~feeder_combout\);

-- Location: FF_X19_Y11_N19
\u_tdm_rx|ch_data_out[6]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[6]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(6));

-- Location: LCCOMB_X19_Y11_N28
\process_1~68\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~68_combout\ = (\u_tdm_rx|ch_data_out\(4) & (!\u_tdm_rx|ch_data_out\(5) & (!\u_tdm_rx|ch_data_out\(7) & !\u_tdm_rx|ch_data_out\(6))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000000000000010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(4),
	datab => \u_tdm_rx|ch_data_out\(5),
	datac => \u_tdm_rx|ch_data_out\(7),
	datad => \u_tdm_rx|ch_data_out\(6),
	combout => \process_1~68_combout\);

-- Location: LCCOMB_X21_Y13_N22
\u_tdm_rx|ch_data_out[0]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[0]~feeder_combout\ = \u_tdm_rx|shift_reg\(0)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(0),
	combout => \u_tdm_rx|ch_data_out[0]~feeder_combout\);

-- Location: FF_X21_Y13_N23
\u_tdm_rx|ch_data_out[0]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[0]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(0));

-- Location: LCCOMB_X21_Y13_N24
\u_tdm_rx|ch_data_out[3]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[3]~feeder_combout\ = \u_tdm_rx|shift_reg\(3)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(3),
	combout => \u_tdm_rx|ch_data_out[3]~feeder_combout\);

-- Location: FF_X21_Y13_N25
\u_tdm_rx|ch_data_out[3]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[3]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(3));

-- Location: FF_X21_Y13_N3
\u_tdm_rx|ch_data_out[2]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(2),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(2));

-- Location: LCCOMB_X21_Y13_N12
\u_tdm_rx|ch_data_out[1]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[1]~feeder_combout\ = \u_tdm_rx|shift_reg\(1)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(1),
	combout => \u_tdm_rx|ch_data_out[1]~feeder_combout\);

-- Location: FF_X21_Y13_N13
\u_tdm_rx|ch_data_out[1]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[1]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(1));

-- Location: LCCOMB_X21_Y13_N2
\process_1~69\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~69_combout\ = (!\u_tdm_rx|ch_data_out\(0) & (\u_tdm_rx|ch_data_out\(3) & (!\u_tdm_rx|ch_data_out\(2) & !\u_tdm_rx|ch_data_out\(1))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000000000000100",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(0),
	datab => \u_tdm_rx|ch_data_out\(3),
	datac => \u_tdm_rx|ch_data_out\(2),
	datad => \u_tdm_rx|ch_data_out\(1),
	combout => \process_1~69_combout\);

-- Location: LCCOMB_X18_Y11_N26
\process_1~70\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~70_combout\ = (\process_1~67_combout\ & (\process_1~68_combout\ & \process_1~69_combout\))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1000100000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \process_1~67_combout\,
	datab => \process_1~68_combout\,
	datad => \process_1~69_combout\,
	combout => \process_1~70_combout\);

-- Location: LCCOMB_X13_Y13_N26
\u_tdm_rx|ch_data_out[105]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[105]~feeder_combout\ = \u_tdm_rx|shift_reg\(105)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(105),
	combout => \u_tdm_rx|ch_data_out[105]~feeder_combout\);

-- Location: FF_X13_Y13_N27
\u_tdm_rx|ch_data_out[105]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[105]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(105));

-- Location: LCCOMB_X13_Y13_N14
\u_tdm_rx|ch_data_out[106]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[106]~feeder_combout\ = \u_tdm_rx|shift_reg\(106)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(106),
	combout => \u_tdm_rx|ch_data_out[106]~feeder_combout\);

-- Location: FF_X13_Y13_N15
\u_tdm_rx|ch_data_out[106]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[106]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(106));

-- Location: FF_X13_Y13_N23
\u_tdm_rx|ch_data_out[107]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(107),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(107));

-- Location: LCCOMB_X13_Y13_N6
\u_tdm_rx|ch_data_out[104]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[104]~feeder_combout\ = \u_tdm_rx|shift_reg\(104)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(104),
	combout => \u_tdm_rx|ch_data_out[104]~feeder_combout\);

-- Location: FF_X13_Y13_N7
\u_tdm_rx|ch_data_out[104]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[104]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(104));

-- Location: LCCOMB_X13_Y13_N22
\process_1~34\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~34_combout\ = (!\u_tdm_rx|ch_data_out\(105) & (\u_tdm_rx|ch_data_out\(106) & (!\u_tdm_rx|ch_data_out\(107) & !\u_tdm_rx|ch_data_out\(104))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000000000000100",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(105),
	datab => \u_tdm_rx|ch_data_out\(106),
	datac => \u_tdm_rx|ch_data_out\(107),
	datad => \u_tdm_rx|ch_data_out\(104),
	combout => \process_1~34_combout\);

-- Location: LCCOMB_X14_Y13_N6
\u_tdm_rx|ch_data_out[118]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[118]~feeder_combout\ = \u_tdm_rx|shift_reg\(118)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(118),
	combout => \u_tdm_rx|ch_data_out[118]~feeder_combout\);

-- Location: FF_X14_Y13_N7
\u_tdm_rx|ch_data_out[118]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[118]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(118));

-- Location: LCCOMB_X14_Y13_N16
\u_tdm_rx|ch_data_out[117]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[117]~feeder_combout\ = \u_tdm_rx|shift_reg\(117)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(117),
	combout => \u_tdm_rx|ch_data_out[117]~feeder_combout\);

-- Location: FF_X14_Y13_N17
\u_tdm_rx|ch_data_out[117]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[117]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(117));

-- Location: FF_X14_Y13_N27
\u_tdm_rx|ch_data_out[116]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(116),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(116));

-- Location: LCCOMB_X14_Y13_N20
\u_tdm_rx|ch_data_out[119]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[119]~feeder_combout\ = \u_tdm_rx|shift_reg\(119)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(119),
	combout => \u_tdm_rx|ch_data_out[119]~feeder_combout\);

-- Location: FF_X14_Y13_N21
\u_tdm_rx|ch_data_out[119]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[119]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(119));

-- Location: LCCOMB_X14_Y13_N26
\process_1~31\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~31_combout\ = (\u_tdm_rx|ch_data_out\(118) & (!\u_tdm_rx|ch_data_out\(117) & (\u_tdm_rx|ch_data_out\(116) & \u_tdm_rx|ch_data_out\(119))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0010000000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(118),
	datab => \u_tdm_rx|ch_data_out\(117),
	datac => \u_tdm_rx|ch_data_out\(116),
	datad => \u_tdm_rx|ch_data_out\(119),
	combout => \process_1~31_combout\);

-- Location: LCCOMB_X13_Y13_N2
\u_tdm_rx|ch_data_out[111]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[111]~feeder_combout\ = \u_tdm_rx|shift_reg\(111)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(111),
	combout => \u_tdm_rx|ch_data_out[111]~feeder_combout\);

-- Location: FF_X13_Y13_N3
\u_tdm_rx|ch_data_out[111]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[111]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(111));

-- Location: LCCOMB_X13_Y13_N28
\u_tdm_rx|ch_data_out[109]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[109]~feeder_combout\ = \u_tdm_rx|shift_reg\(109)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(109),
	combout => \u_tdm_rx|ch_data_out[109]~feeder_combout\);

-- Location: FF_X13_Y13_N29
\u_tdm_rx|ch_data_out[109]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[109]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(109));

-- Location: FF_X13_Y13_N5
\u_tdm_rx|ch_data_out[108]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(108),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(108));

-- Location: LCCOMB_X13_Y13_N18
\u_tdm_rx|ch_data_out[110]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[110]~feeder_combout\ = \u_tdm_rx|shift_reg\(110)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(110),
	combout => \u_tdm_rx|ch_data_out[110]~feeder_combout\);

-- Location: FF_X13_Y13_N19
\u_tdm_rx|ch_data_out[110]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[110]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(110));

-- Location: LCCOMB_X13_Y13_N4
\process_1~33\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~33_combout\ = (\u_tdm_rx|ch_data_out\(111) & (!\u_tdm_rx|ch_data_out\(109) & (\u_tdm_rx|ch_data_out\(108) & \u_tdm_rx|ch_data_out\(110))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0010000000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(111),
	datab => \u_tdm_rx|ch_data_out\(109),
	datac => \u_tdm_rx|ch_data_out\(108),
	datad => \u_tdm_rx|ch_data_out\(110),
	combout => \process_1~33_combout\);

-- Location: FF_X14_Y13_N31
\u_tdm_rx|ch_data_out[114]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(114),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(114));

-- Location: LCCOMB_X14_Y13_N8
\u_tdm_rx|ch_data_out[112]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[112]~feeder_combout\ = \u_tdm_rx|shift_reg\(112)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(112),
	combout => \u_tdm_rx|ch_data_out[112]~feeder_combout\);

-- Location: FF_X14_Y13_N9
\u_tdm_rx|ch_data_out[112]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[112]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(112));

-- Location: FF_X14_Y13_N29
\u_tdm_rx|ch_data_out[115]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(115),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(115));

-- Location: FF_X14_Y13_N3
\u_tdm_rx|ch_data_out[113]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(113),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(113));

-- Location: LCCOMB_X14_Y13_N28
\process_1~32\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~32_combout\ = (\u_tdm_rx|ch_data_out\(114) & (!\u_tdm_rx|ch_data_out\(112) & (!\u_tdm_rx|ch_data_out\(115) & !\u_tdm_rx|ch_data_out\(113))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000000000000010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(114),
	datab => \u_tdm_rx|ch_data_out\(112),
	datac => \u_tdm_rx|ch_data_out\(115),
	datad => \u_tdm_rx|ch_data_out\(113),
	combout => \process_1~32_combout\);

-- Location: LCCOMB_X13_Y13_N30
\process_1~35\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~35_combout\ = (\process_1~34_combout\ & (\process_1~31_combout\ & (\process_1~33_combout\ & \process_1~32_combout\)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1000000000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \process_1~34_combout\,
	datab => \process_1~31_combout\,
	datac => \process_1~33_combout\,
	datad => \process_1~32_combout\,
	combout => \process_1~35_combout\);

-- Location: LCCOMB_X12_Y10_N22
\u_tdm_rx|ch_data_out[98]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[98]~feeder_combout\ = \u_tdm_rx|shift_reg\(98)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(98),
	combout => \u_tdm_rx|ch_data_out[98]~feeder_combout\);

-- Location: FF_X12_Y10_N23
\u_tdm_rx|ch_data_out[98]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[98]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(98));

-- Location: FF_X12_Y10_N13
\u_tdm_rx|ch_data_out[96]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(96),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(96));

-- Location: FF_X12_Y10_N15
\u_tdm_rx|ch_data_out[99]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(99),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(99));

-- Location: FF_X12_Y10_N7
\u_tdm_rx|ch_data_out[97]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(97),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(97));

-- Location: LCCOMB_X12_Y10_N14
\process_1~37\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~37_combout\ = (\u_tdm_rx|ch_data_out\(98) & (!\u_tdm_rx|ch_data_out\(96) & (!\u_tdm_rx|ch_data_out\(99) & !\u_tdm_rx|ch_data_out\(97))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000000000000010",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(98),
	datab => \u_tdm_rx|ch_data_out\(96),
	datac => \u_tdm_rx|ch_data_out\(99),
	datad => \u_tdm_rx|ch_data_out\(97),
	combout => \process_1~37_combout\);

-- Location: LCCOMB_X13_Y10_N10
\u_tdm_rx|ch_data_out[88]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[88]~feeder_combout\ = \u_tdm_rx|shift_reg\(88)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(88),
	combout => \u_tdm_rx|ch_data_out[88]~feeder_combout\);

-- Location: FF_X13_Y10_N11
\u_tdm_rx|ch_data_out[88]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[88]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(88));

-- Location: LCCOMB_X13_Y10_N20
\u_tdm_rx|ch_data_out[90]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[90]~feeder_combout\ = \u_tdm_rx|shift_reg\(90)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(90),
	combout => \u_tdm_rx|ch_data_out[90]~feeder_combout\);

-- Location: FF_X13_Y10_N21
\u_tdm_rx|ch_data_out[90]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[90]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(90));

-- Location: FF_X13_Y10_N17
\u_tdm_rx|ch_data_out[89]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(89),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(89));

-- Location: FF_X13_Y10_N19
\u_tdm_rx|ch_data_out[91]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(91),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(91));

-- Location: LCCOMB_X13_Y10_N16
\process_1~39\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~39_combout\ = (\u_tdm_rx|ch_data_out\(88) & (\u_tdm_rx|ch_data_out\(90) & (!\u_tdm_rx|ch_data_out\(89) & !\u_tdm_rx|ch_data_out\(91))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000000000001000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(88),
	datab => \u_tdm_rx|ch_data_out\(90),
	datac => \u_tdm_rx|ch_data_out\(89),
	datad => \u_tdm_rx|ch_data_out\(91),
	combout => \process_1~39_combout\);

-- Location: FF_X13_Y10_N13
\u_tdm_rx|ch_data_out[92]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(92),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(92));

-- Location: LCCOMB_X13_Y10_N0
\u_tdm_rx|ch_data_out[95]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[95]~feeder_combout\ = \u_tdm_rx|shift_reg\(95)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(95),
	combout => \u_tdm_rx|ch_data_out[95]~feeder_combout\);

-- Location: FF_X13_Y10_N1
\u_tdm_rx|ch_data_out[95]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[95]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(95));

-- Location: FF_X13_Y10_N9
\u_tdm_rx|ch_data_out[93]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(93),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(93));

-- Location: FF_X13_Y10_N7
\u_tdm_rx|ch_data_out[94]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(94),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(94));

-- Location: LCCOMB_X13_Y10_N8
\process_1~38\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~38_combout\ = (!\u_tdm_rx|ch_data_out\(92) & (\u_tdm_rx|ch_data_out\(95) & (\u_tdm_rx|ch_data_out\(93) & \u_tdm_rx|ch_data_out\(94))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0100000000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(92),
	datab => \u_tdm_rx|ch_data_out\(95),
	datac => \u_tdm_rx|ch_data_out\(93),
	datad => \u_tdm_rx|ch_data_out\(94),
	combout => \process_1~38_combout\);

-- Location: LCCOMB_X12_Y10_N8
\u_tdm_rx|ch_data_out[102]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[102]~feeder_combout\ = \u_tdm_rx|shift_reg\(102)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(102),
	combout => \u_tdm_rx|ch_data_out[102]~feeder_combout\);

-- Location: FF_X12_Y10_N9
\u_tdm_rx|ch_data_out[102]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[102]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(102));

-- Location: LCCOMB_X12_Y10_N10
\u_tdm_rx|ch_data_out[103]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[103]~feeder_combout\ = \u_tdm_rx|shift_reg\(103)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(103),
	combout => \u_tdm_rx|ch_data_out[103]~feeder_combout\);

-- Location: FF_X12_Y10_N11
\u_tdm_rx|ch_data_out[103]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[103]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(103));

-- Location: FF_X12_Y10_N3
\u_tdm_rx|ch_data_out[100]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(100),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(100));

-- Location: LCCOMB_X12_Y10_N28
\u_tdm_rx|ch_data_out[101]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[101]~feeder_combout\ = \u_tdm_rx|shift_reg\(101)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(101),
	combout => \u_tdm_rx|ch_data_out[101]~feeder_combout\);

-- Location: FF_X12_Y10_N29
\u_tdm_rx|ch_data_out[101]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[101]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(101));

-- Location: LCCOMB_X12_Y10_N2
\process_1~36\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~36_combout\ = (\u_tdm_rx|ch_data_out\(102) & (\u_tdm_rx|ch_data_out\(103) & (\u_tdm_rx|ch_data_out\(100) & !\u_tdm_rx|ch_data_out\(101))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000000010000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(102),
	datab => \u_tdm_rx|ch_data_out\(103),
	datac => \u_tdm_rx|ch_data_out\(100),
	datad => \u_tdm_rx|ch_data_out\(101),
	combout => \process_1~36_combout\);

-- Location: LCCOMB_X13_Y10_N14
\process_1~40\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~40_combout\ = (\process_1~37_combout\ & (\process_1~39_combout\ & (\process_1~38_combout\ & \process_1~36_combout\)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1000000000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \process_1~37_combout\,
	datab => \process_1~39_combout\,
	datac => \process_1~38_combout\,
	datad => \process_1~36_combout\,
	combout => \process_1~40_combout\);

-- Location: LCCOMB_X19_Y10_N6
\u_tdm_rx|ch_data_out[150]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[150]~feeder_combout\ = \u_tdm_rx|shift_reg\(150)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(150),
	combout => \u_tdm_rx|ch_data_out[150]~feeder_combout\);

-- Location: FF_X19_Y10_N7
\u_tdm_rx|ch_data_out[150]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[150]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(150));

-- Location: FF_X19_Y10_N1
\u_tdm_rx|ch_data_out[151]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(151),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(151));

-- Location: FF_X19_Y10_N21
\u_tdm_rx|ch_data_out[148]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(148),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(148));

-- Location: FF_X19_Y10_N11
\u_tdm_rx|ch_data_out[149]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(149),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(149));

-- Location: LCCOMB_X19_Y10_N20
\process_1~21\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~21_combout\ = (!\u_tdm_rx|ch_data_out\(150) & (\u_tdm_rx|ch_data_out\(151) & (\u_tdm_rx|ch_data_out\(148) & \u_tdm_rx|ch_data_out\(149))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0100000000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(150),
	datab => \u_tdm_rx|ch_data_out\(151),
	datac => \u_tdm_rx|ch_data_out\(148),
	datad => \u_tdm_rx|ch_data_out\(149),
	combout => \process_1~21_combout\);

-- Location: LCCOMB_X19_Y13_N30
\u_tdm_rx|ch_data_out[141]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[141]~feeder_combout\ = \u_tdm_rx|shift_reg\(141)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(141),
	combout => \u_tdm_rx|ch_data_out[141]~feeder_combout\);

-- Location: FF_X19_Y13_N31
\u_tdm_rx|ch_data_out[141]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[141]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(141));

-- Location: LCCOMB_X19_Y13_N8
\u_tdm_rx|ch_data_out[142]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[142]~feeder_combout\ = \u_tdm_rx|shift_reg\(142)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(142),
	combout => \u_tdm_rx|ch_data_out[142]~feeder_combout\);

-- Location: FF_X19_Y13_N9
\u_tdm_rx|ch_data_out[142]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[142]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(142));

-- Location: FF_X19_Y13_N21
\u_tdm_rx|ch_data_out[140]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(140),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(140));

-- Location: LCCOMB_X19_Y13_N24
\u_tdm_rx|ch_data_out[143]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[143]~feeder_combout\ = \u_tdm_rx|shift_reg\(143)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(143),
	combout => \u_tdm_rx|ch_data_out[143]~feeder_combout\);

-- Location: FF_X19_Y13_N25
\u_tdm_rx|ch_data_out[143]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[143]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(143));

-- Location: LCCOMB_X19_Y13_N20
\process_1~23\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~23_combout\ = (!\u_tdm_rx|ch_data_out\(141) & (\u_tdm_rx|ch_data_out\(142) & (!\u_tdm_rx|ch_data_out\(140) & \u_tdm_rx|ch_data_out\(143))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000010000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(141),
	datab => \u_tdm_rx|ch_data_out\(142),
	datac => \u_tdm_rx|ch_data_out\(140),
	datad => \u_tdm_rx|ch_data_out\(143),
	combout => \process_1~23_combout\);

-- Location: LCCOMB_X19_Y13_N10
\u_tdm_rx|ch_data_out[144]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[144]~feeder_combout\ = \u_tdm_rx|shift_reg\(144)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(144),
	combout => \u_tdm_rx|ch_data_out[144]~feeder_combout\);

-- Location: FF_X19_Y13_N11
\u_tdm_rx|ch_data_out[144]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[144]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(144));

-- Location: LCCOMB_X19_Y13_N4
\u_tdm_rx|ch_data_out[146]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[146]~feeder_combout\ = \u_tdm_rx|shift_reg\(146)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(146),
	combout => \u_tdm_rx|ch_data_out[146]~feeder_combout\);

-- Location: FF_X19_Y13_N5
\u_tdm_rx|ch_data_out[146]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[146]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(146));

-- Location: FF_X19_Y13_N23
\u_tdm_rx|ch_data_out[147]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(147),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(147));

-- Location: LCCOMB_X19_Y13_N18
\u_tdm_rx|ch_data_out[145]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[145]~feeder_combout\ = \u_tdm_rx|shift_reg\(145)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(145),
	combout => \u_tdm_rx|ch_data_out[145]~feeder_combout\);

-- Location: FF_X19_Y13_N19
\u_tdm_rx|ch_data_out[145]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[145]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(145));

-- Location: LCCOMB_X19_Y13_N22
\process_1~22\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~22_combout\ = (!\u_tdm_rx|ch_data_out\(144) & (!\u_tdm_rx|ch_data_out\(146) & (!\u_tdm_rx|ch_data_out\(147) & \u_tdm_rx|ch_data_out\(145))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000000100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(144),
	datab => \u_tdm_rx|ch_data_out\(146),
	datac => \u_tdm_rx|ch_data_out\(147),
	datad => \u_tdm_rx|ch_data_out\(145),
	combout => \process_1~22_combout\);

-- Location: LCCOMB_X12_Y15_N10
\u_tdm_rx|ch_data_out[136]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[136]~feeder_combout\ = \u_tdm_rx|shift_reg\(136)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(136),
	combout => \u_tdm_rx|ch_data_out[136]~feeder_combout\);

-- Location: FF_X12_Y15_N11
\u_tdm_rx|ch_data_out[136]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[136]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(136));

-- Location: LCCOMB_X12_Y15_N28
\u_tdm_rx|ch_data_out[139]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[139]~feeder_combout\ = \u_tdm_rx|shift_reg\(139)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(139),
	combout => \u_tdm_rx|ch_data_out[139]~feeder_combout\);

-- Location: FF_X12_Y15_N29
\u_tdm_rx|ch_data_out[139]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[139]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(139));

-- Location: FF_X12_Y15_N31
\u_tdm_rx|ch_data_out[138]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(138),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(138));

-- Location: FF_X12_Y15_N25
\u_tdm_rx|ch_data_out[137]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(137),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(137));

-- Location: LCCOMB_X12_Y15_N30
\process_1~24\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~24_combout\ = (\u_tdm_rx|ch_data_out\(136) & (!\u_tdm_rx|ch_data_out\(139) & (!\u_tdm_rx|ch_data_out\(138) & \u_tdm_rx|ch_data_out\(137))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000001000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(136),
	datab => \u_tdm_rx|ch_data_out\(139),
	datac => \u_tdm_rx|ch_data_out\(138),
	datad => \u_tdm_rx|ch_data_out\(137),
	combout => \process_1~24_combout\);

-- Location: LCCOMB_X19_Y13_N26
\process_1~25\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~25_combout\ = (\process_1~21_combout\ & (\process_1~23_combout\ & (\process_1~22_combout\ & \process_1~24_combout\)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1000000000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \process_1~21_combout\,
	datab => \process_1~23_combout\,
	datac => \process_1~22_combout\,
	datad => \process_1~24_combout\,
	combout => \process_1~25_combout\);

-- Location: LCCOMB_X12_Y14_N22
\u_tdm_rx|ch_data_out[135]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[135]~feeder_combout\ = \u_tdm_rx|shift_reg\(135)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(135),
	combout => \u_tdm_rx|ch_data_out[135]~feeder_combout\);

-- Location: FF_X12_Y14_N23
\u_tdm_rx|ch_data_out[135]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[135]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(135));

-- Location: LCCOMB_X12_Y14_N28
\u_tdm_rx|ch_data_out[134]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[134]~feeder_combout\ = \u_tdm_rx|shift_reg\(134)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(134),
	combout => \u_tdm_rx|ch_data_out[134]~feeder_combout\);

-- Location: FF_X12_Y14_N29
\u_tdm_rx|ch_data_out[134]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[134]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(134));

-- Location: FF_X12_Y14_N15
\u_tdm_rx|ch_data_out[132]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(132),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(132));

-- Location: FF_X12_Y14_N21
\u_tdm_rx|ch_data_out[133]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(133),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(133));

-- Location: LCCOMB_X12_Y14_N14
\process_1~26\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~26_combout\ = (\u_tdm_rx|ch_data_out\(135) & (\u_tdm_rx|ch_data_out\(134) & (!\u_tdm_rx|ch_data_out\(132) & !\u_tdm_rx|ch_data_out\(133))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000000000001000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(135),
	datab => \u_tdm_rx|ch_data_out\(134),
	datac => \u_tdm_rx|ch_data_out\(132),
	datad => \u_tdm_rx|ch_data_out\(133),
	combout => \process_1~26_combout\);

-- Location: LCCOMB_X13_Y14_N26
\u_tdm_rx|ch_data_out[120]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[120]~feeder_combout\ = \u_tdm_rx|shift_reg\(120)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(120),
	combout => \u_tdm_rx|ch_data_out[120]~feeder_combout\);

-- Location: FF_X13_Y14_N27
\u_tdm_rx|ch_data_out[120]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[120]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(120));

-- Location: LCCOMB_X13_Y14_N0
\u_tdm_rx|ch_data_out[123]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[123]~feeder_combout\ = \u_tdm_rx|shift_reg\(123)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(123),
	combout => \u_tdm_rx|ch_data_out[123]~feeder_combout\);

-- Location: FF_X13_Y14_N1
\u_tdm_rx|ch_data_out[123]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[123]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(123));

-- Location: FF_X13_Y14_N7
\u_tdm_rx|ch_data_out[122]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(122),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(122));

-- Location: LCCOMB_X13_Y14_N4
\u_tdm_rx|ch_data_out[121]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[121]~feeder_combout\ = \u_tdm_rx|shift_reg\(121)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(121),
	combout => \u_tdm_rx|ch_data_out[121]~feeder_combout\);

-- Location: FF_X13_Y14_N5
\u_tdm_rx|ch_data_out[121]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[121]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(121));

-- Location: LCCOMB_X13_Y14_N6
\process_1~29\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~29_combout\ = (\u_tdm_rx|ch_data_out\(120) & (!\u_tdm_rx|ch_data_out\(123) & (!\u_tdm_rx|ch_data_out\(122) & \u_tdm_rx|ch_data_out\(121))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000001000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(120),
	datab => \u_tdm_rx|ch_data_out\(123),
	datac => \u_tdm_rx|ch_data_out\(122),
	datad => \u_tdm_rx|ch_data_out\(121),
	combout => \process_1~29_combout\);

-- Location: LCCOMB_X13_Y14_N10
\u_tdm_rx|ch_data_out[125]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[125]~feeder_combout\ = \u_tdm_rx|shift_reg\(125)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(125),
	combout => \u_tdm_rx|ch_data_out[125]~feeder_combout\);

-- Location: FF_X13_Y14_N11
\u_tdm_rx|ch_data_out[125]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[125]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(125));

-- Location: FF_X13_Y14_N25
\u_tdm_rx|ch_data_out[126]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(126),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(126));

-- Location: FF_X13_Y14_N15
\u_tdm_rx|ch_data_out[124]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(124),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(124));

-- Location: LCCOMB_X13_Y14_N16
\u_tdm_rx|ch_data_out[127]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[127]~feeder_combout\ = \u_tdm_rx|shift_reg\(127)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(127),
	combout => \u_tdm_rx|ch_data_out[127]~feeder_combout\);

-- Location: FF_X13_Y14_N17
\u_tdm_rx|ch_data_out[127]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[127]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(127));

-- Location: LCCOMB_X13_Y14_N14
\process_1~28\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~28_combout\ = (!\u_tdm_rx|ch_data_out\(125) & (\u_tdm_rx|ch_data_out\(126) & (!\u_tdm_rx|ch_data_out\(124) & \u_tdm_rx|ch_data_out\(127))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000010000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(125),
	datab => \u_tdm_rx|ch_data_out\(126),
	datac => \u_tdm_rx|ch_data_out\(124),
	datad => \u_tdm_rx|ch_data_out\(127),
	combout => \process_1~28_combout\);

-- Location: LCCOMB_X12_Y14_N30
\u_tdm_rx|ch_data_out[129]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[129]~feeder_combout\ = \u_tdm_rx|shift_reg\(129)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(129),
	combout => \u_tdm_rx|ch_data_out[129]~feeder_combout\);

-- Location: FF_X12_Y14_N31
\u_tdm_rx|ch_data_out[129]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[129]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(129));

-- Location: LCCOMB_X12_Y14_N16
\u_tdm_rx|ch_data_out[131]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[131]~feeder_combout\ = \u_tdm_rx|shift_reg\(131)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(131),
	combout => \u_tdm_rx|ch_data_out[131]~feeder_combout\);

-- Location: FF_X12_Y14_N17
\u_tdm_rx|ch_data_out[131]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[131]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(131));

-- Location: FF_X12_Y14_N9
\u_tdm_rx|ch_data_out[130]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(130),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(130));

-- Location: LCCOMB_X12_Y14_N10
\u_tdm_rx|ch_data_out[128]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[128]~feeder_combout\ = \u_tdm_rx|shift_reg\(128)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(128),
	combout => \u_tdm_rx|ch_data_out[128]~feeder_combout\);

-- Location: FF_X12_Y14_N11
\u_tdm_rx|ch_data_out[128]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[128]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(128));

-- Location: LCCOMB_X12_Y14_N8
\process_1~27\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~27_combout\ = (\u_tdm_rx|ch_data_out\(129) & (!\u_tdm_rx|ch_data_out\(131) & (!\u_tdm_rx|ch_data_out\(130) & \u_tdm_rx|ch_data_out\(128))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000001000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(129),
	datab => \u_tdm_rx|ch_data_out\(131),
	datac => \u_tdm_rx|ch_data_out\(130),
	datad => \u_tdm_rx|ch_data_out\(128),
	combout => \process_1~27_combout\);

-- Location: LCCOMB_X13_Y14_N30
\process_1~30\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~30_combout\ = (\process_1~26_combout\ & (\process_1~29_combout\ & (\process_1~28_combout\ & \process_1~27_combout\)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1000000000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \process_1~26_combout\,
	datab => \process_1~29_combout\,
	datac => \process_1~28_combout\,
	datad => \process_1~27_combout\,
	combout => \process_1~30_combout\);

-- Location: LCCOMB_X12_Y13_N16
\process_1~41\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~41_combout\ = (\process_1~35_combout\ & (\process_1~40_combout\ & (\process_1~25_combout\ & \process_1~30_combout\)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1000000000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \process_1~35_combout\,
	datab => \process_1~40_combout\,
	datac => \process_1~25_combout\,
	datad => \process_1~30_combout\,
	combout => \process_1~41_combout\);

-- Location: LCCOMB_X17_Y14_N6
\u_tdm_rx|ch_data_out[69]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[69]~feeder_combout\ = \u_tdm_rx|shift_reg\(69)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(69),
	combout => \u_tdm_rx|ch_data_out[69]~feeder_combout\);

-- Location: FF_X17_Y14_N7
\u_tdm_rx|ch_data_out[69]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[69]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(69));

-- Location: LCCOMB_X17_Y14_N28
\u_tdm_rx|ch_data_out[70]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[70]~feeder_combout\ = \u_tdm_rx|shift_reg\(70)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(70),
	combout => \u_tdm_rx|ch_data_out[70]~feeder_combout\);

-- Location: FF_X17_Y14_N29
\u_tdm_rx|ch_data_out[70]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[70]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(70));

-- Location: FF_X17_Y14_N9
\u_tdm_rx|ch_data_out[68]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(68),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(68));

-- Location: FF_X17_Y14_N11
\u_tdm_rx|ch_data_out[71]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(71),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(71));

-- Location: LCCOMB_X17_Y14_N8
\process_1~47\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~47_combout\ = (\u_tdm_rx|ch_data_out\(69) & (\u_tdm_rx|ch_data_out\(70) & (\u_tdm_rx|ch_data_out\(68) & \u_tdm_rx|ch_data_out\(71))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1000000000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(69),
	datab => \u_tdm_rx|ch_data_out\(70),
	datac => \u_tdm_rx|ch_data_out\(68),
	datad => \u_tdm_rx|ch_data_out\(71),
	combout => \process_1~47_combout\);

-- Location: LCCOMB_X13_Y12_N28
\u_tdm_rx|ch_data_out[61]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[61]~feeder_combout\ = \u_tdm_rx|shift_reg\(61)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(61),
	combout => \u_tdm_rx|ch_data_out[61]~feeder_combout\);

-- Location: FF_X13_Y12_N29
\u_tdm_rx|ch_data_out[61]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[61]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(61));

-- Location: FF_X13_Y12_N17
\u_tdm_rx|ch_data_out[63]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(63),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(63));

-- Location: FF_X13_Y12_N9
\u_tdm_rx|ch_data_out[60]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(60),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(60));

-- Location: LCCOMB_X13_Y12_N18
\u_tdm_rx|ch_data_out[62]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[62]~feeder_combout\ = \u_tdm_rx|shift_reg\(62)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(62),
	combout => \u_tdm_rx|ch_data_out[62]~feeder_combout\);

-- Location: FF_X13_Y12_N19
\u_tdm_rx|ch_data_out[62]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[62]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(62));

-- Location: LCCOMB_X13_Y12_N8
\process_1~49\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~49_combout\ = (\u_tdm_rx|ch_data_out\(61) & (\u_tdm_rx|ch_data_out\(63) & (\u_tdm_rx|ch_data_out\(60) & \u_tdm_rx|ch_data_out\(62))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1000000000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(61),
	datab => \u_tdm_rx|ch_data_out\(63),
	datac => \u_tdm_rx|ch_data_out\(60),
	datad => \u_tdm_rx|ch_data_out\(62),
	combout => \process_1~49_combout\);

-- Location: LCCOMB_X13_Y12_N20
\u_tdm_rx|ch_data_out[67]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[67]~feeder_combout\ = \u_tdm_rx|shift_reg\(67)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(67),
	combout => \u_tdm_rx|ch_data_out[67]~feeder_combout\);

-- Location: FF_X13_Y12_N21
\u_tdm_rx|ch_data_out[67]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[67]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(67));

-- Location: LCCOMB_X13_Y12_N22
\u_tdm_rx|ch_data_out[65]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[65]~feeder_combout\ = \u_tdm_rx|shift_reg\(65)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(65),
	combout => \u_tdm_rx|ch_data_out[65]~feeder_combout\);

-- Location: FF_X13_Y12_N23
\u_tdm_rx|ch_data_out[65]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[65]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(65));

-- Location: FF_X13_Y12_N15
\u_tdm_rx|ch_data_out[64]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(64),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(64));

-- Location: LCCOMB_X13_Y12_N4
\u_tdm_rx|ch_data_out[66]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[66]~feeder_combout\ = \u_tdm_rx|shift_reg\(66)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(66),
	combout => \u_tdm_rx|ch_data_out[66]~feeder_combout\);

-- Location: FF_X13_Y12_N5
\u_tdm_rx|ch_data_out[66]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[66]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(66));

-- Location: LCCOMB_X13_Y12_N14
\process_1~48\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~48_combout\ = (!\u_tdm_rx|ch_data_out\(67) & (\u_tdm_rx|ch_data_out\(65) & (!\u_tdm_rx|ch_data_out\(64) & \u_tdm_rx|ch_data_out\(66))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000010000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(67),
	datab => \u_tdm_rx|ch_data_out\(65),
	datac => \u_tdm_rx|ch_data_out\(64),
	datad => \u_tdm_rx|ch_data_out\(66),
	combout => \process_1~48_combout\);

-- Location: LCCOMB_X12_Y11_N8
\u_tdm_rx|ch_data_out[57]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[57]~feeder_combout\ = \u_tdm_rx|shift_reg\(57)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(57),
	combout => \u_tdm_rx|ch_data_out[57]~feeder_combout\);

-- Location: FF_X12_Y11_N9
\u_tdm_rx|ch_data_out[57]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[57]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(57));

-- Location: LCCOMB_X13_Y11_N12
\u_tdm_rx|ch_data_out[59]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[59]~feeder_combout\ = \u_tdm_rx|shift_reg\(59)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(59),
	combout => \u_tdm_rx|ch_data_out[59]~feeder_combout\);

-- Location: FF_X13_Y11_N13
\u_tdm_rx|ch_data_out[59]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[59]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(59));

-- Location: FF_X13_Y11_N17
\u_tdm_rx|ch_data_out[56]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(56),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(56));

-- Location: LCCOMB_X13_Y11_N4
\u_tdm_rx|ch_data_out[58]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[58]~feeder_combout\ = \u_tdm_rx|shift_reg\(58)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(58),
	combout => \u_tdm_rx|ch_data_out[58]~feeder_combout\);

-- Location: FF_X13_Y11_N5
\u_tdm_rx|ch_data_out[58]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[58]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(58));

-- Location: LCCOMB_X13_Y11_N16
\process_1~50\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~50_combout\ = (\u_tdm_rx|ch_data_out\(57) & (!\u_tdm_rx|ch_data_out\(59) & (!\u_tdm_rx|ch_data_out\(56) & \u_tdm_rx|ch_data_out\(58))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000001000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(57),
	datab => \u_tdm_rx|ch_data_out\(59),
	datac => \u_tdm_rx|ch_data_out\(56),
	datad => \u_tdm_rx|ch_data_out\(58),
	combout => \process_1~50_combout\);

-- Location: LCCOMB_X13_Y12_N6
\process_1~51\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~51_combout\ = (\process_1~47_combout\ & (\process_1~49_combout\ & (\process_1~48_combout\ & \process_1~50_combout\)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1000000000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \process_1~47_combout\,
	datab => \process_1~49_combout\,
	datac => \process_1~48_combout\,
	datad => \process_1~50_combout\,
	combout => \process_1~51_combout\);

-- Location: LCCOMB_X14_Y9_N26
\u_tdm_rx|ch_data_out[37]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[37]~feeder_combout\ = \u_tdm_rx|shift_reg\(37)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(37),
	combout => \u_tdm_rx|ch_data_out[37]~feeder_combout\);

-- Location: FF_X14_Y9_N27
\u_tdm_rx|ch_data_out[37]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[37]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(37));

-- Location: LCCOMB_X14_Y9_N16
\u_tdm_rx|ch_data_out[39]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[39]~feeder_combout\ = \u_tdm_rx|shift_reg\(39)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(39),
	combout => \u_tdm_rx|ch_data_out[39]~feeder_combout\);

-- Location: FF_X14_Y9_N17
\u_tdm_rx|ch_data_out[39]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[39]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(39));

-- Location: FF_X14_Y9_N15
\u_tdm_rx|ch_data_out[36]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(36),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(36));

-- Location: LCCOMB_X14_Y9_N0
\u_tdm_rx|ch_data_out[38]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[38]~feeder_combout\ = \u_tdm_rx|shift_reg\(38)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(38),
	combout => \u_tdm_rx|ch_data_out[38]~feeder_combout\);

-- Location: FF_X14_Y9_N1
\u_tdm_rx|ch_data_out[38]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[38]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(38));

-- Location: LCCOMB_X14_Y9_N14
\process_1~57\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~57_combout\ = (!\u_tdm_rx|ch_data_out\(37) & (!\u_tdm_rx|ch_data_out\(39) & (!\u_tdm_rx|ch_data_out\(36) & !\u_tdm_rx|ch_data_out\(38))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000000000000001",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(37),
	datab => \u_tdm_rx|ch_data_out\(39),
	datac => \u_tdm_rx|ch_data_out\(36),
	datad => \u_tdm_rx|ch_data_out\(38),
	combout => \process_1~57_combout\);

-- Location: LCCOMB_X14_Y10_N10
\u_tdm_rx|ch_data_out[30]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[30]~feeder_combout\ = \u_tdm_rx|shift_reg\(30)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(30),
	combout => \u_tdm_rx|ch_data_out[30]~feeder_combout\);

-- Location: FF_X14_Y10_N11
\u_tdm_rx|ch_data_out[30]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[30]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(30));

-- Location: LCCOMB_X14_Y10_N0
\u_tdm_rx|ch_data_out[29]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[29]~feeder_combout\ = \u_tdm_rx|shift_reg\(29)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(29),
	combout => \u_tdm_rx|ch_data_out[29]~feeder_combout\);

-- Location: FF_X14_Y10_N1
\u_tdm_rx|ch_data_out[29]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[29]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(29));

-- Location: FF_X14_Y10_N21
\u_tdm_rx|ch_data_out[28]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(28),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(28));

-- Location: LCCOMB_X14_Y10_N24
\u_tdm_rx|ch_data_out[31]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[31]~feeder_combout\ = \u_tdm_rx|shift_reg\(31)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(31),
	combout => \u_tdm_rx|ch_data_out[31]~feeder_combout\);

-- Location: FF_X14_Y10_N25
\u_tdm_rx|ch_data_out[31]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[31]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(31));

-- Location: LCCOMB_X14_Y10_N20
\process_1~59\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~59_combout\ = (!\u_tdm_rx|ch_data_out\(30) & (!\u_tdm_rx|ch_data_out\(29) & (!\u_tdm_rx|ch_data_out\(28) & !\u_tdm_rx|ch_data_out\(31))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000000000000001",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(30),
	datab => \u_tdm_rx|ch_data_out\(29),
	datac => \u_tdm_rx|ch_data_out\(28),
	datad => \u_tdm_rx|ch_data_out\(31),
	combout => \process_1~59_combout\);

-- Location: LCCOMB_X14_Y10_N22
\u_tdm_rx|ch_data_out[35]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[35]~feeder_combout\ = \u_tdm_rx|shift_reg\(35)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(35),
	combout => \u_tdm_rx|ch_data_out[35]~feeder_combout\);

-- Location: FF_X14_Y10_N23
\u_tdm_rx|ch_data_out[35]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[35]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(35));

-- Location: FF_X14_Y10_N3
\u_tdm_rx|ch_data_out[33]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(33),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(33));

-- Location: FF_X14_Y10_N5
\u_tdm_rx|ch_data_out[32]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(32),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(32));

-- Location: LCCOMB_X14_Y10_N6
\u_tdm_rx|ch_data_out[34]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[34]~feeder_combout\ = \u_tdm_rx|shift_reg\(34)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(34),
	combout => \u_tdm_rx|ch_data_out[34]~feeder_combout\);

-- Location: FF_X14_Y10_N7
\u_tdm_rx|ch_data_out[34]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[34]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(34));

-- Location: LCCOMB_X14_Y10_N4
\process_1~58\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~58_combout\ = (!\u_tdm_rx|ch_data_out\(35) & (\u_tdm_rx|ch_data_out\(33) & (\u_tdm_rx|ch_data_out\(32) & \u_tdm_rx|ch_data_out\(34))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0100000000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(35),
	datab => \u_tdm_rx|ch_data_out\(33),
	datac => \u_tdm_rx|ch_data_out\(32),
	datad => \u_tdm_rx|ch_data_out\(34),
	combout => \process_1~58_combout\);

-- Location: LCCOMB_X16_Y10_N26
\u_tdm_rx|ch_data_out[26]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[26]~feeder_combout\ = \u_tdm_rx|shift_reg\(26)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(26),
	combout => \u_tdm_rx|ch_data_out[26]~feeder_combout\);

-- Location: FF_X16_Y10_N27
\u_tdm_rx|ch_data_out[26]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[26]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(26));

-- Location: LCCOMB_X16_Y10_N8
\u_tdm_rx|ch_data_out[25]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[25]~feeder_combout\ = \u_tdm_rx|shift_reg\(25)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(25),
	combout => \u_tdm_rx|ch_data_out[25]~feeder_combout\);

-- Location: FF_X16_Y10_N9
\u_tdm_rx|ch_data_out[25]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[25]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(25));

-- Location: FF_X16_Y10_N31
\u_tdm_rx|ch_data_out[24]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(24),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(24));

-- Location: LCCOMB_X16_Y10_N6
\u_tdm_rx|ch_data_out[27]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[27]~feeder_combout\ = \u_tdm_rx|shift_reg\(27)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(27),
	combout => \u_tdm_rx|ch_data_out[27]~feeder_combout\);

-- Location: FF_X16_Y10_N7
\u_tdm_rx|ch_data_out[27]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[27]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(27));

-- Location: LCCOMB_X16_Y10_N30
\process_1~60\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~60_combout\ = (\u_tdm_rx|ch_data_out\(26) & (\u_tdm_rx|ch_data_out\(25) & (\u_tdm_rx|ch_data_out\(24) & !\u_tdm_rx|ch_data_out\(27))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000000010000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(26),
	datab => \u_tdm_rx|ch_data_out\(25),
	datac => \u_tdm_rx|ch_data_out\(24),
	datad => \u_tdm_rx|ch_data_out\(27),
	combout => \process_1~60_combout\);

-- Location: LCCOMB_X14_Y10_N16
\process_1~61\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~61_combout\ = (\process_1~57_combout\ & (\process_1~59_combout\ & (\process_1~58_combout\ & \process_1~60_combout\)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1000000000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \process_1~57_combout\,
	datab => \process_1~59_combout\,
	datac => \process_1~58_combout\,
	datad => \process_1~60_combout\,
	combout => \process_1~61_combout\);

-- Location: LCCOMB_X16_Y15_N12
\u_tdm_rx|ch_data_out[84]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[84]~feeder_combout\ = \u_tdm_rx|shift_reg\(84)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(84),
	combout => \u_tdm_rx|ch_data_out[84]~feeder_combout\);

-- Location: FF_X16_Y15_N13
\u_tdm_rx|ch_data_out[84]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[84]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(84));

-- Location: LCCOMB_X16_Y15_N28
\u_tdm_rx|ch_data_out[86]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[86]~feeder_combout\ = \u_tdm_rx|shift_reg\(86)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(86),
	combout => \u_tdm_rx|ch_data_out[86]~feeder_combout\);

-- Location: FF_X16_Y15_N29
\u_tdm_rx|ch_data_out[86]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[86]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(86));

-- Location: FF_X16_Y15_N15
\u_tdm_rx|ch_data_out[85]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(85),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(85));

-- Location: FF_X16_Y15_N21
\u_tdm_rx|ch_data_out[87]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(87),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(87));

-- Location: LCCOMB_X16_Y15_N14
\process_1~42\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~42_combout\ = (!\u_tdm_rx|ch_data_out\(84) & (\u_tdm_rx|ch_data_out\(86) & (\u_tdm_rx|ch_data_out\(85) & \u_tdm_rx|ch_data_out\(87))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0100000000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(84),
	datab => \u_tdm_rx|ch_data_out\(86),
	datac => \u_tdm_rx|ch_data_out\(85),
	datad => \u_tdm_rx|ch_data_out\(87),
	combout => \process_1~42_combout\);

-- Location: LCCOMB_X17_Y15_N26
\u_tdm_rx|ch_data_out[75]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[75]~feeder_combout\ = \u_tdm_rx|shift_reg\(75)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(75),
	combout => \u_tdm_rx|ch_data_out[75]~feeder_combout\);

-- Location: FF_X17_Y15_N27
\u_tdm_rx|ch_data_out[75]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[75]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(75));

-- Location: FF_X17_Y14_N1
\u_tdm_rx|ch_data_out[72]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(72),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(72));

-- Location: FF_X17_Y15_N5
\u_tdm_rx|ch_data_out[73]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(73),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(73));

-- Location: LCCOMB_X17_Y15_N0
\u_tdm_rx|ch_data_out[74]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[74]~feeder_combout\ = \u_tdm_rx|shift_reg\(74)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(74),
	combout => \u_tdm_rx|ch_data_out[74]~feeder_combout\);

-- Location: FF_X17_Y15_N1
\u_tdm_rx|ch_data_out[74]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[74]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(74));

-- Location: LCCOMB_X17_Y15_N4
\process_1~45\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~45_combout\ = (!\u_tdm_rx|ch_data_out\(75) & (\u_tdm_rx|ch_data_out\(72) & (!\u_tdm_rx|ch_data_out\(73) & \u_tdm_rx|ch_data_out\(74))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000010000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(75),
	datab => \u_tdm_rx|ch_data_out\(72),
	datac => \u_tdm_rx|ch_data_out\(73),
	datad => \u_tdm_rx|ch_data_out\(74),
	combout => \process_1~45_combout\);

-- Location: LCCOMB_X16_Y15_N26
\u_tdm_rx|ch_data_out[82]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[82]~feeder_combout\ = \u_tdm_rx|shift_reg\(82)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(82),
	combout => \u_tdm_rx|ch_data_out[82]~feeder_combout\);

-- Location: FF_X16_Y15_N27
\u_tdm_rx|ch_data_out[82]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[82]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(82));

-- Location: LCCOMB_X16_Y15_N16
\u_tdm_rx|ch_data_out[83]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[83]~feeder_combout\ = \u_tdm_rx|shift_reg\(83)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(83),
	combout => \u_tdm_rx|ch_data_out[83]~feeder_combout\);

-- Location: FF_X16_Y15_N17
\u_tdm_rx|ch_data_out[83]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[83]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(83));

-- Location: FF_X16_Y15_N7
\u_tdm_rx|ch_data_out[81]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(81),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(81));

-- Location: LCCOMB_X16_Y15_N8
\u_tdm_rx|ch_data_out[80]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[80]~feeder_combout\ = \u_tdm_rx|shift_reg\(80)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(80),
	combout => \u_tdm_rx|ch_data_out[80]~feeder_combout\);

-- Location: FF_X16_Y15_N9
\u_tdm_rx|ch_data_out[80]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[80]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(80));

-- Location: LCCOMB_X16_Y15_N6
\process_1~43\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~43_combout\ = (\u_tdm_rx|ch_data_out\(82) & (!\u_tdm_rx|ch_data_out\(83) & (!\u_tdm_rx|ch_data_out\(81) & \u_tdm_rx|ch_data_out\(80))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000001000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(82),
	datab => \u_tdm_rx|ch_data_out\(83),
	datac => \u_tdm_rx|ch_data_out\(81),
	datad => \u_tdm_rx|ch_data_out\(80),
	combout => \process_1~43_combout\);

-- Location: LCCOMB_X17_Y15_N22
\u_tdm_rx|ch_data_out[76]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[76]~feeder_combout\ = \u_tdm_rx|shift_reg\(76)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(76),
	combout => \u_tdm_rx|ch_data_out[76]~feeder_combout\);

-- Location: FF_X17_Y15_N23
\u_tdm_rx|ch_data_out[76]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[76]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(76));

-- Location: LCCOMB_X17_Y15_N8
\u_tdm_rx|ch_data_out[79]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[79]~feeder_combout\ = \u_tdm_rx|shift_reg\(79)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(79),
	combout => \u_tdm_rx|ch_data_out[79]~feeder_combout\);

-- Location: FF_X17_Y15_N9
\u_tdm_rx|ch_data_out[79]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[79]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(79));

-- Location: FF_X17_Y15_N13
\u_tdm_rx|ch_data_out[77]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(77),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(77));

-- Location: LCCOMB_X17_Y15_N10
\u_tdm_rx|ch_data_out[78]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[78]~feeder_combout\ = \u_tdm_rx|shift_reg\(78)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(78),
	combout => \u_tdm_rx|ch_data_out[78]~feeder_combout\);

-- Location: FF_X17_Y15_N11
\u_tdm_rx|ch_data_out[78]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[78]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(78));

-- Location: LCCOMB_X17_Y15_N12
\process_1~44\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~44_combout\ = (!\u_tdm_rx|ch_data_out\(76) & (\u_tdm_rx|ch_data_out\(79) & (\u_tdm_rx|ch_data_out\(77) & \u_tdm_rx|ch_data_out\(78))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0100000000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(76),
	datab => \u_tdm_rx|ch_data_out\(79),
	datac => \u_tdm_rx|ch_data_out\(77),
	datad => \u_tdm_rx|ch_data_out\(78),
	combout => \process_1~44_combout\);

-- Location: LCCOMB_X17_Y15_N6
\process_1~46\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~46_combout\ = (\process_1~42_combout\ & (\process_1~45_combout\ & (\process_1~43_combout\ & \process_1~44_combout\)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1000000000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \process_1~42_combout\,
	datab => \process_1~45_combout\,
	datac => \process_1~43_combout\,
	datad => \process_1~44_combout\,
	combout => \process_1~46_combout\);

-- Location: LCCOMB_X14_Y11_N12
\u_tdm_rx|ch_data_out[47]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[47]~feeder_combout\ = \u_tdm_rx|shift_reg\(47)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(47),
	combout => \u_tdm_rx|ch_data_out[47]~feeder_combout\);

-- Location: FF_X14_Y11_N13
\u_tdm_rx|ch_data_out[47]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[47]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(47));

-- Location: LCCOMB_X14_Y11_N16
\u_tdm_rx|ch_data_out[46]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[46]~feeder_combout\ = \u_tdm_rx|shift_reg\(46)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(46),
	combout => \u_tdm_rx|ch_data_out[46]~feeder_combout\);

-- Location: FF_X14_Y11_N17
\u_tdm_rx|ch_data_out[46]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[46]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(46));

-- Location: FF_X14_Y11_N7
\u_tdm_rx|ch_data_out[44]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(44),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(44));

-- Location: FF_X14_Y11_N9
\u_tdm_rx|ch_data_out[45]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(45),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(45));

-- Location: LCCOMB_X14_Y11_N6
\process_1~54\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~54_combout\ = (!\u_tdm_rx|ch_data_out\(47) & (!\u_tdm_rx|ch_data_out\(46) & (!\u_tdm_rx|ch_data_out\(44) & !\u_tdm_rx|ch_data_out\(45))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000000000000001",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(47),
	datab => \u_tdm_rx|ch_data_out\(46),
	datac => \u_tdm_rx|ch_data_out\(44),
	datad => \u_tdm_rx|ch_data_out\(45),
	combout => \process_1~54_combout\);

-- Location: LCCOMB_X14_Y9_N30
\u_tdm_rx|ch_data_out[43]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[43]~feeder_combout\ = \u_tdm_rx|shift_reg\(43)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(43),
	combout => \u_tdm_rx|ch_data_out[43]~feeder_combout\);

-- Location: FF_X14_Y9_N31
\u_tdm_rx|ch_data_out[43]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[43]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(43));

-- Location: LCCOMB_X14_Y9_N20
\u_tdm_rx|ch_data_out[41]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[41]~feeder_combout\ = \u_tdm_rx|shift_reg\(41)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(41),
	combout => \u_tdm_rx|ch_data_out[41]~feeder_combout\);

-- Location: FF_X14_Y9_N21
\u_tdm_rx|ch_data_out[41]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[41]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(41));

-- Location: FF_X14_Y9_N9
\u_tdm_rx|ch_data_out[40]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(40),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(40));

-- Location: LCCOMB_X14_Y9_N6
\u_tdm_rx|ch_data_out[42]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[42]~feeder_combout\ = \u_tdm_rx|shift_reg\(42)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(42),
	combout => \u_tdm_rx|ch_data_out[42]~feeder_combout\);

-- Location: FF_X14_Y9_N7
\u_tdm_rx|ch_data_out[42]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[42]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(42));

-- Location: LCCOMB_X14_Y9_N8
\process_1~55\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~55_combout\ = (!\u_tdm_rx|ch_data_out\(43) & (\u_tdm_rx|ch_data_out\(41) & (\u_tdm_rx|ch_data_out\(40) & \u_tdm_rx|ch_data_out\(42))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0100000000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(43),
	datab => \u_tdm_rx|ch_data_out\(41),
	datac => \u_tdm_rx|ch_data_out\(40),
	datad => \u_tdm_rx|ch_data_out\(42),
	combout => \process_1~55_combout\);

-- Location: FF_X14_Y11_N11
\u_tdm_rx|ch_data_out[49]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(49),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(49));

-- Location: FF_X14_Y11_N25
\u_tdm_rx|ch_data_out[50]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(50),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(50));

-- Location: FF_X14_Y11_N27
\u_tdm_rx|ch_data_out[48]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(48),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(48));

-- Location: LCCOMB_X14_Y11_N20
\u_tdm_rx|ch_data_out[51]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[51]~feeder_combout\ = \u_tdm_rx|shift_reg\(51)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(51),
	combout => \u_tdm_rx|ch_data_out[51]~feeder_combout\);

-- Location: FF_X14_Y11_N21
\u_tdm_rx|ch_data_out[51]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[51]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(51));

-- Location: LCCOMB_X14_Y11_N26
\process_1~53\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~53_combout\ = (\u_tdm_rx|ch_data_out\(49) & (\u_tdm_rx|ch_data_out\(50) & (!\u_tdm_rx|ch_data_out\(48) & !\u_tdm_rx|ch_data_out\(51))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000000000001000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(49),
	datab => \u_tdm_rx|ch_data_out\(50),
	datac => \u_tdm_rx|ch_data_out\(48),
	datad => \u_tdm_rx|ch_data_out\(51),
	combout => \process_1~53_combout\);

-- Location: FF_X13_Y11_N27
\u_tdm_rx|ch_data_out[55]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(55),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(55));

-- Location: LCCOMB_X13_Y11_N30
\u_tdm_rx|ch_data_out[54]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[54]~feeder_combout\ = \u_tdm_rx|shift_reg\(54)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(54),
	combout => \u_tdm_rx|ch_data_out[54]~feeder_combout\);

-- Location: FF_X13_Y11_N31
\u_tdm_rx|ch_data_out[54]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[54]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(54));

-- Location: FF_X13_Y11_N25
\u_tdm_rx|ch_data_out[52]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	asdata => \u_tdm_rx|shift_reg\(52),
	clrn => \rst_n~inputclkctrl_outclk\,
	sload => VCC,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(52));

-- Location: LCCOMB_X13_Y11_N18
\u_tdm_rx|ch_data_out[53]~feeder\ : cycloneive_lcell_comb
-- Equation(s):
-- \u_tdm_rx|ch_data_out[53]~feeder_combout\ = \u_tdm_rx|shift_reg\(53)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111111100000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datad => \u_tdm_rx|shift_reg\(53),
	combout => \u_tdm_rx|ch_data_out[53]~feeder_combout\);

-- Location: FF_X13_Y11_N19
\u_tdm_rx|ch_data_out[53]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \u_tdm_rx|ch_data_out[53]~feeder_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	ena => \u_tdm_rx|process_0~0_combout\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \u_tdm_rx|ch_data_out\(53));

-- Location: LCCOMB_X13_Y11_N24
\process_1~52\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~52_combout\ = (\u_tdm_rx|ch_data_out\(55) & (\u_tdm_rx|ch_data_out\(54) & (\u_tdm_rx|ch_data_out\(52) & \u_tdm_rx|ch_data_out\(53))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1000000000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \u_tdm_rx|ch_data_out\(55),
	datab => \u_tdm_rx|ch_data_out\(54),
	datac => \u_tdm_rx|ch_data_out\(52),
	datad => \u_tdm_rx|ch_data_out\(53),
	combout => \process_1~52_combout\);

-- Location: LCCOMB_X14_Y11_N18
\process_1~56\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~56_combout\ = (\process_1~54_combout\ & (\process_1~55_combout\ & (\process_1~53_combout\ & \process_1~52_combout\)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1000000000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \process_1~54_combout\,
	datab => \process_1~55_combout\,
	datac => \process_1~53_combout\,
	datad => \process_1~52_combout\,
	combout => \process_1~56_combout\);

-- Location: LCCOMB_X18_Y12_N28
\process_1~62\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~62_combout\ = (\process_1~51_combout\ & (\process_1~61_combout\ & (\process_1~46_combout\ & \process_1~56_combout\)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1000000000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \process_1~51_combout\,
	datab => \process_1~61_combout\,
	datac => \process_1~46_combout\,
	datad => \process_1~56_combout\,
	combout => \process_1~62_combout\);

-- Location: LCCOMB_X18_Y12_N6
\process_1~71\ : cycloneive_lcell_comb
-- Equation(s):
-- \process_1~71_combout\ = (\process_1~20_combout\ & (\process_1~70_combout\ & (\process_1~41_combout\ & \process_1~62_combout\)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1000000000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \process_1~20_combout\,
	datab => \process_1~70_combout\,
	datac => \process_1~41_combout\,
	datad => \process_1~62_combout\,
	combout => \process_1~71_combout\);

-- Location: LCCOMB_X18_Y12_N8
\match_cnt[0]~7\ : cycloneive_lcell_comb
-- Equation(s):
-- \match_cnt[0]~7_combout\ = match_cnt(0) $ (((!\match_cnt[3]~0_combout\ & (\fail_reg~0_combout\ & \process_1~71_combout\))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1011010011110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \match_cnt[3]~0_combout\,
	datab => \fail_reg~0_combout\,
	datac => match_cnt(0),
	datad => \process_1~71_combout\,
	combout => \match_cnt[0]~7_combout\);

-- Location: FF_X18_Y12_N9
\match_cnt[0]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \match_cnt[0]~7_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => match_cnt(0));

-- Location: LCCOMB_X18_Y12_N16
\match_cnt[1]~3\ : cycloneive_lcell_comb
-- Equation(s):
-- \match_cnt[1]~3_combout\ = (match_cnt(0) & (\lrclk_prev~q\ & startup_ignore(1)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1100000000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => match_cnt(0),
	datac => \lrclk_prev~q\,
	datad => startup_ignore(1),
	combout => \match_cnt[1]~3_combout\);

-- Location: LCCOMB_X18_Y12_N20
\match_cnt[1]~4\ : cycloneive_lcell_comb
-- Equation(s):
-- \match_cnt[1]~4_combout\ = (!\match_cnt[3]~0_combout\ & (\match_cnt[1]~3_combout\ & (!\u_tdm_master|lrclk_reg~q\ & \process_1~71_combout\)))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000010000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \match_cnt[3]~0_combout\,
	datab => \match_cnt[1]~3_combout\,
	datac => \u_tdm_master|lrclk_reg~q\,
	datad => \process_1~71_combout\,
	combout => \match_cnt[1]~4_combout\);

-- Location: LCCOMB_X18_Y12_N12
\match_cnt[1]~6\ : cycloneive_lcell_comb
-- Equation(s):
-- \match_cnt[1]~6_combout\ = match_cnt(1) $ (\match_cnt[1]~4_combout\)

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0000111111110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datac => match_cnt(1),
	datad => \match_cnt[1]~4_combout\,
	combout => \match_cnt[1]~6_combout\);

-- Location: FF_X18_Y12_N13
\match_cnt[1]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \match_cnt[1]~6_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => match_cnt(1));

-- Location: LCCOMB_X18_Y12_N26
\match_cnt[2]~5\ : cycloneive_lcell_comb
-- Equation(s):
-- \match_cnt[2]~5_combout\ = match_cnt(2) $ (((\match_cnt[1]~4_combout\ & match_cnt(1))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "0011110011110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \match_cnt[1]~4_combout\,
	datac => match_cnt(2),
	datad => match_cnt(1),
	combout => \match_cnt[2]~5_combout\);

-- Location: FF_X18_Y12_N27
\match_cnt[2]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \match_cnt[2]~5_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => match_cnt(2));

-- Location: LCCOMB_X18_Y12_N10
\match_cnt[3]~1\ : cycloneive_lcell_comb
-- Equation(s):
-- \match_cnt[3]~1_combout\ = (((\match_cnt[3]~0_combout\) # (!\process_1~71_combout\)) # (!match_cnt(0))) # (!match_cnt(1))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111011111111111",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => match_cnt(1),
	datab => match_cnt(0),
	datac => \match_cnt[3]~0_combout\,
	datad => \process_1~71_combout\,
	combout => \match_cnt[3]~1_combout\);

-- Location: LCCOMB_X18_Y12_N0
\match_cnt[3]~2\ : cycloneive_lcell_comb
-- Equation(s):
-- \match_cnt[3]~2_combout\ = match_cnt(3) $ (((match_cnt(2) & (\fail_reg~0_combout\ & !\match_cnt[3]~1_combout\))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111000001111000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => match_cnt(2),
	datab => \fail_reg~0_combout\,
	datac => match_cnt(3),
	datad => \match_cnt[3]~1_combout\,
	combout => \match_cnt[3]~2_combout\);

-- Location: FF_X18_Y12_N1
\match_cnt[3]\ : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \match_cnt[3]~2_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => match_cnt(3));

-- Location: LCCOMB_X18_Y12_N22
\match_cnt[3]~0\ : cycloneive_lcell_comb
-- Equation(s):
-- \match_cnt[3]~0_combout\ = (match_cnt(3) & ((match_cnt(1)) # (match_cnt(2))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111101000000000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => match_cnt(1),
	datac => match_cnt(2),
	datad => match_cnt(3),
	combout => \match_cnt[3]~0_combout\);

-- Location: LCCOMB_X18_Y12_N24
\pass_reg~0\ : cycloneive_lcell_comb
-- Equation(s):
-- \pass_reg~0_combout\ = (\fail_reg~0_combout\ & (\process_1~71_combout\ & ((\match_cnt[3]~0_combout\) # (\pass_reg~q\)))) # (!\fail_reg~0_combout\ & (((\pass_reg~q\))))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111100000110000",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	dataa => \match_cnt[3]~0_combout\,
	datab => \fail_reg~0_combout\,
	datac => \pass_reg~q\,
	datad => \process_1~71_combout\,
	combout => \pass_reg~0_combout\);

-- Location: FF_X18_Y12_N25
pass_reg : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \pass_reg~0_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \pass_reg~q\);

-- Location: LCCOMB_X18_Y12_N2
\fail_reg~1\ : cycloneive_lcell_comb
-- Equation(s):
-- \fail_reg~1_combout\ = (\fail_reg~q\) # ((\fail_reg~0_combout\ & !\process_1~71_combout\))

-- pragma translate_off
GENERIC MAP (
	lut_mask => "1111000011111100",
	sum_lutc_input => "datac")
-- pragma translate_on
PORT MAP (
	datab => \fail_reg~0_combout\,
	datac => \fail_reg~q\,
	datad => \process_1~71_combout\,
	combout => \fail_reg~1_combout\);

-- Location: FF_X18_Y12_N3
fail_reg : dffeas
-- pragma translate_off
GENERIC MAP (
	is_wysiwyg => "true",
	power_up => "low")
-- pragma translate_on
PORT MAP (
	clk => \clk_18m432~inputclkctrl_outclk\,
	d => \fail_reg~1_combout\,
	clrn => \rst_n~inputclkctrl_outclk\,
	devclrn => ww_devclrn,
	devpor => ww_devpor,
	q => \fail_reg~q\);

ww_pass_led <= \pass_led~output_o\;

ww_fail_led <= \fail_led~output_o\;
END structure;


