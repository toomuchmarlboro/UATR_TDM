onerror {resume}
quietly WaveActivateNextPane {} 0
add wave -noupdate /tb_tdm16/clk_18m432
add wave -noupdate /tb_tdm16/rst
add wave -noupdate /tb_tdm16/bclk
add wave -noupdate /tb_tdm16/lrclk
add wave -noupdate /tb_tdm16/sdata_A
add wave -noupdate /tb_tdm16/sdata_B
add wave -noupdate -radix hexadecimal /tb_tdm16/tdm16_out
add wave -noupdate /tb_tdm16/tdm16_valid
TreeUpdate [SetDefaultTree]
WaveRestoreCursors {{Cursor 1} {22597098 ps} 0}
quietly wave cursor active 1
configure wave -namecolwidth 150
configure wave -valuecolwidth 100
configure wave -justifyvalue left
configure wave -signalnamewidth 0
configure wave -snapdistance 10
configure wave -datasetprefix 0
configure wave -rowmargin 4
configure wave -childrowmargin 2
configure wave -gridoffset 0
configure wave -gridperiod 1
configure wave -griddelta 40
configure wave -timeline 0
configure wave -timelineunits ns
update
WaveRestoreZoom {20753138 ps} {22065906 ps}
