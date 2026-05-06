onerror {resume}
quietly WaveActivateNextPane {} 0
add wave -noupdate /tb_tdm8_rx/rst
add wave -noupdate /tb_tdm8_rx/clk_18m432
add wave -noupdate /tb_tdm8_rx/bclk
add wave -noupdate /tb_tdm8_rx/lrclk
add wave -noupdate /tb_tdm8_rx/sdata_in
add wave -noupdate -radix hexadecimal /tb_tdm8_rx/ch_data_out
TreeUpdate [SetDefaultTree]
WaveRestoreCursors {{Cursor 1} {21076125 ps} 0}
quietly wave cursor active 1
configure wave -namecolwidth 150
configure wave -valuecolwidth 62
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
configure wave -timelineunits ps
update
WaveRestoreZoom {18098140 ps} {23634428 ps}
